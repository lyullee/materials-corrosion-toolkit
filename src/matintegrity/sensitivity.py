"""Independent-input Sobol analysis with portable designs and explicit numerical quality."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, Any, Literal

import numpy as np
from pint.errors import PintError
from pydantic import Field, field_validator, model_validator

from .contracts import (
    Contract,
    Evidence,
    Fraction,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
    check_finite,
)
from .units import _UNITS, convert

ROW_STATES = ("computed", "needs_data", "out_of_scope", "invalid_input", "invalid_output")
SENSITIVITY_SOURCE_IDS = (
    "scipy_sobol",
    "scipy_qmc_sobol",
    "scipy_rqmc_error",
    "sobol_variance_indices",
    "sobol_design_quality_contract",
)
RowState = Literal["computed", "needs_data", "out_of_scope", "invalid_input", "invalid_output"]
PointIndex = Annotated[int, Field(ge=0)]


def _validate_unit(value):
    try:
        convert(0.0, value, value)
    except PintError as error:
        raise ValueError("unrecognized physical unit") from error
    return value


class SensitivityMarginal(Contract):
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    family: Literal["uniform", "normal", "lognormal", "quantile_table"]
    lower: float | None = None
    upper: float | None = None
    mean: float | None = None
    standard_deviation: Positive | None = None
    log_mean: float | None = None
    log_standard_deviation: Positive | None = None
    reference_value: Positive | None = None
    probabilities: list[Fraction] | None = None
    quantiles: list[float] | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def distribution_fields(self):
        required = {
            "uniform": {"lower", "upper"},
            "normal": {"mean", "standard_deviation"},
            "lognormal": {"log_mean", "log_standard_deviation", "reference_value"},
            "quantile_table": {"probabilities", "quantiles"},
        }[self.family]
        fields = {
            "lower",
            "upper",
            "mean",
            "standard_deviation",
            "log_mean",
            "log_standard_deviation",
            "reference_value",
            "probabilities",
            "quantiles",
        }
        if {name for name in fields if getattr(self, name) is not None} != required:
            raise ValueError("supply exactly the fields belonging to the selected marginal family")
        _validate_unit(self.unit)
        if self.family == "uniform" and self.upper <= self.lower:
            raise ValueError("uniform bounds must be strictly ordered")
        if self.family == "lognormal" and _UNITS.Quantity(0, self.unit).to_base_units().magnitude != 0:
            raise ValueError(
                "a logarithmic ratio requires a multiplicative unit, such as kelvin rather than Celsius"
            )
        if self.family == "quantile_table":
            p, q = self.probabilities, self.quantiles
            if len(p) < 2 or len(q) != len(p) or p[0] != 0 or p[-1] != 1:
                raise ValueError("quantile table needs aligned endpoints at probabilities zero and one")
            if any(b <= a for a, b in zip(p[:-1], p[1:], strict=True)) or any(
                b < a for a, b in zip(q[:-1], q[1:], strict=True)
            ):
                raise ValueError("probabilities increase strictly; quantiles cannot decrease")
        return self


class SensitivityQuantity(Contract):
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    repeat_absolute_tolerance: Nonnegative = 0.0
    repeat_relative_tolerance: Nonnegative = 0.0

    @field_validator("unit")
    @classmethod
    def valid_unit(cls, value):
        return _validate_unit(value)


class SobolRequest(Contract):
    schema_version: Literal["matintegrity.sobol_request.v1"] = "matintegrity.sobol_request.v1"
    analysis_id: str = Field(min_length=1)
    context: RunContext
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration: dict[str, Any] = Field(default_factory=dict)
    parameters: list[SensitivityMarginal] = Field(min_length=1, max_length=64)
    quantities: list[SensitivityQuantity] = Field(min_length=1, max_length=32)
    sample_powers: list[int] = Field(default_factory=lambda: [8, 10, 12], min_length=2, max_length=8)
    scrambles: int = Field(default=8, ge=4, le=32)
    seed: int = Field(ge=0, le=2**53 - 1)
    independence_declared: bool
    deterministic_response_declared: bool
    confidence_level: float = Field(default=0.95, gt=0, le=0.999)
    refinement_absolute_tolerance: float = Field(default=0.03, gt=0, le=1)
    confidence_half_width_tolerance: float = Field(default=0.03, gt=0, le=1)
    maximum_model_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    repeat_check_points: int = Field(default=8, ge=1, le=32)

    @field_validator("evaluator_configuration")
    @classmethod
    def finite_configuration(cls, value):
        check_finite(value)
        canonical_digest(value)
        return value

    @model_validator(mode="after")
    def unique_and_ordered(self):
        if len({p.name for p in self.parameters}) != len(self.parameters) or len(
            {q.name for q in self.quantities}
        ) != len(self.quantities):
            raise ValueError("parameter and quantity names must each be unique")
        if any(p < 3 or p > 18 for p in self.sample_powers) or any(
            b <= a for a, b in zip(self.sample_powers[:-1], self.sample_powers[1:], strict=True)
        ):
            raise ValueError("sample powers must increase strictly between three and eighteen")
        return self


class SobolMatrixPair(Contract):
    replicate_index: int = Field(ge=0)
    a: list[list[float]]
    b: list[list[float]]


class SobolDesign(Contract):
    schema_version: Literal["matintegrity.sobol_design.v1"] = "matintegrity.sobol_design.v1"
    request: SobolRequest
    matrices: list[SobolMatrixPair]
    generator_metadata: dict[str, str]
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class SobolInputBatch(Contract):
    design_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    replicate_index: int = Field(ge=0)
    block_id: str
    point_indices: list[PointIndex] = Field(min_length=1)
    parameters: dict[str, list[float]] = Field(min_length=1)
    parameter_units: dict[str, str] = Field(min_length=1)
    repeat: bool = False

    @model_validator(mode="after")
    def aligned(self):
        if self.parameter_units.keys() != self.parameters.keys():
            raise ValueError("each batch parameter requires its declared native unit")
        for unit in self.parameter_units.values():
            _validate_unit(unit)
        if len(set(self.point_indices)) != len(self.point_indices) or any(
            len(v) != len(self.point_indices) for v in self.parameters.values()
        ):
            raise ValueError("batch parameter values and unique point identities must align")
        return self


class SobolEvaluationBatch(Contract):
    design_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    replicate_index: int = Field(ge=0)
    block_id: str
    point_indices: list[PointIndex] = Field(min_length=1)
    values: list[list[float | None]]
    row_status: list[RowState]
    repeat: bool = False

    @model_validator(mode="after")
    def aligned(self):
        if len(self.values) != len(self.point_indices) or len(self.row_status) != len(self.values):
            raise ValueError("evaluation values, point identities and states must align")
        if len(set(self.point_indices)) != len(self.point_indices) or any(i < 0 for i in self.point_indices):
            raise ValueError("point indices must be unique and nonnegative within a batch")
        if any(
            state == "computed" and any(v is None for v in row)
            for state, row in zip(self.row_status, self.values, strict=True)
        ):
            raise ValueError("computed rows cannot contain missing quantities")
        return self


class SobolEvaluations(Contract):
    schema_version: Literal["matintegrity.sobol_evaluations.v1"] = "matintegrity.sobol_evaluations.v1"
    design_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    responses: list[SobolEvaluationBatch]
    runtime_metadata: dict[str, str]
    content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class SobolLevelEstimate(Contract):
    base_samples: int
    first_order: list[float] | None
    total_order: list[float] | None
    first_order_half_width: list[float] | None
    total_order_half_width: list[float] | None
    first_order_replicates: list[list[float]] | None
    total_order_replicates: list[list[float]] | None
    normalized_variance_by_replicate: list[float]


class SobolQuantityResult(Contract):
    name: str
    response_unit: str
    index_unit: Literal["1"] = "1"
    status: Literal["estimated", "undefined_or_unresolved_variance"]
    precision_criteria_satisfied: bool
    refinement_maximum_change: float | None
    theoretical_bounds_diagnostic_passed: bool | None
    levels: list[SobolLevelEstimate]


class SobolReport(Contract):
    schema_version: Literal["matintegrity.sobol_report.v1"] = "matintegrity.sobol_report.v1"
    analysis_id: str
    status: Literal["computed", "needs_data"]
    precision_status: Literal["criteria_met", "sampling_precision_unresolved", "not_evaluable"]
    context: RunContext
    evaluator_id: str
    evaluator_revision: str
    request_digest: str
    design_digest: str
    evaluations_digest: str
    parameter_names: list[str]
    quantities: list[SobolQuantityResult]
    diagnostics: dict[str, Any]
    runtime_metadata: dict[str, str]
    notes: tuple[str, ...]
    source_ids: tuple[str, ...] = SENSITIVITY_SOURCE_IDS
    qualification: Literal["numerical_sensitivity_not_physical_validation"] = (
        "numerical_sensitivity_not_physical_validation"
    )

    @field_validator("diagnostics")
    @classmethod
    def finite_diagnostics(cls, value):
        check_finite(value)
        canonical_digest(value)
        return value


@dataclass(frozen=True)
class SensitivityBatchResult:
    values: np.ndarray
    row_status: tuple[str, ...]


def _runtime():
    from . import __version__

    result = {name: version(name) for name in ("numpy", "scipy")}
    try:
        result["matintegrity"] = version("materials-corrosion-toolkit")
    except PackageNotFoundError:
        result["matintegrity"] = __version__
    return result


def _request_budget(request):
    count, dimensions = 2 ** request.sample_powers[-1], len(request.parameters)
    evaluations = request.scrambles * ((dimensions + 2) * count + min(request.repeat_check_points, count))
    if evaluations > request.maximum_model_evaluations:
        raise ValueError("requested design exceeds the declared model-evaluation budget")
    if (
        2 * request.scrambles * count * dimensions > 2_000_000
        or request.scrambles * (dimensions + 2) * count * len(request.quantities) > 4_000_000
    ):
        raise ValueError("requested design/response exceeds the explicit stored-value limit")
    return count, dimensions


def _marginal_values(marginal, probability):
    from scipy.special import ndtri

    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        if marginal.family == "uniform":
            # Convex interpolation avoids overflowing an otherwise finite interval width.
            values = (1 - probability) * marginal.lower + probability * marginal.upper
        elif marginal.family == "normal":
            values = marginal.mean + marginal.standard_deviation * ndtri(probability)
        elif marginal.family == "lognormal":
            values = np.exp(
                math.log(marginal.reference_value)
                + marginal.log_mean
                + marginal.log_standard_deviation * ndtri(probability)
            )
            if np.any(values == 0):
                raise ValueError("a positive lognormal draw underflowed; use a reviewed bounded marginal")
        else:
            values = np.interp(probability, marginal.probabilities, marginal.quantiles)
    if not np.all(np.isfinite(values)):
        raise ValueError(
            "marginal transform produced an unrepresentable draw; no clipping or tail truncation is applied"
        )
    return values


def create_sobol_design(request: SobolRequest) -> SobolDesign:
    """Generate paired randomized Sobol inputs; preserve native-unit matrices for workers."""
    from scipy.stats import qmc

    if not request.independence_declared or not request.deterministic_response_declared:
        raise ValueError("independent marginals and a deterministic response require explicit declarations")
    count, dimensions = _request_budget(request)
    pairs = []
    for index, seed in enumerate(np.random.SeedSequence(request.seed).spawn(request.scrambles)):
        probabilities = qmc.Sobol(
            d=2 * dimensions, scramble=True, bits=52, rng=np.random.default_rng(seed)
        ).random_base2(request.sample_powers[-1])
        a = np.column_stack(
            [_marginal_values(m, probabilities[:, i]) for i, m in enumerate(request.parameters)]
        )
        b = np.column_stack(
            [_marginal_values(m, probabilities[:, dimensions + i]) for i, m in enumerate(request.parameters)]
        )
        pairs.append(SobolMatrixPair(replicate_index=index, a=a.tolist(), b=b.tolist()))
    payload = dict(
        schema_version="matintegrity.sobol_design.v1",
        request=request.model_dump(mode="json"),
        matrices=[p.model_dump(mode="json") for p in pairs],
        generator_metadata=dict(
            _runtime(), algorithm="scipy_qmc_sobol_2d_scrambled_bits52_v1", mixing="A_with_one_column_from_B"
        ),
    )
    return SobolDesign.model_validate_json(
        json.dumps(dict(payload, content_digest=canonical_digest(payload)))
    )


def _verify_design(design):
    if not isinstance(design, SobolDesign):
        raise TypeError("a validated SobolDesign is required")
    request = design.request
    _request_budget(request)
    if canonical_digest(design.model_dump(mode="json", exclude={"content_digest"})) != design.content_digest:
        raise ValueError("design content digest mismatch")
    if not request.independence_declared or not request.deterministic_response_declared:
        raise ValueError("independent deterministic analysis is not declared")
    if (
        design.generator_metadata.get("algorithm") != "scipy_qmc_sobol_2d_scrambled_bits52_v1"
        or design.generator_metadata.get("mixing") != "A_with_one_column_from_B"
    ):
        raise ValueError("unsupported Sobol generation or mixed-block convention")
    if {p.replicate_index for p in design.matrices} != set(range(request.scrambles)) or len(
        design.matrices
    ) != request.scrambles:
        raise ValueError("one uniquely identified pair per scramble is required")
    shape = (2 ** request.sample_powers[-1], len(request.parameters))
    if any(np.asarray(v).shape != shape for p in design.matrices for v in (p.a, p.b)):
        raise ValueError("Sobol matrix dimensions do not match the request")


def iter_sobol_batches(design: SobolDesign, *, batch_size: int = 1024) -> Iterator[SobolInputBatch]:
    _verify_design(design)
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("positive integer batch size required")
    request, count = design.request, 2 ** design.request.sample_powers[-1]
    batch_metadata = dict(
        design_digest=design.content_digest,
        request_digest=canonical_digest(request.model_dump(mode="json")),
        evaluator_id=request.evaluator_id,
        evaluator_revision=request.evaluator_revision,
        parameter_units={parameter.name: parameter.unit for parameter in request.parameters},
    )
    for pair in sorted(design.matrices, key=lambda p: p.replicate_index):
        a, b = np.asarray(pair.a), np.asarray(pair.b)
        blocks = [("A", None), ("B", None), *[(f"AB:{i}", i) for i in range(len(request.parameters))]]
        for block, column in blocks:
            for start in range(0, count, batch_size):
                stop = min(start + batch_size, count)
                values = (b if block == "B" else a)[start:stop].copy()
                if column is not None:
                    values[:, column] = b[start:stop, column]
                yield SobolInputBatch(
                    **batch_metadata,
                    replicate_index=pair.replicate_index,
                    block_id=block,
                    point_indices=list(range(start, stop)),
                    parameters={m.name: values[:, i].tolist() for i, m in enumerate(request.parameters)},
                )
            if block == "A":
                stop = min(request.repeat_check_points, count)
                yield SobolInputBatch(
                    **batch_metadata,
                    replicate_index=pair.replicate_index,
                    block_id="A",
                    repeat=True,
                    point_indices=list(range(stop)),
                    parameters={m.name: a[:stop, i].tolist() for i, m in enumerate(request.parameters)},
                )


def seal_sobol_evaluations(
    design: SobolDesign,
    responses: list[SobolEvaluationBatch],
    *,
    runtime_metadata: dict[str, str] | None = None,
) -> SobolEvaluations:
    """Attach response bytes to a design; this digest is not a model-validity certificate."""
    _verify_design(design)
    if any(response.design_digest != design.content_digest for response in responses):
        raise ValueError("response batch belongs to another design")
    payload = dict(
        schema_version="matintegrity.sobol_evaluations.v1",
        design_digest=design.content_digest,
        responses=[r.model_dump(mode="json") for r in responses],
        runtime_metadata=runtime_metadata
        if runtime_metadata is not None
        else dict(_runtime(), metadata_role="sealing_environment", evaluation_runtime="not_declared"),
    )
    return SobolEvaluations.model_validate_json(
        json.dumps(dict(payload, content_digest=canonical_digest(payload)))
    )


def evaluate_sobol_design(
    design: SobolDesign, evaluator: Callable, *, batch_size: int = 1024, stop_on_uncomputed: bool = True
) -> SobolEvaluations:
    responses = []
    quantities = len(design.request.quantities)
    repeat_points = min(design.request.repeat_check_points, 2 ** design.request.sample_powers[-1])
    repeat_anchors = np.full((design.request.scrambles, repeat_points, quantities), np.nan)
    for batch in iter_sobol_batches(design, batch_size=batch_size):
        draws = {name: np.asarray(values).copy() for name, values in batch.parameters.items()}
        for values in draws.values():
            values.setflags(write=False)
        raw = evaluator(draws)
        states = (
            raw.row_status
            if isinstance(raw, SensitivityBatchResult)
            else ("computed",) * len(batch.point_indices)
        )
        values = np.asarray(raw.values if isinstance(raw, SensitivityBatchResult) else raw)
        if values.dtype.kind not in "biuf":
            raise ValueError("evaluator quantities must be real numeric arrays")
        with np.errstate(over="ignore", invalid="ignore"):
            values = values.astype(float)
        if quantities == 1 and values.ndim == 1:
            values = values[:, None]
        if (
            values.shape != (len(batch.point_indices), quantities)
            or len(states) != len(values)
            or any(s not in ROW_STATES for s in states)
        ):
            raise ValueError("evaluator must preserve [point,quantity] shape and row states")
        normalized_states, encoded = [], []
        for row, state in zip(values, states, strict=True):
            if state == "computed" and not np.all(np.isfinite(row)):
                state = "invalid_output"
            normalized_states.append(state)
            encoded.append([float(v) if math.isfinite(float(v)) else None for v in row])
        responses.append(
            SobolEvaluationBatch(
                design_digest=batch.design_digest,
                replicate_index=batch.replicate_index,
                block_id=batch.block_id,
                point_indices=batch.point_indices,
                values=encoded,
                row_status=normalized_states,
                repeat=batch.repeat,
            )
        )
        if stop_on_uncomputed and any(s != "computed" for s in normalized_states):
            break
        if batch.block_id == "A" and not batch.repeat:
            for point, row in zip(batch.point_indices, values, strict=True):
                if point < repeat_points:
                    repeat_anchors[batch.replicate_index, point] = row
        if stop_on_uncomputed and batch.repeat:
            original = repeat_anchors[batch.replicate_index, batch.point_indices]
            if np.all(np.isfinite(original)) and _repeat_failures(design.request, original, values):
                break
    return seal_sobol_evaluations(
        design, responses, runtime_metadata=dict(_runtime(), metadata_role="local_evaluation_environment")
    )


def _repeat_failures(request, original, repeated):
    failures = []
    for index, quantity in enumerate(request.quantities):
        with np.errstate(over="ignore", invalid="ignore"):
            match = np.isclose(
                original[..., index],
                repeated[..., index],
                rtol=quantity.repeat_relative_tolerance,
                atol=quantity.repeat_absolute_tolerance,
            )
        if not np.all(match):
            failures.append(quantity.name)
    return failures


def analyze_sobol_evaluations(design: SobolDesign, evaluations: SobolEvaluations) -> SobolReport:
    """Use every paired point; missing, failed or nonrepeatable responses yield no indices."""
    from scipy.stats import sobol_indices, t

    _verify_design(design)
    if not isinstance(evaluations, SobolEvaluations):
        raise TypeError("validated SobolEvaluations required")
    if (
        evaluations.design_digest != design.content_digest
        or canonical_digest(evaluations.model_dump(mode="json", exclude={"content_digest"}))
        != evaluations.content_digest
    ):
        raise ValueError("evaluations/design content digest mismatch")
    request = design.request
    n, dimensions = _request_budget(request)
    outputs, repeats = len(request.quantities), min(request.repeat_check_points, n)
    blocks = {name: index for index, name in enumerate(["A", "B", *[f"AB:{i}" for i in range(dimensions)]])}
    values = np.full((request.scrambles, dimensions + 2, n, outputs), np.nan)
    observed = np.zeros(values.shape[:3], dtype=bool)
    repeat_values = np.full((request.scrambles, repeats, outputs), np.nan)
    repeat_observed = np.zeros(repeat_values.shape[:2], dtype=bool)
    states = Counter()
    for response in evaluations.responses:
        if response.design_digest != design.content_digest:
            raise ValueError("response batch belongs to another design")
        r, block = response.replicate_index, response.block_id
        if r >= request.scrambles or block not in blocks or (response.repeat and block != "A"):
            raise ValueError("unknown response replicate or block identity")
        index = np.asarray(response.point_indices)
        limit = repeats if response.repeat else n
        if np.any(index >= limit) or any(len(row) != outputs for row in response.values):
            raise ValueError("response point/quantity dimensions changed")
        destination, seen = (
            (repeat_values[r], repeat_observed[r])
            if response.repeat
            else (values[r, blocks[block]], observed[r, blocks[block]])
        )
        if np.any(seen[index]):
            raise ValueError("duplicate response point identity; reconcile retries explicitly")
        destination[index] = [[math.nan if v is None else v for v in row] for row in response.values]
        seen[index] = True
        states.update(response.row_status)
    missing = int(observed.size - observed.sum() + repeat_observed.size - repeat_observed.sum())
    bad = sum(count for state, count in states.items() if state != "computed")
    diagnostics = dict(
        requested_evaluations=int(observed.size + repeat_observed.size),
        observed_evaluations=sum(states.values()),
        missing_evaluations=missing,
        observed_row_status_counts=dict(states),
        confidence_level=request.confidence_level,
        confidence_interval_interpretation="approximate Student-t intervals for the mean across independent randomized scrambles; no iid row bootstrap",
        distribution_estimation_uncertainty_in_intervals=False,
        model_form_uncertainty_in_intervals=False,
        variance_indices_are_period_failure_probabilities=False,
    )

    def report(status, precision, quantities, notes):
        return SobolReport(
            analysis_id=request.analysis_id,
            status=status,
            precision_status=precision,
            context=request.context,
            evaluator_id=request.evaluator_id,
            evaluator_revision=request.evaluator_revision,
            request_digest=canonical_digest(request.model_dump(mode="json")),
            design_digest=design.content_digest,
            evaluations_digest=evaluations.content_digest,
            parameter_names=[p.name for p in request.parameters],
            quantities=quantities,
            diagnostics=diagnostics,
            runtime_metadata=_runtime(),
            notes=notes,
        )

    if not bad:
        for replicate in range(request.scrambles):
            paired = observed[replicate, 0, :repeats] & repeat_observed[replicate]
            if not np.any(paired):
                continue
            failures = _repeat_failures(
                request, values[replicate, 0, :repeats][paired], repeat_values[replicate, paired]
            )
            if failures:
                diagnostics["nonrepeatable_quantity"] = failures[0]
                return report(
                    "needs_data",
                    "not_evaluable",
                    [],
                    (
                        "Repeat checks exceed the declared tolerance. A stochastic or batch-dependent evaluator needs another sensitivity formulation.",
                    ),
                )
    if missing or bad:
        return report(
            "needs_data",
            "not_evaluable",
            [],
            (
                "Missing or noncomputed design points prevent analysis. No valid-row filtering, imputation or conditional-subset sensitivity is performed.",
            ),
        )
    scale = np.max(np.abs(values), axis=(1, 2))
    scaled = values / np.where(scale > 0, scale, 1.0)[:, None, None, :]
    scaled -= np.mean(scaled[:, :2], axis=(1, 2))[:, None, None, :]
    critical = float(t.ppf((1 + request.confidence_level) / 2, request.scrambles - 1))
    levels = [[] for _ in request.quantities]
    for power in request.sample_powers:
        count = 2**power
        sample = scaled[:, :, :count]
        combined = sample[:, :2].reshape(request.scrambles, 2 * count, outputs)
        variances = np.var(combined, axis=1)
        resolved = (
            (np.ptp(combined, axis=1) > 64 * np.finfo(float).eps) & (variances > 0) & np.isfinite(variances)
        )
        first = np.full((request.scrambles, outputs, dimensions), np.nan)
        total = np.full_like(first, np.nan)
        for replicate in range(request.scrambles):
            valid = resolved[replicate]
            if not np.any(valid):
                continue
            a = sample[replicate, 0].T[valid]
            b = sample[replicate, 1].T[valid]
            ab = sample[replicate, 2:].transpose(0, 2, 1)[:, valid, :]
            result = sobol_indices(func=dict(f_A=a.copy(), f_B=b.copy(), f_AB=ab.copy()), n=count)
            first[replicate, valid] = np.asarray(result.first_order).reshape(int(valid.sum()), dimensions)
            total[replicate, valid] = np.asarray(result.total_order).reshape(int(valid.sum()), dimensions)
        for quantity in range(outputs):
            available = bool(np.all(resolved[:, quantity]))
            f, s = first[:, quantity], total[:, quantity]
            if available and (not np.all(np.isfinite(f)) or not np.all(np.isfinite(s))):
                available = False
            levels[quantity].append(
                SobolLevelEstimate(
                    base_samples=count,
                    first_order=np.mean(f, axis=0).tolist() if available else None,
                    total_order=np.mean(s, axis=0).tolist() if available else None,
                    first_order_half_width=(
                        critical * np.std(f, axis=0, ddof=1) / math.sqrt(request.scrambles)
                    ).tolist()
                    if available
                    else None,
                    total_order_half_width=(
                        critical * np.std(s, axis=0, ddof=1) / math.sqrt(request.scrambles)
                    ).tolist()
                    if available
                    else None,
                    first_order_replicates=f.tolist() if available else None,
                    total_order_replicates=s.tolist() if available else None,
                    normalized_variance_by_replicate=variances[:, quantity].tolist(),
                )
            )
    results = []
    for quantity, history in zip(request.quantities, levels, strict=True):
        last, previous = history[-1], history[-2]
        change, bounds, precision = None, None, False
        if last.first_order is not None:
            f, s = np.asarray(last.first_order), np.asarray(last.total_order)
            tolerance = request.refinement_absolute_tolerance
            bounds = bool(
                np.all(f >= -tolerance)
                and np.all(s >= -tolerance)
                and np.all(f <= 1 + tolerance)
                and np.all(s <= 1 + tolerance)
                and np.all(s >= f - tolerance)
                and f.sum() <= 1 + tolerance
                and s.sum() >= 1 - tolerance
            )
            if previous.first_order is not None:
                change = max(
                    float(np.max(np.abs(f - previous.first_order))),
                    float(np.max(np.abs(s - previous.total_order))),
                )
                precision = bool(
                    bounds
                    and change <= tolerance
                    and max(*last.first_order_half_width, *last.total_order_half_width)
                    <= request.confidence_half_width_tolerance
                )
        results.append(
            SobolQuantityResult(
                name=quantity.name,
                response_unit=quantity.unit,
                status="estimated" if last.first_order is not None else "undefined_or_unresolved_variance",
                precision_criteria_satisfied=precision,
                refinement_maximum_change=change,
                theoretical_bounds_diagnostic_passed=bounds,
                levels=history,
            )
        )
    return report(
        "computed" if all(q.status == "estimated" for q in results) else "needs_data",
        "not_evaluable"
        if any(q.status != "estimated" for q in results)
        else (
            "criteria_met"
            if all(q.precision_criteria_satisfied for q in results)
            else "sampling_precision_unresolved"
        ),
        results,
        (
            "First and total indices describe variance contributions under the fixed declared independent marginals. Estimates and intervals are not clipped to [0,1].",
            "Between-scramble intervals and nested-size comparisons diagnose numerical integration only. Declared precision criteria, finite repeat checks and matching hashes do not establish model or distribution validity; convergence is not guaranteed.",
            "Dependent physical inputs require a reviewed joint/dependence-aware method. Sensitivity of independent latent coordinates is not automatically sensitivity of correlated physical parameters.",
        ),
    )


def run_sobol(request: SobolRequest, evaluator: Callable, *, batch_size: int = 1024) -> SobolReport:
    design = create_sobol_design(request)
    evaluations = evaluate_sobol_design(design, evaluator, batch_size=batch_size)
    return analyze_sobol_evaluations(design, evaluations)


class RegistrySensitivityBinding(Contract):
    parameter_name: str
    input_field: str
    input_unit: str


class RegistrySensitivityConfiguration(Contract):
    model_id: str
    base_inputs: dict[str, Any]
    bindings: list[RegistrySensitivityBinding] = Field(min_length=1)


def _affine_conversion(source, target):
    zero, one, two = [convert(float(v), source, target) for v in (0, 1, 2)]
    factor = one - zero
    if (
        factor == 0
        or not math.isfinite(factor)
        or not math.isclose(two, zero + 2 * factor, rel_tol=1e-12, abs_tol=0.0)
    ):
        raise ValueError("registry helper requires a resolvable affine unit conversion")
    return zero, factor


def registry_sensitivity_evaluator(registry, request: SobolRequest) -> Callable:
    """Bind declared native-unit marginals to scalar registry inputs, preserving failures."""
    config = RegistrySensitivityConfiguration.model_validate_json(json.dumps(request.evaluator_configuration))
    description = registry.describe(config.model_id)
    if request.evaluator_id != config.model_id or request.evaluator_revision != description["model_version"]:
        raise ValueError("evaluator identity/revision differs from the selected registered model")
    parameters = {p.name: p for p in request.parameters}
    if (
        set(parameters) != {b.parameter_name for b in config.bindings}
        or len(config.bindings) != len(parameters)
        or len({b.input_field for b in config.bindings}) != len(config.bindings)
    ):
        raise ValueError("each uncertain parameter needs one distinct input-field binding")
    properties = description["input_schema"].get("properties", {})
    input_conversions = {}
    for binding in config.bindings:
        if properties.get(binding.input_field, {}).get("type") != "number":
            raise ValueError("registry helper supports top-level real-valued input fields only")
        input_conversions[binding.parameter_name] = _affine_conversion(
            parameters[binding.parameter_name].unit, binding.input_unit
        )
    output_conversions = []
    for quantity in request.quantities:
        if quantity.name not in description["output_units"]:
            raise ValueError("quantity is not a declared scalar model output")
        output_conversions.append(
            _affine_conversion(description["output_units"][quantity.name], quantity.unit)
        )

    def evaluator(draws):
        if set(draws) != set(parameters) or len({len(v) for v in draws.values()}) != 1:
            raise ValueError("registry draws do not match parameter identities and point count")
        count = len(next(iter(draws.values())))
        values = np.full((count, len(request.quantities)), np.nan)
        states = []
        for index in range(count):
            model_inputs = deepcopy(config.base_inputs)
            for binding in config.bindings:
                zero, factor = input_conversions[binding.parameter_name]
                model_inputs[binding.input_field] = zero + factor * float(
                    draws[binding.parameter_name][index]
                )
            try:
                result = registry.run_json(
                    config.model_id, json.dumps(model_inputs, allow_nan=False), request.context
                )
            except ValueError:
                states.append("invalid_input")
                continue
            states.append(result.status)
            if result.status != "computed":
                continue
            for output, (quantity, (zero, factor)) in enumerate(
                zip(request.quantities, output_conversions, strict=True)
            ):
                raw = result.values.get(quantity.name)
                if not isinstance(raw, (float, int)) or isinstance(raw, bool):
                    raise ValueError(
                        "registry quantity is not a scalar real number; use an explicit response callback"
                    )
                values[index, output] = zero + factor * raw
        return SensitivityBatchResult(values, tuple(states))

    return evaluator
