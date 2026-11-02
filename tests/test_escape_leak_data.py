from __future__ import annotations

import hashlib
from datetime import time

import pytest
from openpyxl import Workbook

from matintegrity.escape_leak_data import read_escape1_leak_trace


def _workbook(tmp_path, *, header=("Time", "Methane ppmm"), duplicate_time=False, negative=False):
    path = tmp_path / "NOV1Measurements.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "2021-11-01M"
    sheet.append(header)
    sheet.append([time(12, 0, 0), 2.0])
    sheet.append([time(12, 0, 0 if duplicate_time else 2), -1.0 if negative else 4.0])
    sheet.append([time(12, 0, 4), 3.0])
    workbook.save(path)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_escape_reader_preserves_provider_quantity_and_unresolved_reference_state(tmp_path):
    path, digest = _workbook(tmp_path)
    time_s, response, record = read_escape1_leak_trace(tmp_path, path.name, expected_sha256=digest)
    assert time_s.tolist() == [43200.0, 43202.0, 43204.0]
    assert response.tolist() == [2.0, 4.0, 3.0]
    assert record.provider_declared_leak_rate_value == 5.0
    assert record.provider_declared_leak_rate_unit == "standard_litre_per_minute"
    assert record.leak_reference_pressure_temperature == "unresolved"
    assert record.interpretation_status == "raw_response_not_calibration_ready"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"header": ("time", "Methane ppmm")}, "header"),
        ({"duplicate_time": True}, "strictly increasing"),
        ({"negative": True}, "negative methane"),
    ],
)
def test_escape_reader_rejects_unreviewed_or_invalid_trace_structure(tmp_path, kwargs, message):
    path, digest = _workbook(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        read_escape1_leak_trace(tmp_path, path.name, expected_sha256=digest)


def test_escape_reader_requires_reviewed_filename_and_digest(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="manifest"):
        read_escape1_leak_trace(tmp_path, "other.xlsx", expected_sha256=digest)
    with pytest.raises(ValueError, match="SHA-256"):
        read_escape1_leak_trace(tmp_path, path.name, expected_sha256="0" * 64)
