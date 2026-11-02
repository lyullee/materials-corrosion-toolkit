import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.burst_validation import (
    BurstPressureComparison,
    BurstPressureComparisonRow,
    compare_burst_pressures,
)
from matintegrity.registry import default_registry


def row(identifier, *, partition="holdout", group="holdout-source", ratio=1.0, **overrides):
    values = dict(
        observation_id=identifier,
        physical_specimen_id=f"specimen-{identifier}",
        source_group_id=group,
        partition=partition,
        material_condition_id="steel-condition",
        geometry_id=f"geometry-{identifier}",
        load_case_id="monotonic-internal-pressure",
        observed_pressure_basis="internal_minus_external",
        predicted_pressure_basis="internal_minus_external",
        observed_burst_pressure_Pa=10e6,
        predicted_failure_pressure_Pa=10e6 * ratio,
        observation_source_sha256="a" * 64,
        prediction_input_digest=(identifier[0] * 64),
        observation_use_authorized=True,
        experimental_endpoint_reviewed=True,
        geometry_and_material_reviewed=True,
        pressure_basis_reviewed=True,
    )
    return BurstPressureComparisonRow(**(values | overrides))


def request(rows, **overrides):
    values = dict(
        comparison_id="authored-comparison",
        prediction_provider_id="user.pressure-model",
        prediction_provider_version="1.0.0",
        prediction_configuration_digest="f" * 64,
        rows=tuple(rows),
        physical_specimen_independence_reviewed=True,
        source_group_partitioning_reviewed=True,
        prediction_frozen_before_evaluation=True,
    )
    return BurstPressureComparison(**(values | overrides))


def test_partition_metrics_are_exact_and_registry_composable():
    inputs = request(
        (
            row("a", partition="calibration", group="calibration-source", ratio=1.0),
            row("b", ratio=0.8),
            row("c", ratio=1.25),
        )
    )
    result = compare_burst_pressures(inputs)
    holdout = result.values["partition_summaries"]["holdout"]
    assert result.status == "computed"
    assert holdout["observations"] == 2
    assert holdout["arithmetic_mean_predicted_to_observed_ratio"] == pytest.approx(1.025)
    assert holdout["median_predicted_to_observed_ratio"] == pytest.approx(1.025)
    assert holdout["mean_absolute_relative_error"] == pytest.approx(0.225)
    assert holdout["root_mean_square_log_error"] == pytest.approx(
        math.sqrt((math.log(0.8) ** 2 + math.log(1.25) ** 2) / 2)
    )
    registered = default_registry().run(
        "structural.burst_pressure_comparison",
        inputs,
        RunContext(asset_id="synthetic", location_id="pipe", time_basis="test endpoint"),
    )
    assert registered.status == "computed"
    assert registered.values["observation_count"] == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"physical_specimen_independence_reviewed": False},
        {"source_group_partitioning_reviewed": False},
        {"prediction_frozen_before_evaluation": False},
    ],
)
def test_global_review_gates_do_not_produce_comparison(overrides):
    result = compare_burst_pressures(request((row("a"),), **overrides))
    assert result.status == "needs_data"
    assert result.values == {}


@pytest.mark.parametrize(
    "overrides",
    [
        {"physical_specimen_id": None},
        {"observation_use_authorized": False},
        {"experimental_endpoint_reviewed": False},
        {"geometry_and_material_reviewed": False},
        {"pressure_basis_reviewed": False},
        {"observed_pressure_basis": "unresolved", "predicted_pressure_basis": "unresolved"},
        {"predicted_pressure_basis": "gauge_internal"},
    ],
)
def test_row_review_gates_do_not_produce_comparison(overrides):
    kwargs = {}
    if overrides.get("physical_specimen_id", "present") is None:
        kwargs["physical_specimen_independence_reviewed"] = False
    result = compare_burst_pressures(request((row("a", **overrides),), **kwargs))
    assert result.status == "needs_data"


def test_specimen_reuse_source_leakage_and_absent_evaluation_are_rejected():
    with pytest.raises(ValidationError, match="physical specimen"):
        request(
            (
                row("a", physical_specimen_id="same"),
                row("b", physical_specimen_id="same"),
            )
        )
    with pytest.raises(ValidationError, match="source group"):
        request(
            (
                row("a", partition="calibration", group="shared"),
                row("b", partition="holdout", group="shared"),
            )
        )
    with pytest.raises(ValidationError, match="evaluation row"):
        request((row("a", partition="calibration", group="calibration-only"),))


def test_contract_is_strict():
    with pytest.raises(ValidationError):
        BurstPressureComparisonRow(**(row("a").model_dump() | {"unexpected": "field"}))
