"""Production-weld test evidence compared with caller-owned requirements."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ProductionTestSpecimen(Contract):
    specimen_id: str = Field(min_length=1)
    physical_source_group_id: str = Field(min_length=1)
    extraction_location: str = Field(min_length=1)
    orientation_definition: str = Field(min_length=1)
    specimen_preparation_id: str = Field(min_length=1)
    source_mapping_valid: bool
    invalid_mapping_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_mapping_explained(self):
        if not self.source_mapping_valid and not self.invalid_mapping_basis:
            raise ValueError("an invalid specimen source mapping requires a basis")
        return self


class CallerProductionTestRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    test_kind: Literal["destructive", "nde"]
    test_method_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    maximum_expanded_uncertainty: Nonnegative | None = None
    minimum_available_record_count: int = Field(ge=1)
    minimum_distinct_physical_source_groups: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)
    disposition_id_if_outside: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_requirement(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a production-test requirement needs at least one value bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("production-test requirement bounds must be ordered")
        return self


class ProductionTestObservation(Contract):
    observation_id: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    test_kind: Literal["destructive", "nde"]
    test_method_id: str = Field(min_length=1)
    physical_source_group_id: str = Field(min_length=1)
    specimen_id: str | None = None
    examination_location: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    observed_value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    coverage_factor: Positive | None = None
    uncertainty_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        quantitative = (
            self.observed_value,
            self.expanded_uncertainty,
            self.coverage_factor,
            self.uncertainty_basis,
            self.result_digest,
        )
        if self.record_available and any(value is None for value in quantitative):
            raise ValueError(
                "an available production-test observation requires value, uncertainty and digest"
            )
        if not self.record_available and not self.missing_basis:
            raise ValueError("an unavailable production-test observation requires a missingness basis")
        if not self.record_available and any(value is not None for value in quantitative):
            raise ValueError("an unavailable production-test observation cannot carry quantitative results")
        if self.test_kind == "destructive" and self.specimen_id is None:
            raise ValueError("a destructive production test must reference a physical specimen")
        return self


class ProductionWeldTestEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    production_weld_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    consumable_lot_id: str = Field(min_length=1)
    material_lot_id: str = Field(min_length=1)
    specimens: tuple[ProductionTestSpecimen, ...] = ()
    observations: tuple[ProductionTestObservation, ...] = Field(min_length=1)
    requirements: tuple[CallerProductionTestRequirement, ...] = Field(min_length=1)
    weld_procedure_and_lot_identity_reviewed: bool
    specimen_source_mapping_reviewed: bool
    test_method_and_location_reviewed: bool
    metric_definitions_and_units_reviewed: bool
    uncertainty_records_reviewed: bool
    provider_identity_and_state_reviewed: bool
    result_digests_reviewed: bool
    missingness_reviewed: bool
    caller_requirement_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identifiers(self):
        specimen_ids = [row.specimen_id for row in self.specimens]
        observation_ids = [row.observation_id for row in self.observations]
        requirement_ids = [row.requirement_id for row in self.requirements]
        for values, name in (
            (specimen_ids, "production-test specimen"),
            (observation_ids, "production-test observation"),
            (requirement_ids, "production-test requirement"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} identifiers must be unique")
        specimens = {row.specimen_id: row for row in self.specimens}
        for observation in self.observations:
            if observation.specimen_id is None:
                continue
            specimen = specimens.get(observation.specimen_id)
            if specimen is None:
                raise ValueError("every referenced production-test specimen must be declared")
            if observation.physical_source_group_id != specimen.physical_source_group_id:
                raise ValueError("observation and specimen physical-source groups must match")
        return self


def production_weld_test_evidence(x: ProductionWeldTestEvidenceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "weld_procedure_and_lot_identity_reviewed",
            "specimen_source_mapping_reviewed",
            "test_method_and_location_reviewed",
            "metric_definitions_and_units_reviewed",
            "uncertainty_records_reviewed",
            "provider_identity_and_state_reviewed",
            "result_digests_reviewed",
            "missingness_reviewed",
            "caller_requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    requirements = {row.requirement_id: row for row in x.requirements}
    unknown_requirement_observation_ids = []
    definition_mismatch_observation_ids = []
    unavailable_observation_ids = []
    comparison_rows = []
    observations_by_requirement: dict[str, list[ProductionTestObservation]] = {
        row.requirement_id: [] for row in x.requirements
    }
    for observation in x.observations:
        requirement = requirements.get(observation.requirement_id)
        if requirement is None:
            unknown_requirement_observation_ids.append(observation.observation_id)
            continue
        if (
            observation.test_kind != requirement.test_kind
            or observation.test_method_id != requirement.test_method_id
            or observation.metric_definition != requirement.metric_definition
            or observation.unit != requirement.unit
        ):
            definition_mismatch_observation_ids.append(observation.observation_id)
            continue
        if not observation.record_available:
            unavailable_observation_ids.append(observation.observation_id)
            continue
        observations_by_requirement[requirement.requirement_id].append(observation)
        low = observation.observed_value - observation.expanded_uncertainty
        high = observation.observed_value + observation.expanded_uncertainty
        nominal_within = (
            requirement.minimum_value is None or observation.observed_value >= requirement.minimum_value
        ) and (requirement.maximum_value is None or observation.observed_value <= requirement.maximum_value)
        interval_within = (requirement.minimum_value is None or low >= requirement.minimum_value) and (
            requirement.maximum_value is None or high <= requirement.maximum_value
        )
        uncertainty_within = (
            requirement.maximum_expanded_uncertainty is None
            or observation.expanded_uncertainty <= requirement.maximum_expanded_uncertainty
        )
        comparison_rows.append(
            {
                "observation_id": observation.observation_id,
                "requirement_id": requirement.requirement_id,
                "physical_source_group_id": observation.physical_source_group_id,
                "specimen_id": observation.specimen_id,
                "observed_value": observation.observed_value,
                "expanded_uncertainty": observation.expanded_uncertainty,
                "uncertainty_interval_minimum": low,
                "uncertainty_interval_maximum": high,
                "unit": observation.unit,
                "nominal_value_within_caller_requirement": nominal_within,
                "uncertainty_interval_within_caller_requirement": interval_within,
                "uncertainty_within_caller_requirement": uncertainty_within,
                "disposition_id_if_outside": requirement.disposition_id_if_outside,
            }
        )

    requirement_coverage = []
    insufficient_requirement_ids = []
    for requirement in x.requirements:
        available = observations_by_requirement[requirement.requirement_id]
        source_groups = {row.physical_source_group_id for row in available}
        sufficient = (
            len(available) >= requirement.minimum_available_record_count
            and len(source_groups) >= requirement.minimum_distinct_physical_source_groups
        )
        if not sufficient:
            insufficient_requirement_ids.append(requirement.requirement_id)
        requirement_coverage.append(
            {
                "requirement_id": requirement.requirement_id,
                "available_record_count": len(available),
                "required_record_count": requirement.minimum_available_record_count,
                "distinct_physical_source_group_count": len(source_groups),
                "required_distinct_physical_source_groups": requirement.minimum_distinct_physical_source_groups,
                "coverage_sufficient": sufficient,
            }
        )

    invalid_specimen_ids = [row.specimen_id for row in x.specimens if not row.source_mapping_valid]
    incomplete = (
        missing_reviews
        or unknown_requirement_observation_ids
        or definition_mismatch_observation_ids
        or unavailable_observation_ids
        or insufficient_requirement_ids
        or invalid_specimen_ids
    )
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "assessment_id": x.assessment_id,
            "production_weld_id": x.production_weld_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "consumable_lot_id": x.consumable_lot_id,
            "material_lot_id": x.material_lot_id,
            "specimen_count": len(x.specimens),
            "invalid_specimen_source_mapping_ids": invalid_specimen_ids,
            "observation_count": len(x.observations),
            "unavailable_observation_ids": unavailable_observation_ids,
            "unknown_requirement_observation_ids": unknown_requirement_observation_ids,
            "definition_mismatch_observation_ids": definition_mismatch_observation_ids,
            "requirement_coverage": requirement_coverage,
            "insufficient_requirement_ids": insufficient_requirement_ids,
            "caller_requirement_comparisons": comparison_rows,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Production-weld identity, procedure and lot lineage, specimen mapping, provider state and result digests remain explicit evidence fields.",
            "Requirement comparisons use exact caller-owned method, metric and unit identities; they are not welding-code acceptance declarations.",
            "No defect classification, fracture calculation, remaining-life estimate or failure probability is inferred from the observations.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("production-weld test assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.production_weld_test_evidence",
            ProductionWeldTestEvidenceAssessment,
            production_weld_test_evidence,
            {
                "assessment_id": "1",
                "production_weld_id": "1",
                "procedure_id": "1",
                "procedure_revision": "1",
                "consumable_lot_id": "1",
                "material_lot_id": "1",
                "specimen_count": "1",
                "invalid_specimen_source_mapping_ids": "1",
                "observation_count": "1",
                "unavailable_observation_ids": "1",
                "unknown_requirement_observation_ids": "1",
                "definition_mismatch_observation_ids": "1",
                "requirement_coverage": "mixed",
                "insufficient_requirement_ids": "1",
                "caller_requirement_comparisons": "mixed",
                "missing_reviews": "1",
            },
            (
                "Production-weld, procedure, material-lot and consumable-lot identities are caller-reviewed.",
                "Each destructive observation retains a physical specimen and source-group mapping.",
                "Requirements and dispositions are supplied by the caller and are not bundled code rules.",
            ),
            ("reviewed_production_weld_test_evidence",),
            context_validator=same_identity,
        )
    ]
