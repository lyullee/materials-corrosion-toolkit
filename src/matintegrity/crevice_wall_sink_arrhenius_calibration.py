"""Calibrate one effective Arrhenius crevice wall-transfer velocity from observations."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.crevice_wall_sink_arrhenius_calibration"
SOURCE_ID = "caller_crevice_wall_sink_velocity_arrhenius_calibration"
R_J_MOL_K = 8.31446261815324
MAX_OBSERVATIONS = 5000


class CreviceWallSinkRateObservations(Contract):
    observation_id: tuple[str, ...] = Field(min_length=4, max_length=MAX_OBSERVATIONS)
    source_group_id: tuple[str, ...] = Field(min_length=4, max_length=MAX_OBSERVATIONS)
    partition: tuple[Literal["calibration", "holdout"], ...] = Field(min_length=4, max_length=MAX_OBSERVATIONS)
    temperature_K: tuple[Positive, ...] = Field(min_length=4, max_length=MAX_OBSERVATIONS)
    wall_transfer_velocity_m_s: tuple[Positive, ...] = Field(min_length=4, max_length=MAX_OBSERVATIONS)
    log_velocity_standard_uncertainty: tuple[Positive, ...] | None = Field(default=None, min_length=4, max_length=MAX_OBSERVATIONS)

    @model_validator(mode="after")
    def align_observations(self):
        count = len(self.observation_id)
        vectors = (self.source_group_id, self.partition, self.temperature_K, self.wall_transfer_velocity_m_s)
        if any(len(row) != count for row in vectors):
            raise ValueError("observation vectors must have equal length")
        if self.log_velocity_standard_uncertainty is not None and len(self.log_velocity_standard_uncertainty) != count:
            raise ValueError("log-velocity uncertainty must align with every observation")
        if len(set(self.observation_id)) != count or any(not value for value in (*self.observation_id, *self.source_group_id)):
            raise ValueError("observation and source-group identifiers must be nonempty and observation IDs unique")
        return self


class CreviceWallSinkArrheniusCalibrationRequest(Contract):
    schema_version: Literal["matintegrity.crevice_wall_sink_arrhenius_calibration.v1"] = (
        "matintegrity.crevice_wall_sink_arrhenius_calibration.v1"
    )
    calibration_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    wall_surface_state_id: str = Field(min_length=1)
    fluid_chemistry_state_id: str = Field(min_length=1)
    reference_temperature_K: Positive
    minimum_calibration_temperature_span_K: Positive
    observations: CreviceWallSinkRateObservations
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    observation_to_effective_wall_velocity_mapping_reviewed: bool
    shared_surface_and_fluid_state_across_temperatures_reviewed: bool
    calibration_holdout_partition_predeclared: bool
    temperature_and_measurement_support_reviewed: bool
    arrhenius_law_applicability_reviewed: bool
    computational_use_and_data_rights_reviewed: bool


def fit_crevice_wall_sink_arrhenius(
    request: CreviceWallSinkArrheniusCalibrationRequest,
) -> Calculation:
    """Fit ln(k/k_ref) against reciprocal temperature without holdout leakage."""
    digest = canonical_digest(request.model_dump(mode="json"))
    obs = request.observations
    base = {
        "calibration_id": request.calibration_id,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "wall_surface_state_id": request.wall_surface_state_id,
        "fluid_chemistry_state_id": request.fluid_chemistry_state_id,
        "input_sha256": digest,
        "observation_count": len(obs.observation_id),
    }
    reviews = (
        "observation_to_effective_wall_velocity_mapping_reviewed",
        "shared_surface_and_fluid_state_across_temperatures_reviewed",
        "calibration_holdout_partition_predeclared",
        "temperature_and_measurement_support_reviewed",
        "arrhenius_law_applicability_reviewed",
        "computational_use_and_data_rights_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    partition = np.asarray(obs.partition)
    calibration = partition == "calibration"
    holdout = partition == "holdout"
    if int(calibration.sum()) < 3 or not np.any(holdout):
        return Calculation(status="needs_data", values=base | {
            "reason": "at least three calibration observations and one untouched holdout are required",
        })
    calibration_groups = {obs.source_group_id[index] for index in np.flatnonzero(calibration)}
    holdout_groups = {obs.source_group_id[index] for index in np.flatnonzero(holdout)}
    if calibration_groups & holdout_groups:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "source groups must not cross the calibration and holdout partitions",
            "overlapping_source_group_ids": sorted(calibration_groups & holdout_groups),
        })

    temperature = np.asarray(obs.temperature_K, dtype=float)
    measured = np.asarray(obs.wall_transfer_velocity_m_s, dtype=float)
    reference = request.reference_temperature_K
    cal_temperature = temperature[calibration]
    distinct = np.unique(cal_temperature)
    span = float(cal_temperature.max() - cal_temperature.min())
    if len(distinct) < 3 or span < request.minimum_calibration_temperature_span_K:
        return Calculation(status="needs_data", values=base | {
            "calibration_temperature_span_K": span,
            "distinct_calibration_temperature_count": len(distinct),
            "reason": "calibration requires at least three distinct temperatures and the declared minimum span",
        })
    if not cal_temperature.min() <= reference <= cal_temperature.max():
        return Calculation(status="out_of_scope", values=base | {
            "reason": "reference temperature must lie inside calibration support",
        })
    if np.any(holdout) and (
        temperature[holdout].min() < cal_temperature.min()
        or temperature[holdout].max() > cal_temperature.max()
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "holdout temperatures must lie inside calibration support; extrapolation is not validation",
        })

    x_cal = 1.0 / cal_temperature - 1.0 / reference
    y_cal = np.log(measured[calibration])
    if obs.log_velocity_standard_uncertainty is None:
        weights = np.ones(int(calibration.sum()), dtype=float)
        uncertainty_basis = "unweighted_log_rate_residual_scatter"
        known_sigma = False
    else:
        sigma = np.asarray(obs.log_velocity_standard_uncertainty, dtype=float)[calibration]
        weights = 1.0 / np.square(sigma)
        uncertainty_basis = "caller_supplied_log_velocity_standard_uncertainty"
        known_sigma = True
    weight_sum = float(np.sum(weights))
    center = float(np.dot(weights, x_cal) / weight_sum)
    centered = x_cal - center
    scale = math.sqrt(float(np.dot(weights, np.square(centered)) / weight_sum))
    if not math.isfinite(scale) or scale <= np.finfo(float).eps * max(abs(center), 1.0):
        return Calculation(status="needs_data", values=base | {"reason": "inverse-temperature design is numerically unresolved"})
    normalized = centered / scale
    design = np.column_stack((np.ones(len(normalized)), normalized))
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, None]
    weighted_response = y_cal * root_weight
    coefficients, _, rank, singular = np.linalg.lstsq(weighted_design, weighted_response, rcond=None)
    if rank != 2 or singular[-1] <= 0:
        return Calculation(status="needs_data", values=base | {"reason": "weighted calibration design is rank deficient"})
    slope = float(coefficients[1] / scale)
    intercept = float(coefficients[0] - slope * center)
    activation_energy = -R_J_MOL_K * slope
    if not all(math.isfinite(value) for value in (slope, intercept, activation_energy)):
        return Calculation(status="out_of_scope", values=base | {"reason": "fitted Arrhenius parameters exceed finite numeric support"})
    if activation_energy < 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "fitted_activation_energy_J_mol": activation_energy,
            "reason": "observations imply negative activation energy outside the shared crevice Arrhenius wall-rate contract",
        })

    predicted_log = intercept + slope * (1.0 / temperature - 1.0 / reference)
    residual = np.log(measured) - predicted_log
    dof = int(calibration.sum()) - 2
    covariance_normalized = np.linalg.inv(weighted_design.T @ weighted_design)
    if not known_sigma:
        residual_variance = float(np.dot(residual[calibration], residual[calibration]) / dof)
        covariance_normalized *= residual_variance
    transform = np.array([[1.0, -center / scale], [0.0, 1.0 / scale]])
    covariance_intercept_slope = transform @ covariance_normalized @ transform.T
    parameter_transform = np.array([[1.0, 0.0], [0.0, -R_J_MOL_K]])
    covariance_log_reference_and_activation = parameter_transform @ covariance_intercept_slope @ parameter_transform.T
    try:
        predicted_velocity = np.exp(predicted_log)
        reference_velocity = math.exp(intercept)
    except (FloatingPointError, OverflowError):
        return Calculation(status="out_of_scope", values=base | {"reason": "predicted wall velocity exceeds finite support"})
    if (
        not np.isfinite(predicted_velocity).all()
        or np.any(predicted_velocity <= 0.0)
        or not math.isfinite(reference_velocity) or reference_velocity <= 0.0
        or not np.isfinite(covariance_log_reference_and_activation).all()
    ):
        return Calculation(status="out_of_scope", values=base | {"reason": "predicted rate or covariance exceeds finite support"})
    holdout_residual = residual[holdout]
    rmse_holdout = float(math.sqrt(float(np.mean(np.square(holdout_residual)))))
    rmse_calibration = float(math.sqrt(float(np.mean(np.square(residual[calibration])))))
    return Calculation(values=base | {
        "status": "computed",
        "reference_wall_transfer_velocity_m_s": reference_velocity,
        "reference_temperature_K": reference,
        "activation_energy_J_mol": activation_energy,
        "parameter_covariance_ln_reference_velocity_and_activation_energy": covariance_log_reference_and_activation.tolist(),
        "calibration_temperature_min_K": float(cal_temperature.min()),
        "calibration_temperature_max_K": float(cal_temperature.max()),
        "calibration_temperature_span_K": span,
        "uncertainty_basis": uncertainty_basis,
        "calibration_observation_count": int(calibration.sum()),
        "holdout_observation_count": int(holdout.sum()),
        "calibration_rmse_log_velocity": rmse_calibration,
        "holdout_rmse_log_velocity": rmse_holdout,
        "observation_residuals": [
            {
                "observation_id": obs.observation_id[index],
                "source_group_id": obs.source_group_id[index],
                "partition": obs.partition[index],
                "temperature_K": float(temperature[index]),
                "measured_wall_transfer_velocity_m_s": float(measured[index]),
                "predicted_wall_transfer_velocity_m_s": float(predicted_velocity[index]),
                "log_velocity_residual": float(residual[index]),
            }
            for index in range(len(temperature))
        ],
        "holdout_used_in_fit": False,
        "prediction_extrapolation_performed": False,
        "interpretation_boundary": "This is an effective Arrhenius fit to the supplied wall-transfer velocity observations. It does not establish a universal material law or calibrated corrosion rate outside this specimen/surface/fluid condition and temperature support.",
        "not_inferred": ["corrosion penetration rate", "mass-transfer-controlled metal loss", "reaction mechanism", "multi-species wall chemistry", "surface evolution", "transport feedback", "probability", "acceptance", "qualification"],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceWallSinkArrheniusCalibrationRequest,
        evaluator=fit_crevice_wall_sink_arrhenius,
        units={
            "reference_wall_transfer_velocity_m_s": "m/s",
            "reference_temperature_K": "K",
            "activation_energy_J_mol": "J/mol",
            "parameter_covariance_ln_reference_velocity_and_activation_energy": "mixed_covariance",
            "calibration_temperature_span_K": "K",
            "calibration_rmse_log_velocity": "1",
            "holdout_rmse_log_velocity": "1",
            "observation_residuals[].measured_wall_transfer_velocity_m_s": "m/s",
            "observation_residuals[].predicted_wall_transfer_velocity_m_s": "m/s",
            "observation_residuals[].log_velocity_residual": "1",
        },
        assumptions=(
            "The supplied observations already represent an effective first-order wall-transfer velocity in m/s; this fit does not derive velocity from penetration, current or mass loss.",
            "One Arrhenius law with a nonnegative activation energy is adequate only over the declared material, surface, fluid-chemistry and calibration temperature support.",
            "Only predeclared calibration rows estimate parameters; holdout source groups are separate and remain unused in fitting.",
            "Optional uncertainties are standard deviations in log velocity and define relative weighted-least-squares weights; without them, residual scatter estimates parameter covariance.",
            "No use outside calibration support, mechanism assignment, corrosion rate, wall protection, probability or qualification is implied.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
