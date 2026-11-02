"""Audit the pinned paired critical-plane dataset without treating processed rows as new specimens."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from matintegrity.multiaxial_fatigue_data import read_ecp_multiaxial_fatigue

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/raw/ecp-multiaxial-fatigue"


def inspect(directory: Path = DIRECTORY) -> dict:
    loaded = read_ecp_multiaxial_fatigue(directory)
    configurations = loaded["configurations"]
    observations = loaded["experimental_observations"]
    processed = loaded["processed_method_rows"]
    files = sorted(directory.glob("*.txt"))
    report = {
        "source_id": loaded["source_id"],
        "record_doi": "10.5281/zenodo.14198237",
        "license": "CC-BY-4.0",
        "files": len(files),
        "source_bytes": sum(path.stat().st_size for path in files),
        "file_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "configurations": len(configurations),
        "experimental_observations": len(observations),
        "processed_method_rows": len(processed),
        "method_rows": dict(sorted(Counter(processed.method).items())),
        "provider_load_codes": dict(sorted(Counter(configurations.provider_load_code).items())),
        "specimen_geometry_codes": dict(sorted(Counter(configurations.specimen_geometry_code).items())),
        "phase_angle_rows": dict(
            sorted(Counter(str(value) for value in configurations.phase_angle_deg).items())
        ),
        "stress_ratio_rows": dict(
            sorted(Counter(str(value) for value in configurations.stress_ratio).items())
        ),
        "minimum_reported_cycles": float(observations.reported_cycles_to_failure.min()),
        "maximum_reported_cycles": float(observations.reported_cycles_to_failure.max()),
        "physical_specimen_ids_supplied": int(observations.physical_specimen_id.notna().sum()),
        "censoring_flags_supplied": 0,
        "endpoint_definition_status": "requires_linked_article_review",
        "qualification": loaded["qualification"],
    }
    expected = {
        "files": 28,
        "source_bytes": 9032,
        "configurations": 14,
        "experimental_observations": 147,
        "processed_method_rows": 294,
        "method_rows": {"FS": 147, "SWT": 147},
        "provider_load_codes": {"ASS": 4, "MULTI": 7, "TOR": 3},
        "specimen_geometry_codes": {"BLUNT": 9, "SHARP": 5},
        "physical_specimen_ids_supplied": 0,
        "censoring_flags_supplied": 0,
    }
    for key, value in expected.items():
        if report[key] != value:
            raise ValueError(f"pinned ECP multiaxial dataset changed: {key}")
    return report


if __name__ == "__main__":
    target = ROOT / "validation/ecp_multiaxial_dataset.json"
    target.write_text(json.dumps(inspect(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
