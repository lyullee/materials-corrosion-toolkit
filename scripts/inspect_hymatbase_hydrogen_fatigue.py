"""Audit the pinned HyMatBase 4130X hydrogen fracture/fatigue workbook."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from matintegrity.hydrogen_fatigue_data import audit_hymatbase_hydrogen_fatigue

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/hymatbase-4130x-hydrogen-fracture-fatigue/1211_NIB10_fra_fat.xlsx"
OUTPUT = ROOT / "validation/hymatbase_4130x_hydrogen_fatigue_audit.json"
SHA256 = "d8358b11538f35bd87c7512263b6e3907a48ffe28309a841c2974d3eaec3b528"


def main():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unknown extension is not supported")
        audit = audit_hymatbase_hydrogen_fatigue(
            SOURCE,
            expected_sha256=SHA256,
            source_group_id="hymatbase-j1e8n-2bz97",
            physical_material_condition_id="4130X-QT-SAND2012-7321",
            provider_record_pressure_Pa=4.5e6,
            provider_record_temperature_K=298.15,
            acknowledge_pressure_conflict=True,
        )
    payload = {
        **audit.model_dump(mode="json"),
        "dataset_id": "hymatbase-4130x-hydrogen-fracture-fatigue",
        "provider_record_url": "https://hymatbase.stfc.ac.uk/records/j1e8n-2bz97",
        "rights_status": "review_required_record_rights_section_blank",
        "redistribution": "excluded_from_public_packages",
        "qualification": (
            "Provider-reported curve points with no physical specimen identity in the workbook. The record and "
            "workbook pressure values conflict and remain separate. This audit does not establish test validity, "
            "independent observations, a design curve, component transfer, life or failure probability."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "series_count": audit.series_count,
                "point_count": audit.point_count,
                "pressure_reconciliation_status": audit.pressure_reconciliation_status,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
