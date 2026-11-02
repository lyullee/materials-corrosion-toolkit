import json

import numpy as np
import pytest

from matintegrity.adapters import equivalent_stationary_hazard
from matintegrity.contracts import Calculation, Contract, EventProbability, RunContext
from matintegrity.data import TabulatedProperty, parse_reported_value
from matintegrity.registry import ModelRegistry, ModelSpec
from matintegrity.rules import Rule, evaluate_rules
from matintegrity.uncertainty import UniformMarginal, simulate_limit_state


def test_user_plugin_schema_and_digest():
    class Parameters(Contract):
        value: float

    registry = ModelRegistry()
    registry.register(
        ModelSpec(
            "user.example",
            Parameters,
            lambda x: Calculation(values={"answer": 2 * x.value}),
            {"answer": "1"},
            ("User model demonstration.",),
            ("user-source",),
            qualification="user_model",
        )
    )
    ctx = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    first = registry.run("user.example", {"value": 3.0}, ctx)
    assert first.values["answer"] == 6
    assert first.input_digest == registry.run("user.example", {"value": 3.0}, ctx).input_digest
    assert first.input_digest != registry.run("user.example", {"value": 4.0}, ctx).input_digest
    assert registry.describe("user.example")["input_schema"]["additionalProperties"] is False
    with pytest.raises(ValueError):
        registry.register(registry._models["user.example"])


@pytest.mark.parametrize(
    "raw,kind",
    [
        ("0.1", "exact"),
        ("<0.1", "upper_bound"),
        ("> 2", "lower_bound"),
        ("0.1 - 0.3", "interval"),
        ("A (Resistant)", "unresolved"),
        ("Boiling", "unresolved"),
    ],
)
def test_qualifiers_not_replaced_by_midpoints(raw, kind):
    parsed = parse_reported_value(raw)
    assert parsed["kind"] == kind
    if kind == "unresolved":
        assert parsed["lower"] is None and parsed["upper"] is None


def test_property_domains_and_three_valued_rules():
    table = TabulatedProperty(
        property_id="sample",
        x=[100.0, 200.0],
        y=[10.0, 20.0],
        x_unit="K",
        y_unit="J/kg/K",
        source_id="synthetic",
    )
    assert table.at(150.0) == 15.0
    with pytest.raises(ValueError):
        table.at(250.0)
    rule = Rule(
        id="t",
        field="temperature",
        operator="lt",
        expected=300.0,
        unit="K",
        source_id="user",
        rationale="declared condition",
    )
    assert evaluate_rules([rule], {}, {})["outcome"] == "unknown"
    assert evaluate_rules([rule], {"temperature": 200.0}, {"temperature": "degC"})["outcome"] == "unknown"
    assert evaluate_rules([rule], {"temperature": 200.0}, {"temperature": "K"})["outcome"] == "satisfied"


def test_probability_rate_conversion_requires_explicit_approximation():
    event = EventProbability(
        event_id="e",
        asset_id="a",
        physical_scope_id="scope",
        failure_mode="thinning",
        horizon_start_s=0.0,
        horizon_end_s=100.0,
        probability_given_survival=0.1,
        conditioning="survived initial inspection",
        model_result_digest="a" * 64,
    )
    with pytest.raises(ValueError):
        equivalent_stationary_hazard(event, stationary_hazard_approximation_declared=False)
    rate = equivalent_stationary_hazard(event, stationary_hazard_approximation_declared=True)
    assert rate["equivalent_hazard_per_s"] == pytest.approx(0.001053605156578263)
    assert rate["prism_frequency_event_compatible"] is False


def test_mc_first_crossing_and_initial_survival_conditioning():
    marginal = UniformMarginal(name="x", lower=0.0, upper=1.0)

    def evaluate(draws):
        x = draws["x"]
        return np.column_stack([x - 0.2, x - 0.6, x - 0.4])

    result = simulate_limit_state(
        [marginal], evaluate, samples=20000, seed=123, independence_declared=True, time_s=[0.0, 1.0, 2.0]
    )
    assert result["probability_of_failure_given_initial_survival"][1] == pytest.approx(0.5, abs=0.02)
    assert result["failure_counts"][2] == result["failure_counts"][1]
    json.dumps(result, allow_nan=False)
