import json

import h5py
import numpy as np
import pandas as pd
import pytest

from matintegrity.contracts import Evidence
from matintegrity.ultrasound_data import (
    PulseEchoThicknessCalibration,
    iter_willow_simulations,
    pulse_echo_thickness_observations,
    read_ceit_uniform_corrosion_field,
    read_willow_feature_table,
    read_willow_field_signals,
)


def test_field_flags_initial_geometry_missing_descriptors_and_repeated_unit(tmp_path):
    path = tmp_path / "field.xlsx"
    pd.DataFrame(
        dict(
            valid=["true", "false"],
            reason=["-", "unresolved echo"],
            transducer_length=[3.2] * 2,
            metrics_backwall_tof_mm=[5.0, np.nan],
            timestamp=["2026-01-01 00:00:00", "2026-01-01 06:00:00"],
            sensorID=["sensor"] * 2,
            pit=[1] * 2,
            pit_depth_mm=[0.5] * 2,
            pit_diameter_mm=[1.0] * 2,
            data_origin=["real_harshlab"] * 2,
        )
    ).to_excel(path, index=False)
    frame = read_willow_feature_table(path, domain="field", series_id="one-specimen")
    assert frame.processing_success.tolist() == [True, False]
    assert frame.observational_unit_id.nunique() == 1
    assert frame.initial_pit_depth_m.tolist() == [0.0005] * 2
    assert "synthetic_reference_depth_m" not in frame
    assert frame.metrics_backwall_tof_m.iloc[0] == 0.005
    assert pd.isna(frame.metrics_backwall_tof_m.iloc[1])
    assert len(frame) == 2 and frame.attrs["timestamp_basis"].endswith("timezone unresolved")
    frame["valid"] = ["unknown", "false"]
    frame.drop(columns=[c for c in frame if c.endswith("_m")]).to_excel(path, index=False)
    with pytest.raises(ValueError, match="boolean flag"):
        read_willow_feature_table(path, domain="field", series_id="one-specimen")


def test_simulation_table_requires_reviewed_geometry_units_and_preserves_failed_rows(tmp_path):
    path = tmp_path / "simulation.xlsx"
    pd.DataFrame(
        dict(
            valid=[0],
            reason=["nonfinite signal"],
            transducer_length=[3.2],
            metrics_backwall_tof_mm=[np.nan],
            simu=[1],
            shape=["gaussian"],
            depth=[0.8],
            width=[1.0],
            depth_eff=[0.7],
            width_eff=[1.2],
            transducer=["synthetic"],
        )
    ).to_excel(path, index=False)
    with pytest.raises(ValueError, match="source length unit"):
        read_willow_feature_table(path, domain="simulation", series_id="batch")
    frame = read_willow_feature_table(
        path, domain="simulation", series_id="batch", synthetic_length_unit="mm", specimen_thickness_m=0.003
    )
    assert not frame.processing_success.iloc[0]
    assert frame.synthetic_reference_depth_m.iloc[0] == 0.0007
    assert frame.depth_m.iloc[0] == 0.0008
    assert pd.isna(frame.metrics_backwall_tof_m.iloc[0])


def test_device_clock_units_and_configuration_are_preserved_without_inventing_sampling(tmp_path):
    path = tmp_path / "signals.json"
    value = dict(
        Sensor="board", Temp="20.0", Tof="1600.0", RawData=[0, 1, -1, 0], MeasGain="1.2", Filtered="0"
    )
    path.write_text(json.dumps({"data_2026_01_01_00_00_00": value}), encoding="utf-8")
    result = read_willow_field_signals(path, series_id="specimen")
    row = result["observations"][0]
    assert row["tof_s"] == pytest.approx(1.6e-6)
    assert row["ambient_temperature_K"] is None and row["sample_time_s"] is None
    assert row["reported_device_fields"]["MeasGain"] == "1.2"
    actual = read_willow_field_signals(
        path, series_id="specimen", reported_temperature_unit="degC", sample_interval_s=1e-8
    )["observations"][0]
    assert actual["ambient_temperature_K"] == 293.15
    assert actual["sample_time_s"] == pytest.approx([0, 1e-8, 2e-8, 3e-8])
    path.write_text('{"data_2026_01_01_00_00_00":{},"data_2026_01_01_00_00_00":{}}')
    with pytest.raises(ValueError, match="duplicate JSON"):
        read_willow_field_signals(path, series_id="specimen")


def test_ceit_field_reader_preserves_device_observations_without_inventing_thickness(tmp_path):
    path = tmp_path / "uniform.json"
    base = dict(
        Fecha="2022-02-22T12:01:10.833",
        node_id="AA04",
        sample_id="S355-00-02",
        piezo_id="V111",
        freqc_i=16,
        pwm=33,
        echon_i=2,
        tofref=209,
        tem=21.0,
        bat=3.9,
        tof=1679.0,
        tof_c=1680.0,
        amplitud=107,
        raw=[-2048, 0, 2047],
        fil=[-2, 0, 2],
        cor=[-3, 0, 3],
        env=[1, 2, 1],
    )
    second = {**base, "Fecha": "2022-02-22T12:01:11.833", "tof": 1678.0}
    path.write_text(json.dumps([base, second]), encoding="utf-8")

    unresolved = read_ceit_uniform_corrosion_field(path, series_id="one-sample")
    first = unresolved["observations"][0]
    assert first["tof_reported"] == 1679.0 and first["tof_s"] is None
    assert first["ambient_temperature_K"] is None and first["sample_time_s"] is None
    assert first["raw_adc_rail_count"] == 2
    assert unresolved["identities"]["sample_id"] == ["S355-00-02"]
    assert unresolved["thickness_status"].startswith("not_computed")

    reviewed = read_ceit_uniform_corrosion_field(
        path,
        series_id="one-sample",
        reported_tof_unit="ns",
        reported_temperature_unit="degC",
        sample_interval_s=1e-8,
    )
    first = reviewed["observations"][0]
    assert first["tof_s"] == pytest.approx(1.679e-6)
    assert first["tof_compensated_s"] == pytest.approx(1.680e-6)
    assert first["ambient_temperature_K"] == pytest.approx(294.15)
    assert first["sample_time_s"] == pytest.approx([0, 1e-8, 2e-8])

    path.write_text(json.dumps([second, base]), encoding="utf-8")
    with pytest.raises(ValueError, match="strictly increasing"):
        read_ceit_uniform_corrosion_field(path, series_id="one-sample")


