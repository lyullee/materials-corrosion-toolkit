"""Couple CO2star transfer to a caller-driven variable liquid-film inventory."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_variable_condensate_transfer_history"
SOURCE_ID = "caller_variable_condensate_two_film_mass_balance"
MAX_INTERVALS = 10000


class WetCo2VariableCondensateInterval(Contract):
    """Constant state and signed liquid-volume flux over one time interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    temperature_K: float = Field(gt=0)
    liquid_volume_flux_m_s: float
    incoming_co2star_mol_m3: float = Field(ge=0)
    gas_co2_fugacity_Pa: float = Field(ge=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_film_coefficient_m_s: float = Field(gt=0)
    state_provider_id: str = Field(min_length=1)
    state_provider_revision: str = Field(min_length=1)
    state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    interval_state_and_flux_reviewed: bool

    @model_validator(mode="after")
    def finite_and_evidenced(self):
        values = (
            self.start_time_s, self.end_time_s, self.temperature_K,
            self.liquid_volume_flux_m_s, self.incoming_co2star_mol_m3,
            self.gas_co2_fugacity_Pa,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa, self.liquid_film_coefficient_m_s,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("all interval state and coefficient values must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must follow interval start")
        if self.state_provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("interval Evidence must identify its state/flux provider")
        return self


class WetCo2VariableCondensateHistoryRequest(Contract):
    """Variable liquid volume per fixed wall patch with two-film CO2 transfer."""

    schema_version: Literal["matintegrity.wet_co2_variable_condensate_transfer_history.v1"] = (
        "matintegrity.wet_co2_variable_condensate_transfer_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_liquid_volume_per_area_m: float = Field(gt=0)
    initial_co2star_concentration_mol_m3: float = Field(ge=0)
    intervals: tuple[WetCo2VariableCondensateInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    wall_patch_and_interfacial_area_basis_reviewed: bool
    positive_volume_flux_is_condensate_source_reviewed: bool
    negative_volume_flux_is_well_mixed_liquid_outflow_reviewed: bool
    incoming_co2star_state_reviewed: bool
    no_reaction_or_speciation_change_reviewed: bool
    use_authorized: bool

    @model_validator(mode="after")
    def contiguous_positive_volume(self):
        if not all(math.isfinite(value) for value in (
            self.initial_liquid_volume_per_area_m,
            self.initial_co2star_concentration_mol_m3,
        )):
            raise ValueError("initial liquid volume and CO2star state must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("history intervals must be exactly contiguous")
        volume = self.initial_liquid_volume_per_area_m
        for index, interval in enumerate(self.intervals):
            final = volume + interval.liquid_volume_flux_m_s * (interval.end_time_s - interval.start_time_s)
            if not math.isfinite(final) or final < 0.0:
                raise ValueError("liquid volume per area cannot become negative; partition history at dryout")
            if final == 0.0 and index != len(self.intervals) - 1:
                raise ValueError("dryout is supported only at the end of the final interval")
            volume = final
        return self


def _overall_liquid_transfer_velocity(gas_k: float, henry: float, liquid_k: float) -> float | None:
    log_gh = math.log(gas_k) + math.log(henry)
    log_ratio = math.log(liquid_k) - log_gh
    if log_ratio >= 0:
        log_k = log_gh - math.log1p(math.exp(-log_ratio))
    else:
        log_k = math.log(liquid_k) - math.log1p(math.exp(log_ratio))
    if log_k > math.log(sys.float_info.max):
        return None
    value = math.exp(log_k)
    return value if math.isfinite(value) and value > 0.0 else None


def _power_from_log(log_power: float) -> float | None:
    if not math.isfinite(log_power):
        return 0.0 if log_power < 0 else None
    if log_power > math.log(sys.float_info.max):
        return None
    if log_power < math.log(float.fromhex("0x0.0000000000001p-1022")):
        return 0.0
    return math.exp(log_power)


def evaluate_wet_co2_variable_condensate_transfer_history(
    request: WetCo2VariableCondensateHistoryRequest,
) -> Calculation:
    """Solve exact interval CO2star inventory with constant signed liquid-volume flux."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha,
        "initial_liquid_volume_per_area_m": request.initial_liquid_volume_per_area_m,
        "initial_co2star_concentration_mol_m3": request.initial_co2star_concentration_mol_m3,
    }
    reviews = (
        "wall_patch_and_interfacial_area_basis_reviewed",
        "positive_volume_flux_is_condensate_source_reviewed",
        "negative_volume_flux_is_well_mixed_liquid_outflow_reviewed",
        "incoming_co2star_state_reviewed",
        "no_reaction_or_speciation_change_reviewed",
        "use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].interval_state_and_flux_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_state_and_flux_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "state_history": [],
            "interval_ledger": [],
        })

    volume = request.initial_liquid_volume_per_area_m
    concentration = request.initial_co2star_concentration_mol_m3
    initial_inventory = volume * concentration
    if not math.isfinite(initial_inventory):
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "initial CO2star areal inventory exceeds finite numeric support",
        })
    history = [{
        "time_s": 0.0,
        "liquid_volume_per_area_m": volume,
        "co2star_concentration_mol_m3": concentration,
        "co2star_areal_inventory_mol_m2": initial_inventory,
        "origin": "caller_initial_state",
    }]
    ledger: list[dict] = []
    total_gas_to_liquid_transfer = 0.0

    for index, interval in enumerate(request.intervals):
        dt = interval.end_time_s - interval.start_time_s
        q = interval.liquid_volume_flux_m_s
        volume_start = volume
        volume_end = volume_start + q * dt
        henry = interval.henry_concentration_over_fugacity_mol_m3_Pa
        equilibrium_c = henry * interval.gas_co2_fugacity_Pa
        overall_k = _overall_liquid_transfer_velocity(
            interval.gas_film_coefficient_mol_m2_s_Pa, henry,
            interval.liquid_film_coefficient_m_s,
        )
        if overall_k is None or not math.isfinite(equilibrium_c):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "equilibrium concentration or overall transfer velocity outside finite support",
            })

        concentration_start = concentration
        if q == 0.0:
            exponent = -overall_k * dt / volume_start
            decay = math.exp(exponent) if exponent > math.log(float.fromhex("0x0.0000000000001p-1022")) else 0.0
            concentration_end = equilibrium_c + (concentration_start - equilibrium_c) * decay
            incoming_inventory = 0.0
            outflow_inventory = 0.0
        elif q > 0.0:
            steady_c = (
                overall_k * equilibrium_c + q * interval.incoming_co2star_mol_m3
            ) / (overall_k + q)
            relative_volume_increase = q * dt / volume_start
            if math.isfinite(relative_volume_increase) and relative_volume_increase < 0.5:
                log_volume_growth = math.log1p(relative_volume_increase)
            else:
                log_volume_growth = math.log(volume_end) - math.log(volume_start)
            if overall_k == 0.0:
                kinetic_exponent_term = 0.0
            elif log_volume_growth == 0.0:
                kinetic_exponent_term = overall_k * dt / volume_start
            else:
                log_kinetic_term = math.log(overall_k) - math.log(q) + math.log(log_volume_growth)
                kinetic_exponent_term = _power_from_log(log_kinetic_term)
                if kinetic_exponent_term is None:
                    kinetic_exponent_term = math.inf
            log_factor = -log_volume_growth - kinetic_exponent_term
            factor = _power_from_log(log_factor)
            if factor is None:
                return Calculation(status="out_of_scope", values=base | {
                    "committed_interval_count": len(ledger), "state_history": history,
                    "interval_ledger": ledger, "failed_interval_index": index,
                    "failure_reason": "positive-volume interval power law exceeds finite support",
                })
            concentration_end = steady_c + (concentration_start - steady_c) * factor
            incoming_inventory = q * interval.incoming_co2star_mol_m3 * dt
            outflow_inventory = 0.0
        else:
            if volume_end == 0.0:
                if overall_k > 0.0:
                    concentration_end = equilibrium_c
                else:
                    concentration_end = concentration_start
                outflow_average = (
                    equilibrium_c * dt
                    + (concentration_start - equilibrium_c)
                    * dt
                    / (1.0 - overall_k / q)
                ) if overall_k > 0.0 else concentration_start * dt
            else:
                rate_ratio = -overall_k / q
                log_factor = rate_ratio * (math.log(volume_end) - math.log(volume_start))
                factor = _power_from_log(log_factor)
                if factor is None:
                    return Calculation(status="out_of_scope", values=base | {
                        "committed_interval_count": len(ledger), "state_history": history,
                        "interval_ledger": ledger, "failed_interval_index": index,
                        "failure_reason": "negative-volume interval power law exceeds finite support",
                    })
                concentration_end = equilibrium_c + (concentration_start - equilibrium_c) * factor
                order = rate_ratio + 1.0
                if order == 0.0:
                    outflow_average = concentration_start * dt
                else:
                    log_ratio_power = order * (math.log(volume_end) - math.log(volume_start))
                    ratio_power = _power_from_log(log_ratio_power)
                    if ratio_power is None:
                        return Calculation(status="out_of_scope", values=base | {
                            "committed_interval_count": len(ledger), "state_history": history,
                            "interval_ledger": ledger, "failed_interval_index": index,
                            "failure_reason": "liquid outflow concentration integral exceeds finite support",
                        })
                    integral_factor = (volume_start / q) * (ratio_power - 1.0) / order
                    outflow_average = (
                        equilibrium_c * dt
                        + (concentration_start - equilibrium_c) * integral_factor
                    )
            incoming_inventory = 0.0
            outflow_inventory = q * outflow_average

        inventory_start = volume_start * concentration_start
        inventory_end = volume_end * concentration_end
        gas_to_liquid_transfer = inventory_end - inventory_start - incoming_inventory - outflow_inventory
        if not all(math.isfinite(value) and value >= 0.0 for value in (volume_end, concentration_end, inventory_end)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "liquid film state outside finite nonnegative support",
            })
        if not all(math.isfinite(value) for value in (
            incoming_inventory, outflow_inventory, gas_to_liquid_transfer,
            total_gas_to_liquid_transfer + gas_to_liquid_transfer,
        )):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "CO2star inventory or transfer ledger outside finite support",
            })

        residual = inventory_end - inventory_start - incoming_inventory - outflow_inventory - gas_to_liquid_transfer
        if not math.isfinite(residual) or incoming_inventory < 0.0 or outflow_inventory > 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "incoming/outgoing CO2star flux signs or mass-balance residual are invalid",
            })
        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": dt,
            "liquid_volume_flux_m_s": q,
            "liquid_volume_per_area_start_m": volume_start,
            "liquid_volume_per_area_end_m": volume_end,
            "incoming_co2star_mol_m3": interval.incoming_co2star_mol_m3,
            "gas_co2_fugacity_Pa": interval.gas_co2_fugacity_Pa,
            "equilibrium_co2star_concentration_mol_m3": equilibrium_c,
            "overall_liquid_basis_transfer_velocity_m_s": overall_k,
            "co2star_concentration_start_mol_m3": concentration_start,
            "co2star_concentration_end_mol_m3": concentration_end,
            "co2star_inventory_start_mol_m2": inventory_start,
            "co2star_inventory_end_mol_m2": inventory_end,
            "incoming_co2star_inventory_mol_m2": incoming_inventory,
            "outgoing_well_mixed_co2star_inventory_mol_m2": outflow_inventory,
            "signed_gas_to_liquid_co2star_transfer_mol_m2": gas_to_liquid_transfer,
            "inventory_balance_residual_mol_m2": residual,
            "state_provider_id": interval.state_provider_id,
            "state_provider_revision": interval.state_provider_revision,
            "state_configuration_sha256": interval.state_configuration_sha256,
            "state_result_sha256": interval.state_result_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in interval.evidence],
        })
        total_gas_to_liquid_transfer += gas_to_liquid_transfer
        volume, concentration = volume_end, concentration_end
        history.append({
            "time_s": interval.end_time_s,
            "liquid_volume_per_area_m": volume,
            "co2star_concentration_mol_m3": concentration,
            "co2star_areal_inventory_mol_m2": inventory_end,
            "cumulative_signed_gas_to_liquid_transfer_mol_m2": total_gas_to_liquid_transfer,
            "origin": "integrated_variable_volume_two_film_exchange",
        })

    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "state_history": history,
        "interval_ledger": ledger,
        "final_liquid_volume_per_area_m": volume,
        "final_co2star_concentration_mol_m3": concentration,
        "cumulative_signed_gas_to_liquid_transfer_mol_m2": total_gas_to_liquid_transfer,
        "transfer_sign_convention": "positive means transfer from gas into the liquid film",
        "model": "exact piecewise-constant two-film exchange with constant signed liquid-volume flux and CO2star incoming/outflow mass balance",
        "interpretation_boundary": "One uniformly mixed thin-liquid inventory per fixed interface area. No gas inventory feedback, carbonate chemistry or reactions.",
        "not_inferred": [
            "water condensation or liquid outflow flux from thermodynamics/hydrodynamics",
            "CO2star concentration of incoming condensate, which remains caller supplied",
            "gas reservoir depletion, lateral transport, film coverage or spatial gradients",
            "carbonate speciation, pH, reaction, scale, corrosion, metal loss or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2VariableCondensateHistoryRequest,
        evaluator=evaluate_wet_co2_variable_condensate_transfer_history,
        units={
            "initial_liquid_volume_per_area_m": "m3/m2",
            "initial_co2star_concentration_mol_m3": "mol/m3",
            "state_history[].time_s": "s",
            "state_history[].liquid_volume_per_area_m": "m3/m2",
            "state_history[].co2star_concentration_mol_m3": "mol/m3",
            "state_history[].co2star_areal_inventory_mol_m2": "mol/m2",
            "cumulative_signed_gas_to_liquid_transfer_mol_m2": "mol/m2",
        },
        assumptions=(
            "Liquid volume per area changes linearly at caller-provided constant interval flux; volume flux cannot drive negative inventory.",
            "Positive liquid-volume flux is condensate input with caller-provided CO2star concentration; negative flux removes well-mixed liquid.",
            "Henry coefficient, gas fugacity and film coefficients are fixed within each interval.",
            "The liquid film is well mixed with no reaction, carbonate conversion, lateral exchange or gas-reservoir depletion.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
