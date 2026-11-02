from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import probability_event
from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import (
    CorrosionRateModelOutputWallLossScenario,
    CorrosionRateProjectionRow,
    corrosion_model_output_to_first_passage_inputs,
)
from matintegrity.models.reliability import SampledLinearThicknessFirstPassage

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-1", time_basis="elapsed seconds")


def forecast_input():
    return {
        "forecast_id": "forecast-1",
        "asset_id": "asset-1",
        "location_id": "cml-1",
        "physical_scope_id": "circuit-1/cml-1",
        "physical_location_id": "cml-1",
        "time_basis": "elapsed seconds",
        "assessment_time_s": 0.0,
        "conditioning": "threshold not crossed at assessment time",
        "event_id": "minimum-thickness-first-crossing",
        "event_definition": "first crossing of 0.006 m remaining thickness",
        "required_thickness_m": 0.006,
        "distribution_definition_id": "authored-three-point-joint-distribution",
        "sample_design_id": "authored-exact-discrete-design",
        "joint_sample_source_sha256": "a" * 64,
        "samples": [
            {
                "sample_id": "cross-at-40m",
                "remaining_thickness_at_assessment_m": 0.010,
                "nonnegative_loss_rate_m_s": 1e-10,
                "normalized_weight": 0.2,
            },
            {
                "sample_id": "cross-at-30m",
                "remaining_thickness_at_assessment_m": 0.012,
                "nonnegative_loss_rate_m_s": 2e-10,
                "normalized_weight": 0.5,
            },
            {
                "sample_id": "zero-rate",
                "remaining_thickness_at_assessment_m": 0.009,
                "nonnegative_loss_rate_m_s": 0.0,
                "normalized_weight": 0.3,
            },
        ],
        "candidate_horizon_end_s": [20e6, 30e6, 40e6, 50e6],
        "maximum_weight_sum_error": 1e-12,
        "samples_conditioned_on_survival_to_assessment": True,
        "constant_nonnegative_loss_model_reviewed": True,
        "joint_sample_distribution_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "candidate_horizons_reviewed": True,
    }


def run(payload=None, context=CONTEXT):
    return evaluate(
        "reliability.sampled_linear_thickness_first_passage",
        forecast_input() if payload is None else payload,
        context,
    )


def test_weighted_crossing_curve_matches_direct_discrete_push_forward():
    result = run()
    assert result.status == "computed"
    assert [
        row["cumulative_probability_given_survival"] for row in result.values["forecast_points"]
    ] == pytest.approx([0.0, 0.5, 0.7, 0.7])
    crossing = {row["sample_id"]: row["first_crossing_time_s"] for row in result.values["sample_results"]}
    assert crossing["cross-at-30m"] == pytest.approx(30e6)
    assert crossing["cross-at-40m"] == pytest.approx(40e6)
    assert crossing["zero-rate"] is None
    assert result.values["never_crossing_probability_under_constant_rate"] == pytest.approx(0.3)
    assert result.values["positive_rate_crossing_after_final_horizon_probability"] == pytest.approx(0.0)
    assert result.values["failed_samples_discarded"] is False
    assert (
        result.probability_semantics["final_horizon_probability_given_survival"]
        == "conditional_first_failure_in_period"
    )


def test_positive_rate_mass_after_forecast_horizon_is_summed_directly():
    payload = forecast_input()
    payload["candidate_horizon_end_s"] = [20e6, 30e6]
    result = run(payload)
    assert result.values["final_horizon_probability_given_survival"] == pytest.approx(0.5)
    assert result.values["positive_rate_crossing_after_final_horizon_probability"] == pytest.approx(0.2)
    assert result.values["never_crossing_probability_under_constant_rate"] == pytest.approx(0.3)


