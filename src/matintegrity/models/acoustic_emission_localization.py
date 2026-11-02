"""Weighted arrival-time localization under a declared constant-speed medium."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AESensorLocation(Contract):
    sensor_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]
    calibration_id: str = Field(min_length=1)
    coupling_state_id: str = Field(min_length=1)
    calibration_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    coupling_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AEArrivalPick(Contract):
    pick_id: str = Field(min_length=1)
    sensor_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    arrival_time_s: Nonnegative | None = None
    standard_uncertainty_s: Positive | None = None
    pick_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
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
                raise ValueError("valid AE picks require arrival, uncertainty and result digest")
            if self.missing_or_invalid_basis is not None:
                raise ValueError("valid AE picks cannot carry a missing basis")
        elif (
            any(
                value is not None
                for value in (self.arrival_time_s, self.standard_uncertainty_s, self.result_digest)
            )
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid AE picks require a basis and no result fields")
        return self


class AELocalizationEvent(Contract):
    event_id: str = Field(min_length=1)
    physical_source_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    clock_id: str = Field(min_length=1)
    picks: tuple[AEArrivalPick, ...] = Field(min_length=4)
    known_source_position_m: tuple[float, float, float]
    known_source_position_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_picks(self):
        for attribute in ("pick_id", "sensor_id", "channel_id"):
            values = [getattr(row, attribute) for row in self.picks]
            if len(set(values)) != len(values):
                raise ValueError(f"AE event {attribute} values must be unique")
        if any(row.clock_id != self.clock_id for row in self.picks):
            raise ValueError("AE pick clocks must match the event clock")
        return self


class AEArrivalLocalization(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    sensors: tuple[AESensorLocation, ...] = Field(min_length=4)
    events: tuple[AELocalizationEvent, ...] = Field(min_length=2)
    wave_speed_m_s: Positive
    wave_speed_standard_uncertainty_m_s: Nonnegative
    wave_speed_provider_id: str = Field(min_length=1)
    wave_speed_provider_revision: str = Field(min_length=1)
    wave_speed_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_supported_wave_speed_m_s: Positive
    maximum_supported_wave_speed_m_s: Positive
    support_minimum_position_m: tuple[float, float, float]
    support_maximum_position_m: tuple[float, float, float]
    maximum_iterations: int = Field(ge=1, le=100)
    position_tolerance_m: Positive
    sensor_frame_channel_calibration_and_coupling_reviewed: bool
    homogeneous_isotropic_constant_speed_assumption_reviewed: bool
    pick_clock_method_uncertainty_and_digests_reviewed: bool
    physical_source_partitions_and_independence_reviewed: bool
    caller_position_support_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_support_and_partitions(self):
        if self.maximum_supported_wave_speed_m_s < self.minimum_supported_wave_speed_m_s:
            raise ValueError("AE wave-speed support must be ordered")
        if any(
            high <= low
            for low, high in zip(
                self.support_minimum_position_m, self.support_maximum_position_m, strict=True
            )
        ):
            raise ValueError("AE position support bounds must be ordered")
        for attribute in ("sensor_id", "channel_id"):
            values = [getattr(row, attribute) for row in self.sensors]
            if len(set(values)) != len(values):
                raise ValueError(f"AE sensor {attribute} values must be unique")
        if any(row.coordinate_frame_id != self.coordinate_frame_id for row in self.sensors):
            raise ValueError("all AE sensors must share the assessment coordinate frame")
        sensor_channels = {row.sensor_id: row.channel_id for row in self.sensors}
        source_partitions = {}
        group_partitions = {}
        for event in self.events:
            for pick in event.picks:
                if (
                    pick.sensor_id not in sensor_channels
                    or sensor_channels[pick.sensor_id] != pick.channel_id
                ):
                    raise ValueError("AE picks must reference declared sensor-channel pairs")
            for mapping, key, label in (
                (source_partitions, event.physical_source_id, "physical source"),
                (group_partitions, event.source_group_id, "source group"),
            ):
                prior = mapping.setdefault(key, event.partition)
                if prior != event.partition:
                    raise ValueError(f"AE {label} cannot cross calibration and holdout partitions")
        return self


def _localize(sensor_rows, pick_rows, speed, speed_sigma, maximum_iterations, tolerance):
    import numpy as np

    positions = np.asarray([row.position_m for row in sensor_rows], dtype=float)
    arrivals = np.asarray([row.arrival_time_s for row in pick_rows], dtype=float)
    pick_sigma = np.asarray([row.standard_uncertainty_s for row in pick_rows], dtype=float)
    state = np.empty(4)
    state[:3] = positions.mean(axis=0)
    state[3] = arrivals.min() - np.linalg.norm(positions - state[:3], axis=1).mean() / speed
    rank = 0
    for iteration in range(1, maximum_iterations + 1):
        delta = state[:3] - positions
        distances = np.linalg.norm(delta, axis=1)
        if np.any(distances == 0):
            distances = np.maximum(distances, 1e-15)
        predicted = state[3] + distances / speed
        residual = arrivals - predicted
        sigma = np.sqrt(pick_sigma**2 + (distances * speed_sigma / speed**2) ** 2)
        jacobian = np.column_stack((delta / (speed * distances[:, None]), np.ones(len(arrivals))))
        weighted_jacobian = jacobian / sigma[:, None]
        weighted_residual = residual / sigma
        rank = int(np.linalg.matrix_rank(weighted_jacobian))
        if rank < 4:
            return None, rank, iteration
        step, *_ = np.linalg.lstsq(weighted_jacobian, weighted_residual, rcond=None)
        state += step
        if np.linalg.norm(step[:3]) <= tolerance:
            break
    delta = state[:3] - positions
    distances = np.linalg.norm(delta, axis=1)
    residual = arrivals - (state[3] + distances / speed)
    return (state, residual), rank, iteration


def acoustic_emission_arrival_localization(x: AEArrivalLocalization) -> Calculation:
    reviews = (
        "sensor_frame_channel_calibration_and_coupling_reviewed",
        "homogeneous_isotropic_constant_speed_assumption_reviewed",
        "pick_clock_method_uncertainty_and_digests_reviewed",
        "physical_source_partitions_and_independence_reviewed",
        "caller_position_support_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    invalid_or_missing = [
        pick.pick_id for event in x.events for pick in event.picks if pick.record_status != "valid"
    ]
    if missing_reviews or invalid_or_missing:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_or_missing_pick_ids": invalid_or_missing,
            },
            notes=("Localization is withheld until reviewed valid arrival picks are complete.",),
        )
    if not x.minimum_supported_wave_speed_m_s <= x.wave_speed_m_s <= x.maximum_supported_wave_speed_m_s:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "reason": "wave_speed_outside_support"},
            notes=("The supplied wave speed is outside caller support.",),
        )
    sensors_by_id = {row.sensor_id: row for row in x.sensors}
    rows = []
    rank_fail = []
    outside = []
    for event in x.events:
        sensors = [sensors_by_id[p.sensor_id] for p in event.picks]
        solved, rank, iterations = _localize(
            sensors,
            event.picks,
            x.wave_speed_m_s,
            x.wave_speed_standard_uncertainty_m_s,
            x.maximum_iterations,
            x.position_tolerance_m,
        )
        if solved is None:
            rank_fail.append(event.event_id)
            rows.append(
                {
                    "event_id": event.event_id,
                    "partition": event.partition,
                    "design_rank": rank,
                    "status": "rank_deficient",
                }
            )
            continue
        state, residual = solved
        position = state[:3].tolist()
        within = all(
            low <= value <= high
            for low, value, high in zip(
                x.support_minimum_position_m, position, x.support_maximum_position_m, strict=True
            )
        )
        if not within:
            outside.append(event.event_id)
        error = math.dist(position, event.known_source_position_m)
        rows.append(
            {
                "event_id": event.event_id,
                "partition": event.partition,
                "estimated_position_m": position,
                "estimated_origin_time_s": float(state[3]),
                "arrival_residual_s": [float(v) for v in residual],
                "weighted_residual_rms": math.sqrt(
                    sum(
                        (float(r) / p.standard_uncertainty_s) ** 2
                        for r, p in zip(residual, event.picks, strict=True)
                    )
                    / len(event.picks)
                ),
                "design_rank": rank,
                "iterations": iterations,
                "within_caller_position_support": within,
                "known_source_position_error_m": error,
            }
        )
    values = {
        "assessment_id": x.assessment_id,
        "coordinate_frame_id": x.coordinate_frame_id,
        "event_localizations": rows,
        "rank_deficient_event_ids": rank_fail,
        "outside_position_support_event_ids": outside,
        "holdout_position_errors_m": [
            row["known_source_position_error_m"]
            for row in rows
            if row.get("partition") == "holdout" and "known_source_position_error_m" in row
        ],
    }
    notes = (
        "Arrival picks and wave speed are caller inputs; the model does not generate picks or estimate speed.",
        "Weighted least squares assumes a homogeneous isotropic constant-speed medium and reports geometry rank and residuals.",
        "No event mechanism, damage severity, acceptance, life, POD or failure probability is produced.",
    )
    if rank_fail:
        return Calculation(status="needs_data", values=values, notes=notes)
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("AE localization asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.acoustic_emission_arrival_localization",
            AEArrivalLocalization,
            acoustic_emission_arrival_localization,
            {
                "assessment_id": "1",
                "coordinate_frame_id": "1",
                "event_localizations": "mixed",
                "rank_deficient_event_ids": "1",
                "outside_position_support_event_ids": "1",
                "holdout_position_errors_m": "m",
            },
            (
                "Multi-sensor arrival-time localization in one reviewed frame with fixed caller-supplied wave speed.",
                "Pick and speed uncertainties weight the nonlinear least-squares residuals.",
                "Calibration and holdout physical sources and source groups are disjoint.",
            ),
            ("weighted_constant_speed_acoustic_emission_localization",),
            context_validator=same_identity,
        )
    ]
