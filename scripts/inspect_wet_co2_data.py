"""Audit the pinned wet-CO2 compilation and separately reviewed unit evidence."""

import json
from collections import Counter
from pathlib import Path

from matintegrity.wet_co2_data import (
    ASSOCIATED_PAPER_DOI,
    ASSOCIATED_PAPER_UNIT_BASIS_ID,
    SIMULATION_DATASET_DOI,
    SIMULATION_PINNED_SHA256,
    match_wet_co2_simulation_source,
    read_unresolved_wet_co2_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/heterogeneous-wet-co2-corrosion/CO2.csv"
SIMULATION_SOURCE = (
    ROOT / "data/raw/norsok-m506-simulation-grid/Dataset for internal CO2 corrosion of oil pipeline.xlsx"
)
OUTPUT = ROOT / "validation/heterogeneous_wet_co2_dataset.json"
FIELDS = (
    "raw_temperature",
    "raw_flow_velocity",
    "raw_co2_pressure",
    "raw_internal_pressure",
    "raw_corrosion_inhibitor_efficiency",
    "raw_shear_stress",
    "raw_ph",
    "raw_corrosion_rate",
)


def inspect(path=SOURCE, simulation_source=SIMULATION_SOURCE):
    rows = read_unresolved_wet_co2_compilation(path)
    simulation_matches = match_wet_co2_simulation_source(rows, simulation_source)
    missing = {field: sum(getattr(row, field) is None for row in rows) for field in FIELDS}
    ranges = {}
    unique = {}
    for field in FIELDS:
        values = [getattr(row, field) for row in rows if getattr(row, field) is not None]
        ranges[field] = [min(values), max(values)]
        unique[field] = len(set(values))
    missingness_patterns = Counter(
        ",".join(field for field in FIELDS if getattr(row, field) is None) or "complete" for row in rows
    )
    value_tuples = [tuple(getattr(row, field) for field in FIELDS) for row in rows]
    report = {
        "schema": "matintegrity.heterogeneous_wet_co2_dataset_audit.v1",
        "dataset_id": rows[0].dataset_id,
        "source_sha256": rows[0].source_archive_sha256,
        "rows": len(rows),
        "columns": len(FIELDS),
        "raw_value_ranges_without_units": ranges,
        "unique_value_counts": unique,
        "missing_value_counts": missing,
        "missingness_patterns": dict(sorted(missingness_patterns.items())),
        "fully_duplicated_rows_beyond_first": len(value_tuples) - len(set(value_tuples)),
        "source_group_ids_available_for_rows": len(simulation_matches),
        "source_group_ids_unresolved_rows": len(rows) - len(simulation_matches),
        "physical_specimen_ids_available": False,
        "data_type_labels_available_for_rows": len(simulation_matches),
        "data_type_labels_unresolved_rows": len(rows) - len(simulation_matches),
        "material_condition_available": False,
        "exposure_duration_available": False,
        "source_file_units_available": False,
        "associated_paper_unit_basis": {
            "doi": ASSOCIATED_PAPER_DOI,
            "basis_id": ASSOCIATED_PAPER_UNIT_BASIS_ID,
            "license": "CC-BY-4.0",
            "temperature": "degree_Celsius",
            "flow_velocity": "metre_per_second",
            "co2_pressure": "bar",
            "internal_pressure": "bar",
            "corrosion_inhibitor_efficiency": "percent",
            "shear_stress": "pascal",
            "ph": "dimensionless",
            "corrosion_rate": "millimetre_per_year",
        },
        "associated_paper_aggregate_composition": {
            "simulated_norsok_m506": 243,
            "experimental_autoclave_weight_loss": 50,
            "field_eastern_hainan_china": 60,
            "field_egua_2_niger_delta_nigeria": 74,
            "sum": 427,
            "row_mapping_available": False,
        },
        "exact_external_source_crosswalk": {
            "source_dataset_doi": SIMULATION_DATASET_DOI,
            "source_sha256": SIMULATION_PINNED_SHA256,
            "source_license": "CC-BY-4.0",
            "matched_compilation_rows": len(simulation_matches),
            "first_compilation_provider_source_row": simulation_matches[0].compilation_provider_source_row,
            "last_compilation_provider_source_row": simulation_matches[-1].compilation_provider_source_row,
            "match_basis": simulation_matches[0].match_basis,
            "data_type": "simulated_model_output",
            "independent_physical_observations": False,
            "public_surrogate_release_review_required": True,
        },
        "mechanistic_calibration_ready": False,
        "empirical_calibration_ready": False,
        "qualification": (
            "The source CSV has no unit labels. Its associated CC-BY-4.0 paper supplies one reviewed "
            "column-unit basis and aggregate source-type counts, enabling an explicitly opted-in SI view. "
            "A separately licensed provider workbook exactly matches compilation rows 2 through 244 and "
            "qualifies those 243 rows as model-generated output, not physical observations. The remaining "
            "184 rows still lack row-level literature sources and physical-observation independence."
        ),
    }
    return report


def main():
    report = inspect()
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
