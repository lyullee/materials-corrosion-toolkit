"""Audit a pinned coating-adhesion workbook without assigning units or qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.coating_adhesion_data import read_coating_adhesion_workbook

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "data/raw/zenodo-4777893-coating-adhesion/Adhesion strength.xlsx",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/coating_adhesion_data_audit.json",
    )
    args = parser.parse_args()
    audit = read_coating_adhesion_workbook(args.path)
    summary = {
        "schema": "matintegrity.coating_adhesion_data_audit_summary.v1",
        **audit.model_dump(mode="json"),
        "qualification": (
            "Raw replicate cells are preserved from the reviewed ADHESION sheet while formula summaries are "
            "excluded. The workbook and README do not declare the adhesion-strength unit, dolly area, force, "
            "break mode, instrument calibration or uncertainty. The substrate is wood. Values therefore remain "
            "provider-native and are not used to qualify metal coatings, derive stress, decide acceptance or "
            "create life or failure probability."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"groups": audit.group_count, "observations": audit.raw_observation_count}))


if __name__ == "__main__":
    main()
