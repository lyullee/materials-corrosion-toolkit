"""Spatial mixed-potential screen with electrolyte ohmic coupling along a slit."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_spatial_ohmic_mixed_potential"
KINETICS_SOURCE_ID = "caller_crevice_spatial_butler_volmer_branch_profiles"
ELECTROLYTE_SOURCE_ID = "caller_crevice_spatial_electrolyte_conductivity"
SOLVER_SOURCE_ID = "finite_volume_electrolyte_resistance_with_local_butler_volmer_balance"
FARADAY_CONSTANT_C_MOL = 96485.33212
GAS_CONSTANT_J_MOL_K = 8.31446261815324


class CreviceSpatialReactionBranch(Contract):
    reaction_id: str = Field(min_length=1)
    electron_number: int = Field(ge=1, le=32)
    signed_current_multiplier: Literal[-1, 1]
    exchange_current_density_A_m2_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    equilibrium_potential_V_by_cell_and_time: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    anodic_transfer_coefficient: Positive = Field(le=1.0)
    cathodic_transfer_coefficient: Positive = Field(le=1.0)
    minimum_overpotential_V: float
    maximum_overpotential_V: float
    kinetics_provider_id: str = Field(min_length=1)
    kinetics_revision: str = Field(min_length=1)
    kinetics_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_branch(self):
        if self.maximum_overpotential_V <= self.minimum_overpotential_V:
            raise ValueError("branch overpotential support must be ordered and nonzero")
        if any(not math.isfinite(value) for row in self.equilibrium_potential_V_by_cell_and_time for value in row):
            raise ValueError("branch equilibrium-potential profiles must be finite")
        return self


class CreviceSpatialOhmicMixedPotentialRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    geometry_provider_id: str = Field(min_length=1)
    geometry_revision: str = Field(min_length=1)
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    conductivity_provider_id: str = Field(min_length=1)
    conductivity_revision: str = Field(min_length=1)
    conductivity_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    time_s: tuple[float, ...] = Field(min_length=1, max_length=10000)
    cell_ids: tuple[str, ...] = Field(min_length=2, max_length=500)
    cell_lengths_m: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    cell_apertures_m: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    slit_width_m: Positive
    reactive_face_count: Literal[1, 2]
    temperature_K_by_time: tuple[Positive, ...] = Field(min_length=1, max_length=10000)
    electrolyte_conductivity_S_m_by_cell_and_time: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    branches: tuple[CreviceSpatialReactionBranch, ...] = Field(min_length=2, max_length=32)
    minimum_solution_potential_V: float = -2.0
    maximum_solution_potential_V: float = 2.0
    maximum_solver_evaluations: int = Field(default=10000, ge=100, le=1000000)
    evidence: tuple[Evidence, ...] = Field(min_length=2)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    geometry_mapping_and_cell_order_reviewed: bool
    electrolyte_conductivity_support_reviewed: bool
    local_butler_volmer_parameters_and_sign_convention_reviewed: bool
    electronically_continuous_metal_and_no_metal_ohmic_drop_reviewed: bool
    electrolyte_ohmic_closure_and_insulated_ends_reviewed: bool
    quasi_steady_interval_independence_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_spatial_profile(self):
        n, nt = len(self.cell_ids), len(self.time_s)
        if any(not math.isfinite(t) for t in self.time_s) or any(b <= a for a, b in zip(self.time_s, self.time_s[1:])):
            raise ValueError("time knots must be finite and strictly increasing")
        if len(set(self.cell_ids)) != n or len(self.cell_lengths_m) != n or len(self.cell_apertures_m) != n:
            raise ValueError("cell identities, lengths and apertures must be unique and aligned")
        if len(self.temperature_K_by_time) != nt or len(self.electrolyte_conductivity_S_m_by_cell_and_time) != n:
            raise ValueError("temperature and conductivity arrays must match declared time and space axes")
        if any(len(row) != nt for row in self.electrolyte_conductivity_S_m_by_cell_and_time):
            raise ValueError("each cell conductivity profile must align with the time knots")
        if self.maximum_solution_potential_V <= self.minimum_solution_potential_V:
            raise ValueError("solution-potential solver bounds must be strictly ordered")
        if len({branch.reaction_id for branch in self.branches}) != len(self.branches):
            raise ValueError("reaction branch IDs must be unique")
        for branch in self.branches:
            if (len(branch.exchange_current_density_A_m2_by_cell) != n
                    or len(branch.equilibrium_potential_V_by_cell_and_time) != n
                    or any(len(row) != nt for row in branch.equilibrium_potential_V_by_cell_and_time)):
                raise ValueError("each branch exchange-current vector and equilibrium-potential field must align")
        reviews = (
            self.geometry_mapping_and_cell_order_reviewed,
            self.electrolyte_conductivity_support_reviewed,
            self.local_butler_volmer_parameters_and_sign_convention_reviewed,
            self.electronically_continuous_metal_and_no_metal_ohmic_drop_reviewed,
            self.electrolyte_ohmic_closure_and_insulated_ends_reviewed,
            self.quasi_steady_interval_independence_reviewed,
            self.usage_rights_reviewed,
            self.computational_use_authorized,
        )
        if not all(reviews):
            raise ValueError("all spatial electrical, kinetic, applicability and rights reviews are required")
        if not any(row.license_id for row in self.usage_rights_evidence):
            raise ValueError("rights evidence must identify a license or permitted-use basis")
        for provider_id, digest in ((self.geometry_provider_id, self.geometry_sha256),
                                    (self.conductivity_provider_id, self.conductivity_sha256)):
            if not any(row.source_id == provider_id and row.sha256 == digest for row in self.evidence):
                raise ValueError("geometry and conductivity providers must map to digest-matched Evidence")
        for branch in self.branches:
            if not any(row.source_id == branch.kinetics_provider_id and row.sha256 == branch.kinetics_sha256
                       for row in self.evidence):
                raise ValueError("every kinetic provider digest must map to source Evidence")
        return self


def _branch_current_density(branch: CreviceSpatialReactionBranch, cell: int, time: int,
                            metal_potential: float, solution_potential: float,
                            temperature: float) -> float:
    eta = metal_potential - solution_potential - branch.equilibrium_potential_V_by_cell_and_time[cell][time]
    thermal_voltage = GAS_CONSTANT_J_MOL_K * temperature / FARADAY_CONSTANT_C_MOL
    anodic_exp = np.clip(branch.anodic_transfer_coefficient * branch.electron_number * eta / thermal_voltage, -50.0, 50.0)
    cathodic_exp = np.clip(-branch.cathodic_transfer_coefficient * branch.electron_number * eta / thermal_voltage, -50.0, 50.0)
    raw = branch.exchange_current_density_A_m2_by_cell[cell] * (math.exp(float(anodic_exp)) - math.exp(float(cathodic_exp)))
    return branch.signed_current_multiplier * raw


def solve_crevice_spatial_ohmic_mixed_potential(
    request: CreviceSpatialOhmicMixedPotentialRequest,
) -> Calculation:
    """Solve a quasi-steady spatial current/potential balance independently at each exact knot."""
    try:
        from scipy.optimize import root
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "scipy_runtime_unavailable"})
    digest = canonical_digest(request.model_dump(mode="json"))
    n = len(request.cell_ids)
    area = np.asarray(request.cell_lengths_m) * request.slit_width_m * request.reactive_face_count
    aperture = np.asarray(request.cell_apertures_m)
    lengths = np.asarray(request.cell_lengths_m)
    total_length = float(np.sum(lengths))
    centers = np.cumsum(lengths) - 0.5 * lengths
    face_spacing = np.diff(centers)
    states = []
    previous_metal = float(np.mean([branch.equilibrium_potential_V_by_cell_and_time[0][0] for branch in request.branches]))
    previous_phi = np.zeros(n - 1)
    evaluations = 0
    current_residual_max = 0.0
    for k, time_s in enumerate(request.time_s):
        temperature = request.temperature_K_by_time[k]
        conductivity = np.asarray([row[k] for row in request.electrolyte_conductivity_S_m_by_cell_and_time])
        face_k = 2.0 * conductivity[:-1] * conductivity[1:] / (conductivity[:-1] + conductivity[1:])
        face_h = 2.0 * aperture[:-1] * aperture[1:] / (aperture[:-1] + aperture[1:])
        face_area = face_h * request.slit_width_m
        branch_i0 = np.asarray([branch.exchange_current_density_A_m2_by_cell for branch in request.branches])
        current_scale = max(float(np.sum(area * np.sum(branch_i0, axis=0))), 1e-30)
        e0 = [branch.equilibrium_potential_V_by_cell_and_time[i][k]
              for branch in request.branches for i in range(n)]
        voltage_scale = max(GAS_CONSTANT_J_MOL_K * temperature / FARADAY_CONSTANT_C_MOL,
                            float(np.ptp(e0)), 1e-3)
        # Fix the solution-potential gauge at cell 0; unknowns are metal potential, remaining cell potentials,
        # and internal electrolyte face currents scaled by the characteristic exchange current.
        x0 = np.concatenate(([previous_metal], previous_phi, np.zeros(n - 1)))

        def residual(x: np.ndarray) -> np.ndarray:
            nonlocal evaluations
            evaluations += 1
            metal = float(x[0])
            phi = np.concatenate(([0.0], np.asarray(x[1:n])))
            face_current = np.asarray(x[n:]) * current_scale
            net_current = np.zeros(n)
            for branch in request.branches:
                for i in range(n):
                    net_current[i] += area[i] * _branch_current_density(branch, i, k, metal, phi[i], temperature)
            cell_balance = np.empty(n)
            for i in range(n):
                left = 0.0 if i == 0 else face_current[i - 1]
                right = 0.0 if i == n - 1 else face_current[i]
                cell_balance[i] = (right - left - net_current[i]) / current_scale
            ohmic = np.empty(n - 1)
            for i in range(n - 1):
                ohmic[i] = (phi[i + 1] - phi[i] + face_current[i] * face_spacing[i]
                            / (face_k[i] * face_area[i])) / voltage_scale
            return np.concatenate((cell_balance, ohmic))

        result = root(residual, x0, method="hybr", options={"maxfev": request.maximum_solver_evaluations})
        residual_values = residual(result.x)
        if not result.success or not np.isfinite(result.x).all() or float(np.max(np.abs(residual_values))) > 1e-7:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "reason": "spatial_ohmic_nonlinear_solve_failed",
                "failed_time_index": k, "failed_time_s": time_s, "solver_message": str(result.message),
                "maximum_scaled_residual": float(np.max(np.abs(residual_values))),
                "input_sha256": digest, "solver_function_evaluations": evaluations,
            })
        metal = float(result.x[0])
        solution_phi = np.concatenate(([0.0], np.asarray(result.x[1:n])))
        face_current = np.asarray(result.x[n:]) * current_scale
        branch_profiles = []
        total_cell_current = np.zeros(n)
        for branch in request.branches:
            density = [_branch_current_density(branch, i, k, metal, solution_phi[i], temperature) for i in range(n)]
            total_cell_current += area * np.asarray(density)
            branch_profiles.append({
                "reaction_id": branch.reaction_id,
                "signed_current_density_A_m2_by_cell": density,
                "signed_total_current_A": float(np.dot(area, density)),
            })
        closure = np.empty(n)
        for i in range(n):
            left = 0.0 if i == 0 else face_current[i - 1]
            right = 0.0 if i == n - 1 else face_current[i]
            closure[i] = right - left - total_cell_current[i]
        current_residual_max = max(current_residual_max, float(np.max(np.abs(closure))))
        if (metal < request.minimum_solution_potential_V or metal > request.maximum_solution_potential_V
                or np.any(solution_phi < request.minimum_solution_potential_V)
                or np.any(solution_phi > request.maximum_solution_potential_V)):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "reason": "solved_potential_exceeds_declared_numerical_support",
                "time_s": time_s, "metal_potential_V": metal,
                "solution_potential_V_by_cell": solution_phi.tolist(), "input_sha256": digest,
            })
        if any((metal - solution_phi[i] - branch.equilibrium_potential_V_by_cell_and_time[i][k])
               < branch.minimum_overpotential_V
               or (metal - solution_phi[i] - branch.equilibrium_potential_V_by_cell_and_time[i][k])
               > branch.maximum_overpotential_V
               for branch in request.branches for i in range(n)):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "reason": "branch_overpotential_outside_caller_support",
                "time_s": time_s, "input_sha256": digest,
            })
        previous_metal = metal
        previous_phi = solution_phi[1:].copy()
        states.append({
            "time_s": time_s,
            "metal_potential_V_relative_to_cell_0_solution": metal,
            "solution_potential_V_by_cell_relative_to_cell_0": solution_phi.tolist(),
            "electrolyte_face_current_A_by_cell_boundary": [0.0, *face_current.tolist(), 0.0],
            "net_electrode_current_A_by_cell": total_cell_current.tolist(),
            "electrode_current_closure_residual_A_by_cell": closure.tolist(),
            "reaction_branches": branch_profiles,
        })
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "input_sha256": digest,
        "cell_ids": list(request.cell_ids),
        "solution_potential_gauge_cell_id": request.cell_ids[0],
        "maximum_absolute_cell_current_closure_residual_A": current_residual_max,
        "solver_function_evaluations": evaluations,
        "state_history": states,
        "interpretation": "quasi_steady_spatial_mixed_potential_with_caller_electrolyte_ohmic_drop",
        "limitations": [
            "The metal is one electronically continuous equipotential conductor; metal resistance, capacitive current and transient double-layer charging are excluded.",
            "Electrolyte current follows one-dimensional ohmic resistance with electrically insulated mouth and blind-tip end boundaries.",
            "Local branch current uses caller Butler-Volmer parameters and equilibrium-potential profiles; chemistry and kinetic calibration are not inferred.",
            "The independent knot solves are quasi-steady and do not model flow, mass transfer, time-dependent film depletion, corrosion geometry change, probability or acceptance.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSpatialOhmicMixedPotentialRequest,
        evaluator=solve_crevice_spatial_ohmic_mixed_potential,
        units={
            "state_history[].time_s": "s",
            "state_history[].metal_potential_V_relative_to_cell_0_solution": "V",
            "state_history[].solution_potential_V_by_cell_relative_to_cell_0[]": "V",
            "state_history[].electrolyte_face_current_A_by_cell_boundary[]": "A",
            "state_history[].net_electrode_current_A_by_cell[]": "A",
            "state_history[].electrode_current_closure_residual_A_by_cell[]": "A",
            "state_history[].reaction_branches[].signed_current_density_A_m2_by_cell[]": "A/m^2",
            "state_history[].reaction_branches[].signed_total_current_A": "A",
            "maximum_absolute_cell_current_closure_residual_A": "A",
        },
        assumptions=(
            "One continuous metal conductor has a common potential and caller-defined reaction branches act at finite slit cells.",
            "One-dimensional electrolyte ohmic resistance couples adjacent local mixed-potential reactions; both axial ends are electrically insulated.",
            "Each exact time knot is solved as a separate quasi-steady state with local Butler-Volmer kinetics and caller equilibrium potentials.",
        ),
        source_ids=(KINETICS_SOURCE_ID, ELECTROLYTE_SOURCE_ID, SOLVER_SOURCE_ID,
                    "nist_molar_gas_constant", "iupac_faradays_laws_of_electrolysis"),
    )]
