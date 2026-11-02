"""Create a public-safe aggregate audit from caller-held wet-CO2 literature evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from matintegrity.wet_co2_data import (
    WetCo2LiteratureEvidenceRow,
    WetCo2LiteratureFieldMap,
    audit_wet_co2_literature_row,
    read_unresolved_wet_co2_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPILATION = ROOT / "data/raw/heterogeneous-wet-co2-corrosion/CO2.csv"
DEFAULT_EVIDENCE = ROOT / "data/evidence/wet-co2/abbas_2018_accepted_manuscript.pdf"
DEFAULT_OUTPUT = ROOT / "validation/wet_co2_literature_crosswalk.json"
SOURCE_DOI = "10.1016/j.psep.2018.07.006"
SOURCE_LICENSE = "CC-BY-NC-ND-4.0"


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _extract_appendix_rows(path: Path):
    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover - optional evidence-review dependency
        raise RuntimeError("pdfplumber is required to inspect caller-held PDF evidence") from error

    with pdfplumber.open(path) as document:
        if len(document.pages) != 27:
            raise ValueError("reviewed wet-CO2 evidence PDF page count changed")
        tables = document.pages[26].extract_tables()
    if len(tables) != 2 or [len(table) - 1 for table in tables] != [16, 6]:
        raise ValueError("reviewed wet-CO2 appendix table structure changed")
    rows = []
    for partition, table in zip(("training", "testing"), tables, strict=True):
        for index, cells in enumerate(table[1:], start=1):
            if len(cells) != 6:
                raise ValueError("reviewed wet-CO2 appendix column count changed")
            try:
                values = tuple(float(value) for value in cells[:5])
            except (TypeError, ValueError) as error:
                raise ValueError("reviewed wet-CO2 appendix contains a nonnumeric value") from error
            rows.append((partition, index, values))
    return rows


def _candidate_windows(compilation_rows, source_rows):
    windows = []
    for start in range(len(compilation_rows) - len(source_rows) + 1):
        if all(
            (
                compilation_rows[start + offset].raw_temperature,
                compilation_rows[start + offset].raw_flow_velocity,
                compilation_rows[start + offset].raw_ph,
                compilation_rows[start + offset].raw_corrosion_rate,
            )
            == (values[0], values[2], values[3], values[4])
            for offset, (_, _, values) in enumerate(source_rows)
        ):
            windows.append(start)
    return windows


def inspect(compilation_path=DEFAULT_COMPILATION, evidence_path=DEFAULT_EVIDENCE):
    compilation_path = Path(compilation_path)
    evidence_path = Path(evidence_path)
    compilation_rows = read_unresolved_wet_co2_compilation(compilation_path)
    source_rows = _extract_appendix_rows(evidence_path)
    windows = _candidate_windows(compilation_rows, source_rows)
    if len(windows) != 1:
        raise ValueError("wet-CO2 evidence does not have one unique four-field sequence candidate")

    maps = (
        WetCo2LiteratureFieldMap(
            compilation_field="raw_temperature",
            source_fields=("temperature_c",),
            operation="single_value_affine",
            reviewed_transform_basis_id=f"doi:{SOURCE_DOI}#appendix-temperature-celsius",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_co2_pressure",
            source_fields=("co2_pressure_mpa",),
            operation="single_value_affine",
            scale=10.0,
            reviewed_transform_basis_id=f"doi:{SOURCE_DOI}#appendix-mpa-to-compilation-bar",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_flow_velocity",
            source_fields=("flow_velocity_m_s",),
            operation="single_value_affine",
            reviewed_transform_basis_id=f"doi:{SOURCE_DOI}#appendix-flow-velocity",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_ph",
            source_fields=("ph",),
            operation="single_value_affine",
            reviewed_transform_basis_id=f"doi:{SOURCE_DOI}#appendix-ph",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_corrosion_rate",
            source_fields=("corrosion_rate_mm_y",),
            operation="single_value_affine",
            reviewed_transform_basis_id=f"doi:{SOURCE_DOI}#appendix-corrosion-rate",
        ),
    )
    evidence_hash = _digest(evidence_path)
    audits = []
    start = windows[0]
    for offset, (partition, source_index, values) in enumerate(source_rows):
        source = WetCo2LiteratureEvidenceRow(
            evidence_id=f"doi:{SOURCE_DOI}:appendix:{partition}:{source_index}",
            source_group_id=f"doi:{SOURCE_DOI}",
            source_record_id=f"{partition}-row-{source_index}",
            source_locator=f"appendix-{partition}-table-row-{source_index}",
            bibliographic_id=f"doi:{SOURCE_DOI}",
            bibliographic_link_status="primary_source_row",
            compilation_row_link_status="bibliographically_supported_numeric_sequence",
            compilation_row_link_basis_id=(
                "associated-compilation-citation-plus-unique-temperature-flow-ph-rate-sequence"
            ),
            evidence_asset_sha256=evidence_hash,
            source_values={
                "temperature_c": values[0],
                "co2_pressure_mpa": values[1],
                "flow_velocity_m_s": values[2],
                "ph": values[3],
                "corrosion_rate_mm_y": values[4],
            },
            source_data_role="experimental_autoclave_observation",
            publication_license_id=SOURCE_LICENSE,
            observation_redistribution_status="not_verified",
            data_dictionary_status="partial",
            physical_specimen_identity_status="unresolved",
        )
        audits.append(audit_wet_co2_literature_row(compilation_rows[start + offset], source, maps))

    counts = {
        field: Counter(
            comparison.status
            for audit in audits
            for comparison in audit.comparisons
            if comparison.compilation_field == field
        )
        for field in (mapping.compilation_field for mapping in maps)
    }
    pressure_discrepancies = []
    for audit in audits:
        comparison = next(item for item in audit.comparisons if item.compilation_field == "raw_co2_pressure")
        if comparison.status == "mismatch":
            pressure_discrepancies.append(
                {
                    "compilation_provider_source_row": audit.compilation_provider_source_row,
                    "source_value_mpa": comparison.source_values[0],
                    "transformed_source_value_bar": round(comparison.transformed_source_value, 12),
                    "compilation_value_bar": comparison.compilation_value,
                    "absolute_difference_bar": round(comparison.absolute_difference, 12),
                }
            )
    return {
        "schema": "matintegrity.wet_co2_literature_crosswalk_aggregate.v1",
        "compilation_dataset_id": "heterogeneous-wet-co2-corrosion",
        "compilation_sha256": compilation_rows[0].source_archive_sha256,
        "source_publication_doi": SOURCE_DOI,
        "source_publication_license": SOURCE_LICENSE,
        "source_asset_sha256": evidence_hash,
        "source_table_rows": len(source_rows),
        "source_partition_rows": dict(Counter(partition for partition, _, _ in source_rows)),
        "unique_sequence_candidate_windows": len(windows),
        "candidate_first_compilation_provider_source_row": audits[0].compilation_provider_source_row,
        "candidate_last_compilation_provider_source_row": audits[-1].compilation_provider_source_row,
        "comparison_status_by_field": {
            field: dict(sorted(field_counts.items())) for field, field_counts in counts.items()
        },
        "co2_pressure_discrepancies": pressure_discrepancies,
        "source_group_assignment_status": "candidate_not_qualified",
        "reason_not_qualified": (
            "The cited publication supplies 22 rows, while the associated compilation paper reports "
            "50 observations from that reference; three transformed pressure values also disagree."
        ),
        "physical_specimen_ids_available": False,
        "observation_redistribution_status": "not_verified",
        "automatic_correction_performed": False,
        "empirical_calibration_ready": False,
        "mechanistic_calibration_ready": False,
        "public_release_boundary": (
            "Only this aggregate audit is public. The caller-held publication and extracted point table "
            "remain outside distribution."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compilation", type=Path, default=DEFAULT_COMPILATION)
    parser.add_argument("--evidence-pdf", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = inspect(args.compilation, args.evidence_pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
