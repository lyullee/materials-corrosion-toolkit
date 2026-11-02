"""Campaign aggregation for measured electrochemical and local-environment facts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest


class ElectrodeMaterialCouple(Contract):
    couple_id: str = Field(min_length=1)
    electrode_a_material_id: str = Field(min_length=1)
    electrode_a_surface_condition_id: str = Field(min_length=1)
    electrode_a_exposed_area_m2: Positive
    electrode_b_material_id: str = Field(min_length=1)
    electrode_b_surface_condition_id: str = Field(min_length=1)
    electrode_b_exposed_area_m2: Positive
    electrical_connection_definition: str = Field(min_length=1)
    geometry_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @property
    def area_ratio_b_to_a(self) -> float:
        return self.electrode_b_exposed_area_m2 / self.electrode_a_exposed_area_m2


class LocalEnvironmentFact(Contract):
    fact_id: str = Field(min_length=1)
    fact_kind: Literal["potential", "current", "species", "pH", "state_descriptor"]
    quantity_id: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    reference_electrode_id: str | None = None
    method_id: str = Field(min_length=1)
    fact_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_fact(self):
        if self.status == "reported":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("reported local-environment facts require value and uncertainty")
        elif self.value is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid local-environment facts cannot carry numeric results")
        elif not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid local-environment facts require a basis")
        if self.fact_kind == "potential":
            if self.unit_token != "V" or self.reference_electrode_id is None:
                raise ValueError("potential facts require volts and an exact reference-electrode identity")
        elif self.reference_electrode_id is not None:
            raise ValueError("only potential facts carry a reference-electrode identity")
        if self.fact_kind == "current" and self.unit_token != "A":
            raise ValueError("current facts require the exact ampere unit")
        if self.fact_kind == "pH" and self.unit_token != "pH":
            raise ValueError("pH facts require the exact pH unit token")
        return self


class LocalEnvironmentExposureState(Contract):
    state_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    couple_id: str | None = None
    state_descriptors: dict[str, str] = Field(default_factory=dict)
    facts: tuple[LocalEnvironmentFact, ...] = Field(min_length=1)
    state_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_state(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("local-environment exposure states require positive duration")
        keys = [(row.fact_kind, row.quantity_id) for row in self.facts]
        if len(set(keys)) != len(keys):
            raise ValueError("local-environment fact kind and quantity must be unique within a state")
        if any(not key or not value for key, value in self.state_descriptors.items()):
            raise ValueError("local-environment state descriptors cannot be empty")
        return self


class LocalEnvironmentHistoryCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    applicable_domain: Literal["galvanic_coupling", "crevice_chemistry", "under_deposit"]
    fact_kind: Literal["potential", "current", "species", "pH", "area_ratio"]
    quantity_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    reference_electrode_id: str | None = None
    minimum_acceptable: float | None = None
    maximum_acceptable: float | None = None
    comparison: Literal["uncertainty_interval_against_bounds"] = "uncertainty_interval_against_bounds"
    criterion_basis: str = Field(min_length=1)
    criterion_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_criterion(self):
        if self.minimum_acceptable is None and self.maximum_acceptable is None:
            raise ValueError("local-environment criterion requires at least one caller bound")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("local-environment criterion bounds must be ordered")
        if self.fact_kind == "potential":
            if self.unit_token != "V" or self.reference_electrode_id is None:
                raise ValueError("potential criteria require volts and a reference-electrode identity")
        elif self.reference_electrode_id is not None:
            raise ValueError("only potential criteria carry a reference-electrode identity")
        if self.fact_kind == "area_ratio" and self.unit_token != "1":
            raise ValueError("area-ratio criteria require the exact dimensionless unit")
        return self


class LocalEnvironmentHistoryAssessment(Contract):
    schema_version: Literal["matintegrity.local_environment_history.v1"] = (
        "matintegrity.local_environment_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    domain: Literal["galvanic_coupling", "crevice_chemistry", "under_deposit"]
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    couples: tuple[ElectrodeMaterialCouple, ...] = ()
    states: tuple[LocalEnvironmentExposureState, ...] = Field(min_length=1)
    criteria: tuple[LocalEnvironmentHistoryCriterion, ...] = Field(min_length=1)
    clock_state_and_identity_reviewed: bool
    units_references_methods_and_uncertainties_reviewed: bool
    caller_rules_and_missing_evidence_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def history_links_and_digest(self, info: ValidationInfo):
        for values, label in (
            ([row.couple_id for row in self.couples], "couple"),
            ([row.state_id for row in self.states], "state"),
            ([row.criterion_id for row in self.criteria], "criterion"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"local-environment {label} identifiers must be unique")
        for left, right in zip(self.states, self.states[1:], strict=False):
            if right.start_time_s < left.end_time_s:
                raise ValueError("local-environment exposure states must be ordered and nonoverlapping")
        if any(row.applicable_domain != self.domain for row in self.criteria):
            raise ValueError("local-environment criteria must match the assessment domain")
        couple_ids = {row.couple_id for row in self.couples}
        if any(row.couple_id is not None and row.couple_id not in couple_ids for row in self.states):
            raise ValueError("exposure states must reference declared electrode couples")
        if self.domain == "galvanic_coupling" and any(row.couple_id is None for row in self.states):
            raise ValueError("galvanic exposure states require an electrode couple")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("local-environment history payload digest mismatch")
        return self


def local_environment_history_assessment(**payload) -> LocalEnvironmentHistoryAssessment:
    unsigned = LocalEnvironmentHistoryAssessment.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return LocalEnvironmentHistoryAssessment.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )


class LocalEnvironmentFinding(Contract):
    state_id: str
    criterion_id: str
    outcome: Literal["within", "outside", "boundary_overlap", "missing", "invalid", "mismatch"]
    basis: str
    observed_value: float | None = None
    expanded_uncertainty: float | None = None


class LocalEnvironmentHistoryReport(Contract):
    assessment_id: str
    decision: Literal["accept", "reject", "review", "insufficient_evidence"]
    findings: tuple[LocalEnvironmentFinding, ...]
    total_exposure_time_s: float
    complete_evidence_time_s: float
    complete_evidence_fraction: float
    area_ratios_b_to_a: dict[str, float]
    input_digest: str
    report_digest: str
    qualification_claim: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def bound_digest(self):
        if canonical_digest(self.digest_payload()) != self.report_digest:
            raise ValueError("local-environment history report digest mismatch")
        return self


def assess_local_environment_history(
    x: LocalEnvironmentHistoryAssessment,
) -> LocalEnvironmentHistoryReport:
    findings = []
    couples = {row.couple_id: row for row in x.couples}
    review_ready = all(
        (
            x.clock_state_and_identity_reviewed,
            x.units_references_methods_and_uncertainties_reviewed,
            x.caller_rules_and_missing_evidence_policy_reviewed,
        )
    )
    total_time = sum(row.end_time_s - row.start_time_s for row in x.states)
    complete_time = 0.0
    for state in x.states:
        state_complete = review_ready
        facts = {(row.fact_kind, row.quantity_id): row for row in state.facts}
        for criterion in x.criteria:
            if criterion.fact_kind == "area_ratio":
                couple = couples.get(state.couple_id)
                if couple is None:
                    observed = uncertainty = None
                    outcome, basis = "missing", "No electrode couple supports the requested area ratio."
                else:
                    observed, uncertainty = couple.area_ratio_b_to_a, 0.0
                    outcome, basis = _compare(observed, uncertainty, criterion)
            else:
                fact = facts.get((criterion.fact_kind, criterion.quantity_id))
                if fact is None or fact.status == "missing":
                    observed = uncertainty = None
                    outcome, basis = "missing", "Required local-environment fact is missing."
                elif fact.status == "invalid":
                    observed = uncertainty = None
                    outcome, basis = "invalid", "Required local-environment fact is marked invalid."
                elif fact.unit_token != criterion.unit_token or (
                    criterion.fact_kind == "potential"
                    and fact.reference_electrode_id != criterion.reference_electrode_id
                ):
                    observed, uncertainty = fact.value, fact.expanded_uncertainty
                    outcome, basis = "mismatch", "Fact unit or reference-electrode identity differs."
                else:
                    observed, uncertainty = fact.value, fact.expanded_uncertainty
                    outcome, basis = _compare(observed, uncertainty, criterion)
            if outcome in {"missing", "invalid", "mismatch"}:
                state_complete = False
            findings.append(
                LocalEnvironmentFinding(
                    state_id=state.state_id,
                    criterion_id=criterion.criterion_id,
                    outcome=outcome,
                    basis=basis,
                    observed_value=observed,
                    expanded_uncertainty=uncertainty,
                )
            )
        if state_complete:
            complete_time += state.end_time_s - state.start_time_s

    outcomes = {row.outcome for row in findings}
    if not review_ready or outcomes & {"missing", "invalid", "mismatch"}:
        decision = "insufficient_evidence"
    elif "outside" in outcomes:
        decision = "reject"
    elif "boundary_overlap" in outcomes:
        decision = "review"
    else:
        decision = "accept"
    payload = {
        "assessment_id": x.assessment_id,
        "decision": decision,
        "findings": [row.model_dump(mode="json") for row in findings],
        "total_exposure_time_s": total_time,
        "complete_evidence_time_s": complete_time,
        "complete_evidence_fraction": complete_time / total_time,
        "area_ratios_b_to_a": {key: value.area_ratio_b_to_a for key, value in sorted(couples.items())},
        "input_digest": x.payload_digest,
        "qualification_claim": False,
        "corrosion_rate_inferred": False,
        "failure_probability_inferred": False,
    }
    return LocalEnvironmentHistoryReport.model_validate(
        {**payload, "findings": tuple(findings), "report_digest": canonical_digest(payload)}
    )


def _compare(value, uncertainty, criterion):
    lower, upper = value - uncertainty, value + uncertainty
    inside = (criterion.minimum_acceptable is None or lower >= criterion.minimum_acceptable) and (
        criterion.maximum_acceptable is None or upper <= criterion.maximum_acceptable
    )
    outside = (criterion.minimum_acceptable is not None and upper < criterion.minimum_acceptable) or (
        criterion.maximum_acceptable is not None and lower > criterion.maximum_acceptable
    )
    outcome = "within" if inside else "outside" if outside else "boundary_overlap"
    return outcome, "Measured uncertainty interval compared with caller-owned bounds."
