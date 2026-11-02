"""Audit selected controlled-source acoustic-emission text assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.controlled_ae_data import audit_controlled_wire_cut_ae

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "data/raw/zenodo-22011152-controlled-wire-cut-ae",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/controlled_ae_data_audit.json",
    )
    args = parser.parse_args()
    audit = audit_controlled_wire_cut_ae(args.path)
    summary = {
        "schema": "matintegrity.controlled_ae_data_audit_summary.v1",
        **audit.model_dump(mode="json"),
        "qualification": (
            "Selected provider text assets preserve four sensor coordinates, two provider wire coordinates, "
            "eleven 5 MHz waveforms and the event-feature row inventory. Waveform groups C_A2 and C_I2 lack "
            "matching source coordinates, C_I1 has no selected waveform, and C_A2 lacks channel 10. No arrival "
            "picks, wave-speed calibration or common event grouping are inferred, so localization, mechanism, "
            "severity, acceptance, life, POD and failure probability remain withheld."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"waveforms": audit.waveform_count, "samples": audit.total_waveform_samples}))


if __name__ == "__main__":
    main()
