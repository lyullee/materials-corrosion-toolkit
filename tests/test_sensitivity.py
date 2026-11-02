import json
import math

import numpy as np
import pytest

from matintegrity.contracts import canonical_digest
from matintegrity.registry import default_registry
from matintegrity.sensitivity import (
    SensitivityBatchResult,
    SensitivityMarginal,
    SobolDesign,
    SobolEvaluationBatch,
    SobolEvaluations,
    SobolInputBatch,
    SobolRequest,
    analyze_sobol_evaluations,
    create_sobol_design,
    evaluate_sobol_design,
    iter_sobol_batches,
    registry_sensitivity_evaluator,
    run_sobol,
    seal_sobol_evaluations,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "Authored mathematical fixture"}


def marginal(name, lower=-1.0, upper=1.0, unit="1"):
    return dict(name=name, unit=unit, family="uniform", lower=lower, upper=upper, evidence=[EVIDENCE])


def request(**changes):
    data = dict(
        analysis_id="synthetic",
        context=dict(asset_id="synthetic", location_id="synthetic", time_basis="fixed response"),
        evaluator_id="authored",
        evaluator_revision="1",
        parameters=[marginal("x"), marginal("y")],
        quantities=[dict(name="response", unit="1")],
        sample_powers=[6, 8],
        scrambles=4,
        seed=2026,
        independence_declared=True,
        deterministic_response_declared=True,
    )
    data.update(changes)
    return SobolRequest.model_validate_json(json.dumps(data))


def additive(draws):
    return draws["x"] + 2 * draws["y"]


def ishigami(draws):
    return np.sin(draws["x"]) * (1 + 0.1 * draws["z"] ** 4) + 7 * np.sin(draws["y"]) ** 2


def test_worker_batch_preserves_native_units_and_evaluator_request_identity():
    definition = request(parameters=[marginal("mass", 1.0, 3.0, "mg"), marginal("area", 1.0, 2.0, "cm^2")])
    design = create_sobol_design(definition)
    batch = next(iter_sobol_batches(design))
    restored = SobolInputBatch.model_validate_json(batch.model_dump_json())
    assert restored.parameter_units == {"mass": "mg", "area": "cm^2"}
    assert restored.evaluator_id == definition.evaluator_id
    assert restored.evaluator_revision == definition.evaluator_revision
    assert restored.request_digest == canonical_digest(definition.model_dump(mode="json"))
    assert restored.design_digest == design.content_digest
    assert all(1.0 <= mass <= 3.0 for mass in restored.parameters["mass"])
    for units in ({"mass": "mg"}, {"mass": "mg", "area": "no_such_physical_unit"}):
        payload = restored.model_dump(mode="json")
        payload["parameter_units"] = units
        with pytest.raises(ValueError):
            SobolInputBatch.model_validate_json(json.dumps(payload))


def test_additive_sensitivity_matches_closed_variance_decomposition():
    result = run_sobol(request(sample_powers=[7, 10]), additive)
    final = result.quantities[0].levels[-1]
    assert result.status == "computed" and result.precision_status == "criteria_met"
    np.testing.assert_allclose(final.first_order, [0.2, 0.8], atol=0.005, rtol=0)
    np.testing.assert_allclose(final.total_order, [0.2, 0.8], atol=0.005, rtol=0)
    assert result.diagnostics["observed_evaluations"] == 4 * (1024 * 4 + 8)
    assert not result.diagnostics["variance_indices_are_period_failure_probabilities"]


def test_ishigami_recovers_independent_analytic_main_and_interaction_variances():
    specification = request(
        parameters=[marginal(s, -math.pi, math.pi) for s in ("x", "y", "z")], sample_powers=[9, 12]
    )
    final = run_sobol(specification, ishigami).quantities[0].levels[-1]
    variance_one = 0.5 * (1 + 0.1 * math.pi**4 / 5) ** 2
    variance_two = 49 / 8
    interaction = 0.01 * math.pi**8 * 8 / 225
    total = variance_one + variance_two + interaction
    np.testing.assert_allclose(
        final.first_order, [variance_one / total, variance_two / total, 0], atol=0.015, rtol=0
    )
    np.testing.assert_allclose(
        final.total_order,
        [(variance_one + interaction) / total, variance_two / total, interaction / total],
        atol=0.015,
        rtol=0,
    )


