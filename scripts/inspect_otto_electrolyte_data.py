"""Produce an aggregate-only audit of the locally acquired Otto dataset."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from matintegrity.otto_electrolyte_data import (
    DATASET_ATTRIBUTION,
    DATASET_DOI,
    DATASET_ID,
    DATASET_LICENSE,
    PINNED_ARCHIVE_BYTES,
    PINNED_ARCHIVE_SHA256,
    PINNED_JSON_MEMBER_BYTES,
    PINNED_JSON_MEMBER_SHA256,
    read_otto_electrolyte_archive,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/matr-aqueous-electrolytes/otto_data.zip"
OUTPUT = ROOT / "validation/otto_electrolyte_archive_audit.json"


def _range(values: list[float]) -> list[float] | None:
    finite = [value for value in values if math.isfinite(value)]
    return [min(finite), max(finite)] if finite else None


def audit() -> dict:
    records = read_otto_electrolyte_archive(ARCHIVE)
    run_types = Counter(row.run_type_as_reported for row in records)
    protocols = Counter(row.test_protocol_as_reported for row in records)
    trace_lengths = Counter(len(row.time_s) for row in records)
    derived_keys = Counter(
        key for row in records for key in row.reported_stability_metrics_V
    )
    times = [value for row in records for value in row.time_s]
    potentials = [value for row in records for value in row.potential_V_as_reported]
    currents = [value for row in records for value in row.signed_current_density_mA_cm2]
    return {
        "schema_version": "matintegrity.otto_electrolyte_archive_audit.v1",
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "dataset_license": DATASET_LICENSE,
        "attribution": DATASET_ATTRIBUTION,
        "archive_sha256_local_snapshot": PINNED_ARCHIVE_SHA256,
        "archive_bytes": PINNED_ARCHIVE_BYTES,
        "provider_archive_checksum_published": False,
        "json_member": "otto_data/otto_aqueous.json",
        "json_member_bytes": PINNED_JSON_MEMBER_BYTES,
        "json_member_sha256_local_snapshot": PINNED_JSON_MEMBER_SHA256,
        "record_count": len(records),
        "unique_record_id_count": len({row.record_id for row in records}),
        "unique_run_id_count": len({row.source_run_id for row in records}),
        "run_type_counts": dict(sorted(run_types.items())),
        "protocol_counts": dict(sorted(protocols.items())),
        "trace_length_counts": {str(key): value for key, value in sorted(trace_lengths.items())},
        "elapsed_time_s_range": _range(times),
        "reported_pH_range": _range([row.pH_reported_value for row in records]),
        "temperature_provider_native_range": _range([row.temperature_reported_value for row in records]),
        "conductivity_provider_native_range": _range([row.conductivity_reported_value for row in records]),
        "potential_V_reported_range": _range(potentials),
        "signed_current_density_mA_cm2_range": _range(currents),
        "derived_metric_presence_counts": dict(sorted(derived_keys.items())),
        "current_time_voltage_arrays_aligned": all(
            len(row.time_s) == len(row.potential_V_as_reported) == len(row.signed_current_density_mA_cm2)
            for row in records
        ),
        "corrosion_polarization_curves_created": False,
        "corrosion_calibration_performed": False,
        "pointwise_values_emitted": False,
        "interpretation": (
            "Provider records are fixed-current electrolyte-stability traces on platinum. They are not converted into corrosion polarization curves or corrosion calibration data."
        ),
        "qualification": "dataset structure and lineage audit only; no corrosion interpretation or physical qualification",
    }


def main() -> None:
    report = audit()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
