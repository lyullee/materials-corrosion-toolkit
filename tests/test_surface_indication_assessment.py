from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.surface_indication_assessment import (
    SurfaceIndicationAssessment,
    SurfaceIndicationAssessmentResult,
    assess_surface_indications,
)

SHA = "a" * 64


def evidence(label):
    return {
        "source_id": label,
        "origin": "user_declared",
        "citation": f"caller record {label}",
        "sha256": SHA,
    }


def procedure(method):
    parameters = {
        "visual_surface": {
            "examination_mode": "direct",
            "illumination_basis": "caller procedure illumination record",
            "resolution_check_basis": "caller resolution check",
        },
        "penetrant": {
            "penetrant_family": "caller-selected visible family",
            "dwell_time_s": 600.0,
            "developer_basis": "caller procedure developer",
            "removal_basis": "caller procedure removal",
        },
        "magnetic_particle": {
            "particle_medium": "caller-selected wet medium",
            "magnetization_technique": "caller procedure yoke technique",
            "field_direction_basis": "two caller-declared directions",
            "field_strength_basis": "caller verification record",
        },
    }[method]
    return {
        "method": method,
        "procedure_id": f"procedure-{method}",
        "procedure_revision": "1",
        "procedure_source_digest": SHA,
        "examiner_or_provider_id": "inspection-provider",
        "equipment_configuration_id": f"equipment-{method}",
        "method_parameters": parameters,
        "procedure_reviewed": True,
        "evidence": (evidence(f"procedure-{method}"),),
    }


def indication(method, length_m=0.004, width_m=0.001, reported_class="rounded"):
    return {
        "indication_id": "indication-1",
        "method": method,
        "region_id": "region-1",
        "physical_location_id": "surface-location-1",
        "reported_class": reported_class,
        "observation_description": "caller-observed surface response",
        "length_m": length_m,
        "length_standard_uncertainty_m": 0.0001,
        "width_m": width_m,
        "width_standard_uncertainty_m": 0.0001,
        "area_m2": length_m * width_m,
        "area_standard_uncertainty_m2": 1e-7,
        "orientation_deg": 30.0,
        "method_observation_descriptor": "method-specific caller observation",
        "source_group_id": "source-group-1",
        "provider_result_digest": SHA,
        "geometry_reviewed": True,
        "evidence": (evidence("indication-1"),),
    }


def profile(method):
    return {
        "profile_id": "caller-profile-1",
        "profile_revision": "3",
        "profile_source_digest": SHA,
        "applicable_methods": (method,),
        "applicable_procedure_ids": (f"procedure-{method}",),
        "permitted_geometry_types": ("cylindrical",),
        "permitted_surface_condition_ids": ("prepared-surface",),
        "rules": (
            {
                "rule_kind": "numeric",
                "rule_id": "complete-coverage",
                "target_scope": "examination",
                "metric": "coverage_fraction",
                "operator": "greater_than_or_equal",
                "threshold": 1.0,
                "unit_token": "1",
                "missing_metric_disposition": "insufficient_evidence",
                "rule_description": "caller requires complete declared coverage",
            },
            {
                "rule_kind": "numeric",
                "rule_id": "caller-length-limit",
                "target_scope": "indication",
                "metric": "length_m",
                "operator": "less_than_or_equal",
                "threshold": 0.005,
                "unit_token": "m",
                "missing_metric_disposition": "insufficient_evidence",
                "rule_description": "caller-provided indication length rule",
            },
            {
                "rule_kind": "numeric",
                "rule_id": "caller-group-count-limit",
                "target_scope": "group",
                "metric": "group_member_count",
                "operator": "less_than_or_equal",
                "threshold": 2.0,
                "unit_token": "count",
                "missing_metric_disposition": "review",
                "rule_description": "caller-provided group member rule",
            },
            {
                "rule_kind": "prohibited_class",
                "rule_id": "caller-prohibited-class",
                "prohibited_reported_classes": ("caller-prohibited",),
                "case_sensitive": False,
                "rule_description": "caller-provided reported-class rule",
            },
        ),
        "profile_reviewed": True,
        "evidence": (evidence("caller-profile"),),
    }


