import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.microbial_corrosion import (
    MicrobialCampaign,
    microbial_campaign_summary,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-microbial-record",
    "origin": "synthetic",
    "citation": "authored microbial campaign test record",
}


def inputs(**updates):
    payload = {
        "campaign_id": "mic-campaign-001",
        "asset_id": "water-system-001",
        "location_id": "low-point-a",
        "site_id": "site-a",
        "clock_id": "campaign-elapsed-clock",
        "samples": [
            {
                "sample_id": "sample-1",
                "sampling_location_id": "inlet",
                "sample_time_s": 0.0,
                "sample_matrix": "water",
                "collection_method_id": "caller-method",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "assays": [
            {
                "assay_id": "assay-quantified",
                "sample_id": "sample-1",
                "target_id": "target-a",
                "method_id": "method-a",
                "result_qualifier": "quantified",
                "reported_value": 120.0,
                "unit": "copies/mL",
                "detection_limit": 10.0,
                "caller_indicator_id": "indicator-a",
                "record_valid": True,
                "evidence": [EVIDENCE],
            },
            {
                "assay_id": "assay-censored",
                "sample_id": "sample-1",
                "target_id": "target-b",
                "method_id": "method-b",
                "result_qualifier": "below_detection",
                "reported_value": None,
                "unit": "CFU/mL",
                "detection_limit": 5.0,
                "caller_indicator_id": "indicator-b",
                "record_valid": True,
                "evidence": [EVIDENCE],
            },
        ],
        "water_context": [
            {
                "observation_id": "context-ph",
                "sample_id": "sample-1",
                "parameter_id": "pH",
                "reported_value": 7.1,
                "unit": "1",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "biofilm_deposit_observations": [
            {
                "observation_id": "deposit-1",
                "sample_id": "sample-1",
                "observation_method_id": "caller-visual-method",
                "reported_description": "caller reported adherent deposit",
                "metric_id": "reported_covered_area",
                "reported_value": 0.01,
                "unit": "m^2",
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "caller_indicators": [
            {
                "indicator_id": "indicator-a",
                "target_id": "target-a",
                "method_id": "method-a",
                "unit": "copies/mL",
                "maximum_value": 100.0,
                "definition_basis": "caller monitoring plan",
                "caller_disposition_id_if_outside": "review-target-a",
            },
            {
                "indicator_id": "indicator-b",
                "target_id": "target-b",
                "method_id": "method-b",
                "unit": "CFU/mL",
                "maximum_value": 20.0,
                "definition_basis": "caller monitoring plan",
                "caller_disposition_id_if_outside": "review-target-b",
            },
        ],
        "required_sampling_location_ids": ["inlet"],
        "required_assay_target_ids": ["target-a", "target-b"],
        "required_water_context_parameter_ids": ["pH"],
        "biofilm_deposit_observation_required": True,
        "campaign_site_and_clock_reviewed": True,
        "sampling_plan_and_coverage_reviewed": True,
        "sample_validity_reviewed": True,
        "assay_method_units_and_detection_limits_reviewed": True,
        "water_context_reviewed": True,
        "biofilm_deposit_mapping_reviewed": True,
        "caller_indicator_definitions_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_complete_campaign_keeps_quantified_and_censored_results_separate():
    result = microbial_campaign_summary(MicrobialCampaign.model_validate(inputs()))
    assert result.status == "computed"
    assert result.values["below_detection_assay_ids"] == ["assay-censored"]
    comparison = result.values["quantified_indicator_comparisons"][0]
    assert comparison["above_declared_maximum"] is True
    assert comparison["caller_disposition_id_if_outside"] == "review-target-a"
    censored = result.values["censored_indicator_records"][0]
    assert censored["detection_limit"] == pytest.approx(5.0)
    assert censored["comparison_status"] == "censored_below_detection"


def test_missing_coverage_and_invalid_records_remain_needs_data():
    samples = list(inputs()["samples"])
    samples[0] = {
        **samples[0],
        "record_valid": False,
        "invalid_basis": "sample custody interrupted",
    }
    result = microbial_campaign_summary(
        MicrobialCampaign.model_validate(
            inputs(samples=samples, required_sampling_location_ids=["inlet", "outlet"])
        )
    )
    assert result.status == "needs_data"
    assert result.values["invalid_sample_ids"] == ["sample-1"]
    assert result.values["missing_required_sampling_location_ids"] == ["inlet", "outlet"]


def test_unmatched_indicator_and_unit_mismatch_are_preserved():
    assays = list(inputs()["assays"])
    assays[0] = {**assays[0], "caller_indicator_id": None}
    assays[1] = {**assays[1], "unit": "cells/mL"}
    result = microbial_campaign_summary(MicrobialCampaign.model_validate(inputs(assays=assays)))
    assert result.status == "needs_data"
    assert result.values["unmatched_indicator_assay_ids"] == ["assay-quantified"]
    assert result.values["indicator_unit_mismatch_assay_ids"] == ["assay-censored"]


def test_contract_rejects_zero_substitution_for_censored_result_and_orphan_context():
    assays = list(inputs()["assays"])
    assays[1] = {**assays[1], "reported_value": 0.0}
    with pytest.raises(ValueError, match="preserve censoring"):
        MicrobialCampaign.model_validate(inputs(assays=assays))

    context = list(inputs()["water_context"])
    context[0] = {**context[0], "sample_id": "not-declared"}
    with pytest.raises(ValueError, match="declared samples"):
        MicrobialCampaign.model_validate(inputs(water_context=context))


def test_model_spec_enforces_context_identity():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    request = MicrobialCampaign.model_validate(inputs())
    result = registry.run(
        "degradation.microbial_campaign_summary",
        request,
        RunContext(
            asset_id="water-system-001",
            location_id="low-point-a",
            time_basis="campaign elapsed clock",
        ),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.microbial_campaign_summary",
            request,
            RunContext(asset_id="other", location_id="low-point-a", time_basis="clock"),
        )
