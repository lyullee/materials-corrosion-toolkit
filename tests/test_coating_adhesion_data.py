from __future__ import annotations

import hashlib

import pytest
from openpyxl import Workbook

from matintegrity.coating_adhesion_data import read_coating_adhesion_workbook


def _workbook(tmp_path, *, bad_header=False, negative=False):
    path = tmp_path / "Adhesion strength.xlsx"
    workbook = Workbook()
    adhesion = workbook.active
    adhesion.title = "ADHESION"
    workbook.create_sheet("COLOR")
    workbook.create_sheet("pH and adhesion correlation")
    adhesion.cell(2, 1, "changed" if bad_header else "Sample")
    adhesion.cell(9, 1, "Primers + coatings")
    for row in range(3, 8):
        adhesion.cell(row, 1, f"SW{row}")
        columns = [2, 3, 4, 9, 10, 11, 14, 15, 16]
        if row == 5:
            columns = [2, 3, 4, 7, 8, 9, 10, 11, 14, 15]
        for column in columns:
            adhesion.cell(row, column, -1.0 if negative and row == 3 and column == 2 else 1.0)
    for row in (*range(12, 17), *range(18, 23), *range(24, 29), *range(30, 35)):
        adhesion.cell(row, 1, f"primer-{row}")
        for column in (2, 3, 4):
            adhesion.cell(row, column, 2.0)
    adhesion.cell(16, 5, 2.0)
    adhesion.cell(50, 24, None)
    workbook.save(path)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_preserves_native_replicates_and_unresolved_unit(tmp_path):
    path, digest = _workbook(tmp_path)
    audit = read_coating_adhesion_workbook(path, expected_sha256=digest)
    assert audit.group_count == 35
    assert audit.raw_observation_count == 107
    assert audit.unit_status == "withheld_no_source_unit_label"
    assert all(row.substrate == "wood" for row in audit.groups)
    assert all(
        row.interpretation_status == "raw_replicates_not_metal_coating_qualification" for row in audit.groups
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"bad_header": True}, "identity headers"), ({"negative": True}, "replicate group")],
)
def test_reader_rejects_changed_or_invalid_layout(tmp_path, kwargs, message):
    path, digest = _workbook(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        read_coating_adhesion_workbook(path, expected_sha256=digest)


def test_reader_rejects_digest_mismatch(tmp_path):
    path, _ = _workbook(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        read_coating_adhesion_workbook(path, expected_sha256="0" * 64)
