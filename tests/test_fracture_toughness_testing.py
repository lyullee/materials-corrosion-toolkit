import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fracture_toughness_testing import (
    FractureToughnessCampaignAssessment,
    FractureToughnessCampaignReport,
    fracture_toughness_testing,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def digest(character):
    return character * 64


def specimen(index, value=100.0, uncertainty=4.0, **updates):
    row = {
        "record_id": f"record-{index}",
        "physical_specimen_id": f"specimen-{index}",
        "replicate_group_id": "replicate-group-1",
        "source_group_id": f"source-group-{index}",
        "independence_group_id": f"independence-group-{index}",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "product_form_id": "plate-1",
        "extraction_location_definition": "caller reviewed plate coordinate",
        "notch_orientation_id": "L-T-notch",
        "crack_plane_orientation_id": "L-T-plane",
        "crack_growth_direction_id": "T-direction",
        "geometry": {
            "geometry_id": f"geometry-{index}",
            "specimen_type_descriptor": "caller compact specimen descriptor",
            "width": 50.0,
            "thickness": 25.0,
            "net_thickness": 25.0,
            "initial_notch_length": 20.0,
            "final_crack_length": 25.0,
            "dimension_unit_token": "mm",
            "geometry_measurement_uncertainty": 0.05,
            "geometry_record_digest": digest("a"),
        },
        "test_temperature_K": 293.15,
        "expanded_temperature_uncertainty_K": 0.5,
        "environment_id": "laboratory-air",
        "loading_mode": "opening mode",
        "loading_control_definition": "caller displacement-rate control",
        "loading_rate_value": 1.0,
        "loading_rate_unit_token": "mm/min",
        "expanded_loading_rate_uncertainty": 0.05,
        "fatigue_precrack": {
            "precrack_method_id": "fatigue-precrack-1",
            "cycle_count": 10000,
            "maximum_load_value": 10.0,
            "load_unit_token": "kN",
            "load_ratio": 0.1,
            "frequency_hz": 10.0,
            "precrack_extension": 5.0,
            "extension_unit_token": "mm",
            "precrack_front_definition": "caller measured final crack front",
            "precrack_record_digest": digest("b"),
            "evidence": (EVIDENCE,),
        },
        "toughness_kind": "K",
        "test_method_id": "caller-method-1",
        "test_method_revision": "rev-1",
        "reported_toughness": value,
        "toughness_unit_token": "MPa*sqrt(m)",
        "expanded_toughness_uncertainty": uncertainty,
        "uncertainty_coverage_definition": "caller expanded uncertainty budget",
        "caller_validity_flags": (
            {
                "flag_id": "caller-validity-flag-1",
                "flag_result": "satisfied",
                "flag_definition": "caller-authored validity condition",
                "review_basis": "caller reviewed test record",
                "evidence": (EVIDENCE,),
            },
        ),
        "caller_overall_valid": True,
        "caller_validity_record_id": f"validity-{index}",
        "provider_id": "laboratory-provider",
        "provider_revision": "provider-rev-1",
        "provider_configuration_digest": digest("c"),
        "raw_data_digest": digest(str(index)),
        "result_record_digest": digest("e" if index == 1 else "f"),
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def criterion(metric, direction, accept, reject, unit):
    return {
        "criterion_id": f"criterion-{metric}",
        "metric_id": metric,
        "direction": direction,
        "accept_limit": accept,
        "reject_limit": reject,
        "unit_token": unit,
        "criterion_basis": "caller-authored campaign criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "toughness_kind": "K",
        "test_method_id": "caller-method-1",
        "test_method_revision": "rev-1",
        "toughness_unit_token": "MPa*sqrt(m)",
        "loading_rate_unit_token": "mm/min",
        "minimum_temperature_K": 290.0,
        "maximum_temperature_K": 300.0,
        "minimum_loading_rate": 0.5,
        "maximum_loading_rate": 2.0,
        "criteria": (
            criterion("specimen_count", "minimum", 2, 1, "count"),
            criterion("replicate_group_count", "minimum", 1, 0, "count"),
            criterion("independent_source_group_count", "minimum", 2, 1, "count"),
            criterion("caller_valid_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("minimum_reported_toughness", "minimum", 90, 70, "MPa*sqrt(m)"),
            criterion("maximum_expanded_uncertainty", "maximum", 5, 10, "MPa*sqrt(m)"),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "profile-rev-1",
        "profile_configuration_digest": digest("d"),
        "caller_acceptance_authority": "caller fracture review group",
        "official_standard_validity_rules_embedded": False,
        "toughness_conversion_or_recalculation_claimed": False,
        "design_allowable_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "records": (specimen(1, 100), specimen(2, 105)),
        "caller_profile": profile(),
        "specimen_geometry_orientation_and_extraction_reviewed": True,
        "temperature_loading_rate_and_environment_reviewed": True,
        "notch_crack_and_fatigue_precrack_reviewed": True,
        "method_result_unit_and_uncertainty_reviewed": True,
        "caller_validity_flags_and_basis_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "provider_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return FractureToughnessCampaignAssessment.model_validate(row)


def test_campaign_accepts_only_under_caller_profile_without_recalculation():
    result = fracture_toughness_testing(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["metric_values"]["minimum_reported_toughness"] == 100.0
    assert result.values["official_validity_rules_applied"] is False
    assert result.values["toughness_converted_or_recalculated"] is False
    assert result.values["design_allowable_produced"] is False


def test_caller_review_band_and_reject_are_explainable():
    reviewed = fracture_toughness_testing(payload(records=(specimen(1, 80), specimen(2, 85))))
    assert reviewed.values["campaign_outcome"] == "review"
    finding = next(
        row
        for row in reviewed.values["criterion_findings"]
        if row["metric_id"] == "minimum_reported_toughness"
    )
    assert finding["outcome"] == "review"

    rejected = fracture_toughness_testing(payload(records=(specimen(1, 65), specimen(2, 80))))
    assert rejected.values["campaign_outcome"] == "reject"


def test_caller_invalid_method_unit_or_support_mismatch_is_insufficient():
    invalid_flag = {
        "flag_id": "flag-failed",
        "flag_result": "not_satisfied",
        "flag_definition": "caller condition",
        "review_basis": "caller review",
        "evidence": (EVIDENCE,),
    }
    invalid = specimen(
        2,
        caller_validity_flags=(invalid_flag,),
        caller_overall_valid=False,
        invalid_or_limiting_basis="caller marked test invalid",
    )
    result = fracture_toughness_testing(payload(records=(specimen(1), invalid)))
    assert result.status == "needs_data"
    assert result.values["campaign_outcome"] == "insufficient_evidence"

    for update, diagnostic in (
        ({"test_method_revision": "other"}, "method_identity_mismatch_record_ids"),
        ({"toughness_unit_token": "other"}, "unit_mismatch_record_ids"),
        ({"test_temperature_K": 310.0}, "outside_caller_support_record_ids"),
    ):
        result = fracture_toughness_testing(payload(records=(specimen(1), specimen(2, **update))))
        assert result.status == "needs_data"
        assert result.values["diagnostics"][diagnostic] == ["record-2"]


def test_strict_geometry_validity_identity_and_report_digest_guards():
    bad_geometry = specimen(1)
    bad_geometry["geometry"] = {**bad_geometry["geometry"], "net_thickness": 30.0}
    with pytest.raises(ValueError, match="cannot exceed"):
        payload(records=(bad_geometry, specimen(2)))

    duplicate = specimen(2, physical_specimen_id="specimen-1")
    with pytest.raises(ValueError, match="specimen identities must be unique"):
        payload(records=(specimen(1), duplicate))

    first = fracture_toughness_testing(payload())
    second = fracture_toughness_testing(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    FractureToughnessCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        FractureToughnessCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "inspection.fracture_toughness_testing"
    assert spec.source_ids == ("authored_fracture_toughness_testing_campaign_audit",)
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="test clock")
    spec.context_validator(payload(), context)
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="test clock"),
        )