def test_forecast_points_compose_with_estimate_basis_schedule():
    forecast = run()
    schedule = evaluate(
        "inspection.threshold_inspection_schedule",
        {
            "schedule_id": "schedule-from-forecast-1",
            "asset_id": "asset-1",
            "location_id": "cml-1",
            "physical_scope_id": forecast.values["physical_scope_id"],
            "event_id": forecast.values["event_id"],
            "event_definition": forecast.values["event_definition"],
            "assessment_time_s": forecast.values["assessment_time_s"],
            "conditioning": forecast.values["conditioning"],
            "event_probability_meaning": forecast.values["event_probability_meaning"],
            "forecast_model_id": forecast.model_id,
            "forecast_model_revision": forecast.model_version,
            "forecast_input_sha256": forecast.values["forecast_input_sha256"],
            "forecast_points": forecast.values["forecast_points"],
            "probability_basis": "estimate",
            "maximum_probability_before_inspection": 0.6,
            "minimum_notice_s": 0.0,
            "maximum_deferral_s": 50e6,
            "forecast_identity_reviewed": True,
            "event_scope_and_conditioning_reviewed": True,
            "cumulative_probability_curve_reviewed": True,
            "scheduling_criterion_user_approved": True,
            "evidence": [
                {
                    "source_id": "authored-composition-test",
                    "origin": "synthetic",
                    "citation": "authored first-passage to scheduling composition",
                }
            ],
        },
        CONTEXT,
    )
    assert schedule.status == "computed"
    assert schedule.values["selected_inspection_time_s"] == 30e6
    assert schedule.values["selected_probability_given_survival"] == pytest.approx(0.5)
    assert schedule.values["next_noncompliant_candidate_time_s"] == 40e6


def test_corrosion_scenario_adapter_preserves_lineage_and_composes_to_event_probability():
    source_digest = "c" * 64
    evidence = {
        "source_id": "synthetic-corrosion-model",
        "origin": "model_prediction",
        "citation": "Synthetic corrosion scenario adapter fixture",
        "license_id": "MIT",
        "sha256": source_digest,
    }
    scenario = CorrosionRateModelOutputWallLossScenario(
        rows=[
            CorrosionRateProjectionRow(
                scenario_id="rate-1",
                source_dataset_id="synthetic-corrosion-model",
                source_group_id="synthetic-run-1",
                source_record_id="row-1",
                source_archive_sha256=source_digest,
                source_role="simulated_model_output",
                rate_m_s=1e-10,
                evidence=(evidence,),
            ),
            CorrosionRateProjectionRow(
                scenario_id="rate-2",
                source_dataset_id="synthetic-corrosion-model",
                source_group_id="synthetic-run-1",
                source_record_id="row-2",
                source_archive_sha256=source_digest,
                source_role="simulated_model_output",
                rate_m_s=0.5e-10,
                evidence=(evidence,),
            ),
        ],
        current_thickness_m=0.01,
        required_thickness_m=0.008,
        horizon_s=50e6,
        material_state_compatibility_reviewed=True,
        material_state_review_id="review:material",
        condition_transferability_reviewed=True,
        condition_transfer_review_id="review:condition",
        linear_loss_model_reviewed=True,
        linear_loss_model_review_id="review:linear-loss",
        scenario_weights=[0.75, 0.25],
        weight_meaning="caller_declared_scenario_weight",
        scenario_set_id="synthetic-joint-rate-scenario",
    )
    review_ids = {
        "samples_conditioned_on_survival_to_assessment": "review:survival",
        "constant_nonnegative_loss_model_reviewed": "review:loss-model",
        "joint_sample_distribution_reviewed": "review:joint-distribution",
        "required_thickness_basis_reviewed": "review:required-thickness",
        "candidate_horizons_reviewed": "review:horizons",
    }
    adapted = corrosion_model_output_to_first_passage_inputs(
        scenario,
        forecast_id="synthetic-corrosion-first-passage",
        asset_id="asset-1",
        location_id="cml-1",
        physical_scope_id="circuit-1/cml-1",
        physical_location_id="cml-1",
        time_basis="elapsed seconds",
        assessment_time_s=0.0,
        conditioning="survived above reviewed minimum thickness at assessment",
        event_id="minimum-thickness-first-crossing",
        event_definition="first crossing of 0.008 m remaining thickness",
        distribution_definition_id="reviewed-two-rate-distribution",
        sample_design_id="synthetic-review-design-1",
        candidate_horizon_end_s=[10e6, 20e6, 30e6, 50e6],
        current_thickness_at_assessment_review_id="review:assessment-thickness",
        samples_conditioned_on_survival_to_assessment=True,
        constant_nonnegative_loss_model_reviewed=True,
        joint_sample_distribution_reviewed=True,
        required_thickness_basis_reviewed=True,
        candidate_horizons_reviewed=True,
        review_reference_ids=review_ids,
    )
    forecast = evaluate(
        "reliability.sampled_linear_thickness_first_passage",
        adapted.model_dump(mode="json"),
        CONTEXT,
    )
    assert forecast.status == "computed"
    assert forecast.values["source_lineage"]["source_record_ids"] == ["row-1", "row-2"]
    assert forecast.values["review_reference_ids"]["joint_sample_distribution_reviewed"] == (
        "review:joint-distribution"
    )
    assert [
        point["cumulative_probability_given_survival"] for point in forecast.values["forecast_points"]
    ] == pytest.approx([0.0, 0.75, 0.75, 1.0])
    with pytest.raises(ValueError, match="conditional first-failure probability"):
        probability_event(
            forecast,
            event_id="minimum-thickness-first-crossing",
            physical_scope_id="circuit-1/cml-1",
            failure_mode="caller-defined-thickness-threshold-crossing",
            horizon_start_s=0.0,
            horizon_end_s=50e6,
            conditioning="survived above reviewed minimum thickness at assessment",
        )


