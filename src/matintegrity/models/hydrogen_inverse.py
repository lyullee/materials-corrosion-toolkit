"""One-parameter inverse fitting for reviewed planar hydrogen-flow observations."""

from __future__ import annotations

import json
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen_kinetics import HydrogenSlab, slab_kinetic

Target = Literal[
    "lattice_diffusivity",
    "trap_capture_frequency",
    "trap_release_frequency",
    "left_transfer_coefficient",
    "right_transfer_coefficient",
    "left_absorption_capacity",
    "right_absorption_capacity",
    "left_desorption_capacity",
    "right_desorption_capacity",
]


class HydrogenSlabFlowMultiplierFit(Contract):
    """Fit one positive history multiplier without consuming holdout observations."""

    schema_version: Literal["matintegrity.hydrogen_slab_flow_multiplier_fit.v1"] = (
        "matintegrity.hydrogen_slab_flow_multiplier_fit.v1"
    )
    fit_id: str = Field(min_length=1)
    observation_series_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    detector_calibration_id: str = Field(min_length=1)
    observed_surface: Literal["left", "right"]
    observed_surface_id: str = Field(min_length=1)
    base_slab: HydrogenSlab
    physical_surface_area_m2: Positive
    observation_id: list[str] = Field(min_length=4, max_length=4096)
    source_group_id: list[str]
    partition: list[Literal["calibration", "holdout"]]
    elapsed_time_s: list[Nonnegative]
    outward_hydrogen_atoms_mol_s: list[float]
    outward_flow_standard_uncertainty_mol_s: list[Positive] | None = None
    residual_scale_mol_s: Positive | None = None
    parameter_target: Target
    parameter_target_id: str = Field(min_length=1)
    initial_multiplier: Positive
    multiplier_bounds: tuple[Positive, Positive]
    minimum_calibration_jacobian_norm: Positive = 1e-8
    maximum_function_evaluations: int = Field(default=80, ge=5, le=1000)
    observation_conversion_reviewed: bool = False
    physical_surface_area_reviewed: bool = False
    fixed_inputs_independent_of_holdout_reviewed: bool = False
    one_parameter_scope_reviewed: bool = False
    holdout_partition_predeclared: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_fit(self):
        count = len(self.observation_id)
        vectors = (
            self.source_group_id,
            self.partition,
            self.elapsed_time_s,
            self.outward_hydrogen_atoms_mol_s,
        )
        if any(len(vector) != count for vector in vectors):
            raise ValueError("flow-observation fields must align with every observation ID")
        if (
            self.outward_flow_standard_uncertainty_mol_s is not None
            and len(self.outward_flow_standard_uncertainty_mol_s) != count
        ):
            raise ValueError("flow uncertainties must align with every observation")
        if (self.outward_flow_standard_uncertainty_mol_s is None) == (self.residual_scale_mol_s is None):
            raise ValueError("provide exactly one of per-observation uncertainty or residual scale")
        if len(set(self.observation_id)) != count:
            raise ValueError("flow observation IDs must be unique")
        if any(not value for value in self.observation_id) or any(
            not value for value in self.source_group_id
        ):
            raise ValueError("observation and source-group IDs cannot be empty")
        if self.elapsed_time_s != self.base_slab.elapsed_time_s:
            raise ValueError("observation and slab output knots must share the exact elapsed-time clock")
        boundary = (
            self.base_slab.left_boundary if self.observed_surface == "left" else self.base_slab.right_boundary
        )
        if self.observed_surface_id != boundary.boundary_id:
            raise ValueError("observed surface ID must match the selected slab boundary")
        if self.multiplier_bounds[1] <= self.multiplier_bounds[0]:
            raise ValueError("multiplier bounds must have positive width")
        if not self.multiplier_bounds[0] <= self.initial_multiplier <= self.multiplier_bounds[1]:
            raise ValueError("initial multiplier must lie inside its bounds")
        calibration = self.partition.count("calibration")
        holdout = self.partition.count("holdout")
        if calibration < 3 or holdout < 1:
            raise ValueError("at least three calibration and one holdout observations are required")
        self._validate_target()
        return self

    def _validate_target(self):
        target = self.parameter_target
        if target == "lattice_diffusivity":
            if self.parameter_target_id != self.base_slab.reference_lattice_id:
                raise ValueError("diffusivity target ID must match the slab reference lattice")
            return
        if target.startswith("trap_"):
            matches = [
                trap for trap in self.base_slab.traps if trap.population.trap_id == self.parameter_target_id
            ]
            if len(matches) != 1:
                raise ValueError("trap target ID must identify exactly one slab trap")
            if target == "trap_release_frequency" and matches[0].release_frequency_per_s is None:
                raise ValueError("release-frequency fitting requires an independent-frequency trap")
            return
        side, quantity = target.split("_", 1)
        boundary = self.base_slab.left_boundary if side == "left" else self.base_slab.right_boundary
        if self.parameter_target_id != boundary.boundary_id:
            raise ValueError("boundary target ID must match the selected target boundary")
        required_kind = (
            "linear_surface_transfer"
            if quantity == "transfer_coefficient"
            else "dissociative_surface_reaction"
        )
        if boundary.kind != required_kind:
            raise ValueError(f"{target} requires a {required_kind} boundary")


