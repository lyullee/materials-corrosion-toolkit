"""Bounded interpolation of caller-provided remaining-strength response surfaces."""

from __future__ import annotations

import itertools
from math import prod
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive, canonical_digest


class CapacitySurfaceAxis(Contract):
    axis_id: str = Field(min_length=1)
    quantity_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    knots: tuple[float, ...] = Field(min_length=2, max_length=200)
    capacity_monotonicity: Literal["nondecreasing", "nonincreasing", "not_asserted"]

    @model_validator(mode="after")
    def ordered_knots(self):
        if np.any(np.diff(self.knots) <= 0):
            raise ValueError("capacity-surface axis knots must be strictly increasing")
        return self


class RemainingStrengthSurface(Contract):
    surface_id: str = Field(min_length=1)
    surface_revision: str = Field(min_length=1)
    component_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    response_definition: str = Field(min_length=1)
    response_unit_token: str = Field(min_length=1)
    response_direction: Literal["higher_is_stronger"]
    axes: tuple[CapacitySurfaceAxis, ...] = Field(min_length=1, max_length=5)
    response_values_axis_order_last_axis_fastest: tuple[float, ...] = Field(min_length=2, max_length=100000)
    interpolation: Literal["multilinear"] = "multilinear"
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    domain_and_monotonicity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_and_monotone(self):
        axis_ids = [row.axis_id for row in self.axes]
        if len(set(axis_ids)) != len(axis_ids):
            raise ValueError("capacity-surface axis identifiers must be unique")
        shape = tuple(len(row.knots) for row in self.axes)
        if prod(shape) != len(self.response_values_axis_order_last_axis_fastest):
            raise ValueError("capacity-surface response count must equal the rectangular grid size")
        values = np.asarray(self.response_values_axis_order_last_axis_fastest).reshape(shape)
        if np.any(values <= 0):
            raise ValueError("remaining-strength surface values must be positive")
        for index, axis in enumerate(self.axes):
            differences = np.diff(values, axis=index)
            if axis.capacity_monotonicity == "nondecreasing" and np.any(differences < 0):
                raise ValueError(f"surface is not nondecreasing on axis {axis.axis_id}")
            if axis.capacity_monotonicity == "nonincreasing" and np.any(differences > 0):
                raise ValueError(f"surface is not nonincreasing on axis {axis.axis_id}")
        return self

    @property
    def deterministic_digest(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


class FlawGeometrySample(Contract):
    sample_id: str = Field(min_length=1)
    sample_role: Literal["nominal", "uncertainty_realization"]
    component_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    coordinates: dict[str, float]
    coordinate_units: dict[str, str]
    sample_weight: Positive = 1.0
    geometry_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CallerStrengthCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    response_definition: str = Field(min_length=1)
    response_unit_token: str = Field(min_length=1)
    fail_below: float
    pass_at_or_above: float
    conservative_statistic: Literal["minimum_sample_response"] = "minimum_sample_response"
    criterion_basis: str = Field(min_length=1)
    criterion_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_thresholds(self):
        if self.fail_below <= 0 or self.pass_at_or_above <= 0:
            raise ValueError("caller strength thresholds must be positive")
        if self.fail_below > self.pass_at_or_above:
            raise ValueError("fail threshold cannot exceed pass threshold")
        return self


class RemainingStrengthEvaluationInput(Contract):
    evaluation_id: str = Field(min_length=1)
    surface: RemainingStrengthSurface
    samples: tuple[FlawGeometrySample, ...] = Field(min_length=1, max_length=10000)
    criterion: CallerStrengthCriterion
    sample_set_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    uncertainty_sampling_basis: str = Field(min_length=1)
    surface_identity_units_and_domain_reviewed: bool
    flaw_geometry_and_uncertainty_samples_reviewed: bool
    caller_criterion_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_samples(self):
        ids = [row.sample_id for row in self.samples]
        if len(set(ids)) != len(ids):
            raise ValueError("flaw geometry sample identifiers must be unique")
        return self


class InterpolatedStrengthSample(Contract):
    sample_id: str
    sample_role: Literal["nominal", "uncertainty_realization"]
    response_value: float
    response_unit_token: str
    sample_weight: float
    interpolation_brackets: dict[str, tuple[int, int]]
    geometry_source_digest: str


class RemainingStrengthEvaluationReport(Contract):
    evaluation_id: str
    status: Literal["pass", "fail", "review", "needs_data"]
    status_basis: str
    conservative_response: float | None = None
    response_unit_token: str
    governing_sample_id: str | None = None
    interpolated_samples: tuple[InterpolatedStrengthSample, ...] = ()
    unsupported_sample_ids: tuple[str, ...] = ()
    mismatch_fields: tuple[str, ...] = ()
    surface_digest: str
    input_digest: str
    report_digest: str
    qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False


def _interpolate(surface: RemainingStrengthSurface, coordinates: dict[str, float]):
    shape = tuple(len(row.knots) for row in surface.axes)
    values = np.asarray(surface.response_values_axis_order_last_axis_fastest).reshape(shape)
    brackets: list[tuple[int, int]] = []
    fractions: list[float] = []
    for axis in surface.axes:
        value = coordinates[axis.axis_id]
        knots = np.asarray(axis.knots)
        if value < knots[0] or value > knots[-1]:
            return None
        if value == knots[-1]:
            low, high, fraction = len(knots) - 2, len(knots) - 1, 1.0
        else:
            high = int(np.searchsorted(knots, value, side="right"))
            low = high - 1
            fraction = float((value - knots[low]) / (knots[high] - knots[low]))
        brackets.append((low, high))
        fractions.append(fraction)
    response = 0.0
    for corner in itertools.product((0, 1), repeat=len(surface.axes)):
        index = tuple(brackets[i][corner[i]] for i in range(len(corner)))
        weight = prod(fractions[i] if corner[i] else 1 - fractions[i] for i in range(len(corner)))
        response += weight * float(values[index])
    return response, {axis.axis_id: brackets[i] for i, axis in enumerate(surface.axes)}


def evaluate_remaining_strength_surface(
    x: RemainingStrengthEvaluationInput,
) -> RemainingStrengthEvaluationReport:
    """Interpolate inside the declared grid and apply only the caller's criterion."""

    surface = x.surface
    mismatch = []
    if x.criterion.response_definition != surface.response_definition:
        mismatch.append("response_definition")
    if x.criterion.response_unit_token != surface.response_unit_token:
        mismatch.append("response_unit_token")
    review_gates = (
        surface.domain_and_monotonicity_reviewed,
        x.surface_identity_units_and_domain_reviewed,
        x.flaw_geometry_and_uncertainty_samples_reviewed,
        x.caller_criterion_reviewed,
    )
    input_digest = canonical_digest(x.model_dump(mode="json"))
    if mismatch or not all(review_gates):
        return _report(
            x,
            "needs_data",
            "Surface, sample, criterion identities or review gates are incomplete.",
            input_digest,
            mismatch_fields=tuple(mismatch),
        )

    expected_axes = {axis.axis_id: axis.unit_token for axis in surface.axes}
    unsupported = []
    results = []
    for sample in x.samples:
        identities_match = (
            sample.component_geometry_id == surface.component_geometry_id
            and sample.material_condition_id == surface.material_condition_id
            and sample.load_case_id == surface.load_case_id
        )
        if (
            not identities_match
            or sample.coordinate_units != expected_axes
            or set(sample.coordinates) != set(expected_axes)
        ):
            unsupported.append(sample.sample_id)
            continue
        interpolated = _interpolate(surface, sample.coordinates)
        if interpolated is None:
            unsupported.append(sample.sample_id)
            continue
        value, brackets = interpolated
        results.append(
            InterpolatedStrengthSample(
                sample_id=sample.sample_id,
                sample_role=sample.sample_role,
                response_value=value,
                response_unit_token=surface.response_unit_token,
                sample_weight=sample.sample_weight,
                interpolation_brackets=brackets,
                geometry_source_digest=sample.geometry_source_digest,
            )
        )
    if unsupported:
        return _report(
            x,
            "needs_data",
            "At least one sample is outside the exact identity, unit, coordinate, or interpolation domain.",
            input_digest,
            interpolated_samples=tuple(results),
            unsupported_sample_ids=tuple(sorted(unsupported)),
        )

    governing = min(results, key=lambda row: (row.response_value, row.sample_id))
    conservative = governing.response_value
    if conservative < x.criterion.fail_below:
        status, basis = "fail", "Minimum sample response is below the caller fail threshold."
    elif conservative >= x.criterion.pass_at_or_above:
        status, basis = "pass", "Minimum sample response meets the caller pass threshold."
    else:
        status, basis = "review", "Minimum sample response lies in the caller review interval."
    return _report(
        x,
        status,
        basis,
        input_digest,
        conservative_response=conservative,
        governing_sample_id=governing.sample_id,
        interpolated_samples=tuple(results),
    )


def _report(
    x,
    status,
    basis,
    input_digest,
    *,
    conservative_response=None,
    governing_sample_id=None,
    interpolated_samples=(),
    unsupported_sample_ids=(),
    mismatch_fields=(),
):
    payload = {
        "evaluation_id": x.evaluation_id,
        "status": status,
        "status_basis": basis,
        "conservative_response": conservative_response,
        "response_unit_token": x.surface.response_unit_token,
        "governing_sample_id": governing_sample_id,
        "interpolated_samples": [row.model_dump(mode="json") for row in interpolated_samples],
        "unsupported_sample_ids": unsupported_sample_ids,
        "mismatch_fields": mismatch_fields,
        "surface_digest": x.surface.deterministic_digest,
        "input_digest": input_digest,
        "qualification_claim": False,
        "physical_validation_claim": False,
    }
    return RemainingStrengthEvaluationReport.model_validate(
        {**payload, "interpolated_samples": interpolated_samples, "report_digest": canonical_digest(payload)}
    )
