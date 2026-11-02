"""Fit a caller gasket compression branch under a monotonicity constraint."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_compression_curve_monotone_fit"


class GasketCompressionCurveObservation(Contract):
    observation_id: str = Field(min_length=1)
    compression_m: Nonnegative
    compressive_force_N: Nonnegative
    standard_uncertainty_N: Positive


class GasketCompressionCurveMonotoneFit(Contract):
    schema_version: Literal["matintegrity.gasket_compression_curve_monotone_fit.v1"] = (
        "matintegrity.gasket_compression_curve_monotone_fit.v1"
    )
    assessment_id: str = Field(min_length=1)
    gasket_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_or_lot_id: str = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    loading_branch_id: str = Field(min_length=1)
    temperature_K: Positive
    loading_rate_m_s: Nonnegative
    observations: tuple[GasketCompressionCurveObservation, ...] = Field(min_length=2, max_length=10000)
    minimum_tangent_stiffness_N_m: Positive | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    common_material_state_and_loading_branch_reviewed: bool
    displacement_force_units_and_reference_reviewed: bool
    uncertainty_weights_and_independence_reviewed: bool
    monotone_fit_and_optional_stiffness_floor_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_observations(self):
        if len({row.observation_id for row in self.observations}) != len(self.observations):
            raise ValueError("observation IDs must be unique")
        zero_rows = [row for row in self.observations if row.compression_m == 0.0]
        if not zero_rows or any(row.compressive_force_N != 0.0 for row in zero_rows):
            raise ValueError("a measured zero-compression, zero-force origin is required; the fitter will not invent one")
        record = {
            "gasket_id": self.gasket_id,
            "material_condition_id": self.material_condition_id,
            "specimen_or_lot_id": self.specimen_or_lot_id,
            "test_method_id": self.test_method_id,
            "loading_branch_id": self.loading_branch_id,
            "temperature_K": self.temperature_K,
            "loading_rate_m_s": self.loading_rate_m_s,
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "record_id": self.record_id,
            "observations": [row.model_dump(mode="json") for row in self.observations],
        }
        if canonical_digest(record) != self.record_sha256:
            raise ValueError("test record digest must bind specimen condition, test metadata and all observations")
        if not any(row.source_id == self.provider_id and row.sha256 == self.record_sha256
                   and row.license_id == self.usage_license_id for row in self.evidence):
            raise ValueError("Evidence must bind the measurement source, record digest and computational-use license")
        return self


def _pava(values: list[float], weights: list[float]) -> list[float]:
    """Weighted O(n) pool-adjacent-violators fit for a nondecreasing sequence."""
    blocks: list[list[float]] = []  # [start, end-exclusive, sum_weight, weighted_sum]
    for index, (value, weight) in enumerate(zip(values, weights, strict=True)):
        blocks.append([float(index), float(index + 1), weight, weight * value])
        while len(blocks) >= 2:
            left, right = blocks[-2], blocks[-1]
            if left[3] / left[2] <= right[3] / right[2]:
                break
            blocks[-2:] = [[left[0], right[1], left[2] + right[2], left[3] + right[3]]]
    fitted = [0.0] * len(values)
    for start, end, weight, weighted_sum in blocks:
        level = weighted_sum / weight
        for index in range(int(start), int(end)):
            fitted[index] = level
    return fitted


def _weighted_isotonic(values: list[float], weights: list[float]) -> tuple[list[float], str]:
    """Prefer SciPy's maintained PAVA implementation when its optional extra exists."""
    try:
        from scipy.optimize import isotonic_regression
    except (ImportError, AttributeError):
        return _pava(values, weights), "internal_weighted_pava"
    result = isotonic_regression(values, weights=weights, increasing=True)
    return [float(value) for value in result.x], "scipy.optimize.isotonic_regression"


