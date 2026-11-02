"""Temper-bead production records compared with caller-owned qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

ObservationKind = Literal["hardness", "microstructure", "nondestructive_examination"]


class TemperBeadPassRecord(Contract):
    pass_record_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    layer_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    heat_input_value: Nonnegative
    heat_input_unit_token: str = Field(min_length=1)
    interpass_temperature_K: Positive
    temper_bead_descriptor: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration_and_validity(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("temper-bead pass records require positive duration")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid temper-bead pass record requires a basis")
        return self


class TemperBeadObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: ObservationKind
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    reported_value: float | None = None
    result_unit_token: str = Field(min_length=1)
    result_descriptor: str | None = None
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_coverage_factor: Positive | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def value_or_descriptor_and_uncertainty(self):
        if self.reported_value is None and not self.result_descriptor:
            raise ValueError("temper-bead observations require a value or result descriptor")
        if self.reported_value is not None and (
            self.expanded_uncertainty is None or self.uncertainty_coverage_factor is None
        ):
            raise ValueError("numeric temper-bead observations require expanded uncertainty and coverage")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid temper-bead observation requires a basis")
        return self


class TemperBeadObservationRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    observation_kind: ObservationKind
    method_id: str = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    supported_result_descriptors: tuple[str, ...] = ()
    minimum_value: float | None = None
    maximum_value: float | None = None
    requirement_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_support(self):
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("temper-bead observation requirement bounds must be ordered")
        if len(set(self.supported_result_descriptors)) != len(self.supported_result_descriptors):
            raise ValueError("temper-bead result descriptors must be unique")
        if (
            self.minimum_value is None
            and self.maximum_value is None
            and not self.supported_result_descriptors
        ):
            raise ValueError("an observation requirement needs numeric bounds or descriptor support")
        return self


class TemperBeadQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    repair_scope_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    base_material_condition_id: str = Field(min_length=1)
    deposited_material_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    required_layer_sequence: tuple[str, ...] = Field(min_length=1)
    supported_temper_bead_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_heat_input_value: Nonnegative
    maximum_heat_input_value: Nonnegative
    heat_input_unit_token: str = Field(min_length=1)
    minimum_interpass_temperature_K: Positive
    maximum_interpass_temperature_K: Positive
    observation_requirements: tuple[TemperBeadObservationRequirement, ...] = Field(min_length=1)
    minimum_physical_specimen_count: int = Field(ge=1)
    minimum_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_heat_input_value < self.minimum_heat_input_value:
            raise ValueError("temper-bead heat-input support must be ordered")
        if self.maximum_interpass_temperature_K < self.minimum_interpass_temperature_K:
            raise ValueError("temper-bead interpass-temperature support must be ordered")
        for values, name in (
            (self.required_layer_sequence, "layer"),
            (self.supported_temper_bead_descriptors, "temper-bead descriptor"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"temper-bead {name} values must be unique and nonblank")
        requirement_ids = [row.requirement_id for row in self.observation_requirements]
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("temper-bead observation requirement identifiers must be unique")
        return self


class TemperBeadQualificationAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    repair_scope_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    base_material_condition_id: str = Field(min_length=1)
    deposited_material_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    pass_records: tuple[TemperBeadPassRecord, ...] = Field(min_length=1)
    observations: tuple[TemperBeadObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[TemperBeadQualificationEnvelope, ...] = Field(min_length=1)
    repair_joint_and_material_identity_reviewed: bool
    deposition_sequence_and_clock_reviewed: bool
    heat_input_and_interpass_temperature_reviewed: bool
    temper_bead_descriptors_reviewed: bool
    observation_methods_units_and_uncertainty_reviewed: bool
    specimen_and_source_group_partitions_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_ordered_records(self):
        pass_ids = [row.pass_record_id for row in self.pass_records]
        positions = [row.sequence_position for row in self.pass_records]
        observation_ids = [row.observation_id for row in self.observations]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(pass_ids)) != len(pass_ids) or positions != list(range(1, len(positions) + 1)):
            raise ValueError("temper-bead pass records require unique IDs and consecutive positions")
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("temper-bead observation identifiers must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("temper-bead envelope identifiers must be unique")
        for first, second in zip(self.pass_records, self.pass_records[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("temper-bead pass records must be ordered and cannot overlap")
        return self


def _identity(value) -> tuple[str, ...]:
    return (
        value.repair_scope_id,
        value.joint_configuration_id,
        value.base_material_condition_id,
        value.deposited_material_condition_id,
        value.welding_process_id,
    )


def temper_bead_qualification(x: TemperBeadQualificationAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "repair_joint_and_material_identity_reviewed",
            "deposition_sequence_and_clock_reviewed",
            "heat_input_and_interpass_temperature_reviewed",
            "temper_bead_descriptors_reviewed",
            "observation_methods_units_and_uncertainty_reviewed",
            "specimen_and_source_group_partitions_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    invalid_pass_ids = [row.pass_record_id for row in x.pass_records if not row.record_valid]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    if missing_reviews or invalid_pass_ids or invalid_observation_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "missing_reviews": missing_reviews,
                "invalid_pass_record_ids": invalid_pass_ids,
                "invalid_observation_ids": invalid_observation_ids,
            },
            notes=("Unreviewed or invalid production and examination records are not treated as qualified.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller-owned qualification envelope has the exact repair and material identity.",),
        )

    envelope = matches[0]
    unit_mismatch_pass_ids = [
        row.pass_record_id
        for row in x.pass_records
        if row.heat_input_unit_token != envelope.heat_input_unit_token
    ]
    specimen_ids = sorted({row.physical_specimen_id for row in x.observations})
    source_group_ids = sorted({row.source_group_id for row in x.observations})
    partition_counts_sufficient = (
        len(specimen_ids) >= envelope.minimum_physical_specimen_count
        and len(source_group_ids) >= envelope.minimum_source_group_count
    )
    requirement_rows = []
    missing_requirement_ids = []
    observation_unit_mismatch_ids = []
    outside_observation_ids = []
    for requirement in envelope.observation_requirements:
        candidates = [
            row
            for row in x.observations
            if row.observation_kind == requirement.observation_kind
            and row.method_id == requirement.method_id
            and row.result_definition == requirement.result_definition
        ]
        if not candidates:
            missing_requirement_ids.append(requirement.requirement_id)
        candidate_rows = []
        for row in candidates:
            unit_matches = row.result_unit_token == requirement.result_unit_token
            if not unit_matches:
                observation_unit_mismatch_ids.append(row.observation_id)
                within = None
            elif row.reported_value is not None:
                within = not (
                    requirement.minimum_value is not None
                    and row.reported_value < requirement.minimum_value
                    or requirement.maximum_value is not None
                    and row.reported_value > requirement.maximum_value
                )
            else:
                within = row.result_descriptor in requirement.supported_result_descriptors
            if within is False:
                outside_observation_ids.append(row.observation_id)
            candidate_rows.append(
                {"observation_id": row.observation_id, "unit_matches": unit_matches, "within_support": within}
            )
        requirement_rows.append(
            {"requirement_id": requirement.requirement_id, "candidate_observations": candidate_rows}
        )
    if (
        unit_mismatch_pass_ids
        or observation_unit_mismatch_ids
        or missing_requirement_ids
        or not partition_counts_sufficient
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "heat_input_unit_mismatch_pass_ids": unit_mismatch_pass_ids,
                "observation_unit_mismatch_ids": observation_unit_mismatch_ids,
                "missing_observation_requirement_ids": missing_requirement_ids,
                "evidence_partition_counts_sufficient": partition_counts_sufficient,
                "observation_requirement_comparisons": requirement_rows,
            },
            notes=("Exact units, required examinations and evidence partitions must be complete.",),
        )

    observed_layer_sequence = []
    for row in x.pass_records:
        if not observed_layer_sequence or observed_layer_sequence[-1] != row.layer_id:
            observed_layer_sequence.append(row.layer_id)
    outside_pass_ids = []
    for row in x.pass_records:
        if (
            row.heat_input_value < envelope.minimum_heat_input_value
            or row.heat_input_value > envelope.maximum_heat_input_value
            or row.interpass_temperature_K < envelope.minimum_interpass_temperature_K
            or row.interpass_temperature_K > envelope.maximum_interpass_temperature_K
            or row.temper_bead_descriptor not in envelope.supported_temper_bead_descriptors
        ):
            outside_pass_ids.append(row.pass_record_id)
    sequence_matches = observed_layer_sequence == list(envelope.required_layer_sequence)
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "repair_scope_id": x.repair_scope_id,
        "qualification_envelope_id": envelope.envelope_id,
        "observed_layer_sequence": observed_layer_sequence,
        "required_layer_sequence": list(envelope.required_layer_sequence),
        "layer_sequence_matches": sequence_matches,
        "outside_support_pass_record_ids": outside_pass_ids,
        "outside_support_observation_ids": outside_observation_ids,
        "physical_specimen_ids": specimen_ids,
        "source_group_ids": source_group_ids,
        "observation_requirement_comparisons": requirement_rows,
    }
    notes = (
        "The result compares production records only with a caller-owned qualification envelope.",
        "Hardness, microstructure and NDE evidence are preserved without inferring unmeasured metallurgy.",
        "No code acceptance, crack probability, remaining life or repair disposition is produced.",
    )
    if not sequence_matches or outside_pass_ids or outside_observation_ids:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_qualification_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("temper-bead assessment asset and location must match run context")

    return [
        ModelSpec(
            "welding.temper_bead_qualification",
            TemperBeadQualificationAssessment,
            temper_bead_qualification,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "repair_scope_id": "1",
                "qualification_envelope_id": "1",
                "observed_layer_sequence": "1",
                "required_layer_sequence": "1",
                "layer_sequence_matches": "1",
                "outside_support_pass_record_ids": "1",
                "outside_support_observation_ids": "1",
                "physical_specimen_ids": "1",
                "source_group_ids": "1",
                "observation_requirement_comparisons": "mixed",
                "declared_qualification_outcome": "1",
            },
            (
                "Repair scope, joint, base/deposited material conditions and process match exactly.",
                "Pass order, heat input, interpass temperature and descriptor support are caller declarations.",
                "Observation support does not establish code acceptance, metallurgy or crack probability.",
            ),
            ("reviewed_temper_bead_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