def test_pure_interaction_has_zero_main_effect_and_two_total_effects():
    final = run_sobol(request(sample_powers=[7, 10]), lambda d: d["x"] * d["y"]).quantities[0].levels[-1]
    np.testing.assert_allclose(final.first_order, [0, 0], atol=0.02, rtol=0)
    np.testing.assert_allclose(final.total_order, [1, 1], atol=0.02, rtol=0)


def test_unused_parameter_is_retained_with_zero_contribution():
    specification = request(parameters=[marginal(s) for s in ("x", "y", "unused")])
    result = run_sobol(specification, additive)
    assert result.parameter_names == ["x", "y", "unused"]
    assert result.quantities[0].levels[-1].first_order[2] == 0
    assert result.quantities[0].levels[-1].total_order[2] == 0


def test_affine_response_and_extreme_magnitude_invariance_preserve_indices():
    specification = request(quantities=[dict(name=s, unit="1") for s in ("base", "affine", "tiny", "huge")])

    def response(d):
        value = additive(d)
        return np.column_stack([value, 1000 - 3 * value, 1e-200 * value, 1e200 * value])

    result = run_sobol(specification, response)
    first = result.quantities[0].levels[-1].first_order
    for quantity in result.quantities[1:]:
        np.testing.assert_allclose(quantity.levels[-1].first_order, first, atol=1e-11, rtol=0)
    assert "NaN" not in result.model_dump_json()


def test_constant_quantity_is_undefined_without_erasing_other_quantities():
    specification = request(quantities=[dict(name=s, unit="1") for s in ("constant", "variable")])
    result = run_sobol(specification, lambda d: np.column_stack([np.ones_like(d["x"]), additive(d)]))
    assert result.status == "needs_data" and result.precision_status == "not_evaluable"
    assert result.quantities[0].status == "undefined_or_unresolved_variance"
    assert result.quantities[0].levels[-1].first_order is None
    assert result.quantities[1].status == "estimated"


def test_numerically_unresolved_variation_is_not_reported_as_confident_sensitivity():
    result = run_sobol(request(), lambda d: 1e16 + additive(d))
    assert result.status == "needs_data"
    assert result.quantities[0].levels[-1].first_order is None


def test_finite_estimates_are_separate_from_unmet_precision_criteria():
    specification = request(
        sample_powers=[3, 4], refinement_absolute_tolerance=1e-9, confidence_half_width_tolerance=1e-9
    )
    result = run_sobol(specification, lambda d: np.exp(d["x"]) + d["y"] ** 3)
    assert result.status == "computed" and result.precision_status == "sampling_precision_unresolved"
    assert not result.quantities[0].precision_criteria_satisfied
    assert result.quantities[0].levels[-1].first_order is not None


def test_finite_sample_negative_effect_estimates_are_not_clipped():
    specification = request(
        parameters=[marginal(s, -math.pi, math.pi) for s in ("x", "y", "z")], sample_powers=[3, 4]
    )
    result = run_sobol(specification, ishigami)
    estimates = [row[2] for level in result.quantities[0].levels for row in level.first_order_replicates]
    assert min(estimates) < 0


@pytest.mark.parametrize(
    "callback,match",
    [
        (lambda d: np.ones((len(d["x"]), 2)), "shape"),
        (lambda d: np.array(["text"] * len(d["x"])), "real numeric"),
        (lambda d: additive(d).astype(complex), "real numeric"),
    ],
)
def test_evaluator_shape_and_numeric_contracts(callback, match):
    with pytest.raises(ValueError, match=match):
        evaluate_sobol_design(create_sobol_design(request(sample_powers=[3, 4])), callback)


def test_nonfinite_output_and_physical_failures_cannot_be_filtered_or_imputed():
    design = create_sobol_design(request(sample_powers=[3, 4]))
    bad_output = analyze_sobol_evaluations(
        design, evaluate_sobol_design(design, lambda d: np.full(len(d["x"]), np.nan))
    )
    assert bad_output.status == "needs_data" and bad_output.quantities == []
    assert bad_output.diagnostics["observed_row_status_counts"]["invalid_output"] > 0
    physical = evaluate_sobol_design(
        design,
        lambda d: SensitivityBatchResult(np.full(len(d["x"]), np.nan), ("out_of_scope",) * len(d["x"])),
        stop_on_uncomputed=False,
    )
    result = analyze_sobol_evaluations(design, physical)
    assert result.diagnostics["missing_evaluations"] == 0 and result.quantities == []
    assert result.status == "needs_data"