def _history_location(payload: dict, target: Target, target_id: str):
    if target == "lattice_diffusivity":
        return payload, "lattice_diffusivity_m2_s"
    if target.startswith("trap_"):
        trap = next(item for item in payload["traps"] if item["population"]["trap_id"] == target_id)
        field = "capture_frequency_per_s" if target == "trap_capture_frequency" else "release_frequency_per_s"
        return trap, field
    side, quantity = target.split("_", 1)
    boundary = payload[f"{side}_boundary"]
    fields = {
        "transfer_coefficient": "transfer_coefficient_m_s",
        "absorption_capacity": "absorption_capacity_flux_mol_m2_s",
        "desorption_capacity": "desorption_capacity_flux_mol_m2_s",
    }
    return boundary, fields[quantity]


def _scaled_slab(x: HydrogenSlabFlowMultiplierFit, multiplier: float):
    payload = x.base_slab.model_dump(mode="json")
    owner, field = _history_location(payload, x.parameter_target, x.parameter_target_id)
    base_history = owner[field]
    if not any(value > 0 for value in base_history):
        raise ValueError("the selected base history has no positive value and cannot be scaled")
    owner[field] = [value * multiplier for value in base_history]
    return HydrogenSlab.model_validate_json(json.dumps(payload)), owner[field]


class _ForwardFailure(Exception):
    pass


