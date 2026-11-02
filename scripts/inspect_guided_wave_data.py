"""Audit the pinned guided-wave archive without treating amplitudes as wall-thickness truth."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from matintegrity.guided_wave_data import (
    ARTICLE_REPORTED_MATRIX_SHAPE,
    GUIDED_WAVE_ARCHIVE_SHA256,
    iter_guided_wave_acquisitions,
    list_guided_wave_acquisitions,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/guided-wave-pipeline-shm/ttb63krg6d-1.zip"


def _grid_digest(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<f8").tobytes()).hexdigest()


def inspect(path: Path = ARCHIVE) -> dict:
    inventory = list_guided_wave_acquisitions(path)
    acquisition_ids = [row["acquisition_id"] for row in inventory["acquisitions"]]
    missing_ids = [
        value
        for value in range(min(acquisition_ids), max(acquisition_ids) + 1)
        if value not in set(acquisition_ids)
    ]
    frequency_records = Counter()
    matrix_shapes = Counter()
    raw_window_labels = Counter()
    sheet_orders = Counter()
    distance_grids = Counter()
    workbook_digest_lines = []
    numeric_sample_rows = 0
    signal_records = 0
    repeated_distance_intervals = 0
    article_shape_discrepancies = 0
    provider_dac_nonzero_samples = 0
    channel_minimum = {
        "torsional_V": float("inf"),
        "flexural_V": float("inf"),
        "provider_pure_dac_V": float("inf"),
    }
    channel_maximum = {
        "torsional_V": float("-inf"),
        "flexural_V": float("-inf"),
        "provider_pure_dac_V": float("-inf"),
    }

    for acquisition in iter_guided_wave_acquisitions(path, specimen_id="published-single-steel-tube"):
        workbook_digest_lines.append(f"{acquisition['acquisition_id']}:{acquisition['workbook_sha256']}")
        sheet_orders[
            ",".join(str(int(value)) for value in acquisition["source_sheet_frequency_order_Hz"])
        ] += 1
        for signal in acquisition["signals"]:
            signal_records += 1
            frequency_records[str(int(signal["frequency_Hz"]))] += 1
            matrix_shapes[f"{signal['source_matrix_shape'][0]}x{signal['source_matrix_shape'][1]}"] += 1
            raw_window_labels[signal["raw_window_label"]] += 1
            distance_grids[_grid_digest(signal["distance_m"])] += 1
            numeric_sample_rows += signal["numeric_sample_rows"]
            repeated_distance_intervals += signal["repeated_distance_intervals"]
            article_shape_discrepancies += int(signal["article_shape_discrepancy"])
            dac = signal["provider_pure_dac_V"]
            provider_dac_nonzero_samples += int(np.count_nonzero(dac))
            for channel in channel_minimum:
                values = signal[channel]
                channel_minimum[channel] = min(channel_minimum[channel], float(np.min(values)))
                channel_maximum[channel] = max(channel_maximum[channel], float(np.max(values)))

    periods = Counter(row["article_period_group"] for row in inventory["acquisitions"])
    report = {
        "schema_version": "matintegrity.validation.guided_wave_pipeline_dataset.v1",
        "source_id": "guided-wave-pipeline-shm",
        "record_doi": "10.17632/ttb63krg6d.1",
        "license": "CC-BY-4.0",
        "outer_archive_sha256": inventory["outer_archive_sha256"],
        "outer_archive_bytes": inventory["outer_archive_bytes"],
        "nested_archive_sha256": inventory["nested_archive_sha256"],
        "nested_archive_bytes": inventory["nested_archive_bytes"],
        "workbook_manifest_sha256": hashlib.sha256(
            "\n".join(workbook_digest_lines).encode("utf-8")
        ).hexdigest(),
        "acquisitions": len(acquisition_ids),
        "minimum_acquisition_id": min(acquisition_ids),
        "maximum_acquisition_id": max(acquisition_ids),
        "missing_acquisition_ids_within_range": missing_ids,
        "article_period_groups": dict(sorted(periods.items())),
        "physical_specimens_reported": 1,
        "signal_records": signal_records,
        "frequency_records_Hz": dict(sorted(frequency_records.items(), key=lambda row: int(row[0]))),
        "distinct_source_sheet_orders": len(sheet_orders),
        "source_sheet_order_counts": dict(sorted(sheet_orders.items())),
        "matrix_shape_records": dict(sorted(matrix_shapes.items())),
        "numeric_sample_rows": numeric_sample_rows,
        "distance_grid_digests": dict(sorted(distance_grids.items())),
        "repeated_distance_intervals": repeated_distance_intervals,
        "raw_window_label_counts": dict(sorted(raw_window_labels.items())),
        "provider_dac_nonzero_samples": provider_dac_nonzero_samples,
        "channel_minimum_V": channel_minimum,
        "channel_maximum_V": channel_maximum,
        "article_reported_matrix_shape": list(ARTICLE_REPORTED_MATRIX_SHAPE),
        "actual_matrix_shape": [2509, 4],
        "article_shape_discrepancy_records": article_shape_discrepancies,
        "timestamps_supplied_in_workbooks": 0,
        "temperatures_supplied_in_workbooks": 0,
        "machining_step_mapping_resolved": False,
        "remaining_wall_thickness_supplied": False,
        "qualification": (
            "All voltage matrices are structural-health-monitoring responses from one reported laboratory "
            "tube. The final 29 acquisitions follow staged machining, not natural corrosion growth. The "
            "archive does not map files to the six machining steps or supply direct remaining thickness, "
            "timestamps or temperatures. Provider DAC remains a separate processed channel. Article text "
            "reports 2057 by 4 matrices, while every workbook sheet inspected has 2509 by 4 cells including "
            "two metadata rows; this discrepancy is retained rather than corrected."
        ),
    }
    expected = {
        "outer_archive_sha256": GUIDED_WAVE_ARCHIVE_SHA256,
        "outer_archive_bytes": 103000407,
        "nested_archive_bytes": 106412391,
        "acquisitions": 236,
        "minimum_acquisition_id": 1622,
        "maximum_acquisition_id": 1930,
        "article_period_groups": {"post_machining_period": 29, "reported_healthy_period": 207},
        "physical_specimens_reported": 1,
        "signal_records": 1180,
        "frequency_records_Hz": {
            "14000": 236,
            "18000": 236,
            "24000": 236,
            "30000": 236,
            "37000": 236,
        },
        "matrix_shape_records": {"2509x4": 1180},
        "numeric_sample_rows": 2958260,
        "repeated_distance_intervals": 1180,
        "article_shape_discrepancy_records": 1180,
        "timestamps_supplied_in_workbooks": 0,
        "temperatures_supplied_in_workbooks": 0,
        "machining_step_mapping_resolved": False,
        "remaining_wall_thickness_supplied": False,
    }
    for key, value in expected.items():
        if report[key] != value:
            raise ValueError(f"pinned guided-wave dataset changed: {key}")
    return report


if __name__ == "__main__":
    target = ROOT / "validation/guided_wave_pipeline_dataset.json"
    target.write_text(json.dumps(inspect(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
