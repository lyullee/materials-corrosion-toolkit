import pytest
from openpyxl import Workbook

from matintegrity.creep_data import read_cmsx6_creep, read_cmsx6_trace


def make_workbook(path, criterion="Time limit", rupture="Not applicable"):
    book = Workbook()
    sheet = book.active
    sheet.title = "Vh5205_C-synthetic"
    sheet.cell(3, 3, "ENTRY")
    metadata = [
        ("Test ID", None, sheet.title),
        ("Load control type", None, "Constant force"),
        ("(Digital) Material Identifier", None, "CMSX-6"),
        ("Specified temperature", "°C", "980 °C"),
        ("Initial stress", "MPa", 140),
        ("Test duration", "h", 1000),
        ("Creep rupture time", "h", rupture),
        ("End of test criterium", None, criterion),
    ]
    for i, (key, unit, value) in enumerate(metadata, 4):
        sheet.cell(i, 3, key)
        if unit is not None:
            sheet.cell(i, 5, unit)
        sheet.cell(i, 7, value)
    book.save(path)


def test_endpoint_metadata_preserves_administrative_censoring(tmp_path):
    path = tmp_path / "synthetic.xlsx"
    make_workbook(path)
    frame = read_cmsx6_creep(path)
    assert frame.right_censored.tolist() == [True]
    assert frame.endpoint_time_s.tolist() == [3.6e6]
    assert frame.initial_stress_Pa.tolist() == [1.4e8]
    assert frame.temperature_K.tolist() == [1253.15]
    assert frame.temperature_basis.tolist() == ["nominal_specified"]
    make_workbook(path, "Test piece break", 500)
    frame = read_cmsx6_creep(path)
    assert frame.right_censored.tolist() == [False]
    assert frame.endpoint_time_s.tolist() == [1.8e6]
    make_workbook(path, "Test piece break", 1000.5)
    with pytest.raises(ValueError, match="inconsistent"):
        read_cmsx6_creep(path)


def test_unknown_termination_does_not_become_a_failure(tmp_path):
    path = tmp_path / "synthetic.xlsx"
    make_workbook(path, "Equipment interruption")
    row = read_cmsx6_creep(path).iloc[0]
    assert row.endpoint_kind == "unresolved"
    assert row.endpoint_time_s is None and row.right_censored is None


def test_processed_lis_uses_local_units_and_preserves_clock_origin(tmp_path):
    path = tmp_path / "synthetic.LIS"
    path.write_text(
        "[data]\nlabels\nt\te\tTc\tTc\tTc\nh\t%\t°C\t°C\t°C\n0\t0\t980\t979\t981\n0,5\t2\t980\t979\t981\n",
        encoding="latin1",
    )
    trace = read_cmsx6_trace(path)
    assert trace.time_s.tolist() == [0, 1800]
    assert trace.plastic_extension_fraction.tolist() == [0, 0.02]
    assert trace.attrs["clock_origin"] == "end_of_loading"
    path.write_text(path.read_text(encoding="latin1").replace("0,5\t", "0\t"), encoding="latin1")
    with pytest.raises(ValueError, match="repeated"):
        read_cmsx6_trace(path)
    preserved = read_cmsx6_trace(path, duplicate_policy="preserve")
    assert preserved.time_s.tolist() == [0, 0]
    assert preserved.repeated_timestamp.all()
    assert preserved.attrs["repeated_clock_intervals"] == 1
