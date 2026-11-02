"""Non-isothermal parabolic oxidation using caller-owned rate evidence."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class OxidationRatePoint(Contract):
    point_id: str = Field(min_length=1)
    temperature_K: Positive
    parabolic_rate_m2_s: Nonnegative
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class OxidationQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_table: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_evidence(self):
        if (not self.record_valid or not self.supports_declared_table) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting oxidation qualification evidence requires a basis")
        return self


class TemperatureDependentParabolicRateTable(Contract):
    table_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    rate_unit_token: Literal["m^2/s"]
    interpolation_policy: Literal["linear_rate_vs_temperature"]
    points: tuple[OxidationRatePoint, ...] = Field(min_length=2)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_evidence: tuple[OxidationQualificationEvidence, ...] = Field(min_length=2)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_independent_table(self):
        point_ids = [row.point_id for row in self.points]
        temperatures = [row.temperature_K for row in self.points]
        evidence_ids = [row.evidence_record_id for row in self.qualification_evidence]
        if len(point_ids) != len(set(point_ids)):
            raise ValueError("oxidation rate-table point identifiers must be unique")
        if any(second <= first for first, second in zip(temperatures, temperatures[1:], strict=False)):
            raise ValueError("oxidation rate-table temperatures must be strictly increasing")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("oxidation qualification evidence identifiers must be unique")
        partitions = {row.partition for row in self.qualification_evidence}
        if partitions != {"calibration", "holdout"}:
            raise ValueError("oxidation qualification requires calibration and holdout evidence")
        calibration = {
            row.source_group_id for row in self.qualification_evidence if row.partition == "calibration"
        }
        holdout = {row.source_group_id for row in self.qualification_evidence if row.partition == "holdout"}
        if calibration & holdout:
            raise ValueError("oxidation calibration and holdout source groups must be disjoint")
        return self


class OxidationTemperatureKnot(Contract):
    knot_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    temperature_K: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid oxidation temperature knot requires a basis")
        return self


class NonisothermalParabolicOxidation(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    initial_oxide_thickness_m: Nonnegative
    temperature_history: tuple[OxidationTemperatureKnot, ...] = Field(min_length=2)
    rate_table: TemperatureDependentParabolicRateTable
    material_surface_and_environment_identity_reviewed: bool
    temperature_clock_and_interpolation_reviewed: bool
    rate_units_and_temperature_support_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    calibration_holdout_and_source_groups_reviewed: bool
    retained_parabolic_scale_regime_reviewed: bool
    rate_table_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_history(self):
        knot_ids = [row.knot_id for row in self.temperature_history]
        times = [row.elapsed_time_s for row in self.temperature_history]
        if len(knot_ids) != len(set(knot_ids)):
            raise ValueError("oxidation temperature-knot identifiers must be unique")
        if any(second <= first for first, second in zip(times, times[1:], strict=False)):
            raise ValueError("oxidation temperature-history times must be strictly increasing")
        return self


def _rate_at_temperature(table: TemperatureDependentParabolicRateTable, temperature_K: float) -> float:
    points = table.points
    for left, right in zip(points, points[1:], strict=False):
        if left.temperature_K <= temperature_K <= right.temperature_K:
            fraction = (temperature_K - left.temperature_K) / (right.temperature_K - left.temperature_K)
            return left.parabolic_rate_m2_s + fraction * (
                right.parabolic_rate_m2_s - left.parabolic_rate_m2_s
            )
    raise ValueError("temperature is outside the reviewed oxidation rate table")


def _integrate_segment(
    table: TemperatureDependentParabolicRateTable,
    start_time_s: float,
    end_time_s: float,
    start_temperature_K: float,
    end_temperature_K: float,
) -> float:
    duration = end_time_s - start_time_s
    if start_temperature_K == end_temperature_K:
        return _rate_at_temperature(table, start_temperature_K) * duration
    low = min(start_temperature_K, end_temperature_K)
    high = max(start_temperature_K, end_temperature_K)
    crossing_temperatures = [
        row.temperature_K for row in table.points[1:-1] if low < row.temperature_K < high
    ]
    if end_temperature_K < start_temperature_K:
        crossing_temperatures.reverse()
    temperatures = [start_temperature_K, *crossing_temperatures, end_temperature_K]
    integral = 0.0
    total_temperature_change = end_temperature_K - start_temperature_K
    for left_temperature, right_temperature in zip(temperatures, temperatures[1:], strict=False):
        left_fraction = (left_temperature - start_temperature_K) / total_temperature_change
        right_fraction = (right_temperature - start_temperature_K) / total_temperature_change
        sub_duration = duration * (right_fraction - left_fraction)
        left_rate = _rate_at_temperature(table, left_temperature)
        right_rate = _rate_at_temperature(table, right_temperature)
        integral += 0.5 * (left_rate + right_rate) * sub_duration
    return integral


def nonisothermal_parabolic_oxidation(x: NonisothermalParabolicOxidation) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_surface_and_environment_identity_reviewed",
            "temperature_clock_and_interpolation_reviewed",
            "rate_units_and_temperature_support_reviewed",
            "provider_lineage_and_digests_reviewed",
            "calibration_holdout_and_source_groups_reviewed",
            "retained_parabolic_scale_regime_reviewed",
            "rate_table_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_knot_ids = [row.knot_id for row in x.temperature_history if not row.record_valid]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in x.rate_table.qualification_evidence
        if not row.record_valid or not row.supports_declared_table
    ]
    identity_mismatch_fields = [
        name
        for name in ("material_condition_id", "surface_condition_id", "environment_id")
        if getattr(x, name) != getattr(x.rate_table, name)
    ]
    if missing_reviews or invalid_knot_ids or invalid_evidence_ids or identity_mismatch_fields:
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                "missing_reviews": missing_reviews,
                "invalid_temperature_knot_ids": invalid_knot_ids,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "identity_mismatch_fields": identity_mismatch_fields,
            },
            notes=(
                "Reviewed identities, history records and qualified caller-owned rate evidence are required.",
            ),
        )

    minimum_supported_temperature_K = x.rate_table.points[0].temperature_K
    maximum_supported_temperature_K = x.rate_table.points[-1].temperature_K
    outside_support_knot_ids = [
        row.knot_id
        for row in x.temperature_history
        if row.temperature_K < minimum_supported_temperature_K
        or row.temperature_K > maximum_supported_temperature_K
    ]
    if outside_support_knot_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                "table_id": x.rate_table.table_id,
                "outside_support_temperature_knot_ids": outside_support_knot_ids,
                "minimum_supported_temperature_K": minimum_supported_temperature_K,
                "maximum_supported_temperature_K": maximum_supported_temperature_K,
            },
            notes=("The caller-owned rate table is not extrapolated beyond its temperature support.",),
        )

    interval_increments_m2 = []
    cumulative_thickness_squared_increment_m2 = 0.0
    for start, end in zip(x.temperature_history, x.temperature_history[1:], strict=False):
        increment = _integrate_segment(
            x.rate_table,
            start.elapsed_time_s,
            end.elapsed_time_s,
            start.temperature_K,
            end.temperature_K,
        )
        cumulative_thickness_squared_increment_m2 += increment
        interval_increments_m2.append(
            {
                "start_knot_id": start.knot_id,
                "end_knot_id": end.knot_id,
                "thickness_squared_increment_m2": increment,
            }
        )
    final_oxide_thickness_m = math.sqrt(
        x.initial_oxide_thickness_m**2 + cumulative_thickness_squared_increment_m2
    )
    return Calculation(
        status="computed",
        values={
            "history_id": x.history_id,
            "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id,
            "table_id": x.rate_table.table_id,
            "interpolation_policy": x.rate_table.interpolation_policy,
            "interval_thickness_squared_increments": interval_increments_m2,
            "cumulative_thickness_squared_increment_m2": cumulative_thickness_squared_increment_m2,
            "final_oxide_thickness_m": final_oxide_thickness_m,
            "oxide_growth_m": final_oxide_thickness_m - x.initial_oxide_thickness_m,
        },
        notes=(
            "Piecewise-linear temperature and rate interpolation are integrated exactly after splitting at table knots.",
            "The retained-scale parabolic model excludes spallation, breakaway oxidation, metal consumption, acceptance, life and probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("non-isothermal oxidation history asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.nonisothermal_parabolic_oxidation",
            NonisothermalParabolicOxidation,
            nonisothermal_parabolic_oxidation,
            {
                "history_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "table_id": "1",
                "interpolation_policy": "1",
                "interval_thickness_squared_increments": "mixed",
                "cumulative_thickness_squared_increment_m2": "m^2",
                "final_oxide_thickness_m": "m",
                "oxide_growth_m": "m",
            },
            (
                "A retained protective scale follows a caller-qualified parabolic law over the full history.",
                "Temperature is linear between ordered history knots and rate is linear between table temperatures.",
                "The rate table is not extrapolated and material, surface and environment identities are exact.",
            ),
            ("reviewed_temperature_dependent_parabolic_oxidation_rate_table",),
            context_validator=same_identity,
        )
    ]