def payload(method="visual_surface", **changes):
    data = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "method": method,
        "procedure": procedure(method),
        "regions": (
            {
                "region_id": "region-1",
                "physical_location_id": "surface-location-1",
                "geometry_type": "cylindrical",
                "geometry_description": "caller-declared cylindrical surface",
                "surface_condition_id": "prepared-surface",
                "surface_preparation_id": "preparation-1",
                "target_area_m2": 0.1,
                "examined_area_m2": 0.1,
                "examination_temperature_k": 295.0,
                "surface_constraints_reviewed": True,
                "evidence": (evidence("region-1"),),
            },
        ),
        "indications": (indication(method),),
        "groups": (
            {
                "group_id": "group-1",
                "member_indication_ids": ("indication-1",),
                "grouping_basis": "caller-declared proximity group",
                "aggregate_length_m": 0.004,
                "aggregate_width_m": 0.001,
                "aggregate_area_m2": 4e-6,
                "provider_result_digest": SHA,
                "grouping_reviewed": True,
                "evidence": (evidence("group-1"),),
            },
        ),
        "acceptance_profile": profile(method),
        "negative_observation_reviewed": False,
        "region_mapping_and_coverage_reviewed": True,
        "indication_geometry_and_grouping_reviewed": True,
        "procedure_and_profile_applicability_reviewed": True,
        "evidence": (evidence("assessment"),),
    }
    data.update(changes)
    return SurfaceIndicationAssessment.model_validate(data)


@pytest.mark.parametrize("method", ["visual_surface", "penetrant", "magnetic_particle"])
def test_all_three_methods_apply_only_caller_profile_and_accept(method):
    result = assess_surface_indications(payload(method))
    assert result.disposition == "accept"
    assert result.method == method
    assert result.acceptance_profile_id == "caller-profile-1"
    assert all(row.outcome == "pass" for row in result.rule_evaluations)
    assert not result.code_or_standard_qualification_claim
    assert not result.physical_validation_claim


def test_reject_review_and_insufficient_evidence_are_distinct():
    too_long = indication("visual_surface", length_m=0.006)
    rejected = assess_surface_indications(payload(indications=(too_long,)))
    assert rejected.disposition == "reject"
    assert any(
        row.rule_id == "caller-length-limit" and row.outcome == "fail" for row in rejected.rule_evaluations
    )

    regions = list(payload().model_dump(mode="python")["regions"])
    regions[0]["surface_condition_id"] = "unlisted-surface"
    reviewed = assess_surface_indications(payload(regions=tuple(regions)))
    assert reviewed.disposition == "review"
    assert reviewed.review_reasons

    incomplete = assess_surface_indications(payload(indication_geometry_and_grouping_reviewed=False))
    assert incomplete.disposition == "insufficient_evidence"
    assert incomplete.insufficient_evidence_reasons


def test_missing_rule_metric_and_unreviewed_negative_observation_are_not_accepted():
    without_width = indication("visual_surface")
    without_width["width_m"] = None
    without_width["width_standard_uncertainty_m"] = None
    profile_value = profile("visual_surface")
    rules = list(profile_value["rules"])
    rules[1] = {**rules[1], "metric": "width_m", "rule_id": "caller-width-limit"}
    profile_value["rules"] = tuple(rules)
    result = assess_surface_indications(
        payload(indications=(without_width,), acceptance_profile=profile_value)
    )
    assert result.disposition == "insufficient_evidence"
    assert any(row.outcome == "insufficient_evidence" for row in result.rule_evaluations)

    empty = assess_surface_indications(payload(indications=(), groups=()))
    assert empty.disposition == "insufficient_evidence"
    assert any("negative observation" in row for row in empty.insufficient_evidence_reasons)


def test_result_digest_is_deterministic_traceable_and_tamper_evident():
    first = assess_surface_indications(payload("penetrant"))
    second = assess_surface_indications(payload("penetrant"))
    assert first.input_digest == second.input_digest
    assert first.result_digest == second.result_digest

    restored = SurfaceIndicationAssessmentResult.model_validate_json(first.model_dump_json())
    assert restored.result_digest == first.result_digest
    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        SurfaceIndicationAssessmentResult.model_validate(changed)


def test_group_members_units_and_method_specific_procedure_are_strict():
    bad_groups = list(payload().model_dump(mode="python")["groups"])
    bad_groups[0]["member_indication_ids"] = ("missing",)
    with pytest.raises(ValidationError, match="declared indication"):
        payload(groups=tuple(bad_groups))

    bad_profile = profile("visual_surface")
    rules = list(bad_profile["rules"])
    rules[1] = {**rules[1], "unit_token": "m^2"}
    bad_profile["rules"] = tuple(rules)
    with pytest.raises(ValidationError, match="unit"):
        payload(acceptance_profile=bad_profile)

    bad_procedure = procedure("penetrant")
    bad_procedure["method_parameters"].pop("developer_basis")
    with pytest.raises(ValidationError, match="method parameters"):
        payload("penetrant", procedure=bad_procedure)
