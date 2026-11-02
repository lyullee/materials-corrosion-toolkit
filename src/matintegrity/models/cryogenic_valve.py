"""Cryogenic-valve cycle and observation evidence against caller-owned support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class CryogenicValveCycle(Contract):
    cycle_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_value: Nonnegative
    maximum_pressure_value: Nonnegative
    pressure_unit_token: str = Field(min_length=1)
    actuation_count: int = Field(ge=0)
    actuation_mode_descriptor: str = Field(min_length=1)
    thermal_stabilization_basis: str = Field(min_length=1)
    acquisition_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_cycle(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("cryogenic-valve cycles must have positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("cryogenic-valve temperature ranges must be ordered")
        if self.maximum_pressure_value < self.minimum_pressure_value:
            raise ValueError("cryogenic-valve pressure ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid cryogenic-valve cycles require a basis")
        return self


class CryogenicValveObservation(Contract):
    observation_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    physical_component_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    observation_role: Literal["background", "control", "test"]
    observation_kind: Literal["leakage", "torque", "function"]
    method_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    reporting_status: Literal["quantified", "below_detection", "missing"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    coverage_factor: Positive | None = None
    detection_limit: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_contract(self):
        if self.reporting_status == "quantified":
            if self.value is None or self.expanded_uncertainty is None or self.result_digest is None:
                raise ValueError("quantified valve observations require value, uncertainty and digest")
            if self.coverage_factor is None:
                raise ValueError("quantified valve observations require an uncertainty coverage factor")
        elif self.reporting_status == "below_detection":
            if self.value is not None or self.detection_limit is None or self.result_digest is None:
                raise ValueError("below-detection valve observations require only a limit and digest")
            if self.expanded_uncertainty is not None or self.coverage_factor is not None:
                raise ValueError("below-detection valve observations do not carry quantified uncertainty")
        elif (
            any(
                value is not None
                for value in (
                    self.value,
                    self.expanded_uncertainty,
                    self.coverage_factor,
                    self.detection_limit,
                    self.result_digest,
                )
            )
            or not self.missing_basis
        ):
            raise ValueError("missing valve observations require a basis and no result fields")
        return self


class CryogenicValveObservationRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    observation_kind: Literal["leakage", "torque", "function"]
    observation_role: Literal["background", "control", "test"]
    method_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_record_count: int = Field(ge=1)
    requirement_basis: str = Field(min_length=1)


class CryogenicValveQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    valve_type_id: str = Field(min_length=1)
    body_material_id: str = Field(min_length=1)
    seat_component_id: str = Field(min_length=1)
    seat_material_id: str = Field(min_length=1)
    stem_component_id: str = Field(min_length=1)
    stem_material_id: str = Field(min_length=1)
    seal_system_id: str = Field(min_length=1)
    test_medium_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge", "differential"]
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_value: Nonnegative
    maximum_pressure_value: Nonnegative
    pressure_unit_token: str = Field(min_length=1)
    supported_actuation_mode_descriptors: tuple[str, ...] = Field(min_length=1)
    maximum_single_cycle_duration_s: Positive
    maximum_cumulative_actuation_count: int = Field(ge=0)
    observation_requirements: tuple[CryogenicValveObservationRequirement, ...] = Field(min_length=1)
    physical_specimen_ids: tuple[str, ...] = Field(min_length=1)
    source_group_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("cryogenic-valve temperature support must be ordered")
        if self.maximum_pressure_value < self.minimum_pressure_value:
            raise ValueError("cryogenic-valve pressure support must be ordered")
        for values, name in (
            (self.supported_actuation_mode_descriptors, "actuation mode"),
            (self.physical_specimen_ids, "physical specimen"),
            (self.source_group_ids, "source group"),
        ):
            if len(set(values)) != len(values) or any(not item.strip() for item in values):
                raise ValueError(f"{name} identifiers must be unique and nonblank")
        requirement_ids = [row.requirement_id for row in self.observation_requirements]
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("cryogenic-valve observation requirement IDs must be unique")
        return self


class CryogenicValveEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    valve_id: str = Field(min_length=1)
    valve_type_id: str = Field(min_length=1)
    body_material_id: str = Field(min_length=1)
    seat_component_id: str = Field(min_length=1)
    seat_material_id: str = Field(min_length=1)
    stem_component_id: str = Field(min_length=1)
    stem_material_id: str = Field(min_length=1)
    seal_system_id: str = Field(min_length=1)
    test_medium_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge", "differential"]
    cycles: tuple[CryogenicValveCycle, ...] = Field(min_length=1)
    observations: tuple[CryogenicValveObservation, ...] = Field(min_length=1)
    qualification_envelope: CryogenicValveQualificationEnvelope
    valve_component_material_and_seal_identity_reviewed: bool
    medium_and_pressure_basis_reviewed: bool
    clock_cycle_and_actuation_alignment_reviewed: bool
    thermal_stabilization_reviewed: bool
    observation_roles_metrics_and_units_reviewed: bool
    uncertainty_detection_limits_and_missingness_reviewed: bool
    physical_specimen_and_source_group_partitions_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_linked_ordered_records(self):
        cycle_ids = [row.cycle_id for row in self.cycles]
        observation_ids = [row.observation_id for row in self.observations]
        if len(set(cycle_ids)) != len(cycle_ids):
            raise ValueError("cryogenic-valve cycle IDs must be unique")
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("cryogenic-valve observation IDs must be unique")
        if {row.cycle_id for row in self.observations} - set(cycle_ids):
            raise ValueError("every valve observation must reference a declared cycle")
        for first, second in zip(self.cycles, self.cycles[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("cryogenic-valve cycles must be ordered and cannot overlap")
        return self


def cryogenic_valve_evidence(x: CryogenicValveEvidenceAssessment) -> Calculation:
    envelope = x.qualification_envelope
    review_fields = (
        "valve_component_material_and_seal_identity_reviewed",
        "medium_and_pressure_basis_reviewed",
        "clock_cycle_and_actuation_alignment_reviewed",
        "thermal_stabilization_reviewed",
        "observation_roles_metrics_and_units_reviewed",
        "uncertainty_detection_limits_and_missingness_reviewed",
        "physical_specimen_and_source_group_partitions_reviewed",
        "provider_lineage_and_digests_reviewed",
        "qualification_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    identity_fields = (
        "valve_type_id",
        "body_material_id",
        "seat_component_id",
        "seat_material_id",
        "stem_component_id",
        "stem_material_id",
        "seal_system_id",
        "test_medium_id",
        "pressure_basis",
    )
    identity_mismatches = [name for name in identity_fields if getattr(x, name) != getattr(envelope, name)]
    invalid_cycle_ids = [row.cycle_id for row in x.cycles if not row.record_valid]
    missing_observation_ids = [
        row.observation_id for row in x.observations if row.reporting_status == "missing"
    ]
    pressure_unit_mismatch_cycle_ids = [
        row.cycle_id for row in x.cycles if row.pressure_unit_token != envelope.pressure_unit_token
    ]

    requirement_counts = {}
    definition_mismatch_observation_ids = []
    matched_requirement_by_observation = {}
    for observation in x.observations:
        matches = [
            requirement
            for requirement in envelope.observation_requirements
            if observation.observation_kind == requirement.observation_kind
            and observation.observation_role == requirement.observation_role
            and observation.method_id == requirement.method_id
            and observation.metric_id == requirement.metric_id
            and observation.metric_definition == requirement.metric_definition
            and observation.unit_token == requirement.unit_token
        ]
        if len(matches) != 1:
            definition_mismatch_observation_ids.append(observation.observation_id)
        else:
            matched_requirement_by_observation[observation.observation_id] = matches[0].requirement_id
    for requirement in envelope.observation_requirements:
        count = sum(
            requirement_id == requirement.requirement_id
            for requirement_id in matched_requirement_by_observation.values()
        )
        requirement_counts[requirement.requirement_id] = count
    missing_requirement_ids = [
        requirement.requirement_id
        for requirement in envelope.observation_requirements
        if requirement_counts[requirement.requirement_id] < requirement.minimum_record_count
    ]

    if any(
        (
            missing_reviews,
            identity_mismatches,
            invalid_cycle_ids,
            missing_observation_ids,
            pressure_unit_mismatch_cycle_ids,
            definition_mismatch_observation_ids,
            missing_requirement_ids,
        )
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "invalid_cycle_ids": invalid_cycle_ids,
                "missing_observation_ids": missing_observation_ids,
                "pressure_unit_mismatch_cycle_ids": pressure_unit_mismatch_cycle_ids,
                "definition_mismatch_observation_ids": definition_mismatch_observation_ids,
                "observation_requirement_counts": requirement_counts,
                "missing_observation_requirement_ids": missing_requirement_ids,
            },
            notes=("Valve evidence comparison is withheld until reviews and records are complete.",),
        )

    cycle_comparisons = []
    outside_cycle_ids = []
    cumulative_actuation_count = 0
    for cycle in x.cycles:
        duration = cycle.end_time_s - cycle.start_time_s
        cumulative_actuation_count += cycle.actuation_count
        reasons = []
        if (
            cycle.minimum_temperature_K < envelope.minimum_temperature_K
            or cycle.maximum_temperature_K > envelope.maximum_temperature_K
        ):
            reasons.append("temperature_range")
        if (
            cycle.minimum_pressure_value < envelope.minimum_pressure_value
            or cycle.maximum_pressure_value > envelope.maximum_pressure_value
        ):
            reasons.append("pressure_range")
        if cycle.actuation_mode_descriptor not in envelope.supported_actuation_mode_descriptors:
            reasons.append("actuation_mode_descriptor")
        if duration > envelope.maximum_single_cycle_duration_s:
            reasons.append("cycle_duration")
        if reasons:
            outside_cycle_ids.append(cycle.cycle_id)
        cycle_comparisons.append(
            {
                "cycle_id": cycle.cycle_id,
                "duration_s": duration,
                "actuation_count": cycle.actuation_count,
                "outside_support_reasons": reasons,
                "within_declared_qualification_support": not reasons,
            }
        )
    cumulative_actuation_within_support = (
        cumulative_actuation_count <= envelope.maximum_cumulative_actuation_count
    )

    observation_summaries = []
    for observation in x.observations:
        conservative_value = (
            observation.value + observation.expanded_uncertainty
            if observation.reporting_status == "quantified"
            else observation.detection_limit
            if observation.reporting_status == "below_detection"
            else None
        )
        observation_summaries.append(
            {
                "observation_id": observation.observation_id,
                "cycle_id": observation.cycle_id,
                "physical_component_id": observation.physical_component_id,
                "observation_role": observation.observation_role,
                "observation_kind": observation.observation_kind,
                "reporting_status": observation.reporting_status,
                "matched_requirement_id": matched_requirement_by_observation.get(observation.observation_id),
                "reported_or_conservative_value": conservative_value,
            }
        )

    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "valve_id": x.valve_id,
        "qualification_envelope_id": envelope.envelope_id,
        "cycle_comparisons": cycle_comparisons,
        "outside_support_cycle_ids": outside_cycle_ids,
        "cumulative_actuation_count": cumulative_actuation_count,
        "cumulative_actuation_within_support": cumulative_actuation_within_support,
        "observation_summaries": observation_summaries,
        "observation_requirement_counts": requirement_counts,
        "qualification_evidence_summary": {
            "physical_specimen_ids": list(envelope.physical_specimen_ids),
            "source_group_ids": list(envelope.source_group_ids),
            "provider_id": envelope.provider_id,
            "provider_revision": envelope.provider_revision,
        },
    }
    notes = (
        "Background, control and test roles and below-detection records are preserved; no missing or censored value is replaced by zero.",
        "The model reports only support and record completeness and does not infer service leakage, torque or function from test evidence.",
        "No thermal stress, code acceptance, reliability, remaining life or failure probability is produced.",
    )
    if outside_cycle_ids or not cumulative_actuation_within_support:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_evidence_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("cryogenic-valve assessment asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.cryogenic_valve_evidence",
            CryogenicValveEvidenceAssessment,
            cryogenic_valve_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "valve_id": "1",
                "qualification_envelope_id": "1",
                "cycle_comparisons": "mixed",
                "outside_support_cycle_ids": "1",
                "cumulative_actuation_count": "count",
                "cumulative_actuation_within_support": "1",
                "observation_summaries": "mixed",
                "observation_requirement_counts": "1",
                "qualification_evidence_summary": "1",
                "declared_evidence_outcome": "1",
            },
            (
                "Valve, body, seat, stem, seal, medium and pressure-basis identities match caller qualification evidence exactly.",
                "Cycle pressure is compared only under an exact caller-declared unit token; no conversion or code threshold is inferred.",
                "Leakage, torque and function observations retain their role, censoring status, uncertainty and provider lineage.",
            ),
            ("reviewed_cryogenic_valve_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
