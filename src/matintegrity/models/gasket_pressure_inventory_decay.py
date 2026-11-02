"""Couple caller gasket leak calibration to a finite gas-inventory pressure decay."""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Any, Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .gasket_leakage_calibration import GasketLeakageHistory

MODEL_ID = "integration.gasket_leakage_pressure_inventory_decay"
R_GAS_J_MOL_K = 8.31446261815324


class GasketPressureInventoryDecay(Contract):
    """Ideal-gas inventory ODE driven by an existing calibrated gasket leak history."""

    schema_version: Literal["matintegrity.gasket_leakage_pressure_inventory_decay.v1"] = (
        "matintegrity.gasket_leakage_pressure_inventory_decay.v1"
    )
    assessment_id: str = Field(min_length=1)
    leakage_history: GasketLeakageHistory
    gas_volume_m3: Positive
    gas_temperature_K: Positive
    downstream_absolute_pressure_Pa: float = Field(ge=0)
    initial_upstream_absolute_pressure_Pa: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    inventory_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    fixed_volume_and_isothermal_gas_reviewed: bool
    pressure_boundary_and_calibration_support_reviewed: bool
    contact_history_independent_of_inventory_pressure_reviewed: bool
    leakage_units_and_area_partition_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def check_inventory_record(self):
        expected = canonical_digest({
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "gas_volume_m3": self.gas_volume_m3,
            "gas_temperature_K": self.gas_temperature_K,
            "downstream_absolute_pressure_Pa": self.downstream_absolute_pressure_Pa,
            "initial_upstream_absolute_pressure_Pa": self.initial_upstream_absolute_pressure_Pa,
            "leakage_history_sha256": canonical_digest(self.leakage_history.model_dump(mode="json")),
        })
        if expected != self.inventory_record_sha256:
            raise ValueError("gas inventory record digest does not match declared state and leakage history")
        if not any(
            item.source_id == self.provider_id
            and item.sha256 == self.inventory_record_sha256
            and item.license_id == self.usage_license_id
            for item in self.evidence
        ):
            raise ValueError("inventory Evidence must pin the declared record and usage license")
        pressure_difference = (
            self.initial_upstream_absolute_pressure_Pa - self.downstream_absolute_pressure_Pa
        )
        if not math.isfinite(self.downstream_absolute_pressure_Pa) or not math.isfinite(pressure_difference):
            raise ValueError("absolute pressures and their difference must be finite")
        if pressure_difference < 0:
            raise ValueError("initial upstream pressure must not be below the downstream boundary")
        if not math.isclose(
            pressure_difference,
            self.leakage_history.differential_pressure_history_Pa[0],
            rel_tol=1.0e-10,
            abs_tol=1.0e-6,
        ):
            raise ValueError("initial pressure difference must match the first caller leakage-history knot")
        if pressure_difference > self.leakage_history.calibration.differential_pressure_Pa[-1]:
            raise ValueError("initial pressure difference is outside the leakage calibration support")
        if any(row.molar_leak_flux_by_delta_pressure_mol_s_m2[0] != 0.0
               for row in self.leakage_history.calibration.rows):
            raise ValueError("pressure-driven calibration flux must be zero at zero differential pressure")
        return self


def _linear_at(times: tuple[float, ...], rows: tuple[tuple[float, ...], ...], t: float) -> tuple[float, ...]:
    if t <= times[0]:
        return rows[0]
    if t >= times[-1]:
        return rows[-1]
    right = bisect_right(times, t)
    left = right - 1
    fraction = (t - times[left]) / (times[right] - times[left])
    return tuple(a + fraction * (b - a) for a, b in zip(rows[left], rows[right]))


