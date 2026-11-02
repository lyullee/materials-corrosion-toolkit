import hashlib
import zipfile

import pandas as pd
import pytest

from matintegrity.thermal_data import _fitted_rows, read_thermal_rod_series


def archive_with_csv(path, name="run-one", rows=None):
    if rows is None:
        rows = [
            "Time,TC1,TC2,TC3,TC4,TC5,TC6,Power (1023 Max)",
            "0,-0.2,0,1,2,3,4,40",
            "0.2,0.1,0.2,1.2,2.2,3.2,4.2,40",
        ]
    payload = "\n".join(rows).encode()
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"dataset/Raw_Data/{name}.csv", payload)
    return payload


def test_raw_reader_preserves_negative_excess_temperature_and_controller_basis(tmp_path):
    path = tmp_path / "thermal.zip"
    payload = archive_with_csv(path)
    frame = read_thermal_rod_series(path, "run-one")
    assert frame.time_s.tolist() == [0.0, 0.2]
    assert frame.tc1_excess_temperature_K.tolist() == [-0.2, 0.1]
    assert frame.controller_setting_counts.tolist() == [40, 40]
    assert frame.attrs["source_member_sha256"] == hashlib.sha256(payload).hexdigest()
    assert "not watts" in frame.attrs["controller_setting_basis"]


@pytest.mark.parametrize(
    "rows, message",
    [
        (
            [
                "Time,TC1,TC2,TC3,TC4,TC5,TC6,Power",
                "0,0,0,0,0,0,0,40",
                "0.2,0,0,0,0,0,0,40",
            ],
            "column",
        ),
        (
            [
                "Time,TC1,TC2,TC3,TC4,TC5,TC6,Power (1023 Max)",
                "0,0,0,0,0,0,0,40",
                "0,0,0,0,0,0,0,40",
            ],
            "strictly increasing",
        ),
    ],
)
def test_raw_reader_rejects_schema_and_clock_changes(tmp_path, rows, message):
    path = tmp_path / "thermal.zip"
    archive_with_csv(path, rows=rows)
    with pytest.raises(ValueError, match=message):
        read_thermal_rod_series(path, "run-one")


def test_raw_reader_requires_exact_stem_and_unique_member(tmp_path):
    path = tmp_path / "thermal.zip"
    archive_with_csv(path)
    with pytest.raises(ValueError, match="stem"):
        read_thermal_rod_series(path, "run-one.csv")
    with pytest.raises(ValueError, match="found 0"):
        read_thermal_rod_series(path, "absent")


def fitted_frame():
    rows = [[None, None] for _ in range(26)]
    rows[0] = ["Variable", "test-1"]
    rows[18] = ["Transient model", None]
    rows[4] = ["alpha", 0.02]
    rows[5] = ["tau", 10.0]
    for index, (label, value) in enumerate(
        [
            ("h", 50.0),
            ("k", 15.0),
            ("Pss", 2.0),
            ("standard_error", 0.5),
            ("h error", 1.0),
            ("k error", 0.2),
            ("Pss error", 0.1),
        ],
        19,
    ):
        rows[index] = [label, value]
    return pd.DataFrame(rows)


def test_fitted_result_normalization_keeps_same_data_fit_identity():
    records = _fitted_rows(fitted_frame(), "results.xlsx", "source-group", "SS")
    assert records == [
        {
            "run_id": "test-1",
            "source_workbook": "results.xlsx",
            "experiment_group": "source-group",
            "source_sheet": "SS",
            "fitted_boundary_ramp_rate_1_s": 0.02,
            "fitted_boundary_delay_s": 10.0,
            "fitted_convection_W_m2_K": 50.0,
            "fitted_conductivity_W_m_K": 15.0,
            "fitted_steady_power_W": 2.0,
            "fitted_standard_error_K": 0.5,
            "reported_h_error": 1.0,
            "reported_k_error": 0.2,
            "reported_power_error": 0.1,
        }
    ]


def test_fitted_result_labels_are_not_positional_defaults():
    frame = fitted_frame()
    frame.iat[20, 0] = "conductivity"
    with pytest.raises(ValueError, match="labels changed"):
        _fitted_rows(frame, "results.xlsx", "source-group", "SS")
