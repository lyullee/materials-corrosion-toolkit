import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.electromagnetic_campaign_quality import (
    ElectromagneticCampaignQualityAssessment,
    ElectromagneticCampaignQualityReport,
    electromagnetic_campaign_quality,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored EM audit"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def check(identifier, sequence, stage, sensitivity, noise=1.0, resolution=0.5, **updates):
    row = {
        "check_id": identifier,
        "sequence_index": sequence,
        "elapsed_time_s": float(sequence),
        "check_stage": stage,
        "reference_feature_id": "feature-1",
        "channel_id": "channel-1",
        "drift_group_id": "drift-1",
        "reported_response_present": True,
        "sensitivity_metric": sensitivity,
        "sensitivity_unit_token": "signal-ratio",
        "expanded_sensitivity_uncertainty": 0.2,
        "noise_metric": noise,
        "noise_unit_token": "signal-unit",
        "expanded_noise_uncertainty": 0.1,
        "resolution_metric": resolution,
        "resolution_unit_token": "mm",
        "expanded_resolution_uncertainty": 0.05,
        "check_method_definition": "caller reference response check",
        "check_record_digest": DIGEST_C,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def criterion(metric, direction, pass_limit, fail_limit, unit):
    return {
        "criterion_id": f"criterion-{metric}",
        "metric_id": metric,
        "direction": direction,
        "pass_limit": pass_limit,
        "fail_limit": fail_limit,
        "unit_token": unit,
        "criterion_basis": "caller-authored electromagnetic quality limit",
    }


def profile(family):
    return {
        "profile_id": f"{family}-profile-1",
        "profile_version": "1.0.0",
        "family": family,
        "required_check_stages": ("pre_scan", "post_scan"),
        "sensitivity_metric_definition": "caller signal ratio",
        "sensitivity_unit_token": "signal-ratio",
        "noise_metric_definition": "caller background noise metric",
        "noise_unit_token": "signal-unit",
        "resolution_metric_definition": "caller spatial resolution metric",
        "resolution_unit_token": "mm",
        "criteria": (
            criterion("scan_count", "minimum", 1.0, 0.0, "count"),
            criterion("coverage_fraction", "minimum", 0.9, 0.7, "1"),
            criterion("channel_coverage_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("reference_feature_stage_coverage_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("response_present_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("minimum_sensitivity_metric", "minimum", 8.0, 5.0, "signal-ratio"),
            criterion("maximum_noise_metric", "maximum", 2.0, 4.0, "signal-unit"),
            criterion("maximum_resolution_metric", "maximum", 0.6, 1.0, "mm"),
            criterion("maximum_drift_relative_change", "maximum", 0.05, 0.1, "1"),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": DIGEST_D,
        "caller_acceptance_authority": "caller NDE review group",
        "built_in_code_or_standard_limits_used": False,
        "automatic_sizing_or_acceptance_claimed": False,
        "pod_claimed": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def scan(examined=90.0, checks=None, **updates):
    row = {
        "scan_id": "scan-1",
        "procedure_id": "procedure-1",
        "procedure_revision": "rev-1",
        "configuration_id": "configuration-1",
        "reference_standard_id": "standard-1",
        "active_channel_ids": ("channel-1",),
        "scan_speed_m_s": 0.5,
        "expanded_scan_speed_uncertainty_m_s": 0.01,
        "speed_control_basis": "caller encoder speed control",
        "target_extent": 100.0,
        "examined_extent": examined,
        "extent_unit_token": "mm",
        "encoded_data_id": "encoded-1",
        "encoded_data_digest": DIGEST_B,
        "encoded_data_format": "caller encoded signal format",
        "checks": checks
        or (
            check("check-pre", 0, "pre_scan", 10.0),
            check("check-post", 1, "post_scan", 9.8),
        ),
        "scan_record_digest": DIGEST_C,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def payload(family="eddy_current", **updates):
    row = {
        "assessment_id": f"{family}-campaign-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "family": family,
        "procedure_id": "procedure-1",
        "procedure_revision": "rev-1",
        "extent_unit_token": "mm",
        "declared_channel_ids": ("channel-1",),
        "acquisition_configuration": {
            "configuration_id": "configuration-1",
            "family": family,
            "probe_or_sensor_array_id": "probe-1" if family == "eddy_current" else "sensor-array-1",
            "magnetizer_id": None if family == "eddy_current" else "magnetizer-1",
            "excitation_id": "frequency-1" if family == "eddy_current" else "magnetization-1",
            "excitation_value": 1000.0,
            "excitation_unit_token": "Hz" if family == "eddy_current" else "A",
            "nominal_lift_off_m": 0.001,
            "expanded_lift_off_uncertainty_m": 0.0001,
            "lift_off_control_basis": "caller lift-off control record",
            "configuration_digest": DIGEST_A,
            "evidence": (EVIDENCE,),
        },
        "reference_standard": {
            "reference_standard_id": "standard-1",
            "material_condition_id": "material-condition-1",
            "standard_configuration_digest": DIGEST_A,
            "features": (
                {
                    "feature_id": "feature-1",
                    "feature_type_descriptor": "caller reference feature",
                    "physical_location_definition": "reviewed standard coordinate",
                    "nominal_dimension": 1.0,
                    "dimension_unit_token": "mm",
                    "expanded_dimension_uncertainty": 0.05,
                    "physical_feature_identity_reviewed": True,
                    "feature_record_digest": DIGEST_B,
                    "evidence": (EVIDENCE,),
                },
            ),
            "evidence": (EVIDENCE,),
        },
        "scans": (scan(),),
        "acceptance_profile": profile(family),
        "procedure_probe_sensor_magnetizer_and_excitation_reviewed": True,
        "lift_off_speed_and_uncertainty_reviewed": True,
        "reference_standard_features_reviewed": True,
        "encoded_scan_identity_and_digests_reviewed": True,
        "channel_mapping_and_coverage_reviewed": True,
        "pre_in_post_checks_and_drift_groups_reviewed": True,
        "sensitivity_noise_resolution_units_and_uncertainty_reviewed": True,
        "caller_acceptance_profile_reviewed": True,
        "record_validity_and_missingness_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ElectromagneticCampaignQualityAssessment.model_validate(row)


def test_eddy_current_and_mfl_pass_only_caller_profile_without_qualification():
    for family in ("eddy_current", "flux_leakage"):
        result = electromagnetic_campaign_quality(payload(family))
        assert result.status == "computed"
        assert result.values["quality_outcome"] == "pass"
        assert result.values["metric_values"]["maximum_drift_relative_change"] == pytest.approx(0.02)
        assert result.values["automatic_sizing_or_acceptance"] is False
        assert result.values["pod_claimed"] is False
        assert result.values["physical_qualification"] is False


def test_caller_review_band_and_fail_limits_are_explainable():
    review = electromagnetic_campaign_quality(payload(scans=(scan(examined=80.0),)))
    assert review.values["quality_outcome"] == "review"
    coverage = [
        row for row in review.values["criterion_findings"] if row["metric_id"] == "coverage_fraction"
    ][0]
    assert coverage["outcome"] == "review"

    noisy = (
        check("check-pre", 0, "pre_scan", 10.0, noise=5.0),
        check("check-post", 1, "post_scan", 9.8, noise=5.0),
    )
    failed = electromagnetic_campaign_quality(payload(scans=(scan(checks=noisy),)))
    assert failed.values["quality_outcome"] == "fail"
    noise = [
        row for row in failed.values["criterion_findings"] if row["metric_id"] == "maximum_noise_metric"
    ][0]
    assert noise["outcome"] == "fail"


def test_invalid_records_unit_mismatch_or_missing_drift_are_insufficient():
    invalid = scan(record_valid=False, invalid_or_missing_basis="encoded record invalid")
    result = electromagnetic_campaign_quality(payload(scans=(invalid,)))
    assert result.status == "needs_data"
    assert result.values["quality_outcome"] == "insufficient_evidence"

    unit_conflict = (
        check("check-pre", 0, "pre_scan", 10.0, noise_unit_token="other"),
        check("check-post", 1, "post_scan", 9.8),
    )
    result = electromagnetic_campaign_quality(payload(scans=(scan(checks=unit_conflict),)))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["metric_unit_mismatch_check_ids"]["noise"] == ["check-pre"]

    no_drift = (
        check("check-pre", 0, "pre_scan", 10.0, drift_group_id="drift-a"),
        check("check-post", 1, "post_scan", 9.8, drift_group_id="drift-b"),
    )
    result = electromagnetic_campaign_quality(payload(scans=(scan(checks=no_drift),)))
    assert result.status == "needs_data"
    assert "no_usable_drift_group" in result.values["diagnostics"]["unavailable_drift_groups"]


def test_report_digest_is_deterministic_and_detects_tamper():
    assessment = payload()
    first = electromagnetic_campaign_quality(assessment)
    second = electromagnetic_campaign_quality(assessment)
    assert first.values["report_digest"] == second.values["report_digest"]
    ElectromagneticCampaignQualityReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["metric_values"] = {**tampered["metric_values"], "coverage_fraction": 1.0}
    with pytest.raises(ValueError, match="digest does not match"):
        ElectromagneticCampaignQualityReport.model_validate(tampered)


def test_mfl_requires_magnetizer_and_local_specs_enforce_family():
    data = payload("flux_leakage").model_dump()
    data["acquisition_configuration"]["magnetizer_id"] = None
    with pytest.raises(ValueError, match="require magnetizer identity"):
        ElectromagneticCampaignQualityAssessment.model_validate(data)

    specs = specifications()
    assert [row.model_id for row in specs] == [
        "inspection.eddy_current_campaign_quality",
        "inspection.flux_leakage_campaign_quality",
    ]
    assert all(
        row.source_ids == ("authored_electromagnetic_reference_campaign_quality_audit",) for row in specs
    )
    assessment = payload()
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign snapshot")
    specs[0].context_validator(assessment, context)
    with pytest.raises(ValueError, match="matching campaign family"):
        specs[1].context_validator(assessment, context)
