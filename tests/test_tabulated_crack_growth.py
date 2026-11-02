import copy
import math

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.models.crack import (
    TabulatedCrackGrowthScenarioEnsemble,
    crack_growth_scenario_manifest,
    evaluate_crack_growth_scenario_job,
)

CONTEXT = RunContext(
    asset_id="synthetic-asset",
    location_id="synthetic-crack",
    time_basis="ordered synthetic load blocks",
)


def curve(*, upper=40e6, policy="out_of_scope", threshold=None):
    delta_k = [5e6, 10e6, 20e6, upper]
    if upper <= 20e6:
        delta_k = [5e6, upper]
    coefficient = 1e-28
    return {
        "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
        "curve_id": "synthetic-paris-points",
        "source_group_id": "authored-validation",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "stress_ratio": 0.1,
        "frequency_Hz": 1.0,
        "delta_k_Pa_sqrt_m": delta_k,
        "crack_growth_m_cycle": [coefficient * value**3 for value in delta_k],
        "interpolation": "log_delta_k_log_growth_linear",
        "below_minimum_policy": policy,
        "declared_threshold_delta_k_Pa_sqrt_m": threshold,
        "source_content_sha256": "a" * 64,
        "pointwise_computational_use_authorized": True,
        "curve_applicability_reviewed": True,
        "physical_specimen_identity_status": "not_required_for_user_model",
    }


def growth_input():
    return {
        "schema_version": "matintegrity.tabulated_crack_growth.v1",
        "assessment_id": "synthetic-growth-check",
        "physical_scope_id": "synthetic-crack-front",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "curve_material_environment_mapping_reviewed": True,
        "initial_depth_m": 0.001,
        "terminal_depth_m": 0.004,
        "geometry_depth_m": [0.0005, 0.004],
        "geometry_factor": [1.12, 1.12],
        "blocks": [
            {
                "minimum_stress_Pa": 10e6,
                "maximum_stress_Pa": 100e6,
                "cycles": 1000.0,
                "frequency_Hz": 1.0,
            }
        ],
        "curve": curve(),
        "maximum_absolute_stress_ratio_difference": 0.0,
        "maximum_relative_frequency_difference": 0.0,
        "fracture_toughness_Pa_sqrt_m": 100e6,
        "relative_integration_tolerance": 1e-9,
        "absolute_cycle_tolerance": 1e-7,
        "absolute_depth_tolerance_m": 1e-12,
        "geometry_solution_reviewed": True,
        "load_to_curve_mapping_reviewed": True,
        "toughness_application_reviewed": True,
    }


def family_curve(curve_id, stress_ratio, frequency_hz, coefficient):
    item = curve()
    item.update(
        {
            "curve_id": curve_id,
            "stress_ratio": stress_ratio,
            "frequency_Hz": frequency_hz,
            "delta_k_Pa_sqrt_m": [2e6, 5e6, 10e6, 20e6],
        }
    )
    item["crack_growth_m_cycle"] = [coefficient * value**3 for value in item["delta_k_Pa_sqrt_m"]]
    return item


def family_growth_input():
    inputs = growth_input()
    inputs.pop("curve")
    inputs.pop("maximum_absolute_stress_ratio_difference")
    inputs.pop("maximum_relative_frequency_difference")
    inputs.pop("curve_material_environment_mapping_reviewed")
    inputs["schema_version"] = "matintegrity.tabulated_curve_family_growth.v1"
    inputs["material_condition_id"] = "synthetic-state"
    inputs["environment_id"] = "synthetic-environment"
    inputs["curve_family_material_environment_mapping_reviewed"] = True
    inputs["blocks"] = [
        {
            "minimum_stress_Pa": 10e6,
            "maximum_stress_Pa": 100e6,
            "cycles": 1000.0,
            "frequency_Hz": 1.0,
        },
        {
            "minimum_stress_Pa": 50e6,
            "maximum_stress_Pa": 100e6,
            "cycles": 2000.0,
            "frequency_Hz": 0.1,
        },
    ]
    inputs["curve_family"] = {
        "schema_version": "matintegrity.tabulated_crack_growth_curve_family.v1",
        "family_id": "synthetic-two-condition-family",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "curves": [
            family_curve("R01-f1", 0.1, 1.0, 1e-28),
            family_curve("R05-f01", 0.5, 0.1, 2e-28),
        ],
        "maximum_absolute_stress_ratio_difference": 0.0,
        "maximum_relative_frequency_difference": 0.0,
        "selection_policy": "nearest_within_declared_tolerances",
        "family_applicability_reviewed": True,
    }
    return inputs


def uncertainty_input(base=None):
    return {
        "schema_version": "matintegrity.tabulated_crack_growth_uncertainty.v1",
        "uncertainty_run_id": "synthetic-joint-ensemble",
        "distribution_definition_id": "authored-discrete-mass",
        "sample_design_id": "authored-two-point-design",
        "joint_sample_source_id": "authored-validation",
        "joint_sample_source_sha256": "c" * 64,
        "base_growth": growth_input() if base is None else base,
        "samples": [
            {
                "sample_id": "low-growth",
                "normalized_weight": 0.25,
                "crack_growth_rate_multiplier": 0.5,
                "geometry_factor_multiplier": 1.0,
                "stress_multiplier": 1.0,
                "fracture_toughness_multiplier": 1.0,
            },
            {
                "sample_id": "high-growth",
                "normalized_weight": 0.75,
                "crack_growth_rate_multiplier": 2.0,
                "geometry_factor_multiplier": 1.0,
                "stress_multiplier": 1.0,
                "fracture_toughness_multiplier": 1.0,
            },
        ],
        "requested_quantiles": [0.25, 0.5, 0.9],
        "depth_exceedance_threshold_m": 0.00102,
        "maximum_weight_sum_error": 1e-12,
        "joint_sample_values_reviewed": True,
        "dependence_preserved_in_joint_rows": True,
        "normalized_weight_meaning_reviewed": True,
        "base_model_and_multiplier_scope_reviewed": True,
    }


def scenario_ensemble_input():
    low = growth_input()
    high = growth_input()
    low["assessment_id"] = "synthetic-full-scenario-low"
    high["assessment_id"] = "synthetic-full-scenario-high"
    low["curve"]["crack_growth_m_cycle"] = [0.5 * value for value in low["curve"]["crack_growth_m_cycle"]]
    high["curve"]["crack_growth_m_cycle"] = [2.0 * value for value in high["curve"]["crack_growth_m_cycle"]]
    low["curve"]["source_content_sha256"] = "d" * 64
    high["curve"]["source_content_sha256"] = "e" * 64
    return {
        "schema_version": "matintegrity.tabulated_crack_growth_scenario_ensemble.v1",
        "ensemble_run_id": "synthetic-complete-scenario-ensemble",
        "distribution_definition_id": "authored-discrete-mass",
        "sample_design_id": "authored-two-complete-inputs",
        "scenarios": [
            {
                "schema_version": "matintegrity.crack_growth_scenario.v1",
                "scenario_id": "low-growth",
                "normalized_weight": 0.25,
                "joint_scenario_source_id": "authored-low-input",
                "joint_scenario_source_sha256": "f" * 64,
                "growth": low,
            },
            {
                "schema_version": "matintegrity.crack_growth_scenario.v1",
                "scenario_id": "high-growth",
                "normalized_weight": 0.75,
                "joint_scenario_source_id": "authored-high-input",
                "joint_scenario_source_sha256": "9" * 64,
                "growth": high,
            },
        ],
        "requested_quantiles": [0.25, 0.5, 0.9],
        "depth_exceedance_threshold_m": 0.00102,
        "maximum_weight_sum_error": 1e-12,
        "full_scenario_inputs_reviewed": True,
        "dependence_preserved_inside_scenarios": True,
        "normalized_weight_meaning_reviewed": True,
        "common_physical_scope_reviewed": True,
    }


def scenario_reduction_input():
    ensemble = TabulatedCrackGrowthScenarioEnsemble.model_validate(scenario_ensemble_input())
    evaluator = {
        "evaluator_id": "matintegrity-tabulated-growth",
        "evaluator_revision": "authored-test-revision",
        "evaluator_configuration_sha256": "8" * 64,
    }
    return {
        "schema_version": "matintegrity.tabulated_crack_growth_scenario_reduction.v1",
        "ensemble_run_id": ensemble.ensemble_run_id,
        "distribution_definition_id": ensemble.distribution_definition_id,
        "sample_design_id": ensemble.sample_design_id,
        "manifest": [row.model_dump(mode="json") for row in crack_growth_scenario_manifest(ensemble)],
        "evaluations": [
            evaluate_crack_growth_scenario_job(
                scenario,
                evaluator_id=evaluator["evaluator_id"],
                evaluator_revision=evaluator["evaluator_revision"],
                evaluator_configuration_sha256=evaluator["evaluator_configuration_sha256"],
            ).model_dump(mode="json")
            for scenario in ensemble.scenarios
        ],
        "requested_quantiles": ensemble.requested_quantiles,
        "depth_exceedance_threshold_m": ensemble.depth_exceedance_threshold_m,
        "maximum_weight_sum_error": ensemble.maximum_weight_sum_error,
        **evaluator,
        "external_evaluations_reviewed": True,
        "normalized_weight_meaning_reviewed": True,
        "common_physical_scope_reviewed": True,
    }


def convergence_input():
    def sample(sample_id, weight, *, growth=1.0, stress=1.0):
        return {
            "sample_id": sample_id,
            "normalized_weight": weight,
            "crack_growth_rate_multiplier": growth,
            "geometry_factor_multiplier": 1.0,
            "stress_multiplier": stress,
            "fracture_toughness_multiplier": 1.0,
        }

    return {
        "schema_version": "matintegrity.tabulated_crack_growth_uncertainty_convergence.v1",
        "convergence_run_id": "synthetic-nested-design-check",
        "distribution_definition_id": "authored-degenerate-input-mass",
        "base_growth": growth_input(),
        "levels": [
            {
                "schema_version": "matintegrity.crack_growth_uncertainty_design_level.v1",
                "level_id": "n2",
                "sample_design_id": "nested-design-n2",
                "joint_sample_source_id": "authored-validation",
                "joint_sample_source_sha256": "d" * 64,
                "relationship_to_previous": "initial",
                "samples": [sample("s1", 0.5), sample("s2", 0.5)],
            },
            {
                "schema_version": "matintegrity.crack_growth_uncertainty_design_level.v1",
                "level_id": "n4",
                "sample_design_id": "nested-design-n4",
                "joint_sample_source_id": "authored-validation",
                "joint_sample_source_sha256": "e" * 64,
                "relationship_to_previous": "nested_refinement",
                "samples": [
                    sample("s1", 0.25),
                    sample("s2", 0.25),
                    sample("s3", 0.25),
                    sample("s4", 0.25),
                ],
            },
        ],
        "requested_quantiles": [0.25, 0.5, 0.9],
        "depth_exceedance_threshold_m": 0.00102,
        "maximum_weight_sum_error": 1e-12,
        "depth_change_scale_m": 0.001,
        "maximum_normalized_mean_depth_change": 1e-12,
        "maximum_normalized_standard_deviation_change": 1e-12,
        "maximum_normalized_quantile_depth_change": 1e-12,
        "maximum_absolute_exceedance_probability_change": 0.0,
        "joint_sample_values_reviewed": True,
        "dependence_preserved_in_joint_rows": True,
        "normalized_weight_meaning_reviewed": True,
        "base_model_and_multiplier_scope_reviewed": True,
        "level_relationships_reviewed": True,
        "diagnostic_tolerances_reviewed": True,
    }


def test_log_log_query_recovers_power_law_and_refuses_extrapolation():
    item = curve()
    query = math.sqrt(item["delta_k_Pa_sqrt_m"][0] * item["delta_k_Pa_sqrt_m"][1])
    result = evaluate(
        "fracture.tabulated_growth_rate",
        {"curve": item, "query_delta_k_Pa_sqrt_m": [query, 50e6]},
        CONTEXT,
    )
    assert result.status == "out_of_scope"
    assert result.qualification == "user_model"
    assert result.values["query_results"][0]["crack_growth_m_cycle"] == pytest.approx(1e-28 * query**3)
    assert result.values["query_results"][1]["crack_growth_m_cycle"] is None


def test_tabulated_integration_recovers_closed_form_paris_solution():
    inputs = growth_input()
    result = evaluate("fracture.tabulated_crack_growth", inputs, CONTEXT)
    factor = 1e-28 * (1.12 * 90e6 * math.sqrt(math.pi)) ** 3
    expected = (0.001**-0.5 - factor * 1000.0 / 2.0) ** -2
    assert result.status == "computed"
    assert result.values["final_depth_m"] == pytest.approx(expected, rel=2e-8)
    assert result.values["cycles_evaluated"] == 1000.0
    assert abs(result.values["block_results"][0]["cycle_inversion_residual"]) < 1e-4


def test_curve_support_toughness_and_mapping_terminations_remain_distinct():
    support = growth_input()
    support["curve"] = curve(upper=7e6)
    support["blocks"][0]["cycles"] = 1e8
    result = evaluate("fracture.tabulated_crack_growth", support, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["termination_reason"] == "growth_curve_upper_bound_reached"

    toughness = growth_input()
    toughness["fracture_toughness_Pa_sqrt_m"] = 8e6
    toughness["blocks"][0]["cycles"] = 1e8
    result = evaluate("fracture.tabulated_crack_growth", toughness, CONTEXT)
    assert result.status == "computed"
    assert result.values["termination_reason"] == "toughness_limit_reached"

    mismatch = growth_input()
    mismatch["blocks"][0]["frequency_Hz"] = 2.0
    result = evaluate("fracture.tabulated_crack_growth", mismatch, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["termination_reason"] == "frequency_outside_curve_mapping"


def test_below_support_requires_an_explicit_threshold_policy():
    inputs = growth_input()
    inputs["blocks"][0]["maximum_stress_Pa"] = 20e6
    inputs["blocks"][0]["minimum_stress_Pa"] = 2e6
    result = evaluate("fracture.tabulated_crack_growth", inputs, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["termination_reason"] == "delta_K_below_curve_support"

    inputs["curve"] = curve(policy="zero_below_declared_threshold", threshold=2e6)
    result = evaluate("fracture.tabulated_crack_growth", inputs, CONTEXT)
    assert result.status == "computed"
    assert result.values["final_depth_m"] == inputs["initial_depth_m"]
    assert result.values["block_results"][0]["mode"] == "below_declared_threshold"


@pytest.mark.parametrize(
    "change, match",
    [
        ({"pointwise_computational_use_authorized": False}, "literal_error"),
        ({"curve_applicability_reviewed": False}, "literal_error"),
        ({"delta_k_Pa_sqrt_m": [5e6, 5e6]}, "strictly increase"),
        (
            {
                "below_minimum_policy": "zero_below_declared_threshold",
                "declared_threshold_delta_k_Pa_sqrt_m": None,
            },
            "requires a caller-declared threshold",
        ),
    ],
)
def test_curve_contract_rejects_unreviewed_or_invalid_inputs(change, match):
    inputs = growth_input()
    inputs["curve"] = copy.deepcopy(inputs["curve"])
    inputs["curve"].update(change)
    if "delta_k_Pa_sqrt_m" in change:
        inputs["curve"]["crack_growth_m_cycle"] = [1e-8, 1e-8]
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_crack_growth", inputs, CONTEXT)


def test_curve_family_selects_one_curve_per_block_and_matches_piecewise_closed_form():
    inputs = family_growth_input()
    result = evaluate("fracture.tabulated_curve_family_growth", inputs, CONTEXT)
    first_factor = 1e-28 * (1.12 * 90e6 * math.sqrt(math.pi)) ** 3
    after_first = (0.001**-0.5 - first_factor * 1000.0 / 2.0) ** -2
    second_factor = 2e-28 * (1.12 * 50e6 * math.sqrt(math.pi)) ** 3
    expected = (after_first**-0.5 - second_factor * 2000.0 / 2.0) ** -2
    assert result.status == "computed"
    assert result.values["selected_curve_ids"] == ["R01-f1", "R05-f01"]
    assert result.values["final_depth_m"] == pytest.approx(expected, rel=3e-8)
    assert [row["block_index"] for row in result.values["block_results"]] == [0, 1]


def test_curve_family_allows_unique_nearest_match_but_does_not_interpolate_conditions():
    inputs = family_growth_input()
    inputs["blocks"] = [
        {
            "minimum_stress_Pa": 11e6,
            "maximum_stress_Pa": 100e6,
            "cycles": 1000.0,
            "frequency_Hz": 1.01,
        }
    ]
    inputs["curve_family"]["maximum_absolute_stress_ratio_difference"] = 0.02
    inputs["curve_family"]["maximum_relative_frequency_difference"] = 0.02
    result = evaluate("fracture.tabulated_curve_family_growth", inputs, CONTEXT)
    selection = result.values["curve_selection_results"][0]
    assert result.status == "computed"
    assert selection["selected_curve_id"] == "R01-f1"
    assert result.values["selected_curve_ids"] == ["R01-f1"]


def test_curve_family_stops_on_missing_and_ambiguous_mappings():
    missing = family_growth_input()
    missing["blocks"] = [
        {
            "minimum_stress_Pa": 30e6,
            "maximum_stress_Pa": 100e6,
            "cycles": 10.0,
            "frequency_Hz": 3.0,
        }
    ]
    result = evaluate("fracture.tabulated_curve_family_growth", missing, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["termination_reason"] == "no_curve_within_mapping_tolerances"
    assert result.values["cycles_evaluated"] == 0

    ambiguous = family_growth_input()
    ambiguous["curve_family"]["curves"] = [
        family_curve("R00-f1", 0.0, 1.0, 1e-28),
        family_curve("R02-f1", 0.2, 1.0, 2e-28),
    ]
    ambiguous["curve_family"]["maximum_absolute_stress_ratio_difference"] = 0.11
    ambiguous["curve_family"]["maximum_relative_frequency_difference"] = 0.0
    ambiguous["blocks"] = [
        {
            "minimum_stress_Pa": 10e6,
            "maximum_stress_Pa": 100e6,
            "cycles": 10.0,
            "frequency_Hz": 1.0,
        }
    ]
    result = evaluate("fracture.tabulated_curve_family_growth", ambiguous, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["termination_reason"] == "ambiguous_curve_mapping"
    assert set(result.values["curve_selection_results"][0]["tied_curve_ids"]) == {
        "R00-f1",
        "R02-f1",
    }


@pytest.mark.parametrize(
    "change, match",
    [
        ({"material_condition_id": "different-state"}, "declared material condition"),
        ({"environment_id": "different-environment"}, "declared environment"),
    ],
)
def test_curve_family_rejects_mixed_material_or_environment(change, match):
    inputs = family_growth_input()
    inputs["curve_family"]["curves"][1].update(change)
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_curve_family_growth", inputs, CONTEXT)


def test_joint_uncertainty_matches_direct_weighted_deterministic_runs():
    inputs = uncertainty_input()
    result = evaluate("fracture.tabulated_crack_growth_uncertainty", inputs, CONTEXT)
    direct_depths = []
    for sample in inputs["samples"]:
        direct = copy.deepcopy(inputs["base_growth"])
        direct["curve"]["crack_growth_m_cycle"] = [
            value * sample["crack_growth_rate_multiplier"]
            for value in direct["curve"]["crack_growth_m_cycle"]
        ]
        direct_depths.append(
            evaluate("fracture.tabulated_crack_growth", direct, CONTEXT).values["final_depth_m"]
        )
    expected_mean = 0.25 * direct_depths[0] + 0.75 * direct_depths[1]
    expected_variance = sum(
        weight * (value - expected_mean) ** 2
        for value, weight in zip(direct_depths, (0.25, 0.75), strict=True)
    )
    assert result.status == "computed"
    assert result.values["weighted_mean_final_depth_m"] == pytest.approx(expected_mean)
    assert result.values["weighted_standard_deviation_final_depth_m"] == pytest.approx(
        math.sqrt(expected_variance)
    )
    assert [row["final_depth_m"] for row in result.values["weighted_quantiles"]] == [
        direct_depths[0],
        direct_depths[1],
        direct_depths[1],
    ]
    assert result.values["model_implied_depth_exceedance_probability"] == 0.75
    assert result.probability_semantics["model_implied_depth_exceedance_probability"] == (
        "model_implied_input_uncertainty_probability"
    )


def test_uncertainty_keeps_failed_samples_and_withholds_aggregates():
    inputs = uncertainty_input()
    inputs["samples"][1]["crack_growth_rate_multiplier"] = 1.0
    inputs["samples"][1]["stress_multiplier"] = 10.0
    result = evaluate("fracture.tabulated_crack_growth_uncertainty", inputs, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["status_counts"] == {
        "computed": 1,
        "out_of_scope": 1,
        "needs_data": 0,
    }
    assert len(result.values["sample_results"]) == 2
    assert result.values["weighted_mean_final_depth_m"] is None
    assert result.values["weighted_quantiles"] is None
    assert result.values["model_implied_depth_exceedance_probability"] is None


def test_uncertainty_accepts_curve_family_base_and_preserves_joint_rows():
    inputs = uncertainty_input(family_growth_input())
    for sample in inputs["samples"]:
        sample["crack_growth_rate_multiplier"] = 1.0
    result = evaluate("fracture.tabulated_crack_growth_uncertainty", inputs, CONTEXT)
    direct = evaluate("fracture.tabulated_curve_family_growth", inputs["base_growth"], CONTEXT)
    assert result.status == "computed"
    assert result.values["weighted_mean_final_depth_m"] == pytest.approx(direct.values["final_depth_m"])
    assert [row["sample_id"] for row in result.values["sample_results"]] == [
        "low-growth",
        "high-growth",
    ]


@pytest.mark.parametrize(
    "mutator, match",
    [
        (lambda x: x["samples"][1].update(normalized_weight=0.5), "weights must sum to one"),
        (lambda x: x["samples"][1].update(sample_id="low-growth"), "sample IDs must be unique"),
        (lambda x: x.update(requested_quantiles=[0.5, 0.5]), "strictly increase"),
    ],
)
def test_uncertainty_rejects_invalid_weight_identity_or_quantile_design(mutator, match):
    inputs = uncertainty_input()
    mutator(inputs)
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_crack_growth_uncertainty", inputs, CONTEXT)


def test_nested_uncertainty_design_reports_stable_identical_push_forwards():
    inputs = convergence_input()
    result = evaluate("fracture.tabulated_crack_growth_uncertainty_convergence", inputs, CONTEXT)
    transition = result.values["transition_diagnostics"][0]
    assert result.status == "computed"
    assert result.values["all_transition_diagnostic_criteria_met"] is True
    assert transition["normalized_mean_depth_change"] == pytest.approx(0.0, abs=1e-15)
    assert transition["maximum_normalized_quantile_depth_change"] == pytest.approx(0.0, abs=1e-15)
    assert result.probability_semantics["model_implied_depth_exceedance_probability"] == (
        "model_implied_input_uncertainty_probability"
    )


def test_uncertainty_design_change_can_fail_diagnostic_without_becoming_an_error():
    inputs = convergence_input()
    inputs["levels"][1]["samples"][2]["crack_growth_rate_multiplier"] = 2.0
    inputs["levels"][1]["samples"][3]["crack_growth_rate_multiplier"] = 2.0
    result = evaluate("fracture.tabulated_crack_growth_uncertainty_convergence", inputs, CONTEXT)
    assert result.status == "computed"
    assert result.values["all_transition_diagnostic_criteria_met"] is False
    assert result.values["transition_diagnostics"][0]["diagnostic_criteria_met"] is False


def test_uncertainty_convergence_withholds_claim_when_refined_level_has_failed_samples():
    inputs = convergence_input()
    inputs["levels"][1]["samples"][2]["stress_multiplier"] = 10.0
    inputs["levels"][1]["samples"][3]["stress_multiplier"] = 10.0
    result = evaluate("fracture.tabulated_crack_growth_uncertainty_convergence", inputs, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["all_transition_diagnostic_criteria_met"] is None
    assert result.values["transition_diagnostics"][0]["diagnostic_criteria_met"] is None


def remove_prior_nested_sample(inputs):
    inputs["levels"][1]["samples"].pop(0)
    for sample in inputs["levels"][1]["samples"]:
        sample["normalized_weight"] = 1 / 3


def change_prior_nested_sample(inputs):
    inputs["levels"][1]["samples"][0]["crack_growth_rate_multiplier"] = 1.1


def change_initial_relationship(inputs):
    inputs["levels"][0]["relationship_to_previous"] = "refined_design"


@pytest.mark.parametrize(
    "mutator, match",
    [
        (remove_prior_nested_sample, "retain every prior sample ID"),
        (change_prior_nested_sample, "changed a prior joint sample row"),
        (change_initial_relationship, "first uncertainty level"),
    ],
)
def test_uncertainty_convergence_rejects_false_lineage(mutator, match):
    inputs = convergence_input()
    mutator(inputs)
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_crack_growth_uncertainty_convergence", inputs, CONTEXT)


def test_complete_scenario_ensemble_matches_equivalent_global_multiplier_ensemble():
    scenario = evaluate(
        "fracture.tabulated_crack_growth_scenario_ensemble",
        scenario_ensemble_input(),
        CONTEXT,
    )
    multiplier = evaluate("fracture.tabulated_crack_growth_uncertainty", uncertainty_input(), CONTEXT)
    assert scenario.status == "computed"
    assert scenario.values["weighted_mean_final_depth_m"] == pytest.approx(
        multiplier.values["weighted_mean_final_depth_m"]
    )
    assert scenario.values["weighted_quantiles"] == multiplier.values["weighted_quantiles"]
    assert scenario.values["model_implied_depth_exceedance_probability"] == 0.75
    assert (
        scenario.probability_semantics["model_implied_depth_exceedance_probability"]
        == "model_implied_input_uncertainty_probability"
    )


def test_complete_scenario_ensemble_accepts_joint_local_curve_geometry_load_and_toughness():
    inputs = scenario_ensemble_input()
    changed = inputs["scenarios"][1]["growth"]
    changed["curve"]["crack_growth_m_cycle"][-1] *= 1.25
    changed["geometry_factor"][-1] = 1.2
    changed["blocks"][0]["minimum_stress_Pa"] *= 0.9
    changed["blocks"][0]["maximum_stress_Pa"] *= 0.9
    changed["fracture_toughness_Pa_sqrt_m"] *= 0.9
    result = evaluate("fracture.tabulated_crack_growth_scenario_ensemble", inputs, CONTEXT)
    assert result.status == "computed"
    rows = result.values["scenario_results"]
    assert rows[0]["input_sha256"] != rows[1]["input_sha256"]
    assert rows[0]["final_depth_m"] != rows[1]["final_depth_m"]


def test_complete_scenario_ensemble_retains_failed_scenario_and_withholds_aggregates():
    inputs = scenario_ensemble_input()
    failed = inputs["scenarios"][1]["growth"]
    failed["blocks"][0]["minimum_stress_Pa"] *= 10.0
    failed["blocks"][0]["maximum_stress_Pa"] *= 10.0
    result = evaluate("fracture.tabulated_crack_growth_scenario_ensemble", inputs, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["scenario_count"] == 2
    assert result.values["status_counts"]["out_of_scope"] == 1
    assert result.values["weighted_mean_final_depth_m"] is None
    assert result.values["weighted_quantiles"] is None
    assert result.values["model_implied_depth_exceedance_probability"] is None


@pytest.mark.parametrize(
    "mutator, match",
    [
        (
            lambda x: x["scenarios"][1].update(scenario_id="low-growth"),
            "scenario IDs must be unique",
        ),
        (
            lambda x: x["scenarios"][1].update(normalized_weight=0.5),
            "scenario weights must sum to one",
        ),
        (
            lambda x: x["scenarios"][1]["growth"].update(physical_scope_id="another-crack-front"),
            "share one physical scope",
        ),
    ],
)
def test_complete_scenario_ensemble_rejects_false_distribution_contract(mutator, match):
    inputs = scenario_ensemble_input()
    mutator(inputs)
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_crack_growth_scenario_ensemble", inputs, CONTEXT)


def test_portable_scenario_reduction_matches_in_process_ensemble_and_manifest_order():
    inputs = scenario_reduction_input()
    inputs["evaluations"].reverse()
    reduced = evaluate("fracture.tabulated_crack_growth_scenario_reduction", inputs, CONTEXT)
    direct = evaluate(
        "fracture.tabulated_crack_growth_scenario_ensemble",
        scenario_ensemble_input(),
        CONTEXT,
    )
    assert reduced.status == "computed"
    assert reduced.values["weighted_mean_final_depth_m"] == pytest.approx(
        direct.values["weighted_mean_final_depth_m"]
    )
    assert reduced.values["weighted_quantiles"] == direct.values["weighted_quantiles"]
    assert [row["scenario_id"] for row in reduced.values["scenario_results"]] == [
        "low-growth",
        "high-growth",
    ]


@pytest.mark.parametrize(
    "mutator, match",
    [
        (
            lambda x: x["evaluations"][1].update(scenario_id="unmanifested-scenario"),
            "exactly cover the manifest",
        ),
        (
            lambda x: x["evaluations"][0].update(input_sha256="0" * 64),
            "input digest does not match",
        ),
        (
            lambda x: x["evaluations"][0].update(evaluator_revision="mixed-revision"),
            "evaluator identity is inconsistent",
        ),
    ],
)
def test_portable_scenario_reduction_rejects_incomplete_or_mismatched_rows(mutator, match):
    inputs = scenario_reduction_input()
    mutator(inputs)
    with pytest.raises(ValidationError, match=match):
        evaluate("fracture.tabulated_crack_growth_scenario_reduction", inputs, CONTEXT)


def test_portable_scenario_reduction_retains_external_failure_and_withholds_aggregates():
    inputs = scenario_reduction_input()
    failed = inputs["evaluations"][1]
    failed.update(
        status="execution_failed",
        final_depth_m=None,
        cycles_evaluated=None,
        termination_reason=None,
        result_sha256="7" * 64,
    )
    result = evaluate("fracture.tabulated_crack_growth_scenario_reduction", inputs, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["scenario_count"] == 2
    assert result.values["status_counts"]["execution_failed"] == 1
    assert result.values["weighted_mean_final_depth_m"] is None
    assert result.values["weighted_quantiles"] is None
