"""Caller-curve dynamic double-layer and Faradaic potential history.

This bounded lumped-cell solver integrates electrode potential from a supplied
total-current history, caller polarization tables, and a differential Cdl curve.
It does not derive those empirical curves or couple them to ionic transport.
"""

from __future__ import annotations

import bisect
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_dynamic_double_layer_faradaic_history"
SOURCE_ID = "caller_evidenced_dynamic_double_layer_and_faradaic_polarization_curves"
MAX_TABLE_OPERATIONS = 20_000_000


class DynamicDoubleLayerPolarizationBranch(Contract):
    """One caller-calibrated, signed current-density curve for each cell."""

    branch_id: str = Field(min_length=1)
    overpotential_axis_V: tuple[float, ...] = Field(min_length=2, max_length=2000)
    signed_current_density_A_m2_by_cell_and_overpotential: tuple[tuple[float, ...], ...] = Field(
        min_length=1, max_length=500
    )
    equilibrium_potential_V_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(
        min_length=2, max_length=1000
    )
    curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_branch(self):
        if any(not math.isfinite(v) for v in self.overpotential_axis_V) or any(
            b <= a for a, b in zip(self.overpotential_axis_V[:-1], self.overpotential_axis_V[1:], strict=True)
        ):
            raise ValueError("branch overpotential support must be finite and strictly increasing")
        if any(not math.isfinite(v) for row in self.signed_current_density_A_m2_by_cell_and_overpotential for v in row):
            raise ValueError("branch current-density tables must be finite")
        if any(len(row) != len(self.overpotential_axis_V)
               for row in self.signed_current_density_A_m2_by_cell_and_overpotential):
            raise ValueError("each branch/cell current-density row must align with the overpotential axis")
        if any(not math.isfinite(v) for row in self.equilibrium_potential_V_by_knot_and_cell for v in row):
            raise ValueError("branch equilibrium-potential histories must be finite")
        record = {
            "branch_id": self.branch_id,
            "overpotential_axis_V": list(self.overpotential_axis_V),
            "signed_current_density_A_m2_by_cell_and_overpotential": [
                list(row) for row in self.signed_current_density_A_m2_by_cell_and_overpotential
            ],
            "equilibrium_potential_V_by_knot_and_cell": [
                list(row) for row in self.equilibrium_potential_V_by_knot_and_cell
            ],
        }
        if canonical_digest(record) != self.curve_sha256:
            raise ValueError("branch digest must bind the complete ordered polarization record")
        if not any(row.sha256 == self.curve_sha256 and row.source_id == SOURCE_ID and row.license_id
                   for row in self.evidence):
            raise ValueError("branch Evidence must license and pin the exact polarization curve")
        return self


