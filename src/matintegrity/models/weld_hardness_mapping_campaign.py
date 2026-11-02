"""Caller-profile campaign audit for spatial weld hardness maps."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

WeldRegion = Literal["base_material", "haz", "fusion_boundary", "weld_metal", "user_defined"]


class WeldHardnessSubject(Contract):
    weld_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    wps_id: str = Field(min_length=1)
    wps_revision: str = Field(min_length=1)
    production_heat_id: str = Field(min_length=1)
    consumable_id: str = Field(min_length=1)
    consumable_lot_id: str = Field(min_length=1)
    base_material_a_id: str = Field(min_length=1)
    base_material_a_heat_id: str = Field(min_length=1)
    base_material_b_id: str = Field(min_length=1)
    base_material_b_heat_id: str = Field(min_length=1)
    weld_metal_material_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    cross_section_id: str = Field(min_length=1)
    cross_section_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    subject_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HardnessTestConfiguration(Contract):
    configuration_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    method_revision: str = Field(min_length=1)
    hardness_scale_id: str = Field(min_length=1)
    hardness_unit_token: str = Field(min_length=1)
    test_load_value: Positive
    test_load_unit_token: str = Field(min_length=1)
    dwell_time_s: Positive
    indenter_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    reference_calibration_id: str = Field(min_length=1)
    reference_calibration_provider_id: str = Field(min_length=1)
    reference_calibration_valid: bool
    invalid_calibration_basis: str | None = None
    reference_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def calibration_basis(self):
        if not self.reference_calibration_valid and not self.invalid_calibration_basis:
            raise ValueError("invalid hardness calibration requires a basis")
        return self


class WeldHardnessPoint(Contract):
    point_id: str = Field(min_length=1)
    traverse_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_x: float
    coordinate_y: float
    coordinate_z: float
    coordinate_unit_token: str = Field(min_length=1)
    caller_assigned_region: WeldRegion
    user_defined_region_description: str | None = Field(default=None, min_length=1)
    region_assignment_basis: str = Field(min_length=1)
    hardness_value: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    expanded_hardness_uncertainty: Nonnegative
    uncertainty_basis: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_reading_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    point_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_region_and_record(self):
        if self.caller_assigned_region == "user_defined" and not self.user_defined_region_description:
            raise ValueError("user-defined hardness regions require a description")
        if self.caller_assigned_region != "user_defined" and self.user_defined_region_description is not None:
            raise ValueError("only user-defined hardness regions may carry a custom description")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid hardness points require a basis")
        return self


class WeldHardnessTraverse(Contract):
    traverse_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    orientation_definition: str = Field(min_length=1)
    nominal_offset_or_depth: float
    coordinate_unit_token: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    points: tuple[WeldHardnessPoint, ...] = Field(min_length=1)
    traverse_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_points(self):
        ids = [row.point_id for row in self.points]
        if len(set(ids)) != len(ids):
            raise ValueError("hardness point identities must be unique within a traverse")
        if any(row.traverse_id != self.traverse_id for row in self.points):
            raise ValueError("hardness points must reference their containing traverse")
        if any(
            row.coordinate_frame_id != self.coordinate_frame_id
            or row.coordinate_unit_token != self.coordinate_unit_token
            for row in self.points
        ):
            raise ValueError("hardness points must use their traverse coordinate frame and unit")
        return self


class HardnessRegionCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    region: WeldRegion
    aggregation: Literal["minimum", "maximum"]
    direction: Literal["minimum", "maximum"]
    accept_limit: Nonnegative
    reject_limit: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum hardness criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum hardness criteria require accept <= reject")
        return self


class WeldHardnessCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_regions: tuple[WeldRegion, ...] = Field(min_length=1)
    minimum_traverse_count: int = Field(ge=1)
    minimum_independent_source_group_count: int = Field(ge=1)
    required_configuration_id: str = Field(min_length=1)
    required_method_id: str = Field(min_length=1)
    required_method_revision: str = Field(min_length=1)
    required_hardness_scale_id: str = Field(min_length=1)
    required_hardness_unit_token: str = Field(min_length=1)
    required_test_load_value: Positive
    required_test_load_unit_token: str = Field(min_length=1)
    required_dwell_time_s: Positive
    required_indenter_id: str = Field(min_length=1)
    criteria: tuple[HardnessRegionCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    scale_conversion_used: Literal[False] = False
    strength_inference_claimed: Literal[False] = False
    built_in_code_or_standard_limits_used: Literal[False] = False
    automatic_haz_classification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_regions)) != len(self.required_regions):
            raise ValueError("required weld hardness regions must be unique")
        ids = [row.criterion_id for row in self.criteria]
        regions = [row.region for row in self.criteria]
        if len(set(ids)) != len(ids) or len(set(regions)) != len(regions):
            raise ValueError("hardness criteria must have unique identities and one row per region")
        if set(regions) != set(self.required_regions):
            raise ValueError("caller profile requires one hardness criterion per required region")
        return self


class WeldHardnessMappingCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    subject: WeldHardnessSubject
    configuration: HardnessTestConfiguration
    traverses: tuple[WeldHardnessTraverse, ...] = Field(min_length=1)
    caller_profile: WeldHardnessCallerProfile
    weld_joint_wps_heat_consumable_material_identity_reviewed: bool
    coordinate_frame_traverse_and_orientation_reviewed: bool
    caller_region_assignment_and_basis_reviewed: bool
    method_scale_load_dwell_indenter_and_calibration_reviewed: bool
    point_coordinates_readings_units_and_uncertainty_reviewed: bool
    replicate_source_and_independence_claims_reviewed: bool
    provider_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        traverse_ids = [row.traverse_id for row in self.traverses]
        point_ids = [point.point_id for row in self.traverses for point in row.points]
        raw_digests = [point.raw_reading_digest for row in self.traverses for point in row.points]
        point_digests = [point.point_record_digest for row in self.traverses for point in row.points]
        for values, label in (
            (traverse_ids, "traverse"),
            (point_ids, "point"),
            (raw_digests, "raw-reading digest"),
            (point_digests, "point-record digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"weld hardness campaign {label} identities must be unique")
        if any(row.coordinate_frame_id != self.subject.coordinate_frame_id for row in self.traverses):
            raise ValueError("hardness traverses must use the subject coordinate frame")
        return self


class WeldHardnessMappingCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.weld_hardness_mapping_campaign_report.v1"] = (
        "matintegrity.weld_hardness_mapping_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    region_metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    hardness_scale_converted: Literal[False] = False
    strength_inferred: Literal[False] = False
    automatic_haz_classification: Literal[False] = False
    specification_acceptance_or_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("weld hardness mapping report digest does not match content")
        return self


def _bound_report(**payload: Any) -> WeldHardnessMappingCampaignReport:
    unsigned = WeldHardnessMappingCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return WeldHardnessMappingCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: HardnessRegionCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def weld_hardness_mapping_campaign(x: WeldHardnessMappingCampaignAssessment) -> Calculation:
    review_fields = (
        "weld_joint_wps_heat_consumable_material_identity_reviewed",
        "coordinate_frame_traverse_and_orientation_reviewed",
        "caller_region_assignment_and_basis_reviewed",
        "method_scale_load_dwell_indenter_and_calibration_reviewed",
        "point_coordinates_readings_units_and_uncertainty_reviewed",
        "replicate_source_and_independence_claims_reviewed",
        "provider_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    points = [point for row in x.traverses for point in row.points]
    invalid_points = [row.point_id for row in points if not row.record_valid]
    profile = x.caller_profile
    configuration_identity = (
        x.configuration.configuration_id,
        x.configuration.method_id,
        x.configuration.method_revision,
        x.configuration.hardness_scale_id,
        x.configuration.hardness_unit_token,
        x.configuration.test_load_value,
        x.configuration.test_load_unit_token,
        x.configuration.dwell_time_s,
        x.configuration.indenter_id,
    )
    required_identity = (
        profile.required_configuration_id,
        profile.required_method_id,
        profile.required_method_revision,
        profile.required_hardness_scale_id,
        profile.required_hardness_unit_token,
        profile.required_test_load_value,
        profile.required_test_load_unit_token,
        profile.required_dwell_time_s,
        profile.required_indenter_id,
    )
    configuration_mismatch = configuration_identity != required_identity
    unit_mismatch_points = [
        row.point_id for row in points if row.hardness_unit_token != profile.required_hardness_unit_token
    ]
    represented_regions = {row.caller_assigned_region for row in points}
    missing_regions = sorted(set(profile.required_regions) - represented_regions)
    independent_groups = {(row.source_group_id, row.independence_group_id) for row in x.traverses}
    count_gaps = {
        "traverse_count": len(x.traverses) < profile.minimum_traverse_count,
        "independent_source_group_count": len(independent_groups)
        < profile.minimum_independent_source_group_count,
    }
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_point_ids": invalid_points,
        "configuration_identity_mismatch": configuration_mismatch,
        "invalid_reference_calibration": not x.configuration.reference_calibration_valid,
        "unit_mismatch_point_ids": unit_mismatch_points,
        "missing_required_regions": missing_regions,
        "campaign_count_gaps": count_gaps,
        "traverse_ids": [row.traverse_id for row in x.traverses],
        "raw_reading_digests": [row.raw_reading_digest for row in points],
        "point_record_digests": [row.point_record_digest for row in points],
    }
    incomplete = (
        missing_reviews
        or invalid_points
        or configuration_mismatch
        or not x.configuration.reference_calibration_valid
        or unit_mismatch_points
        or missing_regions
        or any(count_gaps.values())
    )
    if incomplete:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            region_metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Reviewed exact-configuration readings in every caller-required region are required.",),
        )

    criteria = {row.region: row for row in profile.criteria}
    metric_values: dict[str, float] = {}
    for region, criterion in criteria.items():
        values = [row.hardness_value for row in points if row.caller_assigned_region == region]
        metric_values[region] = min(values) if criterion.aggregation == "minimum" else max(values)
    criterion_unit_mismatch = [
        row.criterion_id
        for row in profile.criteria
        if row.hardness_unit_token != profile.required_hardness_unit_token
    ]
    if criterion_unit_mismatch:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            region_metric_values=metric_values,
            criterion_findings=(),
            diagnostics={**diagnostics, "criterion_unit_mismatch_ids": criterion_unit_mismatch},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller criterion scale and unit must exactly match point readings.",),
        )

    findings = tuple(
        {
            "criterion_id": row.criterion_id,
            "caller_assigned_region": row.region,
            "aggregation": row.aggregation,
            "value": metric_values[row.region],
            "unit": row.hardness_unit_token,
            "direction": row.direction,
            "accept_limit": row.accept_limit,
            "reject_limit": row.reject_limit,
            "outcome": _criterion_outcome(metric_values[row.region], row),
            "criterion_basis": row.criterion_basis,
        }
        for row in profile.criteria
    )
    outcomes = {row["outcome"] for row in findings}
    campaign_outcome = "reject" if "reject" in outcomes else "review" if "review" in outcomes else "accept"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        campaign_outcome=campaign_outcome,
        caller_profile_id=profile.profile_id,
        region_metric_values=metric_values,
        criterion_findings=findings,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Accept, review and reject reflect caller-authored region criteria only.",
            "Regions are caller labels; no HAZ or fusion-boundary classification is inferred from coordinates or readings.",
            "No scale conversion, strength inference, specification acceptance, qualification, life, or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("weld hardness mapping asset and location must match run context")

    return [
        ModelSpec(
            "welding.hardness_mapping",
            WeldHardnessMappingCampaignAssessment,
            weld_hardness_mapping_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "campaign_outcome": "1",
                "caller_profile_id": "1",
                "region_metric_values": "hardness scale unit",
                "criterion_findings": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "hardness_scale_converted": "1",
                "strength_inferred": "1",
                "automatic_haz_classification": "1",
                "specification_acceptance_or_qualification": "1",
                "report_digest": "1",
            },
            (
                "Weld identity, exact test configuration, coordinates, caller regions, readings, uncertainty and lineage are preserved.",
                "No scale conversion, strength inference, automatic region classification, standard limit, or qualification is produced.",
            ),
            ("authored_weld_hardness_mapping_campaign_audit",),
            context_validator=same_identity,
        )
    ]
