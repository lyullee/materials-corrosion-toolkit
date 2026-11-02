"""Audit pinned cathodic-protection curves without assigning acceptance criteria."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.cathodic_protection_data import audit_cathodic_protection_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "data/raw/zenodo-18735817-cathodic-protection",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/cathodic_protection_data_audit.json",
    )
    args = parser.parse_args()
    _, audit = audit_cathodic_protection_dataset(args.path)
    summary = {
        "schema": "matintegrity.cathodic_protection_data_audit_summary.v1",
        **audit.model_dump(mode="json"),
        "qualification": (
            "Five provider DPlot exports are structurally audited with native axes. Open-circuit potential "
            "uses seconds and volts versus a calomel electrode. The potentiodynamic current-axis exponent is "
            "encoded ambiguously in the export, so it remains unresolved. Exposure chemistry, temperature, "
            "electrode subtype, instrument calibration, area normalization and uncertainty are not complete; "
            "therefore no protection criterion, corrosion current, rate, acceptance or probability is produced."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"curves": audit.curve_count, "samples": audit.total_samples}))


if __name__ == "__main__":
    main()
