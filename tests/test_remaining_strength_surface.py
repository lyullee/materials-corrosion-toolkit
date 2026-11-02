import pytest
from pydantic import ValidationError

from matintegrity.remaining_strength_surface import (
    CallerStrengthCriterion,
    CapacitySurfaceAxis,
    FlawGeometrySample,
    RemainingStrengthEvaluationInput,
    RemainingStrengthSurface,
    evaluate_remaining_strength_surface,
)

E = {"source_id": "caller", "origin": "user_declared", "citation": "caller surface"}
D = "c" * 64


def surface(**updates):
    value = {
        "surface_id": "surface-1",
        "surface_revision": "1",
        "component_geometry_id": "pipe-1",
        "material_condition_id": "material-1",
        "load_case_id": "pressure-1",
        "response_definition": "caller remaining-strength capacity",
        "response_unit_token": "Pa",
        "response_direction": "higher_is_stronger",
        "axes": (
            CapacitySurfaceAxis(
                axis_id="depth_fraction",
                quantity_definition="maximum local depth over reference wall",
                unit_token="1",
                knots=(0.1, 0.5),
                capacity_monotonicity="nonincreasing",
            ),
            CapacitySurfaceAxis(
                axis_id="length_ratio",
                quantity_definition="caller flaw length ratio",
                unit_token="1",
                knots=(1.0, 3.0),
                capacity_monotonicity="nonincreasing",
            ),
        ),
        "response_values_axis_order_last_axis_fastest": (90.0, 70.0, 50.0, 30.0),
        "provider_id": "caller-provider",
        "provider_revision": "1",
        "provider_configuration_digest": D,
        "provider_result_digest": D,
        "domain_and_monotonicity_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return RemainingStrengthSurface(**value)


def sample(sample_id, depth, length):
    return FlawGeometrySample(
        sample_id=sample_id,
        sample_role="uncertainty_realization",
        component_geometry_id="pipe-1",
        material_condition_id="material-1",
        load_case_id="pressure-1",
        coordinates={"depth_fraction": depth, "length_ratio": length},
        coordinate_units={"depth_fraction": "1", "length_ratio": "1"},
        sample_weight=1.0,
        geometry_source_digest=D,
        evidence=(E,),
    )


def criterion(fail=40.0, passed=70.0):
    return CallerStrengthCriterion(
        criterion_id="criterion-1",
        response_definition="caller remaining-strength capacity",
        response_unit_token="Pa",
        fail_below=fail,
        pass_at_or_above=passed,
        criterion_basis="caller decision rule",
        criterion_source_digest=D,
        evidence=(E,),
    )


def inputs(samples, **updates):
    value = {
        "evaluation_id": "evaluation-1",
        "surface": surface(),
        "samples": samples,
        "criterion": criterion(),
        "sample_set_digest": D,
        "uncertainty_sampling_basis": "caller-provided reviewed realizations",
        "surface_identity_units_and_domain_reviewed": True,
        "flaw_geometry_and_uncertainty_samples_reviewed": True,
        "caller_criterion_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return RemainingStrengthEvaluationInput(**value)


def test_multilinear_interpolation_and_conservative_review_summary():
    result = evaluate_remaining_strength_surface(
        inputs((sample("less-severe", 0.1, 1.0), sample("governing", 0.3, 2.0)))
    )
    assert result.status == "review"
    assert result.conservative_response == pytest.approx(60.0)
    assert result.governing_sample_id == "governing"
    assert result.qualification_claim is False
    assert result == evaluate_remaining_strength_surface(
        inputs((sample("less-severe", 0.1, 1.0), sample("governing", 0.3, 2.0)))
    )


def test_caller_thresholds_produce_pass_and_fail_without_builtin_limits():
    item = inputs((sample("one", 0.3, 2.0),))
    passed = evaluate_remaining_strength_surface(item.model_copy(update={"criterion": criterion(20, 50)}))
    failed = evaluate_remaining_strength_surface(item.model_copy(update={"criterion": criterion(70, 80)}))
    assert (passed.status, failed.status) == ("pass", "fail")


def test_extrapolation_and_identity_mismatch_are_needs_data_not_clipped():
    outside = evaluate_remaining_strength_surface(inputs((sample("outside", 0.8, 2.0),)))
    assert outside.status == "needs_data"
    assert outside.unsupported_sample_ids == ("outside",)
    wrong = sample("wrong", 0.2, 2.0).model_copy(update={"component_geometry_id": "other"})
    assert evaluate_remaining_strength_surface(inputs((wrong,))).status == "needs_data"


def test_surface_shape_and_declared_monotonicity_are_strict():
    with pytest.raises(ValidationError, match="grid size"):
        surface(response_values_axis_order_last_axis_fastest=(1.0, 2.0))
    with pytest.raises(ValidationError, match="not nonincreasing"):
        surface(response_values_axis_order_last_axis_fastest=(30.0, 70.0, 50.0, 90.0))
