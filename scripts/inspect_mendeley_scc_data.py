"""Write aggregate structure evidence for the locally cached 304L SCC workbook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.nist_corr_data import audit_mendeley_scc_archive

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "data/raw/mendeley-304l-chloride-scc-salt-loading/processed-data.zip",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "validation/mendeley_scc_archive_audit.json")
    args = parser.parse_args()
    report = audit_mendeley_scc_archive(args.archive)
    target = args.output.resolve()
    if ROOT not in target.parents:
        raise ValueError("audit output must remain inside the project")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
