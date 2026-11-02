"""Audit the acquired BAM eddy-current archives after safe external extraction."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from matintegrity.eddy_current_data import read_eddy_current_diconde

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "bam-compound-defect-eddy-current"
SIMULATION_ARCHIVE_SHA256 = "56350631379d7d5de013ce959bf4045656140fb0327f7fc85e38629d94d2405e"
LABORATORY_ARCHIVE_SHA256 = "a393b25a7435f63f2a2cac6c9db628c294dcd3eb42cf0ff6ce62ce590683c5ef"
EXPECTED_HEADER = ["y position in mm", "Re voltage in V", "Im voltage in V", "total rel. acc"]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inspect(archive_root: Path, extracted_root: Path) -> dict:
    simulation_archive = archive_root / "Simulation Data.7z"
    laboratory_archive = archive_root / "Laboratory Data.7z"
    if digest(simulation_archive) != SIMULATION_ARCHIVE_SHA256:
        raise ValueError("simulation archive digest changed")
    if digest(laboratory_archive) != LABORATORY_ARCHIVE_SHA256:
        raise ValueError("laboratory archive digest changed")

    simulation_root = extracted_root / "Simulation Data"
    simulation_rows = []
    for path in sorted(simulation_root.rglob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        if not rows or rows[0] != EXPECTED_HEADER:
            raise ValueError(f"simulation CSV header changed: {path.name}")
        numeric = []
        for row_number, row in enumerate(rows[1:], 2):
            if len(row) not in {3, 4} or (len(row) == 4 and row[3].strip()):
                raise ValueError(f"unexpected simulation CSV field at {path.name}:{row_number}")
            values = [float(value) for value in row[:3]]
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"nonfinite simulation value at {path.name}:{row_number}")
            numeric.append(values)
        positions = [row[0] for row in numeric]
        if any(right >= left for left, right in zip(positions, positions[1:], strict=False)):
            raise ValueError(f"simulation positions are not strictly decreasing: {path.name}")
        simulation_rows.append(
            {
                "member": path.relative_to(extracted_root).as_posix(),
                "sha256": digest(path),
                "rows": len(numeric),
                "position_min_mm": min(positions),
                "position_max_mm": max(positions),
                "fourth_header_has_no_row_values": all(
                    len(row) == 3 or not row[3].strip() for row in rows[1:]
                ),
            }
        )
    if len(simulation_rows) != 12:
        raise ValueError("expected twelve simulation CSV members")

    laboratory_root = extracted_root / "Laboratory Data"
    laboratory_rows = []
    slope_values = []
    for path in sorted(laboratory_root.glob("*.dcm")):
        result = read_eddy_current_diconde(
            path,
            physical_specimen_id="published-laboratory-series-physical-independence-unresolved",
            source_role="laboratory_observation",
            component_order=("provider_real_component", "provider_imaginary_component"),
            component_order_basis="Zenodo record states first frame real and second frame imaginary",
        )
        metadata = result["metadata"]
        slope_values.extend(value for value in metadata.frame_rescale_slopes if value is not None)
        laboratory_rows.append(
            {
                "filename": metadata.source_filename,
                "sha256": metadata.source_sha256,
                "bytes": metadata.source_bytes,
                "sop_instance_uid": metadata.sop_instance_uid,
                "shape": [metadata.frame_count, metadata.rows, metadata.columns],
                "excitation_frequency_Hz": metadata.excitation_frequency_Hz,
                "coordinate_sources_agree": metadata.coordinate_sources_agree,
                "padding_count_by_component": metadata.padding_count_by_component,
                "decode_warning_messages": metadata.decode_warning_messages,
            }
        )
    if len(laboratory_rows) != 10:
        raise ValueError("expected ten laboratory DICONDE members")
    if len({row["sop_instance_uid"] for row in laboratory_rows}) != len(laboratory_rows):
        raise ValueError("laboratory DICONDE SOP instance UIDs must be unique")

    return {
        "schema_version": "matintegrity.validation.eddy_current_dataset_audit.v1",
        "dataset_id": DATASET_ID,
        "archives": {
            "simulation": {
                "sha256": SIMULATION_ARCHIVE_SHA256,
                "bytes": simulation_archive.stat().st_size,
            },
            "laboratory": {
                "sha256": LABORATORY_ARCHIVE_SHA256,
                "bytes": laboratory_archive.stat().st_size,
            },
        },
        "simulation": {
            "file_count": len(simulation_rows),
            "row_count_distribution": dict(sorted(Counter(row["rows"] for row in simulation_rows).items())),
            "members": simulation_rows,
            "role": "commercial_solver_outputs_not_physical_observations",
        },
        "laboratory": {
            "file_count": len(laboratory_rows),
            "shape_set": sorted({tuple(row["shape"]) for row in laboratory_rows}),
            "excitation_frequency_Hz_set": sorted(
                {row["excitation_frequency_Hz"] for row in laboratory_rows}
            ),
            "all_coordinate_sources_agree": all(
                row["coordinate_sources_agree"] is True for row in laboratory_rows
            ),
            "frame_rescale_slope_range": [min(slope_values), max(slope_values)],
            "files_with_decode_warnings": sum(
                bool(row["decode_warning_messages"]) for row in laboratory_rows
            ),
            "files": laboratory_rows,
            "physical_specimen_independence": "unresolved",
        },
        "qualification": (
            "File structure, hashes and DICONDE contracts only. Provider filenames/comments are not promoted to independently verified flaw dimensions, physical specimen IDs, calibration, POD or acceptance evidence."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive-root", type=Path, default=ROOT / "data/raw/bam-compound-defect-eddy-current"
    )
    parser.add_argument("--extracted-root", type=Path, default=ROOT / "tmp/eddy-current-review")
    parser.add_argument("--output", type=Path, default=ROOT / "validation/eddy_current_dataset_audit.json")
    args = parser.parse_args()
    result = inspect(args.archive_root, args.extracted_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"simulation_files": 12, "laboratory_files": 10}, indent=2))


if __name__ == "__main__":
    main()
