import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.weld_hardness_mapping_campaign import (
    WeldHardnessMappingCampaignAssessment,
    WeldHardnessMappingCampaignReport,
    specifications,
    weld_hardness_mapping_campaign,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored weld map"}


def digest(character):
    return character * 64


def point(index, region, hardness, **updates):
    row = {
        "point_id": f"point-{index}",
        "traverse_id": "traverse-1",
        "coordinate_frame_id": "frame-1",
        "coordinate_x": float(index),
        "coordinate_y": 1.0,
        "coordinate_z": 0.0,
        "coordinate_unit_token": "mm",
        "caller_assigned_region": region,
        "user_defined_region_description": None,
        "region_assignment_basis": "caller-reviewed macrograph coordinate assignment",
        "hardness_value": hardness,
        "hardness_unit_token": "HV10",
        "expanded_hardness_uncertainty": 5.0,
        "uncertainty_basis": "caller uncertainty budget",
        "provider_id": "laboratory-provider",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("a"),
        "raw_reading_digest": digest("0123456789abcdef"[index]),
        "point_record_digest": digest("0123456789abcdef"[index + 8]),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def points(haz=320.0, unit="HV10"):
    return (
        point(0, "base_material", 220.0, hardness_unit_token=unit),
        point(1, "haz", haz, hardness_unit_token=unit),
        point(2, "fusion_boundary", 330.0, hardness_unit_token=unit),
        point(3, "weld_metal", 300.0, hardness_unit_token=unit),
    )


def traverse(rows=None, **updates):
    row = {
        "traverse_id": "traverse-1",
        "coordinate_frame_id": "frame-1",
        "orientation_definition": "caller transverse line at reviewed depth",
        "nominal_offset_or_depth": 1.0,
        "coordinate_unit_token": "mm",
        "replicate_group_id": "replicate-group-1",
        "source_group_id": "source-group-1",
        "independence_group_id": "independence-group-1",
        "points": rows or points(),
        "traverse_record_digest": digest("c"),
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def criterion(region, accept, reject):
    return {
        "criterion_id": f"criterion-{region}",
        "region": region,
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": accept,
        "reject_limit": reject,
        "hardness_unit_token": "HV10",
        "criterion_basis": "caller-authored regional hardness criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_regions": ("base_material", "haz", "fusion_boundary", "weld_metal"),
        "minimum_traverse_count": 1,
        "minimum_independent_source_group_count": 1,
        "required_configuration_id": "configuration-1",
        "required_method_id": "method-1",
        "required_method_revision": "rev-1",
        "required_hardness_scale_id": "HV10",
        "required_hardness_unit_token": "HV10",
        "required_test_load_value": 10.0,
        "required_test_load_unit_token": "kgf",
        "required_dwell_time_s": 10.0,
        "required_indenter_id": "indenter-1",
        "criteria": (
            criterion("base_material", 250, 300),
            criterion("haz", 350, 400),
            criterion("fusion_boundary", 350, 400),
            criterion("weld_metal", 350, 400),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("d"),
        "caller_acceptance_authority": "caller welding review group",
        "scale_conversion_used": False,
        "strength_inference_claimed": False,
        "built_in_code_or_standard_limits_used": False,
        "automatic_haz_classification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "subject": {
            "weld_id": "weld-1",
            "joint_id": "joint-1",
            "joint_configuration_id": "joint-configuration-1",
            "wps_id": "wps-1",
            "wps_revision": "rev-1",
            "production_heat_id": "production-heat-1",
            "consumable_id": "consumable-1",
            "consumable_lot_id": "consumable-lot-1",
            "base_material_a_id": "base-a",
            "base_material_a_heat_id": "base-a-heat",
            "base_material_b_id": "base-b",
            "base_material_b_heat_id": "base-b-heat",
            "weld_metal_material_id": "weld-metal-1",
            "coordinate_frame_id": "frame-1",
            "cross_section_id": "cross-section-1",
            "cross_section_record_digest": digest("e"),
            "subject_configuration_digest": digest("f"),
            "evidence": (EVIDENCE,),
        },
        "configuration": {
            "configuration_id": "configuration-1",
            "method_id": "method-1",
            "method_revision": "rev-1",
            "hardness_scale_id": "HV10",
            "hardness_unit_token": "HV10",
            "test_load_value": 10.0,
            "test_load_unit_token": "kgf",
            "dwell_time_s": 10.0,
            "indenter_id": "indenter-1",
            "instrument_id": "instrument-1",
            "reference_calibration_id": "calibration-1",
            "reference_calibration_provider_id": "calibration-provider",
            "reference_calibration_valid": True,
            "invalid_calibration_basis": None,
            "reference_calibration_digest": digest("a"),
            "configuration_digest": digest("b"),
            "evidence": (EVIDENCE,),
        },
        "traverses": (traverse(),),
        "caller_profile": profile(),
        "weld_joint_wps_heat_consumable_material_identity_reviewed": True,
        "coordinate_frame_traverse_and_orientation_reviewed": True,
        "caller_region_assignment_and_basis_reviewed": True,
        "method_scale_load_dwell_indenter_and_calibration_reviewed": True,
        "point_coordinates_readings_units_and_uncertainty_reviewed": True,
        "replicate_source_and_independence_claims_reviewed": True,
        "provider_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return WeldHardnessMappingCampaignAssessment.model_validate(row)


def test_campaign_accepts_caller_regions_without_conversion_or_inference():
    result = weld_hardness_mapping_campaign(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["region_metric_values"]["haz"] == 320.0
    assert result.values["hardness_scale_converted"] is False
    assert result.values["strength_inferred"] is False
    assert result.values["automatic_haz_classification"] is False
    assert result.values["specification_acceptance_or_qualification"] is False


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = weld_hardness_mapping_campaign(payload(traverses=(traverse(points(375)),)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = weld_hardness_mapping_campaign(payload(traverses=(traverse(points(425)),)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_region_invalid_calibration_and_scale_unit_mismatch_are_insufficient():
    no_haz = tuple(row for row in points() if row["caller_assigned_region"] != "haz")
    result = weld_hardness_mapping_campaign(payload(traverses=(traverse(no_haz),)))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["missing_required_regions"] == ["haz"]

    data = payload().model_dump()
    data["configuration"]["reference_calibration_valid"] = False
    data["configuration"]["invalid_calibration_basis"] = "caller rejected calibration"
    result = weld_hardness_mapping_campaign(WeldHardnessMappingCampaignAssessment.model_validate(data))
    assert result.status == "needs_data"

    result = weld_hardness_mapping_campaign(payload(traverses=(traverse(points(unit="HV5")),)))
    assert result.status == "needs_data"
    assert len(result.values["diagnostics"]["unit_mismatch_point_ids"]) == 4


def test_frame_region_contract_and_report_digest_are_strict():
    bad_points = list(points())
    bad_points[0] = {**bad_points[0], "coordinate_frame_id": "other-frame"}
    with pytest.raises(ValueError, match="traverse coordinate frame"):
        payload(traverses=(traverse(tuple(bad_points)),))

    user_region = point(0, "user_defined", 220.0)
    with pytest.raises(ValueError, match="require a description"):
        payload(traverses=(traverse((user_region, *points()[1:])),))

    first = weld_hardness_mapping_campaign(payload())
    second = weld_hardness_mapping_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    WeldHardnessMappingCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        WeldHardnessMappingCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "welding.hardness_mapping"
    assert spec.source_ids == ("authored_weld_hardness_mapping_campaign_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="mapping clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="mapping clock")
        )
