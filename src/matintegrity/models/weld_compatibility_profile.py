"""Caller-owned compatibility profiles for weld, overlay and consumable selections."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest

AssessmentKind = Literal["dissimilar_weld", "overlay_cladding", "consumable_selection"]
MaterialRole = Literal["base_a", "base_b", "filler", "buttering", "overlay", "dilution_layer"]
LayerRole = Literal["buttering", "filler", "overlay", "dilution_layer"]
Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "welding.caller_owned_compatibility_profile_assessment"


class CompatibilityFact(Contract):
    fact_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    fact_kind: Literal["chemistry", "property", "dilution", "service_environment"]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    missing_or_invalid_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_payload(self):
        if self.status == "available":
            if self.value is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("available compatibility facts require value, uncertainty and digest")
            if self.missing_or_invalid_basis is not None:
                raise ValueError("available compatibility facts cannot carry a missing basis")
        else:
            if self.value is not None or self.standard_uncertainty is not None:
                raise ValueError("missing or invalid compatibility facts cannot carry values")
            if not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid compatibility facts require a basis")
        return self


class CompatibilityMaterial(Contract):
    material_subject_id: str = Field(min_length=1)
    material_role: MaterialRole
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    material_lot_id: str = Field(min_length=1)
    consumable_id: str | None = None
    facts: tuple[CompatibilityFact, ...] = Field(min_length=1)
    identity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_facts(self):
        keys = [(row.fact_kind, row.metric_id, row.unit_token) for row in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("material compatibility facts require unique kind, metric and unit keys")
        if any(row.subject_id != self.material_subject_id for row in self.facts):
            raise ValueError("material compatibility facts must reference their material subject")
        if self.material_role == "filler" and self.consumable_id is None:
            raise ValueError("filler material subjects require a consumable ID")
        return self


class CompatibilityLayer(Contract):
    layer_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    layer_role: LayerRole
    material_subject_id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    dilution_parent_subject_ids: tuple[str, ...] = ()
    facts: tuple[CompatibilityFact, ...] = ()
    sequence_and_parentage_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_facts(self):
        keys = [(row.fact_kind, row.metric_id, row.unit_token) for row in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("layer compatibility facts require unique kind, metric and unit keys")
        if any(row.subject_id != self.layer_id for row in self.facts):
            raise ValueError("layer compatibility facts must reference their layer")
        if len(self.dilution_parent_subject_ids) != len(set(self.dilution_parent_subject_ids)):
            raise ValueError("layer dilution-parent subject IDs must be unique")
        return self


class CompatibilityServiceEnvironment(Contract):
    service_environment_id: str = Field(min_length=1)
    environment_definition: str = Field(min_length=1)
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    temperature_unit_token: Literal["K"] = "K"
    maximum_absolute_pressure_pa: Nonnegative
    pressure_unit_token: Literal["Pa_abs"] = "Pa_abs"
    medium_component_ids: tuple[str, ...] = Field(min_length=1)
    facts: tuple[CompatibilityFact, ...] = ()
    environment_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_linked_environment(self):
        if self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("service temperature range must be ordered")
        if len(self.medium_component_ids) != len(set(self.medium_component_ids)):
            raise ValueError("service medium component IDs must be unique")
        if any(row.subject_id != self.service_environment_id for row in self.facts):
            raise ValueError("service compatibility facts must reference the environment")
        return self


class NumericEnvelopeRule(Contract):
    rule_kind: Literal["numeric_envelope"] = "numeric_envelope"
    rule_id: str = Field(min_length=1)
    target_kind: Literal["material_role", "layer_role", "layer_position", "service_environment"]
    target_value: str = Field(min_length=1)
    fact_kind: Literal["chemistry", "property", "dilution", "service_environment"]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    missing_fact_disposition: Literal["review", "insufficient_evidence"]
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def nonempty_ordered_envelope(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("numeric compatibility envelopes require at least one bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("numeric compatibility envelope bounds must be ordered")
        return self


class IdentityEnvelopeRule(Contract):
    rule_kind: Literal["identity_envelope"] = "identity_envelope"
    rule_id: str = Field(min_length=1)
    target_kind: Literal["material_role", "layer_role", "layer_position", "service_environment"]
    target_value: str = Field(min_length=1)
    identity_field: Literal[
        "material_id",
        "material_condition_id",
        "material_lot_id",
        "consumable_id",
        "process_id",
        "procedure_id",
        "service_environment_id",
    ]
    allowed_values: tuple[str, ...] = Field(min_length=1)
    mismatch_disposition: Literal["reject", "review"]
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_allowed_values(self):
        if any(not row for row in self.allowed_values) or len(self.allowed_values) != len(
            set(self.allowed_values)
        ):
            raise ValueError("identity-envelope allowed values must be nonempty and unique")
        return self


CompatibilityRule = NumericEnvelopeRule | IdentityEnvelopeRule


class CallerWeldCompatibilityProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_kind: Literal["tabulated_envelope", "plugin_style_rules"]
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    applicable_assessment_kinds: tuple[AssessmentKind, ...] = Field(min_length=1)
    permitted_layer_role_sequences: tuple[tuple[LayerRole, ...], ...] = Field(min_length=1)
    sequence_mismatch_disposition: Literal["reject", "review"]
    rules: tuple[CompatibilityRule, ...] = Field(min_length=1)
    plugin_adapter_id: str | None = None
    plugin_adapter_revision: str | None = None
    plugin_configuration_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_unique_profile(self):
        plugin = (
            self.plugin_adapter_id,
            self.plugin_adapter_revision,
            self.plugin_configuration_digest,
        )
        if self.profile_kind == "plugin_style_rules" and not all(plugin):
            raise ValueError("plugin-style profiles require adapter identity, revision and digest")
        if self.profile_kind == "tabulated_envelope" and any(plugin):
            raise ValueError("tabulated profiles cannot carry plugin adapter fields")
        if len(self.applicable_assessment_kinds) != len(set(self.applicable_assessment_kinds)):
            raise ValueError("profile assessment kinds must be unique")
        if len(self.permitted_layer_role_sequences) != len(set(self.permitted_layer_role_sequences)):
            raise ValueError("permitted layer-role sequences must be unique")
        rule_ids = [row.rule_id for row in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("compatibility-profile rule IDs must be unique")
        return self


class WeldCompatibilityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    assessment_kind: AssessmentKind
    materials: tuple[CompatibilityMaterial, ...] = Field(min_length=1)
    layers: tuple[CompatibilityLayer, ...] = Field(min_length=1)
    service_environment: CompatibilityServiceEnvironment
    profile: CallerWeldCompatibilityProfile
    material_fact_units_uncertainty_and_lineage_reviewed: bool
    layer_sequence_parentage_and_dilution_facts_reviewed: bool
    service_environment_and_fact_support_reviewed: bool
    profile_authority_applicability_and_plugin_identity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_assessment(self):
        subject_ids = [row.material_subject_id for row in self.materials]
        layer_ids = [row.layer_id for row in self.layers]
        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError("compatibility material-subject IDs must be unique")
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("compatibility layer IDs must be unique")
        positions = [row.sequence_position for row in self.layers]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("compatibility layers require ordered consecutive positions")
        known = set(subject_ids)
        if any(row.material_subject_id not in known for row in self.layers):
            raise ValueError("every compatibility layer must reference a material subject")
        if any(set(row.dilution_parent_subject_ids) - known for row in self.layers):
            raise ValueError("every dilution parent must reference a declared material subject")
        roles = {row.material_role for row in self.materials}
        if self.assessment_kind == "dissimilar_weld" and not {"base_a", "base_b", "filler"}.issubset(roles):
            raise ValueError("dissimilar-weld assessments require base A, base B and filler subjects")
        if self.assessment_kind == "overlay_cladding" and "overlay" not in roles:
            raise ValueError("overlay-cladding assessments require an overlay material subject")
        if self.assessment_kind == "consumable_selection" and "filler" not in roles:
            raise ValueError("consumable-selection assessments require a filler material subject")
        return self


class CompatibilityRuleFinding(Contract):
    rule_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str = Field(min_length=1)


class WeldCompatibilityAssessmentResult(Contract):
    schema_version: Literal["matintegrity.weld_compatibility_profile.v1"] = (
        "matintegrity.weld_compatibility_profile.v1"
    )
    model_id: Literal["welding.caller_owned_compatibility_profile_assessment"] = MODEL_ID
    assessment_id: str
    assessment_kind: AssessmentKind
    profile_id: str
    profile_revision: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[CompatibilityRuleFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_standard_or_diagram_qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def bound_digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("weld compatibility result digest does not match its content")
        return self


def _targets(x: WeldCompatibilityAssessment, kind: str, value: str):
    if kind == "material_role":
        return [
            (row.material_subject_id, row, row.facts) for row in x.materials if row.material_role == value
        ]
    if kind == "layer_role":
        return [(row.layer_id, row, row.facts) for row in x.layers if row.layer_role == value]
    if kind == "layer_position":
        return [(row.layer_id, row, row.facts) for row in x.layers if str(row.sequence_position) == value]
    if x.service_environment.service_environment_id == value:
        row = x.service_environment
        return [(row.service_environment_id, row, row.facts)]
    return []


def assess_weld_compatibility(x: WeldCompatibilityAssessment) -> WeldCompatibilityAssessmentResult:
    """Evaluate caller rules without embedded alloy diagrams or acceptance criteria."""

    profile = x.profile
    reviews = []
    insufficient = []
    for reviewed, statement in (
        (profile.profile_reviewed, "caller compatibility profile was not reviewed"),
        (
            x.material_fact_units_uncertainty_and_lineage_reviewed,
            "material facts, units, uncertainty and lineage were not reviewed",
        ),
        (
            x.layer_sequence_parentage_and_dilution_facts_reviewed,
            "layer sequence, parentage and dilution facts were not reviewed",
        ),
        (
            x.service_environment_and_fact_support_reviewed,
            "service environment and fact support were not reviewed",
        ),
        (
            x.profile_authority_applicability_and_plugin_identity_reviewed,
            "profile authority, applicability or plugin identity was not reviewed",
        ),
        (
            all(row.identity_reviewed for row in x.materials),
            "one or more material identities were not reviewed",
        ),
        (
            all(row.sequence_and_parentage_reviewed for row in x.layers),
            "one or more layer sequence or parentage records were not reviewed",
        ),
        (x.service_environment.environment_reviewed, "service environment was not reviewed"),
    ):
        if not reviewed:
            insufficient.append(statement)
    if x.assessment_kind not in profile.applicable_assessment_kinds:
        reviews.append("assessment kind is outside the caller profile applicability")
    sequence = tuple(row.layer_role for row in x.layers)
    sequence_outcome = None
    if sequence not in profile.permitted_layer_role_sequences:
        sequence_outcome = profile.sequence_mismatch_disposition
        if sequence_outcome == "review":
            reviews.append("layer-role sequence is outside the caller profile")

    findings = []
    for rule in profile.rules:
        targets = _targets(x, rule.target_kind, rule.target_value)
        if not targets:
            insufficient.append(f"{rule.rule_id}: no exact target matched the caller rule")
            continue
        for target_id, target, facts in targets:
            if isinstance(rule, NumericEnvelopeRule):
                matches = [
                    row
                    for row in facts
                    if row.fact_kind == rule.fact_kind
                    and row.metric_id == rule.metric_id
                    and row.unit_token == rule.unit_token
                ]
                if not matches or matches[0].status != "available":
                    outcome = rule.missing_fact_disposition
                    if outcome == "review":
                        reviews.append(f"{rule.rule_id}:{target_id} fact unavailable")
                    else:
                        insufficient.append(f"{rule.rule_id}:{target_id} fact unavailable")
                    findings.append(
                        CompatibilityRuleFinding(
                            rule_id=rule.rule_id,
                            target_id=target_id,
                            outcome=outcome,
                            observed_value=None,
                            unit_token=rule.unit_token,
                            basis="exact metric/unit fact is unavailable",
                        )
                    )
                    continue
                fact = matches[0]
                lower = fact.value
                upper = fact.value
                if rule.uncertainty_policy == "interval_must_fit":
                    span = rule.uncertainty_coverage_factor * fact.standard_uncertainty
                    lower -= span
                    upper += span
                within = (rule.minimum_inclusive is None or lower >= rule.minimum_inclusive) and (
                    rule.maximum_inclusive is None or upper <= rule.maximum_inclusive
                )
                findings.append(
                    CompatibilityRuleFinding(
                        rule_id=rule.rule_id,
                        target_id=target_id,
                        outcome="pass" if within else "fail",
                        observed_value=fact.value,
                        unit_token=rule.unit_token,
                        evaluated_lower=lower,
                        evaluated_upper=upper,
                        basis=f"caller numeric envelope with {rule.uncertainty_policy}",
                    )
                )
            else:
                observed = getattr(target, rule.identity_field, None)
                if observed is None:
                    insufficient.append(f"{rule.rule_id}:{target_id} identity field unavailable")
                    outcome = "insufficient_evidence"
                elif observed in rule.allowed_values:
                    outcome = "pass"
                else:
                    outcome = rule.mismatch_disposition
                    if outcome == "review":
                        reviews.append(f"{rule.rule_id}:{target_id} identity outside envelope")
                findings.append(
                    CompatibilityRuleFinding(
                        rule_id=rule.rule_id,
                        target_id=target_id,
                        outcome=outcome,
                        observed_value=observed,
                        unit_token="identity",
                        basis="caller identity-envelope membership",
                    )
                )

    if insufficient:
        disposition: Disposition = "insufficient_evidence"
    elif sequence_outcome == "reject" or any(row.outcome == "fail" for row in findings):
        disposition = "reject"
    elif reviews:
        disposition = "review"
    else:
        disposition = "accept"
    values = {
        "assessment_id": x.assessment_id,
        "assessment_kind": x.assessment_kind,
        "profile_id": profile.profile_id,
        "profile_revision": profile.profile_revision,
        "disposition": disposition,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "findings": tuple(findings),
        "review_reasons": tuple(dict.fromkeys(reviews)),
        "insufficient_evidence_reasons": tuple(dict.fromkeys(insufficient)),
        "notes": (
            "Only caller-owned tabulated or plugin-style rules are evaluated; no alloy diagram or standard acceptance criterion is embedded.",
            "Composition, property, dilution and service facts retain exact caller metric definitions, units, uncertainty and provider lineage.",
            "The result is not code qualification, physical validation, remaining-life prediction or failure probability.",
        ),
    }
    unsigned = WeldCompatibilityAssessmentResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return WeldCompatibilityAssessmentResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )
