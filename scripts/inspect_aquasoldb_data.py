"""Aggregate-only audit of locally held AquaSolDB v2.1 CO2 observations."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from matintegrity.aquasoldb_data import (
    DATASET_ID,
    DATASET_LICENSE,
    DATASET_VERSION_DOI,
    PINNED_ARCHIVE_BYTES,
    PINNED_ARCHIVE_MD5,
    PINNED_ARCHIVE_SHA256,
    iter_aquasoldb_co2_solubility,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/aquasoldb-gas-solubility-v2-1/AquaSolDB-v2.1.zip"
OUTPUT = ROOT / "validation/aquasoldb_co2_archive_audit.json"


def audit() -> dict:
    records = tuple(iter_aquasoldb_co2_solubility(ARCHIVE))
    flags = Counter(flag for row in records for flag in row.flags)
    numeric = [row for row in records if row.solubility_mol_per_kg_water is not None]
    conservative_scope = [
        row
        for row in records
        if row.status == "measured"
        and row.temperature_K is not None
        and row.pressure_MPa is not None
        and row.salt == "none"
        and row.pressure_basis == "partial_CO2"
        and row.pressure_MPa <= 0.1
        and not row.flags
    ]
    return {
        "schema_version": "matintegrity.aquasoldb_co2_archive_audit.v1",
        "checked_on": "2026-10-29",
        "dataset_id": DATASET_ID,
        "dataset_version_doi": DATASET_VERSION_DOI,
        "compilation_license_scope": DATASET_LICENSE,
        "attribution": "Abd, A.; Abushaikha, A. (2026), AquaSolDB v2.1",
        "archive_path": "data/raw/aquasoldb-gas-solubility-v2-1/AquaSolDB-v2.1.zip",
        "archive_bytes": PINNED_ARCHIVE_BYTES,
        "archive_md5": PINNED_ARCHIVE_MD5,
        "archive_sha256": PINNED_ARCHIVE_SHA256,
        "co2_solubility_record_count": len(records),
        "status_counts": dict(sorted(Counter(row.status for row in records).items())),
        "pressure_basis_counts": dict(sorted(Counter(row.pressure_basis for row in records).items())),
        "medium_counts": dict(sorted(Counter(row.salt for row in records).items())),
        "method_class_counts": dict(sorted(Counter(row.method for row in records).items())),
        "flag_counts": dict(sorted(flags.items())),
        "records_with_any_missing_ion_composition": sum(
            all(
                value is None
                for value in (
                    row.sodium_molality_mol_per_kgw,
                    row.chloride_molality_mol_per_kgw,
                    row.potassium_molality_mol_per_kgw,
                    row.calcium_molality_mol_per_kgw,
                    row.magnesium_molality_mol_per_kgw,
                    row.sulfate_molality_mol_per_kgw,
                )
            )
            for row in records
        ),
        "records_missing_temperature": sum(row.temperature_K is None for row in records),
        "records_missing_pressure": sum(row.pressure_MPa is None for row in records),
        "numeric_solubility_range_mol_per_kg_water": [
            min(row.solubility_mol_per_kg_water for row in numeric),
            max(row.solubility_mol_per_kg_water for row in numeric),
        ],
        "temperature_range_K": [
            min(row.temperature_K for row in records if row.temperature_K is not None),
            max(row.temperature_K for row in records if row.temperature_K is not None),
        ],
        "pressure_range_MPa": [
            min(row.pressure_MPa for row in records if row.pressure_MPa is not None),
            max(row.pressure_MPa for row in records if row.pressure_MPa is not None),
        ],
        "diagnostic_low_pressure_pure_water_unflagged_count": len(conservative_scope),
        "diagnostic_low_pressure_candidate_source_count": len({row.source_id for row in conservative_scope}),
        "diagnostic_scope_definition": {
            "status": "measured",
            "medium": "none",
            "pressure_basis": "partial_CO2",
            "pressure_ceiling_MPa": 0.1,
            "flags": "empty",
        },
        "diagnostic_scope_is_not_thermodynamic_qualification": True,
        "henry_coefficients_derived": False,
        "corrosion_calibration_performed": False,
        "pointwise_values_or_source_citations_included": False,
        "rights_status": (
            "CC-BY-4.0 covers the compilation only; original measurement paper rights and citations "
            "remain record-specific"
        ),
        "qualification": (
            "Aggregate archive audit only. Pressure-defined dissolved concentrations cannot be used as "
            "Henry coefficients without source-level review of fugacity, solvent density, chemistry, "
            "uncertainty and the original paper. No corrosion model was fitted."
        ),
    }


def main() -> None:
    report = audit()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