def evaluate_gasket_compression_curve_monotone_fit(request: GasketCompressionCurveMonotoneFit) -> Calculation:
    """Fit force observations at measured compression knots; never extrapolate."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "gasket_id": request.gasket_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "measurement_record_sha256": request.record_sha256,
    }
    reviews = {
        "common_material_state_and_loading_branch_reviewed": request.common_material_state_and_loading_branch_reviewed,
        "displacement_force_units_and_reference_reviewed": request.displacement_force_units_and_reference_reviewed,
        "uncertainty_weights_and_independence_reviewed": request.uncertainty_weights_and_independence_reviewed,
        "monotone_fit_and_optional_stiffness_floor_reviewed": request.monotone_fit_and_optional_stiffness_floor_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    grouped: dict[float, list[tuple[float, float]]] = {}
    observation_weight: dict[str, float] = {}
    for row in request.observations:
        try:
            weight = 1.0 / (row.standard_uncertainty_N * row.standard_uncertainty_N)
        except (ArithmeticError, OverflowError, ZeroDivisionError):
            weight = math.inf
        if not math.isfinite(weight) or weight <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "measurement_uncertainty_implies_nonfinite_weight",
                "observation_id": row.observation_id,
            })
        grouped.setdefault(row.compression_m, []).append(
            (row.compressive_force_N, weight)
        )
        observation_weight[row.observation_id] = weight
    xs = sorted(grouped)
    observed_means = []
    combined_weights = []
    try:
        for compression in xs:
            records = grouped[compression]
            weight = math.fsum(item[1] for item in records)
            weighted_mean = math.fsum(force * row_weight for force, row_weight in records) / weight
            if not math.isfinite(weighted_mean) or not math.isfinite(weight):
                return Calculation(status="out_of_scope", values=base | {"reason": "weighted_observation_aggregation_nonfinite"})
            observed_means.append(weighted_mean)
            combined_weights.append(weight)
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "weighted_observation_aggregation_nonfinite",
            "detail": str(error),
        })

    floor = request.minimum_tangent_stiffness_N_m
    transformed = [force - (floor * compression if floor is not None else 0.0)
                   for compression, force in zip(xs, observed_means, strict=True)]
    if not all(math.isfinite(value) for value in transformed):
        return Calculation(status="out_of_scope", values=base | {"reason": "stiffness_floor_transform_nonfinite"})
    try:
        transformed_fit, algorithm = _weighted_isotonic(transformed, combined_weights)
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "weighted_isotonic_fit_failed",
            "detail": str(error),
        })
    fitted = [value + (floor * compression if floor is not None else 0.0)
              for compression, value in zip(xs, transformed_fit, strict=True)]
    if not all(math.isfinite(value) and value >= 0 for value in fitted):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fitted_curve_is_negative_or_nonfinite",
        })

    residual_rows = []
    weighted_sse_terms = []
    unweighted_sse_terms = []
    max_abs_residual = 0.0
    index_by_x = {compression: index for index, compression in enumerate(xs)}
    for observation in request.observations:
        index = index_by_x[observation.compression_m]
        residual = observation.compressive_force_N - fitted[index]
        weight = observation_weight[observation.observation_id]
        if not math.isfinite(residual) or not math.isfinite(weight * residual * residual):
            return Calculation(status="out_of_scope", values=base | {"reason": "fit_residual_nonfinite"})
        weighted_sse_terms.append(weight * residual * residual)
        unweighted_sse_terms.append(residual * residual)
        max_abs_residual = max(max_abs_residual, abs(residual))
        residual_rows.append({
            "observation_id": observation.observation_id,
            "compression_m": observation.compression_m,
            "measured_force_N": observation.compressive_force_N,
            "fitted_force_N": fitted[index],
            "residual_N": residual,
        })
    try:
        total_weight = math.fsum(row[1] for records in grouped.values() for row in records)
        weighted_rmse = math.sqrt(math.fsum(weighted_sse_terms) / total_weight)
        rmse = math.sqrt(math.fsum(unweighted_sse_terms) / len(request.observations))
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fit_diagnostics_nonfinite",
            "detail": str(error),
        })
    curve_points = [
        {"compression_m": compression, "compressive_force_N": force}
        for compression, force in zip(xs, fitted, strict=True)
    ]
    if not all(math.isfinite(value) for value in (weighted_rmse, rmse, max_abs_residual)):
        return Calculation(status="out_of_scope", values=base | {"reason": "fit_diagnostics_nonfinite"})
    return Calculation(status="computed", values=base | {
        "test_condition": {
            "material_condition_id": request.material_condition_id,
            "specimen_or_lot_id": request.specimen_or_lot_id,
            "test_method_id": request.test_method_id,
            "loading_branch_id": request.loading_branch_id,
            "temperature_K": request.temperature_K,
            "loading_rate_m_s": request.loading_rate_m_s,
        },
        "fitted_curve_points": curve_points,
        "strictly_increasing_force_curve_compatible": all(
            right["compressive_force_N"] > left["compressive_force_N"]
            for left, right in zip(curve_points, curve_points[1:])
        ),
        "residuals": residual_rows,
        "fit_diagnostics": {
            "algorithm": algorithm,
            "observation_count": len(request.observations),
            "unique_compression_knot_count": len(xs),
            "pool_count": sum(1 for left, right in zip(transformed_fit, transformed_fit[1:]) if right > left) + 1,
            "weighted_rmse_N": weighted_rmse,
            "rmse_N": rmse,
            "maximum_absolute_residual_N": max_abs_residual,
            "minimum_tangent_stiffness_N_m": floor,
        },
        "method": "weighted_non_decreasing_isotonic_regression_by_pool_adjacent_violators",
        "limitations": [
            "Only one caller-identified monotone compression loading branch at one material condition, temperature and rate is fitted.",
            "Weights are inverse squared caller standard uncertainties and assume compatible independent observation errors; residual summaries are descriptive, not a validated statistical model.",
            "The output is supported only at observed compression knots and must not be extrapolated or transferred to another gasket, lot, temperature, rate, unloading branch or cycling history without separate evidence.",
            "No hysteresis, stress relaxation, leakage relation, seal acceptance, material qualification or failure probability is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketCompressionCurveMonotoneFit,
        evaluate_gasket_compression_curve_monotone_fit,
        {
            "test_condition.temperature_K": "K",
            "test_condition.loading_rate_m_s": "m/s",
            "fitted_curve_points[].compression_m": "m",
            "fitted_curve_points[].compressive_force_N": "N",
            "residuals[].residual_N": "N",
            "fit_diagnostics.weighted_rmse_N": "N",
            "fit_diagnostics.rmse_N": "N",
            "fit_diagnostics.maximum_absolute_residual_N": "N",
            "fit_diagnostics.minimum_tangent_stiffness_N_m": "N/m",
        },
        (
            "Observed force values are fit by weighted least-squares isotonic regression at sorted measured compression knots.",
            "An optional caller-selected positive tangent floor is enforced by subtracting its linear component before isotonic fitting and adding it back afterward.",
            "The fitted monotone loading curve remains tied to the specific supplied specimen condition and must not be extrapolated or transferred automatically.",
        ),
        (
            "caller_gasket_compression_force_observations_and_uncertainties",
            "weighted_non_decreasing_isotonic_regression_pool_adjacent_violators",
            "caller_material_condition_temperature_rate_and_loading_branch",
        ),
        qualification="user_model",
    )]
