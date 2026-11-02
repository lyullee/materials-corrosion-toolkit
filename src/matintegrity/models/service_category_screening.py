"""Evidence-bound caller service categories, without embedded code criteria."""

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest
from .scc_rule_screening import SCCRuleCondition, SCCScreeningFact, SCCScreeningRule, _condition_finding


class ServiceCategoryFact(SCCScreeningFact):
    domain: Literal[
        "fluid", "pressure", "temperature", "equipment", "material", "operation", "owner_decision", "location"
    ]
    numeric_value: float | None = Field(default=None, strict=True)
    boolean_value: bool | None = Field(default=None, strict=True)


class ServiceCategoryCondition(SCCRuleCondition):
    threshold: float | None = Field(default=None, strict=True)
    lower_bound: float | None = Field(default=None, strict=True)
    upper_bound: float | None = Field(default=None, strict=True)


class ServiceCategoryRule(SCCScreeningRule):
    conditions: tuple[ServiceCategoryCondition, ...] = Field(min_length=1)


class ServiceCategoryProfile(Contract):
    profile_id: str = Field(min_length=1)
    category_id: str = Field(min_length=1)
    code_namespace: str = Field(min_length=1)
    code_edition: str = Field(min_length=1)
    equipment_boundary_id: str = Field(min_length=1)
    authority_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    required_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=1000)
    rules: tuple[ServiceCategoryRule, ...] = Field(min_length=1, max_length=1000)
    authority_scope_and_rule_completeness_reviewed: bool
    profile_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def pinned_conditions(self):
        for ids in (self.required_fact_ids, tuple(rule.rule_id for rule in self.rules)):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("service profile fact and rule identifiers must be unique and nonblank")
        if any(
            condition.fact_id not in self.required_fact_ids
            for rule in self.rules
            for condition in rule.conditions
        ):
            raise ValueError("service rules must reference explicitly required facts")
        digest = canonical_digest(self.model_dump(mode="json", exclude={"profile_sha256", "evidence"}))
        if digest != self.profile_sha256 or not any(
            e.sha256 == digest and e.license_id for e in self.evidence
        ):
            raise ValueError("licensed service profile evidence must pin its exact criteria and authority")
        return self


class ServiceCategoryScreening(CorrelationRequest):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    equipment_boundary_id: str = Field(min_length=1)
    facts: tuple[ServiceCategoryFact, ...] = Field(max_length=10000)
    profiles: tuple[ServiceCategoryProfile, ...] = Field(min_length=1, max_length=500)
    facts_units_scope_and_lineage_reviewed: bool
    owner_authority_and_profile_selection_reviewed: bool
    maximum_condition_evaluations: int = Field(default=100000, ge=1, le=1000000)

    @model_validator(mode="after")
    def identity_and_budget(self):
        for ids in (tuple(f.fact_id for f in self.facts), tuple(p.profile_id for p in self.profiles)):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("service fact and profile identities must be unique and nonblank")
        keys = [(p.code_namespace, p.code_edition, p.category_id) for p in self.profiles]
        if len(set(keys)) != len(keys):
            raise ValueError("one profile per code edition and category is required")
        if any(p.equipment_boundary_id != self.equipment_boundary_id for p in self.profiles):
            raise ValueError("all service profiles must match the exact equipment boundary")
        if (
            sum(len(rule.conditions) for p in self.profiles for rule in p.rules)
            > self.maximum_condition_evaluations
        ):
            raise ValueError("service condition evaluation budget exceeded")
        return self


def service_category_screening(x: ServiceCategoryScreening) -> Calculation:
    facts = {fact.fact_id: fact for fact in x.facts}
    results = []
    for profile in x.profiles:
        missing = [key for key in profile.required_fact_ids if key not in facts]
        unresolved = [
            key for key in profile.required_fact_ids if key in facts and facts[key].status != "known"
        ]
        findings = []
        for rule in profile.rules:
            conditions = [_condition_finding(condition, facts) for condition in rule.conditions]
            for finding in conditions:
                fact = facts.get(finding["fact_id"])
                if fact is not None:
                    finding.update(
                        record_digest=fact.record_digest,
                        evidence_record_id=fact.evidence_record_id,
                        source_group_id=fact.source_group_id,
                        fact_domain=fact.domain,
                    )
            outcomes = {condition["outcome"] for condition in conditions}
            outcome = "unknown" if "unknown" in outcomes else "not_met" if "false" in outcomes else "met"
            findings.append(dict(rule_id=rule.rule_id, outcome=outcome, conditions=conditions))
        reviewed = (
            x.facts_units_scope_and_lineage_reviewed
            and x.owner_authority_and_profile_selection_reviewed
            and profile.authority_scope_and_rule_completeness_reviewed
        )
        if not reviewed or missing or unresolved or any(row["outcome"] == "unknown" for row in findings):
            outcome, status = "indeterminate", "needs_data"
        else:
            outcome = "matched" if any(row["outcome"] == "met" for row in findings) else "not_matched"
            status = "computed"
        results.append(
            dict(
                profile_id=profile.profile_id,
                category_id=profile.category_id,
                code_namespace=profile.code_namespace,
                code_edition=profile.code_edition,
                authority_id=profile.authority_id,
                revision=profile.revision,
                profile_sha256=profile.profile_sha256,
                outcome=outcome,
                status=status,
                reviews_complete=reviewed,
                missing_required_fact_ids=missing,
                unresolved_required_fact_ids=unresolved,
                rule_findings=findings,
            )
        )
    return Calculation(
        status="needs_data" if any(row["status"] == "needs_data" for row in results) else "computed",
        values=dict(
            assessment_id=x.assessment_id,
            physical_scope_id=x.physical_scope_id,
            equipment_boundary_id=x.equipment_boundary_id,
            category_findings=results,
            matched_profile_ids=[row["profile_id"] for row in results if row["outcome"] == "matched"],
            classification_decision="not_made",
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Caller categories only; conditions are AND within each rule and rules are OR within a profile.",
            "Missing, invalid and unit/kind-mismatched facts stay indeterminate. No default normal category, hierarchy, code equivalence, toxicity, failure probability or acceptance is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("service screening asset and location must match run context")

    return [
        ModelSpec(
            "workflow.service_category_screening",
            ServiceCategoryScreening,
            service_category_screening,
            {"category_findings": "structured_record", "matched_profile_ids": "structured_record"},
            ("Caller profiles bind code edition, equipment boundary, authority and reviewed evidence.",),
            (SOURCE_ID,),
            qualification="user_model",
            context_validator=same_identity,
        )
    ]
