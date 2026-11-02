from __future__ import annotations

import hashlib

import pytest
from openpyxl import Workbook

from matintegrity.pressure_decay_leak_data import SERIES_COLUMNS, read_pressure_decay_leak_workbook


def _workbook(tmp_path, *, bad_header=False, duplicate_time=False, negative_pressure=False):
    path = tmp_path / "DataSet Temperatue-Pressure.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hárok1"
    sheet.cell(1, 1, "Testing gas")
    sheet.cell(2, 1, "Lenght of capilar [mm]")
    sheet.cell(3, 1, "Time t [s]")
    for raw_gas, _, length_mm, temperature_column, pressure_column in SERIES_COLUMNS:
        if length_mm == 100.0:
            sheet.cell(1, temperature_column, raw_gas)
        sheet.cell(2, temperature_column, f"{int(length_mm)} mm")
        sheet.cell(3, temperature_column, "temperature" if bad_header else "Temperatures T [°C]")
        sheet.cell(3, pressure_column, "Pressure [Pa]")
    for index, row in enumerate(range(4, 35)):
        sheet.cell(row, 1, 0 if duplicate_time and index == 1 else index * 30)
        for _, _, _, temperature_column, pressure_column in SERIES_COLUMNS:
            sheet.cell(row, temperature_column, 20.0)
            sheet.cell(row, pressure_column, -1.0 if negative_pressure and index == 2 else 5000 - index)
    workbook.save(path)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_preserves_raw_series_and_withholds_leak_rate(tmp_path):
    path, digest = _workbook(tmp_path)
    time_s, arrays, audit = read_pressure_decay_leak_workbook(path, expected_sha256=digest)
    assert time_s.tolist() == [float(value) for value in range(0, 901, 30)]
    assert len(arrays) == 10
    assert audit.total_samples == 310
    assert audit.missing_configuration == "reference_state_without_artificial_defect"
    assert audit.calibration_use_status == "withheld_missing_blank_volume_and_pressure_basis"
    assert all(row.temperature_role == "unresolved_ambient_or_internal" for row in audit.series)
    assert all(row.interpretation_status == "raw_pressure_temperature_not_leak_rate" for row in audit.series)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"bad_header": True}, "temperature header"),
        ({"duplicate_time": True}, "strictly increasing"),
        ({"negative_pressure": True}, "nonnegative"),
    ],
)
def test_reader_rejects_invalid_or_changed_layout(tmp_path, kwargs, message):
    path, digest = _workbook(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        read_pressure_decay_leak_workbook(path, expected_sha256=digest)


def test_reader_rejects_digest_mismatch(tmp_path):
    path, _ = _workbook(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        read_pressure_decay_leak_workbook(path, expected_sha256="0" * 64)