class CreviceDynamicDoubleLayerFaradaicHistoryRequest(Contract):
    """Integrate lumped cell potentials under caller total-current histories."""

    schema_version: Literal["matintegrity.crevice_dynamic_double_layer_faradaic_history.v1"] = (
        "matintegrity.crevice_dynamic_double_layer_faradaic_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=500)
    initial_potential_V_by_cell: tuple[float, ...] = Field(min_length=1, max_length=500)
    reference_potential_V_by_cell: tuple[float, ...] = Field(min_length=1, max_length=500)
    active_area_m2_by_knot_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=1000)
    active_area_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    active_area_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    total_current_A_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=1000)
    total_current_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    total_current_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    differential_capacitance_potential_axis_V: tuple[float, ...] = Field(min_length=2, max_length=2000)
    differential_capacitance_F_m2: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    differential_capacitance_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    capacitance_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    faradaic_branches: tuple[DynamicDoubleLayerPolarizationBranch, ...] = Field(min_length=1, max_length=32)
    absolute_current_closure_tolerance_A: Positive = 1e-9
    absolute_potential_tolerance_V: Positive = 1e-9
    relative_current_closure_tolerance: Positive = Field(default=1e-8, le=1e-3)
    relative_potential_tolerance: Positive = Field(default=1e-8, le=1e-3)
    maximum_total_rhs_evaluations: int = Field(default=2_000_000, ge=2, le=20_000_000)
    maximum_total_table_operations: int = Field(default=20_000_000, ge=1, le=20_000_000)
    curve_linearity_and_no_extrapolation_reviewed: bool
    current_sign_and_external_boundary_reviewed: bool
    lumped_cell_independence_and_no_ionic_transport_reviewed: bool
    parameter_applicability_reviewed: bool
    computation_budget_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_request(self):
        nt, nc = len(self.time_s), len(self.cell_ids)
        if self.time_s[0] != 0.0 or any(not math.isfinite(t) or t < 0 for t in self.time_s):
            raise ValueError("time knots must be finite, nonnegative and start at zero")
        if any(b <= a for a, b in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("time knots must increase strictly")
        if len(set(self.cell_ids)) != nc:
            raise ValueError("cell IDs must be unique and remain in source order")
        if any(len(values) != nc for values in (
            self.initial_potential_V_by_cell, self.reference_potential_V_by_cell
        )):
            raise ValueError("initial and reference potentials must align with cells")
        for name, rows in (("active area", self.active_area_m2_by_knot_and_cell),
                           ("total current", self.total_current_A_by_knot_and_cell)):
            if len(rows) != nt or any(len(row) != nc for row in rows):
                raise ValueError(f"{name} schedule must align with exact time knots and cells")
        if any(not math.isfinite(v) for v in (*self.initial_potential_V_by_cell,
                                               *self.reference_potential_V_by_cell)):
            raise ValueError("potential inputs must be finite")
        if any(not math.isfinite(v) for row in self.total_current_A_by_knot_and_cell for v in row):
            raise ValueError("total-current history must be finite")
        axis = self.differential_capacitance_potential_axis_V
        if any(not math.isfinite(v) for v in axis) or any(
            b <= a for a, b in zip(axis[:-1], axis[1:], strict=True)
        ):
            raise ValueError("capacitance-potential axis must be finite and strictly increasing")
        if len(axis) != len(self.differential_capacitance_F_m2):
            raise ValueError("capacitance axis and ordinates must align")
        capacitance_record = {
            "potential_axis_V": list(axis),
            "differential_capacitance_F_m2": [float(v) for v in self.differential_capacitance_F_m2],
        }
        if canonical_digest(capacitance_record) != self.differential_capacitance_curve_sha256:
            raise ValueError("capacitance digest must bind its ordered axis and values")
        if not any(row.sha256 == self.differential_capacitance_curve_sha256
                   and row.source_id == SOURCE_ID and row.license_id for row in self.capacitance_evidence):
            raise ValueError("capacitance Evidence must license and pin its curve")
        area_record = {
            "time_s": list(self.time_s), "cell_ids": list(self.cell_ids),
            "active_area_m2_by_knot_and_cell": [list(map(float, row)) for row in self.active_area_m2_by_knot_and_cell],
            "reference_potential_V_by_cell": list(self.reference_potential_V_by_cell),
        }
        if canonical_digest(area_record) != self.active_area_record_sha256:
            raise ValueError("active-area digest must bind the exact geometry/potential reference map")
        if not any(row.sha256 == self.active_area_record_sha256 and row.source_id == SOURCE_ID
                   and row.license_id for row in self.active_area_evidence):
            raise ValueError("active-area Evidence must license and pin the exact map")
        current_record = {
            "time_s": list(self.time_s), "cell_ids": list(self.cell_ids),
            "total_current_A_by_knot_and_cell": [list(row) for row in self.total_current_A_by_knot_and_cell],
        }
        if canonical_digest(current_record) != self.total_current_record_sha256:
            raise ValueError("total-current digest must bind the exact ordered current schedule")
        if not any(row.sha256 == self.total_current_record_sha256 and row.source_id == SOURCE_ID
                   and row.license_id for row in self.total_current_evidence):
            raise ValueError("total-current Evidence must license and pin the schedule")
        for branch in self.faradaic_branches:
            if len(branch.signed_current_density_A_m2_by_cell_and_overpotential) != nc:
                raise ValueError("every Faradaic branch needs one polarization table per cell")
            if len(branch.equilibrium_potential_V_by_knot_and_cell) != nt or any(
                len(row) != nc for row in branch.equilibrium_potential_V_by_knot_and_cell
            ):
                raise ValueError("branch equilibrium potentials must align with exact knots and cells")
        if len({branch.branch_id for branch in self.faradaic_branches}) != len(self.faradaic_branches):
            raise ValueError("Faradaic branch IDs must be unique")
        table_ops = nt * nc * len(self.differential_capacitance_F_m2) + sum(
            nt * nc * len(branch.overpotential_axis_V) for branch in self.faradaic_branches
        )
        if table_ops > self.maximum_total_table_operations or table_ops > MAX_TABLE_OPERATIONS:
            raise ValueError("curve lookup work exceeds the declared finite budget")
        if not all((self.curve_linearity_and_no_extrapolation_reviewed,
                    self.current_sign_and_external_boundary_reviewed,
                    self.lumped_cell_independence_and_no_ionic_transport_reviewed,
                    self.parameter_applicability_reviewed,
                    self.computation_budget_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("curve, sign, scope, applicability and computation reviews are required")
        lo, hi = axis[0], axis[-1]
        if any(not lo <= value <= hi for value in (
            *self.initial_potential_V_by_cell, *self.reference_potential_V_by_cell
        )):
            raise ValueError("initial or reference potential is outside capacitance support")
        return self


def _piecewise_linear(axis: tuple[float, ...], values: tuple[float, ...], x: float) -> float:
    if not axis[0] <= x <= axis[-1]:
        raise ArithmeticError("caller_curve_support_exceeded")
    j = min(max(bisect.bisect_right(axis, x) - 1, 0), len(axis) - 2)
    f = (x - axis[j]) / (axis[j + 1] - axis[j])
    return values[j] + f * (values[j + 1] - values[j])


def _integrated_capacitance_charge(
    potential: float, reference: float, axis: tuple[float, ...], values: tuple[float, ...]
) -> float:
    """Exact integral of a piecewise-linear differential capacitance curve."""
    if potential < axis[0] or potential > axis[-1] or reference < axis[0] or reference > axis[-1]:
        raise ArithmeticError("capacitance_curve_support_exceeded")
    if potential == reference:
        return 0.0
    direction = 1.0 if potential > reference else -1.0
    low, high = (reference, potential) if direction > 0 else (potential, reference)
    total = 0.0
    first = max(0, bisect.bisect_right(axis, low) - 1)
    for j in range(first, len(axis) - 1):
        left, right = max(low, axis[j]), min(high, axis[j + 1])
        if right <= left:
            if axis[j] >= high:
                break
            continue
        c_left = _piecewise_linear(axis, values, left)
        c_right = _piecewise_linear(axis, values, right)
        total += 0.5 * (right - left) * (c_left + c_right)
        if axis[j + 1] >= high:
            break
    return direction * total


def solve_crevice_dynamic_double_layer_faradaic_history(
    request: CreviceDynamicDoubleLayerFaradaicHistoryRequest,
) -> Calculation:
    """Integrate cell potentials and report ``I_total = I_F + dQ/dt`` closure."""
    digest = canonical_digest(request.model_dump(mode="json"))
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "scipy_runtime_unavailable", "committed": False,
        })

    times = request.time_s
    areas = np.asarray(request.active_area_m2_by_knot_and_cell, dtype=float)
    currents = np.asarray(request.total_current_A_by_knot_and_cell, dtype=float)
    ntime, ncells = areas.shape
    axis_c = request.differential_capacitance_potential_axis_V
    cap_values = tuple(float(v) for v in request.differential_capacitance_F_m2)
    evaluations = 0
    potentials = np.empty((ntime, ncells), dtype=float)
    potentials[0] = np.asarray(request.initial_potential_V_by_cell, dtype=float)
    interval_nfev: list[int] = []
    rhs_by_interval = []
    branch_arrays = [np.asarray(branch.equilibrium_potential_V_by_knot_and_cell, dtype=float)
                     for branch in request.faradaic_branches]

    def area_at(i: int, t: float) -> tuple[np.ndarray, np.ndarray]:
        dt = times[i + 1] - times[i]
        fraction = min(1.0, max(0.0, (t - times[i]) / dt))
        slope = (areas[i + 1] - areas[i]) / dt
        return areas[i] + fraction * (areas[i + 1] - areas[i]), slope

    def linear_knot_values(values: np.ndarray, i: int, t: float) -> np.ndarray:
        fraction = min(1.0, max(0.0, (t - times[i]) / (times[i + 1] - times[i])))
        return values[i] + fraction * (values[i + 1] - values[i])

    try:
        for interval in range(ntime - 1):
            def rhs(t: float, potential: np.ndarray, _interval: int = interval) -> np.ndarray:
                nonlocal evaluations
                evaluations += 1
                if evaluations > request.maximum_total_rhs_evaluations:
                    raise ArithmeticError("dynamic_double_layer_rhs_budget_exceeded")
                area, area_rate = area_at(_interval, t)
                imposed = linear_knot_values(currents, _interval, t)
                faradaic = np.zeros(ncells, dtype=float)
                for branch, equilibrium_history in zip(request.faradaic_branches, branch_arrays, strict=True):
                    equilibrium = linear_knot_values(equilibrium_history, _interval, t)
                    for cell in range(ncells):
                        eta = float(potential[cell] - equilibrium[cell])
                        density = _piecewise_linear(
                            branch.overpotential_axis_V,
                            tuple(branch.signed_current_density_A_m2_by_cell_and_overpotential[cell]), eta,
                        )
                        faradaic[cell] += area[cell] * density
                for cell, e in enumerate(potential):
                    cdl = _piecewise_linear(axis_c, cap_values, float(e))
                    q_areal = _integrated_capacitance_charge(
                        float(e), request.reference_potential_V_by_cell[cell], axis_c, cap_values
                    )
                    denominator = area[cell] * cdl
                    if not math.isfinite(denominator) or denominator <= 0.0:
                        raise ArithmeticError("nonpositive_dynamic_double_layer_differential_capacity")
                q_areal_all = np.asarray([
                    _integrated_capacitance_charge(float(e), request.reference_potential_V_by_cell[cell], axis_c, cap_values)
                    for cell, e in enumerate(potential)
                ])
                cdl_all = np.asarray([_piecewise_linear(axis_c, cap_values, float(e)) for e in potential])
                derivative = (imposed - faradaic - area_rate * q_areal_all) / (area * cdl_all)
                if not np.isfinite(derivative).all():
                    raise ArithmeticError("nonfinite_dynamic_double_layer_potential_rate")
                return derivative

            rhs_by_interval.append(rhs)

            solved = solve_ivp(
                rhs,
                (times[interval], times[interval + 1]),
                potentials[interval],
                method="BDF",
                t_eval=[times[interval + 1]],
                rtol=float(request.relative_potential_tolerance),
                atol=float(request.absolute_potential_tolerance_V),
            )
            interval_nfev.append(int(solved.nfev))
            if not solved.success or solved.y.shape != (ncells, 1):
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                    "input_sha256": digest, "failed_interval_index": interval,
                    "reason": "dynamic_double_layer_BDF_failed:" + str(solved.message), "committed": False,
                })
            potentials[interval + 1] = solved.y[:, -1]
            if not np.isfinite(potentials[interval + 1]).all():
                raise ArithmeticError("nonfinite_dynamic_double_layer_potential")

        charge = np.zeros((ntime, ncells), dtype=float)
        branch_current = np.zeros((len(request.faradaic_branches), ntime, ncells), dtype=float)
        capacitive_current = np.zeros((ntime, ncells), dtype=float)
        closure = np.zeros((ntime, ncells), dtype=float)
        for knot, time_s in enumerate(times):
            interval = min(knot, ntime - 2)
            area, area_rate = area_at(interval, time_s)
            for cell in range(ncells):
                q_areal = _integrated_capacitance_charge(
                    float(potentials[knot, cell]), request.reference_potential_V_by_cell[cell], axis_c, cap_values
                )
                charge[knot, cell] = area[cell] * q_areal
                for branch_index, branch in enumerate(request.faradaic_branches):
                    equilibrium = linear_knot_values(
                        np.asarray(branch.equilibrium_potential_V_by_knot_and_cell, dtype=float),
                        interval, time_s,
                    )[cell]
                    eta = float(potentials[knot, cell] - equilibrium)
                    branch_current[branch_index, knot, cell] = area[cell] * _piecewise_linear(
                        branch.overpotential_axis_V,
                        tuple(branch.signed_current_density_A_m2_by_cell_and_overpotential[cell]), eta,
                    )
            imposed = currents[knot]
            faradaic_total = np.sum(branch_current[:, knot, :], axis=0)
            q_areal_values = np.asarray([
                _integrated_capacitance_charge(float(potentials[knot, cell]),
                                               request.reference_potential_V_by_cell[cell], axis_c, cap_values)
                for cell in range(ncells)
            ])
            cdl = np.asarray([_piecewise_linear(axis_c, cap_values, float(e)) for e in potentials[knot]])
            equilibrium_faradic = np.zeros(ncells, dtype=float)
            for branch, equilibrium_history in zip(request.faradaic_branches, branch_arrays, strict=True):
                equilibrium = linear_knot_values(equilibrium_history, interval, time_s)
                for cell in range(ncells):
                    eta = float(potentials[knot, cell] - equilibrium[cell])
                    equilibrium_faradic[cell] += area[cell] * _piecewise_linear(
                        branch.overpotential_axis_V,
                        tuple(branch.signed_current_density_A_m2_by_cell_and_overpotential[cell]), eta,
                    )
            potential_rate = rhs_by_interval[interval](time_s, potentials[knot].copy())
            capacitive_current[knot] = area * cdl * potential_rate + area_rate * q_areal_values
            closure[knot] = imposed - equilibrium_faradic - capacitive_current[knot]
            allowed = float(request.absolute_current_closure_tolerance_A) + \
                float(request.relative_current_closure_tolerance) * np.maximum(
                    np.abs(imposed), np.abs(equilibrium_faradic + capacitive_current[knot])
                )
            if np.any(np.abs(closure[knot]) > allowed):
                raise ArithmeticError("dynamic_double_layer_current_closure_failed")
    except (ArithmeticError, OverflowError, RuntimeError, ValueError, FloatingPointError) as exc:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": str(exc), "committed": False,
        })

    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "committed": True,
        "time_s": list(times),
        "cell_ids": list(request.cell_ids),
        "potential_V_by_knot_and_cell": potentials.tolist(),
        "stored_double_layer_charge_C_by_knot_and_cell": charge.tolist(),
        "faradaic_current_A_by_branch_knot_and_cell": branch_current.tolist(),
        "capacitive_current_A_by_knot_and_cell": capacitive_current.tolist(),
        "total_current_A_by_knot_and_cell": currents.tolist(),
        "current_closure_residual_A_by_knot_and_cell": closure.tolist(),
        "maximum_absolute_current_closure_residual_A": float(np.max(np.abs(closure))),
        "bdf_rhs_evaluations": evaluations,
        "bdf_rhs_evaluations_by_interval": interval_nfev,
        "capacitance_curve_sha256": request.differential_capacitance_curve_sha256,
        "active_area_record_sha256": request.active_area_record_sha256,
        "total_current_record_sha256": request.total_current_record_sha256,
        "faradaic_branch_curve_sha256s": [branch.curve_sha256 for branch in request.faradaic_branches],
        "current_convention": "positive_into_electrode",
        "spatial_ionic_transport_coupled": False,
        "qualification_claimed": False,
    }, notes=(
        "Potential is integrated with BDF from caller total-current, signed polarization and differential-capacitance records.",
        "Cell histories are independent lumped balances; electrolyte ohmic coupling, ionic transport, active-area geometry prediction and procedure qualification are not included.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        CreviceDynamicDoubleLayerFaradaicHistoryRequest,
        solve_crevice_dynamic_double_layer_faradaic_history,
        {
            "potential_V_by_knot_and_cell[][]": "V",
            "stored_double_layer_charge_C_by_knot_and_cell[][]": "C",
            "faradaic_current_A_by_branch_knot_and_cell[][][]": "A",
            "capacitive_current_A_by_knot_and_cell[][]": "A",
            "current_closure_residual_A_by_knot_and_cell[][]": "A",
            "maximum_absolute_current_closure_residual_A": "A",
        },
        (
            "Caller-provided polarization and differential-capacitance curves are used only within their declared supports.",
            "Active area, imposed total current and branch equilibrium potentials are interpolated linearly between exact caller knots.",
            "The ODE applies I_total = I_F + dQ/dt with Q from the exact integral of the piecewise-linear differential-capacitance curve.",
            "This is independent-cell lumped dynamics; no electrolyte network, moving boundary, kinetic parameter calibration or qualification is inferred.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
    )]
