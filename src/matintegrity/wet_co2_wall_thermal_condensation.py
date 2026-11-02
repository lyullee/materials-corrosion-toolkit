"""Lumped wall thermal response coupled to finite-gas water condensation."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_lumped_wall_thermal_condensation_history"
SOURCE_SATURATION = "caller_temperature_tabulated_wall_water_saturation_fugacity"
SOURCE_THERMAL = "caller_lumped_wall_heat_capacity_and_boundary_flux"
SOURCE_TRANSFER = "caller_finite_gas_water_film_transfer_parameters"
SOURCE_METHOD = "lumped_wall_energy_and_finite_gas_water_mass_balance"
R_GAS = 8.31446261815324
M_WATER = 0.01801528
MAX_INTERVALS = 20_000
MAX_SATURATION_POINTS = 10_000


class WallWaterSaturationPoint(Contract):
    temperature_K: float = Field(gt=0)
    water_fugacity_Pa: float = Field(gt=0)

    @model_validator(mode="after")
    def finite(self):
        if not math.isfinite(self.temperature_K) or not math.isfinite(self.water_fugacity_Pa):
            raise ValueError("saturation-table values must be finite")
        return self


class LumpedWallCondensationInterval(Contract):
    """Piecewise-constant external and gas-side boundary over one interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    gas_temperature_K: float = Field(gt=0)
    gas_volume_m3: float = Field(gt=0)
    water_vapor_fugacity_coefficient: float = Field(gt=0)
    gas_film_molar_transfer_coefficient_mol_m2_s_Pa: float = Field(ge=0)
    transfer_area_m2: float = Field(gt=0)
    gas_to_wall_heat_transfer_coefficient_W_m2_K: float = Field(ge=0)
    external_wall_heat_flux_W_m2: float
    latent_heat_of_vaporization_J_kg: float = Field(gt=0)
    liquid_water_density_kg_m3: float = Field(gt=0)
    transfer_provider_id: str = Field(min_length=1)
    transfer_provider_revision: str = Field(min_length=1)
    transfer_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transfer_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    thermal_provider_id: str = Field(min_length=1)
    thermal_provider_revision: str = Field(min_length=1)
    thermal_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    thermal_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=64)
    interval_boundary_and_sign_reviewed: bool

    @model_validator(mode="after")
    def finite_and_provenance(self):
        values = (
            self.start_time_s, self.end_time_s, self.gas_temperature_K, self.gas_volume_m3,
            self.water_vapor_fugacity_coefficient,
            self.gas_film_molar_transfer_coefficient_mol_m2_s_Pa,
            self.transfer_area_m2, self.gas_to_wall_heat_transfer_coefficient_W_m2_K,
            self.external_wall_heat_flux_W_m2, self.latent_heat_of_vaporization_J_kg,
            self.liquid_water_density_kg_m3,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("all interval inputs must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must be later than start")
        if not {self.transfer_provider_id, self.thermal_provider_id}.issubset(
            {item.source_id for item in self.evidence}
        ):
            raise ValueError("Evidence must identify transfer and thermal boundary inputs")
        return self


class WetCo2LumpedWallThermalCondensationRequest(Contract):
    """Finite-gas water transfer coupled to lumped wall energy on a fixed patch."""

    schema_version: Literal["matintegrity.wet_co2_lumped_wall_thermal_condensation_history.v1"] = (
        "matintegrity.wet_co2_lumped_wall_thermal_condensation_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_wall_temperature_K: float = Field(gt=0)
    initial_gas_water_vapor_moles: float = Field(ge=0)
    initial_wall_water_areal_inventory_kg_m2: float = Field(ge=0)
    wall_areal_heat_capacity_J_m2_K: float = Field(gt=0)
    saturation_fugacity_table: tuple[WallWaterSaturationPoint, ...] = Field(
        min_length=2, max_length=MAX_SATURATION_POINTS
    )
    saturation_table_provider_id: str = Field(min_length=1)
    saturation_table_revision: str = Field(min_length=1)
    saturation_table_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    saturation_table_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    intervals: tuple[LumpedWallCondensationInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    rtol: float = Field(gt=0, le=1e-2)
    atol_temperature_K: float = Field(gt=0)
    atol_gas_moles: float = Field(gt=0)
    atol_liquid_kg_m2: float = Field(gt=0)
    atol_energy_J_m2: float = Field(gt=0)
    max_step_s: float = Field(gt=0)
    lumped_wall_temperature_and_fixed_patch_reviewed: bool
    energy_boundary_and_latent_heat_sign_reviewed: bool
    finite_gas_ideal_component_pressure_reviewed: bool
    saturation_table_basis_and_support_reviewed: bool
    no_wall_phase_change_or_spatial_gradient_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def ordered_and_supported(self):
        values = (
            self.initial_wall_temperature_K, self.initial_gas_water_vapor_moles,
            self.initial_wall_water_areal_inventory_kg_m2, self.wall_areal_heat_capacity_J_m2_K,
            self.rtol, self.atol_temperature_K, self.atol_gas_moles,
            self.atol_liquid_kg_m2, self.atol_energy_J_m2, self.max_step_s,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("thermal state, solver controls and inventories must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at elapsed time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous")
        temperatures = [point.temperature_K for point in self.saturation_fugacity_table]
        fugacities = [point.water_fugacity_Pa for point in self.saturation_fugacity_table]
        if any(right <= left for left, right in zip(temperatures[:-1], temperatures[1:])):
            raise ValueError("saturation-table temperatures must be strictly increasing")
        if any(right <= left for left, right in zip(fugacities[:-1], fugacities[1:])):
            raise ValueError("water saturation fugacity must increase strictly with temperature")
        if not any(
            row.source_id == self.saturation_table_provider_id and row.sha256 == self.saturation_table_sha256
            for row in self.saturation_table_evidence
        ):
            raise ValueError("saturation table digest must match its Evidence")
        return self


def _interpolate_saturation_fugacity(table: tuple[WallWaterSaturationPoint, ...], temperature_K: float) -> float:
    if temperature_K < table[0].temperature_K or temperature_K > table[-1].temperature_K:
        raise ArithmeticError("wall temperature left caller saturation-table support")
    for left, right in zip(table[:-1], table[1:]):
        if left.temperature_K <= temperature_K <= right.temperature_K:
            fraction = (temperature_K - left.temperature_K) / (right.temperature_K - left.temperature_K)
            return left.water_fugacity_Pa + fraction * (right.water_fugacity_Pa - left.water_fugacity_Pa)
    return table[-1].water_fugacity_Pa


def evaluate_wet_co2_lumped_wall_thermal_condensation(
    request: WetCo2LumpedWallThermalCondensationRequest,
    *,
    scipy=None,
    solve_ivp=None,
) -> Calculation:
    """Integrate wall temperature and finite gas/liquid water inventories together."""
    if solve_ivp is None:
        if scipy is not None:
            solve_ivp = scipy.integrate.solve_ivp
        else:
            try:
                from scipy.integrate import solve_ivp as scipy_solve_ivp
            except ImportError:
                return Calculation(status="needs_data", values={
                    "model_id": MODEL_ID,
                    "reason": "optional_scipy_runtime_unavailable",
                })
            solve_ivp = scipy_solve_ivp

    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha,
        "wall_areal_heat_capacity_J_m2_K": request.wall_areal_heat_capacity_J_m2_K,
        "saturation_table_provider_id": request.saturation_table_provider_id,
        "saturation_table_revision": request.saturation_table_revision,
        "saturation_table_sha256": request.saturation_table_sha256,
        "time_s": [request.intervals[0].start_time_s, *[row.end_time_s for row in request.intervals]],
    }
    reviews = (
        "lumped_wall_temperature_and_fixed_patch_reviewed",
        "energy_boundary_and_latent_heat_sign_reviewed",
        "finite_gas_ideal_component_pressure_reviewed",
        "saturation_table_basis_and_support_reviewed",
        "no_wall_phase_change_or_spatial_gradient_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].interval_boundary_and_sign_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_boundary_and_sign_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    # y = [wall temperature, gas water moles, wall water kg/m2,
    #      cumulative external heat, sensible exchange, latent heat]
    state = [
        request.initial_wall_temperature_K,
        request.initial_gas_water_vapor_moles,
        request.initial_wall_water_areal_inventory_kg_m2,
        0.0,
        0.0,
        0.0,
    ]
    history = [{
        "time_s": 0.0,
        "wall_temperature_K": state[0],
        "gas_water_vapor_moles": state[1],
        "wall_water_areal_inventory_kg_m2": state[2],
        "wall_equivalent_film_thickness_m": state[2] / request.intervals[0].liquid_water_density_kg_m3,
        "cumulative_external_heat_J_m2": 0.0,
        "cumulative_sensible_heat_J_m2": 0.0,
        "cumulative_latent_heat_J_m2": 0.0,
        "origin": "caller_initial_state",
    }]
    ledger: list[dict] = []
    for index, interval in enumerate(request.intervals):
        start_state = list(state)

        def rhs(_time, y):
            wall_temperature, gas_moles, liquid_areal, _q_external, _q_sensible, _q_latent = y
            if gas_moles < 0.0:
                raise ArithmeticError("gas water inventory became negative")
            saturation_fugacity = _interpolate_saturation_fugacity(
                request.saturation_fugacity_table, wall_temperature
            )
            gas_pressure = gas_moles * R_GAS * interval.gas_temperature_K / interval.gas_volume_m3
            gas_fugacity = interval.water_vapor_fugacity_coefficient * gas_pressure
            molar_flux_gas_to_wall = interval.gas_film_molar_transfer_coefficient_mol_m2_s_Pa * (
                gas_fugacity - saturation_fugacity
            )
            if liquid_areal <= 0.0 and molar_flux_gas_to_wall < 0.0:
                molar_flux_gas_to_wall = 0.0
            gas_rate = -interval.transfer_area_m2 * molar_flux_gas_to_wall
            liquid_mass_flux = molar_flux_gas_to_wall * M_WATER
            sensible_flux = interval.gas_to_wall_heat_transfer_coefficient_W_m2_K * (
                interval.gas_temperature_K - wall_temperature
            )
            latent_flux = interval.latent_heat_of_vaporization_J_kg * liquid_mass_flux
            wall_temperature_rate = (
                interval.external_wall_heat_flux_W_m2 + sensible_flux + latent_flux
            ) / request.wall_areal_heat_capacity_J_m2_K
            derivatives = (
                wall_temperature_rate,
                gas_rate,
                liquid_mass_flux,
                interval.external_wall_heat_flux_W_m2,
                sensible_flux,
                latent_flux,
            )
            if not all(math.isfinite(value) for value in derivatives):
                raise ArithmeticError("coupled wall state derivative exceeds finite support")
            return derivatives

        def wall_support_event(_time, y):
            return min(
                y[0] - request.saturation_fugacity_table[0].temperature_K,
                request.saturation_fugacity_table[-1].temperature_K - y[0],
            )

        wall_support_event.terminal = True
        wall_support_event.direction = -1
        try:
            result = solve_ivp(
                rhs,
                (interval.start_time_s, interval.end_time_s),
                state,
                method="DOP853",
                t_eval=[interval.end_time_s],
                rtol=request.rtol,
                atol=[
                    request.atol_temperature_K,
                    request.atol_gas_moles,
                    request.atol_liquid_kg_m2,
                    request.atol_energy_J_m2,
                    request.atol_energy_J_m2,
                    request.atol_energy_J_m2,
                ],
                max_step=min(request.max_step_s, interval.end_time_s - interval.start_time_s),
                events=wall_support_event,
            )
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": str(error),
            })
        if not result.success or result.y.shape[1] != 1 or result.t[-1] != interval.end_time_s:
            reason = "wall_temperature_left_saturation_table_support" if result.t_events[0].size else result.message
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": str(reason),
            })
        state = [float(value) for value in result.y[:, -1]]
        if state[2] < 0.0 and state[2] >= -10.0 * request.atol_liquid_kg_m2:
            state[2] = 0.0
        if state[1] < 0.0 or state[2] < 0.0 or not all(math.isfinite(value) for value in state):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "coupled state left nonnegative finite inventory domain",
            })
        energy_storage_change = request.wall_areal_heat_capacity_J_m2_K * (state[0] - start_state[0])
        external_change = state[3] - start_state[3]
        sensible_change = state[4] - start_state[4]
        latent_change = state[5] - start_state[5]
        energy_residual = energy_storage_change - external_change - sensible_change - latent_change
        if not all(math.isfinite(value) for value in (energy_storage_change, energy_residual)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "integrated wall energy exceeds finite support",
            })
        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "wall_temperature_start_K": start_state[0],
            "wall_temperature_end_K": state[0],
            "gas_water_vapor_moles_start": start_state[1],
            "gas_water_vapor_moles_end": state[1],
            "wall_water_areal_inventory_start_kg_m2": start_state[2],
            "wall_water_areal_inventory_end_kg_m2": state[2],
            "wall_equivalent_film_thickness_end_m": state[2] / interval.liquid_water_density_kg_m3,
            "external_heat_J_m2": external_change,
            "sensible_heat_J_m2": sensible_change,
            "latent_heat_J_m2": latent_change,
            "wall_energy_storage_change_J_m2": energy_storage_change,
            "wall_energy_balance_residual_J_m2": energy_residual,
            "solver_function_evaluations": int(result.nfev),
            "transfer_provider_id": interval.transfer_provider_id,
            "transfer_provider_revision": interval.transfer_provider_revision,
            "transfer_configuration_sha256": interval.transfer_configuration_sha256,
            "transfer_result_sha256": interval.transfer_result_sha256,
            "thermal_provider_id": interval.thermal_provider_id,
            "thermal_provider_revision": interval.thermal_provider_revision,
            "thermal_configuration_sha256": interval.thermal_configuration_sha256,
            "thermal_result_sha256": interval.thermal_result_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in interval.evidence],
        })
        history.append({
            "time_s": interval.end_time_s,
            "wall_temperature_K": state[0],
            "gas_water_vapor_moles": state[1],
            "wall_water_areal_inventory_kg_m2": state[2],
            "wall_equivalent_film_thickness_m": state[2] / interval.liquid_water_density_kg_m3,
            "cumulative_external_heat_J_m2": state[3],
            "cumulative_sensible_heat_J_m2": state[4],
            "cumulative_latent_heat_J_m2": state[5],
            "origin": "coupled_dop853_wall_heat_and_water_transfer",
        })
    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "final_wall_temperature_K": state[0],
        "final_gas_water_vapor_moles": state[1],
        "final_wall_water_areal_inventory_kg_m2": state[2],
        "state_history": history,
        "interval_ledger": ledger,
        "limitations": [
            "The wall is represented by one lumped temperature and a caller-supplied areal heat capacity.",
            "Water saturation fugacity is linearly interpolated only within the caller table; no property extrapolation occurs.",
            "Gas-side conditions, heat flux, heat-transfer coefficient, and latent heat are piecewise constant per interval.",
            "No through-wall gradient, substrate conduction network, brine/MEG activity, droplet or drainage model, scale, corrosion rate, or qualification is calculated.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2LumpedWallThermalCondensationRequest,
        evaluator=evaluate_wet_co2_lumped_wall_thermal_condensation,
        units={
            "final_wall_temperature_K": "K",
            "final_gas_water_vapor_moles": "mol",
            "final_wall_water_areal_inventory_kg_m2": "kg/m^2",
            "state_history[].cumulative_external_heat_J_m2": "J/m^2",
            "state_history[].cumulative_sensible_heat_J_m2": "J/m^2",
            "state_history[].cumulative_latent_heat_J_m2": "J/m^2",
            "interval_ledger[].wall_energy_balance_residual_J_m2": "J/m^2",
        },
        assumptions=(
            "A single wall temperature is governed by a lumped areal heat capacity and caller heat boundary terms.",
            "Finite gas water transfer uses the gas-fugacity to wall-saturation-fugacity driving force with caller transfer coefficient.",
            "Wall water vapor saturation fugacity is linearly interpolated within the caller's strictly increasing tabulated support.",
            "Latent heat is added to the wall for condensation and removed for evaporation; liquid depletion blocks further evaporation.",
        ),
        source_ids=(SOURCE_SATURATION, SOURCE_THERMAL, SOURCE_TRANSFER, SOURCE_METHOD, "scipy_integrate_solve_ivp", "scipy_integrate_dop853"),
        runtime_dependency_names=("scipy",),
    )]
