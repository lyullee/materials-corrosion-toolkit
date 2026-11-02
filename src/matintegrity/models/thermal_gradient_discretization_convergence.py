"""Discretization diagnostics for externally computed transient-temperature histories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ThermalObservationQuery(Contract):
    query_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    position_m: Nonnegative
    query_definition: str = Field(min_length=1)
    comparison_weight: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ThermalQueryTemperature(Contract):
    query_id: str = Field(min_length=1)
    temperature_K: Positive
    provider_query_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_result_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid thermal query results require a basis")
        return self


class ThermalDiscretizationLevel(Contract):
    level_id: str = Field(min_length=1)
    ordinal: int = Field(ge=0)
    relationship_to_previous: Literal["initial", "nested_refinement", "nonnested_refinement"]
    spatial_characteristic_size_m: Positive
    maximum_time_step_s: Positive
    spatial_cell_count: int = Field(ge=1)
    time_step_count: int = Field(ge=1)
    refinement_path_scale: Positive
    mesh_id: str = Field(min_length=1)
    mesh_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    time_step_schedule_id: str = Field(min_length=1)
    time_step_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    query_temperatures: tuple[ThermalQueryTemperature, ...] = Field(min_length=1)
    level_record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_query_results(self):
        identifiers = [row.query_id for row in self.query_temperatures]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("thermal query result identifiers must be unique within a level")
        if not self.level_record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid thermal discretization levels require a basis")
        return self


class ThermalGradientDiscretizationConvergence(Contract):
    comparison_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    physical_scope_definition: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_condition_id: str = Field(min_length=1)
    boundary_condition_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_property_state_id: str = Field(min_length=1)
    material_property_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_queries: tuple[ThermalObservationQuery, ...] = Field(min_length=1)
    refinement_levels: tuple[ThermalDiscretizationLevel, ...] = Field(min_length=2)
    refinement_path_scale_definition: str = Field(min_length=1)
    temperature_change_normalization_scale_K: Positive
    maximum_adjacent_weighted_rms_change_K: Nonnegative
    maximum_adjacent_relative_rms_change: Nonnegative
    observed_order_refinement_ratio_tolerance: Nonnegative
    geometry_boundary_property_and_provider_identity_reviewed: bool
    input_result_mesh_and_time_step_digests_reviewed: bool
    common_query_identity_units_and_weights_reviewed: bool
    refinement_order_and_relationships_reviewed: bool
    refinement_path_scale_definition_reviewed: bool
    level_validity_and_missingness_reviewed: bool
    diagnostic_norm_tolerances_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_refinement_design(self):
        query_ids = [row.query_id for row in self.common_queries]
        if len(set(query_ids)) != len(query_ids):
            raise ValueError("common thermal query identifiers must be unique")
        level_ids = [row.level_id for row in self.refinement_levels]
        if len(set(level_ids)) != len(level_ids):
            raise ValueError("thermal refinement level identifiers must be unique")
        expected_query_ids = set(query_ids)
        for index, level in enumerate(self.refinement_levels):
            if level.ordinal != index:
                raise ValueError("thermal refinement ordinals must be contiguous from zero")
            expected_relationship = "initial" if index == 0 else None
            if expected_relationship is not None and level.relationship_to_previous != expected_relationship:
                raise ValueError("the first thermal refinement level must be initial")
            if index > 0 and level.relationship_to_previous == "initial":
                raise ValueError("only the first thermal refinement level can be initial")
            if {row.query_id for row in level.query_temperatures} != expected_query_ids:
                raise ValueError("every thermal refinement level must contain the complete common query set")
        for coarse, fine in zip(self.refinement_levels, self.refinement_levels[1:], strict=False):
            if fine.spatial_characteristic_size_m > coarse.spatial_characteristic_size_m:
                raise ValueError("spatial characteristic size cannot increase under refinement")
            if fine.maximum_time_step_s > coarse.maximum_time_step_s:
                raise ValueError("maximum time step cannot increase under refinement")
            if (
                fine.spatial_characteristic_size_m == coarse.spatial_characteristic_size_m
                and fine.maximum_time_step_s == coarse.maximum_time_step_s
            ):
                raise ValueError("each thermal level must refine space, time or both")
            if fine.spatial_cell_count < coarse.spatial_cell_count:
                raise ValueError("spatial cell count cannot decrease under refinement")
            if fine.time_step_count < coarse.time_step_count:
                raise ValueError("time-step count cannot decrease under refinement")
            if fine.refinement_path_scale >= coarse.refinement_path_scale:
                raise ValueError("refinement path scale must strictly decrease")
        return self


def thermal_gradient_discretization_convergence(
    x: ThermalGradientDiscretizationConvergence,
) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "geometry_boundary_property_and_provider_identity_reviewed",
            "input_result_mesh_and_time_step_digests_reviewed",
            "common_query_identity_units_and_weights_reviewed",
            "refinement_order_and_relationships_reviewed",
            "refinement_path_scale_definition_reviewed",
            "level_validity_and_missingness_reviewed",
            "diagnostic_norm_tolerances_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_level_ids = [row.level_id for row in x.refinement_levels if not row.level_record_valid]
    invalid_query_result_ids = [
        f"{level.level_id}:{row.query_id}"
        for level in x.refinement_levels
        for row in level.query_temperatures
        if not row.record_valid
    ]
    if missing_reviews or invalid_level_ids or invalid_query_result_ids:
        return Calculation(
            status="needs_data",
            values={
                "comparison_id": x.comparison_id,
                "missing_reviews": missing_reviews,
                "invalid_level_ids": invalid_level_ids,
                "invalid_query_result_ids": invalid_query_result_ids,
            },
            notes=("Reviewed, complete and valid external solver refinement results are required.",),
        )

    weights = {row.query_id: row.comparison_weight for row in x.common_queries}
    temperatures = {
        level.level_id: {row.query_id: row.temperature_K for row in level.query_temperatures}
        for level in x.refinement_levels
    }
    weight_sum = math.fsum(weights.values())
    transitions = []
    for coarse, fine in zip(x.refinement_levels, x.refinement_levels[1:], strict=False):
        changes = {
            query_id: temperatures[fine.level_id][query_id] - temperatures[coarse.level_id][query_id]
            for query_id in weights
        }
        weighted_bias = math.fsum(weights[key] * changes[key] for key in weights) / weight_sum
        weighted_rms = math.sqrt(math.fsum(weights[key] * changes[key] ** 2 for key in weights) / weight_sum)
        maximum_query_id = max(changes, key=lambda key: abs(changes[key]))
        path_step = coarse.refinement_path_scale - fine.refinement_path_scale
        transitions.append(
            {
                "coarse_level_id": coarse.level_id,
                "fine_level_id": fine.level_id,
                "relationship_to_previous": fine.relationship_to_previous,
                "spatial_refinement_ratio": (
                    coarse.spatial_characteristic_size_m / fine.spatial_characteristic_size_m
                ),
                "time_refinement_ratio": coarse.maximum_time_step_s / fine.maximum_time_step_s,
                "refinement_path_ratio": coarse.refinement_path_scale / fine.refinement_path_scale,
                "weighted_signed_temperature_change_K": weighted_bias,
                "weighted_rms_temperature_change_K": weighted_rms,
                "relative_weighted_rms_temperature_change": (
                    weighted_rms / x.temperature_change_normalization_scale_K
                ),
                "weighted_rms_change_per_refinement_path_scale_K": weighted_rms / path_step,
                "maximum_absolute_temperature_change_K": abs(changes[maximum_query_id]),
                "maximum_change_query_id": maximum_query_id,
                "query_temperature_changes_K": changes,
                "meets_declared_rms_diagnostics": (
                    weighted_rms <= x.maximum_adjacent_weighted_rms_change_K
                    and weighted_rms / x.temperature_change_normalization_scale_K
                    <= x.maximum_adjacent_relative_rms_change
                ),
            }
        )

    observed_order_diagnostics = []
    for index in range(1, len(transitions)):
        previous = transitions[index - 1]
        current = transitions[index]
        first_ratio = previous["refinement_path_ratio"]
        second_ratio = current["refinement_path_ratio"]
        first_change = previous["weighted_rms_temperature_change_K"]
        second_change = current["weighted_rms_temperature_change_K"]
        ratio_scale = max(first_ratio, second_ratio)
        ratios_match = abs(first_ratio - second_ratio) <= (
            x.observed_order_refinement_ratio_tolerance * ratio_scale
        )
        observed_order = None
        unavailable_basis = None
        if not ratios_match:
            unavailable_basis = "adjacent refinement-path ratios differ beyond the declared tolerance"
        elif first_ratio <= 1.0 or second_ratio <= 1.0:
            unavailable_basis = "refinement-path ratios must exceed one"
        elif first_change <= 0.0 or second_change <= 0.0:
            unavailable_basis = "positive adjacent weighted RMS changes are required"
        else:
            observed_order = math.log(first_change / second_change) / math.log(
                math.sqrt(first_ratio * second_ratio)
            )
        observed_order_diagnostics.append(
            {
                "coarse_level_id": x.refinement_levels[index - 1].level_id,
                "middle_level_id": x.refinement_levels[index].level_id,
                "fine_level_id": x.refinement_levels[index + 1].level_id,
                "refinement_ratios_match": ratios_match,
                "diagnostic_observed_order": observed_order,
                "observed_order_unavailable_basis": unavailable_basis,
            }
        )

    return Calculation(
        status="computed",
        values={
            "comparison_id": x.comparison_id,
            "component_id": x.component_id,
            "provider_id": x.provider_id,
            "solver_id": x.solver_id,
            "solver_revision": x.solver_revision,
            "level_ids": [row.level_id for row in x.refinement_levels],
            "common_query_ids": [row.query_id for row in x.common_queries],
            "adjacent_level_diagnostics": transitions,
            "observed_order_diagnostics": observed_order_diagnostics,
            "all_adjacent_levels_meet_declared_rms_diagnostics": all(
                row["meets_declared_rms_diagnostics"] for row in transitions
            ),
            "missing_reviews": [],
        },
        notes=(
            "Temperature changes compare common query values already computed by the declared external solver.",
            "Observed order is a path-scale diagnostic only when adjacent refinement ratios match; it is not a convergence proof or error bound.",
            "No PDE, thermal stress, parameter fit, acceptance, life or probability is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id, x.time_basis) != (
            context.asset_id,
            context.location_id,
            context.time_basis,
        ):
            raise ValueError("thermal discretization comparison identity and clock must match run context")

    return [
        ModelSpec(
            "structural.thermal_gradient_discretization_convergence",
            ThermalGradientDiscretizationConvergence,
            thermal_gradient_discretization_convergence,
            {
                "comparison_id": "1",
                "component_id": "1",
                "provider_id": "1",
                "solver_id": "1",
                "solver_revision": "1",
                "level_ids": "1",
                "common_query_ids": "1",
                "adjacent_level_diagnostics": "mixed",
                "observed_order_diagnostics": "mixed",
                "all_adjacent_levels_meet_declared_rms_diagnostics": "1",
                "missing_reviews": "1",
            },
            (
                "All refinement levels share exact geometry, boundary, property, provider and common-query identity.",
                "Spatial and time discretization metadata and per-level input, result, mesh and time-step digests remain explicit.",
                "Adjacent changes and observed-order values are diagnostics rather than convergence claims.",
            ),
            ("authored_external_thermal_discretization_refinement_diagnostic",),
            context_validator=same_identity,
        )
    ]