def test_pulse_echo_thickness_requires_reviewed_units_calibration_and_matching_identity(tmp_path):
    path = tmp_path / "uniform.json"
    record = dict(
        Fecha="2022-02-22T12:01:10.833",
        node_id="AA04",
        sample_id="S355-00-02",
        piezo_id="V111",
        freqc_i=16,
        pwm=33,
        echon_i=2,
        tofref=209,
        tem=21.0,
        bat=3.9,
        tof=1680.0,
        tof_c=1678.0,
        amplitud=107,
        raw=[-2048, 0, 2047],
        fil=[-2, 0, 2],
        cor=[-3, 0, 3],
        env=[1, 2, 1],
    )
    path.write_text(json.dumps([record]), encoding="utf-8")
    unresolved = read_ceit_uniform_corrosion_field(path, series_id="one-sample")
    reviewed = read_ceit_uniform_corrosion_field(path, series_id="one-sample", reported_tof_unit="ns")
    evidence = Evidence(
        source_id="synthetic-calibration",
        origin="synthetic",
        citation="authored round-trip identity test",
        sha256="1" * 64,
    )

    def calibration(**updates):
        values = dict(
            calibration_id="one-sample-calibration",
            material_id="synthetic-steel",
            applicable_sample_ids=("S355-00-02",),
            applicable_probe_ids=("V111",),
            wave_mode="longitudinal",
            sound_speed_m_s=6000.0,
            sound_speed_temperature_K=293.15,
            time_zero_offset_s=10e-9,
            tof_field="tof_s",
            calibration_basis="synthetic exact round-trip path",
            evidence=evidence,
            calibration_reviewed=True,
        )
        values.update(updates)
        return PulseEchoThicknessCalibration(**values)

    with pytest.raises(ValueError, match="ToF unit"):
        pulse_echo_thickness_observations(unresolved, calibration=calibration())
    with pytest.raises(ValueError, match="must be reviewed"):
        pulse_echo_thickness_observations(reviewed, calibration=calibration(calibration_reviewed=False))
    with pytest.raises(ValueError, match="sample identity"):
        pulse_echo_thickness_observations(
            reviewed, calibration=calibration(applicable_sample_ids=("another-sample",))
        )

    converted = pulse_echo_thickness_observations(reviewed, calibration=calibration())
    row = converted["observations"][0]
    assert row["remaining_thickness_m"] == pytest.approx(0.00501)
    assert row["measurement_standard_deviation_m"] is None
    assert converted["corrosion_rate_fit_ready"] is False
    assert converted["bayesian_update_ready"] is False
    assert len(converted["calibration_digest"]) == 64


def test_compensated_pulse_echo_tof_requires_an_explicit_compensation_basis():
    evidence = Evidence(
        source_id="synthetic-calibration",
        origin="synthetic",
        citation="authored validation",
    )
    with pytest.raises(ValueError, match="temperature-compensation basis"):
        PulseEchoThicknessCalibration(
            calibration_id="calibration",
            material_id="steel",
            applicable_sample_ids=("sample",),
            applicable_probe_ids=("probe",),
            wave_mode="longitudinal",
            sound_speed_m_s=5900.0,
            time_zero_offset_s=0.0,
            tof_field="tof_compensated_s",
            calibration_basis="synthetic",
            evidence=evidence,
            calibration_reviewed=True,
        )


def test_matlab_references_and_axes_do_not_supply_an_unreported_timebase(tmp_path):
    path = tmp_path / "simulation.mat"
    with h5py.File(path, "w") as f:
        group = f.create_group("case")
        pit = group.create_group("pit")
        pit["shape"] = np.array([ord(c) for c in "ellipse"], dtype=np.uint16)[:, None]
        pit["depth"] = [[0.001]]
        pit["width"] = [[0.002]]
        pit["use_roughness"] = [[0]]
        group["pit_eff/depth"] = [[0.0009]]
        group["pit_eff/width"] = [[0.0021]]
        group["trans_len"] = [[0.0032]]
        group["result"] = np.array([1.0, np.inf, 2.0])[:, None]
        dataset = f.create_dataset("dataset", (1, 1), dtype=h5py.ref_dtype)
        dataset[0, 0] = group.ref
    row = next(iter_willow_simulations(path, source_length_unit="m"))
    assert row["simulation_index"] == 1 and row["pit_shape"] == "ellipse"
    assert row["effective_depth_m"] == 0.0009
    assert row["raw_signal"].shape == (3,) and not row["raw_signal_finite"]
    assert row["sample_time_s"] is None and row["declared_roughness"] is False
