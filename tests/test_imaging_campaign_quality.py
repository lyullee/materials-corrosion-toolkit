import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.imaging_campaign_quality import (
    ImagingCampaignQualityAssessment,
    ImagingCampaignQualityReport,
    imaging_campaign_quality,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored imaging audit"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def verification(identifier, stage, sensitivity=10.0, resolution=0.5, present=True, **updates):
    row = {
        "verification_id": identifier,
        "reference_feature_id": "feature-1",
        "check_stage": stage,
        "reported_response_present": present,
        "sensitivity_metric": sensitivity,
        "sensitivity_unit_token": "response-ratio",
        "expanded_sensitivity_uncertainty": 0.2,
        "resolution_metric": resolution,
        "resolution_unit_token": "mm",
        "expanded_resolution_uncertainty": 0.05,
        "verification_method_definition": "caller reference response measurement",
        "verification_record_digest": DIGEST_C,
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
        "criterion_basis": "caller-authored campaign quality limit",
    }


def profile(family):
    return {
        "profile_id": f"{family}-profile-1",
        "profile_version": "1.0.0",
        "imaging_family": family,
        "required_check_stages": ("pre_acquisition", "post_acquisition"),
        "sensitivity_metric_definition": "caller response ratio",
        "sensitivity_unit_token": "response-ratio",
        "resolution_metric_definition": "caller spatial resolution metric",
        "resolution_unit_token": "mm",
        "criteria": (
            criterion("acquisition_count", "minimum", 1.0, 0.0, "count"),
            criterion("coverage_fraction", "minimum", 0.9, 0.7, "1"),
            criterion("reference_feature_check_coverage_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("required_stage_coverage_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("response_present_fraction", "minimum", 1.0, 0.5, "1"),
            criterion("minimum_sensitivity_metric", "minimum", 8.0, 5.0, "response-ratio"),
            criterion("maximum_resolution_metric", "maximum", 0.6, 1.0, "mm"),
        ),
        "profile_provider_id": "caller-profile-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": DIGEST_D,
        "caller_acceptance_authority": "caller NDE review group",
        "built_in_code_or_standard_limits_used": False,
        "flaw_acceptance_claimed": False,
        "pod_claimed": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def acquisition(examined=90.0, verifications=None, **updates):
    row = {
        "acquisition_id": "acquisition-1",
        "procedure_id": "procedure-1",
        "procedure_revision": "rev-1",
        "acquisition_configuration_id": "config-1",
        "acquisition_configuration_digest": DIGEST_A,
        "acquisition_device_id": "device-1",
        "reference_standard_id": "standard-1",
        "target_extent": 100.0,
        "examined_extent": examined,
        "extent_unit_token": "mm",
        "encoded_data_id": "encoded-1",
        "encoded_data_digest": DIGEST_B,
        "encoded_data_format": "caller encoded format",
        "verifications": verifications
        or (
            verification("verification-pre", "pre_acquisition"),
            verification("verification-post", "post_acquisition"),
        ),
        "acquisition_record_digest": DIGEST_C,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def payload(family="radiography", **updates):
    row = {
        "assessment_id": f"{family}-campaign-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "imaging_family": family,
        "procedure_id": "procedure-1",
        "procedure_revision": "rev-1",
        "extent_unit_token": "mm",
        "reference_standard": {
            "reference_standard_id": "standard-1",
            "material_and_product_form_id": "standard-material-1",
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
        "acquisitions": (acquisition(),),
        "acceptance_profile": profile(family),
        "procedure_and_acquisition_identities_reviewed": True,
        "reference_standard_features_and_uncertainty_reviewed": True,
        "calibration_and_verification_checks_reviewed": True,
        "coverage_and_extent_units_reviewed": True,
        "encoded_data_identity_and_digests_reviewed": True,
        "sensitivity_resolution_metrics_units_and_uncertainty_reviewed": True,
        "caller_acceptance_profile_reviewed": True,
        "record_validity_and_missingness_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ImagingCampaignQualityAssessment.model_validate(row)


def test_radiography_and_phased_array_pass_only_caller_campaign_profile():
    for family in ("radiography", "phased_array"):
        result = imaging_campaign_quality(payload(family))
        assert result.status == "computed"
        assert result.values["quality_outcome"] == "pass"
        assert result.values["metric_values"]["coverage_fraction"] == pytest.approx(0.9)
        assert result.values["automatic_flaw_acceptance"] is False
        assert result.values["pod_claimed"] is False
        assert result.values["physical_qualification"] is False
        assert result.values["diagnostics"]["encoded_data_digests"] == [DIGEST_B]


def test_caller_review_band_and_fail_limit_are_explainable():
    review = imaging_campaign_quality(payload(acquisitions=(acquisition(examined=80.0),)))
    assert review.values["quality_outcome"] == "review"
    coverage = [
        row for row in review.values["criterion_findings"] if row["metric_id"] == "coverage_fraction"
    ][0]
    assert coverage["outcome"] == "review"

    failed_checks = (
        verification("verification-pre", "pre_acquisition", present=False),
        verification("verification-post", "post_acquisition", present=False),
    )
    fail = imaging_campaign_quality(payload(acquisitions=(acquisition(verifications=failed_checks),)))
    assert fail.values["quality_outcome"] == "fail"
    response = [
        row for row in fail.values["criterion_findings"] if row["metric_id"] == "response_present_fraction"
    ][0]
    assert response["outcome"] == "fail"


def test_invalid_records_missing_reviews_or_unit_conflicts_are_insufficient():
    invalid = acquisition(record_valid=False, invalid_or_missing_basis="encoded acquisition invalid")
    result = imaging_campaign_quality(payload(acquisitions=(invalid,)))
    assert result.status == "needs_data"
    assert result.values["quality_outcome"] == "insufficient_evidence"
    assert result.values["diagnostics"]["invalid_acquisition_ids"] == ["acquisition-1"]

    assert imaging_campaign_quality(payload(encoded_data_identity_and_digests_reviewed=False)).status == (
        "needs_data"
    )
    unit_conflict = (
        verification("verification-pre", "pre_acquisition", sensitivity_unit_token="other"),
        verification("verification-post", "post_acquisition"),
    )
    result = imaging_campaign_quality(payload(acquisitions=(acquisition(verifications=unit_conflict),)))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["sensitivity_unit_mismatch_verification_ids"] == ["verification-pre"]


def test_report_digest_detects_tamper_and_is_deterministic():
    assessment = payload()
    first = imaging_campaign_quality(assessment)
    second = imaging_campaign_quality(assessment)
    assert first.values["report_digest"] == second.values["report_digest"]
    ImagingCampaignQualityReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["metric_values"] = {**tampered["metric_values"], "coverage_fraction": 1.0}
    with pytest.raises(ValueError, match="digest does not match"):
        ImagingCampaignQualityReport.model_validate(tampered)


def test_local_specs_enforce_family_and_preserve_source_id():
    specs = specifications()
    assert [row.model_id for row in specs] == [
        "inspection.radiography_campaign_quality",
        "inspection.phased_array_campaign_quality",
    ]
    assert all(row.source_ids == ("authored_imaging_reference_campaign_quality_audit",) for row in specs)
    assessment = payload()
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign snapshot")
    specs[0].context_validator(assessment, context)
    with pytest.raises(ValueError, match="matching imaging family"):
        specs[1].context_validator(assessment, context)
