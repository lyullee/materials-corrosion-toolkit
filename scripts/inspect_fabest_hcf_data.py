"""Audit the pinned FABEST HCF package without extracting files or predicting blind outcomes."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/fabest-hcf-competition/FABEST_HCF_Zenodo_Release_v2_1_2_ZENODO.zip"
BLIND_MATRIX_SUFFIX = "04_Blind_Tests_Load_Matrix/FABEST_HCF_Blind_Load_Matrix.xlsx"
SUBMISSION_SUFFIX = "03_Submission_Templates/FABEST_HCF_Submission_Template.xlsx"
PROTOCOL_MEMBER_SUFFIXES = {
    "competition_rules": "01_Competition_Rules/FABEST_HCF_Competition_Rules.pdf",
    "experimental_setup": "06_Test_Protocols/_1_Experimental setup/FABEST_HCF_Experimental_Setup.pdf",
    "test_sequence": "06_Test_Protocols/_2_Test sequence/FABEST_HCF_Test_Sequence.pdf",
    "clarifications": "_CLARIFICATIONS & TECHNICAL Q&A/FABEST_HCF_Clarifications_Technical_QA.pdf",
}


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _member_with_suffix(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one archive member ending with {suffix!r}, found {len(matches)}")
    return matches[0]


def _formula_count(workbook) -> int:
    return sum(
        isinstance(cell.value, str) and cell.value.startswith("=")
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
    )


def inspect_fabest_hcf_package(path: Path = ARCHIVE) -> dict:
    payload = path.read_bytes()
    with ZipFile(io.BytesIO(payload)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        unsafe = [name for name in names if not _safe_member(name)]
        encrypted = [info.filename for info in infos if info.flag_bits & 0x1]
        blind_name = _member_with_suffix(names, BLIND_MATRIX_SUFFIX)
        submission_name = _member_with_suffix(names, SUBMISSION_SUFFIX)
        protocol_members = {
            key: _member_with_suffix(names, suffix) for key, suffix in PROTOCOL_MEMBER_SUFFIXES.items()
        }
        protocol_documents = {
            key: {
                "member": name,
                "bytes": len(content := archive.read(name)),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for key, name in protocol_members.items()
        }

        blind = openpyxl.load_workbook(
            io.BytesIO(archive.read(blind_name)), read_only=True, data_only=False, keep_links=False
        )
        submission = openpyxl.load_workbook(
            io.BytesIO(archive.read(submission_name)),
            read_only=True,
            data_only=False,
            keep_links=False,
        )
        try:
            matrix = blind["Blind_Strength_Matrix"]
            rows = [tuple(cell.value for cell in row) for row in matrix.iter_rows(min_row=2)]
            estimation = submission["Estimations"]
            submission_rows = [
                values
                for row in estimation.iter_rows(min_row=6)
                if (values := tuple(cell.value for cell in row)) and values[0] is not None
            ]
            case_ids = [row[0] for row in rows]
            submission_case_ids = [row[0] for row in submission_rows]
            result = {
                "source_id": "fabest-hcf-competition",
                "record_doi": "10.5281/zenodo.23532147",
                "package_version": "2.1.2",
                "source_sha256": hashlib.sha256(payload).hexdigest(),
                "source_md5": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
                "source_bytes": len(payload),
                "archive_members": len(infos),
                "archive_files": sum(not info.is_dir() for info in infos),
                "archive_uncompressed_bytes": sum(info.file_size for info in infos),
                "unsafe_member_paths": unsafe,
                "encrypted_members": encrypted,
                "extension_counts": dict(
                    sorted(
                        Counter(
                            PurePosixPath(info.filename).suffix.lower() or "<directory>" for info in infos
                        ).items()
                    )
                ),
                "blind_workbook_sheets": blind.sheetnames,
                "submission_workbook_sheets": submission.sheetnames,
                "workbook_formula_cells": _formula_count(blind) + _formula_count(submission),
                "blind_target_rows": len(rows),
                "case_ids_unique": len(case_ids) == len(set(case_ids)),
                "submission_case_ids_match": submission_case_ids == case_ids,
                "geometry_rows": dict(sorted(Counter(row[1] for row in rows).items())),
                "phase_angle_rows": dict(sorted(Counter(str(row[4]) for row in rows).items())),
                "target_life_rows": dict(sorted(Counter(str(row[6]) for row in rows).items())),
                "torsion_to_axial_amplitude_ratios": sorted({row[8] for row in rows}),
                "axial_load_ratios": sorted({row[9] for row in rows}),
                "torsional_load_ratios": sorted({row[10] for row in rows}),
                "internal_pressures_MPa": sorted({row[11] for row in rows}),
                "axial_frequencies_Hz": sorted({row[12] for row in rows}),
                "torsional_frequencies_Hz": sorted({row[13] for row in rows}),
                "empty_submission_outputs": sum(row[11] is None for row in submission_rows),
                "blind_outcome_status": "withheld_by_protocol",
                "protocol_documents": protocol_documents,
                "endpoint_protocol_review": {
                    "declared_pressure_drop_fraction_threshold": 0.1,
                    "pressure_drop_character": "abrupt",
                    "specimen_origin_confirmation_required": True,
                    "confirmed_specimen_event_kinds": [
                        "complete_rupture",
                        "through_thickness_crack",
                    ],
                    "endpoint_physical_meaning": "loss_of_specimen_pressure_integrity",
                    "complete_separation_required": False,
                    "runout_limit_cycles": 2_000_000,
                    "pressure_system_interruption_is_specimen_failure": False,
                    "same_intact_specimen_restart_permitted_after_system_recovery": True,
                    "cumulative_valid_loading_cycles_across_restarts": True,
                    "unconfirmed_specimen_integrity_or_loading_history": "invalid_or_ambiguous",
                    "blind_results_available": False,
                    "scope": (
                        "FABEST HCF competition package v2.1.2 only; not the separate FABEST "
                        "database workbook and not a material fatigue-life calibration."
                    ),
                },
                "qualification": (
                    "The archive defines a blind axial-torsion-pressure fatigue-strength exercise. "
                    "It supplies load cases, geometry/protocol documents and empty submission targets, "
                    "not observed target lives. It can verify input contracts and stress-state preparation "
                    "but cannot independently validate a fatigue criterion, strength curve or life model."
                ),
            }
        finally:
            blind.close()
            submission.close()

    expected = {
        "source_sha256": "bed23c7253197a226c5394a0eb6267193a2f7946e98478fc85effcb575666f7b",
        "source_md5": "c90b4de3006cefa9d294adac29cc32ee",
        "source_bytes": 46_329_584,
        "archive_members": 36,
        "archive_files": 15,
        "archive_uncompressed_bytes": 46_538_569,
        "unsafe_member_paths": [],
        "encrypted_members": [],
        "extension_counts": {".docx": 1, ".pdf": 11, ".tex": 1, ".xlsx": 2, "<directory>": 21},
        "workbook_formula_cells": 0,
        "blind_target_rows": 20,
        "case_ids_unique": True,
        "submission_case_ids_match": True,
        "geometry_rows": {"Notched": 10, "Plain": 10},
        "phase_angle_rows": {"0": 10, "90": 10},
        "target_life_rows": {"100000": 4, "20000": 4, "200000": 4, "50000": 4, "500000": 4},
        "torsion_to_axial_amplitude_ratios": [0.5773502691896258],
        "axial_load_ratios": [-1],
        "torsional_load_ratios": [-1],
        "internal_pressures_MPa": [60],
        "axial_frequencies_Hz": [10],
        "torsional_frequencies_Hz": [10],
        "empty_submission_outputs": 20,
        "blind_outcome_status": "withheld_by_protocol",
        "protocol_documents": {
            "competition_rules": {
                "member": (
                    "FABEST_HCF_Zenodo_Release_v2_1_2_ZENODO/01_Competition_Rules/"
                    "FABEST_HCF_Competition_Rules.pdf"
                ),
                "bytes": 252_301,
                "sha256": "72cdd49ce63fcbf5f1a1235e4eb9c0a83eadbc30544b3abd964b5bd947915844",
            },
            "experimental_setup": {
                "member": (
                    "FABEST_HCF_Zenodo_Release_v2_1_2_ZENODO/06_Test_Protocols/"
                    "_1_Experimental setup/FABEST_HCF_Experimental_Setup.pdf"
                ),
                "bytes": 40_570_741,
                "sha256": "88da25629b97766b56f4fb9100e7ebf097d7ccbcb051a2514232276cc417902f",
            },
            "test_sequence": {
                "member": (
                    "FABEST_HCF_Zenodo_Release_v2_1_2_ZENODO/06_Test_Protocols/"
                    "_2_Test sequence/FABEST_HCF_Test_Sequence.pdf"
                ),
                "bytes": 1_259_695,
                "sha256": "ac3a1e0e9aae3fbf0eb23f87bc311143fd8e62677a1dd82431b8a93ce63e67bd",
            },
            "clarifications": {
                "member": (
                    "FABEST_HCF_Zenodo_Release_v2_1_2_ZENODO/"
                    "_CLARIFICATIONS & TECHNICAL Q&A/FABEST_HCF_Clarifications_Technical_QA.pdf"
                ),
                "bytes": 176_477,
                "sha256": "4c913e7eb9604d0c8799c55b6d19d59119b76488387a0788b4130d2fe18932f9",
            },
        },
    }
    for key, value in expected.items():
        if result[key] != value:
            raise ValueError(f"pinned FABEST HCF package changed: {key}")
    return result


if __name__ == "__main__":
    report = json.dumps(inspect_fabest_hcf_package(), ensure_ascii=False, indent=2) + "\n"
    if len(sys.argv) == 1:
        print(report, end="")
    elif len(sys.argv) == 3 and sys.argv[1] == "--output":
        target = Path(sys.argv[2])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        print(target)
    else:
        raise SystemExit("usage: inspect_fabest_hcf_data.py [--output PATH]")
