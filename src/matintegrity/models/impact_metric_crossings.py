"""Observed-domain impact metric crossings; no fitted service-limit inference."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec
from .engineering_correlations import CorrelationRequest


class ImpactMetricPoint(Contract):
    observation_id: str = Field(min_length=1)
    temperature_K: Positive
    metric_value: Nonnegative
    source_group_id: str = Field(min_length=1)


class ImpactMetricCrossings(CorrelationRequest):
    series_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_geometry_id: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    observational_unit_description: str = Field(min_length=1)
    statistic_basis: str = Field(min_length=1)
    metric: Literal["absorbed_energy", "shear_fracture_fraction", "lateral_expansion"]
    metric_unit: Literal["J", "1", "m"]
    target_value: Nonnegative
    points: tuple[ImpactMetricPoint, ...] = Field(min_length=2, max_length=10000)
    interpolation: Literal["piecewise_linear"]

    @model_validator(mode="after")
    def reviewed_metric_series(self):
        units = {"absorbed_energy": "J", "shear_fracture_fraction": "1", "lateral_expansion": "m"}
        if self.metric_unit != units[self.metric]:
            raise ValueError("impact metric and SI/fraction unit must match exactly")
        if self.metric == "shear_fracture_fraction" and (
            self.target_value > 1 or any(p.metric_value > 1 for p in self.points)
        ):
            raise ValueError("shear fracture values must be explicit fractions, not percentages")
        if len({p.observation_id for p in self.points}) != len(self.points):
            raise ValueError("observation IDs must be unique")
        if any(
            b.temperature_K <= a.temperature_K for a, b in zip(self.points, self.points[1:], strict=False)
        ):
            raise ValueError(
                "temperatures must strictly increase; replicate reduction needs an explicit upstream statistic"
            )
        return self


def impact_metric_crossings(x: ImpactMetricCrossings) -> Calculation:
    plateau_intervals = []
    plateau_records = []
    plateau_point_indices = set()
    crossings = []
    for i, (left, right) in enumerate(zip(x.points, x.points[1:], strict=False)):
        a, b = left.metric_value, right.metric_value
        if a == b == x.target_value:
            plateau_point_indices.update((i, i + 1))
            if plateau_intervals and plateau_intervals[-1][1] == left.temperature_K:
                plateau_intervals[-1][1] = right.temperature_K
                plateau_records[-1]["observation_ids"].append(right.observation_id)
                plateau_records[-1]["source_group_ids"].append(right.source_group_id)
            else:
                plateau_intervals.append([left.temperature_K, right.temperature_K])
                plateau_records.append(
                    dict(
                        observation_ids=[left.observation_id, right.observation_id],
                        source_group_ids=[left.source_group_id, right.source_group_id],
                    )
                )
        elif a < x.target_value < b or b < x.target_value < a:
            fraction = (x.target_value - a) / (b - a)
            crossings.append(
                dict(
                    temperature_K=left.temperature_K + fraction * (right.temperature_K - left.temperature_K),
                    kind="interpolated",
                    observation_ids=[left.observation_id, right.observation_id],
                    source_group_ids=[left.source_group_id, right.source_group_id],
                )
            )
    for i, point in enumerate(x.points):
        if point.metric_value == x.target_value and i not in plateau_point_indices:
            crossings.append(
                dict(
                    temperature_K=point.temperature_K,
                    kind="observed_point",
                    observation_ids=[point.observation_id],
                    source_group_ids=[point.source_group_id],
                )
            )
    crossings.sort(key=lambda row: row["temperature_K"])
    unique = len(crossings) == 1 and not plateau_intervals
    status = "computed" if unique else "needs_data" if crossings or plateau_intervals else "out_of_scope"
    return Calculation(
        status=status,
        values=dict(
            series_id=x.series_id,
            metric=x.metric,
            material_condition_id=x.material_condition_id,
            specimen_geometry_id=x.specimen_geometry_id,
            orientation_id=x.orientation_id,
            observational_unit_description=x.observational_unit_description,
            statistic_basis=x.statistic_basis,
            interpolation=x.interpolation,
            metric_unit=x.metric_unit,
            target_value=x.target_value,
            unique_crossing_temperature_K=crossings[0]["temperature_K"] if unique else None,
            crossing_temperatures_K=[row["temperature_K"] for row in crossings],
            crossing_records=crossings,
            plateau_intervals_K=plateau_intervals,
            plateau_records=plateau_records,
            observed_temperature_domain_K=[x.points[0].temperature_K, x.points[-1].temperature_K],
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "All crossings of the declared piecewise-linear observed curve are retained; nonmonotonic data and target plateaus are not replaced by an arbitrary single temperature.",
            "Input points use the caller's declared observational/statistic basis. No replicate independence, smoothing, extrapolation, confidence interval, DBTT/FATT qualification, toughness conversion or design acceptance is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.impact_metric_crossings",
            ImpactMetricCrossings,
            impact_metric_crossings,
            {
                "series_id": "1",
                "metric": "1",
                "metric_unit": "1",
                "target_value": "caller_declared_metric_unit",
                "material_condition_id": "1",
                "specimen_geometry_id": "1",
                "orientation_id": "1",
                "observational_unit_description": "1",
                "statistic_basis": "1",
                "interpolation": "1",
                "unique_crossing_temperature_K": "K",
                "crossing_temperatures_K": "K",
                "crossing_records": "structured_record",
                "plateau_intervals_K": "K",
                "plateau_records": "structured_record",
                "observed_temperature_domain_K": "K",
                "record_sha256": "1",
            },
            (
                "One reviewed common material/geometry/orientation series, explicit point statistic, native SI/fraction metric and caller target.",
            ),
            ("observed_impact_metric_linear_crossings",),
            version="0.1.0",
            qualification="user_model",
        )
    ]
