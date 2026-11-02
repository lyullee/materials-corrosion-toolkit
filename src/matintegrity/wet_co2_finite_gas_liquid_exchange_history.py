"""Exact exchange history for finite gas and well-mixed liquid CO2 inventories."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_gas_liquid_exchange_history"
SOURCE_ID = "caller_finite_gas_finite_liquid_two_film_balance"
MAX_INTERVALS = 5000


class WetCo2FiniteGasLiquidInterval(Contract):
    """Piecewise-constant transfer and gas-capacity data for one time interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    temperature_K: float = Field(gt=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_film_coefficient_m_s: float = Field(gt=0)
    gas_inventory_capacity_mol_Pa: float = Field(gt=0)
    henry_provider_id: str = Field(min_length=1)
    henry_provider_revision: str = Field(min_length=1)
    henry_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    henry_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gas_capacity_provider_id: str = Field(min_length=1)
    gas_capacity_provider_revision: str = Field(min_length=1)
    gas_capacity_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gas_capacity_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    film_provider_id: str = Field(min_length=1)
    film_provider_revision: str = Field(min_length=1)
    film_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    film_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    parameters_and_state_reviewed: bool

    @model_validator(mode="after")
    def validate_interval(self):
        values = (
            self.start_time_s, self.end_time_s, self.temperature_K,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa,
            self.liquid_film_coefficient_m_s,
            self.gas_inventory_capacity_mol_Pa,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("all interval values must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must be after start")
        evidence_ids = {row.source_id for row in self.evidence}
        required = {self.henry_provider_id, self.gas_capacity_provider_id, self.film_provider_id}
        if not required.issubset(evidence_ids):
            raise ValueError("Evidence must identify Henry, gas capacity and film coefficient sources")
        return self


class WetCo2FiniteGasLiquidHistoryRequest(Contract):
    """Finite gas reservoir exchanging CO2 with a fixed-volume, well-mixed liquid."""

    schema_version: Literal["matintegrity.wet_co2_finite_gas_liquid_exchange_history.v1"] = (
        "matintegrity.wet_co2_finite_gas_liquid_exchange_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    interfacial_area_m2: float = Field(gt=0)
    fixed_liquid_volume_m3: float = Field(gt=0)
    initial_liquid_co2star_mol_m3: float = Field(ge=0)
    initial_gas_co2_fugacity_Pa: float = Field(ge=0)
    intervals: tuple[WetCo2FiniteGasLiquidInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    fixed_geometry_reviewed: bool
    closed_gas_inventory_reviewed: bool
    well_mixed_single_phase_reviewed: bool
    no_reaction_or_other_co2_source_sink_reviewed: bool
    henry_and_gas_capacity_conventions_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def validate_history(self):
        if not all(math.isfinite(value) for value in (
            self.interfacial_area_m2, self.fixed_liquid_volume_m3,
            self.initial_liquid_co2star_mol_m3, self.initial_gas_co2_fugacity_Pa,
        )):
            raise ValueError("geometry and initial states must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous")
        if any(
            row.gas_inventory_capacity_mol_Pa != self.intervals[0].gas_inventory_capacity_mol_Pa
            for row in self.intervals[1:]
        ):
            raise ValueError("closed-reservoir gas inventory capacity must remain fixed across intervals")
        return self


def _overall_liquid_coefficient(gas_k: float, henry_h: float, liquid_k: float) -> float | None:
    """Stable series resistance combination on a liquid concentration basis."""
    log_gas_h = math.log(gas_k) + math.log(henry_h)
    log_ratio = math.log(liquid_k) - log_gas_h
    if log_ratio >= 0.0:
        log_value = log_gas_h - math.log1p(math.exp(-log_ratio))
    else:
        log_value = math.log(liquid_k) - math.log1p(math.exp(log_ratio))
    if log_value > math.log(sys.float_info.max):
        return None
    value = math.exp(log_value)
    return value if math.isfinite(value) and value > 0.0 else None


def evaluate_wet_co2_finite_gas_liquid_exchange_history(
    request: WetCo2FiniteGasLiquidHistoryRequest,
) -> Calculation:
    """Integrate exact two-compartment exchange over piecewise-constant intervals."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "input_sha256": input_digest,
        "interfacial_area_m2": request.interfacial_area_m2,
        "fixed_liquid_volume_m3": request.fixed_liquid_volume_m3,
        "initial_liquid_co2star_mol_m3": request.initial_liquid_co2star_mol_m3,
        "initial_gas_co2_fugacity_Pa": request.initial_gas_co2_fugacity_Pa,
    }
    checks = (
        "fixed_geometry_reviewed", "closed_gas_inventory_reviewed",
        "well_mixed_single_phase_reviewed", "no_reaction_or_other_co2_source_sink_reviewed",
        "henry_and_gas_capacity_conventions_reviewed", "calculation_use_authorized",
    )
    missing = [name for name in checks if not getattr(request, name)]
    missing.extend(
        f"interval[{i}].parameters_and_state_reviewed"
        for i, interval in enumerate(request.intervals) if not interval.parameters_and_state_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    area, volume = request.interfacial_area_m2, request.fixed_liquid_volume_m3
    gas_fugacity = request.initial_gas_co2_fugacity_Pa
    liquid_c = request.initial_liquid_co2star_mol_m3
    initial_inventory = (
        volume * liquid_c
        + request.intervals[0].gas_inventory_capacity_mol_Pa * gas_fugacity
    )
    if not math.isfinite(initial_inventory):
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "initial combined gas-liquid inventory exceeds finite numeric support",
        })
    ledger: list[dict] = []
    history = [{
        "time_s": 0.0,
        "gas_co2_fugacity_Pa": gas_fugacity,
        "liquid_co2star_mol_m3": liquid_c,
        "combined_co2_inventory_mol": initial_inventory,
        "origin": "caller_initial_state",
    }]
    cumulative_gas_to_liquid = 0.0

    for i, interval in enumerate(request.intervals):
        duration = interval.end_time_s - interval.start_time_s
        henry = interval.henry_concentration_over_fugacity_mol_m3_Pa
        capacity = interval.gas_inventory_capacity_mol_Pa
        k_overall = _overall_liquid_coefficient(
            interval.gas_film_coefficient_mol_m2_s_Pa,
            henry,
            interval.liquid_film_coefficient_m_s,
        )
        if k_overall is None:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "overall transfer coefficient outside finite numeric support",
            })
        total_inventory = volume * liquid_c + capacity * gas_fugacity
        if not math.isfinite(total_inventory):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "initial combined compartment inventory exceeds numeric support",
            })
        equilibrium_denominator = capacity + volume * henry
        if not math.isfinite(equilibrium_denominator) or equilibrium_denominator <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "combined equilibrium capacity exceeds numeric support",
            })
        f_eq = total_inventory / equilibrium_denominator
        c_eq = henry * f_eq
        if not math.isfinite(f_eq) or not math.isfinite(c_eq):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "equilibrium state exceeds finite numeric support",
            })

        # Decay rate of the gas-liquid disequilibrium x = H*f - C.
        log_capacity_ratio = math.log(volume) + math.log(henry) - math.log(capacity)
        if log_capacity_ratio > 40.0:
            log_exchange_factor = log_capacity_ratio + math.log1p(math.exp(-log_capacity_ratio))
        else:
            log_exchange_factor = math.log1p(math.exp(log_capacity_ratio))
        log_rate = math.log(area) + math.log(k_overall) - math.log(volume) + log_exchange_factor
        log_exposure = log_rate + math.log(duration)
        if log_exposure > math.log(sys.float_info.max):
            decay = 0.0
        elif log_exposure < math.log(float.fromhex("0x0.0000000000001p-1022")):
            decay = 1.0
        else:
            decay = math.exp(-math.exp(log_exposure))

        disequilibrium = henry * gas_fugacity - liquid_c
        liquid_weight = capacity / equilibrium_denominator
        liquid_next = c_eq - liquid_weight * disequilibrium * decay
        gas_next = f_eq + (volume / capacity) * liquid_weight * disequilibrium * decay
        if not all(math.isfinite(value) and value >= 0.0 for value in (liquid_next, gas_next)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "closed-form exchange state outside finite nonnegative support",
            })
        delta_liquid_moles = volume * (liquid_next - liquid_c)
        gas_to_liquid = delta_liquid_moles
        cumulative_next = cumulative_gas_to_liquid + gas_to_liquid
        inventory_next = volume * liquid_next + capacity * gas_next
        residual = inventory_next - total_inventory
        if not all(math.isfinite(value) for value in (delta_liquid_moles, cumulative_next, inventory_next, residual)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "history": history,
                "interval_ledger": ledger, "failed_interval_index": i,
                "failure_reason": "inventory or transfer ledger outside finite numeric support",
            })
        ledger.append({
            "interval_index": i,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": duration,
            "temperature_K": interval.temperature_K,
            "initial_gas_co2_fugacity_Pa": gas_fugacity,
            "final_gas_co2_fugacity_Pa": gas_next,
            "initial_liquid_co2star_mol_m3": liquid_c,
            "final_liquid_co2star_mol_m3": liquid_next,
            "henry_concentration_over_fugacity_mol_m3_Pa": henry,
            "gas_inventory_capacity_mol_Pa": capacity,
            "overall_liquid_basis_coefficient_m_s": k_overall,
            "signed_gas_to_liquid_transfer_mol": gas_to_liquid,
            "combined_inventory_initial_mol": total_inventory,
            "combined_inventory_final_mol": inventory_next,
            "combined_inventory_balance_residual_mol": residual,
            "henry_provider_id": interval.henry_provider_id,
            "henry_provider_revision": interval.henry_provider_revision,
            "henry_configuration_sha256": interval.henry_configuration_sha256,
            "henry_result_sha256": interval.henry_result_sha256,
            "gas_capacity_provider_id": interval.gas_capacity_provider_id,
            "gas_capacity_provider_revision": interval.gas_capacity_provider_revision,
            "gas_capacity_configuration_sha256": interval.gas_capacity_configuration_sha256,
            "gas_capacity_result_sha256": interval.gas_capacity_result_sha256,
            "film_provider_id": interval.film_provider_id,
            "film_provider_revision": interval.film_provider_revision,
            "film_configuration_sha256": interval.film_configuration_sha256,
            "film_result_sha256": interval.film_result_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
        })
        cumulative_gas_to_liquid = cumulative_next
        gas_fugacity, liquid_c = gas_next, liquid_next
        history.append({
            "time_s": interval.end_time_s,
            "gas_co2_fugacity_Pa": gas_fugacity,
            "liquid_co2star_mol_m3": liquid_c,
            "combined_co2_inventory_mol": inventory_next,
            "cumulative_signed_gas_to_liquid_transfer_mol": cumulative_gas_to_liquid,
            "origin": "integrated_finite_reservoir_two_film_exchange",
        })

    return Calculation(values=base | {
        "status": "computed",
        "committed_interval_count": len(ledger),
        "history": history,
        "interval_ledger": ledger,
        "final_gas_co2_fugacity_Pa": gas_fugacity,
        "final_liquid_co2star_mol_m3": liquid_c,
        "cumulative_signed_gas_to_liquid_transfer_mol": cumulative_gas_to_liquid,
        "transfer_sign_convention": "positive means transfer from finite gas inventory to liquid",
        "model": "exact two-compartment first-order exchange for piecewise-constant transfer and capacity data",
        "interpretation_boundary": "Finite gas inventory and fixed-volume well-mixed neutral CO2star liquid only; carbonate chemistry, reactions and corrosion are excluded.",
        "not_inferred": [
            "gas inventory capacity from an equation of state",
            "pressure-volume-temperature changes, gas nonideality or gas composition changes",
            "carbonate speciation, alkalinity, pH, reaction, precipitation or wall consumption",
            "spatial gradients, variable interface area, outflow, corrosion loss or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2FiniteGasLiquidHistoryRequest,
        evaluator=evaluate_wet_co2_finite_gas_liquid_exchange_history,
        units={
            "interfacial_area_m2": "m2",
            "fixed_liquid_volume_m3": "m3",
            "initial_liquid_co2star_mol_m3": "mol/m3",
            "initial_gas_co2_fugacity_Pa": "Pa",
            "history[].time_s": "s",
            "history[].gas_co2_fugacity_Pa": "Pa",
            "history[].liquid_co2star_mol_m3": "mol/m3",
            "interval_ledger[].signed_gas_to_liquid_transfer_mol": "mol",
        },
        assumptions=(
            "Each interval has fixed area, liquid volume, Henry coefficient, gas inventory capacity and two-film transfer coefficients.",
            "Gas inventory is represented only by a caller-supplied local capacity in mol/Pa; no equation of state is included.",
            "Liquid is well mixed, single phase and non-flowing, with no reaction or other CO2 sources or sinks.",
            "Henry relation and film resistance combination are applicable to the caller's state and conditions.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
