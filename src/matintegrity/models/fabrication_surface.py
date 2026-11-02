"""Reviewed surface-cleanliness observations evaluated against caller-owned limits."""

from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class DepositedLayerGeometry(Contract):
    layer_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    thickness_m: Positive
    thickness_origin: Literal["measured", "procedure_target"]
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class LayerGeometryEvent(Contract):
    event_id: str = Field(min_length=1)
    kind: Literal["deposit", "surface_removal"]
    thickness_m: Positive
    thickness_origin: Literal["measured", "procedure_target"]
    layer_id: str | None = Field(default=None, min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def deposition_identity(self):
        if self.kind == "deposit":
            if self.layer_id is None or self.material_condition_id is None:
                raise ValueError("deposition requires new layer and material identities")
        elif self.layer_id is not None or self.material_condition_id is not None:
            raise ValueError("surface removal does not create a material or layer")
        return self


class DepositionRemovalHistory(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    outward_normal_direction_id: str = Field(min_length=1)
    initial_layers: tuple[DepositedLayerGeometry, ...] = ()
    events: tuple[LayerGeometryEvent, ...] = Field(min_length=1)
    history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_normal_and_uniform_local_thickness_reviewed: bool
    event_order_and_thickness_origins_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_identities(self):
        layers = [row.layer_id for row in self.initial_layers] + [
            row.layer_id for row in self.events if row.kind == "deposit"
        ]
        if len(layers) != len(set(layers)):
            raise ValueError("layer identities cannot be reused, including removed layers")
        ids = [row.event_id for row in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("event identities must be unique in supplied execution order")
        if self.history_digest != canonical_digest(
            {
                "initial_layers": [row.model_dump(mode="json") for row in self.initial_layers],
                "events": [row.model_dump(mode="json") for row in self.events],
            }
        ):
            raise ValueError("history digest must bind normalized initial layers and ordered events")
        return self


def deposition_removal_history(x: DepositionRemovalHistory) -> Calculation:
    base = dict(
        physical_region_id=x.physical_region_id,
        coordinate_frame_id=x.coordinate_frame_id,
        outward_normal_direction_id=x.outward_normal_direction_id,
        history_digest=x.history_digest,
    )
    if not (
        x.common_normal_and_uniform_local_thickness_reviewed and x.event_order_and_thickness_origins_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    layers = [
        dict(
            layer_id=row.layer_id,
            material_condition_id=row.material_condition_id,
            retained_thickness_m=row.thickness_m,
            thickness_origin=row.thickness_origin,
            record_digest=row.record_digest,
        )
        for row in x.initial_layers
    ]
    deposited = []
    removed = []
    history = []
    try:
        initial_total = math.fsum(row["retained_thickness_m"] for row in layers)
        for event in x.events:
            affected = []
            if event.kind == "deposit":
                layers.append(
                    dict(
                        layer_id=event.layer_id,
                        material_condition_id=event.material_condition_id,
                        retained_thickness_m=event.thickness_m,
                        thickness_origin=event.thickness_origin,
                        record_digest=event.record_digest,
                    )
                )
                deposited.append(event.thickness_m)
            else:
                available = math.fsum(row["retained_thickness_m"] for row in layers)
                if event.thickness_m > available:
                    return Calculation(
                        status="out_of_scope",
                        values=base | {"unsupported_event_id": event.event_id},
                        notes=(
                            "Removal reaches beyond the declared layer stack; substrate geometry is not inferred.",
                        ),
                    )
                remaining = event.thickness_m
                for layer in reversed(layers):
                    if remaining <= 0.0:
                        break
                    take = min(remaining, layer["retained_thickness_m"])
                    if take > 0.0:
                        layer["retained_thickness_m"] -= take
                        remaining -= take
                        affected.append(dict(layer_id=layer["layer_id"], removed_thickness_m=take))
                if remaining > 0.0:
                    raise ArithmeticError("removal cannot be resolved at this numeric scale")
                removed.append(event.thickness_m)
            total = math.fsum(row["retained_thickness_m"] for row in layers)
            if not math.isfinite(total):
                raise ArithmeticError("nonfinite retained thickness")
            history.append(
                dict(
                    event_id=event.event_id,
                    kind=event.kind,
                    thickness_origin=event.thickness_origin,
                    total_retained_thickness_m=total,
                    removed_by_layer=affected,
                    retained_layers=[dict(layer) for layer in layers],
                )
            )
        total_deposited = math.fsum(deposited)
        total_removed = math.fsum(removed)
        balance_residual = math.fsum((total, -initial_total, -total_deposited, total_removed))
        if not all(
            math.isfinite(v) for v in (initial_total, total_deposited, total_removed, balance_residual)
        ):
            raise ArithmeticError("nonfinite geometry balance")
    except (OverflowError, ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope", values=base, notes=("Layer geometry exceeds finite arithmetic support.",)
        )
    return Calculation(
        values=base
        | dict(
            initial_total_thickness_m=initial_total,
            total_deposited_thickness_m=total_deposited,
            total_removed_thickness_m=total_removed,
            final_total_thickness_m=total,
            thickness_balance_residual_m=balance_residual,
            final_layers=layers,
            event_history=history,
            exposed_top_layer_id=next(
                (row["layer_id"] for row in reversed(layers) if row["retained_thickness_m"] > 0), None
            ),
        ),
        notes=(
            "Initial layers are ordered from substrate outward; events follow supplied execution order.",
            "Uniform local thickness bookkeeping only: no dilution, penetration, area, mass, plasticity or metallurgical qualification.",
            "Measured and procedure-target thickness origins remain distinct; target geometry is not a measurement.",
        ),
    )


class SurfaceProfileRoughness(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    measurement_direction_id: str = Field(min_length=1)
    position_m: tuple[float, ...] = Field(min_length=2)
    height_m: tuple[float, ...] = Field(min_length=2)
    profile_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    processing_basis: str = Field(min_length=1)
    profile_filter_form_removal_and_direction_reviewed: bool
    piecewise_linear_interpretation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def profile_arrays(self):
        if len(self.position_m) != len(self.height_m):
            raise ValueError("profile positions and heights must align")
        if any(b <= a for a, b in zip(self.position_m, self.position_m[1:], strict=False)):
            raise ValueError("profile positions must strictly increase")
        if self.profile_digest != canonical_digest(
            {"position_m": self.position_m, "height_m": self.height_m}
        ):
            raise ValueError("profile digest must bind exact positions and heights")
        return self


def surface_profile_roughness(x: SurfaceProfileRoughness) -> Calculation:
    base = {
        "profile_id": x.profile_id,
        "physical_specimen_id": x.physical_specimen_id,
        "coordinate_frame_id": x.coordinate_frame_id,
        "measurement_direction_id": x.measurement_direction_id,
        "profile_digest": x.profile_digest,
    }
    if not (
        x.profile_filter_form_removal_and_direction_reviewed and x.piecewise_linear_interpretation_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    length = x.position_m[-1] - x.position_m[0]
    if not math.isfinite(length):
        return Calculation(status="out_of_scope", values=base)
    weights = [(b - a) / length for a, b in zip(x.position_m, x.position_m[1:], strict=False)]
    if any(not math.isfinite(weight) or weight <= 0.0 for weight in weights):
        return Calculation(status="out_of_scope", values=base)
    weight_sum = math.fsum(weights)
    scale = max(abs(height) for height in x.height_m) or 1.0
    normalized = [height / scale for height in x.height_m]
    mean = (
        math.fsum(
            weight * (a + b) / 2.0 for weight, a, b in zip(weights, normalized, normalized[1:], strict=False)
        )
        / weight_sum
    )
    centered = [height - mean for height in normalized]
    absolute_integrals = []
    square_integrals = []
    for weight, a, b in zip(weights, centered, centered[1:], strict=False):
        same_sign = (a >= 0.0 and b >= 0.0) or (a <= 0.0 and b <= 0.0)
        mean_absolute = (abs(a) + abs(b)) / 2.0 if same_sign else (a * a + b * b) / (2.0 * (abs(a) + abs(b)))
        absolute_integrals.append(weight * mean_absolute)
        square_integrals.append(weight * (a * a + a * b + b * b) / 3.0)
    metrics = {
        "evaluation_length_m": length,
        "removed_length_weighted_mean_height_m": mean * scale,
        "profile_Ra_m": math.fsum(absolute_integrals) / weight_sum * scale,
        "profile_Rq_m": math.sqrt(math.fsum(square_integrals) / weight_sum) * scale,
        "evaluation_peak_height_Rp_m": max(centered) * scale,
        "evaluation_valley_depth_Rv_m": -min(centered) * scale,
        "evaluation_total_height_Rt_m": (max(centered) - min(centered)) * scale,
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        return Calculation(status="out_of_scope", values=base)
    return Calculation(
        values=base | metrics,
        notes=(
            "Exact length-weighted integrals of the centered piecewise-linear supplied profile; Ra resolves sign crossings inside segments and Rq integrates each segment's squared linear height.",
            "Rp/Rv/Rt describe this whole evaluation trace, not averages across standard-specific sampling lengths. No automatic filter, cutoff, tilt/form removal, Rz conversion, instrument qualification or surface acceptance is inferred.",
        ),
    )


class CoatingDamagePatch(Contract):
    patch_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    damaged_area_m2: Positive
    maximum_length_m: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CoatingDamageAreaInventory(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    coated_component_id: str = Field(min_length=1)
    original_coated_area_m2: Positive
    inspected_area_m2: Nonnegative
    patches: tuple[CoatingDamagePatch, ...] = ()
    patch_identity_and_nonoverlapping_area_basis_reviewed: bool
    inspected_and_original_area_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def scope_and_identity(self):
        if self.inspected_area_m2 > self.original_coated_area_m2:
            raise ValueError("inspected area cannot exceed the original coated area")
        if len({row.patch_id for row in self.patches}) != len(self.patches):
            raise ValueError("damage patch IDs must be unique")
        return self


def coating_damage_area_inventory(x: CoatingDamageAreaInventory) -> Calculation:
    base = {
        "coated_component_id": x.coated_component_id,
        "inventory_digest": canonical_digest(x.model_dump(mode="json")),
    }
    if not (
        x.patch_identity_and_nonoverlapping_area_basis_reviewed
        and x.inspected_and_original_area_scope_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    try:
        damaged = math.fsum(row.damaged_area_m2 for row in x.patches)
    except OverflowError:
        return Calculation(
            status="out_of_scope", values=base, notes=("Summed damage area exceeds numeric support.",)
        )
    if damaged > x.inspected_area_m2:
        return Calculation(
            status="out_of_scope", values=base, notes=("Nonoverlapping damaged area exceeds inspected area.",)
        )
    maximum_area = max((row.damaged_area_m2 for row in x.patches), default=0.0)
    maximum_length = max((row.maximum_length_m for row in x.patches), default=0.0)
    return Calculation(
        values=base
        | {
            "known_damaged_area_m2": damaged,
            "known_damage_fraction_of_original_coated_area": damaged / x.original_coated_area_m2,
            "damage_fraction_of_inspected_area": damaged / x.inspected_area_m2
            if x.inspected_area_m2 > 0.0
            else None,
            "inspected_area_fraction": x.inspected_area_m2 / x.original_coated_area_m2,
            "full_declared_area_inspected": x.inspected_area_m2 == x.original_coated_area_m2,
            "maximum_patch_area_m2": maximum_area,
            "maximum_patch_length_m": maximum_length,
            "maximum_area_patch_ids": [
                row.patch_id for row in x.patches if row.damaged_area_m2 == maximum_area
            ],
            "maximum_length_patch_ids": [
                row.patch_id for row in x.patches if row.maximum_length_m == maximum_length
            ],
        },
        notes=(
            "Known damage is measured within an explicit inspected extent. Partial coverage does not establish total damage or absence of damage outside it.",
            "Patches must have reviewed nonoverlapping areas. Area and length extrema can come from different patches; their IDs remain separate.",
            "This inventory does not choose a repair route, restore corrosion resistance or establish coating acceptance or life.",
        ),
    )


class SurfaceProfilePoint(Contract):
    point_id: str = Field(min_length=1)
    reference_position_m: tuple[float, float, float]
    measured_position_m: tuple[float, float, float]
    outward_unit_normal: tuple[float, float, float]
    normal_deviation_expanded_uncertainty_m: Nonnegative
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unit_normal(self):
        if not math.isclose(math.hypot(*self.outward_unit_normal), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("surface normal must be an explicitly supplied unit vector")
        return self


class SurfaceProfileDeviation(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    reference_geometry_id: str = Field(min_length=1)
    measurement_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_geometry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_length_m: Positive
    points: tuple[SurfaceProfilePoint, ...] = Field(min_length=1)
    caller_minimum_signed_deviation_m: float
    caller_maximum_signed_deviation_m: float
    point_correspondence_coordinate_frame_and_normals_reviewed: bool
    measurement_uncertainty_and_limit_authority_reviewed: bool
    limit_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_points_and_ordered_bounds(self):
        if len({row.point_id for row in self.points}) != len(self.points):
            raise ValueError("surface profile point IDs must be unique")
        if self.caller_minimum_signed_deviation_m > self.caller_maximum_signed_deviation_m:
            raise ValueError("signed deviation bounds must be ordered")
        return self


def surface_profile_deviation(x: SurfaceProfileDeviation) -> Calculation:
    if not (
        x.point_correspondence_coordinate_frame_and_normals_reviewed
        and x.measurement_uncertainty_and_limit_authority_reviewed
    ):
        return Calculation(status="needs_data", values={"coordinate_frame_id": x.coordinate_frame_id})
    rows = []
    for point in x.points:
        delta = tuple(
            a - b for a, b in zip(point.measured_position_m, point.reference_position_m, strict=True)
        )
        if not all(math.isfinite(value) for value in delta):
            return Calculation(status="out_of_scope", values={"numeric_range_point_id": point.point_id})
        try:
            deviation = math.fsum(
                value * normal for value, normal in zip(delta, point.outward_unit_normal, strict=True)
            )
        except (OverflowError, ValueError):
            return Calculation(status="out_of_scope", values={"numeric_range_point_id": point.point_id})
        lower = deviation - point.normal_deviation_expanded_uncertainty_m
        upper = deviation + point.normal_deviation_expanded_uncertainty_m
        normalized = deviation / x.reference_length_m
        if not all(math.isfinite(value) for value in (deviation, lower, upper, normalized)):
            return Calculation(status="out_of_scope", values={"numeric_range_point_id": point.point_id})
        within = lower >= x.caller_minimum_signed_deviation_m and upper <= x.caller_maximum_signed_deviation_m
        outside = upper < x.caller_minimum_signed_deviation_m or lower > x.caller_maximum_signed_deviation_m
        rows.append(
            {
                "point_id": point.point_id,
                "signed_normal_deviation_m": deviation,
                "normalized_signed_deviation": normalized,
                "lower_m": lower,
                "upper_m": upper,
                "declared_interval_outcome": "within_bounds"
                if within
                else "outside_bounds"
                if outside
                else "overlaps_boundary",
            }
        )
    return Calculation(
        values={
            "coordinate_frame_id": x.coordinate_frame_id,
            "reference_geometry_id": x.reference_geometry_id,
            "point_results": rows,
        },
        notes=(
            "Positive deviation follows the caller-supplied outward normal. No registration, closest-point matching, interpolation, whole-surface coverage or code acceptance is inferred.",
            "Interval outcomes compare supplied bounds only; uncertainty intervals are not joint statistical confidence statements.",
        ),
    )


class PreparedSurfaceArea(Contract):
    area_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    preparation_process_id: str = Field(min_length=1)
    target_area_m2: Positive
    inspected_area_m2: Nonnegative
    uninspected_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def coverage(self):
        if self.inspected_area_m2 > self.target_area_m2:
            raise ValueError("inspected area cannot exceed the declared target area")
        if self.inspected_area_m2 < self.target_area_m2 and not self.uninspected_basis:
            raise ValueError("incomplete coverage requires an uninspected-area basis")
        return self


class CleanlinessObservation(Contract):
    observation_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    value: Nonnegative
    expanded_uncertainty: Nonnegative
    unit_token: str = Field(min_length=1)
    sample_location_description: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class DeclaredCleanlinessRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    comparator: Literal["maximum", "minimum"]
    limit_value: Nonnegative
    unit_token: str = Field(min_length=1)
    requirement_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class SurfaceCleanlinessAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    areas: list[PreparedSurfaceArea] = Field(min_length=1)
    observations: list[CleanlinessObservation] = Field(default_factory=list)
    declared_requirements: list[DeclaredCleanlinessRequirement] = Field(min_length=1)
    areas_mutually_exclusive_reviewed: bool
    preparation_identity_reviewed: bool
    method_applicability_reviewed: bool
    calibration_and_uncertainty_reviewed: bool
    observation_mapping_reviewed: bool
    requirement_authority_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_and_units(self):
        area_ids = [area.area_id for area in self.areas]
        observation_ids = [item.observation_id for item in self.observations]
        requirement_ids = [item.requirement_id for item in self.declared_requirements]
        if len(set(area_ids)) != len(area_ids):
            raise ValueError("prepared-surface area IDs must be unique")
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("cleanliness observation IDs must be unique")
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("cleanliness requirement IDs must be unique")
        known = set(area_ids)
        if {item.area_id for item in self.observations} - known:
            raise ValueError("every cleanliness observation must reference a declared area")
        if {item.area_id for item in self.declared_requirements} - known:
            raise ValueError("every cleanliness requirement must reference a declared area")
        units = {(item.area_id, item.metric_id): item.unit_token for item in self.declared_requirements}
        if len(units) != len(self.declared_requirements):
            raise ValueError("declare at most one requirement for each area and metric")
        for item in self.observations:
            expected = units.get((item.area_id, item.metric_id))
            if expected is not None and item.unit_token != expected:
                raise ValueError("observation and declared requirement units must match exactly")
        return self


def surface_cleanliness_assessment(x: SurfaceCleanlinessAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "areas_mutually_exclusive_reviewed",
            "preparation_identity_reviewed",
            "method_applicability_reviewed",
            "calibration_and_uncertainty_reviewed",
            "observation_mapping_reviewed",
            "requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.observations and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")

    rows = []
    missing_requirement_observations = []
    for requirement in x.declared_requirements:
        observations = [
            item
            for item in x.observations
            if item.area_id == requirement.area_id and item.metric_id == requirement.metric_id
        ]
        if not observations:
            missing_requirement_observations.append(requirement.requirement_id)
            rows.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "area_id": requirement.area_id,
                    "metric_id": requirement.metric_id,
                    "comparator": requirement.comparator,
                    "limit_value": requirement.limit_value,
                    "unit_token": requirement.unit_token,
                    "observation_count": 0,
                    "governing_observation_id": None,
                    "governing_conservative_value": None,
                    "declared_requirement_satisfied": None,
                }
            )
            continue
        if requirement.comparator == "maximum":
            governing = max(observations, key=lambda item: item.value + item.expanded_uncertainty)
            conservative = governing.value + governing.expanded_uncertainty
            satisfied = conservative <= requirement.limit_value
        else:
            governing = min(observations, key=lambda item: item.value - item.expanded_uncertainty)
            conservative = governing.value - governing.expanded_uncertainty
            satisfied = conservative >= requirement.limit_value
        rows.append(
            {
                "requirement_id": requirement.requirement_id,
                "area_id": requirement.area_id,
                "metric_id": requirement.metric_id,
                "comparator": requirement.comparator,
                "limit_value": requirement.limit_value,
                "unit_token": requirement.unit_token,
                "observation_count": len(observations),
                "governing_observation_id": governing.observation_id,
                "governing_conservative_value": conservative,
                "declared_requirement_satisfied": satisfied,
            }
        )

    target_area = sum(area.target_area_m2 for area in x.areas)
    inspected_area = sum(area.inspected_area_m2 for area in x.areas)
    decisions = [row["declared_requirement_satisfied"] for row in rows]
    status = "needs_data" if missing_reviews or missing_requirement_observations else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "target_area_m2": target_area,
            "inspected_area_m2": inspected_area,
            "uninspected_area_m2": target_area - inspected_area,
            "coverage_fraction": inspected_area / target_area,
            "observation_count": len(x.observations),
            "observation_counts_by_metric": dict(Counter(item.metric_id for item in x.observations)),
            "requirement_rows": rows,
            "missing_requirement_observation_ids": missing_requirement_observations,
            "missing_reviews": missing_reviews,
            "all_declared_requirements_satisfied": (
                all(decision is True for decision in decisions)
                if not missing_requirement_observations
                else None
            ),
        },
        notes=(
            "Limits, units and their authority are caller-supplied; no coating, fabrication or design-code acceptance rule is embedded.",
            "The conservative comparison adds uncertainty to maximum-limited observations and subtracts it from minimum-limited observations.",
            "Coverage and measured cleanliness do not establish coating life, adhesion, corrosion rate or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("surface profile asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.deposition_removal_history",
            DepositionRemovalHistory,
            deposition_removal_history,
            {
                "physical_region_id": "1",
                "coordinate_frame_id": "1",
                "outward_normal_direction_id": "1",
                "history_digest": "1",
                "initial_total_thickness_m": "m",
                "total_deposited_thickness_m": "m",
                "total_removed_thickness_m": "m",
                "final_total_thickness_m": "m",
                "thickness_balance_residual_m": "m",
                "final_layers": "mixed",
                "event_history": "mixed",
                "exposed_top_layer_id": "1",
            },
            (
                "Reviewed uniform local layer thickness along one common normal; explicit deposition and top-down removal events.",
            ),
            ("ordered_layer_deposition_removal_balance",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "inspection.surface_profile_roughness",
            SurfaceProfileRoughness,
            surface_profile_roughness,
            {
                "profile_id": "1",
                "physical_specimen_id": "1",
                "coordinate_frame_id": "1",
                "measurement_direction_id": "1",
                "profile_digest": "1",
                "evaluation_length_m": "m",
                "removed_length_weighted_mean_height_m": "m",
                "profile_Ra_m": "m",
                "profile_Rq_m": "m",
                "evaluation_peak_height_Rp_m": "m",
                "evaluation_valley_depth_Rv_m": "m",
                "evaluation_total_height_Rt_m": "m",
            },
            (
                "Caller-reviewed filtered profile and evaluation direction; explicitly piecewise-linear positions/heights with a length-weighted mean removed.",
            ),
            ("length_weighted_profile_roughness_integrals",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.coating_damage_area_inventory",
            CoatingDamageAreaInventory,
            coating_damage_area_inventory,
            {
                "coated_component_id": "1",
                "inventory_digest": "1",
                "known_damaged_area_m2": "m^2",
                "known_damage_fraction_of_original_coated_area": "1",
                "damage_fraction_of_inspected_area": "1",
                "inspected_area_fraction": "1",
                "full_declared_area_inspected": "1",
                "maximum_patch_area_m2": "m^2",
                "maximum_patch_length_m": "m",
                "maximum_area_patch_ids": "1",
                "maximum_length_patch_ids": "1",
            },
            (
                "Explicit inspected extent and reviewed nonoverlapping damage patch measurements; no uninspected-area inference.",
            ),
            ("coating_damage_patch_area_geometry",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.surface_profile_deviation",
            SurfaceProfileDeviation,
            surface_profile_deviation,
            {"coordinate_frame_id": "1", "reference_geometry_id": "1", "point_results": "mixed"},
            ("Exact caller-reviewed point pairing in one SI coordinate frame and unit outward normals.",),
            ("signed_surface_normal_projection",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.surface_cleanliness_assessment",
            SurfaceCleanlinessAssessment,
            surface_cleanliness_assessment,
            {
                "assessment_id": "1",
                "procedure_id": "1",
                "procedure_revision": "1",
                "target_area_m2": "m^2",
                "inspected_area_m2": "m^2",
                "uninspected_area_m2": "m^2",
                "coverage_fraction": "1",
                "observation_count": "1",
                "observation_counts_by_metric": "1",
                "requirement_rows": "mixed",
                "missing_requirement_observation_ids": "1",
                "missing_reviews": "1",
                "all_declared_requirements_satisfied": "1",
            },
            (
                "Area coverage is summed only after the caller reviews areas as mutually exclusive.",
                "Observation values and expanded uncertainties share the exact caller-declared unit token.",
                "Every comparison is against a caller-owned requirement with separately preserved authority evidence.",
            ),
            ("declared_surface_cleanliness_comparison",),
        ),
    ]
