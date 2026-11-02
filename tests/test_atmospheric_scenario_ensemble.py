import pytest
from pydantic import ValidationError

from matintegrity.models.atmospheric import AtmosphericFirstYearModel, AtmosphericFirstYearPrediction
from matintegrity.models.atmospheric_ensemble import (
    AtmosphericScenario,
    AtmosphericScenarioEnsemble,
    atmospheric_scenario_ensemble,
)
from matintegrity.units import SECONDS_PER_YEAR


def _model():
    return AtmosphericFirstYearModel(
        model_id="model",
        fit_id="fit",
        coefficient_log_m=-11.0,
        coefficient_temperature_per_10_K=0.0,
        coefficient_relative_humidity_per_0_1=0.0,
        coefficient_log1p_chloride=0.0,
        coefficient_log1p_sulfur_dioxide=0.0,
        coefficient_covariance=[[0.0] * 5 for _ in range(5)],
        residual_standard_deviation_log_m=0.0,
        calibration_support_temperature_K=[280.0, 300.0],
        calibration_support_relative_humidity_fraction=[0.5, 0.9],
        calibration_support_chloride_mg_m2_day=[0.0, 10.0],
        calibration_support_sulfur_dioxide_mg_m2_day=[0.0, 10.0],
        calibration_observation_count=12,
        calibration_source_group_ids=["a", "b"],
        calibration_input_digest="a" * 64,
        holdout_input_digest="b" * 64,
        holdout_observation_count=4,
        holdout_log_rmse=0.1,
        holdout_absolute_log_bias=0.1,
        holdout_outside_support_fraction=0.0,
        holdout_source_group_metrics=[
            {
                "source_group_id": "holdout-a",
                "observation_count": 2,
                "log_rmse": 0.1,
                "absolute_log_bias": 0.1,
                "outside_support_count": 0,
                "outside_support_fraction": 0.0,
            },
            {
                "source_group_id": "holdout-b",
                "observation_count": 2,
                "log_rmse": 0.1,
                "absolute_log_bias": 0.1,
                "outside_support_count": 0,
                "outside_support_fraction": 0.0,
            },
        ],
        maximum_holdout_source_group_log_rmse=0.1,
        maximum_holdout_source_group_absolute_log_bias=0.1,
        source_group_transfer_criteria_met=True,
        maximum_holdout_log_rmse=1.0,
        maximum_absolute_holdout_log_bias=1.0,
        maximum_holdout_outside_support_fraction=0.2,
        transfer_criteria_met=True,
    )


def _scenario(name, weight, temperature):
    return AtmosphericScenario(
        scenario_id=name,
        weight=weight,
        prediction_input=AtmosphericFirstYearPrediction(
            prediction_id=name,
            asset_id="asset",
            location_id="location",
            physical_scope_id="scope",
            material_condition_id="carbon-steel",
            exposure_environment_id="environment",
            time_basis="exposure seconds",
            exposure_start_s=0,
            exposure_duration_s=SECONDS_PER_YEAR,
            model=_model(),
            temperature_K=temperature,
            relative_humidity_fraction=0.7,
            chloride_deposition_mg_m2_day=2,
            sulfur_dioxide_deposition_mg_m2_day=1,
            first_year_atmospheric_carbon_steel_scope_reviewed=True,
            covariates_reviewed=True,
            model_applicability_reviewed=True,
        ),
    )


def _ensemble(scenarios):
    return AtmosphericScenarioEnsemble(
        ensemble_id="ensemble",
        asset_id="asset",
        location_id="location",
        scenarios=tuple(scenarios),
        independence_assumption_reviewed=True,
        scenario_weights_reviewed=True,
        evidence=({"source_id": "fixture", "origin": "synthetic", "citation": "authored fixture"},),
    )


def test_weighted_scenario_summary_preserves_predictions_and_quantiles():
    report = atmospheric_scenario_ensemble(
        _ensemble([_scenario("low", 0.25, 285), _scenario("high", 0.75, 295)])
    )
    assert report.status == "computed"
    summary = report.values["summary"]
    one_year_loss = 1.670170079024566e-5
    expected = 0.25 * one_year_loss + 0.75 * one_year_loss
    assert summary["weighted_mean_first_year_loss_m"] == pytest.approx(expected)
    assert summary["weighted_quantiles_first_year_loss_m"]["0.5"] == pytest.approx(one_year_loss)
    assert report.values["remaining_life_or_probability_generated"] is False


def test_weights_must_be_normalized_and_scenarios_unique():
    with pytest.raises(ValidationError, match="sum to one"):
        _ensemble([_scenario("a", 0.4, 285), _scenario("b", 0.4, 295)])
    with pytest.raises(ValidationError, match="unique"):
        _ensemble([_scenario("a", 0.5, 285), _scenario("a", 0.5, 295)])


def test_scenarios_must_share_scope_and_match_parent_asset():
    original = _scenario("b", 0.5, 295)
    changed_input = original.prediction_input.model_copy(update={"asset_id": "other"})
    changed = original.model_copy(update={"prediction_input": changed_input})
    with pytest.raises(ValidationError, match="asset and location"):
        _ensemble([_scenario("a", 0.5, 285), changed])


def test_unreviewed_weights_block_aggregation():
    item = AtmosphericScenarioEnsemble(
        ensemble_id="ensemble",
        asset_id="asset",
        location_id="location",
        scenarios=(_scenario("a", 1.0, 285),),
        independence_assumption_reviewed=True,
        scenario_weights_reviewed=False,
        evidence=({"source_id": "fixture", "origin": "synthetic", "citation": "authored fixture"},),
    )
    assert atmospheric_scenario_ensemble(item).status == "needs_data"
