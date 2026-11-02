"""Caller-profile reconciliation of measured wall-thickness replicates."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest


class WallThicknessReplicate(Contract):
    replicate_id: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    measured_thickness: Positive | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    measurement_location_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    measurement_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_values(self):
        if self.status == "reported":
            if self.measured_thickness is None or self.expanded_uncertainty is None:
                raise ValueError("reported wall-thickness replicates require value and uncertainty")
        elif self.measured_thickness is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid wall-thickness replicates cannot carry numeric results")
        elif not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid wall-thickness replicates require a basis")
        return self


class WallToleranceCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    nominal_thickness: Positive
    thickness_unit_token: str = Field(min_length=1)
    lower_tolerance_from_nominal: Nonnegative
    upper_tolerance_from_nominal: Nonnegative
    forming_allowance: Nonnegative
    corrosion_allowance: Nonnegative
    allowance_accounting: Literal["record_only_not_applied_to_product_tolerance"] = (
        "record_only_not_applied_to_product_tolerance"
    )
    comparison_basis: Literal["reported_thickness_uncertainty_interval_against_nominal_band"] = (
        "reported_thickness_uncertainty_interval_against_nominal_band"
    )
    profile_basis: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_lower_limit(self):
        if self.lower_tolerance_from_nominal >= self.nominal_thickness:
            raise ValueError("caller lower wall tolerance must leave a positive product thickness")
        return self

    @property
    def lower_limit(self) -> float:
        return self.nominal_thickness - self.lower_tolerance_from_nominal

    @property
    def upper_limit(self) -> float:
        return self.nominal_thickness + self.upper_tolerance_from_nominal

    @property
    def deterministic_digest(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


class WallToleranceAssessment(Contract):
    schema_version: Literal["matintegrity.wall_tolerances.v1"] = "matintegrity.wall_tolerances.v1"
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    nominal_thickness: Positive
    thickness_unit_token: str = Field(min_length=1)
    forming_allowance: Nonnegative
    corrosion_allowance: Nonnegative
    replicates: tuple[WallThicknessReplicate, ...] = Field(min_length=1)
    caller_profile: WallToleranceCallerProfile
    product_region_nominal_and_units_reviewed: bool
    allowances_and_nonapplication_policy_reviewed: bool
    replicate_methods_uncertainties_and_provenance_reviewed: bool
    caller_profile_and_missing_evidence_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def identities_and_digest(self, info: ValidationInfo):
        ids = [row.replicate_id for row in self.replicates]
        if len(set(ids)) != len(ids):
            raise ValueError("wall-thickness replicate identifiers must be unique")
        profile = self.caller_profile
        pairs = (
            (self.product_id, profile.product_id),
            (self.product_form_id, profile.product_form_id),
            (self.region_id, profile.region_id),
            (self.thickness_unit_token, profile.thickness_unit_token),
            (self.nominal_thickness, profile.nominal_thickness),
            (self.forming_allowance, profile.forming_allowance),
            (self.corrosion_allowance, profile.corrosion_allowance),
        )
        if any(left != right for left, right in pairs):
            raise ValueError(
                "assessment product, region, nominal, unit and allowances must match the profile"
            )
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("wall-tolerance assessment payload digest mismatch")
        return self


def wall_tolerance_assessment(**payload) -> WallToleranceAssessment:
    unsigned = WallToleranceAssessment.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return WallToleranceAssessment.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )


class WallToleranceReplicateFinding(Contract):
    replicate_id: str
    outcome: Literal["within", "outside", "boundary_overlap", "missing", "invalid", "unit_mismatch"]
    lower_measurement_bound: float | None = None
    upper_measurement_bound: float | None = None
    basis: str


class WallToleranceReport(Contract):
    assessment_id: str
    decision: Literal["accept", "reject", "review", "insufficient_evidence"]
    nominal_thickness: float
    lower_tolerance_limit: float
    upper_tolerance_limit: float
    forming_allowance_recorded: float
    corrosion_allowance_recorded: float
    allowances_applied_to_tolerance_decision: Literal[False] = False
    conservative_reported_lower_bound: float | None = None
    findings: tuple[WallToleranceReplicateFinding, ...]
    input_digest: str
    profile_digest: str
    report_digest: str
    specification_qualification_claim: Literal[False] = False
    design_adequacy_claim: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def bound_digest(self):
        if canonical_digest(self.digest_payload()) != self.report_digest:
            raise ValueError("wall-tolerance report digest mismatch")
        return self


def assess_wall_tolerances(x: WallToleranceAssessment) -> WallToleranceReport:
    profile = x.caller_profile
    reviews = (
        x.product_region_nominal_and_units_reviewed,
        x.allowances_and_nonapplication_policy_reviewed,
        x.replicate_methods_uncertainties_and_provenance_reviewed,
        x.caller_profile_and_missing_evidence_policy_reviewed,
    )
    findings = []
    reported_lower_bounds = []
    for replicate in x.replicates:
        if replicate.status != "reported":
            findings.append(
                WallToleranceReplicateFinding(
                    replicate_id=replicate.replicate_id,
                    outcome=replicate.status,
                    basis="Replicate is missing or invalid.",
                )
            )
            continue
        if replicate.unit_token != profile.thickness_unit_token:
            findings.append(
                WallToleranceReplicateFinding(
                    replicate_id=replicate.replicate_id,
                    outcome="unit_mismatch",
                    basis="Replicate unit differs from the exact caller-profile unit.",
                )
            )
            continue
        lower = replicate.measured_thickness - replicate.expanded_uncertainty
        upper = replicate.measured_thickness + replicate.expanded_uncertainty
        reported_lower_bounds.append(lower)
        entirely_within = lower >= profile.lower_limit and upper <= profile.upper_limit
        entirely_outside = upper < profile.lower_limit or lower > profile.upper_limit
        outcome = "within" if entirely_within else "outside" if entirely_outside else "boundary_overlap"
        findings.append(
            WallToleranceReplicateFinding(
                replicate_id=replicate.replicate_id,
                outcome=outcome,
                lower_measurement_bound=lower,
                upper_measurement_bound=upper,
                basis="Reported uncertainty interval compared with the caller asymmetric nominal band.",
            )
        )
    outcomes = {row.outcome for row in findings}
    if not all(reviews) or outcomes & {"missing", "invalid", "unit_mismatch"}:
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
        "nominal_thickness": x.nominal_thickness,
        "lower_tolerance_limit": profile.lower_limit,
        "upper_tolerance_limit": profile.upper_limit,
        "forming_allowance_recorded": x.forming_allowance,
        "corrosion_allowance_recorded": x.corrosion_allowance,
        "allowances_applied_to_tolerance_decision": False,
        "conservative_reported_lower_bound": min(reported_lower_bounds) if reported_lower_bounds else None,
        "findings": [row.model_dump(mode="json") for row in findings],
        "input_digest": x.payload_digest,
        "profile_digest": profile.deterministic_digest,
        "specification_qualification_claim": False,
        "design_adequacy_claim": False,
    }
    return WallToleranceReport.model_validate(
        {**payload, "findings": tuple(findings), "report_digest": canonical_digest(payload)}
    )
