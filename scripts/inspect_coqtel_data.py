"""Inspect pinned COQTEL experiments without publishing waveforms, images or point rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.signals import (
    coqtel_waveform,
    inspect_coqtel_experiment,
    waveform_change,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/raw/coqtel"
DEFAULT_OUTPUT = ROOT / "validation/coqtel_dataset.json"


def inspect(directory=DEFAULT_INPUT):
    directory = Path(directory)
    experiments = []
    for path in sorted(directory.glob("*.h5")):
        report = inspect_coqtel_experiment(path)
        first = coqtel_waveform(
            path,
            state=1,
            actuator=1,
            sensor=4,
            require_pinned_hash=True,
        )
        last = coqtel_waveform(
            path,
            state=report["state_count"],
            actuator=1,
            sensor=4,
            require_pinned_hash=True,
        )
        report["first_to_last_selected_path_change"] = waveform_change(first, last)
        experiments.append(report)
    if len(experiments) != 2 or {item["experiment_id"] for item in experiments} != {
        "coqtel-experiment-1",
        "coqtel-experiment-2",
    }:
        raise ValueError("expected exactly the two pinned COQTEL experiments")
    return {
        "schema": "matintegrity.coqtel_dataset_aggregate.v1",
        "dataset_id": "coqtel",
        "dataset_doi": "10.5281/zenodo.14193336",
        "article_doi": "10.1016/j.dib.2025.111393",
        "license": "CC-BY-4.0",
        "independent_physical_specimens": 2,
        "experiments": experiments,
        "total_states": sum(item["state_count"] for item in experiments),
        "total_waveform_records": sum(item["waveform_records"] for item in experiments),
        "state_resolved_pit_dimensions_available": False,
        "empirical_pit_sizing_calibration_ready": False,
        "pod_calibration_ready": False,
        "remaining_life_calibration_ready": False,
        "public_release_boundary": (
            "Only this aggregate audit and independently authored readers are public. Raw HDF5 "
            "waveforms, electrochemical rows and images remain outside source distributions."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = inspect(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