def test_repeat_checks_refuse_stochastic_or_batch_dependent_evaluators():
    calls = 0

    def changing(d):
        nonlocal calls
        calls += 1
        return additive(d) + calls

    result = run_sobol(request(sample_powers=[3, 4]), changing)
    assert result.status == "needs_data" and result.quantities == []
    assert result.diagnostics["nonrepeatable_quantity"] == "response"
    assert calls == 2


def test_portable_out_of_order_batches_recover_the_same_paired_design():
    design = SobolDesign.model_validate_json(
        create_sobol_design(request(sample_powers=[3, 5])).model_dump_json()
    )
    ordered = evaluate_sobol_design(design, additive, batch_size=7)
    responses = []
    for batch in iter_sobol_batches(design, batch_size=7):
        values = additive({name: np.asarray(v) for name, v in batch.parameters.items()})
        responses.append(
            SobolEvaluationBatch(
                design_digest=batch.design_digest,
                replicate_index=batch.replicate_index,
                block_id=batch.block_id,
                repeat=batch.repeat,
                point_indices=batch.point_indices[::-1],
                values=[[float(v)] for v in values[::-1]],
                row_status=["computed"] * len(values),
            )
        )
    shuffled = SobolEvaluations.model_validate_json(
        seal_sobol_evaluations(design, responses[::-1]).model_dump_json()
    )
    first = analyze_sobol_evaluations(design, ordered).quantities[0]
    second = analyze_sobol_evaluations(design, shuffled).quantities[0]
    assert ordered.content_digest != shuffled.content_digest
    assert first == second


def test_same_seed_reproduces_design_and_mutation_breaks_its_digest():
    specification = request(sample_powers=[3, 4])
    first, second = create_sobol_design(specification), create_sobol_design(specification)
    assert first.content_digest == second.content_digest
    first.matrices[0].a[0][0] += 0.1
    with pytest.raises(ValueError, match="design content digest"):
        list(iter_sobol_batches(first))


def test_cross_design_replay_evaluation_tampering_and_duplicate_ids_are_rejected():
    first = create_sobol_design(request(sample_powers=[3, 4]))
    second = create_sobol_design(request(sample_powers=[3, 4], seed=2027))
    evaluations = evaluate_sobol_design(first, additive)
    with pytest.raises(ValueError, match="another design"):
        seal_sobol_evaluations(second, evaluations.responses)
    duplicates = seal_sobol_evaluations(first, [*evaluations.responses, evaluations.responses[0]])
    with pytest.raises(ValueError, match="duplicate response"):
        analyze_sobol_evaluations(first, duplicates)
    evaluations.responses[0].values[0][0] += 1
    with pytest.raises(ValueError, match="content digest"):
        analyze_sobol_evaluations(first, evaluations)


def test_incomplete_evaluations_have_no_estimated_indices():
    design = create_sobol_design(request(sample_powers=[3, 4]))
    complete = evaluate_sobol_design(design, additive)
    result = analyze_sobol_evaluations(design, seal_sobol_evaluations(design, complete.responses[:-1]))
    assert result.status == "needs_data" and result.diagnostics["missing_evaluations"] > 0
    assert result.quantities == []


@pytest.mark.parametrize("field", ["independence_declared", "deterministic_response_declared"])
def test_unreviewed_joint_or_noise_assumptions_are_refused(field):
    with pytest.raises(ValueError, match="explicit declarations"):
        create_sobol_design(request(**{field: False}))


def test_budget_is_checked_before_model_evaluation():
    called = False

    def response(d):
        nonlocal called
        called = True
        return additive(d)

    with pytest.raises(ValueError, match="evaluation budget"):
        run_sobol(request(maximum_model_evaluations=10), response)
    assert not called


def test_native_normal_lognormal_and_quantile_table_distributions():
    parameters = [
        dict(
            name="normal", unit="Pa", family="normal", mean=10.0, standard_deviation=2.0, evidence=[EVIDENCE]
        ),
        dict(
            name="positive",
            unit="m",
            family="lognormal",
            log_mean=0.1,
            log_standard_deviation=0.2,
            reference_value=5.0,
            evidence=[EVIDENCE],
        ),
        dict(
            name="table",
            unit="1",
            family="quantile_table",
            probabilities=[0.0, 0.5, 1.0],
            quantiles=[0.0, 0.0, 2.0],
            evidence=[EVIDENCE],
        ),
    ]
    design = create_sobol_design(request(parameters=parameters, sample_powers=[7, 9]))
    draws = np.concatenate([np.asarray(v) for p in design.matrices for v in (p.a, p.b)])
    assert np.mean(draws[:, 0]) == pytest.approx(10, abs=0.02)
    assert np.std(draws[:, 0]) == pytest.approx(2, abs=0.03)
    assert np.mean(np.log(draws[:, 1] / 5)) == pytest.approx(0.1, abs=0.003)
    assert np.std(np.log(draws[:, 1] / 5)) == pytest.approx(0.2, abs=0.003)
    assert np.mean(draws[:, 2] == 0) == 0.5
    assert np.mean(draws[:, 2]) == pytest.approx(0.5, abs=0.003)


