"""Caller-defined, evidence-linked screening rules for three SCC mechanisms."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec

SCCMechanism = Literal["chloride_scc", "ammonia_scc", "alkaline_scc"]
FactDomain = Literal["environment", "material", "stress"]
FactKind = Literal["number", "descriptor", "boolean"]
FactStatus = Literal["known", "unknown", "invalid"]
ConditionOperator = Literal[
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "between_inclusive",
    "equals",
    "in_set",
    "is_true",
    "is_false",
]


class SCCScreeningFact(Contract):
    fact_id: str = Field(min_length=1)
    domain: FactDomain
    definition: str = Field(min_length=1)
    value_kind: FactKind
    status: FactStatus
    numeric_value: float | None = None
    unit_token: str | None = None
    descriptor_value: str | None = None
    boolean_value: bool | None = None
    unknown_or_invalid_basis: str | None = None
    evidence_record_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_value(self):
        values = (self.numeric_value, self.descriptor_value, self.boolean_value)
        if self.status == "known":
            expected_index = {"number": 0, "descriptor": 1, "boolean": 2}[self.value_kind]
            if values[expected_index] is None or any(
                value is not None for index, value in enumerate(values) if index != expected_index
            ):
                raise ValueError("known SCC facts require exactly the value matching their kind")
            if self.value_kind == "number" and not self.unit_token:
                raise ValueError("known numeric SCC facts require an exact unit token")
            if self.value_kind != "number" and self.unit_token is not None:
                raise ValueError("nonnumeric SCC facts cannot declare a unit token")
            if self.unknown_or_invalid_basis is not None:
                raise ValueError("known SCC facts cannot declare an unknown or invalid basis")
        else:
            if any(value is not None for value in values) or self.unit_token is not None:
                raise ValueError("unknown or invalid SCC facts cannot carry a value or unit")
            if not self.unknown_or_invalid_basis:
                raise ValueError("unknown or invalid SCC facts require an explicit basis")
        return self


class SCCRuleCondition(Contract):
    condition_id: str = Field(min_length=1)
    fact_id: str = Field(min_length=1)
    expected_fact_kind: FactKind
    operator: ConditionOperator
    unit_token: str | None = None
    threshold: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    expected_descriptors: tuple[str, ...] = ()
    condition_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def fields_match_operator(self):
        numeric_operators = {
            "greater_than",
            "greater_than_or_equal",
            "less_than",
            "less_than_or_equal",
            "between_inclusive",
        }
        descriptor_operators = {"equals", "in_set"}
        boolean_operators = {"is_true", "is_false"}
        if self.operator in numeric_operators:
            if self.expected_fact_kind != "number" or not self.unit_token:
                raise ValueError("numeric SCC rule conditions require number kind and exact unit")
            if self.operator == "between_inclusive":
                if (
                    self.lower_bound is None
                    or self.upper_bound is None
                    or self.upper_bound < self.lower_bound
                ):
                    raise ValueError("between conditions require ordered lower and upper bounds")
                if self.threshold is not None:
                    raise ValueError("between conditions cannot also declare a threshold")
            elif self.threshold is None or self.lower_bound is not None or self.upper_bound is not None:
                raise ValueError("one-sided numeric conditions require exactly one threshold")
            if self.expected_descriptors:
                raise ValueError("numeric conditions cannot contain descriptor values")
        elif self.operator in descriptor_operators:
            if self.expected_fact_kind != "descriptor" or not self.expected_descriptors:
                raise ValueError("descriptor SCC conditions require at least one expected descriptor")
            if self.operator == "equals" and len(self.expected_descriptors) != 1:
                raise ValueError("equals conditions require exactly one descriptor")
            if len(set(self.expected_descriptors)) != len(self.expected_descriptors):
                raise ValueError("expected SCC descriptors must be unique")
            if any(
                value is not None
                for value in (self.unit_token, self.threshold, self.lower_bound, self.upper_bound)
            ):
                raise ValueError("descriptor conditions cannot contain numeric fields")
        else:
            if self.operator not in boolean_operators or self.expected_fact_kind != "boolean":
                raise ValueError("boolean SCC conditions require boolean kind and operator")
            if self.expected_descriptors or any(
                value is not None
                for value in (self.unit_token, self.threshold, self.lower_bound, self.upper_bound)
            ):
                raise ValueError("boolean conditions cannot contain numeric or descriptor fields")
        return self


class SCCScreeningRule(Contract):
    rule_id: str = Field(min_length=1)
    rule_definition: str = Field(min_length=1)
    conditions: tuple[SCCRuleCondition, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_conditions(self):
        identifiers = [row.condition_id for row in self.conditions]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("SCC rule condition identifiers must be unique within a rule")
        return self


class SCCMechanismProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    mechanism: SCCMechanism
    mechanism_definition: str = Field(min_length=1)
    unknown_policy: Literal["indeterminate", "screen_in"]
    rules: tuple[SCCScreeningRule, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    screening_only: Literal[True] = True
    qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_rules(self):
        identifiers = [row.rule_id for row in self.rules]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("SCC screening rule identifiers must be unique")
        return self


class UserDefinedSCCScreening(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    mechanism: SCCMechanism
    facts: tuple[SCCScreeningFact, ...] = Field(min_length=3)
    mechanism_profile: SCCMechanismProfile
    environment_evidence_reviewed: bool
    material_evidence_reviewed: bool
    stress_evidence_reviewed: bool
    fact_definitions_units_and_digests_reviewed: bool
    mechanism_profile_rules_and_unknown_policy_reviewed: bool
    screening_and_qualification_boundary_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_profile_and_facts(self):
        if self.mechanism != self.mechanism_profile.mechanism:
            raise ValueError("SCC assessment and mechanism profile must name the same mechanism")
        identifiers = [row.fact_id for row in self.facts]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("SCC screening fact identifiers must be unique")
        domains = {row.domain for row in self.facts}
        if domains != {"environment", "material", "stress"}:
            raise ValueError("SCC screening requires environment, material and stress evidence facts")
        return self


def _condition_finding(condition: SCCRuleCondition, facts: dict[str, SCCScreeningFact]) -> dict[str, Any]:
    fact = facts.get(condition.fact_id)
    common = {
        "condition_id": condition.condition_id,
        "fact_id": condition.fact_id,
        "operator": condition.operator,
        "condition_basis": condition.condition_basis,
    }
    if fact is None:
        return {**common, "outcome": "unknown", "basis": "referenced fact was not supplied"}
    if fact.status != "known":
        return {
            **common,
            "outcome": "unknown",
            "basis": fact.unknown_or_invalid_basis,
            "fact_status": fact.status,
        }
    if fact.value_kind != condition.expected_fact_kind:
        return {
            **common,
            "outcome": "unknown",
            "basis": "fact kind does not match the caller-defined condition",
            "fact_kind": fact.value_kind,
        }
    result = False
    observed: Any
    expected: Any
    if condition.expected_fact_kind == "number":
        observed = {"value": fact.numeric_value, "unit": fact.unit_token}
        expected = {
            "threshold": condition.threshold,
            "lower_bound": condition.lower_bound,
            "upper_bound": condition.upper_bound,
            "unit": condition.unit_token,
        }
        if fact.unit_token != condition.unit_token:
            return {
                **common,
                "outcome": "unknown",
                "basis": "numeric fact and condition unit tokens differ; no conversion was performed",
                "observed": observed,
                "expected": expected,
            }
        value = fact.numeric_value
        if condition.operator == "greater_than":
            result = value > condition.threshold
        elif condition.operator == "greater_than_or_equal":
            result = value >= condition.threshold
        elif condition.operator == "less_than":
            result = value < condition.threshold
        elif condition.operator == "less_than_or_equal":
            result = value <= condition.threshold
        else:
            result = condition.lower_bound <= value <= condition.upper_bound
    elif condition.expected_fact_kind == "descriptor":
        observed = fact.descriptor_value
        expected = list(condition.expected_descriptors)
        result = (
            observed == condition.expected_descriptors[0]
            if condition.operator == "equals"
            else observed in condition.expected_descriptors
        )
    else:
        observed = fact.boolean_value
        expected = condition.operator == "is_true"
        result = observed is expected
    return {
        **common,
        "outcome": "true" if result else "false",
        "basis": "caller-defined condition evaluated against the reviewed fact",
        "observed": observed,
        "expected": expected,
        "evidence_record_id": fact.evidence_record_id,
        "source_group_id": fact.source_group_id,
        "record_digest": fact.record_digest,
    }


def user_defined_scc_screening(x: UserDefinedSCCScreening) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "environment_evidence_reviewed",
            "material_evidence_reviewed",
            "stress_evidence_reviewed",
            "fact_definitions_units_and_digests_reviewed",
            "mechanism_profile_rules_and_unknown_policy_reviewed",
            "screening_and_qualification_boundary_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_fact_ids = [row.fact_id for row in x.facts if row.status == "invalid"]
    facts = {row.fact_id: row for row in x.facts}
    rule_findings = []
    any_rule_met = False
    any_rule_unknown = False
    for rule in x.mechanism_profile.rules:
        conditions = [_condition_finding(condition, facts) for condition in rule.conditions]
        outcomes = {row["outcome"] for row in conditions}
        if "false" in outcomes:
            rule_outcome = "not_met"
        elif "unknown" in outcomes:
            rule_outcome = "unknown"
            any_rule_unknown = True
        else:
            rule_outcome = "met"
            any_rule_met = True
        rule_findings.append(
            {
                "rule_id": rule.rule_id,
                "rule_definition": rule.rule_definition,
                "rule_outcome": rule_outcome,
                "condition_findings": conditions,
            }
        )

    if missing_reviews or invalid_fact_ids:
        status = "needs_data"
        outcome = "indeterminate"
        outcome_basis = "review gates or invalid evidence records are incomplete"
    elif any_rule_met:
        status = "computed"
        outcome = "potentially_applicable"
        outcome_basis = "at least one caller-defined screening rule was met"
    elif any_rule_unknown:
        if x.mechanism_profile.unknown_policy == "screen_in":
            status = "computed"
            outcome = "potentially_applicable"
            outcome_basis = "unknown evidence was conservatively screened in by caller policy"
        else:
            status = "needs_data"
            outcome = "indeterminate"
            outcome_basis = "unknown evidence was retained as indeterminate by caller policy"
    else:
        status = "computed"
        outcome = "not_indicated"
        outcome_basis = "every caller-defined screening rule had at least one false condition"

    body = {
        "assessment_id": x.assessment_id,
        "mechanism": x.mechanism,
        "profile_id": x.mechanism_profile.profile_id,
        "profile_version": x.mechanism_profile.profile_version,
        "profile_provider_id": x.mechanism_profile.profile_provider_id,
        "unknown_policy": x.mechanism_profile.unknown_policy,
        "screening_outcome": outcome,
        "screening_outcome_basis": outcome_basis,
        "rule_findings": rule_findings,
        "invalid_fact_ids": invalid_fact_ids,
        "unknown_fact_ids": [row.fact_id for row in x.facts if row.status == "unknown"],
        "missing_reviews": missing_reviews,
        "screening_only": True,
        "qualification_outcome": "not_evaluated",
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }
    notes = (
        "Rules, thresholds, descriptors and unknown policy are caller-owned; no proprietary limit is bundled.",
        "A potentially-applicable or not-indicated result is a screening outcome, not qualification, acceptance or evidence of cracking.",
        "No initiation threshold, crack-growth rate, life or failure probability is inferred.",
    )
    body["result_digest"] = canonical_digest({"status": status, "values": body, "notes": list(notes)})
    return Calculation(status=status, values=body, notes=notes)


def specifications():
    output_units = {
        "assessment_id": "1",
        "mechanism": "1",
        "profile_id": "1",
        "profile_version": "1",
        "profile_provider_id": "1",
        "unknown_policy": "1",
        "screening_outcome": "1",
        "screening_outcome_basis": "1",
        "rule_findings": "mixed",
        "invalid_fact_ids": "1",
        "unknown_fact_ids": "1",
        "missing_reviews": "1",
        "screening_only": "1",
        "qualification_outcome": "1",
        "input_digest": "1",
        "result_digest": "1",
    }

    def spec(mechanism: SCCMechanism):
        def same_identity(x, context):
            if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
                raise ValueError("SCC screening asset and location must match run context")
            if x.mechanism != mechanism:
                raise ValueError(f"{mechanism} model requires its matching mechanism profile")

        return ModelSpec(
            f"degradation.{mechanism}_user_screening",
            UserDefinedSCCScreening,
            user_defined_scc_screening,
            output_units,
            (
                "Facts and rules are caller-authored and retain evidence record, source group and digest lineage.",
                "Unknown inputs cannot produce a not-indicated result.",
                "Screening does not establish qualification, acceptance, life or failure probability.",
            ),
            ("authored_caller_defined_scc_rule_screening",),
            context_validator=same_identity,
        )

    return [spec(mechanism) for mechanism in ("chloride_scc", "ammonia_scc", "alkaline_scc")]
