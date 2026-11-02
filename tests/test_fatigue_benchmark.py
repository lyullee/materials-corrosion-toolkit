import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.fatigue_benchmark import (
    CyclicResponseRelativeError,
    CyclicResponseSeries,
    DynamicModulusDropEndpoint,
    FatigueLifeRmsle,
    cyclic_response_relative_error,
    dynamic_modulus_drop_endpoint,
    fatigue_life_rmsle,
)
from matintegrity.registry import default_registry


def _series(experiment_id="exp-1"):
    return CyclicResponseSeries(
        experiment_id=experiment_id,
        cycle=[1, 10],
        observed_mean=[10.0, 10.0],
        predicted_mean=[11.0, 8.0],
        observed_amplitude=[20.0, 20.0],
        predicted_amplitude=[24.0, 18.0],
        mean_normalizer=10.0,
        amplitude_normalizer=20.0,
    )


def test_cyclic_response_metric_averages_within_then_across_experiments():
    exact = CyclicResponseSeries(
        experiment_id="exp-2",
        cycle=[1],
        observed_mean=[3.0],
        predicted_mean=[3.0],
        observed_amplitude=[4.0],
        predicted_amplitude=[4.0],
        mean_normalizer=3.0,
        amplitude_normalizer=4.0,
    )
    result = cyclic_response_relative_error(CyclicResponseRelativeError(series=[_series(), exact]))
    assert result.values["experiment_errors"][0]["weighted_relative_error"] == pytest.approx(0.15)
    assert result.values["aggregate_weighted_relative_error"] == pytest.approx(0.075)
    assert result.values["experiment_count"] == 2


@pytest.mark.parametrize(
    "update",
    [
        {"cycle": [2, 1]},
        {"predicted_mean": [1.0]},
        {"observed_amplitude": [-1.0, 2.0]},
        {"mean_normalizer": 0.0},
    ],
)
def test_cyclic_response_series_rejects_ambiguous_numeric_contracts(update):
    payload = _series().model_dump()
    payload.update(update)
    with pytest.raises(ValidationError):
        CyclicResponseSeries(**payload)


def test_cyclic_response_metric_requires_unique_ids_and_unit_weight_sum():
    with pytest.raises(ValidationError):
        CyclicResponseRelativeError(series=[_series(), _series()])
    with pytest.raises(ValidationError):
        CyclicResponseRelativeError(series=[_series()], mean_weight=0.7, amplitude_weight=0.4)


def test_life_rmsle_preserves_signed_case_residuals():
    result = fatigue_life_rmsle(
        FatigueLifeRmsle(
            case_id=["over", "under"],
            observed_cycles=[100.0, 100.0],
            predicted_cycles=[1000.0, 10.0],
        )
    )
    assert result.values["root_mean_square_log_error"] == pytest.approx(1.0)
    assert [row["log_residual"] for row in result.values["case_log_residuals"]] == [1.0, -1.0]


def test_life_rmsle_rejects_censoring_placeholders_and_duplicate_cases():
    with pytest.raises(ValidationError):
        FatigueLifeRmsle(case_id=["a"], observed_cycles=[0.0], predicted_cycles=[1.0])
    with pytest.raises(ValidationError):
        FatigueLifeRmsle(case_id=["a", "a"], observed_cycles=[1.0, 2.0], predicted_cycles=[1.0, 2.0])


def _endpoint(**updates):
    payload = dict(
        test_id="test-1",
        cycle=[1.0, 5.0, 10.0],
        compressive_dynamic_modulus_Pa=[100.0, 95.0, 85.0],
        reference_dynamic_modulus_Pa=100.0,
        drop_fraction_threshold=0.1,
        crossing_policy="first_observed_sample",
        observation_window_closed=True,
    )
    payload.update(updates)
    return DynamicModulusDropEndpoint(**payload)


def test_dynamic_modulus_endpoint_distinguishes_sample_and_interpolated_crossing():
    sampled = dynamic_modulus_drop_endpoint(_endpoint())
    interpolated = dynamic_modulus_drop_endpoint(_endpoint(crossing_policy="linear_between_samples"))
    assert sampled.values["endpoint_cycle"] == 10.0
    assert sampled.values["crossing_bracket_cycles"] is None
    assert interpolated.values["endpoint_cycle"] == pytest.approx(7.5)
    assert interpolated.values["crossing_bracket_cycles"] == [5.0, 10.0]
    assert sampled.values["threshold_dynamic_modulus_Pa"] == pytest.approx(90.0)


def test_dynamic_modulus_endpoint_preserves_censoring_and_open_window():
    no_crossing = dict(compressive_dynamic_modulus_Pa=[100.0, 98.0, 95.0])
    closed = dynamic_modulus_drop_endpoint(_endpoint(**no_crossing))
    opened = dynamic_modulus_drop_endpoint(_endpoint(**no_crossing, observation_window_closed=False))
    assert closed.status == "computed"
    assert closed.values["endpoint_role"] == "right_censored_no_crossing"
    assert opened.status == "needs_data"
    assert opened.values["endpoint_role"] == "not_reached_open_window"


def test_dynamic_modulus_endpoint_rejects_unsorted_or_misaligned_trace():
    with pytest.raises(ValidationError):
        _endpoint(cycle=[1.0, 1.0, 2.0])
    with pytest.raises(ValidationError):
        _endpoint(compressive_dynamic_modulus_Pa=[100.0, 90.0])


def test_fatigue_benchmark_models_are_registered():
    registry = default_registry()
    assert {
        "fatigue.cyclic_response_relative_error",
        "fatigue.life_rmsle",
        "fatigue.dynamic_modulus_drop_endpoint",
    } <= set(registry.list_models())
    result = registry.run(
        "fatigue.life_rmsle",
        {
            "case_id": ["a"],
            "observed_cycles": [100.0],
            "predicted_cycles": [100.0],
        },
        RunContext(asset_id="benchmark", location_id="laboratory", time_basis="declared cycles"),
    )
    assert result.values["root_mean_square_log_error"] == 0.0
    assert math.isfinite(result.values["root_mean_square_log_error"])