@pytest.mark.parametrize(
    "change",
    [dict(upper=-2.0), dict(lower=0.0, mean=1.0), dict(unit="unrecognized_unit"), dict(lower=math.inf)],
)
def test_bad_marginal_parameters_are_not_silently_repaired(change):
    data = marginal("x")
    data.update(change)
    with pytest.raises(ValueError):
        SensitivityMarginal.model_validate_json(json.dumps(data))


def test_lognormal_offset_units_and_numerical_underflow_are_refused():
    parameters = dict(
        name="positive",
        unit="degC",
        family="lognormal",
        log_mean=0.0,
        log_standard_deviation=0.1,
        reference_value=1.0,
        evidence=[EVIDENCE],
    )
    with pytest.raises(ValueError, match="multiplicative unit"):
        SensitivityMarginal.model_validate_json(json.dumps(parameters))
    parameters.update(unit="1", log_mean=-1000.0)
    with pytest.raises(ValueError, match="underflowed"):
        create_sobol_design(request(parameters=[parameters], sample_powers=[3, 4]))


def test_registry_bridge_uses_declared_units_and_matches_independent_coupon_arithmetic():
    specification = request(
        evaluator_id="corrosion.coupon_loss",
        evaluator_revision="0.1.1",
        evaluator_configuration=dict(
            model_id="corrosion.coupon_loss",
            base_inputs=dict(density_kg_m3=7800.0, duration_s=86400.0),
            bindings=[
                dict(parameter_name="mass", input_field="mass_loss_kg", input_unit="kg"),
                dict(parameter_name="area", input_field="exposed_area_m2", input_unit="m^2"),
            ],
        ),
        parameters=[marginal("mass", 1.0, 3.0, "mg"), marginal("area", 1.0, 2.0, "cm^2")],
        quantities=[dict(name="mean_penetration_m", unit="mm")],
        sample_powers=[3, 4],
    )
    design = create_sobol_design(specification)
    registry = evaluate_sobol_design(
        design, registry_sensitivity_evaluator(default_registry(), specification)
    )
    direct = evaluate_sobol_design(design, lambda d: d["mass"] * 1e-6 / (d["area"] * 1e-4 * 7800) * 1000)
    for expected, actual in zip(direct.responses, registry.responses, strict=True):
        np.testing.assert_allclose(actual.values, expected.values, rtol=1e-13)
    assert analyze_sobol_evaluations(design, registry).status == "computed"
    stale = specification.model_copy(update={"evaluator_revision": "another-version"})
    with pytest.raises(ValueError, match="identity/revision"):
        registry_sensitivity_evaluator(default_registry(), stale)


def test_registry_input_domain_failure_stops_instead_of_changing_the_prior():
    data = request(
        evaluator_id="corrosion.coupon_loss",
        evaluator_revision="0.1.1",
        evaluator_configuration=dict(
            model_id="corrosion.coupon_loss",
            base_inputs=dict(exposed_area_m2=0.01, density_kg_m3=7800.0, duration_s=86400.0),
            bindings=[dict(parameter_name="mass", input_field="mass_loss_kg", input_unit="kg")],
        ),
        parameters=[marginal("mass", -1.0, 1.0, "mg")],
        quantities=[dict(name="rate_m_s", unit="m/s")],
        sample_powers=[3, 4],
    )
    result = run_sobol(data, registry_sensitivity_evaluator(default_registry(), data))
    assert result.status == "needs_data" and result.quantities == []
    assert result.diagnostics["observed_row_status_counts"]["invalid_input"] > 0


def test_evaluator_receives_read_only_copies():
    def mutating(draws):
        draws["x"][0] = 0
        return additive(draws)

    with pytest.raises(ValueError, match="read-only"):
        run_sobol(request(sample_powers=[3, 4]), mutating)
