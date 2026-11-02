"""Caller-profile assessment of visual, penetrant and magnetic-particle indications."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest, check_finite

InspectionMethod = Literal["visual_surface", "penetrant", "magnetic_particle"]
Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "inspection.surface_indication_profile_assessment"


class SurfaceInspectionProcedure(Contract):
    method: InspectionMethod
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    procedure_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    examiner_or_provider_id: str = Field(min_length=1)
    equipment_configuration_id: str = Field(min_length=1)
    method_parameters: dict[str, str | float | bool]
    procedure_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def method_parameter_minimum(self):
        required = {
            "visual_surface": {
                "examination_mode",
                "illumination_basis",
                "resolution_check_basis",
            },
            "penetrant": {
                "penetrant_family",
                "dwell_time_s",
                "developer_basis",
                "removal_basis",
            },
            "magnetic_particle": {
                "particle_medium",
                "magnetization_technique",
                "field_direction_basis",
                "field_strength_basis",
            },
        }[self.method]
        missing = required - set(self.method_parameters)
        if missing:
            raise ValueError(f"inspection procedure is missing method parameters: {sorted(missing)}")
        check_finite(self.method_parameters)
        return self


class ExaminedSurfaceRegion(Contract):
    region_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    geometry_type: Literal["planar", "cylindrical", "conical", "complex", "user_defined"]
    geometry_description: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    surface_preparation_id: str = Field(min_length=1)
    target_area_m2: Positive
    examined_area_m2: Nonnegative
    examination_temperature_k: Positive
    unexamined_basis: str | None = None
    surface_constraints_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_coverage(self):
        if self.examined_area_m2 > self.target_area_m2:
            raise ValueError("examined surface area cannot exceed target area")
        if self.examined_area_m2 < self.target_area_m2 and not self.unexamined_basis:
            raise ValueError("incomplete surface coverage requires an unexamined basis")
        return self


class ProfileSurfaceIndication(Contract):
    indication_id: str = Field(min_length=1)
    method: InspectionMethod
    region_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    reported_class: str = Field(min_length=1)
    observation_description: str = Field(min_length=1)
    length_m: Nonnegative | None = None
    length_standard_uncertainty_m: Nonnegative | None = None
    width_m: Nonnegative | None = None
    width_standard_uncertainty_m: Nonnegative | None = None
    area_m2: Nonnegative | None = None
    area_standard_uncertainty_m2: Nonnegative | None = None
    orientation_deg: float | None = Field(default=None, ge=0, lt=360)
    method_observation_descriptor: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_uncertainties(self):
        for value_name, uncertainty_name in (
            ("length_m", "length_standard_uncertainty_m"),
            ("width_m", "width_standard_uncertainty_m"),
            ("area_m2", "area_standard_uncertainty_m2"),
        ):
            value = getattr(self, value_name)
            uncertainty = getattr(self, uncertainty_name)
            if (value is None) != (uncertainty is None):
                raise ValueError(f"{value_name} and {uncertainty_name} must be supplied together")
        return self


class CallerIndicationGroup(Contract):
    group_id: str = Field(min_length=1)
    member_indication_ids: tuple[str, ...] = Field(min_length=1)
    grouping_basis: str = Field(min_length=1)
    aggregate_length_m: Nonnegative | None = None
    aggregate_width_m: Nonnegative | None = None
    aggregate_area_m2: Nonnegative | None = None
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    grouping_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_members(self):
        if len(self.member_indication_ids) != len(set(self.member_indication_ids)):
            raise ValueError("indication group member IDs must be unique")
        return self


class NumericAcceptanceRule(Contract):
    rule_kind: Literal["numeric"] = "numeric"
    rule_id: str = Field(min_length=1)
    target_scope: Literal["examination", "region", "indication", "group"]
    metric: Literal[
        "coverage_fraction",
        "indication_count",
        "length_m",
        "width_m",
        "area_m2",
        "group_member_count",
        "aggregate_length_m",
        "aggregate_width_m",
        "aggregate_area_m2",
    ]
    operator: Literal["less_than", "less_than_or_equal", "greater_than", "greater_than_or_equal"]
    threshold: float
    unit_token: Literal["1", "count", "m", "m^2"]
    missing_metric_disposition: Literal["review", "insufficient_evidence"]
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def metric_unit(self):
        expected = {
            "coverage_fraction": "1",
            "indication_count": "count",
            "length_m": "m",
            "width_m": "m",
            "area_m2": "m^2",
            "group_member_count": "count",
            "aggregate_length_m": "m",
            "aggregate_width_m": "m",
            "aggregate_area_m2": "m^2",
        }[self.metric]
        if self.unit_token != expected:
            raise ValueError("acceptance-rule unit does not match its metric")
        permitted = {
            "examination": {"coverage_fraction", "indication_count"},
            "region": {"coverage_fraction", "indication_count"},
            "indication": {"length_m", "width_m", "area_m2"},
            "group": {
                "group_member_count",
                "aggregate_length_m",
                "aggregate_width_m",
                "aggregate_area_m2",
            },
        }[self.target_scope]
        if self.metric not in permitted:
            raise ValueError("acceptance-rule metric is not valid for its target scope")
        return self


class ProhibitedClassRule(Contract):
    rule_kind: Literal["prohibited_class"] = "prohibited_class"
    rule_id: str = Field(min_length=1)
    target_scope: Literal["indication"] = "indication"
    prohibited_reported_classes: tuple[str, ...] = Field(min_length=1)
    case_sensitive: bool
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_classes(self):
        values = self.prohibited_reported_classes
        normalized = values if self.case_sensitive else tuple(value.casefold() for value in values)
        if any(not value for value in values) or len(normalized) != len(set(normalized)):
            raise ValueError("prohibited reported classes must be nonempty and unique")
        return self


AcceptanceRule = NumericAcceptanceRule | ProhibitedClassRule


class CallerAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    applicable_methods: tuple[InspectionMethod, ...] = Field(min_length=1)
    applicable_procedure_ids: tuple[str, ...] = Field(min_length=1)
    permitted_geometry_types: tuple[
        Literal["planar", "cylindrical", "conical", "complex", "user_defined"], ...
    ] = Field(min_length=1)
    permitted_surface_condition_ids: tuple[str, ...] = Field(min_length=1)
    rules: tuple[AcceptanceRule, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile_entries(self):
        for values, label in (
            (self.applicable_methods, "applicable methods"),
            (self.applicable_procedure_ids, "procedure IDs"),
            (self.permitted_geometry_types, "geometry types"),
            (self.permitted_surface_condition_ids, "surface conditions"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"acceptance-profile {label} must be unique")
        rule_ids = [row.rule_id for row in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("acceptance-profile rule IDs must be unique")
        return self


class SurfaceIndicationAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    method: InspectionMethod
    procedure: SurfaceInspectionProcedure
    regions: tuple[ExaminedSurfaceRegion, ...] = Field(min_length=1)
    indications: tuple[ProfileSurfaceIndication, ...] = ()
    groups: tuple[CallerIndicationGroup, ...] = ()
    acceptance_profile: CallerAcceptanceProfile
    negative_observation_reviewed: bool = False
    region_mapping_and_coverage_reviewed: bool
    indication_geometry_and_grouping_reviewed: bool
    procedure_and_profile_applicability_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_records(self):
        if self.procedure.method != self.method:
            raise ValueError("inspection procedure method must match the assessment method")
        region_ids = [row.region_id for row in self.regions]
        indication_ids = [row.indication_id for row in self.indications]
        group_ids = [row.group_id for row in self.groups]
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("surface-region IDs must be unique")
        if len(indication_ids) != len(set(indication_ids)):
            raise ValueError("surface-indication IDs must be unique")
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("indication-group IDs must be unique")
        if any(row.method != self.method for row in self.indications):
            raise ValueError("all indication methods must match the assessment method")
        if {row.region_id for row in self.indications} - set(region_ids):
            raise ValueError("every indication must reference a declared surface region")
        known = set(indication_ids)
        assigned: set[str] = set()
        for group in self.groups:
            if set(group.member_indication_ids) - known:
                raise ValueError("every indication-group member must be a declared indication")
            if assigned & set(group.member_indication_ids):
                raise ValueError("an indication cannot belong to more than one caller group")
            assigned.update(group.member_indication_ids)
        return self


class AcceptanceRuleEvaluation(Contract):
    rule_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    threshold_or_classes: float | tuple[str, ...]
    unit_token: str
    basis: str = Field(min_length=1)


class SurfaceIndicationAssessmentResult(Contract):
    schema_version: Literal["matintegrity.surface_indication_assessment.v1"] = (
        "matintegrity.surface_indication_assessment.v1"
    )
    model_id: Literal["inspection.surface_indication_profile_assessment"] = MODEL_ID
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    method: InspectionMethod
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    acceptance_profile_id: str = Field(min_length=1)
    acceptance_profile_revision: str = Field(min_length=1)
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    rule_evaluations: tuple[AcceptanceRuleEvaluation, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_or_standard_qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def bound_result(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("surface-indication assessment result digest does not match its content")
        return self


def _passes(value: float, rule: NumericAcceptanceRule) -> bool:
    return {
        "less_than": value < rule.threshold,
        "less_than_or_equal": value <= rule.threshold,
        "greater_than": value > rule.threshold,
        "greater_than_or_equal": value >= rule.threshold,
    }[rule.operator]


def _numeric_targets(x: SurfaceIndicationAssessment, rule: NumericAcceptanceRule):
    total_target = sum(row.target_area_m2 for row in x.regions)
    total_examined = sum(row.examined_area_m2 for row in x.regions)
    if rule.target_scope == "examination":
        value = (
            total_examined / total_target if rule.metric == "coverage_fraction" else float(len(x.indications))
        )
        return [(x.assessment_id, value)]
    if rule.target_scope == "region":
        rows = []
        for region in x.regions:
            value = (
                region.examined_area_m2 / region.target_area_m2
                if rule.metric == "coverage_fraction"
                else float(sum(item.region_id == region.region_id for item in x.indications))
            )
            rows.append((region.region_id, value))
        return rows
    if rule.target_scope == "indication":
        return [(row.indication_id, getattr(row, rule.metric)) for row in x.indications]
    attribute = {
        "group_member_count": None,
        "aggregate_length_m": "aggregate_length_m",
        "aggregate_width_m": "aggregate_width_m",
        "aggregate_area_m2": "aggregate_area_m2",
    }[rule.metric]
    return [
        (
            row.group_id,
            float(len(row.member_indication_ids)) if attribute is None else getattr(row, attribute),
        )
        for row in x.groups
    ]


def assess_surface_indications(x: SurfaceIndicationAssessment) -> SurfaceIndicationAssessmentResult:
    """Apply only the caller-owned profile; no published acceptance table is embedded."""

    profile = x.acceptance_profile
    review_reasons = []
    insufficient_reasons = []
    if not x.procedure.procedure_reviewed:
        insufficient_reasons.append("inspection procedure was not reviewed")
    if not profile.profile_reviewed:
        insufficient_reasons.append("caller acceptance profile was not reviewed")
    for field, statement in (
        ("region_mapping_and_coverage_reviewed", "region mapping and coverage were not reviewed"),
        (
            "indication_geometry_and_grouping_reviewed",
            "indication geometry and grouping were not reviewed",
        ),
        (
            "procedure_and_profile_applicability_reviewed",
            "procedure and profile applicability were not reviewed",
        ),
    ):
        if not getattr(x, field):
            insufficient_reasons.append(statement)
    if any(not row.surface_constraints_reviewed for row in x.regions):
        insufficient_reasons.append("one or more surface-region constraints were not reviewed")
    if any(not row.geometry_reviewed for row in x.indications):
        insufficient_reasons.append("one or more indication geometries were not reviewed")
    if any(not row.grouping_reviewed for row in x.groups):
        insufficient_reasons.append("one or more caller indication groups were not reviewed")
    if not x.indications and not x.negative_observation_reviewed:
        insufficient_reasons.append("an empty indication set requires a reviewed negative observation")

    if x.method not in profile.applicable_methods:
        review_reasons.append("assessment method is outside the caller profile applicability")
    if x.procedure.procedure_id not in profile.applicable_procedure_ids:
        review_reasons.append("procedure ID is outside the caller profile applicability")
    outside_geometry = sorted(
        row.region_id for row in x.regions if row.geometry_type not in profile.permitted_geometry_types
    )
    if outside_geometry:
        review_reasons.append(f"regions outside profile geometry constraints: {outside_geometry}")
    outside_surface = sorted(
        row.region_id
        for row in x.regions
        if row.surface_condition_id not in profile.permitted_surface_condition_ids
    )
    if outside_surface:
        review_reasons.append(f"regions outside profile surface constraints: {outside_surface}")

    evaluations = []
    for rule in profile.rules:
        if isinstance(rule, NumericAcceptanceRule):
            targets = _numeric_targets(x, rule)
            if not targets and rule.target_scope in {"indication", "group"}:
                continue
            for target_id, value in targets:
                if value is None:
                    outcome = rule.missing_metric_disposition
                    basis = f"required caller metric {rule.metric} is missing"
                    if outcome == "review":
                        review_reasons.append(f"{rule.rule_id}:{target_id} missing metric")
                    else:
                        insufficient_reasons.append(f"{rule.rule_id}:{target_id} missing metric")
                else:
                    outcome = "pass" if _passes(value, rule) else "fail"
                    basis = f"caller rule {rule.operator} {rule.threshold} {rule.unit_token}"
                evaluations.append(
                    AcceptanceRuleEvaluation(
                        rule_id=rule.rule_id,
                        target_id=target_id,
                        outcome=outcome,
                        observed_value=value,
                        threshold_or_classes=rule.threshold,
                        unit_token=rule.unit_token,
                        basis=basis,
                    )
                )
        else:
            prohibited = (
                set(rule.prohibited_reported_classes)
                if rule.case_sensitive
                else {value.casefold() for value in rule.prohibited_reported_classes}
            )
            for indication in x.indications:
                observed = (
                    indication.reported_class if rule.case_sensitive else indication.reported_class.casefold()
                )
                evaluations.append(
                    AcceptanceRuleEvaluation(
                        rule_id=rule.rule_id,
                        target_id=indication.indication_id,
                        outcome="fail" if observed in prohibited else "pass",
                        observed_value=indication.reported_class,
                        threshold_or_classes=rule.prohibited_reported_classes,
                        unit_token="reported_class",
                        basis="caller profile prohibited-class comparison",
                    )
                )

    if insufficient_reasons:
        disposition: Disposition = "insufficient_evidence"
    elif review_reasons or any(row.outcome == "review" for row in evaluations):
        disposition = "review"
    elif any(row.outcome == "fail" for row in evaluations):
        disposition = "reject"
    else:
        disposition = "accept"

    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "method": x.method,
        "procedure_id": x.procedure.procedure_id,
        "procedure_revision": x.procedure.procedure_revision,
        "acceptance_profile_id": profile.profile_id,
        "acceptance_profile_revision": profile.profile_revision,
        "disposition": disposition,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "rule_evaluations": tuple(evaluations),
        "review_reasons": tuple(dict.fromkeys(review_reasons)),
        "insufficient_evidence_reasons": tuple(dict.fromkeys(insufficient_reasons)),
        "notes": (
            "Disposition applies only the caller-supplied procedure and acceptance profile.",
            "No published acceptance table, qualification, physical validation, remaining life or failure probability is claimed.",
            "Reported indication classes and caller groups are not reclassified by this module.",
        ),
    }
    unsigned = SurfaceIndicationAssessmentResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return SurfaceIndicationAssessmentResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )
