"""Verify tabulated growth interpolation and integration against authored closed forms."""

import copy
import json
import math
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.models.crack import (
    CrackGrowthScenario,
    TabulatedCrackGrowthScenarioEnsemble,
    crack_growth_scenario_manifest,
    evaluate_crack_growth_scenario_job,
)
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/tabulated_crack_growth_math.json"


def authored_curve(
    upper_delta_k=40e6,
    *,
    lower_delta_k=5e6,
    curve_id="authored-cubic-growth",
    stress_ratio=0.1,
    frequency_hz=1.0,
    coefficient=1e-28,
):
    delta_k = sorted(
        {
            value
            for value in (lower_delta_k, 5e6, 10e6, 20e6, upper_delta_k)
            if lower_delta_k <= value <= upper_delta_k
        }
    )
    return {
        "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
        "curve_id": curve_id,
        "source_group_id": "authored-validation",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "stress_ratio": stress_ratio,
        "frequency_Hz": frequency_hz,
        "delta_k_Pa_sqrt_m": delta_k,
        "crack_growth_m_cycle": [coefficient * value**3 for value in delta_k],
        "interpolation": "log_delta_k_log_growth_linear",
        "below_minimum_policy": "out_of_scope",
        "declared_threshold_delta_k_Pa_sqrt_m": None,
        "source_content_sha256": ("a" if coefficient == 1e-28 else "b") * 64,
        "pointwise_computational_use_authorized": True,
        "curve_applicability_reviewed": True,
        "physical_specimen_identity_status": "not_required_for_user_model",
    }


