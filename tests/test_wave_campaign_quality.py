import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.wave_campaign_quality import (
    WaveCampaignQualityAssessment,
    WaveCampaignQualityReport,
    specifications,
    wave_campaign_quality,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored wave audit"}
DIGESTS = {key: key * 64 for key in "abcdef"}


def check(identifier, sequence, stage, **updates):
    row = {
        "check_id": identifier,
        "sequence_index": sequence,
        "elapsed_time_s": float(sequence),
        "check_stage": stage,
        "reference_source_id": "reference-source-1",
        "reference_source_digest": DIGESTS["a"],
        "channel_id": "channel-1",
        "source_group_id": "source-group-1",
        "independence_group_id": "independence-group-1",
        "timing_error_s": 0.0001,
        "expanded_timing_uncertainty_s": 0.00002,
        "amplitude_metric": 10.0,
        "amplitude_unit_token": "signal-unit",
        "expanded_amplitude_uncertainty": 0.2,
        "noise_metric": 1.0,
        "noise_unit_token": "noise-unit",
        "expanded_noise_uncertainty": 0.1,
        "localization_error_m": 0.02,
        "expanded_localization_uncertainty_m": 0.005,
        "reference_consistency_error": 0.02,
        "expanded_consistency_uncertainty": 0.01,
        "check_method_definition": "caller reference-source consistency check",
        "check_record_digest": DIGESTS["b"],
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def record(identifier, role, encoded_digest, first_sequence, examined=100.0, **updates):
    row = {
        "record_id": identifier,
        "record_role": role,
        "configuration_id": "configuration-1",
        "coupling_state_id": "coupling-state-1",
        "clock_id": "clock-1",
        "source_group_id": f"source-{identifier}",
        "independence_group_id": f"independence-{identifier}",
        "active_channel_ids": ("channel-1",),
        "target_extent": 100.0,
        "examined_extent": examined,
        "extent_unit_token": "m",
        "encoded_data_id": f"data-{identifier}",
        "encoded_data_digest": encoded_digest,
        "encoded_data_format": "caller encoded waveform container",
        "reference_checks": (
            check(f"{identifier}-pre", first_sequence, "pre_acquisition"),
            check(f"{identifier}-post", first_sequence + 1, "post_acquisition"),
        ),
        "record_digest": DIGESTS["c"],
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
        "criterion_basis": "caller-authored wave campaign quality threshold",
    }


def profile(family):
    return {
        "profile_id": f"{family}-profile-1",
        "profile_version": "1.0.0",
        "family": family,
        "required_check_stages": ("pre_acquisition", "post_acquisition"),
        "amplitude_metric_definition": "caller reference response amplitude",
        "amplitude_unit_token": "signal-unit",
        "noise_metric_definition": "caller background noise measure",
        "noise_unit_token": "noise-unit",
        "reference_consistency_metric_definition": "absolute caller reference consistency error",
        "criteria": (
            criterion("record_count", "minimum", 2, 1, "count"),
            criterion("baseline_count", "minimum", 1, 0, "count"),
            criterion("observation_count", "minimum", 1, 0, "count"),
            criterion("coverage_fraction", "minimum", 0.9, 0.7, "1"),
            criterion("channel_coverage_fraction", "minimum", 1, 0.5, "1"),
            criterion("reference_stage_coverage_fraction", "minimum", 1, 0.5, "1"),
            criterion("maximum_absolute_timing_error_s", "maximum", 0.001, 0.01, "s"),
            criterion("minimum_amplitude_metric", "minimum", 8, 5, "signal-unit"),
            criterion("maximum_noise_metric", "maximum", 2, 4, "noise-unit"),
            criterion("maximum_localization_error_m", "maximum", 0.05, 0.1, "m"),
            criterion("maximum_reference_consistency_error", "maximum", 0.05, 0.1, "1"),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": DIGESTS["d"],
        "caller_acceptance_authority": "caller inspection review team",
        "built_in_code_or_standard_limits_used": False,
        "automatic_damage_detection_or_sizing_claimed": False,
        "pod_claimed": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(family="acoustic_emission", **updates):
    kind = "sensor" if family == "acoustic_emission" else "transducer"
    row = {
        "assessment_id": f"{family}-assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "family": family,
        "procedure_id": "procedure-1",
        "procedure_revision": "rev-1",
        "extent_unit_token": "m",
        "acquisition_configuration": {
            "configuration_id": "configuration-1",
            "family": family,
            "array_id": "array-1",
            "elements": (
                {
                    "element_id": "element-1",
                    "channel_id": "channel-1",
                    "element_kind": kind,
                    "physical_position_definition": "reviewed asset coordinate",
                    "calibration_id": "calibration-1",
                    "calibration_digest": DIGESTS["e"],
                    "evidence": (EVIDENCE,),
                },
            ),
            "coupling_method": "caller documented coupling method",
            "coupling_state_id": "coupling-state-1",
            "coupling_record_digest": DIGESTS["f"],
            "clock_id": "clock-1",
            "sampling_rate_hz": 1_000_000,
            "acquisition_configuration_digest": DIGESTS["a"],
            "evidence": (EVIDENCE,),
        },
        "records": (
            record("baseline-1", "baseline", DIGESTS["b"], 0),
            record("observation-1", "observation", DIGESTS["c"], 2),
        ),
        "acceptance_profile": profile(family),
        "procedure_array_and_acquisition_identity_reviewed": True,
        "coupling_and_clock_identity_reviewed": True,
        "calibration_and_reference_source_checks_reviewed": True,
        "baseline_observation_identity_and_digests_reviewed": True,
        "channel_mapping_and_coverage_reviewed": True,
        "timing_amplitude_noise_localization_units_and_uncertainty_reviewed": True,
        "source_and_independence_groups_reviewed": True,
        "caller_acceptance_profile_reviewed": True,
        "record_validity_and_missingness_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return WaveCampaignQualityAssessment.model_validate(row)


def test_both_wave_families_pass_only_caller_profile_without_damage_claims():
    for family in ("acoustic_emission", "guided_waves"):
        result = wave_campaign_quality(payload(family))
        assert result.status == "computed"
        assert result.values["quality_outcome"] == "pass"
        assert result.values["metric_values"]["baseline_count"] == 1
        assert result.values["automatic_damage_detection_or_sizing"] is False
        assert result.values["pod_claimed"] is False
        assert result.values["physical_qualification"] is False


def test_review_and_fail_are_explainable_caller_threshold_outcomes():
    review_records = (
        record("baseline-1", "baseline", DIGESTS["b"], 0, examined=80),
        record("observation-1", "observation", DIGESTS["c"], 2, examined=80),
    )
    reviewed = wave_campaign_quality(payload(records=review_records))
    assert reviewed.values["quality_outcome"] == "review"
    coverage = next(
        row for row in reviewed.values["criterion_findings"] if row["metric_id"] == "coverage_fraction"
    )
    assert coverage["outcome"] == "review"

    noisy_checks = (
        check("observation-1-pre", 2, "pre_acquisition", noise_metric=5),
        check("observation-1-post", 3, "post_acquisition", noise_metric=5),
    )
    failed_records = (
        record("baseline-1", "baseline", DIGESTS["b"], 0),
        record("observation-1", "observation", DIGESTS["c"], 2, reference_checks=noisy_checks),
    )
    failed = wave_campaign_quality(payload(records=failed_records))
    assert failed.values["quality_outcome"] == "fail"


def test_missing_partition_invalid_record_and_exact_units_need_data():
    no_observation = wave_campaign_quality(
        payload(records=(record("baseline-1", "baseline", DIGESTS["b"], 0),))
    )
    assert no_observation.status == "needs_data"
    assert "observation_record_required" in no_observation.values["diagnostics"]["unavailable_evidence"]

    invalid = record(
        "observation-1",
        "observation",
        DIGESTS["c"],
        2,
        record_valid=False,
        invalid_or_missing_basis="review rejected record",
    )
    result = wave_campaign_quality(
        payload(records=(record("baseline-1", "baseline", DIGESTS["b"], 0), invalid))
    )
    assert result.status == "needs_data"

    mismatched_checks = (
        check("observation-1-pre", 2, "pre_acquisition", amplitude_unit_token="other"),
        check("observation-1-post", 3, "post_acquisition"),
    )
    records = (
        record("baseline-1", "baseline", DIGESTS["b"], 0),
        record("observation-1", "observation", DIGESTS["c"], 2, reference_checks=mismatched_checks),
    )
    result = wave_campaign_quality(payload(records=records))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["metric_unit_mismatch_check_ids"]["amplitude"] == [
        "observation-1-pre"
    ]


def test_report_digest_is_deterministic_and_detects_tamper():
    assessment = payload()
    first = wave_campaign_quality(assessment)
    second = wave_campaign_quality(assessment)
    assert first.values["report_digest"] == second.values["report_digest"]
    WaveCampaignQualityReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["quality_outcome"] = "fail"
    with pytest.raises(ValueError, match="digest does not match"):
        WaveCampaignQualityReport.model_validate(tampered)


def test_array_kind_links_and_local_specs_are_strict():
    data = payload("guided_waves").model_dump()
    data["acquisition_configuration"]["elements"][0]["element_kind"] = "sensor"
    with pytest.raises(ValueError, match="must use transducer identity"):
        WaveCampaignQualityAssessment.model_validate(data)

    specs = specifications()
    assert [row.model_id for row in specs] == [
        "inspection.acoustic_emission_campaign_quality",
        "inspection.guided_waves_campaign_quality",
    ]
    assert all(
        row.source_ids == ("authored_wave_reference_baseline_campaign_quality_audit",) for row in specs
    )
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign snapshot")
    specs[0].context_validator(payload(), context)
    with pytest.raises(ValueError, match="matching campaign family"):
        specs[1].context_validator(payload(), context)
