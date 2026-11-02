"""Caller-owned multi-mechanism screening; no built-in susceptibility matrix."""

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest
from .scc_rule_screening import SCCScreeningFact, SCCScreeningRule, _condition_finding


class DamageMechanismFact(SCCScreeningFact):
    domain: Literal[
        "environment", "material", "stress", "geometry", "flow", "thermal_history", "inspection", "process"
    ]


class DamageMechanismProfile(Contract):
    profile_id: str = Field(min_length=1)
    mechanism_id: str = Field(min_length=1)
    mechanism_definition: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    required_fact_ids: tuple[str, ...] = Field(min_length=1, max_length=1000)
    rules: tuple[SCCScreeningRule, ...] = Field(min_length=1, max_length=1000)
    unknown_policy: Literal["indeterminate", "screen_in"]
    authority_and_rule_completeness_reviewed: bool
    profile_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def exact_rules_and_digest(self):
        for ids in (self.required_fact_ids, tuple(row.rule_id for row in self.rules)):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("profile required facts and rule identities must be unique and nonblank")
        if any(c.fact_id not in self.required_fact_ids for rule in self.rules for c in rule.conditions):
            raise ValueError("every rule condition must reference an explicitly required fact")
        digest = canonical_digest(self.model_dump(mode="json", exclude={"profile_sha256", "evidence"}))
        if digest != self.profile_sha256 or not any(
            row.sha256 == digest and row.license_id for row in self.evidence
        ):
            raise ValueError("licensed profile evidence must pin the exact rules, required facts and policy")
        return self


class DamageMechanismScreening(CorrelationRequest):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    facts: tuple[DamageMechanismFact, ...] = Field(max_length=10000)
    profiles: tuple[DamageMechanismProfile, ...] = Field(min_length=1, max_length=500)
    facts_units_lineage_and_physical_scope_reviewed: bool
    screening_boundary_and_profile_selection_reviewed: bool
    maximum_condition_evaluations: int = Field(default=100000, ge=1, le=1000000)

    @model_validator(mode="after")
    def unique_scope_and_budget(self):
        for ids in (
            tuple(row.fact_id for row in self.facts),
            tuple(row.profile_id for row in self.profiles),
            tuple(row.mechanism_id for row in self.profiles),
        ):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("fact, profile and mechanism identities must be unique and nonblank")
        if (
            sum(len(rule.conditions) for profile in self.profiles for rule in profile.rules)
            > self.maximum_condition_evaluations
        ):
            raise ValueError("mechanism condition evaluation budget exceeded")
        return self


def damage_mechanism_screening(x: DamageMechanismScreening) -> Calculation:
    facts = {row.fact_id: row for row in x.facts}
    results = []
    for profile in x.profiles:
        missing = [key for key in profile.required_fact_ids if key not in facts]
        invalid = [
            key for key in profile.required_fact_ids if key in facts and facts[key].status == "invalid"
        ]
        unknown = [
            key for key in profile.required_fact_ids if key in facts and facts[key].status == "unknown"
        ]
        rules = []
        for rule in profile.rules:
            conditions = []
            for condition in rule.conditions:
                finding = _condition_finding(condition, facts)
                fact = facts.get(condition.fact_id)
                if fact is not None:
                    finding.update(
                        fact_domain=fact.domain,
                        fact_status=fact.status,
                        evidence_record_id=fact.evidence_record_id,
                        source_group_id=fact.source_group_id,
                        record_digest=fact.record_digest,
                    )
                conditions.append(finding)
            # Unknown dominates a false condition for this conservative interface.
            outcomes = {row["outcome"] for row in conditions}
            outcome = "unknown" if "unknown" in outcomes else "not_met" if "false" in outcomes else "met"
            rules.append(dict(rule_id=rule.rule_id, rule_outcome=outcome, condition_findings=conditions))
        reviewed = (
            x.facts_units_lineage_and_physical_scope_reviewed
            and x.screening_boundary_and_profile_selection_reviewed
            and profile.authority_and_rule_completeness_reviewed
        )
        unresolved = bool(
            missing or invalid or unknown or any(row["rule_outcome"] == "unknown" for row in rules)
        )
        if not reviewed or invalid:
            outcome, status = "indeterminate", "needs_data"
        elif unresolved:
            outcome = "potentially_applicable" if profile.unknown_policy == "screen_in" else "indeterminate"
            status = "needs_data"
        else:
            outcome = (
                "potentially_applicable"
                if any(row["rule_outcome"] == "met" for row in rules)
                else "not_indicated"
            )
            status = "computed"
        results.append(
            dict(
                profile_id=profile.profile_id,
                mechanism_id=profile.mechanism_id,
                provider_id=profile.provider_id,
                revision=profile.revision,
                profile_sha256=profile.profile_sha256,
                unknown_policy=profile.unknown_policy,
                screening_outcome=outcome,
                status=status,
                missing_required_fact_ids=missing,
                unknown_required_fact_ids=unknown,
                invalid_required_fact_ids=invalid,
                reviews_complete=reviewed,
                rule_findings=rules,
            )
        )
    return Calculation(
        status="needs_data" if any(row["status"] == "needs_data" for row in results) else "computed",
        values=dict(
            assessment_id=x.assessment_id,
            physical_scope_id=x.physical_scope_id,
            material_condition_id=x.material_condition_id,
            mechanism_findings=results,
            screening_only=True,
            qualification_outcome="not_evaluated",
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Caller-selected profiles only; no proprietary susceptibility matrix, default threshold or unselected mechanism is inferred.",
            "Unknown required facts and unit/kind mismatches cannot screen a mechanism out; conservative inclusion still retains needs_data.",
            "Not-indicated is relative to the reviewed caller rules, not proof of absent damage, safety, acceptance, life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("mechanism screening asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.damage_mechanism_screening",
            DamageMechanismScreening,
            damage_mechanism_screening,
            {"mechanism_findings": "structured_record"},
            ("Explicit physical scope, caller facts/profiles and conservative missingness policy.",),
            (SOURCE_ID,),
            qualification="user_model",
            context_validator=same_identity,
        )
    ]