def growth_payload(curve, cycles):
    return {
        "schema_version": "matintegrity.tabulated_crack_growth.v1",
        "assessment_id": "authored-closed-form-check",
        "physical_scope_id": "synthetic-crack-front",
        "initial_depth_m": 0.001,
        "terminal_depth_m": 0.004,
        "geometry_depth_m": [0.0005, 0.004],
        "geometry_factor": [1.12, 1.12],
        "blocks": [
            {
                "minimum_stress_Pa": 10e6,
                "maximum_stress_Pa": 100e6,
                "cycles": cycles,
                "frequency_Hz": 1.0,
            }
        ],
        "curve": curve,
        "maximum_absolute_stress_ratio_difference": 0.0,
        "maximum_relative_frequency_difference": 0.0,
        "fracture_toughness_Pa_sqrt_m": 100e6,
        "relative_integration_tolerance": 1e-8,
        "absolute_cycle_tolerance": 1e-6,
        "absolute_depth_tolerance_m": 1e-13,
        "geometry_solution_reviewed": True,
        "load_to_curve_mapping_reviewed": True,
        "toughness_application_reviewed": True,
    }


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="synthetic-asset",
        location_id="synthetic-crack",
        time_basis="authored closed-form validation",
    )
    curve = authored_curve()
    query_delta_k = math.sqrt(5e6 * 10e6)
    query = registry.run(
        "fracture.tabulated_growth_rate",
        {"curve": curve, "query_delta_k_Pa_sqrt_m": [query_delta_k]},
        context,
    )
    computed_rate = query.values["query_results"][0]["crack_growth_m_cycle"]
    expected_rate = 1e-28 * query_delta_k**3

    cycles = 1000.0
    growth = registry.run("fracture.tabulated_crack_growth", growth_payload(curve, cycles), context)
    rate_factor = 1e-28 * (1.12 * 90e6 * math.sqrt(math.pi)) ** 3
    expected_depth = (0.001**-0.5 - rate_factor * cycles / 2.0) ** -2

    upper_delta_k = 7e6
    bounded = registry.run(
        "fracture.tabulated_crack_growth",
        growth_payload(authored_curve(upper_delta_k), 1e8),
        context,
    )
    expected_bound_depth = (upper_delta_k / (1.12 * 90e6)) ** 2 / math.pi
    family_cycles = (1000.0, 2000.0)
    family_curves = [
        authored_curve(
            upper_delta_k=20e6,
            lower_delta_k=2e6,
            curve_id="authored-R01-f1",
        ),
        authored_curve(
            upper_delta_k=20e6,
            lower_delta_k=2e6,
            curve_id="authored-R05-f01",
            stress_ratio=0.5,
            frequency_hz=0.1,
            coefficient=2e-28,
        ),
    ]
    family = registry.run(
        "fracture.tabulated_curve_family_growth",
        {
            "schema_version": "matintegrity.tabulated_curve_family_growth.v1",
            "assessment_id": "authored-family-check",
            "physical_scope_id": "synthetic-crack-front",
            "initial_depth_m": 0.001,
            "terminal_depth_m": 0.004,
            "geometry_depth_m": [0.0005, 0.004],
            "geometry_factor": [1.12, 1.12],
            "blocks": [
                {
                    "minimum_stress_Pa": 10e6,
                    "maximum_stress_Pa": 100e6,
                    "cycles": family_cycles[0],
                    "frequency_Hz": 1.0,
                },
                {
                    "minimum_stress_Pa": 50e6,
                    "maximum_stress_Pa": 100e6,
                    "cycles": family_cycles[1],
                    "frequency_Hz": 0.1,
                },
            ],
            "curve_family": {
                "schema_version": "matintegrity.tabulated_crack_growth_curve_family.v1",
                "family_id": "authored-two-condition-family",
                "material_condition_id": "synthetic-state",
                "environment_id": "synthetic-environment",
                "curves": family_curves,
                "maximum_absolute_stress_ratio_difference": 0.0,
                "maximum_relative_frequency_difference": 0.0,
                "selection_policy": "nearest_within_declared_tolerances",
                "family_applicability_reviewed": True,
            },
            "fracture_toughness_Pa_sqrt_m": 100e6,
            "relative_integration_tolerance": 1e-8,
            "absolute_cycle_tolerance": 1e-6,
            "absolute_depth_tolerance_m": 1e-13,
            "geometry_solution_reviewed": True,
            "load_to_curve_mapping_reviewed": True,
            "toughness_application_reviewed": True,
        },
        context,
    )
    first_family_factor = 1e-28 * (1.12 * 90e6 * math.sqrt(math.pi)) ** 3
    depth_after_first = (0.001**-0.5 - first_family_factor * family_cycles[0] / 2.0) ** -2
    second_family_factor = 2e-28 * (1.12 * 50e6 * math.sqrt(math.pi)) ** 3
    expected_family_depth = (depth_after_first**-0.5 - second_family_factor * family_cycles[1] / 2.0) ** -2
    uncertainty = registry.run(
        "fracture.tabulated_crack_growth_uncertainty",
        {
            "schema_version": "matintegrity.tabulated_crack_growth_uncertainty.v1",
            "uncertainty_run_id": "authored-two-point-push-forward",
            "distribution_definition_id": "authored-discrete-input-mass",
            "sample_design_id": "authored-two-point-design",
            "joint_sample_source_id": "authored-validation",
            "joint_sample_source_sha256": "c" * 64,
            "base_growth": growth_payload(curve, cycles),
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
        },
        context,
    )
    uncertainty_depths = [
        (0.001**-0.5 - rate_factor * multiplier * cycles / 2.0) ** -2 for multiplier in (0.5, 2.0)
    ]
    expected_uncertainty_mean = 0.25 * uncertainty_depths[0] + 0.75 * uncertainty_depths[1]
    unit_sample = {
        "normalized_weight": 0.5,
        "crack_growth_rate_multiplier": 1.0,
        "geometry_factor_multiplier": 1.0,
        "stress_multiplier": 1.0,
        "fracture_toughness_multiplier": 1.0,
    }
    convergence = registry.run(
        "fracture.tabulated_crack_growth_uncertainty_convergence",
        {
            "schema_version": ("matintegrity.tabulated_crack_growth_uncertainty_convergence.v1"),
            "convergence_run_id": "authored-stable-design-comparison",
            "distribution_definition_id": "authored-degenerate-input-mass",
            "base_growth": growth_payload(curve, cycles),
            "levels": [
                {
                    "level_id": "n2",
                    "sample_design_id": "authored-degenerate-n2",
                    "joint_sample_source_id": "authored-validation-n2",
                    "joint_sample_source_sha256": "d" * 64,
                    "relationship_to_previous": "initial",
                    "samples": [
                        {**unit_sample, "sample_id": "s1"},
                        {**unit_sample, "sample_id": "s2"},
                    ],
                },
                {
                    "level_id": "n4",
                    "sample_design_id": "authored-degenerate-n4",
                    "joint_sample_source_id": "authored-validation-n4",
                    "joint_sample_source_sha256": "e" * 64,
                    "relationship_to_previous": "nested_refinement",
                    "samples": [
                        {
                            **unit_sample,
                            "sample_id": sample_id,
                            "normalized_weight": 0.25,
                        }
                        for sample_id in ("s1", "s2", "s3", "s4")
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
            "maximum_absolute_exceedance_probability_change": 1e-12,
            "joint_sample_values_reviewed": True,
            "dependence_preserved_in_joint_rows": True,
            "normalized_weight_meaning_reviewed": True,
            "base_model_and_multiplier_scope_reviewed": True,
            "level_relationships_reviewed": True,
            "diagnostic_tolerances_reviewed": True,
        },
        context,
    )
    low_scenario = growth_payload(curve, cycles)
    high_scenario = copy.deepcopy(low_scenario)
    low_scenario["assessment_id"] = "authored-complete-low"
    high_scenario["assessment_id"] = "authored-complete-high"
    low_scenario["curve"]["crack_growth_m_cycle"] = [
        0.5 * value for value in low_scenario["curve"]["crack_growth_m_cycle"]
    ]
    high_scenario["curve"]["crack_growth_m_cycle"] = [
        2.0 * value for value in high_scenario["curve"]["crack_growth_m_cycle"]
    ]
    low_scenario["curve"]["source_content_sha256"] = "f" * 64
    high_scenario["curve"]["source_content_sha256"] = "9" * 64
    scenario_ensemble_payload = {
        "schema_version": "matintegrity.tabulated_crack_growth_scenario_ensemble.v1",
        "ensemble_run_id": "authored-complete-scenario-check",
        "distribution_definition_id": "authored-discrete-input-mass",
        "sample_design_id": "authored-two-complete-inputs",
        "scenarios": [
            {
                "schema_version": "matintegrity.crack_growth_scenario.v1",
                "scenario_id": "low-growth",
                "normalized_weight": 0.25,
                "joint_scenario_source_id": "authored-low-input",
                "joint_scenario_source_sha256": "1" * 64,
                "growth": low_scenario,
            },
            {
                "schema_version": "matintegrity.crack_growth_scenario.v1",
                "scenario_id": "high-growth",
                "normalized_weight": 0.75,
                "joint_scenario_source_id": "authored-high-input",
                "joint_scenario_source_sha256": "2" * 64,
                "growth": high_scenario,
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
    scenario_ensemble = registry.run(
        "fracture.tabulated_crack_growth_scenario_ensemble",
        scenario_ensemble_payload,
        context,
    )
    scenario_contract = TabulatedCrackGrowthScenarioEnsemble.model_validate(scenario_ensemble_payload)
    evaluator = {
        "evaluator_id": "matintegrity-tabulated-growth",
        "evaluator_revision": "authored-validation-v1",
        "evaluator_configuration_sha256": "8" * 64,
    }
    scenario_evaluations = [
        evaluate_crack_growth_scenario_job(
            CrackGrowthScenario.model_validate(scenario.model_dump(mode="json")),
            **evaluator,
        ).model_dump(mode="json")
        for scenario in scenario_contract.scenarios
    ]
    scenario_reduction = registry.run(
        "fracture.tabulated_crack_growth_scenario_reduction",
        {
            "schema_version": "matintegrity.tabulated_crack_growth_scenario_reduction.v1",
            "ensemble_run_id": scenario_contract.ensemble_run_id,
            "distribution_definition_id": scenario_contract.distribution_definition_id,
            "sample_design_id": scenario_contract.sample_design_id,
            "manifest": [
                row.model_dump(mode="json") for row in crack_growth_scenario_manifest(scenario_contract)
            ],
            "evaluations": list(reversed(scenario_evaluations)),
            "requested_quantiles": scenario_contract.requested_quantiles,
            "depth_exceedance_threshold_m": (scenario_contract.depth_exceedance_threshold_m),
            "maximum_weight_sum_error": scenario_contract.maximum_weight_sum_error,
            **evaluator,
            "external_evaluations_reviewed": True,
            "normalized_weight_meaning_reviewed": True,
            "common_physical_scope_reviewed": True,
        },
        context,
    )
    report = {
        "schema": "matintegrity.tabulated_crack_growth_math.v1",
        "validation_input_origin": "independently authored synthetic cubic curve",
        "external_pointwise_data_used": False,
        "interpolation": {
            "query_delta_k_Pa_sqrt_m": query_delta_k,
            "computed_growth_m_cycle": computed_rate,
            "closed_form_growth_m_cycle": expected_rate,
            "relative_difference": abs(computed_rate / expected_rate - 1.0),
        },
        "integration": {
            "cycles": cycles,
            "computed_final_depth_m": growth.values["final_depth_m"],
            "closed_form_final_depth_m": expected_depth,
            "relative_difference": abs(growth.values["final_depth_m"] / expected_depth - 1.0),
            "cycle_inversion_residual": growth.values["block_results"][0]["cycle_inversion_residual"],
        },
        "curve_upper_bound": {
            "computed_final_depth_m": bounded.values["final_depth_m"],
            "closed_form_bound_depth_m": expected_bound_depth,
            "relative_difference": abs(bounded.values["final_depth_m"] / expected_bound_depth - 1.0),
            "status": bounded.status,
            "termination_reason": bounded.values["termination_reason"],
        },
        "curve_family": {
            "selected_curve_ids": family.values["selected_curve_ids"],
            "computed_final_depth_m": family.values["final_depth_m"],
            "closed_form_final_depth_m": expected_family_depth,
            "relative_difference": abs(family.values["final_depth_m"] / expected_family_depth - 1.0),
            "condition_interpolation_performed": False,
        },
        "joint_input_uncertainty": {
            "sample_ids": [row["sample_id"] for row in uncertainty.values["sample_results"]],
            "computed_weighted_mean_final_depth_m": uncertainty.values["weighted_mean_final_depth_m"],
            "closed_form_weighted_mean_final_depth_m": expected_uncertainty_mean,
            "relative_difference": abs(
                uncertainty.values["weighted_mean_final_depth_m"] / expected_uncertainty_mean - 1.0
            ),
            "model_implied_depth_exceedance_probability": uncertainty.values[
                "model_implied_depth_exceedance_probability"
            ],
            "probability_meaning": uncertainty.probability_semantics[
                "model_implied_depth_exceedance_probability"
            ],
            "failed_samples_discarded": False,
        },
        "uncertainty_design_convergence_diagnostic": {
            "level_ids": [row["level_id"] for row in convergence.values["level_results"]],
            "all_transition_diagnostic_criteria_met": convergence.values[
                "all_transition_diagnostic_criteria_met"
            ],
            "transition_diagnostics": convergence.values["transition_diagnostics"],
            "convergence_proof_claimed": False,
            "failed_levels_discarded": False,
        },
        "complete_input_scenario_ensemble": {
            "scenario_ids": [row["scenario_id"] for row in scenario_ensemble.values["scenario_results"]],
            "computed_weighted_mean_final_depth_m": scenario_ensemble.values["weighted_mean_final_depth_m"],
            "closed_form_weighted_mean_final_depth_m": expected_uncertainty_mean,
            "relative_difference": abs(
                scenario_ensemble.values["weighted_mean_final_depth_m"] / expected_uncertainty_mean - 1.0
            ),
            "model_implied_depth_exceedance_probability": scenario_ensemble.values[
                "model_implied_depth_exceedance_probability"
            ],
            "probability_meaning": scenario_ensemble.probability_semantics[
                "model_implied_depth_exceedance_probability"
            ],
            "failed_scenarios_discarded": False,
        },
        "portable_scenario_map_reduce": {
            "external_evaluation_order_reversed": True,
            "reported_scenario_ids": [
                row["scenario_id"] for row in scenario_reduction.values["scenario_results"]
            ],
            "direct_weighted_mean_final_depth_m": scenario_ensemble.values["weighted_mean_final_depth_m"],
            "reduced_weighted_mean_final_depth_m": scenario_reduction.values["weighted_mean_final_depth_m"],
            "absolute_difference_m": abs(
                scenario_reduction.values["weighted_mean_final_depth_m"]
                - scenario_ensemble.values["weighted_mean_final_depth_m"]
            ),
            "input_digest_match_required": True,
            "evaluator_identity_match_required": True,
            "failed_evaluations_discarded": False,
        },
        "qualification": (
            "Synthetic mathematical verification only. It does not qualify a material curve, "
            "hydrogen environment, geometry solution, service load, toughness or remaining life."
        ),
    }
    if report["interpolation"]["relative_difference"] > 1e-12:
        raise SystemExit("log-log interpolation failed the cubic identity")
    if report["integration"]["relative_difference"] > 2e-8:
        raise SystemExit("tabulated growth failed the closed-form depth identity")
    if report["curve_upper_bound"]["relative_difference"] > 1e-9:
        raise SystemExit("curve-support termination failed the closed-form depth identity")
    if bounded.status != "out_of_scope" or bounded.values["termination_reason"] != (
        "growth_curve_upper_bound_reached"
    ):
        raise SystemExit("curve-support termination semantics changed")
    if report["curve_family"]["selected_curve_ids"] != [
        "authored-R01-f1",
        "authored-R05-f01",
    ]:
        raise SystemExit("curve-family selection changed")
    if report["curve_family"]["relative_difference"] > 3e-8:
        raise SystemExit("curve-family growth failed the piecewise closed-form identity")
    if report["joint_input_uncertainty"]["relative_difference"] > 3e-8:
        raise SystemExit("joint uncertainty propagation failed the weighted closed-form identity")
    if report["joint_input_uncertainty"]["model_implied_depth_exceedance_probability"] != 0.75:
        raise SystemExit("joint uncertainty exceedance mass changed")
    if not report["uncertainty_design_convergence_diagnostic"]["all_transition_diagnostic_criteria_met"]:
        raise SystemExit("stable uncertainty-design diagnostic changed")
    diagnostic = report["uncertainty_design_convergence_diagnostic"]["transition_diagnostics"][0]
    if any(
        diagnostic[key] != 0.0
        for key in (
            "normalized_mean_depth_change",
            "normalized_standard_deviation_change",
            "maximum_normalized_quantile_depth_change",
            "absolute_exceedance_probability_change",
        )
    ):
        raise SystemExit("degenerate uncertainty designs should have zero statistic changes")
    if report["complete_input_scenario_ensemble"]["relative_difference"] > 3e-8:
        raise SystemExit("complete scenario ensemble failed the weighted closed-form identity")
    if report["complete_input_scenario_ensemble"]["model_implied_depth_exceedance_probability"] != 0.75:
        raise SystemExit("complete scenario ensemble exceedance mass changed")
    if report["portable_scenario_map_reduce"]["absolute_difference_m"] != 0.0:
        raise SystemExit("portable scenario reduction changed the in-process result")
    if report["portable_scenario_map_reduce"]["reported_scenario_ids"] != [
        "low-growth",
        "high-growth",
    ]:
        raise SystemExit("portable scenario reduction did not restore manifest order")
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
