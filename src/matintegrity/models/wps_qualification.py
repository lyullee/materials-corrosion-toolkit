"""Production welding variables compared with caller-owned qualification envelopes."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence
from ..registry import ModelSpec

Digest = str


class QualifiedEssentialVariable(Contract):
    variable_id: str = Field(min_length=1)
    qualification_class: Literal["essential", "supplementary_essential", "nonessential"] = "essential"
    variable_kind: Literal["numeric", "categorical"]
    unit_token: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    supported_value_tokens: tuple[str, ...] = ()
    applicability_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def kind_specific_support(self):
        if self.variable_kind == "numeric":
            if self.minimum_value is None or self.maximum_value is None:
                raise ValueError("numeric qualified variables require both range bounds")
            if self.maximum_value < self.minimum_value:
                raise ValueError("numeric qualified-variable bounds must be ordered")
            if self.supported_value_tokens:
                raise ValueError("numeric qualified variables cannot declare categorical tokens")
        else:
            if self.minimum_value is not None or self.maximum_value is not None:
                raise ValueError("categorical qualified variables cannot declare numeric bounds")
            if not self.supported_value_tokens:
                raise ValueError("categorical qualified variables require supported value tokens")
            if any(not token.strip() for token in self.supported_value_tokens):
                raise ValueError("categorical support tokens cannot be blank")
            if len(set(self.supported_value_tokens)) != len(self.supported_value_tokens):
                raise ValueError("categorical support tokens must be unique")
        return self


class ProductionEssentialVariableRecord(Contract):
    record_id: str = Field(min_length=1)
    variable_id: str = Field(min_length=1)
    variable_kind: Literal["numeric", "categorical"]
    unit_token: str = Field(min_length=1)
    numeric_value: float | None = None
    categorical_value_token: str | None = None
    record_valid: bool
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def value_matches_kind(self):
        if self.variable_kind == "numeric":
            if self.numeric_value is None or self.categorical_value_token is not None:
                raise ValueError("numeric production variables require only a numeric value")
        elif self.categorical_value_token is None or self.numeric_value is not None:
            raise ValueError("categorical production variables require only a value token")
        elif not self.categorical_value_token.strip():
            raise ValueError("categorical production-variable tokens cannot be blank")
        if not self.record_valid and not self.missing_or_invalid_basis:
            raise ValueError("an invalid production-variable record requires a basis")
        return self


class WPSQualificationTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    qualification_test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    supported_variable_ids: tuple[str, ...] = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_state(self):
        if any(not identifier.strip() for identifier in self.supported_variable_ids):
            raise ValueError("supported variable identifiers cannot be blank")
        if len(set(self.supported_variable_ids)) != len(self.supported_variable_ids):
            raise ValueError("supported variable identifiers must be unique per evidence record")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting qualification evidence requires a basis")
        return self


class DeclaredWPSQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    qualified_procedure_id: str = Field(min_length=1)
    qualified_procedure_revision: str = Field(min_length=1)
    base_material_side_a_condition_id: str = Field(min_length=1)
    base_material_side_b_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    essential_variables: tuple[QualifiedEssentialVariable, ...] = Field(min_length=1)
    test_evidence: tuple[WPSQualificationTestEvidence, ...] = Field(min_length=1)
    declaration_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_linked_records(self):
        variable_ids = [row.variable_id for row in self.essential_variables]
        evidence_ids = [row.evidence_record_id for row in self.test_evidence]
        if len(set(variable_ids)) != len(variable_ids):
            raise ValueError("qualified essential-variable identifiers must be unique")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("qualification evidence-record identifiers must be unique")
        known_variables = set(variable_ids)
        for record in self.test_evidence:
            if set(record.supported_variable_ids) - known_variables:
                raise ValueError("qualification evidence must reference declared essential variables")
        return self


class WPSQualificationAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    production_weld_id: str = Field(min_length=1)
    production_procedure_id: str = Field(min_length=1)
    production_procedure_revision: str = Field(min_length=1)
    base_material_side_a_condition_id: str = Field(min_length=1)
    base_material_side_b_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    production_variables: tuple[ProductionEssentialVariableRecord, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredWPSQualificationEnvelope, ...] = Field(min_length=1)
    production_procedure_identity_reviewed: bool
    material_and_joint_identity_reviewed: bool
    variable_records_reviewed: bool
    qualification_specimen_identity_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_records_and_envelopes(self):
        record_ids = [row.record_id for row in self.production_variables]
        variable_ids = [row.variable_id for row in self.production_variables]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("production variable record identifiers must be unique")
        if len(set(variable_ids)) != len(variable_ids):
            raise ValueError("production essential-variable identifiers must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("qualification envelope identifiers must be unique")
        identities = [_envelope_identity(row) for row in self.candidate_envelopes]
        if len(set(identities)) != len(identities):
            raise ValueError("qualification envelopes must have unique exact identities")
        return self


def _envelope_identity(envelope: DeclaredWPSQualificationEnvelope) -> tuple[str, ...]:
    return (
        envelope.qualified_procedure_id,
        envelope.qualified_procedure_revision,
        envelope.base_material_side_a_condition_id,
        envelope.base_material_side_b_condition_id,
        envelope.joint_configuration_id,
        envelope.welding_process_id,
    )


def _assessment_identity(x: WPSQualificationAssessment) -> tuple[str, ...]:
    return (
        x.production_procedure_id,
        x.production_procedure_revision,
        x.base_material_side_a_condition_id,
        x.base_material_side_b_condition_id,
        x.joint_configuration_id,
        x.welding_process_id,
    )


def wps_qualification_envelope(x: WPSQualificationAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "production_procedure_identity_reviewed",
            "material_and_joint_identity_reviewed",
            "variable_records_reviewed",
            "qualification_specimen_identity_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_production_ids = [row.record_id for row in x.production_variables if not row.record_valid]
    matches = [row for row in x.candidate_envelopes if _envelope_identity(row) == _assessment_identity(x)]
    if missing_reviews or invalid_production_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "invalid_production_record_ids": invalid_production_ids,
                "missing_reviews": missing_reviews,
            },
            notes=("Reviewed production records and caller-owned qualification evidence are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [],
                "invalid_production_record_ids": [],
                "missing_reviews": [],
            },
            notes=("No declared qualification envelope has the exact production procedure identity.",),
        )

    envelope = matches[0]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.test_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    supported_by_evidence = {
        variable_id
        for row in envelope.test_evidence
        if row.record_valid and row.supports_declared_envelope
        for variable_id in row.supported_variable_ids
    }
    qualified = {row.variable_id: row for row in envelope.essential_variables}
    production = {row.variable_id: row for row in x.production_variables}
    missing_production_ids = sorted(set(qualified) - set(production))
    unmatched_production_ids = sorted(set(production) - set(qualified))
    qualification_required = {
        variable_id
        for variable_id, row in qualified.items()
        if row.qualification_class in {"essential", "supplementary_essential"}
    }
    unsupported_evidence_variable_ids = sorted(qualification_required - supported_by_evidence)

    comparison_rows = []
    unit_mismatch_ids = []
    outside_ids = []
    outside_essential_ids = []
    outside_supplementary_ids = []
    outside_nonessential_ids = []
    for variable_id in sorted(set(production) & set(qualified)):
        record = production[variable_id]
        support = qualified[variable_id]
        kind_matches = record.variable_kind == support.variable_kind
        unit_matches = record.unit_token == support.unit_token
        if not unit_matches:
            unit_mismatch_ids.append(variable_id)
        within = None
        if kind_matches and unit_matches:
            if support.variable_kind == "numeric":
                within = support.minimum_value <= record.numeric_value <= support.maximum_value
            else:
                within = record.categorical_value_token in support.supported_value_tokens
            if not within:
                outside_ids.append(variable_id)
                if support.qualification_class == "essential":
                    outside_essential_ids.append(variable_id)
                elif support.qualification_class == "supplementary_essential":
                    outside_supplementary_ids.append(variable_id)
                else:
                    outside_nonessential_ids.append(variable_id)
        comparison_rows.append(
            {
                "variable_id": variable_id,
                "qualification_class": support.qualification_class,
                "record_id": record.record_id,
                "variable_kind": record.variable_kind,
                "unit_token": record.unit_token,
                "kind_matches": kind_matches,
                "unit_matches_exactly": unit_matches,
                "within_declared_envelope": within,
            }
        )

    needs_data = bool(
        invalid_evidence_ids
        or missing_production_ids
        or unsupported_evidence_variable_ids
        or unit_mismatch_ids
        or any(not row["kind_matches"] for row in comparison_rows)
    )
    status = "needs_data" if needs_data else "out_of_scope" if unmatched_production_ids else "computed"
    all_within = None
    if status == "computed":
        all_within = not outside_ids
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "selected_envelope_id": envelope.envelope_id,
            "comparison_rows": comparison_rows,
            "qualification_test_ids": sorted({row.qualification_test_id for row in envelope.test_evidence}),
            "physical_specimen_ids": sorted({row.physical_specimen_id for row in envelope.test_evidence}),
            "source_group_ids": sorted({row.source_group_id for row in envelope.test_evidence}),
            "invalid_qualification_evidence_ids": invalid_evidence_ids,
            "missing_production_variable_ids": missing_production_ids,
            "unmatched_production_variable_ids": unmatched_production_ids,
            "variables_without_supporting_evidence_ids": unsupported_evidence_variable_ids,
            "unit_mismatch_variable_ids": unit_mismatch_ids,
            "outside_declared_envelope_variable_ids": outside_ids,
            "outside_essential_variable_ids": outside_essential_ids,
            "outside_supplementary_essential_variable_ids": outside_supplementary_ids,
            "outside_nonessential_variable_ids": outside_nonessential_ids,
            "requalification_required_variable_ids": sorted(outside_essential_ids + outside_supplementary_ids),
            "all_variables_within_declared_envelope": all_within,
            "missing_reviews": [],
        },
        notes=(
            "Qualification ranges, category tokens, evidence scope and authority are caller-owned; no welding-code table or acceptance rule is bundled.",
            "Exact identity and unit-token comparison does not establish weld quality, structural integrity, corrosion resistance or production acceptance.",
            "Qualification specimen and source-group identifiers are retained and are not interpreted as statistically independent observations.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("WPS-qualification asset and location must match the run context")

    return [
        ModelSpec(
            "welding.wps_qualification_envelope",
            WPSQualificationAssessment,
            wps_qualification_envelope,
            {
                "assessment_id": "1",
                "selected_envelope_id": "1",
                "comparison_rows": "mixed",
                "qualification_test_ids": "1",
                "physical_specimen_ids": "1",
                "source_group_ids": "1",
                "invalid_qualification_evidence_ids": "1",
                "missing_production_variable_ids": "1",
                "unmatched_production_variable_ids": "1",
                "variables_without_supporting_evidence_ids": "1",
                "unit_mismatch_variable_ids": "1",
                "outside_declared_envelope_variable_ids": "1",
                "outside_essential_variable_ids": "1",
                "outside_supplementary_essential_variable_ids": "1",
                "outside_nonessential_variable_ids": "1",
                "requalification_required_variable_ids": "1",
                "all_variables_within_declared_envelope": "1",
                "missing_reviews": "1",
            },
            (
                "Qualified-procedure, revision, material-side, joint and welding-process identities match exactly.",
                "Variable kinds and unit tokens are never converted or inferred.",
            "Essential and supplementary-essential variables require valid caller-supplied test-evidence links with pinned provider state; nonessential variables are checked against their declared envelope without implying qualification-test support.",
            ),
            ("declared_wps_qualification_envelope_accounting",),
            version="1.1.0",
            context_validator=same_identity,
        )
    ]
