"""Propagate calibrated Arrhenius parameter covariance to exact wall-rate knots."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field

from .contracts import Calculation, Contract, canonical_digest
from .crevice_wall_sink_arrhenius_calibration import (
    CreviceWallSinkArrheniusCalibrationRequest,
    fit_crevice_wall_sink_arrhenius,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_wall_sink_rate_parameter_uncertainty"
SOURCE_ID = "caller_crevice_wall_sink_arrhenius_parameter_covariance_propagation"
R_J_MOL_K = 8.31446261815324


class CreviceWallSinkRateUncertaintyRequest(Contract):
    schema_version: Literal["matintegrity.crevice_wall_sink_rate_uncertainty.v1"] = (
        "matintegrity.crevice_wall_sink_rate_uncertainty.v1"
    )
    assessment_id: str = Field(min_length=1)
    calibration_request: CreviceWallSinkArrheniusCalibrationRequest
    calibration_result: dict
    calibration_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibrated_rate_history_result: dict
    calibrated_rate_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_covariance_propagation_reviewed: bool
    first_order_delta_method_reviewed: bool
    uncertainty_not_probability_reviewed: bool


def propagate_crevice_wall_sink_rate_uncertainty(
    request: CreviceWallSinkRateUncertaintyRequest,
) -> Calculation:
    """Project calibration covariance onto k(T) without assigning a distribution."""
    calibration = request.calibration_request
    calibration_result = request.calibration_result
    rate_result = request.calibrated_rate_history_result
    fit_values = calibration_result.get("values", calibration_result)
    history_values = rate_result.get("values", rate_result)
    base = {
        "assessment_id": request.assessment_id,
        "calibration_id": calibration.calibration_id,
        "calibration_result_sha256": request.calibration_result_sha256,
        "calibrated_rate_history_result_sha256": request.calibrated_rate_history_result_sha256,
        "physical_scope_id": calibration.physical_scope_id,
        "material_condition_id": calibration.material_condition_id,
        "wall_surface_state_id": calibration.wall_surface_state_id,
        "fluid_chemistry_state_id": calibration.fluid_chemistry_state_id,
    }
    if canonical_digest(calibration_result) != request.calibration_result_sha256:
        return Calculation(status="out_of_scope", values=base | {"reason": "calibration result digest mismatch"})
    if canonical_digest(rate_result) != request.calibrated_rate_history_result_sha256:
        return Calculation(status="out_of_scope", values=base | {"reason": "calibrated wall-rate history result digest mismatch"})
    if calibration_result.get("status") != "computed" or rate_result.get("status") != "computed":
        return Calculation(status="needs_data", values=base | {"reason": "computed calibration and applied rate history are required"})
    if any(not value for value in (
        request.parameter_covariance_propagation_reviewed,
        request.first_order_delta_method_reviewed,
        request.uncertainty_not_probability_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": [name for name in (
                "parameter_covariance_propagation_reviewed",
                "first_order_delta_method_reviewed",
                "uncertainty_not_probability_reviewed",
            ) if not getattr(request, name)],
        })

    expected_fit = fit_crevice_wall_sink_arrhenius(calibration)
    if expected_fit.status != "computed" or canonical_digest(expected_fit.model_dump(mode="json")) != request.calibration_result_sha256:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "calibration result cannot be reproduced from the pinned observations",
        })
    if (
        history_values.get("calibration_fit_result_sha256") != request.calibration_result_sha256
        or not isinstance(history_values.get("rate_history"), dict)
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "rate history is not linked to the supplied calibration result",
        })
    nested_history = history_values["rate_history"]
    if (
        canonical_digest(nested_history) != history_values.get("rate_history_result_sha256")
        or nested_history.get("status") != "computed"
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nested exact-knot rate history digest or status is invalid",
        })

    covariance_raw = fit_values.get("parameter_covariance_ln_reference_velocity_and_activation_energy")
    if not isinstance(covariance_raw, list) or len(covariance_raw) != 2 or any(
        not isinstance(row, list) or len(row) != 2 for row in covariance_raw
    ):
        return Calculation(status="needs_data", values=base | {"reason": "2x2 calibration parameter covariance is unavailable"})
    covariance = np.asarray(covariance_raw, dtype=float)
    if not np.isfinite(covariance).all() or not np.allclose(covariance, covariance.T, rtol=1e-10, atol=1e-14):
        return Calculation(status="out_of_scope", values=base | {"reason": "parameter covariance is nonfinite or nonsymmetric"})
    eigenvalues = np.linalg.eigvalsh(covariance)
    if eigenvalues[0] < -1e-10 * max(1.0, float(np.max(np.abs(eigenvalues)))):
        return Calculation(status="out_of_scope", values=base | {"reason": "parameter covariance is not positive semidefinite"})

    reference_temperature = fit_values.get("reference_temperature_K")
    rate_rows = nested_history.get("values", {}).get("wall_rate_knots")
    if not isinstance(reference_temperature, (int, float)) or not isinstance(rate_rows, list) or not rate_rows:
        return Calculation(status="needs_data", values=base | {"reason": "reference temperature or exact rate knots are missing"})
    uncertainty_rows = []
    for index, row in enumerate(rate_rows):
        temperature = row.get("temperature_K")
        rate = row.get("wall_transfer_velocity_m_s")
        if (
            isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature)
            or isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0
        ):
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_count": len(uncertainty_rows),
                "rate_uncertainty_knots": uncertainty_rows,
                "failed_knot_index": index,
                "reason": "exact rate knot has invalid temperature or positive velocity",
            })
        gradient = np.array([1.0, -(1.0 / R_J_MOL_K) * (1.0 / temperature - 1.0 / float(reference_temperature))])
        variance = float(gradient @ covariance @ gradient.T)
        tolerance = 1e-12 * max(1.0, float(np.max(np.abs(covariance))))
        if not math.isfinite(variance) or variance < -tolerance:
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_count": len(uncertainty_rows),
                "rate_uncertainty_knots": uncertainty_rows,
                "failed_knot_index": index,
                "reason": "propagated log-rate variance is negative or nonfinite",
            })
        log_std = math.sqrt(max(0.0, variance))
        uncertainty_rows.append({
            "knot_index": index,
            "elapsed_time_s": row.get("elapsed_time_s"),
            "temperature_K": float(temperature),
            "wall_transfer_velocity_m_s": float(rate),
            "log_velocity_parameter_standard_uncertainty": log_std,
            "linearized_velocity_standard_uncertainty_m_s": float(rate) * log_std,
            "sensitivity_vector_ln_rate_to_ln_reference_and_Ea": gradient.tolist(),
        })
    return Calculation(values=base | {
        "status": "computed",
        "reference_temperature_K": float(reference_temperature),
        "calibration_parameter_covariance": covariance.tolist(),
        "uncertainty_rows": uncertainty_rows,
        "uncertainty_basis": "first_order_delta_method_from_fitted_parameter_covariance",
        "probability_distribution_assumed": False,
        "interval_probability_claimed": False,
        "interpretation_boundary": "Propagates the fitted covariance to a local standard uncertainty for wall-transfer velocity. The linearized uncertainty is not a confidence interval or probability statement and excludes model discrepancy, condition-transfer uncertainty and observation bias.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceWallSinkRateUncertaintyRequest,
        evaluator=propagate_crevice_wall_sink_rate_uncertainty,
        units={
            "reference_temperature_K": "K",
            "uncertainty_rows[].elapsed_time_s": "s",
            "uncertainty_rows[].temperature_K": "K",
            "uncertainty_rows[].wall_transfer_velocity_m_s": "m/s",
            "uncertainty_rows[].log_velocity_parameter_standard_uncertainty": "1",
            "uncertainty_rows[].linearized_velocity_standard_uncertainty_m_s": "m/s",
            "sensitivity_vector_ln_rate_to_ln_reference_and_Ea": "mixed_sensitivity",
        },
        assumptions=(
            "Calibration and wall-rate results are bound by complete result digests and calibration request reproduction.",
            "The reported covariance is interpreted as a local covariance of (ln reference wall velocity, activation energy) from the existing calibration fit.",
            "First-order delta propagation uses the Arrhenius logarithmic sensitivity at each exact history temperature.",
            "No Gaussian distribution, confidence interval, probability, model discrepancy or extrapolation is inferred.",
            "Only fitted parameter covariance is propagated; shared-condition transfer and measurement systematics remain unquantified.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
