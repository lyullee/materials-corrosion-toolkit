"""Transport, handling and erection records with caller-owned metric limits."""

from __future__ import annotations

import math
from collections import Counter

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class EquipmentMassComponent(Contract):
    component_id: str = Field(min_length=1)
    mass_kg: Positive
    center_of_mass_position_m: tuple[float, float, float]
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class EquipmentMassProperties(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    assembly_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    components: tuple[EquipmentMassComponent, ...] = Field(min_length=1)
    complete_installed_inventory_and_common_frame_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_components(self):
        if len({row.component_id for row in self.components}) != len(self.components):
            raise ValueError("mass inventory component IDs must be unique")
        return self


def equipment_mass_properties(x: EquipmentMassProperties) -> Calculation:
    base = {
        "assembly_id": x.assembly_id,
        "coordinate_frame_id": x.coordinate_frame_id,
        "inventory_digest": canonical_digest(x.model_dump(mode="json")),
        "component_ids": [row.component_id for row in x.components],
    }
    if not x.complete_installed_inventory_and_common_frame_reviewed:
        return Calculation(status="needs_data", values=base)
    try:
        mass = math.fsum(row.mass_kg for row in x.components)
        centroid = [
            math.fsum((row.mass_kg / mass) * row.center_of_mass_position_m[axis] for row in x.components)
            for axis in range(3)
        ]
    except (OverflowError, ValueError):
        return Calculation(
            status="out_of_scope", values=base, notes=("Mass or weighted position exceeds numeric support.",)
        )
    if not all(math.isfinite(value) for value in (mass, *centroid)):
        return Calculation(status="out_of_scope", values=base)
    return Calculation(
        values=base | {"total_mass_kg": mass, "center_of_mass_position_m": centroid},
        notes=(
            "Only declared installed components are aggregated in one reviewed frame; no missing accessory mass or coordinate transform is inferred.",
            "Mass properties alone do not establish support load distribution, local stress or lifting capacity.",
        ),
    )


class EquipmentTwoSupportLift(Contract):
    inventory: EquipmentMassProperties
    first_support_id: str = Field(min_length=1)
    second_support_id: str = Field(min_length=1)
    first_support_position_xy_m: tuple[float, float]
    second_support_position_xy_m: tuple[float, float]
    body_to_world_rotation_rad: float
    gravity_m_s2: Positive
    caller_load_multiplier: Positive
    minimum_supported_horizontal_span_m: Positive
    planar_xy_projection_parallel_vertical_reactions_and_rigid_body_reviewed: bool
    load_multiplier_and_orientation_applicability_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @property
    def asset_id(self):
        return self.inventory.asset_id

    @property
    def location_id(self):
        return self.inventory.location_id

    @model_validator(mode="after")
    def distinct_supports(self):
        if self.first_support_id == self.second_support_id:
            raise ValueError("two distinct support identities are required")
        return self


def equipment_two_support_lift(x: EquipmentTwoSupportLift) -> Calculation:
    mass_result = equipment_mass_properties(x.inventory)
    base = {
        "assembly_id": x.inventory.assembly_id,
        "coordinate_frame_id": x.inventory.coordinate_frame_id,
        "inventory_digest": canonical_digest(x.inventory.model_dump(mode="json")),
        "first_support_id": x.first_support_id,
        "second_support_id": x.second_support_id,
    }
    if mass_result.status != "computed":
        return Calculation(status=mass_result.status, values=base, notes=mass_result.notes)
    if not (
        x.planar_xy_projection_parallel_vertical_reactions_and_rigid_body_reviewed
        and x.load_multiplier_and_orientation_applicability_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    cosine, sine = math.cos(x.body_to_world_rotation_rad), math.sin(x.body_to_world_rotation_rad)

    def horizontal(point):
        return cosine * point[0] - sine * point[1]

    # Relative body coordinates avoid subtracting large translated world positions.
    delta = tuple(
        b - a for a, b in zip(x.first_support_position_xy_m, x.second_support_position_xy_m, strict=True)
    )
    cg_delta = tuple(
        b - a
        for a, b in zip(
            x.first_support_position_xy_m, mass_result.values["center_of_mass_position_m"][:2], strict=True
        )
    )
    span, cg_lever = horizontal(delta), horizontal(cg_delta)
    if (
        not all(math.isfinite(v) for v in (span, cg_lever))
        or abs(span) < x.minimum_supported_horizontal_span_m
    ):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Projected support span is singular or outside the caller-supported minimum.",),
        )
    weight = mass_result.values["total_mass_kg"] * x.gravity_m_s2 * x.caller_load_multiplier
    fraction = cg_lever / span
    first, second = weight * (1.0 - fraction), weight * fraction
    if weight <= 0.0 or not all(math.isfinite(v) for v in (weight, fraction, first, second)):
        return Calculation(
            status="out_of_scope", values=base, notes=("Load or reaction exceeds numeric support.",)
        )
    outside = not 0.0 <= fraction <= 1.0
    return Calculation(
        status="out_of_scope" if outside else "computed",
        values=base
        | {
            "total_mass_kg": mass_result.values["total_mass_kg"],
            "factored_vertical_load_N": weight,
            "signed_horizontal_support_span_m": span,
            "center_of_mass_horizontal_lever_m": cg_lever,
            "first_vertical_reaction_N": first,
            "second_vertical_reaction_N": second,
            "uplift_required": outside,
        },
        notes=(
            "Static planar rigid-body equilibrium with two parallel vertical reactions only; signed negative reaction indicates an unsupported uplift configuration.",
            "Caller multiplier is not a simulated impact. No sling tension, crane chart, lug stress/buckling, contact redistribution, dynamic stability or lifting approval is inferred.",
        ),
    )


class HandlingActivityInterval(Contract):
    interval_id: str = Field(min_length=1)
    activity_id: str = Field(min_length=1)
    activity_kind: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("handling activity interval must have positive duration")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid activity interval requires an invalid-record basis")
        return self


class TransportMetricObservation(Contract):
    observation_id: str = Field(min_length=1)
    interval_id: str = Field(min_length=1)
    observation_time_s: Nonnegative
    metric_id: str = Field(min_length=1)
    value: float | None = None
    unit: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_observation(self):
        if self.record_valid and self.value is None:
            raise ValueError("a valid metric observation requires a value")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid metric observation requires an invalid-record basis")
        return self


class TransportMetricLimit(Contract):
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    limit_basis: str = Field(min_length=1)
    caller_disposition_id_if_outside: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_limit(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a metric limit requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("metric bounds must be ordered")
        return self


class HandlingInspection(Contract):
    inspection_id: str = Field(min_length=1)
    stage_id: str = Field(min_length=1)
    inspection_time_s: Nonnegative
    inspection_type: str = Field(min_length=1)
    reported_finding: str | None = None
    caller_disposition_id: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if self.record_valid and not self.reported_finding:
            raise ValueError("a valid handling inspection requires a reported finding")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid handling inspection requires an invalid-record basis")
        return self


class TransportErectionHistory(Contract):
    record_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    activity_intervals: list[HandlingActivityInterval] = Field(min_length=1)
    metric_observations: list[TransportMetricObservation] = Field(default_factory=list)
    metric_limits: list[TransportMetricLimit] = Field(default_factory=list)
    inspections: list[HandlingInspection] = Field(default_factory=list)
    required_inspection_stage_ids: list[str] = Field(default_factory=list)
    clock_and_activity_coverage_reviewed: bool
    metric_identity_and_units_reviewed: bool
    metric_limits_reviewed: bool
    inspection_stage_mapping_reviewed: bool
    disposition_mapping_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_and_clock(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("transport and erection horizon must have positive duration")

        interval_ids = [row.interval_id for row in self.activity_intervals]
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("activity interval IDs must be unique")
        intervals_by_id = {row.interval_id: row for row in self.activity_intervals}
        previous_end = self.horizon_start_s
        for row in self.activity_intervals:
            if row.start_time_s < self.horizon_start_s or row.end_time_s > self.horizon_end_s:
                raise ValueError("activity intervals must remain inside the history horizon")
            if row.start_time_s < previous_end:
                raise ValueError("activity intervals must be ordered and cannot overlap")
            previous_end = row.end_time_s

        observation_ids = [row.observation_id for row in self.metric_observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("metric observation IDs must be unique")
        for row in self.metric_observations:
            interval = intervals_by_id.get(row.interval_id)
            if interval is None:
                raise ValueError("every metric observation must reference a declared activity interval")
            if not interval.start_time_s <= row.observation_time_s <= interval.end_time_s:
                raise ValueError("metric observation time must lie inside its activity interval")

        limit_ids = [row.metric_id for row in self.metric_limits]
        if len(set(limit_ids)) != len(limit_ids):
            raise ValueError("metric limit IDs must be unique")

        inspection_ids = [row.inspection_id for row in self.inspections]
        if len(set(inspection_ids)) != len(inspection_ids):
            raise ValueError("handling inspection IDs must be unique")
        if any(
            not self.horizon_start_s <= row.inspection_time_s <= self.horizon_end_s
            for row in self.inspections
        ):
            raise ValueError("handling inspection times must remain inside the history horizon")
        if len(set(self.required_inspection_stage_ids)) != len(self.required_inspection_stage_ids):
            raise ValueError("required inspection stage IDs must be unique")
        if any(not value.strip() for value in self.required_inspection_stage_ids):
            raise ValueError("required inspection stage IDs cannot be blank")
        return self


def transport_erection_history(x: TransportErectionHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "clock_and_activity_coverage_reviewed",
            "metric_identity_and_units_reviewed",
            "metric_limits_reviewed",
            "inspection_stage_mapping_reviewed",
            "disposition_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    represented_duration = sum(row.end_time_s - row.start_time_s for row in x.activity_intervals)
    invalid_activity_duration = sum(
        row.end_time_s - row.start_time_s for row in x.activity_intervals if not row.record_valid
    )
    uncovered_duration = x.horizon_end_s - x.horizon_start_s - represented_duration
    missing_activity_duration = invalid_activity_duration + uncovered_duration

    limits = {row.metric_id: row for row in x.metric_limits}
    unmatched_observations = []
    unit_mismatch_observations = []
    outside_rows = []
    valid_metric_counts = Counter()
    for row in x.metric_observations:
        if not row.record_valid:
            continue
        valid_metric_counts[row.metric_id] += 1
        limit = limits.get(row.metric_id)
        if limit is None:
            unmatched_observations.append(row.observation_id)
            continue
        if row.unit != limit.unit:
            unit_mismatch_observations.append(row.observation_id)
            continue
        below = limit.minimum_value is not None and row.value < limit.minimum_value
        above = limit.maximum_value is not None and row.value > limit.maximum_value
        if below or above:
            outside_rows.append(
                {
                    "observation_id": row.observation_id,
                    "interval_id": row.interval_id,
                    "observation_time_s": row.observation_time_s,
                    "metric_id": row.metric_id,
                    "value": row.value,
                    "unit": row.unit,
                    "below_declared_minimum": below,
                    "above_declared_maximum": above,
                    "caller_disposition_id": limit.caller_disposition_id_if_outside,
                }
            )

    invalid_observation_ids = [row.observation_id for row in x.metric_observations if not row.record_valid]
    invalid_inspection_ids = [row.inspection_id for row in x.inspections if not row.record_valid]
    completed_stages = {row.stage_id for row in x.inspections if row.record_valid}
    missing_stages = [stage for stage in x.required_inspection_stage_ids if stage not in completed_stages]
    caller_dispositions = Counter(
        row.caller_disposition_id
        for row in x.inspections
        if row.record_valid and row.caller_disposition_id is not None
    )

    incomplete = (
        missing_reviews
        or missing_activity_duration > 0
        or invalid_observation_ids
        or invalid_inspection_ids
        or unmatched_observations
        or unit_mismatch_observations
        or missing_stages
    )
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "record_id": x.record_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "clock_id": x.clock_id,
            "horizon_duration_s": x.horizon_end_s - x.horizon_start_s,
            "represented_activity_duration_s": represented_duration,
            "invalid_activity_duration_s": invalid_activity_duration,
            "uncovered_activity_duration_s": uncovered_duration,
            "missing_activity_duration_s": missing_activity_duration,
            "invalid_activity_interval_ids": [
                row.interval_id for row in x.activity_intervals if not row.record_valid
            ],
            "metric_observation_count": len(x.metric_observations),
            "valid_metric_counts": dict(valid_metric_counts),
            "invalid_metric_observation_ids": invalid_observation_ids,
            "unmatched_metric_observation_ids": unmatched_observations,
            "unit_mismatch_observation_ids": unit_mismatch_observations,
            "outside_declared_limit_count": len(outside_rows),
            "outside_declared_limit_observations": outside_rows,
            "inspection_count": len(x.inspections),
            "invalid_inspection_ids": invalid_inspection_ids,
            "completed_inspection_stage_ids": sorted(completed_stages),
            "missing_required_inspection_stage_ids": missing_stages,
            "caller_inspection_disposition_counts": dict(caller_dispositions),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Metric limits and disposition identifiers are caller-owned; an outside-limit observation is not an embedded acceptance decision.",
            "Point observations do not establish unobserved continuous conditions, and activity gaps or invalid records are never bridged.",
            "The record summary does not infer damage, defect size, degradation rate, remaining life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("transport-history asset and location must match the assessment context")

    return [
        ModelSpec(
            "fabrication.equipment_mass_properties",
            EquipmentMassProperties,
            equipment_mass_properties,
            {
                "assembly_id": "1",
                "coordinate_frame_id": "1",
                "inventory_digest": "1",
                "component_ids": "1",
                "total_mass_kg": "kg",
                "center_of_mass_position_m": "m",
            },
            ("Complete caller-declared installed mass inventory in one explicit coordinate frame.",),
            ("equipment_mass_weighted_centroid",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.equipment_two_support_lift",
            EquipmentTwoSupportLift,
            equipment_two_support_lift,
            {
                "assembly_id": "1",
                "coordinate_frame_id": "1",
                "inventory_digest": "1",
                "first_support_id": "1",
                "second_support_id": "1",
                "total_mass_kg": "kg",
                "factored_vertical_load_N": "N",
                "signed_horizontal_support_span_m": "m",
                "center_of_mass_horizontal_lever_m": "m",
                "first_vertical_reaction_N": "N",
                "second_vertical_reaction_N": "N",
                "uplift_required": "1",
            },
            (
                "Caller-reviewed body XY plane, explicit rotation about Z, rigid body and two parallel vertical support reactions.",
            ),
            ("planar_two_support_static_equilibrium",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.transport_erection_history",
            TransportErectionHistory,
            transport_erection_history,
            {
                "horizon_duration_s": "s",
                "represented_activity_duration_s": "s",
                "invalid_activity_duration_s": "s",
                "uncovered_activity_duration_s": "s",
                "missing_activity_duration_s": "s",
                "metric_observation_count": "count",
                "outside_declared_limit_count": "count",
                "inspection_count": "count",
            },
            (
                "Ordered handling, transport and erection activity intervals remain separate from metric observations, inspections and caller-owned limits.",
                "Missing coverage, invalid records, unmatched metrics, unit conflicts and absent caller-required inspection stages prevent a complete-history result.",
            ),
            ("transport_erection_record_accounting",),
            context_validator=same_identity,
        ),
    ]
