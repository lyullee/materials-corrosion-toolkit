"""Caller-owned pressure-test method and eligibility evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PressureTestRequirementRecord(Contract):
    requirement_id: str = Field(min_length=1)
    requirement_definition: str = Field(min_length=1)
    disposition: Literal["satisfied", "not_satisfied", "missing"]
    physical_source_group_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    disposition_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_disposition(self):
        if self.disposition == "missing":
            if self.result_digest is not None or not self.disposition_basis:
                raise ValueError("a missing pressure-test requirement needs a basis and no result digest")
        elif self.result_digest is None or not self.disposition_basis:
            raise ValueError("a reviewed pressure-test requirement needs a result digest and basis")
        return self


class DeclaredPressureTestEligibilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    component_type_id: str = Field(min_length=1)
    supported_material_condition_ids: tuple[str, ...] = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    supported_test_medium_ids: tuple[str, ...] = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge", "differential"]
    minimum_test_pressure_Pa: Nonnegative
    maximum_test_pressure_Pa: Positive
    minimum_test_temperature_K: Positive
    maximum_test_temperature_K: Positive
    maximum_stored_energy_value: Nonnegative | None = None
    stored_energy_unit_token: str | None = None
    required_requirement_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    authority_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_test_pressure_Pa < self.minimum_test_pressure_Pa:
            raise ValueError("pressure-test pressure support must be ordered")
        if self.maximum_test_temperature_K < self.minimum_test_temperature_K:
            raise ValueError("pressure-test temperature support must be ordered")
        for values, label in (
            (self.supported_material_condition_ids, "material condition"),
            (self.supported_test_medium_ids, "test medium"),
            (self.required_requirement_ids, "pressure-test requirement"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        if (self.maximum_stored_energy_value is None) != (self.stored_energy_unit_token is None):
            raise ValueError("stored-energy support requires both a value and unit token")
        return self


class PressureTestEligibilityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    component_type_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    test_medium_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge", "differential"]
    proposed_test_pressure_Pa: Nonnegative
    minimum_test_temperature_K: Positive
    maximum_test_temperature_K: Positive
    stored_energy_value: Nonnegative | None = None
    stored_energy_unit_token: str | None = None
    boundary_and_isolation_definition: str = Field(min_length=1)
    requirement_records: tuple[PressureTestRequirementRecord, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredPressureTestEligibilityEnvelope, ...] = Field(min_length=1)
    component_material_and_scope_reviewed: bool
    test_method_medium_and_pressure_basis_reviewed: bool
    pressure_and_temperature_plan_reviewed: bool
    boundary_isolation_and_stored_energy_reviewed: bool
    requirement_records_and_source_groups_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    eligibility_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_complete_records(self):
        if self.maximum_test_temperature_K < self.minimum_test_temperature_K:
            raise ValueError("planned pressure-test temperature range must be ordered")
        if (self.stored_energy_value is None) != (self.stored_energy_unit_token is None):
            raise ValueError("planned stored energy requires both a value and unit token")
        record_ids = [row.requirement_id for row in self.requirement_records]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("pressure-test requirement IDs must be unique")
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("pressure-test envelope IDs must be unique")
        return self


def pressure_test_eligibility(x: PressureTestEligibilityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_material_and_scope_reviewed",
            "test_method_medium_and_pressure_basis_reviewed",
            "pressure_and_temperature_plan_reviewed",
            "boundary_isolation_and_stored_energy_reviewed",
            "requirement_records_and_source_groups_reviewed",
            "provider_lineage_and_digests_reviewed",
            "eligibility_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    matching = [
        envelope
        for envelope in x.candidate_envelopes
        if envelope.component_type_id == x.component_type_id
        and x.material_condition_id in envelope.supported_material_condition_ids
        and envelope.test_method_id == x.test_method_id
        and x.test_medium_id in envelope.supported_test_medium_ids
        and envelope.pressure_basis == x.pressure_basis
    ]
    missing_record_ids = [row.requirement_id for row in x.requirement_records if row.disposition == "missing"]
    if missing_reviews or missing_record_ids or len(matching) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matching],
                "missing_requirement_record_ids": missing_record_ids,
                "missing_reviews": missing_reviews,
            },
            notes=("A unique reviewed envelope and complete requirement records are required.",),
        )

    envelope = matching[0]
    supplied = {row.requirement_id: row for row in x.requirement_records}
    absent_required_ids = [
        requirement_id
        for requirement_id in envelope.required_requirement_ids
        if requirement_id not in supplied
    ]
    extra_requirement_ids = sorted(set(supplied) - set(envelope.required_requirement_ids))
    if absent_required_ids or extra_requirement_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "selected_envelope_id": envelope.envelope_id,
                "absent_required_ids": absent_required_ids,
                "extra_requirement_ids": extra_requirement_ids,
                "missing_reviews": [],
            },
            notes=("Requirement coverage must exactly match the selected caller envelope.",),
        )

    outside_support_reasons = []
    if not (
        envelope.minimum_test_pressure_Pa <= x.proposed_test_pressure_Pa <= envelope.maximum_test_pressure_Pa
    ):
        outside_support_reasons.append("test_pressure")
    if not (
        envelope.minimum_test_temperature_K
        <= x.minimum_test_temperature_K
        <= x.maximum_test_temperature_K
        <= envelope.maximum_test_temperature_K
    ):
        outside_support_reasons.append("test_temperature_range")
    stored_energy_comparison = None
    if envelope.maximum_stored_energy_value is not None:
        if x.stored_energy_value is None or x.stored_energy_unit_token != envelope.stored_energy_unit_token:
            return Calculation(
                status="needs_data",
                values={
                    "assessment_id": x.assessment_id,
                    "selected_envelope_id": envelope.envelope_id,
                    "stored_energy_definition_complete": False,
                    "missing_reviews": [],
                },
                notes=("Stored-energy value and exact unit are required by the selected envelope.",),
            )
        stored_energy_comparison = {
            "reported_value": x.stored_energy_value,
            "unit_token": x.stored_energy_unit_token,
            "caller_maximum": envelope.maximum_stored_energy_value,
            "within_declared_support": x.stored_energy_value <= envelope.maximum_stored_energy_value,
        }
        if not stored_energy_comparison["within_declared_support"]:
            outside_support_reasons.append("stored_energy")
    elif x.stored_energy_value is not None:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "selected_envelope_id": envelope.envelope_id,
                "stored_energy_definition_complete": False,
                "missing_reviews": [],
            },
            notes=("The selected envelope does not define support for the supplied stored-energy metric.",),
        )

    unsatisfied_ids = [
        requirement_id
        for requirement_id in envelope.required_requirement_ids
        if supplied[requirement_id].disposition == "not_satisfied"
    ]
    if outside_support_reasons:
        status = "out_of_scope"
        outcome = "outside_declared_support"
    else:
        status = "computed"
        outcome = "requirements_satisfied" if not unsatisfied_ids else "requirements_not_satisfied"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "selected_envelope_id": envelope.envelope_id,
            "declared_eligibility_outcome": outcome,
            "outside_support_reasons": outside_support_reasons,
            "unsatisfied_requirement_ids": unsatisfied_ids,
            "requirement_comparisons": [
                {
                    "requirement_id": requirement_id,
                    "disposition": supplied[requirement_id].disposition,
                    "physical_source_group_id": supplied[requirement_id].physical_source_group_id,
                }
                for requirement_id in envelope.required_requirement_ids
            ],
            "stored_energy_comparison": stored_energy_comparison,
            "missing_reviews": [],
        },
        notes=(
            "Eligibility requirements and support ranges are caller-owned; no code pressure or temperature is supplied.",
            "A computed requirements-satisfied outcome is not regulatory acceptance, proof-test qualification, structural capacity, or service fitness.",
            "This model does not calculate test pressure, stored energy, fracture risk, leak probability, or remaining life.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("pressure-test assessment asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.pressure_test_eligibility",
            PressureTestEligibilityAssessment,
            pressure_test_eligibility,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "selected_envelope_id": "1",
                "declared_eligibility_outcome": "1",
                "outside_support_reasons": "1",
                "unsatisfied_requirement_ids": "1",
                "requirement_comparisons": "mixed",
                "stored_energy_comparison": "mixed",
                "missing_reviews": "1",
            },
            (
                "Test method, medium, pressure basis and component/material identities are caller-reviewed.",
                "Pressure, temperature, stored-energy and prerequisite limits are caller-owned and not extrapolated.",
                "Requirement dispositions retain physical source-group and provider lineage.",
            ),
            ("reviewed_pressure_test_eligibility_envelope",),
            context_validator=same_identity,
        )
    ]
