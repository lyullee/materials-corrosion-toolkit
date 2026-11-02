"""WILLOW tables and waveforms with explicit domains, units and quality limitations."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest
from .models.inspection import UltrasonicThickness, ultrasonic_thickness


class PulseEchoThicknessCalibration(Contract):
    """Caller-reviewed calibration for converting one pulse-echo series to thickness."""

    schema_version: Literal["matintegrity.pulse_echo_thickness_calibration.v1"] = (
        "matintegrity.pulse_echo_thickness_calibration.v1"
    )
    calibration_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    applicable_sample_ids: tuple[str, ...] = Field(min_length=1)
    applicable_probe_ids: tuple[str, ...] = Field(min_length=1)
    wave_mode: Literal["longitudinal"]
    sound_speed_m_s: Positive
    sound_speed_temperature_K: Positive | None = None
    incidence_angle_rad: float = Field(default=0.0, ge=0, lt=math.pi / 2)
    time_zero_offset_s: Nonnegative
    tof_field: Literal["tof_s", "tof_compensated_s"]
    temperature_compensation_basis: str | None = None
    calibration_basis: str = Field(min_length=1)
    evidence: Evidence
    calibration_reviewed: bool

    @model_validator(mode="after")
    def complete_basis(self):
        if len(set(self.applicable_sample_ids)) != len(self.applicable_sample_ids):
            raise ValueError("pulse-echo applicable sample IDs must be unique")
        if len(set(self.applicable_probe_ids)) != len(self.applicable_probe_ids):
            raise ValueError("pulse-echo applicable probe IDs must be unique")
        if self.tof_field == "tof_compensated_s" and not self.temperature_compensation_basis:
            raise ValueError("compensated ToF requires a temperature-compensation basis")
        return self


def _flag(value) -> bool:
    # bool("false") is True in Python; provider text flags require explicit interpretation.
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in {"true", "false", "0", "1"}:
        return value.strip().lower() in {"true", "1"}
    raise ValueError("unknown provider boolean flag; no truthiness conversion is permitted")


def _length_factor(unit: str | None) -> float:
    if unit not in {"mm", "m"}:
        raise ValueError("an explicit reviewed source length unit, mm or m, is required")
    return 1e-3 if unit == "mm" else 1.0


def _positive(value: float | None, name: str):
    if value is not None and (not math.isfinite(value) or value <= 0):
        raise ValueError(f"{name} must be finite and positive")


def read_willow_feature_table(
    path: str | Path,
    *,
    domain: str,
    series_id: str,
    specimen_thickness_m: float | None = None,
    synthetic_length_unit: str | None = None,
):
    """Keep original columns; field initial geometry never becomes serial size truth."""
    import pandas as pd

    if domain not in {"simulation", "field"} or not series_id.strip():
        raise ValueError("a declared simulation/field domain and series identity are required")
    _positive(specimen_thickness_m, "specimen thickness")
    frame = pd.read_excel(path)
    common = {"valid", "reason", "transducer_length", "metrics_backwall_tof_mm"}
    required = (
        {"simu", "shape", "depth", "width", "depth_eff", "width_eff", "transducer"}
        if domain == "simulation"
        else {"timestamp", "sensorID", "pit", "pit_diameter_mm", "pit_depth_mm", "data_origin"}
    )
    if not (common | required) <= set(frame):
        raise ValueError("WILLOW feature-table schema changed or domain is inconsistent")
    frame["processing_success"] = frame.valid.map(_flag)
    frame["source_row"] = np.arange(len(frame)) + 2
    frame["series_id"] = series_id
    frame["specimen_thickness_m"] = specimen_thickness_m
    frame["observation_domain"] = domain
    units = {}
    for column in list(frame):
        if column.endswith("_mm"):
            target = column.removesuffix("_mm") + "_m"
            if target in frame:
                raise ValueError("source column collides with a normalized length column")
            frame[target] = pd.to_numeric(frame[column], errors="raise") * 1e-3
            units[target] = "m"
    if domain == "simulation":
        factor = _length_factor(synthetic_length_unit)
        ids = pd.to_numeric(frame.simu, errors="raise").to_numpy(dtype=float)
        if (
            not np.isfinite(ids).all()
            or np.any(ids != np.floor(ids))
            or np.any(ids < 1)
            or len(set(ids)) != len(ids)
        ):
            raise ValueError("simulation indices must be unique positive integers")
        frame["observation_id"] = [f"{series_id}/case-{int(i)}" for i in ids]
        frame["observational_unit_id"] = frame.observation_id
        for column in [
            "depth",
            "width",
            "inner_width",
            "offset",
            "depth_eff",
            "width_eff",
            "transducer_length",
        ]:
            if column in frame:
                frame[column + "_m"] = pd.to_numeric(frame[column], errors="raise") * factor
                units[column + "_m"] = "m"
        frame["synthetic_reference_depth_m"] = frame.depth_eff_m
        frame["synthetic_reference_width_m"] = frame.width_eff_m
        frame["source_id"] = "willow-synthetic"
    else:
        if not (frame.data_origin == "real_harshlab").all():
            raise ValueError("field origin label changed")
        frame["timestamp"] = pd.to_datetime(frame.timestamp, errors="raise")
        if frame.timestamp.isna().any() or frame.timestamp.dt.tz is not None:
            raise ValueError("expected complete provider timestamps with unresolved timezone")
        frame["duplicate_timestamp"] = frame.timestamp.duplicated(keep=False)
        frame["pit_location_indicated"] = frame.pit.map(_flag)
        frame["initial_pit_depth_m"] = frame.pit_depth_m
        frame["initial_pit_diameter_m"] = frame.pit_diameter_m
        frame["observation_id"] = [f"{series_id}/row-{i}" for i in frame.source_row]
        frame["observational_unit_id"] = series_id
        frame["source_id"] = "willow-harshlab"
        # The length convention is corroborated against the supplied simulation MAT geometry.
        frame["transducer_length_m"] = pd.to_numeric(frame.transducer_length, errors="raise") * 1e-3
        units["transducer_length_m"] = "m"
    frame.attrs = dict(
        source_id="willow-synthetic" if domain == "simulation" else "willow-harshlab",
        domain=domain,
        normalized_column_units=units,
        timestamp_basis=None
        if domain == "simulation"
        else "provider naive calendar time; timezone unresolved",
        limitations="Processing success is not measurement validity. Nonfinite/missing individual features remain missing; no row removal, imputation, waveform sample clock, volume/surface unit or field depth truth is inferred.",
    )
    return frame


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key would overwrite an observation")
        result[key] = value
    return result


def read_willow_field_signals(
    path: str | Path,
    *,
    series_id: str,
    sample_interval_s: float | None = None,
    reported_temperature_unit: str | None = None,
) -> dict:
    _positive(sample_interval_s, "sample interval")
    if not series_id.strip() or reported_temperature_unit not in {None, "degC", "K"}:
        raise ValueError("series identity and explicit temperature convention are required")
    records = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    observations = []
    for index, (key, value) in enumerate(records.items()):
        timestamp = datetime.strptime(key, "data_%Y_%m_%d_%H_%M_%S")
        if not {"Sensor", "Temp", "Tof", "RawData"} <= set(value):
            raise ValueError("WILLOW device schema changed")
        signal = np.asarray(value["RawData"], dtype=float)
        if signal.ndim != 1 or len(signal) < 2:
            raise ValueError("one raw sample vector is required per device observation")
        tof = float(value["Tof"]) * 1e-9
        temperature = float(value["Temp"])
        temperature_K = (
            None
            if reported_temperature_unit is None
            else temperature + (273.15 if reported_temperature_unit == "degC" else 0)
        )
        if temperature_K is not None and (not math.isfinite(temperature_K) or temperature_K <= 0):
            temperature_K = None
        observations.append(
            dict(
                source_key=key,
                source_order=index,
                timestamp=timestamp,
                observational_unit_id=series_id,
                sensor_id=str(value["Sensor"]),
                tof_s=tof if math.isfinite(tof) and tof > 0 else None,
                reported_temperature=value["Temp"],
                ambient_temperature_K=temperature_K,
                raw_signal=signal,
                raw_signal_finite=bool(np.isfinite(signal).all()),
                sample_time_s=None
                if sample_interval_s is None
                else np.arange(len(signal)) * sample_interval_s,
                reported_device_fields={k: v for k, v in value.items() if k != "RawData"},
            )
        )
    if not observations or any(
        b["timestamp"] <= a["timestamp"] for a, b in zip(observations, observations[1:], strict=False)
    ):
        raise ValueError("device observations need a strictly increasing provider clock; no implicit sorting")
    return dict(
        source_id="willow-harshlab",
        series_id=series_id,
        observations=observations,
        timestamp_basis="provider naive calendar time; timezone unresolved",
        sample_interval_s=sample_interval_s,
        reported_temperature_unit=reported_temperature_unit,
        signal_unit="unqualified provider ADC scale",
        notes="Device ToF ns is converted to seconds. Ambient temperature is not assumed to be specimen temperature. Gain/filter/configuration fields are preserved; no depth or processing-valid flag is inferred from them.",
    )


def read_ceit_uniform_corrosion_field(
    path: str | Path,
    *,
    series_id: str,
    reported_tof_unit: str | None = None,
    reported_temperature_unit: str | None = None,
    sample_interval_s: float | None = None,
) -> dict:
    """Read the CEIT field JSON without turning device ToF into wall thickness."""
    _positive(sample_interval_s, "sample interval")
    if not series_id.strip():
        raise ValueError("a nonempty series identity is required")
    if reported_tof_unit not in {None, "ns", "s"}:
        raise ValueError("reported ToF unit must be omitted, ns or s")
    if reported_temperature_unit not in {None, "degC", "K"}:
        raise ValueError("reported temperature unit must be omitted, degC or K")
    records = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(records, list) or not records:
        raise ValueError("expected a nonempty CEIT observation list")
    required = {
        "Fecha",
        "node_id",
        "sample_id",
        "piezo_id",
        "freqc_i",
        "pwm",
        "echon_i",
        "tofref",
        "tem",
        "bat",
        "tof",
        "tof_c",
        "amplitud",
        "raw",
        "fil",
        "cor",
        "env",
    }
    observations = []
    previous_timestamp = None
    for index, value in enumerate(records):
        if not isinstance(value, dict) or set(value) != required:
            raise ValueError("CEIT field record schema changed")
        timestamp = datetime.fromisoformat(value["Fecha"])
        if timestamp.tzinfo is not None:
            raise ValueError("expected provider naive calendar time with unresolved timezone")
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise ValueError(
                "CEIT observations need a strictly increasing provider clock; no implicit sorting"
            )
        previous_timestamp = timestamp
        signals = {
            target: np.asarray(value[source], dtype=float)
            for source, target in (
                ("raw", "raw_signal"),
                ("fil", "filtered_signal"),
                ("cor", "correlation_signal"),
                ("env", "envelope_signal"),
            )
        }
        if any(signal.ndim != 1 or len(signal) < 2 for signal in signals.values()):
            raise ValueError("each CEIT signal channel must be a one-dimensional vector")
        if not all(np.isfinite(signal).all() for signal in signals.values()):
            raise ValueError("nonfinite CEIT signal samples require an explicit future missing-data contract")
        tof_reported = float(value["tof"])
        tof_compensated_reported = float(value["tof_c"])
        tof_factor = None if reported_tof_unit is None else (1e-9 if reported_tof_unit == "ns" else 1.0)
        reported_temperature = float(value["tem"])
        temperature_K = (
            None
            if reported_temperature_unit is None
            else reported_temperature + (273.15 if reported_temperature_unit == "degC" else 0.0)
        )
        if temperature_K is not None and (not math.isfinite(temperature_K) or temperature_K <= 0):
            raise ValueError("reviewed temperature conversion must produce positive kelvin")
        observations.append(
            dict(
                source_order=index,
                timestamp=timestamp,
                observational_unit_id=series_id,
                node_id=str(value["node_id"]),
                sample_id=str(value["sample_id"]),
                piezo_id=str(value["piezo_id"]),
                reported_frequency_code=value["freqc_i"],
                reported_pwm=value["pwm"],
                reported_echo_index=value["echon_i"],
                reported_tof_reference=value["tofref"],
                tof_reported=tof_reported,
                tof_compensated_reported=tof_compensated_reported,
                tof_s=None if tof_factor is None else tof_reported * tof_factor,
                tof_compensated_s=None if tof_factor is None else tof_compensated_reported * tof_factor,
                reported_temperature=reported_temperature,
                ambient_temperature_K=temperature_K,
                reported_battery=value["bat"],
                reported_amplitude=value["amplitud"],
                sample_time_s=None
                if sample_interval_s is None
                else np.arange(len(signals["raw_signal"])) * sample_interval_s,
                raw_adc_rail_count=int(
                    np.count_nonzero((signals["raw_signal"] == -2048) | (signals["raw_signal"] == 2047))
                ),
                **signals,
            )
        )
    identities = {
        key: sorted({observation[key] for observation in observations})
        for key in ("node_id", "sample_id", "piezo_id")
    }
    return dict(
        source_id="ceit-uniform-corrosion-field",
        series_id=series_id,
        observations=observations,
        identities=identities,
        observational_unit="one monitored steel sample; repeated device acquisitions",
        timestamp_basis="provider naive calendar time; timezone unresolved",
        reported_tof_unit=reported_tof_unit,
        reported_temperature_unit=reported_temperature_unit,
        sample_interval_s=sample_interval_s,
        signal_unit="unqualified provider ADC/processed scales",
        thickness_status="not_computed_without_a_reviewed_wave_speed_and_path_definition",
        notes=(
            "Reported and temperature-compensated ToF remain device observations. No thickness, "
            "corrosion rate, uncertainty, spatial coverage, remaining life or failure probability is inferred."
        ),
    )


def pulse_echo_thickness_observations(
    series: dict,
    *,
    calibration: PulseEchoThicknessCalibration,
) -> dict:
    """Apply an explicitly reviewed pulse-echo calibration without fitting a loss rate."""
    if not calibration.calibration_reviewed:
        raise ValueError("pulse-echo calibration must be reviewed before thickness conversion")
    if not isinstance(series, dict) or not series.get("observations"):
        raise ValueError("a nonempty pulse-echo observation series is required")
    if series.get("reported_tof_unit") is None:
        raise ValueError("pulse-echo ToF unit must be reviewed by the source reader")
    observations = series["observations"]
    sample_ids = {str(row.get("sample_id", "")) for row in observations}
    probe_ids = {str(row.get("piezo_id", "")) for row in observations}
    if not sample_ids <= set(calibration.applicable_sample_ids):
        raise ValueError("pulse-echo sample identity is outside the calibration scope")
    if not probe_ids <= set(calibration.applicable_probe_ids):
        raise ValueError("pulse-echo probe identity is outside the calibration scope")

    converted = []
    for row in observations:
        observed_tof_s = row.get(calibration.tof_field)
        if not isinstance(observed_tof_s, (int, float)) or not math.isfinite(observed_tof_s):
            raise ValueError("selected pulse-echo ToF values must be finite SI seconds")
        calculation = ultrasonic_thickness(
            UltrasonicThickness(
                round_trip_time_s=float(observed_tof_s),
                sound_speed_m_s=calibration.sound_speed_m_s,
                time_zero_offset_s=calibration.time_zero_offset_s,
                incidence_angle_rad=calibration.incidence_angle_rad,
            )
        )
        if calculation.status != "computed":
            raise ValueError("pulse-echo time-zero correction leaves no positive sound path")
        converted.append(
            {
                "source_order": row["source_order"],
                "timestamp": row["timestamp"],
                "observational_unit_id": row["observational_unit_id"],
                "sample_id": row["sample_id"],
                "probe_id": row["piezo_id"],
                "selected_tof_field": calibration.tof_field,
                "selected_tof_s": float(observed_tof_s),
                "remaining_thickness_m": calculation.values["thickness_m"],
                "measurement_standard_deviation_m": None,
            }
        )
    calibration_digest = canonical_digest(calibration.model_dump(mode="json"))
    return {
        "schema_version": "matintegrity.pulse_echo_thickness_series.v1",
        "source_id": series.get("source_id", "unidentified-pulse-echo-series"),
        "series_id": series.get("series_id"),
        "calibration_id": calibration.calibration_id,
        "calibration_digest": calibration_digest,
        "material_id": calibration.material_id,
        "observations": converted,
        "thickness_series_ready": True,
        "corrosion_rate_fit_ready": False,
        "bayesian_update_ready": False,
        "qualification": (
            "Caller-reviewed calibration application only. Measurement uncertainty, spatial-location "
            "identity and independent dimensional validation remain separate requirements."
        ),
    }


def iter_willow_simulations(
    path: str | Path,
    *,
    source_length_unit: str,
    sample_interval_s: float | None = None,
):
    """Read v7.3 MATLAB cell references; preserve nonfinite failed signals and absent clocks."""
    import h5py

    factor = _length_factor(source_length_unit)
    _positive(sample_interval_s, "sample interval")
    with h5py.File(path) as file:
        if "dataset" not in file or file["dataset"].ndim != 2 or file["dataset"].shape[0] != 1:
            raise ValueError("expected WILLOW MATLAB row-cell dataset")
        for index, reference in enumerate(file["dataset"][0]):
            group = file[reference]
            if not {"pit", "pit_eff", "result", "trans_len"} <= set(group):
                raise ValueError("simulation cell schema changed")

            def scalar(node):
                value = np.asarray(node)
                if value.size != 1:
                    raise ValueError("simulation geometry must be scalar")
                return float(value.reshape(-1)[0])

            def shape_text(node):
                return "".join(chr(int(v)) for v in np.asarray(node).reshape(-1))

            signal = np.asarray(group["result"])
            if signal.ndim != 2 or min(signal.shape) != 1:
                raise ValueError("unexpected simulation waveform axes")
            signal = signal.reshape(-1)
            pit = group["pit"]
            geometry = {
                f"{key}_m": scalar(pit[key]) * factor
                for key in ("depth", "width", "inner_width", "offset")
                if key in pit
            }
            yield dict(
                source_id="willow-synthetic",
                simulation_index=index + 1,
                pit_shape=shape_text(pit["shape"]),
                input_geometry=geometry,
                declared_roughness=None
                if "use_roughness" not in pit
                else _flag(scalar(pit["use_roughness"])),
                effective_depth_m=scalar(group["pit_eff/depth"]) * factor,
                effective_width_m=scalar(group["pit_eff/width"]) * factor,
                transducer_length_m=scalar(group["trans_len"]) * factor,
                raw_signal=signal,
                raw_signal_finite=bool(np.isfinite(signal).all()),
                sample_time_s=None
                if sample_interval_s is None
                else np.arange(len(signal)) * sample_interval_s,
                sample_interval_s=sample_interval_s,
                signal_unit="unqualified simulation amplitude",
                auxiliary_parameters={key: scalar(group[key]) for key in ("sigma", "alpha") if key in group},
            )
