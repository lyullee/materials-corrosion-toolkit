import json
from pathlib import Path

import pytest

from matintegrity import evaluate
from matintegrity.adapters import monitoring_record, probability_event
from matintegrity.contracts import Calculation, Contract, RunContext
from matintegrity.registry import ModelRegistry, ModelSpec

CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="age seconds")


def event(result, **extra):
    return probability_event(
        result,
        event_id="synthetic",
        physical_scope_id="one-scope",
        failure_mode="declared-first-failure",
        horizon_start_s=20.0,
        horizon_end_s=30.0,
        conditioning="survived to age 20 s in declared population",
        **extra,
    )


def test_weibull_event_preserves_period_and_rejects_a_different_age_clock():
    result = evaluate(
        "reliability.weibull_interval",
        dict(shape=2.0, scale_s=100.0, current_age_s=20.0, horizon_s=10.0),
        CONTEXT,
    )
    converted = event(result)
    assert converted.probability_given_survival == result.values["probability_given_survival"]
    with pytest.raises(ValueError, match="age clock"):
        probability_event(
            result,
            event_id="wrong",
            physical_scope_id="one",
            failure_mode="first",
            horizon_start_s=0.0,
            horizon_end_s=10.0,
            conditioning="wrong clock",
        )


def test_period_clock_tolerance_tracks_the_interval_instead_of_large_absolute_age():
    result = evaluate(
        "reliability.weibull_interval",
        dict(shape=1.0, scale_s=1e12, current_age_s=1e10, horizon_s=10.0),
        CONTEXT,
    )
    with pytest.raises(ValueError, match="age clock"):
        probability_event(
            result,
            event_id="wrong-clock",
            physical_scope_id="one",
            failure_mode="first",
            horizon_start_s=1e10 + 0.001,
            horizon_end_s=1e10 + 10,
            conditioning="deliberately shifted clock",
        )


def test_spatial_probability_and_detection_cannot_be_relabelled_as_period_failure():
    inputs = json.loads(
        (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
    )["models"]
    result = evaluate("corrosion.gumbel_area_maximum", inputs["corrosion.gumbel_area_maximum"], CONTEXT)
    with pytest.raises(ValueError, match="first-failure"):
        event(result, probability_key="area_depth_exceedance_probability")
    record = monitoring_record(result)
    assert (
        record["probability_semantics"]["area_depth_exceedance_probability"]
        == "spatial_size_exceedance_at_one_exposure"
    )
    assert (
        record["inputs"]["exposure_condition_id"]
        == inputs["corrosion.gumbel_area_maximum"]["exposure_condition_id"]
    )
    record["values"]["area_depth_exceedance_probability"] = -1
    record["probability_semantics"].clear()
    assert result.values["area_depth_exceedance_probability"] >= 0
    assert (
        result.probability_semantics["area_depth_exceedance_probability"]
        == "spatial_size_exceedance_at_one_exposure"
    )
    result = evaluate("inspection.logistic_pod", inputs["inspection.logistic_pod"], CONTEXT)
    with pytest.raises(ValueError, match="first-failure"):
        event(result, probability_key="probability_of_detection")


def test_unknown_user_probability_requires_an_explicit_model_declaration():
    class Input(Contract):
        value: float

    registry = ModelRegistry()
    spec = ModelSpec(
        "user.probability",
        Input,
        lambda x: Calculation(values={"probability_given_survival": x.value}),
        {"probability_given_survival": "1"},
        ("Caller-reviewed synthetic period model.",),
        ("synthetic",),
        qualification="user_model",
    )
    registry.register(spec)
    with pytest.raises(ValueError, match="first-failure"):
        event(registry.run(spec.model_id, dict(value=0.1), CONTEXT))
    registry.register(
        ModelSpec(
            "user.scoped",
            Input,
            spec.evaluator,
            spec.units,
            spec.assumptions,
            spec.source_ids,
            qualification="user_model",
            probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
        )
    )
    assert event(registry.run("user.scoped", dict(value=0.1), CONTEXT)).probability_given_survival == 0.1
    with pytest.raises(ValueError, match="dimensionless"):
        registry.register(
            ModelSpec(
                "user.invalid",
                Input,
                spec.evaluator,
                {"probability_given_survival": "m"},
                spec.assumptions,
                spec.source_ids,
                probability_semantics={"probability_given_survival": "conditional_first_failure_in_period"},
            )
        )
