"""Synthetic, observed-domain metric crossings with explicit units and provenance."""

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.impact_metric_crossings import ImpactMetricCrossings, ImpactMetricPoint
from matintegrity.registry import default_registry


def sample_requests():
    requests = []
    for metric, unit, values, target in (
        ("absorbed_energy", "J", (10.0, 60.0, 90.0), 50.0),
        ("shear_fracture_fraction", "1", (0.1, 0.6, 0.9), 0.5),
        ("lateral_expansion", "m", (0.001, 0.006, 0.009), 0.005),
    ):
        points = tuple(
            ImpactMetricPoint(
                observation_id=f"p{i}", temperature_K=t, metric_value=value, source_group_id="authored-series"
            )
            for i, (t, value) in enumerate(zip((300.0, 350.0, 400.0), values, strict=True))
        )
        data = dict(
            series_id=f"synthetic-{metric}",
            material_condition_id="synthetic-condition",
            specimen_geometry_id="synthetic-geometry",
            orientation_id="synthetic-orientation",
            observational_unit_description="one representative point per temperature",
            statistic_basis="synthetic point values, not specimen measurements",
            metric=metric,
            metric_unit=unit,
            target_value=target,
            points=points,
            interpolation="piecewise_linear",
        )
        serialized = ImpactMetricCrossings.model_construct(**data).model_dump(mode="json", exclude={"basis"})
        digest = canonical_digest(serialized)
        inputs = ImpactMetricCrossings(
            **data,
            basis=dict(
                source_id="authored",
                revision="1",
                license_id="authored-example",
                record_sha256=digest,
                applicability_and_units_reviewed=True,
                computational_use_authorized=True,
                evidence=(
                    dict(
                        source_id="authored",
                        origin="synthetic",
                        citation="synthetic metric series",
                        license_id="authored-example",
                        sha256=digest,
                    ),
                ),
            ),
        )
        requests.append(("inspection.impact_metric_crossings", inputs))
    return requests


if __name__ == "__main__":
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="specimen", time_basis="example")
    for model_id, inputs in sample_requests():
        print(registry.run(model_id, inputs, context).model_dump_json(indent=2))
