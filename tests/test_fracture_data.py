import zipfile

import numpy as np
import pytest

from matintegrity.fracture_data import list_crack_arrest_runs, read_crack_arrest_series

ROOT = "Raw test data of C1 and C2 crack arrest toughness test/Raw data "
HEADER = '"Time Sec";"Weg mm";"Kraft kN";"Sandner_1191 mm";"Cycle"\n'
ROWS = "0.;-24.0;-0.01;-0.5;1\n0.05;-23.5;0.02;-0.4;2\n"


def archive(tmp_path, members):
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as target:
        for name, text in members.items():
            target.writestr(name, text)
    return path


def member(family, stem):
    return f"{ROOT}{family}/{stem}.csv"


def test_series_converts_units_without_zeroing_or_sign_changes(tmp_path):
    path = archive(tmp_path, {member("C1", "L7_m123_cantilver_W20_LMM"): HEADER + ROWS})
    frame = read_crack_arrest_series(path, "L7_m123_cantilver_W20_LMM")
    assert frame.time_s.tolist() == [0, 0.05]
    assert frame.machine_displacement_m.tolist() == pytest.approx([-0.024, -0.0235])
    assert frame.force_N.tolist() == pytest.approx([-10, 20])
    assert frame.extensometer_displacement_m.tolist() == pytest.approx([-0.0005, -0.0004])
    assert frame.reported_cycle_index.tolist() == [1, 2]
    assert frame.attrs["reported_temperature_K"] == pytest.approx(150.15)
    assert frame.attrs["test_family"] == "C1"
    assert len(frame.attrs["source_member_sha256"]) == 64


def test_exact_whole_header_quoting_defect_is_normalized(tmp_path):
    malformed = '"Time Sec;""Weg mm"";""Kraft kN"";""Sandner_1191 mm"";""Cycle"""\n'
    path = archive(tmp_path, {member("C1", "L7_m70_cantilver_W20_LMM"): malformed + ROWS})
    assert len(read_crack_arrest_series(path, "L7_m70_cantilver_W20_LMM")) == 2


def test_c2_decimal_temperature_is_parsed(tmp_path):
    path = archive(tmp_path, {member("C2", "97EF_0P5_5P5_m20p1"): HEADER + ROWS})
    frame = read_crack_arrest_series(path, "97EF_0P5_5P5_m20p1")
    assert frame.attrs["reported_temperature_K"] == pytest.approx(253.05)


@pytest.mark.parametrize(
    "rows, message",
    [
        ("0.;1;2;3;1\n0.;2;3;4;2\n", "strictly increasing"),
        ("0.;1;2;3;1.5\n0.1;2;3;4;2\n", "integer"),
        ("0.;1;2;3\n", "five-column"),
    ],
)
def test_invalid_raw_rows_are_rejected(tmp_path, rows, message):
    path = archive(tmp_path, {member("C1", "L7_m4_cantilver_W20_LMM"): HEADER + rows})
    with pytest.raises(ValueError, match=message):
        read_crack_arrest_series(path, "L7_m4_cantilver_W20_LMM")


def test_unknown_or_ambiguous_specimen_is_rejected(tmp_path):
    name = member("C1", "L7_m4_cantilver_W20_LMM")
    path = archive(tmp_path, {name: HEADER + ROWS})
    with pytest.raises(ValueError, match="found 0"):
        read_crack_arrest_series(path, "unknown")


def test_inventory_requires_expected_18_unique_runs(tmp_path):
    stems_c1 = [
        "L7_m123_x",
        "L7_m104_x",
        "L7_m90_x",
        "L7_m70_x",
        "L7_m52_x",
        "L7_m34_x",
        "L7_m20_x",
        "L7_m4_x",
        "L7_23_x",
    ]
    stems_c2 = ["x_m122p6", "x_m104", "x_m89p8", "x_m70p3", "x_m52", "x_m34", "x_m20p1", "x_m4", "x_22p5"]
    members = {member("C1", stem): HEADER + ROWS for stem in stems_c1}
    members.update({member("C2", stem): HEADER + ROWS for stem in stems_c2})
    frame = list_crack_arrest_runs(archive(tmp_path, members))
    assert len(frame) == 18
    assert frame.specimen_id.is_unique
    assert np.isclose(frame.reported_temperature_K.min(), 150.15)
    assert frame.attrs["temperature_origin"].startswith("parsed")


def test_inventory_rejects_incomplete_archive(tmp_path):
    path = archive(tmp_path, {member("C1", "L7_m4_x"): HEADER + ROWS})
    with pytest.raises(ValueError, match="18 unique"):
        list_crack_arrest_runs(path)
