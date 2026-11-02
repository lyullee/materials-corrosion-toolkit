"""Calibration and identifiability diagnostics for thermal hydrogen-trap frequencies."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen import R_J_mol_K
from .hydrogen_rates import (
    BOLTZMANN_J_K,
    PLANCK_J_S,
    ThermallyActivatedFrequency,
)


class HydrogenThermalRateFit(Contract):
    """Reviewed rate observations split into calibration and untouched holdout rows."""

    schema_version: Literal["matintegrity.hydrogen_thermal_rate_fit.v1"] = (
        "matintegrity.hydrogen_thermal_rate_fit.v1"
    )
    fit_id: str = Field(min_length=1)
    frequency_id: str = Field(min_length=1)
    frequency_role: Literal["capture", "release"]
    kind: Literal["arrhenius", "transition_state"]
    trap_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    energy_reference_id: str = Field(min_length=1)
    observation_id: list[str] = Field(min_length=3, max_length=10_000)
    source_group_id: list[str]
    partition: list[Literal["calibration", "holdout"]]
    temperature_K: list[Positive]
    frequency_per_s: list[Positive]
    log_frequency_standard_uncertainty: list[Positive] | None = None
    transmission_coefficient: float | None = Field(default=None, gt=0, le=1)
    minimum_calibration_temperature_span_K: Positive
    calibration_observations_independent_reviewed: bool = False
    rate_observation_mapping_reviewed: bool = False
    common_energy_reference_reviewed: bool = False
    holdout_partition_predeclared: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_observations(self):
        count = len(self.observation_id)
        vectors = (
            self.source_group_id,
            self.partition,
            self.temperature_K,
            self.frequency_per_s,
        )
        if any(len(vector) != count for vector in vectors):
            raise ValueError("rate observation fields must have one aligned row per observation ID")
        if (
            self.log_frequency_standard_uncertainty is not None
            and len(self.log_frequency_standard_uncertainty) != count
        ):
            raise ValueError("log-frequency uncertainties must align with every observation")
        if len(set(self.observation_id)) != count:
            raise ValueError("rate observation IDs must be unique")
        if any(not value for value in self.observation_id) or any(
            not value for value in self.source_group_id
        ):
            raise ValueError("observation and source-group IDs cannot be empty")
        if self.kind == "transition_state" and self.transmission_coefficient is None:
            raise ValueError("transition-state fitting requires a fixed transmission coefficient")
        if self.kind == "arrhenius" and self.transmission_coefficient is not None:
            raise ValueError("Arrhenius fitting does not accept a transmission coefficient")
        return self


def _transform(x: HydrogenThermalRateFit, temperature: np.ndarray, frequency: np.ndarray):
    inverse_temperature = 1.0 / temperature
    if x.kind == "arrhenius":
        response = np.log(frequency)
    else:
        response = (
            np.log(frequency)
            - math.log(BOLTZMANN_J_K / PLANCK_J_S)
            - np.log(temperature)
            - math.log(x.transmission_coefficient)
        )
    return inverse_temperature, response


def fit_thermal_rate(x: HydrogenThermalRateFit) -> Calculation:
    """Fit one Arrhenius or fixed-transmission transition-state frequency law."""
    if not all(
        (
            x.calibration_observations_independent_reviewed,
            x.rate_observation_mapping_reviewed,
            x.common_energy_reference_reviewed,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Calibration-observation independence, rate mapping and common energy reference require explicit review.",
            ),
        )
    partition = np.asarray(x.partition)
    calibration = partition == "calibration"
    holdout = partition == "holdout"
    temperatures = np.asarray(x.temperature_K, dtype=float)
    frequencies = np.asarray(x.frequency_per_s, dtype=float)
    calibration_temperatures = temperatures[calibration]
    distinct = np.unique(calibration_temperatures)
    if calibration.sum() < 3 or len(distinct) < 3:
        return Calculation(
            status="needs_data",
            values={},
            notes=("At least three distinct calibration temperatures are required for fit diagnostics.",),
        )
    span = float(calibration_temperatures.max() - calibration_temperatures.min())
    if span < x.minimum_calibration_temperature_span_K:
        return Calculation(
            status="needs_data",
            values={"calibration_temperature_span_K": span},
            notes=("Calibration temperature span is below the caller-declared identifiability minimum.",),
        )
    if np.any(holdout) and (
        temperatures[holdout].min() < calibration_temperatures.min()
        or temperatures[holdout].max() > calibration_temperatures.max()
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=(
                "Holdout temperatures must remain inside calibration support; extrapolation is not validation.",
            ),
        )
    inverse_temperature, response = _transform(x, temperatures, frequencies)
    inverse_calibration = inverse_temperature[calibration]
    response_calibration = response[calibration]
    if x.log_frequency_standard_uncertainty is None:
        sigma = None
        weights = np.ones(int(calibration.sum()))
        uncertainty_basis = "residual_scatter_unweighted"
    else:
        sigma = np.asarray(x.log_frequency_standard_uncertainty, dtype=float)
        weights = 1.0 / sigma[calibration] ** 2
        uncertainty_basis = "caller_supplied_log_frequency_standard_uncertainty"
    weight_sum = float(weights.sum())
    center = float(np.dot(weights, inverse_calibration) / weight_sum)
    centered = inverse_calibration - center
    scale = math.sqrt(float(np.dot(weights, centered**2) / weight_sum))
    if not math.isfinite(scale) or scale <= np.finfo(float).eps * max(abs(center), 1.0):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Inverse-temperature design is numerically unresolved.",),
        )
    normalized = centered / scale
    design = np.column_stack([np.ones(len(normalized)), normalized])
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, None]
    weighted_response = response_calibration * root_weight
    coefficients, _, rank, singular = np.linalg.lstsq(weighted_design, weighted_response, rcond=None)
    if rank != 2 or singular[-1] <= 0:
        return Calculation(
            status="needs_data",
            values={},
            notes=("The thermal-rate design is rank deficient.",),
        )
    slope = float(coefficients[1] / scale)
    intercept = float(coefficients[0] - slope * center)
    fitted_log_frequency = intercept + slope * inverse_temperature
    if x.kind == "transition_state":
        fitted_log_frequency = (
            fitted_log_frequency
            + math.log(BOLTZMANN_J_K / PLANCK_J_S)
            + np.log(temperatures)
            + math.log(x.transmission_coefficient)
        )
    log_frequency = np.log(frequencies)
    residual = log_frequency - fitted_log_frequency
    residual_calibration = residual[calibration]
    dof = int(calibration.sum()) - 2
    inverse_normalized_information = np.linalg.inv(weighted_design.T @ weighted_design)
    if sigma is None:
        residual_variance = float(np.dot(residual_calibration, residual_calibration) / dof)
        covariance_normalized = inverse_normalized_information * residual_variance
    else:
        residual_variance = None
        covariance_normalized = inverse_normalized_information
    normalized_to_raw = np.array([[1.0, -center / scale], [0.0, 1.0 / scale]])
    covariance_intercept_slope = normalized_to_raw @ covariance_normalized @ normalized_to_raw.T
    if x.kind == "arrhenius":
        activation = -R_J_mol_K * slope
        if activation < 0:
            return Calculation(
                status="out_of_scope",
                values={"fitted_activation_energy_J_mol": activation},
                notes=("The fitted slope implies a negative Arrhenius activation energy.",),
            )
        if intercept < math.log(math.ulp(0.0)) or intercept > math.log(
            float.fromhex("0x1.fffffffffffffp+1023")
        ):
            return Calculation(
                status="out_of_scope",
                values={"fitted_log_pre_exponential_frequency_per_s": intercept},
                notes=("The fitted Arrhenius prefactor is outside positive floating-point range.",),
            )
        law = ThermallyActivatedFrequency(
            frequency_id=x.frequency_id,
            kind="arrhenius",
            pre_exponential_frequency_per_s=math.exp(intercept),
            activation_energy_J_mol=activation,
            evidence=x.evidence,
        )
        transform = np.array([[1.0, 0.0], [0.0, -R_J_mol_K]])
        parameter_names = ("log_pre_exponential_frequency_per_s", "activation_energy_J_mol")
        parameter_values = (intercept, activation)
    else:
        entropy = R_J_mol_K * intercept
        enthalpy = -R_J_mol_K * slope
        law = ThermallyActivatedFrequency(
            frequency_id=x.frequency_id,
            kind="transition_state",
            activation_enthalpy_J_mol=enthalpy,
            activation_entropy_J_mol_K=entropy,
            transmission_coefficient=x.transmission_coefficient,
            evidence=x.evidence,
        )
        transform = np.array([[R_J_mol_K, 0.0], [0.0, -R_J_mol_K]])
        parameter_names = ("activation_entropy_J_mol_K", "activation_enthalpy_J_mol")
        parameter_values = (entropy, enthalpy)
    covariance = transform @ covariance_intercept_slope @ transform.T
    standard_uncertainty = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    denominator = float(standard_uncertainty[0] * standard_uncertainty[1])
    correlation = None if denominator == 0 else float(covariance[0, 1] / denominator)
    source_groups_calibration = set(np.asarray(x.source_group_id)[calibration])
    source_groups_holdout = set(np.asarray(x.source_group_id)[holdout])
    records = [
        {
            "observation_id": observation_id,
            "source_group_id": source_group_id,
            "partition": row_partition,
            "temperature_K": temperature,
            "observed_frequency_per_s": frequency,
            "predicted_frequency_per_s": math.exp(float(predicted)),
            "log_frequency_residual": float(row_residual),
        }
        for observation_id, source_group_id, row_partition, temperature, frequency, predicted, row_residual in zip(
            x.observation_id,
            x.source_group_id,
            x.partition,
            x.temperature_K,
            x.frequency_per_s,
            fitted_log_frequency,
            residual,
            strict=True,
        )
    ]
    holdout_rmse = math.sqrt(float(np.mean(residual[holdout] ** 2))) if np.any(holdout) else None
    return Calculation(
        values={
            "fit_id": x.fit_id,
            "frequency_role": x.frequency_role,
            "trap_id": x.trap_id,
            "material_condition_id": x.material_condition_id,
            "reference_lattice_id": x.reference_lattice_id,
            "energy_reference_id": x.energy_reference_id,
            "frequency_law": law.model_dump(mode="json"),
            "frequency_law_digest": canonical_digest(law.model_dump(mode="json")),
            "calibration_temperature_support_K": [
                float(calibration_temperatures.min()),
                float(calibration_temperatures.max()),
            ],
            "calibration_temperature_span_K": span,
            "calibration_observations": int(calibration.sum()),
            "holdout_observations": int(holdout.sum()),
            "residual_degrees_of_freedom": dof,
            "calibration_log_frequency_rmse": math.sqrt(float(np.mean(residual_calibration**2))),
            "holdout_log_frequency_rmse": holdout_rmse,
            "holdout_partition_predeclared": x.holdout_partition_predeclared,
            "holdout_source_groups_disjoint": not bool(source_groups_calibration & source_groups_holdout),
            "normalized_design_condition_number": float(singular[0] / singular[-1]),
            "uncertainty_basis": uncertainty_basis,
            "residual_log_frequency_variance": residual_variance,
            "parameter_names": parameter_names,
            "parameter_values": parameter_values,
            "parameter_covariance": covariance.tolist(),
            "parameter_standard_uncertainty": standard_uncertainty.tolist(),
            "parameter_correlation": correlation,
            "observation_predictions": records,
            "training_digest": canonical_digest(x.model_dump(mode="json")),
        },
        notes=(
            "The fit uses only rows labelled calibration. Holdout rows are predicted after fitting and are not independent validation unless their predeclaration, source separation and physical independence are established externally.",
            "Reported covariance is conditional on the selected single-path law, reviewed rate observations and either supplied log-frequency uncertainties or calibration residual scatter; it excludes model-form, source-group and transport-inversion uncertainty.",
            "A fixed transmission coefficient is required for transition-state fitting because it is structurally confounded with activation entropy in rate-only observations.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_thermal_rate_fit",
            HydrogenThermalRateFit,
            fit_thermal_rate,
            {
                "calibration_temperature_support_K": "K",
                "calibration_temperature_span_K": "K",
                "calibration_log_frequency_rmse": "1",
                "holdout_log_frequency_rmse": "1",
                "normalized_design_condition_number": "1",
                "residual_log_frequency_variance": "1",
            },
            (
                "Weighted log-linear calibration of one reviewed effective Arrhenius or fixed-transmission transition-state frequency law with preserved calibration/holdout identities.",
            ),
            (
                "eyring_transition_state",
                "hydrogen_thermal_rate_fit_derivation",
                "numpy_lstsq",
            ),
        )
    ]
