"""Read the pinned Aalto Oxford EBSD archive and emit aggregate, non-pointwise diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from matintegrity.oxford_ebsd import read_oxford_ebsd_phase_labels

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/aalto-low-alloy-weld-ebsd-maps/low_alloy_steel_weld_metals_EBSD.zip"
ARCHIVE_SHA256 = "9c02bf44f8bd34afff432e6f78d0bd4cf176a75a544fb18ac6d83938a667c436"
EXPECTED_SHAPE = (934, 1245)
EXPECTED_GRID_STEP = 0.1


def main() -> None:
    maps = []
    for basename in ("CV_3", "HY_1", "LA_1"):
        loaded = read_oxford_ebsd_phase_labels(
            ARCHIVE,
            basename,
            expected_archive_sha256=ARCHIVE_SHA256,
        )
        if loaded.record.shape != EXPECTED_SHAPE:
            raise AssertionError(f"{basename} map shape differs from the provider metadata audit")
        if loaded.record.provider_grid_step_value != EXPECTED_GRID_STEP:
            raise AssertionError(f"{basename} grid step differs from the provider metadata audit")
        counts = {
            str(int(value)): int(count)
            for value, count in zip(*np.unique(loaded.labels, return_counts=True), strict=True)
        }
        if sum(counts.values()) != loaded.labels.size:
            raise AssertionError(f"{basename} label histogram does not close to the reader map size")
        maps.append(
            {
                "map_id": basename,
                "shape": loaded.record.shape,
                "grid_step_value": loaded.record.provider_grid_step_value,
                "grid_step_unit_status": loaded.record.provider_grid_step_unit_status,
                "label_array_sha256": loaded.record.label_array_sha256,
                "cpr_member_sha256": loaded.record.cpr_member_sha256,
                "crc_member_sha256": loaded.record.crc_member_sha256,
                "label_pixel_counts": counts,
                "nonindexed_label_value": loaded.record.nonindexed_label_value,
                "reader_name": loaded.record.reader_name,
                "reader_version": loaded.record.reader_version,
                "reader_compatibility_patch": loaded.record.reader_compatibility_patch,
            }
        )
    report = {
        "schema_version": "matintegrity.oxford_ebsd_provider_reader_validation.v1",
        "dataset": "Aalto low-alloy weld-metal EBSD maps",
        "doi": "10.5281/zenodo.5054204",
        "license": "CC-BY-4.0",
        "archive_sha256": ARCHIVE_SHA256,
        "checks": {
            "all_three_maps_read": True,
            "provider_shape_match": True,
            "provider_grid_step_match": True,
            "per_map_histogram_closes": True,
            "pointwise_labels_written": False,
            "physical_grid_units_inferred": False,
            "phase_identity_inferred": False,
        },
        "maps": maps,
        "qualification_limit": "Format-reader integration and aggregate label accounting only; no map registration, phase identity, physical area, uncertainty, specimen qualification, or corrosion response is established.",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
