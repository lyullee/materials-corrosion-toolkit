from __future__ import annotations

import csv
import io
import zipfile

import pytest

from matintegrity.nist_corr_data import (
    ARCHIVE_BYTES,
    EXPECTED_HEADER,
    _summarize_archive_bytes,
    _summarize_mendeley_scc_archive_bytes,
    audit_nist_corr_data_archive,
)


def _archive(csv_text: str, *, header: tuple[str, ...] = EXPECTED_HEADER) -> bytes:
    contents = io.StringIO(newline="")
    writer = csv.writer(contents)
    writer.writerow(header)
    writer.writerow(
        [
            "synthetic environment",
            "synthetic group",
            "synthetic family",
            "synthetic alloy",
            "0.12",
            "4.72",
            "",
            "",
            "",
            "10",
            "25",
            "77",
            "",
            "R-1",
            "synthetic citation",
        ]
    )
    csv_text = contents.getvalue() if not csv_text else csv_text
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("CORR-DATA_Database.csv", csv_text)
        archive.writestr("about-CORR-DATA_Database.txt", "synthetic metadata")
        archive.writestr("columnDefinitions.txt", "synthetic definitions")
    return result.getvalue()


def _csv_row(**overrides: str) -> str:
    row = {field: "synthetic" for field in EXPECTED_HEADER}
    row.update(overrides)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=EXPECTED_HEADER)
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def test_structure_audit_counts_rows_and_marks_mixed_value_tokens_only():
    archive = _archive(
        _csv_row(
            **{
                "Rate (mm/yr) or Rating": "0.12",
                "Rate (mils/yr) or Rating": "B",
                "Reference #": "R-1",
                "Temperature (deg C)": "25",
                "Duration": "",
            }
        )
    )
    summary = _summarize_archive_bytes(archive)
    assert summary["record_count"] == 1
    assert summary["row_widths"] == {"15": 1}
    assert summary["token_classes"]["Rate (mm/yr) or Rating"] == {"numeric_scalar": 1}
    assert summary["token_classes"]["Rate (mils/yr) or Rating"] == {"qualitative_rating_code": 1}
    assert summary["reference_key_count"] == 1
    assert "synthetic citation" not in repr(summary)


def test_structure_audit_rejects_schema_or_archive_member_drift():
    with pytest.raises(ValueError, match="header"):
        _summarize_archive_bytes(_archive("", header=EXPECTED_HEADER[:-1]))

    malformed = io.BytesIO()
    with zipfile.ZipFile(malformed, "w") as archive:
        archive.writestr("unexpected.csv", "x")
    with pytest.raises(ValueError, match="members"):
        _summarize_archive_bytes(malformed.getvalue())


def test_pinned_audit_rejects_unmanifested_archive(tmp_path):
    path = tmp_path / "CORR-DATA_Database.zip"
    path.write_bytes(b"wrong")
    assert ARCHIVE_BYTES > path.stat().st_size
    with pytest.raises(ValueError, match="byte size"):
        audit_nist_corr_data_archive(path)


def test_scc_archive_audit_reports_structure_without_workbook_values(tmp_path):
    import openpyxl

    workbook_buffer = io.BytesIO()
    workbook = openpyxl.Workbook()
    workbook.active.title = "Synthetic"
    workbook.active["A1"] = "synthetic-only-label"
    workbook.active["A2"] = "=1+1"
    workbook.save(workbook_buffer)
    inner_buffer = io.BytesIO()
    with zipfile.ZipFile(inner_buffer, "w") as inner:
        inner.writestr(
            "Processed data/Salt loading experiment processed data.xlsx", workbook_buffer.getvalue()
        )
    outer_buffer = io.BytesIO()
    with zipfile.ZipFile(outer_buffer, "w") as outer:
        outer.writestr(
            "Data for The effect of salt loading on chloride-induced stress corrosion cracking of "
            "304L austenitic stainless steel under atmospheric conditions/Processed Data.zip",
            inner_buffer.getvalue(),
        )
    summary = _summarize_mendeley_scc_archive_bytes(outer_buffer.getvalue())
    assert summary["sheet_count"] == 1
    assert summary["formula_cells"] == 1
    assert summary["pointwise_values_published"] is False
    assert summary["qualification"].endswith("provider_checksum_unavailable")
    assert "synthetic-only-label" not in repr(summary)