def _interpolate_map(table: GasketLeakageHistory, contact_Pa: float, delta_Pa: float) -> float:
    p_knots = tuple(row.contact_pressure_Pa for row in table.calibration.rows)
    d_knots = table.calibration.differential_pressure_Pa
    if not p_knots[0] <= contact_Pa <= p_knots[-1]:
        raise ValueError("contact pressure outside calibration support")
    if not d_knots[0] <= delta_Pa <= d_knots[-1]:
        raise ValueError("pressure difference outside calibration support")
    pi = min(max(bisect_right(p_knots, contact_Pa) - 1, 0), len(p_knots) - 2)
    di = min(max(bisect_right(d_knots, delta_Pa) - 1, 0), len(d_knots) - 2)
    fp = (contact_Pa - p_knots[pi]) / (p_knots[pi + 1] - p_knots[pi])
    fd = (delta_Pa - d_knots[di]) / (d_knots[di + 1] - d_knots[di])
    flux_rows = [row.molar_leak_flux_by_delta_pressure_mol_s_m2 for row in table.calibration.rows]
    low = flux_rows[pi][di] + fd * (flux_rows[pi][di + 1] - flux_rows[pi][di])
    high = flux_rows[pi + 1][di] + fd * (flux_rows[pi + 1][di + 1] - flux_rows[pi + 1][di])
    value = low + fp * (high - low)
    if not math.isfinite(value) or value < 0:
        raise ValueError("interpolated gasket leak flux is not finite and nonnegative")
    return value


