import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.leak_campaign_quality import (
    LeakTestCampaignQualityAssessment,
    leak_test_campaign_quality,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored campaign test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def reference_point(identifier, sequence, time, response, **updates):
    row = {
        "point_id": identifier,
        "sequence_index": sequence,
        "elapsed_time_s": time,
        "state_id": "state-1",
        "physical_reference_id": "reference-1",
        "reference_level_id": "level-1",
        "reference_leak_rate_mol_s": 1e-9,
        "expanded_reference_leak_uncertainty_mol_s": 1e-11,
        "response_value": response,
        "expanded_response_uncertainty": 0.5,
        "response_unit_token": "instrument-count",
        "repeatability_group_id": "repeat-1",
        "drift_group_id": "drift-1",
        "source_group_id": "reference-source-1",
        "independence_group_id": "reference-independence-1",
        "observation_record_digest": DIGEST_B,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def background(identifier, sequence, response, **updates):
    row = {
        "observation_id": identifier,
        "observation_kind": "background",
        "sequence_index": sequence,
        "elapsed_time_s": float(sequence),
        "state_id": "state-1",
        "response_value": response,
        "expanded_response_uncertainty": 0.1,
        "response_unit_token": "instrument-count",
        "source_group_id": "background-source-1",
        "observation_record_digest": DIGEST_C,
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
        "criterion_basis": "caller-authored campaign quality boundary",
    }


def acceptance_profile(family, capability_mode="response_uncertainty_profile"):
    detection = (
        criterion("maximum_relative_response_uncertainty", "maximum", 0.2, 0.4, "1")
        if capability_mode == "response_uncertainty_profile"
        else criterion("detection_threshold_response", "maximum", 2.0, 4.0, "instrument-count")
    )
    return {
        "profile_id": f"{family}-profile-1",
        "profile_version": "1.0.0",
        "campaign_family": family,
        "criteria": (
            criterion("reference_point_count", "minimum", 2.0, 1.0, "count"),
            criterion("distinct_reference_level_count", "minimum", 1.0, 0.0, "count"),
            criterion("blank_background_count", "minimum", 2.0, 1.0, "count"),
            criterion(
                "mean_absolute_blank_background_response",
                "maximum",
                2.0,
                3.0,
                "instrument-count",
            ),
            criterion("maximum_repeatability_relative_standard_deviation", "maximum", 0.05, 0.1, "1"),
            criterion("maximum_drift_relative_change", "maximum", 0.05, 0.1, "1"),
            detection,
        ),
        "profile_provider_id": "caller-profile-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": DIGEST_D,
        "caller_acceptance_authority": "caller engineering review group",
        "built_in_standard_criteria_used": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(family="leak_rate", capability_mode="response_uncertainty_profile", **updates):
    capability = {
        "evidence_id": "capability-1",
        "mode": capability_mode,
        "detection_threshold_response": 1.0 if capability_mode == "detection_threshold" else None,
        "response_unit_token": "instrument-count" if capability_mode == "detection_threshold" else None,
        "uncertainty_profile_id": (
            "uncertainty-profile-1" if capability_mode == "response_uncertainty_profile" else None
        ),
        "uncertainty_profile_digest": (
            DIGEST_D if capability_mode == "response_uncertainty_profile" else None
        ),
        "capability_definition": "caller-reviewed response capability evidence",
        "capability_record_digest": DIGEST_C,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row = {
        "assessment_id": f"{family}-campaign-audit-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "campaign_family": family,
        "method_id": "method-1",
        "instrument_id": "instrument-1",
        "instrument_configuration_id": "instrument-config-1",
        "instrument_configuration_digest": DIGEST_A,
        "test_gas_id": "gas-1",
        "response_definition": "caller instrument response",
        "response_unit_token": "instrument-count",
        "clock_id": "clock-1",
        "states": (
            {
                "state_id": "state-1",
                "temperature_K": 300.0,
                "expanded_temperature_uncertainty_K": 0.5,
                "internal_pressure_Pa": 1e5,
                "external_pressure_Pa": 1e3,
                "expanded_pressure_uncertainty_Pa": 100.0,
                "pressure_basis": "caller absolute pressure basis",
                "thermal_and_phase_state_descriptor": "caller stable test state",
                "state_record_digest": DIGEST_A,
                "record_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            },
        ),
        "reference_points": (
            reference_point("reference-point-1", 0, 0.0, 100.0),
            reference_point("reference-point-2", 3, 10.0, 102.0),
        ),
        "blank_background_observations": (
            background("background-1", 1, 1.0),
            background("background-2", 2, 1.5),
        ),
        "detection_capability": capability,
        "acceptance_profile": acceptance_profile(family, capability_mode),
        "campaign_method_instrument_and_gas_reviewed": True,
        "temperature_pressure_and_state_identity_reviewed": True,
        "reference_leak_traceability_and_uncertainty_reviewed": True,
        "blank_and_background_records_reviewed": True,
        "repeatability_and_drift_groups_reviewed": True,
        "detection_threshold_or_uncertainty_profile_reviewed": True,
        "caller_acceptance_profile_reviewed": True,
        "record_digests_and_missingness_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return LeakTestCampaignQualityAssessment.model_validate(row)


def test_all_three_campaign_families_pass_caller_profile_without_qualification():
    for family in ("leak_rate", "vacuum_testing", "cryogenic_leak_testing"):
        result = leak_test_campaign_quality(payload(family))
        assert result.status == "computed"
        assert result.values["quality_outcome"] == "pass"
        assert result.values["physical_qualification"] is False
        assert result.values["caller_acceptance_profile_only"] is True
        assert result.values["metric_values"]["maximum_drift_relative_change"] == pytest.approx(0.02)


def test_caller_review_band_and_fail_limit_produce_explicit_outcomes():
    review = payload(
        blank_background_observations=(
            background("background-1", 1, 2.0),
            background("background-2", 2, 3.0),
        )
    )
    result = leak_test_campaign_quality(review)
    assert result.values["quality_outcome"] == "review"
    blank = [
        row
        for row in result.values["criterion_findings"]
        if row["metric_id"] == "mean_absolute_blank_background_response"
    ][0]
    assert blank["outcome"] == "review"

    fail = payload(
        reference_points=(
            reference_point("reference-point-1", 0, 0.0, 100.0),
            reference_point("reference-point-2", 3, 10.0, 120.0),
        )
    )
    assert leak_test_campaign_quality(fail).values["quality_outcome"] == "fail"


def test_missing_replicates_invalid_records_or_unreviewed_evidence_are_insufficient():
    one_reference = payload(reference_points=(reference_point("reference-point-1", 0, 0.0, 100.0),))
    result = leak_test_campaign_quality(one_reference)
    assert result.status == "needs_data"
    assert result.values["quality_outcome"] == "insufficient_evidence"
    assert "maximum_drift_relative_change" in result.values["missing_metric_ids"]

    state = (
        payload()
        .states[0]
        .model_copy(update={"record_valid": False, "invalid_or_missing_basis": "state acquisition invalid"})
    )
    assert leak_test_campaign_quality(payload(states=(state,))).status == "needs_data"
    assert leak_test_campaign_quality(payload(blank_and_background_records_reviewed=False)).status == (
        "needs_data"
    )


def test_detection_threshold_mode_and_exact_units_are_supported_without_inversion():
    result = leak_test_campaign_quality(payload("vacuum_testing", "detection_threshold"))
    assert result.status == "computed"
    assert result.values["metric_values"]["detection_threshold_response"] == pytest.approx(1.0)
    assert "maximum_relative_response_uncertainty" not in result.values["metric_values"]

    data = payload("vacuum_testing", "detection_threshold").model_dump()
    data["detection_capability"]["response_unit_token"] = "different-unit"
    with pytest.raises(ValueError, match="units must match exactly"):
        LeakTestCampaignQualityAssessment.model_validate(data)


def test_report_digest_is_deterministic_and_local_specs_enforce_family():
    assessment = payload()
    first = leak_test_campaign_quality(assessment)
    second = leak_test_campaign_quality(assessment)
    assert first.values["input_digest"] == second.values["input_digest"]
    assert first.values["report_digest"] == second.values["report_digest"]
    specs = specifications()
    assert [row.model_id for row in specs] == [
        "inspection.leak_rate_campaign_quality",
        "inspection.vacuum_testing_campaign_quality",
        "inspection.cryogenic_leak_testing_campaign_quality",
    ]
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign clock")
    specs[0].context_validator(assessment, context)
    with pytest.raises(ValueError, match="matching campaign family"):
        specs[1].context_validator(assessment, context)
