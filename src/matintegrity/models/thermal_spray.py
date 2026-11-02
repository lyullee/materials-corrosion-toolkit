"""Thermal-spray condition evidence compared with caller-owned requirements."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ThermalSprayRegion(Contract):
    region_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    nominal_area_m2: Positive
    examined_area_m2: Nonnegative
    surface_preparation_id: str = Field(min_length=1)
    deposition_pass_group_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_coverage(self):
        if self.examined_area_m2 > self.nominal_area_m2:
            raise ValueError("examined thermal-spray area cannot exceed nominal region area")
        return self


class ThermalSprayObservation(Contract):
    observation_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["qualification", "production"]
    metric_id: str = Field(min_length=1)
    metric_kind: Literal[
        "layer_thickness",
        "porosity_fraction",
        "bond_strength",
        "oxide_content_fraction",
        "surface_roughness",
        "user_defined",
    ]
    metric_definition: str = Field(min_length=1)
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def explicit_missingness(self):
        if self.value is None:
            if self.record_valid or self.expanded_uncertainty is not None or self.result_digest is not None:
                raise ValueError(
                    "a missing thermal-spray value must be invalid without uncertainty or digest"
                )
            if not self.missing_or_invalid_basis:
                raise ValueError("a missing thermal-spray value requires a basis")
        elif self.expanded_uncertainty is None or self.result_digest is None:
            raise ValueError("a reported thermal-spray value requires uncertainty and result digest")
        if not self.record_valid and not self.missing_or_invalid_basis:
            raise ValueError("an invalid thermal-spray observation requires a basis")
        return self


class DeclaredThermalSprayRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_kind: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    applicable_region_ids: tuple[str, ...] = Field(min_length=1)
    required_partitions: tuple[Literal["qualification", "production"], ...] = Field(min_length=1)
    comparator: Literal["minimum", "maximum"]
    limit_value: float
    unit_token: str = Field(min_length=1)
    authority_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_scope(self):
        if len(set(self.applicable_region_ids)) != len(self.applicable_region_ids):
            raise ValueError("thermal-spray requirement region IDs must be unique")
        if len(set(self.required_partitions)) != len(self.required_partitions):
            raise ValueError("thermal-spray required partitions must be unique")
        return self


class ThermalSprayConditionAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    spray_process_id: str = Field(min_length=1)
    feedstock_lot_id: str = Field(min_length=1)
    substrate_material_condition_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    procedure_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    regions: tuple[ThermalSprayRegion, ...] = Field(min_length=1)
    observations: tuple[ThermalSprayObservation, ...] = Field(min_length=1)
    declared_requirements: tuple[DeclaredThermalSprayRequirement, ...] = Field(min_length=1)
    system_and_lot_identity_reviewed: bool
    surface_preparation_and_pass_traceability_reviewed: bool
    region_coverage_reviewed: bool
    measurement_methods_reviewed: bool
    uncertainty_and_provider_lineage_reviewed: bool
    requirement_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_linked_records(self):
        region_ids = [row.region_id for row in self.regions]
        observation_ids = [row.observation_id for row in self.observations]
        requirement_ids = [row.requirement_id for row in self.declared_requirements]
        for values, label in (
            (region_ids, "thermal-spray region"),
            (observation_ids, "thermal-spray observation"),
            (requirement_ids, "thermal-spray requirement"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        known_regions = set(region_ids)
        if {row.region_id for row in self.observations} - known_regions:
            raise ValueError("every thermal-spray observation must reference a declared region")
        if any(set(row.applicable_region_ids) - known_regions for row in self.declared_requirements):
            raise ValueError("every thermal-spray requirement region must be declared")
        keys = [
            (row.region_id, row.partition, row.metric_id, row.physical_specimen_id)
            for row in self.observations
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("thermal-spray observation keys must be unique")
        partition_groups: dict[str, set[str]] = defaultdict(set)
        for row in self.observations:
            partition_groups[row.partition].add(row.source_group_id)
        if partition_groups["qualification"] & partition_groups["production"]:
            raise ValueError("qualification and production source groups must be disjoint")
        return self


def thermal_spray_condition(x: ThermalSprayConditionAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "system_and_lot_identity_reviewed",
            "surface_preparation_and_pass_traceability_reviewed",
            "region_coverage_reviewed",
            "measurement_methods_reviewed",
            "uncertainty_and_provider_lineage_reviewed",
            "requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    comparison_rows = []
    incomplete_requirement_scopes = []
    for requirement in x.declared_requirements:
        for region_id in requirement.applicable_region_ids:
            for partition in requirement.required_partitions:
                candidates = [
                    row
                    for row in x.observations
                    if row.region_id == region_id
                    and row.partition == partition
                    and row.metric_id == requirement.metric_id
                ]
                exact = [
                    row
                    for row in candidates
                    if row.metric_kind == requirement.metric_kind
                    and row.metric_definition == requirement.metric_definition
                    and row.unit_token == requirement.unit_token
                    and row.record_valid
                    and row.value is not None
                ]
                scope_id = f"{requirement.requirement_id}:{region_id}:{partition}"
                complete = bool(candidates) and len(exact) == len(candidates)
                if not complete:
                    incomplete_requirement_scopes.append(scope_id)
                conservative_values = [
                    row.value + row.expanded_uncertainty
                    if requirement.comparator == "maximum"
                    else row.value - row.expanded_uncertainty
                    for row in exact
                ]
                comparisons = [
                    value <= requirement.limit_value
                    if requirement.comparator == "maximum"
                    else value >= requirement.limit_value
                    for value in conservative_values
                ]
                comparison_rows.append(
                    {
                        "requirement_scope_id": scope_id,
                        "requirement_id": requirement.requirement_id,
                        "region_id": region_id,
                        "partition": partition,
                        "metric_id": requirement.metric_id,
                        "unit_token": requirement.unit_token,
                        "matching_observation_ids": [row.observation_id for row in exact],
                        "complete_exact_comparison": complete,
                        "all_observations_satisfy_declared_requirement": (
                            all(comparisons) if complete and comparisons else None
                        ),
                        "governing_conservative_value": (
                            max(conservative_values)
                            if conservative_values and requirement.comparator == "maximum"
                            else min(conservative_values)
                            if conservative_values
                            else None
                        ),
                    }
                )

    status = (
        "needs_data"
        if missing_reviews or invalid_observation_ids or incomplete_requirement_scopes
        else "computed"
    )
    total_area = sum(row.nominal_area_m2 for row in x.regions)
    examined_area = sum(row.examined_area_m2 for row in x.regions)
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "coating_system_id": x.coating_system_id,
            "spray_process_id": x.spray_process_id,
            "feedstock_lot_id": x.feedstock_lot_id,
            "nominal_area_m2": total_area,
            "examined_area_m2": examined_area,
            "examined_area_fraction": examined_area / total_area,
            "comparison_rows": comparison_rows,
            "invalid_observation_ids": invalid_observation_ids,
            "incomplete_requirement_scope_ids": incomplete_requirement_scopes,
            "physical_specimen_ids": sorted({row.physical_specimen_id for row in x.observations}),
            "source_group_ids_by_partition": {
                partition: sorted(
                    {row.source_group_id for row in x.observations if row.partition == partition}
                )
                for partition in ("qualification", "production")
            },
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Comparisons use exact metric definitions and unit tokens with caller-provided expanded uncertainty.",
            "Qualification and production records remain separate and source groups cannot cross those partitions.",
            "The summary does not predict coating life, corrosion rate, structural capacity, defect probability or acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("thermal-spray asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.thermal_spray_condition",
            ThermalSprayConditionAssessment,
            thermal_spray_condition,
            {
                "assessment_id": "1",
                "coating_system_id": "1",
                "spray_process_id": "1",
                "feedstock_lot_id": "1",
                "nominal_area_m2": "m^2",
                "examined_area_m2": "m^2",
                "examined_area_fraction": "1",
                "comparison_rows": "mixed",
                "invalid_observation_ids": "1",
                "incomplete_requirement_scope_ids": "1",
                "physical_specimen_ids": "1",
                "source_group_ids_by_partition": "1",
                "missing_reviews": "1",
            },
            (
                "System, process, feedstock lot, substrate condition and procedure identities are caller-reviewed.",
                "Metric definitions, units, uncertainty and one-sided requirements are caller-owned.",
                "Qualification and production observations are evidence partitions, not assumed independent populations.",
            ),
            ("partitioned_thermal_spray_condition_accounting",),
            context_validator=same_identity,
        )
    ]
