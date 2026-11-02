"""Fit a caller-reviewed nonnegative bilinear leakage surface to observations."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class GasketLeakageFitObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: Literal["calibration", "holdout"]
    contact_pressure_Pa: Nonnegative
    differential_pressure_Pa: Nonnegative
    molar_leak_flux_mol_s_m2: Nonnegative
    residual_scale_mol_s_m2: Positive


class GasketLeakageMapFit(Contract):
    assessment_id: str = Field(min_length=1)
    joint_scope_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    contact_pressure_knots_Pa: tuple[Nonnegative, ...] = Field(min_length=2, max_length=30)
    differential_pressure_knots_Pa: tuple[Nonnegative, ...] = Field(min_length=2, max_length=30)
    observations: tuple[GasketLeakageFitObservation, ...] = Field(min_length=4, max_length=100000)
    maximum_design_cells: int = Field(default=2000000, ge=4, le=10000000)
    maximum_solver_iterations: int = Field(default=1000, ge=1, le=10000)
    solver_tolerance: Positive = Field(default=1e-10, le=1e-3)
    observation_units_and_scope_reviewed: bool
    predeclared_partition_and_source_independence_reviewed: bool
    bilinear_nonnegative_surface_and_residual_scale_reviewed: bool
    pointwise_computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def supported_observations(self):
        for axis in (self.contact_pressure_knots_Pa, self.differential_pressure_knots_Pa):
            if axis[0] != 0 or any(b <= a for a, b in zip(axis, axis[1:])):
                raise ValueError("surface axes must begin at zero and strictly increase")
        if len(self.observations) * len(self.contact_pressure_knots_Pa) * len(self.differential_pressure_knots_Pa) > self.maximum_design_cells:
            raise ValueError("leakage fitting design budget exceeded")
        ids = [row.observation_id for row in self.observations]
        if len(set(ids)) != len(ids):
            raise ValueError("observation IDs must be unique")
        partitions = {}
        for row in self.observations:
            if row.contact_pressure_Pa > self.contact_pressure_knots_Pa[-1] or row.differential_pressure_Pa > self.differential_pressure_knots_Pa[-1]:
                raise ValueError("every observation must lie inside declared knot support")
            for key in (("specimen", row.physical_specimen_id), ("source", row.source_group_id)):
                if key in partitions and partitions[key] != row.role:
                    raise ValueError("a specimen or source group must not cross calibration and holdout")
                partitions[key] = row.role
        if not any(row.role == "calibration" for row in self.observations):
            raise ValueError("calibration observations are required")
        return self


def fit_gasket_leakage_map(x: GasketLeakageMapFit) -> Calculation:
    base = {"assessment_id": x.assessment_id, "joint_scope_id": x.joint_scope_id,
            "calibration_id": x.calibration_id, "input_sha256": canonical_digest(x.model_dump(mode="json"))}
    if not all((x.observation_units_and_scope_reviewed, x.predeclared_partition_and_source_independence_reviewed,
                x.bilinear_nonnegative_surface_and_residual_scale_reviewed, x.pointwise_computational_use_authorized)):
        return Calculation(status="needs_data", values=base, notes=("Observation, partition, model and computational-use reviews are required.",))
    try:
        import numpy as np
        from scipy.optimize import lsq_linear
    except ImportError:
        return Calculation(status="needs_data", values=base, notes=("The optional science dependencies NumPy and SciPy are required.",))
    p, d = x.contact_pressure_knots_Pa, x.differential_pressure_knots_Pa
    design = np.zeros((len(x.observations), len(p) * len(d)))
    for index, row in enumerate(x.observations):
        i = min(int(np.searchsorted(p, row.contact_pressure_Pa, side="right")) - 1, len(p) - 2)
        j = min(int(np.searchsorted(d, row.differential_pressure_Pa, side="right")) - 1, len(d) - 2)
        u = (row.contact_pressure_Pa - p[i]) / (p[i + 1] - p[i])
        v = (row.differential_pressure_Pa - d[j]) / (d[j + 1] - d[j])
        for a, b, weight in ((i,j,(1-u)*(1-v)), (i+1,j,u*(1-v)), (i,j+1,(1-u)*v), (i+1,j+1,u*v)):
            design[index, a * len(d) + b] = weight
    train = np.array([row.role == "calibration" for row in x.observations])
    scales = np.array([row.residual_scale_mol_s_m2 for row in x.observations])
    observed = np.array([row.molar_leak_flux_mol_s_m2 for row in x.observations])
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        matrix = design[train] / scales[train, None]
        target = observed[train] / scales[train]
    if not np.isfinite(matrix).all() or not np.isfinite(target).all():
        return Calculation(status="out_of_scope", values=base | {"reason": "scaled_design_exceeds_numeric_support"})
    try:
        rank = int(np.linalg.matrix_rank(matrix))
    except (FloatingPointError, np.linalg.LinAlgError, ValueError):
        return Calculation(status="out_of_scope", values=base | {"reason": "calibration_rank_diagnostic_failed"}, notes=("The scaled calibration design could not be assessed numerically.",))
    if rank != matrix.shape[1]:
        return Calculation(status="needs_data", values=base | {"design_rank": rank, "parameter_count": matrix.shape[1]}, notes=("Calibration observations do not identify every declared surface knot.",))
    try:
        fit = lsq_linear(matrix, target, bounds=(0.0, np.inf), tol=x.solver_tolerance, max_iter=x.maximum_solver_iterations)
    except (FloatingPointError, np.linalg.LinAlgError, RuntimeError, ValueError) as exc:
        return Calculation(status="out_of_scope", values=base | {"solver_exception": type(exc).__name__}, notes=("The bounded least-squares solver raised a numerical or input-domain error; no fitted map is returned.",))
    if not fit.success or not np.isfinite(fit.x).all():
        return Calculation(status="out_of_scope", values=base | {"solver_status": int(fit.status)}, notes=("The bounded least-squares solve did not complete; no fitted map is returned.",))
    with np.errstate(over="ignore", invalid="ignore"):
        predicted = design @ fit.x
    if not np.isfinite(predicted).all() or not np.isfinite(fit.optimality):
        return Calculation(status="out_of_scope", values=base | {"reason": "fitted_prediction_exceeds_numeric_support"})
    rows = [{"observation_id": row.observation_id, "physical_specimen_id": row.physical_specimen_id,
             "source_group_id": row.source_group_id, "source_sha256": row.source_sha256, "role": row.role,
             "predicted_flux_mol_s_m2": float(value), "signed_residual_mol_s_m2": float(value - row.molar_leak_flux_mol_s_m2)}
            for row, value in zip(x.observations, predicted, strict=True)]
    table = {"differential_pressure_Pa": list(d), "rows": [
        {"contact_pressure_Pa": pressure, "molar_leak_flux_by_delta_pressure_mol_s_m2": [float(value) for value in fit.x[i*len(d):(i+1)*len(d)]]}
        for i, pressure in enumerate(p)]}
    return Calculation(values=base | {"calibration_map": table, "calibration_map_sha256": canonical_digest(table),
        "observation_results": rows, "design_rank": rank, "solver_iterations": fit.nit,
        "solver_optimality": float(fit.optimality), "calibration_observation_count": int(train.sum()),
        "holdout_observation_count": int((~train).sum()), "acceptance_inferred": False}, notes=(
        "Weighted nonnegative bilinear least squares uses calibration rows only; holdout observations never update the map.",
        "A fitted surface is not a qualified joint law, sealing acceptance, uncertainty interval or independent specimen count. Monotonicity and zero-pressure flux are not imposed.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec("fabrication.gasket_leakage_map_fit", GasketLeakageMapFit, fit_gasket_leakage_map,
        {"observation_results[].predicted_flux_mol_s_m2": "mol/s/m2", "observation_results[].signed_residual_mol_s_m2": "mol/s/m2"},
        ("Caller-reviewed nonnegative bilinear surface with supplied knot support and residual scales.",
         "Calibration and holdout specimen/source groups are disjoint; holdout data never determine coefficients.",
         "Surface rank and solver completion are numerical diagnostics, not physical qualification or sealing acceptance."),
        ("caller_gasket_leakage_surface_fit",), qualification="user_model")]
