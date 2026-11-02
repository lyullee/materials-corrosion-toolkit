"""Transient finite-gas CO2 transfer with instantaneous caller-parameterized carbonate equilibrium."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium"
SOURCE_ID = "caller_wet_co2_conditional_carbonate_equilibrium_parameters"
FLUX_SOURCE_ID = "caller_wet_co2_wall_carbon_and_alkalinity_flux_schedule"
TRANSFER_SOURCE_ID = "caller_finite_gas_carbonate_transfer_and_variable_liquid"


class WetCo2TransientCarbonateInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive
    conditional_k1_mol_m3: Positive
    conditional_k2_mol_m3: Positive
    conditional_kw_mol2_m6: Positive
    henry_concentration_over_fugacity_mol_m3_Pa: Positive
    overall_gas_liquid_transfer_velocity_m_s: Nonnegative
    liquid_volume_flux_m3_s: float
    incoming_total_inorganic_carbon_mol_m3: Nonnegative
    incoming_total_alkalinity_mol_m3: float
    wall_total_carbon_flux_mol_m2_s: float
    wall_total_alkalinity_flux_mol_m2_s: float
    pH_lower_bound: float = Field(ge=-2.0, le=15.0)
    pH_upper_bound: float = Field(ge=-2.0, le=15.0)
    constant_provider_id: str = Field(min_length=1)
    constant_provider_revision: str = Field(min_length=1)
    constant_source_record_id: str = Field(min_length=1)
    constant_evidence: Evidence
    flux_provider_id: str = Field(min_length=1)
    flux_provider_revision: str = Field(min_length=1)
    flux_source_record_id: str = Field(min_length=1)
    flux_evidence: Evidence
    interval_condition_and_flux_mapping_reviewed: bool

    @model_validator(mode="after")
    def validate_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must follow start")
        if self.pH_upper_bound <= self.pH_lower_bound:
            raise ValueError("pH root bracket must be ordered")
        if self.constant_provider_id != self.constant_evidence.source_id or self.constant_evidence.sha256 is None:
            raise ValueError("conditional-constant provider must match SHA-256-bearing Evidence")
        if self.flux_provider_id != self.flux_evidence.source_id or self.flux_evidence.sha256 is None:
            raise ValueError("wall-flux provider must match SHA-256-bearing Evidence")
        numeric = (
            self.temperature_K,
            self.conditional_k1_mol_m3,
            self.conditional_k2_mol_m3,
            self.conditional_kw_mol2_m6,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.overall_gas_liquid_transfer_velocity_m_s,
            self.liquid_volume_flux_m3_s,
            self.incoming_total_inorganic_carbon_mol_m3,
            self.incoming_total_alkalinity_mol_m3,
            self.wall_total_carbon_flux_mol_m2_s,
            self.wall_total_alkalinity_flux_mol_m2_s,
            self.pH_lower_bound,
            self.pH_upper_bound,
        )
        if any(isinstance(value, bool) or not math.isfinite(value) for value in numeric):
            raise ValueError("interval thermodynamic and flux values must be finite")
        return self


class WetCo2TransientCarbonateHistoryRequest(Contract):
    initial_liquid_volume_m3: Positive
    initial_gas_fugacity_Pa: Nonnegative
    gas_molar_capacity_mol_Pa: Positive
    wall_area_m2: Positive
    initial_total_inorganic_carbon_mol_m3: Nonnegative
    initial_total_alkalinity_mol_m3: float
    intervals: tuple[WetCo2TransientCarbonateInterval, ...] = Field(min_length=1, max_length=10000)
    absolute_tolerance_mol: Positive = 1e-10
    absolute_tolerance_fugacity_Pa: Positive = 1e-7
    relative_tolerance: float = Field(default=1e-8, gt=0.0, lt=1.0)
    maximum_step_s: Positive | None = None
    initial_state_evidence: Evidence
    initial_state_provider_id: str = Field(min_length=1)
    initial_state_provider_revision: str = Field(min_length=1)
    initial_state_record_id: str = Field(min_length=1)
    equilibrium_model_scope_reviewed: bool
    ideal_carbonate_only_activity_assumption_reviewed: bool
    finite_gas_and_well_mixed_liquid_basis_reviewed: bool
    intervalwise_constant_input_and_operator_split_reviewed: bool
    physical_scope_and_clock_match_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if self.initial_state_provider_id != self.initial_state_evidence.source_id or self.initial_state_evidence.sha256 is None:
            raise ValueError("initial-state provider must match SHA-256-bearing Evidence")
        for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True):
            if left.end_time_s != right.start_time_s:
                raise ValueError("intervals must be contiguous exact time knots")
        return self


def _carbonate_state(total_carbon: float, alkalinity: float, interval: WetCo2TransientCarbonateInterval):
    """Return an ideal carbonate-only equilibrium state at fixed DIC and alkalinity."""
    if not math.isfinite(total_carbon) or total_carbon < 0.0 or not math.isfinite(alkalinity):
        return None

    def at_ph(pH):
        try:
            h = 1000.0 * 10.0 ** (-pH)
            k1, k2, kw = interval.conditional_k1_mol_m3, interval.conditional_k2_mol_m3, interval.conditional_kw_mol2_m6
            denom = h * h + k1 * h + k1 * k2
            if not all(math.isfinite(value) and value > 0.0 for value in (h, denom)):
                return None
            co2star = total_carbon * h * h / denom
            bicarbonate = total_carbon * k1 * h / denom
            carbonate = total_carbon * k1 * k2 / denom
            hydroxide = kw / h
            computed_alk = bicarbonate + 2.0 * carbonate + hydroxide - h
            if not all(math.isfinite(value) and value >= 0.0 for value in (co2star, bicarbonate, carbonate, hydroxide)) or not math.isfinite(computed_alk):
                return None
            return {
                "pH_ideal_concentration_scale": pH,
                "co2star_mol_m3": co2star,
                "bicarbonate_mol_m3": bicarbonate,
                "carbonate_mol_m3": carbonate,
                "hydrogen_ion_mol_m3": h,
                "hydroxide_mol_m3": hydroxide,
                "carbonate_only_alkalinity_mol_m3": computed_alk,
            }
        except (OverflowError, ZeroDivisionError):
            return None

    lo, hi = interval.pH_lower_bound, interval.pH_upper_bound
    left, right = at_ph(lo), at_ph(hi)
    if left is None or right is None:
        return None
    flo, fhi = left["carbonate_only_alkalinity_mol_m3"] - alkalinity, right["carbonate_only_alkalinity_mol_m3"] - alkalinity
    if flo == 0.0:
        return left
    if fhi == 0.0:
        return right
    if flo * fhi > 0.0:
        return None
    state = left
    for _ in range(160):
        mid = lo + (hi - lo) * 0.5
        state = at_ph(mid)
        if state is None:
            return None
        residual = state["carbonate_only_alkalinity_mol_m3"] - alkalinity
        if residual == 0.0 or mid == lo or mid == hi:
            return state
        if (residual > 0.0) == (flo > 0.0):
            lo, flo = mid, residual
        else:
            hi, fhi = mid, residual
    return state if abs(state["carbonate_only_alkalinity_mol_m3"] - alkalinity) <= max(1e-10, abs(alkalinity) * 1e-10) else None


def evaluate_wet_co2_transient_carbonate_history(
    request: WetCo2TransientCarbonateHistoryRequest,
    *,
    solve_ivp=None,
) -> Calculation:
    """Integrate gas-liquid CO2 exchange, DIC and alkalinity with equilibrium speciation."""
    if solve_ivp is None:
        try:
            from scipy.integrate import solve_ivp as scipy_solve_ivp
        except ImportError:
            return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "optional_scipy_runtime_unavailable"})
        solve_ivp = scipy_solve_ivp
    flags = {
        "equilibrium_model_scope_reviewed": request.equilibrium_model_scope_reviewed,
        "ideal_carbonate_only_activity_assumption_reviewed": request.ideal_carbonate_only_activity_assumption_reviewed,
        "finite_gas_and_well_mixed_liquid_basis_reviewed": request.finite_gas_and_well_mixed_liquid_basis_reviewed,
        "intervalwise_constant_input_and_operator_split_reviewed": request.intervalwise_constant_input_and_operator_split_reviewed,
        "physical_scope_and_clock_match_reviewed": request.physical_scope_and_clock_match_reviewed,
    }
    missing = [key for key, value in flags.items() if not value]
    times = [request.intervals[0].start_time_s] + [row.end_time_s for row in request.intervals]
    base = {
        "model_id": MODEL_ID,
        "time_s": times,
        "initial_total_inorganic_carbon_mol_m3": request.initial_total_inorganic_carbon_mol_m3,
        "initial_total_alkalinity_mol_m3": request.initial_total_alkalinity_mol_m3,
        "wall_area_m2": request.wall_area_m2,
        "interval_count": len(request.intervals),
        "interpolation_performed": False,
        "activity_model": "caller-conditional ideal concentration constants",
        "aqueous_network_complete": False,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    volume = request.initial_liquid_volume_m3
    beta = request.gas_molar_capacity_mol_Pa
    state = [request.initial_total_inorganic_carbon_mol_m3 * volume, request.initial_total_alkalinity_mol_m3 * volume, request.initial_gas_fugacity_Pa, 0.0, 0.0, 0.0, 0.0, 0.0]
    history = []
    ledger = []
    first_speciation = _carbonate_state(state[0] / volume, state[1] / volume, request.intervals[0])
    if first_speciation is None:
        return Calculation(status="out_of_scope", values=base | {"reason": "initial_carbonate_alkalinity_state_outside_pH_bracket"})
    history.append({
        "time_s": times[0],
        "liquid_volume_m3": volume,
        "gas_fugacity_Pa": state[2],
        "gas_inventory_mol": beta * state[2],
        "total_inorganic_carbon_mol_m3": state[0] / volume,
        "total_alkalinity_mol_m3": state[1] / volume,
        "species_mol_m3": first_speciation,
    })
    for index, interval in enumerate(request.intervals):
        if not interval.interval_condition_and_flux_mapping_reviewed:
            return Calculation(status="needs_data", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "interval_flux_or_condition_mapping_not_reviewed"})
        dt = interval.end_time_s - interval.start_time_s
        liquid_flux = interval.liquid_volume_flux_m3_s
        volume_end = volume + liquid_flux * dt
        if volume_end <= 0.0 or not math.isfinite(volume_end):
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "liquid_volume_nonpositive"})
        interval_state = list(state)

        def rhs(t, y):
            current_volume = volume + liquid_flux * (t - interval.start_time_s)
            if current_volume <= 0.0:
                raise ArithmeticError("liquid volume reached zero")
            carbon = y[0] / current_volume
            alk = y[1] / current_volume
            chemistry = _carbonate_state(carbon, alk, interval)
            if chemistry is None:
                raise ArithmeticError("carbonate equilibrium root left caller pH bracket")
            transfer = request.wall_area_m2 * interval.overall_gas_liquid_transfer_velocity_m_s * (
                interval.henry_concentration_over_fugacity_mol_m3_Pa * y[2] - chemistry["co2star_mol_m3"]
            )
            if liquid_flux > 0.0:
                carbon_water = liquid_flux * interval.incoming_total_inorganic_carbon_mol_m3
                alk_water = liquid_flux * interval.incoming_total_alkalinity_mol_m3
            else:
                carbon_water = liquid_flux * carbon
                alk_water = liquid_flux * alk
            carbon_wall = request.wall_area_m2 * interval.wall_total_carbon_flux_mol_m2_s
            alk_wall = request.wall_area_m2 * interval.wall_total_alkalinity_flux_mol_m2_s
            return [
                transfer + carbon_water + carbon_wall,
                alk_water + alk_wall,
                -transfer / beta,
                carbon_wall,
                alk_wall,
                transfer,
                carbon_water,
                alk_water,
            ]

        try:
            solution = solve_ivp(
                rhs,
                (interval.start_time_s, interval.end_time_s),
                state,
                method="DOP853",
                rtol=request.relative_tolerance,
                atol=[request.absolute_tolerance_mol, request.absolute_tolerance_mol, request.absolute_tolerance_fugacity_Pa] + [request.absolute_tolerance_mol] * 5,
                max_step=request.maximum_step_s if request.maximum_step_s is not None else math.inf,
            )
        except (ArithmeticError, OverflowError, ValueError) as exc:
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "coupled_gas_carbonate_ode_failed", "detail": str(exc)})
        if not solution.success or solution.y.shape[1] == 0:
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "coupled_gas_carbonate_solver_failed", "detail": str(solution.message)})
        end_state = [float(solution.y[i, -1]) for i in range(8)]
        if any(not math.isfinite(value) for value in end_state) or end_state[0] < -request.absolute_tolerance_mol or end_state[2] < -request.absolute_tolerance_fugacity_Pa:
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "negative_or_nonfinite_carbon_or_gas_inventory"})
        carbon_end = end_state[0] / volume_end
        alk_end = end_state[1] / volume_end
        final_chemistry = _carbonate_state(carbon_end, alk_end, interval)
        if final_chemistry is None:
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "endpoint_speciation_outside_pH_bracket"})
        carbon_wall = end_state[3] - interval_state[3]
        alk_wall = end_state[4] - interval_state[4]
        transfer = end_state[5] - interval_state[5]
        carbon_water = end_state[6] - interval_state[6]
        alk_water = end_state[7] - interval_state[7]
        carbon_residual = (end_state[0] - interval_state[0]) + beta * (end_state[2] - interval_state[2]) - carbon_wall - carbon_water
        alk_residual = (end_state[1] - interval_state[1]) - alk_wall - alk_water
        carbon_scale = max(abs(end_state[0]), abs(interval_state[0]), abs(carbon_wall), abs(carbon_water), abs(transfer), 1e-30)
        alk_scale = max(abs(end_state[1]), abs(interval_state[1]), abs(alk_wall), abs(alk_water), 1e-30)
        carbon_tolerance = request.absolute_tolerance_mol + request.relative_tolerance * carbon_scale
        alk_tolerance = request.absolute_tolerance_mol + request.relative_tolerance * alk_scale
        if abs(carbon_residual) > carbon_tolerance or abs(alk_residual) > alk_tolerance:
            return Calculation(status="out_of_scope", values=base | {"committed_interval_count": index, "history_prefix": history, "interval_ledger": ledger, "failed_interval_index": index, "reason": "carbon_or_alkalinity_inventory_closure_failed", "carbon_balance_residual_mol": carbon_residual, "alkalinity_balance_residual_mol": alk_residual})
        ledger.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "temperature_K": interval.temperature_K,
            "conditional_constant_record_id": interval.constant_source_record_id,
            "conditional_constant_provider_id": interval.constant_provider_id,
            "conditional_constant_provider_revision": interval.constant_provider_revision,
            "conditional_constant_evidence_sha256": interval.constant_evidence.sha256,
            "wall_flux_record_id": interval.flux_source_record_id,
            "wall_flux_provider_id": interval.flux_provider_id,
            "wall_flux_evidence_sha256": interval.flux_evidence.sha256,
            "gas_liquid_transfer_mol": transfer,
            "wall_carbon_transfer_mol": carbon_wall,
            "waterborne_carbon_transfer_mol": carbon_water,
            "wall_alkalinity_transfer_mol_eq": alk_wall,
            "waterborne_alkalinity_transfer_mol_eq": alk_water,
            "carbon_balance_residual_mol": carbon_residual,
            "carbon_balance_tolerance_mol": carbon_tolerance,
            "alkalinity_balance_residual_mol_eq": alk_residual,
            "alkalinity_balance_tolerance_mol_eq": alk_tolerance,
        })
        state, volume = end_state, volume_end
        history.append({
            "time_s": interval.end_time_s,
            "liquid_volume_m3": volume,
            "gas_fugacity_Pa": state[2],
            "gas_inventory_mol": beta * state[2],
            "total_inorganic_carbon_mol_m3": carbon_end,
            "total_alkalinity_mol_m3": alk_end,
            "species_mol_m3": final_chemistry,
        })
    return Calculation(values=base | {
        "all_intervals_computed": True,
        "final_liquid_volume_m3": volume,
        "final_gas_fugacity_Pa": state[2],
        "final_gas_inventory_mol": beta * state[2],
        "final_total_inorganic_carbon_mol_m3": state[0] / volume,
        "final_total_alkalinity_mol_m3": state[1] / volume,
        "state_history": history,
        "interval_ledger": ledger,
    }, notes=(
        "At every ODE evaluation, ideal carbonate-only equilibrium is resolved from caller DIC, alkalinity and interval-specific conditional constants.",
        "Gas exchange acts on dissolved CO2-star; caller wall source uses total carbon and alkalinity-equivalent fluxes.",
        "Other buffer systems, nonideal activity, complete speciation, mineral reactions and corrosion kinetics are not represented.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        WetCo2TransientCarbonateHistoryRequest,
        evaluate_wet_co2_transient_carbonate_history,
        {
            "time_s": "s",
            "temperature_K": "K",
            "gas_fugacity_Pa": "Pa",
            "gas_inventory_mol": "mol",
            "total_inorganic_carbon_mol_m3": "mol/m3",
            "total_alkalinity_mol_m3": "mol/m3 as charge equivalents",
            "species_mol_m3.*": "mol/m3",
            "carbon_balance_residual_mol": "mol",
            "alkalinity_balance_residual_mol_eq": "mol as charge equivalents",
        },
        (
            "Only the ideal carbonate-only system is equilibrated using caller conditional K1, K2 and Kw values with explicit pH support.",
            "Finite gas exchange is coupled to dissolved CO2-star; total carbon and alkalinity inventories receive caller wall and waterborne fluxes.",
            "The model requires SciPy DOP853 at runtime and performs no interpolation across exact caller interval knots.",
        ),
        (SOURCE_ID, FLUX_SOURCE_ID, TRANSFER_SOURCE_ID, "scipy_integrate_solve_ivp", "scipy_integrate_dop853"),
        runtime_dependency_names=("scipy",),
    )]
