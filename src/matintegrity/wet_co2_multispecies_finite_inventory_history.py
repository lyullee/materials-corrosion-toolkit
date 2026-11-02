"""Transient finite gas/liquid wet-CO2 inventory with caller-supplied wall species fluxes."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_gas_multispecies_wall_flux_history"
SOURCE_ID = "caller_wet_co2_electrochemical_species_flux_interval_schedule"
TRANSFER_SOURCE_ID = "caller_finite_gas_two_film_and_variable_liquid_transfer"
CO2STAR = "CO2_star"


class WetCo2SpeciesFluxInterval(Contract):
    """One exact interval of caller-owned signed inward wall molar fluxes."""

    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    inward_species_flux_mol_m2_s: dict[str, float]
    source_model_id: str = Field(min_length=1)
    source_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_record_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    evidence: Evidence
    flux_mapping_reviewed: bool

    @model_validator(mode="after")
    def validate_flux_schedule(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("flux interval end must be after start")
        if not self.inward_species_flux_mol_m2_s:
            raise ValueError("at least one explicit species flux is required")
        if self.provider_id != self.evidence.source_id:
            raise ValueError("flux provider ID must match Evidence source ID")
        if any(not key or isinstance(value, bool) or not math.isfinite(value) for key, value in self.inward_species_flux_mol_m2_s.items()):
            raise ValueError("species fluxes must be finite signed molar rates with nonempty species IDs")
        return self


class WetCo2FiniteGasMultispeciesHistoryRequest(Contract):
    species_ids: tuple[str, ...] = Field(min_length=1, max_length=64)
    co2star_species_id: str = CO2STAR
    initial_liquid_concentration_mol_m3: tuple[Nonnegative, ...]
    initial_liquid_volume_m3: Positive
    initial_gas_fugacity_Pa: Nonnegative
    gas_molar_capacity_mol_Pa: Positive
    wall_area_m2: Positive
    intervals: tuple[WetCo2SpeciesFluxInterval, ...] = Field(min_length=1, max_length=10000)
    henry_concentration_over_fugacity_mol_m3_Pa: Positive
    overall_gas_liquid_transfer_velocity_m_s: Nonnegative
    liquid_volume_flux_m3_s: tuple[float, ...]
    incoming_liquid_concentration_mol_m3: tuple[tuple[Nonnegative, ...], ...]
    absolute_tolerance_mol: Positive = 1e-10
    absolute_tolerance_fugacity_Pa: Positive = 1e-7
    relative_tolerance: Positive = 1e-8
    maximum_step_s: Positive | None = None
    initial_state_basis_reviewed: bool
    gas_liquid_transfer_parameter_reviewed: bool
    variable_liquid_flux_and_inflow_basis_reviewed: bool
    wall_flux_direction_and_area_mapping_reviewed: bool
    source_scope_and_clock_match_reviewed: bool

    @model_validator(mode="after")
    def validate_history_layout(self):
        count = len(self.species_ids)
        if len(set(self.species_ids)) != count or self.co2star_species_id not in self.species_ids:
            raise ValueError("species IDs must be unique and include the CO2-star inventory species")
        if len(self.initial_liquid_concentration_mol_m3) != count:
            raise ValueError("initial concentrations must match declared species order")
        if len(self.liquid_volume_flux_m3_s) != len(self.intervals) or len(self.incoming_liquid_concentration_mol_m3) != len(self.intervals):
            raise ValueError("one liquid flux and inflow composition are required per exact interval")
        if any(len(row) != count for row in self.incoming_liquid_concentration_mol_m3):
            raise ValueError("every inflow concentration vector must match the species order")
        for index, (left, right) in enumerate(zip(self.intervals[:-1], self.intervals[1:], strict=True)):
            if left.end_time_s != right.start_time_s:
                raise ValueError("intervals must be contiguous exact knots")
            if left.end_time_s <= left.start_time_s:
                raise ValueError("each interval must have positive duration")
        if self.intervals[-1].end_time_s <= self.intervals[0].start_time_s:
            raise ValueError("history must have positive duration")
        for row in self.intervals:
            if tuple(row.inward_species_flux_mol_m2_s) != self.species_ids:
                raise ValueError("each interval flux mapping keys and order must exactly match species_ids")
        return self


def evaluate_wet_co2_finite_gas_multispecies_history(
    request: WetCo2FiniteGasMultispeciesHistoryRequest,
    *,
    solve_ivp=None,
) -> Calculation:
    """Integrate finite gas/liquid inventories and an explicit wall-flux schedule.

    Liquid inventory states are moles, gas state is fugacity, and auxiliary
    states accumulate signed wall, waterborne, and gas/liquid transfer moles.
    Positive liquid-volume flux means incoming well-mixed liquid; negative
    flux removes liquid at the instantaneous bulk composition. Interval wall
    fluxes and transfer parameters are held constant; no chemistry is inferred.
    """
    if solve_ivp is None:
        try:
            from scipy.integrate import solve_ivp as scipy_solve_ivp
        except ImportError:
            return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "optional_scipy_runtime_unavailable"})
        solve_ivp = scipy_solve_ivp

    n = len(request.species_ids)
    co2_index = request.species_ids.index(request.co2star_species_id)
    times = [request.intervals[0].start_time_s] + [item.end_time_s for item in request.intervals]
    volume = request.initial_liquid_volume_m3
    beta = request.gas_molar_capacity_mol_Pa
    initial_fugacity = request.initial_gas_fugacity_Pa
    initial_liquid = [value * volume for value in request.initial_liquid_concentration_mol_m3]
    state = initial_liquid + [initial_fugacity] + [0.0] * (3 * n)
    base = {
        "model_id": MODEL_ID,
        "species_ids": list(request.species_ids),
        "co2star_species_id": request.co2star_species_id,
        "time_s": times,
        "liquid_inventory_unit": "mol",
        "gas_fugacity_unit": "Pa",
        "wall_flux_area_m2": request.wall_area_m2,
        "interval_count": len(request.intervals),
        "all_intervals_computed": False,
        "interpolation_performed": False,
    }
    history = [{
        "time_s": times[0],
        "liquid_volume_m3": volume,
        "gas_fugacity_Pa": initial_fugacity,
        "liquid_inventory_mol": dict(zip(request.species_ids, initial_liquid, strict=True)),
        "liquid_concentration_mol_m3": dict(zip(request.species_ids, request.initial_liquid_concentration_mol_m3, strict=True)),
    }]
    ledger = []
    review_flags = {
        "initial_state_basis_reviewed": request.initial_state_basis_reviewed,
        "gas_liquid_transfer_parameter_reviewed": request.gas_liquid_transfer_parameter_reviewed,
        "variable_liquid_flux_and_inflow_basis_reviewed": request.variable_liquid_flux_and_inflow_basis_reviewed,
        "wall_flux_direction_and_area_mapping_reviewed": request.wall_flux_direction_and_area_mapping_reviewed,
        "source_scope_and_clock_match_reviewed": request.source_scope_and_clock_match_reviewed,
    }
    missing = [key for key, value in review_flags.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    for index, (interval, liquid_flux, inflow) in enumerate(zip(
        request.intervals,
        request.liquid_volume_flux_m3_s,
        request.incoming_liquid_concentration_mol_m3,
        strict=True,
    )):
        dt = interval.end_time_s - interval.start_time_s
        volume_end = volume + liquid_flux * dt
        if not math.isfinite(volume_end) or volume_end <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "reason": "liquid_volume_nonpositive_at_interval_end",
            })
        flux = tuple(interval.inward_species_flux_mol_m2_s[item] for item in request.species_ids)
        if not interval.flux_mapping_reviewed:
            return Calculation(status="needs_data", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "reason": "wall_flux_species_and_area_mapping_not_reviewed",
            })
        liquid_state = state[:n]
        gas_state = state[n]
        auxiliary_start = state[n + 1:]

        def rhs(t, y):
            elapsed = t - interval.start_time_s
            current_volume = volume + liquid_flux * elapsed
            if current_volume <= 0.0:
                raise ArithmeticError("liquid volume reached zero")
            c = [y[k] / current_volume for k in range(n)]
            transfer = request.wall_area_m2 * request.overall_gas_liquid_transfer_velocity_m_s * (
                request.henry_concentration_over_fugacity_mol_m3_Pa * y[n] - c[co2_index]
            )
            derivatives = []
            for k in range(n):
                gas_liquid = transfer if k == co2_index else 0.0
                wall = request.wall_area_m2 * flux[k]
                waterborne = liquid_flux * inflow[k] if liquid_flux > 0.0 else liquid_flux * c[k]
                derivatives.append(gas_liquid + wall + waterborne)
            transfer_per_species = [0.0] * n
            transfer_per_species[co2_index] = transfer
            waterborne_per_species = [
                liquid_flux * inflow[k] if liquid_flux > 0.0 else liquid_flux * c[k]
                for k in range(n)
            ]
            return derivatives + [-transfer / beta] + [request.wall_area_m2 * value for value in flux] + waterborne_per_species + transfer_per_species

        try:
            solution = solve_ivp(
                rhs,
                (interval.start_time_s, interval.end_time_s),
                state,
                method="DOP853",
                rtol=request.relative_tolerance,
                atol=([request.absolute_tolerance_mol] * n
                      + [request.absolute_tolerance_fugacity_Pa]
                      + [request.absolute_tolerance_mol] * (3 * n)),
                max_step=request.maximum_step_s if request.maximum_step_s is not None else math.inf,
            )
        except (ArithmeticError, OverflowError, ValueError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "reason": "interval_ode_evaluation_failed",
                "detail": str(exc),
            })
        if not solution.success or solution.y.shape[1] == 0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "reason": "interval_ode_solver_failed",
                "detail": str(solution.message),
            })
        end_state = [float(solution.y[k, -1]) for k in range(solution.y.shape[0])]
        concentrations_end = [value / volume_end for value in end_state[:n]]
        if (
            any(not math.isfinite(value) for value in end_state)
            or any(value < -request.absolute_tolerance_mol for value in end_state[:n])
            or end_state[n] < -request.absolute_tolerance_fugacity_Pa
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "reason": "negative_or_nonfinite_inventory_state",
            })
        cumulative_wall = end_state[n + 1:n + 1 + n]
        cumulative_water = end_state[n + 1 + n:n + 1 + 2 * n]
        cumulative_transfer = end_state[n + 1 + 2 * n:n + 1 + 3 * n]
        rows = []
        for k, species in enumerate(request.species_ids):
            gas_delta = beta * (end_state[n] - gas_state) if k == co2_index else 0.0
            liquid_change = end_state[k] - liquid_state[k]
            wall_delta = cumulative_wall[k] - auxiliary_start[k]
            water_delta = cumulative_water[k] - auxiliary_start[n + k]
            transfer_delta = cumulative_transfer[k] - auxiliary_start[2 * n + k]
            residual = liquid_change + gas_delta - wall_delta - water_delta
            scale = max(abs(liquid_state[k]), abs(end_state[k]), abs(gas_delta), abs(wall_delta), abs(water_delta), 1e-30)
            tolerance = request.absolute_tolerance_mol + request.relative_tolerance * scale
            rows.append({
                "species_id": species,
                "liquid_inventory_start_mol": liquid_state[k],
                "liquid_inventory_end_mol": end_state[k],
                "liquid_concentration_end_mol_m3": concentrations_end[k],
                "gas_inventory_change_mol": gas_delta,
                "wall_inventory_change_mol": wall_delta,
                "waterborne_inventory_change_mol": water_delta,
                "gas_liquid_transfer_change_mol": transfer_delta,
                "balance_residual_mol": residual,
                "balance_tolerance_mol": tolerance,
            })
            if abs(residual) > tolerance:
                return Calculation(status="out_of_scope", values=base | {
                    "committed_interval_count": index,
                    "failed_interval_index": index,
                    "species_balance_prefix": rows,
                    "reason": "species_inventory_balance_closure_failed",
                })
        ledger.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "source_model_id": interval.source_model_id,
            "source_result_sha256": interval.source_result_sha256,
            "source_record_id": interval.source_record_id,
            "provider_id": interval.provider_id,
            "provider_revision": interval.provider_revision,
            "evidence_sha256": interval.evidence.sha256,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "volume_start_m3": volume,
            "volume_end_m3": volume_end,
            "species_balances": rows,
        })
        state = end_state
        volume = volume_end
        history.append({
            "time_s": interval.end_time_s,
            "liquid_volume_m3": volume,
            "gas_fugacity_Pa": state[n],
            "liquid_inventory_mol": dict(zip(request.species_ids, state[:n], strict=True)),
            "liquid_concentration_mol_m3": dict(zip(request.species_ids, concentrations_end, strict=True)),
        })

    return Calculation(values=base | {
        "all_intervals_computed": True,
        "final_liquid_volume_m3": volume,
        "final_gas_fugacity_Pa": state[n],
        "final_gas_inventory_mol": beta * state[n],
        "initial_gas_inventory_mol": beta * initial_fugacity,
        "final_liquid_inventory_mol": dict(zip(request.species_ids, state[:n], strict=True)),
        "final_liquid_concentration_mol_m3": dict(zip(request.species_ids, [state[k] / volume for k in range(n)], strict=True)),
        "state_history": history,
        "interval_ledger": ledger,
    }, notes=(
        "Gas-liquid exchange is coupled only to the declared CO2-star species via the caller effective transfer velocity and Henry coefficient.",
        "Wall fluxes are caller-supplied exact-interval species molar fluxes and are held constant over their interval.",
        "Other aqueous species are independent inventory states; no acid-base reaction, speciation, electroneutrality or reaction kinetics are solved.",
        "Positive liquid-volume flux is well-mixed inflow; negative flux is outflow at instantaneous bulk concentrations.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        WetCo2FiniteGasMultispeciesHistoryRequest,
        evaluate_wet_co2_finite_gas_multispecies_history,
        {
            "time_s": "s",
            "gas_fugacity_Pa": "Pa",
            "final_gas_inventory_mol": "mol",
            "final_liquid_inventory_mol.*": "mol",
            "final_liquid_concentration_mol_m3.*": "mol/m3",
            "species_balances[].wall_inventory_change_mol": "mol",
        },
        (
            "The interval species-flux schedule, transfer coefficient, Henry coefficient, inflow, area and initial inventories are caller owned.",
            "A finite gas inventory exchanges with only the explicitly designated CO2-star liquid inventory; no aqueous reaction network or speciation is inferred.",
            "The model requires SciPy DOP853 at runtime and reports interval-level species material balance closure.",
        ),
        (SOURCE_ID, TRANSFER_SOURCE_ID, "scipy_integrate_solve_ivp", "scipy_integrate_dop853"),
        runtime_dependency_names=("scipy",),
    )]