def fit_slab_flow_multiplier(x: HydrogenSlabFlowMultiplierFit) -> Calculation:
    """Fit one positive multiplier using calibration rows only."""
    if not all(
        (
            x.observation_conversion_reviewed,
            x.physical_surface_area_reviewed,
            x.fixed_inputs_independent_of_holdout_reviewed,
            x.one_parameter_scope_reviewed,
            x.holdout_partition_predeclared,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Signal conversion, physical area, fixed-input independence, one-parameter scope and holdout predeclaration require explicit review.",
            ),
        )
    try:
        from scipy.optimize import least_squares
    except ImportError:
        return Calculation(
            status="needs_data",
            values={},
            notes=("SciPy is required for bounded nonlinear least-squares fitting.",),
        )
    observed = np.asarray(x.outward_hydrogen_atoms_mol_s, dtype=float)
    partition = np.asarray(x.partition)
    calibration = partition == "calibration"
    holdout = partition == "holdout"
    if x.outward_flow_standard_uncertainty_mol_s is None:
        scale = np.full(len(observed), x.residual_scale_mol_s)
        uncertainty_basis = "caller_declared_common_residual_scale"
    else:
        scale = np.asarray(x.outward_flow_standard_uncertainty_mol_s, dtype=float)
        uncertainty_basis = "caller_supplied_observation_standard_uncertainty"

    evaluations = 0

    def forward(log_multiplier):
        nonlocal evaluations
        evaluations += 1
        multiplier = math.exp(float(np.atleast_1d(log_multiplier)[0]))
        try:
            slab, scaled_history = _scaled_slab(x, multiplier)
        except ValueError as error:
            raise _ForwardFailure(str(error)) from error
        result = slab_kinetic(slab)
        if result.status != "computed":
            raise _ForwardFailure("; ".join(result.notes))
        inward = np.asarray(result.values[f"{x.observed_surface}_inward_flux_mol_m2_s"])
        predicted = -x.physical_surface_area_m2 * inward
        if not np.all(np.isfinite(predicted)):
            raise _ForwardFailure("forward-model flow is non-finite")
        return predicted, slab, scaled_history, result

    def residual(log_multiplier):
        predicted, _, _, _ = forward(log_multiplier)
        return (predicted[calibration] - observed[calibration]) / scale[calibration]

    lower, upper = (math.log(value) for value in x.multiplier_bounds)
    try:
        optimization = least_squares(
            residual,
            np.asarray([math.log(x.initial_multiplier)]),
            bounds=(np.asarray([lower]), np.asarray([upper])),
            max_nfev=x.maximum_function_evaluations,
            method="trf",
        )
        if not optimization.success or not np.all(np.isfinite(optimization.x)):
            return Calculation(
                status="out_of_scope",
                values={
                    "optimizer_status": int(optimization.status),
                    "optimizer_message": str(optimization.message),
                    "function_evaluations": int(optimization.nfev),
                },
                notes=("The bounded one-parameter optimization did not converge.",),
            )
        multiplier = math.exp(float(optimization.x[0]))
        predicted, fitted_slab, fitted_history, forward_result = forward(optimization.x)
    except _ForwardFailure as error:
        return Calculation(
            status="out_of_scope",
            values={"forward_evaluations_attempted": evaluations},
            notes=(f"A trial forward model left its declared scope: {error}",),
        )

    jacobian = np.asarray(optimization.jac, dtype=float).reshape(-1)
    jacobian_norm = float(np.linalg.norm(jacobian))
    if not math.isfinite(jacobian_norm) or jacobian_norm < x.minimum_calibration_jacobian_norm:
        return Calculation(
            status="needs_data",
            values={
                "fitted_multiplier": multiplier,
                "calibration_jacobian_norm": jacobian_norm,
            },
            notes=(
                "Calibration observations have insufficient sensitivity to the selected log multiplier under the caller-declared threshold.",
            ),
        )
    normalized_residual = (predicted - observed) / scale
    raw_residual = predicted - observed
    information = float(np.dot(jacobian, jacobian))
    degrees_of_freedom = int(calibration.sum()) - 1
    if x.outward_flow_standard_uncertainty_mol_s is None:
        residual_variance = float(
            np.dot(normalized_residual[calibration], normalized_residual[calibration]) / degrees_of_freedom
        )
        log_multiplier_variance = residual_variance / information
    else:
        residual_variance = None
        log_multiplier_variance = 1.0 / information
    multiplier_standard_uncertainty = multiplier * math.sqrt(max(log_multiplier_variance, 0.0))
    source_groups_calibration = set(np.asarray(x.source_group_id)[calibration])
    source_groups_holdout = set(np.asarray(x.source_group_id)[holdout])
    records = [
        {
            "observation_id": observation_id,
            "source_group_id": source_group_id,
            "partition": row_partition,
            "elapsed_time_s": elapsed,
            "observed_outward_hydrogen_atoms_mol_s": observation,
            "predicted_outward_hydrogen_atoms_mol_s": float(prediction),
            "flow_residual_mol_s": float(row_residual),
            "normalized_residual": float(row_normalized),
        }
        for observation_id, source_group_id, row_partition, elapsed, observation, prediction, row_residual, row_normalized in zip(
            x.observation_id,
            x.source_group_id,
            x.partition,
            x.elapsed_time_s,
            x.outward_hydrogen_atoms_mol_s,
            predicted,
            raw_residual,
            normalized_residual,
            strict=True,
        )
    ]
    fitted_payload = fitted_slab.model_dump(mode="json")
    return Calculation(
        values={
            "fit_id": x.fit_id,
            "observation_series_id": x.observation_series_id,
            "specimen_id": x.specimen_id,
            "detector_calibration_id": x.detector_calibration_id,
            "material_condition_id": x.base_slab.material_condition_id,
            "reference_lattice_id": x.base_slab.reference_lattice_id,
            "elapsed_time_origin_id": x.base_slab.elapsed_time_origin_id,
            "observed_surface": x.observed_surface,
            "observed_surface_id": x.observed_surface_id,
            "physical_surface_area_m2": x.physical_surface_area_m2,
            "parameter_target": x.parameter_target,
            "parameter_target_id": x.parameter_target_id,
            "fitted_multiplier": multiplier,
            "fitted_multiplier_standard_uncertainty": multiplier_standard_uncertainty,
            "fitted_log_multiplier_variance": log_multiplier_variance,
            "multiplier_bound_active": bool(optimization.active_mask[0]),
            "fitted_target_history": fitted_history,
            "fitted_slab_contract": fitted_payload,
            "base_slab_digest": canonical_digest(x.base_slab.model_dump(mode="json")),
            "fitted_slab_digest": canonical_digest(fitted_payload),
            "calibration_observations": int(calibration.sum()),
            "holdout_observations": int(holdout.sum()),
            "residual_degrees_of_freedom": degrees_of_freedom,
            "uncertainty_basis": uncertainty_basis,
            "calibration_residual_variance": residual_variance,
            "calibration_jacobian_norm": jacobian_norm,
            "calibration_flow_rmse_mol_s": math.sqrt(float(np.mean(raw_residual[calibration] ** 2))),
            "holdout_flow_rmse_mol_s": math.sqrt(float(np.mean(raw_residual[holdout] ** 2))),
            "calibration_normalized_rmse": math.sqrt(float(np.mean(normalized_residual[calibration] ** 2))),
            "holdout_normalized_rmse": math.sqrt(float(np.mean(normalized_residual[holdout] ** 2))),
            "holdout_source_groups_disjoint": not bool(source_groups_calibration & source_groups_holdout),
            "optimizer_status": int(optimization.status),
            "optimizer_message": str(optimization.message),
            "optimizer_function_evaluations": int(optimization.nfev),
            "forward_evaluations_including_final": evaluations,
            "forward_relative_mass_balance_error": forward_result.values["relative_mass_balance_error"],
            "observation_predictions": records,
            "fit_request_digest": canonical_digest(x.model_dump(mode="json")),
        },
        notes=(
            "Only the declared calibration observations enter the objective. Holdout observations are evaluated after fitting and are not independent validation unless source and physical independence are established externally.",
            "The fitted quantity is one positive multiplier applied to the complete named history. Every other initial condition, boundary, trap, geometry and detector conversion remains fixed and must be independently reviewed.",
            "The local Jacobian and conditional standard uncertainty do not cover model form, fixed-input uncertainty, source-group dependence, detector dynamics, clock uncertainty or alternative parameter compensation.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_slab_flow_multiplier_fit",
            HydrogenSlabFlowMultiplierFit,
            fit_slab_flow_multiplier,
            {
                "physical_surface_area_m2": "m^2",
                "fitted_multiplier": "1",
                "fitted_multiplier_standard_uncertainty": "1",
                "fitted_log_multiplier_variance": "1",
                "fitted_target_history": "target-dependent SI units",
                "calibration_jacobian_norm": "1",
                "calibration_flow_rmse_mol_s": "mol/s",
                "holdout_flow_rmse_mol_s": "mol/s",
                "calibration_normalized_rmse": "1",
                "holdout_normalized_rmse": "1",
                "forward_relative_mass_balance_error": "1",
            },
            (
                "One reviewed positive history multiplier, calibrated against signed outward planar hydrogen-atom flow with a predeclared calibration/holdout partition and all other transport inputs fixed.",
            ),
            (
                "hydrogen_slab_flow_multiplier_fit_derivation",
                "scipy_least_squares",
            ),
        )
    ]
