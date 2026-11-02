import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.impact_metric_crossings import (
    ImpactMetricCrossings,
    ImpactMetricPoint,
    impact_metric_crossings,
    specifications,
)
from matintegrity.registry import ModelRegistry


def payload(values=(0.1, 0.6, 0.9), **changes):
    points = tuple(
        ImpactMetricPoint(
            observation_id=f"p{i}", temperature_K=t, metric_value=value, source_group_id="synthetic-series"
        )
        for i, (t, value) in enumerate(zip((300.0, 350.0, 400.0), values, strict=True))
    )
    data = (
        dict(
            series_id="series-1",
            material_condition_id="condition-1",
            specimen_geometry_id="geometry-1",
            orientation_id="orientation-1",
            observational_unit_description="one caller-declared representative point per temperature",
            statistic_basis="synthetic values, no replicate independence inferred",
            metric="shear_fracture_fraction",
            metric_unit="1",
            target_value=0.5,
            points=points,
            interpolation="piecewise_linear",
        )
        | changes
    )
    serialized = ImpactMetricCrossings.model_construct(**data).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(serialized)
    return ImpactMetricCrossings(
        **data,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="authored impact points",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "metric,unit,values,target",
    [
        ("absorbed_energy", "J", (10.0, 60.0, 90.0), 50.0),
        ("shear_fracture_fraction", "1", (0.1, 0.6, 0.9), 0.5),
        ("lateral_expansion", "m", (0.001, 0.006, 0.009), 0.005),
    ],
)
def test_separate_metric_units_preserve_the_same_observed_crossing(metric, unit, values, target):
    result = impact_metric_crossings(payload(values, metric=metric, metric_unit=unit, target_value=target))
    assert result.status == "computed"
    assert result.values["unique_crossing_temperature_K"] == pytest.approx(340.0)
    assert result.values["crossing_records"][0]["observation_ids"] == ["p0", "p1"]


def test_nonmonotonic_series_preserves_multiple_crossings():
    result = impact_metric_crossings(payload((0.1, 0.9, 0.1)))
    assert result.status == "needs_data"
    assert result.values["crossing_temperatures_K"] == [325.0, 375.0]
    assert result.values["unique_crossing_temperature_K"] is None


def test_target_plateau_is_an_interval_without_arbitrary_point_selection():
    result = impact_metric_crossings(payload((0.5, 0.5, 0.5)))
    assert result.status == "needs_data"
    assert result.values["plateau_intervals_K"] == [[300.0, 400.0]]
    assert result.values["plateau_records"][0]["observation_ids"] == ["p0", "p1", "p2"]
    assert result.values["crossing_temperatures_K"] == []


def test_exact_target_point_is_not_counted_twice():
    result = impact_metric_crossings(payload((0.1, 0.5, 0.9)))
    assert result.status == "computed"
    assert result.values["crossing_temperatures_K"] == [350.0]
    assert result.values["crossing_records"][0]["kind"] == "observed_point"


def test_outside_target_is_not_extrapolated():
    result = impact_metric_crossings(payload(target_value=0.95))
    assert result.status == "out_of_scope"
    assert result.values["unique_crossing_temperature_K"] is None


def test_fraction_percentage_and_metric_unit_mismatches_are_rejected():
    with pytest.raises(ValueError, match="fractions"):
        payload((10.0, 60.0, 90.0))
    with pytest.raises(ValueError, match="unit must match"):
        payload(metric_unit="J")


def test_repeated_temperature_or_observation_identity_requires_upstream_review():
    x = payload()
    duplicate = x.points[1].model_copy(update={"temperature_K": 300.0})
    with pytest.raises(ValueError, match="strictly increase"):
        payload(points=(x.points[0], duplicate, x.points[2]))
    with pytest.raises(ValueError, match="IDs must be unique"):
        payload(points=(x.points[0], x.points[0], x.points[2]))


def test_public_python_json_exchange_preserves_scope_and_all_crossings():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    context = RunContext(asset_id="synthetic", location_id="specimen", time_basis="test")
    x = payload()
    direct = registry.run("inspection.impact_metric_crossings", x, context)
    serialized = registry.run_json("inspection.impact_metric_crossings", x.model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()
    assert direct.values["material_condition_id"] == x.material_condition_id
    assert direct.values["statistic_basis"] == x.statistic_basis
