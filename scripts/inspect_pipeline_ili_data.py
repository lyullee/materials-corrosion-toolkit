"""Audit every cell in the four pinned consecutive-ILI workbooks."""

from __future__ import annotations

import json
from pathlib import Path

from matintegrity.pipeline_ili_data import audit_pipeline_ili_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/cross-country-pipeline-ili-history"
OUTPUT = ROOT / "validation/pipeline_ili_history_audit.json"
FILES = {
    "External Features Year One.xlsx": (
        1,
        "68dc9b2b651f07f27b8f3a28d24f3909f74e505f9da17fa8782e750f0c3db49f",
    ),
    "External Features Year Three.xlsx": (
        3,
        "3622b9d5689e504bd09c3cf389e2fc2b1c638fb50d13a0b290d84f3464a2f611",
    ),
    "External Features Year Five.xlsx": (
        5,
        "2e948c8f23aa0668e57798c03e4ac9b34b617c89599631c8e93da1601d63d31c",
    ),
    "External Features Year Seven.xlsx": (
        7,
        "37128dfb91f40325314af71cb4e8771e76577ef3ca0f75ed5020f771b8cab462",
    ),
}


def main():
    audits = []
    for filename, (year, digest) in FILES.items():
        audit = audit_pipeline_ili_workbook(
            DATA / filename,
            expected_inspection_year_token=year,
            expected_sha256=digest,
        )
        audits.append(audit.model_dump(mode="json"))
    payload = {
        "schema_version": "matintegrity.validation.pipeline_ili_history_audit.v1",
        "dataset_id": "cross-country-pipeline-ili-history",
        "observation_count": sum(item["observation_count"] for item in audits),
        "source_bytes": sum(item["source_bytes"] for item in audits),
        "inspection_year_tokens": [1, 3, 5, 7],
        "workbooks": audits,
        "qualification": (
            "Processed and filtered provider observations with ordinal inspection-year tokens; not raw MFL flux, "
            "real asset age, independent physical feature tracks, excavation truth, growth calibration, sizing "
            "accuracy, POD or acceptance qualification."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "observation_count": payload["observation_count"],
                "source_bytes": payload["source_bytes"],
                "inspection_year_tokens": payload["inspection_year_tokens"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
