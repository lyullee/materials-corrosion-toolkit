"""Weighted constant wave-speed and clock-offset calibration from known AE sources."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AESpeedSensor(Contract):
    sensor_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]
    calibration_id: str = Field(min_length=1)
    calibration_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AEKnownSource(Contract):
    source_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    coordinate_frame_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]
    emission_reference_time_s: Nonnegative
    source_definition_id: str = Field(min_length=1)
    source_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AESpeedArrivalPick(Contract):
    pick_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    sensor_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    arrival_time_s: Nonnegative | None = None
    standard_uncertainty_s: Positive | None = None
    pick_method_id: str = Field(min_length=1)
    source_trace_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_status: Literal["valid", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_contract(self):
        if self.record_status == "valid":
            if (
                self.arrival_time_s is None
                or self.standard_uncertainty_s is None
                or self.result_digest is None
            ):
                raise ValueError("valid AE speed picks require arrival, uncertainty and digest")
        elif (
            any(
                value is not None
                for value in (self.arrival_time_s, self.standard_uncertainty_s, self.result_digest)
            )
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid AE speed picks require a basis and no result fields")
        return self


class AcousticEmissionWaveSpeedCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    sensors: tuple[AESpeedSensor, ...] = Field(min_length=2)
    known_sources: tuple[AEKnownSource, ...] = Field(min_length=2)
    picks: tuple[AESpeedArrivalPick, ...] = Field(min_length=4)
    minimum_supported_wave_speed_m_s: Positive
    maximum_supported_wave_speed_m_s: Positive
    minimum_calibration_distance_span_m: Positive
    minimum_calibration_source_count: int = Field(ge=2)
    minimum_holdout_source_count: int = Field(ge=1)
    sensor_source_coordinates_and_frame_reviewed: bool
    clock_and_emission_reference_reviewed: bool
    pick_methods_uncertainties_and_digests_reviewed: bool
    source_specimen_groups_and_partitions_reviewed: bool
    homogeneous_isotropic_constant_speed_assumption_reviewed: bool
    support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_links_and_partitions(self):
        if self.maximum_supported_wave_speed_m_s < self.minimum_supported_wave_speed_m_s:
            raise ValueError("AE wave-speed support must be ordered")
        for rows, attribute, label in (
            (self.sensors, "sensor_id", "sensor"),
            (self.known_sources, "source_id", "known source"),
            (self.picks, "pick_id", "arrival pick"),
        ):
            values = [getattr(row, attribute) for row in rows]
            if len(set(values)) != len(values):
                raise ValueError(f"AE {label} IDs must be unique")
        if any(
            row.coordinate_frame_id != self.coordinate_frame_id for row in self.sensors + self.known_sources
        ):
            raise ValueError("AE sensors and known sources must share the calibration frame")
        sensor_channels = {row.sensor_id: row.channel_id for row in self.sensors}
        sources = {row.source_id: row for row in self.known_sources}
        specimen_partitions = {}
        group_partitions = {}
        for source in self.known_sources:
            for mapping, key, label in (
                (specimen_partitions, source.physical_specimen_id, "physical specimen"),
                (group_partitions, source.source_group_id, "source group"),
            ):
                prior = mapping.setdefault(key, source.partition)
                if prior != source.partition:
                    raise ValueError(f"AE {label} cannot cross calibration and holdout partitions")
        for pick in self.picks:
            if pick.source_id not in sources:
                raise ValueError("AE speed picks must reference declared known sources")
            if pick.sensor_id not in sensor_channels or sensor_channels[pick.sensor_id] != pick.channel_id:
                raise ValueError("AE speed picks must reference declared sensor-channel pairs")
            if pick.clock_id != self.clock_id:
                raise ValueError("AE speed picks must share the calibration clock")
        return self


def acoustic_emission_wave_speed_calibration(x: AcousticEmissionWaveSpeedCalibration) -> Calculation:
    reviews = (
        "sensor_source_coordinates_and_frame_reviewed",
        "clock_and_emission_reference_reviewed",
        "pick_methods_uncertainties_and_digests_reviewed",
        "source_specimen_groups_and_partitions_reviewed",
        "homogeneous_isotropic_constant_speed_assumption_reviewed",
        "support_and_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    excluded = [row.pick_id for row in x.picks if row.record_status != "valid"]
    valid_picks = [row for row in x.picks if row.record_status == "valid"]
    sensors = {row.sensor_id: row for row in x.sensors}
    sources = {row.source_id: row for row in x.known_sources}
    calibration_picks = [row for row in valid_picks if sources[row.source_id].partition == "calibration"]
    holdout_picks = [row for row in valid_picks if sources[row.source_id].partition == "holdout"]
    calibration_source_ids = {row.source_id for row in calibration_picks}
    holdout_source_ids = {row.source_id for row in holdout_picks}
    counts_ok = (
        len(calibration_source_ids) >= x.minimum_calibration_source_count
        and len(holdout_source_ids) >= x.minimum_holdout_source_count
    )
    if missing_reviews or not counts_ok:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "excluded_missing_or_invalid_pick_ids": excluded,
                "minimum_source_counts_satisfied": counts_ok,
            },
            notes=(
                "Wave-speed calibration is withheld until reviews and valid source partitions are complete.",
            ),
        )

    def distance(pick):
        return math.dist(sensors[pick.sensor_id].position_m, sources[pick.source_id].position_m)

    xs = [distance(row) for row in calibration_picks]
    ys = [row.arrival_time_s - sources[row.source_id].emission_reference_time_s for row in calibration_picks]
    ws = [1.0 / row.standard_uncertainty_s**2 for row in calibration_picks]
    distance_span = max(xs) - min(xs)
    if distance_span < x.minimum_calibration_distance_span_m:
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "calibration_distance_span_m": distance_span},
            notes=("Calibration distance span is below the caller minimum.",),
        )
    sw = sum(ws)
    xm = sum(w * v for w, v in zip(ws, xs, strict=True)) / sw
    ym = sum(w * v for w, v in zip(ws, ys, strict=True)) / sw
    denominator = sum(w * (v - xm) ** 2 for w, v in zip(ws, xs, strict=True))
    slowness = sum(w * (a - xm) * (b - ym) for w, a, b in zip(ws, xs, ys, strict=True)) / denominator
    offset = ym - slowness * xm
    if slowness <= 0:
        return Calculation(
            status="out_of_scope",
            values={"calibration_id": x.calibration_id, "fitted_slowness_s_m": slowness},
            notes=("Known-source records do not identify a positive propagation slowness.",),
        )
    speed = 1.0 / slowness
    if not x.minimum_supported_wave_speed_m_s <= speed <= x.maximum_supported_wave_speed_m_s:
        return Calculation(
            status="out_of_scope",
            values={"calibration_id": x.calibration_id, "wave_speed_m_s": speed, "clock_offset_s": offset},
            notes=("Fitted speed is outside caller support.",),
        )
    outside = [row.pick_id for row in holdout_picks if not min(xs) <= distance(row) <= max(xs)]
    values = {
        "calibration_id": x.calibration_id,
        "wave_speed_m_s": speed,
        "fitted_slowness_s_m": slowness,
        "clock_offset_s": offset,
        "calibration_distance_support_m": [min(xs), max(xs)],
        "outside_support_holdout_pick_ids": outside,
        "excluded_missing_or_invalid_pick_ids": excluded,
        "calibration_pick_ids": [row.pick_id for row in calibration_picks],
        "holdout_pick_ids": [row.pick_id for row in holdout_picks],
    }
    notes = (
        "Weighted fit uses known source-to-sensor distance and arrival minus reviewed emission-reference time.",
        "Only calibration picks identify speed and one clock offset; holdout picks provide residuals inside calibration distance support.",
        "No pick generation, anisotropy, dispersion, localization, mechanism, severity, acceptance, POD or probability is inferred.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    residuals = [
        row.arrival_time_s
        - sources[row.source_id].emission_reference_time_s
        - (offset + slowness * distance(row))
        for row in holdout_picks
    ]
    hws = [1.0 / row.standard_uncertainty_s**2 for row in holdout_picks]
    hsw = sum(hws)
    values["holdout_time_residual_s"] = residuals
    values["holdout_weighted_time_bias_s"] = sum(w * r for w, r in zip(hws, residuals, strict=True)) / hsw
    values["holdout_weighted_time_rmse_s"] = math.sqrt(
        sum(w * r * r for w, r in zip(hws, residuals, strict=True)) / hsw
    )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("AE speed calibration asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.acoustic_emission_wave_speed_calibration",
            AcousticEmissionWaveSpeedCalibration,
            acoustic_emission_wave_speed_calibration,
            {
                "calibration_id": "1",
                "wave_speed_m_s": "m/s",
                "fitted_slowness_s_m": "s/m",
                "clock_offset_s": "s",
                "calibration_distance_support_m": "m",
                "outside_support_holdout_pick_ids": "1",
                "excluded_missing_or_invalid_pick_ids": "1",
                "calibration_pick_ids": "1",
                "holdout_pick_ids": "1",
                "holdout_time_residual_s": "s",
                "holdout_weighted_time_bias_s": "s",
                "holdout_weighted_time_rmse_s": "s",
            },
            (
                "Weighted linear calibration of arrival minus known emission time against known source-sensor distance.",
                "One homogeneous isotropic constant speed and one clock offset are fitted from calibration picks only.",
                "Physical specimens and source groups cannot cross calibration and holdout partitions.",
            ),
            ("weighted_known_source_acoustic_emission_wave_speed_calibration",),
            context_validator=same_identity,
        )
    ]