def test_assessment_conditioning_conflict_is_retained_and_withholds_curve():
    payload = forecast_input()
    payload["samples"][1]["remaining_thickness_at_assessment_m"] = 0.006
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["forecast_state"] == "conditioning_conflict_at_assessment"
    assert result.values["conditioning_conflict_sample_ids"] == ["cross-at-30m"]
    assert "forecast_points" not in result.values


def test_missing_review_gate_withholds_curve_without_dropping_identity():
    payload = forecast_input()
    payload["joint_sample_distribution_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["forecast_state"] == "review_required"
    assert result.values["missing_review_gates"] == ["joint_sample_distribution_reviewed"]
    assert result.values["joint_sample_source_sha256"] == "a" * 64


def test_nested_non_finite_source_lineage_is_rejected_at_contract_boundary():
    payload = forecast_input()
    payload["source_lineage"] = {"provider": {"weights": [0.5, float("nan")]}}
    with pytest.raises(ValidationError, match="non-finite numbers"):
        SampledLinearThicknessFirstPassage.model_validate(payload)


def test_blank_review_reference_id_is_rejected_at_contract_boundary():
    payload = forecast_input()
    payload["review_reference_ids"] = {"distribution_review": "  "}
    with pytest.raises(ValidationError, match="review reference IDs must be non-blank"):
        SampledLinearThicknessFirstPassage.model_validate(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["samples"][1].update(sample_id="cross-at-40m"), "IDs must be unique"),
        (lambda value: value["samples"][0].update(normalized_weight=0.3), "weights must sum"),
        (lambda value: value.update(candidate_horizon_end_s=[20e6, 20e6]), "strictly increase"),
        (lambda value: value.update(candidate_horizon_end_s=[0.0, 20e6]), "greater than 0"),
    ],
)
def test_invalid_joint_distribution_or_horizons_are_rejected(mutate, message):
    payload = forecast_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        SampledLinearThicknessFirstPassage.model_validate(payload)


def test_context_identity_and_time_basis_are_enforced():
    wrong_asset = RunContext(asset_id="asset-2", location_id="cml-1", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="asset and location"):
        run(context=wrong_asset)
    wrong_clock = RunContext(asset_id="asset-1", location_id="cml-1", time_basis="calendar seconds")
    with pytest.raises(ValueError, match="time basis"):
        run(context=wrong_clock)


def test_input_is_not_mutated_and_content_digest_changes_with_samples():
    payload = forecast_input()
    original = deepcopy(payload)
    first = run(payload)
    assert payload == original
    payload["samples"][0]["remaining_thickness_at_assessment_m"] = 0.011
    second = run(payload)
    assert first.values["forecast_input_sha256"] != second.values["forecast_input_sha256"]