def evaluate_gasket_pressure_inventory_decay(request: GasketPressureInventoryDecay, *, scipy: Any) -> Calculation:
    """Integrate pressure and released moles for one fixed-volume isothermal ideal-gas volume."""
    history = request.leakage_history
    result_base = {
        "assessment_id": request.assessment_id,
        "asset_id": history.asset_id,
        "joint_id": history.joint_id,
        "physical_scope_id": history.physical_scope_id,
        "leakage_history_sha256": canonical_digest(history.model_dump(mode="json")),
        "inventory_record_sha256": request.inventory_record_sha256,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "model_id": MODEL_ID,
    }
    required_reviews = (
        request.fixed_volume_and_isothermal_gas_reviewed,
        request.pressure_boundary_and_calibration_support_reviewed,
        request.contact_history_independent_of_inventory_pressure_reviewed,
        request.leakage_units_and_area_partition_reviewed,
        request.computational_use_authorized,
    )
    if not all(required_reviews):
        return Calculation(status="needs_data", values=result_base | {
            "missing_review_count": sum(not row for row in required_reviews),
        })
    if history.mean_contact_pressure_history_Pa is None:
        return Calculation(status="needs_data", values=result_base | {
            "reason": "contact_pressure_history_required_for_pressure_feedback",
        })
    solve_ivp = getattr(getattr(scipy, "integrate", None), "solve_ivp", None)
    if not callable(solve_ivp):
        return Calculation(status="needs_data", values=result_base | {
            "reason": "scipy_integrate_solve_ivp_unavailable",
        })
    times = tuple(history.time_s)
    areas = tuple(history.contact_area_m2)
    pressure_rows = history.mean_contact_pressure_history_Pa
    initial_moles = request.initial_upstream_absolute_pressure_Pa * request.gas_volume_m3 / (
        R_GAS_J_MOL_K * request.gas_temperature_K
    )

    def rhs(t: float, state: list[float]) -> tuple[float, float]:
        delta = max(0.0, state[0] - request.downstream_absolute_pressure_Pa)
        contacts = _linear_at(times, pressure_rows, t)
        rate = math.fsum(
            area * _interpolate_map(history, contact, delta)
            for area, contact in zip(areas, contacts)
        )
        return (-rate * R_GAS_J_MOL_K * request.gas_temperature_K / request.gas_volume_m3, rate)

    try:
        sol = solve_ivp(
            rhs,
            (times[0], times[-1]),
            [request.initial_upstream_absolute_pressure_Pa, 0.0],
            method="RK45",
            t_eval=list(times),
            rtol=1.0e-8,
            atol=[1.0e-3, 1.0e-12],
            max_step=max((times[-1] - times[0]) / 100.0, 1.0e-9),
        )
    except (ArithmeticError, ValueError, OverflowError, RuntimeError):
        return Calculation(status="out_of_scope", values=result_base | {
            "reason": "pressure_feedback_integration_left_model_support",
        })
    if not sol.success or sol.y.shape[1] != len(times) or not all(math.isfinite(float(v)) for row in sol.y for v in row):
        return Calculation(status="out_of_scope", values=result_base | {
            "reason": "pressure_feedback_solver_failed_or_nonfinite",
            "solver_message": str(sol.message),
        })
    upstream_pressure = [float(v) for v in sol.y[0]]
    cumulative_moles = [float(v) for v in sol.y[1]]
    if any(p < request.downstream_absolute_pressure_Pa - 1.0e-6 for p in upstream_pressure):
        return Calculation(status="out_of_scope", values=result_base | {
            "reason": "solver_crossed_downstream_pressure_boundary",
        })
    rows = []
    for t, p_abs, escaped in zip(times, upstream_pressure, cumulative_moles):
        delta = max(0.0, p_abs - request.downstream_absolute_pressure_Pa)
        contacts = _linear_at(times, pressure_rows, t)
        rate = math.fsum(area * _interpolate_map(history, contact, delta) for area, contact in zip(areas, contacts))
        rows.append({
            "time_s": t,
            "upstream_absolute_pressure_Pa": p_abs,
            "differential_pressure_Pa": delta,
            "instantaneous_molar_leak_rate_mol_s": rate,
            "cumulative_released_moles_mol": escaped,
        })
    final_moles = upstream_pressure[-1] * request.gas_volume_m3 / (
        R_GAS_J_MOL_K * request.gas_temperature_K
    )
    return Calculation(values=result_base | {
        "initial_gas_inventory_mol": initial_moles,
        "final_gas_inventory_mol": final_moles,
        "integrated_released_moles_mol": cumulative_moles[-1],
        "inventory_balance_residual_mol": initial_moles - final_moles - cumulative_moles[-1],
        "time_history": rows,
        "interpretation": "ideal_gas_fixed_volume_isothermal_inventory_feedback_under_caller_contact_history_and_leak_calibration",
        "limitations": [
            "Gasket contact pressures follow the supplied piecewise-linear trajectory and do not respond to falling cavity pressure.",
            "The volume is fixed, gas is ideal and isothermal, downstream absolute pressure is fixed, and the caller leakage calibration is used only inside its tabulated support.",
            "No heat transfer, gas composition change, sonic flow correction, leak-path evolution, seal acceptance, failure probability or service-life claim is inferred.",
        ],
    }, notes=(
        "The differential equation couples calibrated molar leak rate to ideal-gas inventory pressure at constant volume and temperature.",
        "This result is conditional on caller contact history, pressure boundaries, gas-volume record and calibrated leakage map.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketPressureInventoryDecay,
        evaluate_gasket_pressure_inventory_decay,
        {
            "initial_gas_inventory_mol": "mol",
            "final_gas_inventory_mol": "mol",
            "integrated_released_moles_mol": "mol",
            "inventory_balance_residual_mol": "mol",
            "time_history[].time_s": "s",
            "time_history[].upstream_absolute_pressure_Pa": "Pa",
            "time_history[].differential_pressure_Pa": "Pa",
            "time_history[].instantaneous_molar_leak_rate_mol_s": "mol/s",
            "time_history[].cumulative_released_moles_mol": "mol",
        },
        (
            "Gas inventory follows a fixed-volume isothermal ideal-gas equation of state.",
            "Molar leak rate is evaluated from the caller's bilinear gasket calibration and linearly interpolated contact-pressure history.",
            "Contact pressures and downstream absolute pressure are prescribed; they do not change with gas inventory pressure.",
        ),
        (
            "caller_gasket_leak_calibration_map",
            "caller_gasket_contact_pressure_history",
            "caller_gasket_gas_inventory_volume_temperature_pressure",
            "ideal_gas_inventory_balance_with_calibrated_leakage",
        ),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    )]
