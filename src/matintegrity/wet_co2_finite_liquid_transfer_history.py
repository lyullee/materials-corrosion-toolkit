"""Exact finite-volume CO2-star history under a prescribed two-film gas reservoir."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_liquid_transfer_history"
SOURCE_ID = "caller_finite_liquid_two_film_co2star_mass_balance"
MAX_INTERVALS = 5000


class WetCo2FiniteLiquidTransferInterval(Contract):
    """Piecewise-constant gas/liquid state and two-film coefficients over one interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    temperature_K: float = Field(gt=0)
    co2_fugacity_Pa: float = Field(ge=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_film_coefficient_m_s: float = Field(gt=0)
    fugacity_provider_id: str = Field(min_length=1)
    fugacity_provider_revision: str = Field(min_length=1)
    fugacity_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fugacity_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    henry_source_id: str = Field(min_length=1)
    henry_record_id: str = Field(min_length=1)
    henry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    film_coefficient_source_id: str = Field(min_length=1)
    film_coefficient_provider_revision: str = Field(min_length=1)
    film_coefficient_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    film_coefficient_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    state_and_parameter_support_reviewed: bool

    @model_validator(mode="after")
    def validate_interval_and_evidence(self):
        numeric = (
            self.start_time_s,
            self.end_time_s,
            self.temperature_K,
            self.co2_fugacity_Pa,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa,
            self.liquid_film_coefficient_m_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all interval inputs must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end time must be after its start time")
        evidence_ids = {row.source_id for row in self.evidence}
        required = {self.fugacity_provider_id, self.henry_source_id, self.film_coefficient_source_id}
        if not required.issubset(evidence_ids):
            raise ValueError("interval Evidence must identify fugacity, Henry data and film coefficients")
        return self


class WetCo2FiniteLiquidTransferHistoryRequest(Contract):
    """A fixed-volume, well-mixed liquid receiving CO2 from a prescribed gas reservoir."""

    schema_version: Literal["matintegrity.wet_co2_finite_liquid_transfer_history.v1"] = (
        "matintegrity.wet_co2_finite_liquid_transfer_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    interfacial_area_m2: float = Field(gt=0)
    fixed_liquid_volume_m3: float = Field(gt=0)
    initial_co2star_concentration_mol_m3: float = Field(ge=0)
    intervals: tuple[WetCo2FiniteLiquidTransferInterval, ...] = Field(
        min_length=1, max_length=MAX_INTERVALS
    )
    fixed_area_and_liquid_volume_reviewed: bool
    fixed_fugacity_reservoir_over_each_interval_reviewed: bool
    well_mixed_single_liquid_phase_reviewed: bool
    no_liquid_flow_or_other_co2star_source_sink_reviewed: bool
    co2star_definition_and_henry_convention_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def exact_interval_chain(self):
        if not all(math.isfinite(value) for value in (
            self.interfacial_area_m2,
            self.fixed_liquid_volume_m3,
            self.initial_co2star_concentration_mol_m3,
        )):
            raise ValueError("area, volume and initial concentration must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at time zero")
        for left, right in zip(self.intervals[:-1], self.intervals[1:]):
            if left.end_time_s != right.start_time_s:
                raise ValueError("transfer intervals must be exactly contiguous")
        return self


def _exp_from_log(value: float) -> float | None:
    if not math.isfinite(value) or value > math.log(sys.float_info.max):
        return None
    if value < math.log(float.fromhex("0x0.0000000000001p-1022")):
        return 0.0
    result = math.exp(value)
    return result if math.isfinite(result) else None


def _overall_liquid_coefficient(
    gas_coefficient: float,
    henry_coefficient: float,
    liquid_coefficient: float,
) -> float | None:
    """Combine gas- and liquid-side resistances on a liquid-concentration basis."""
    log_gas_henry = math.log(gas_coefficient) + math.log(henry_coefficient)
    log_resistance_ratio = math.log(liquid_coefficient) - log_gas_henry
    if log_resistance_ratio > 40.0:
        log_overall = log_gas_henry - math.log1p(math.exp(-log_resistance_ratio))
    elif log_resistance_ratio < -40.0:
        log_overall = math.log(liquid_coefficient) - math.log1p(math.exp(log_resistance_ratio))
    else:
        log_overall = math.log(liquid_coefficient) - math.log1p(math.exp(log_resistance_ratio))
    result = _exp_from_log(log_overall)
    return result if result is not None and result > 0.0 else None


def evaluate_wet_co2_finite_liquid_transfer_history(
    request: WetCo2FiniteLiquidTransferHistoryRequest,
) -> Calculation:
    """Solve each constant-parameter interval exactly for the well-mixed CO2-star state."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "input_sha256": request_digest,
        "interfacial_area_m2": request.interfacial_area_m2,
        "fixed_liquid_volume_m3": request.fixed_liquid_volume_m3,
        "initial_co2star_concentration_mol_m3": request.initial_co2star_concentration_mol_m3,
        "state_quantity": "neutral_dissolved_CO2star_only",
        "gas_reservoir_depletion_included": False,
        "carbonate_chemistry_or_corrosion_inferred": False,
    }
    required_reviews = (
        "fixed_area_and_liquid_volume_reviewed",
        "fixed_fugacity_reservoir_over_each_interval_reviewed",
        "well_mixed_single_liquid_phase_reviewed",
        "no_liquid_flow_or_other_co2star_source_sink_reviewed",
        "co2star_definition_and_henry_convention_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in required_reviews if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].state_and_parameter_support_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.state_and_parameter_support_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "committed_interval_count": 0,
            "concentration_history": [],
            "interval_transfer_ledger": [],
        })

    concentration = request.initial_co2star_concentration_mol_m3
    cumulative_moles = 0.0
    volume = request.fixed_liquid_volume_m3
    area = request.interfacial_area_m2
    history = [{
        "time_s": 0.0,
        "co2star_concentration_mol_m3": concentration,
        "cumulative_signed_gas_to_liquid_transfer_mol": 0.0,
        "origin": "caller_initial_liquid_inventory",
    }]
    ledger: list[dict] = []

    for index, interval in enumerate(request.intervals):
        duration = interval.end_time_s - interval.start_time_s
        equilibrium_concentration = (
            interval.henry_concentration_over_fugacity_mol_m3_Pa * interval.co2_fugacity_Pa
        )
        if not math.isfinite(equilibrium_concentration):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "concentration_history": history,
                "interval_transfer_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "Henry-equilibrium CO2star concentration exceeds finite numeric support",
            })
        overall_k = _overall_liquid_coefficient(
            interval.gas_film_coefficient_mol_m2_s_Pa,
            interval.henry_concentration_over_fugacity_mol_m3_Pa,
            interval.liquid_film_coefficient_m_s,
        )
        if overall_k is None:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "concentration_history": history,
                "interval_transfer_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "overall two-film coefficient exceeds finite numeric support",
            })

        log_lambda = math.log(overall_k) + math.log(area) - math.log(volume)
        log_exposure = log_lambda + math.log(duration)
        if log_exposure > math.log(sys.float_info.max):
            approach_fraction = 1.0
        elif log_exposure < math.log(float.fromhex("0x0.0000000000001p-1022")):
            approach_fraction = 0.0
        else:
            exposure = math.exp(log_exposure)
            approach_fraction = -math.expm1(-exposure)

        concentration_difference = equilibrium_concentration - concentration
        next_concentration = concentration + concentration_difference * approach_fraction
        if (
            not math.isfinite(concentration_difference)
            or not math.isfinite(next_concentration)
            or next_concentration < 0.0
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "concentration_history": history,
                "interval_transfer_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "closed-form CO2star concentration exceeds nonnegative finite support",
            })
        concentration_change = next_concentration - concentration
        signed_transfer_moles = volume * concentration_change
        cumulative_candidate = cumulative_moles + signed_transfer_moles
        if not all(math.isfinite(value) for value in (signed_transfer_moles, cumulative_candidate)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "concentration_history": history,
                "interval_transfer_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "integrated gas-liquid transfer exceeds finite mole inventory support",
            })

        if signed_transfer_moles == 0.0:
            average_flux = 0.0
        else:
            average_flux_magnitude = _exp_from_log(
                math.log(abs(signed_transfer_moles)) - math.log(area) - math.log(duration)
            )
            average_flux = (
                None if average_flux_magnitude is None
                else math.copysign(average_flux_magnitude, signed_transfer_moles)
            )
        if average_flux is None or not math.isfinite(average_flux):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "concentration_history": history,
                "interval_transfer_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "interval-average transfer flux exceeds finite numeric support",
            })

        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": duration,
            "temperature_K": interval.temperature_K,
            "co2_fugacity_Pa": interval.co2_fugacity_Pa,
            "henry_concentration_over_fugacity_mol_m3_Pa": interval.henry_concentration_over_fugacity_mol_m3_Pa,
            "gas_film_coefficient_mol_m2_s_Pa": interval.gas_film_coefficient_mol_m2_s_Pa,
            "liquid_film_coefficient_m_s": interval.liquid_film_coefficient_m_s,
            "overall_liquid_basis_coefficient_m_s": overall_k,
            "equilibrium_co2star_concentration_mol_m3": equilibrium_concentration,
            "initial_co2star_concentration_mol_m3": concentration,
            "final_co2star_concentration_mol_m3": next_concentration,
            "signed_gas_to_liquid_transfer_mol": signed_transfer_moles,
            "interval_average_gas_to_liquid_flux_mol_m2_s": average_flux,
            "mass_balance_residual_mol": signed_transfer_moles - volume * concentration_change,
            "fugacity_provider_id": interval.fugacity_provider_id,
            "fugacity_provider_revision": interval.fugacity_provider_revision,
            "fugacity_configuration_sha256": interval.fugacity_configuration_sha256,
            "fugacity_result_sha256": interval.fugacity_result_sha256,
            "henry_source_id": interval.henry_source_id,
            "henry_record_id": interval.henry_record_id,
            "henry_record_sha256": interval.henry_record_sha256,
            "film_coefficient_source_id": interval.film_coefficient_source_id,
            "film_coefficient_provider_revision": interval.film_coefficient_provider_revision,
            "film_coefficient_configuration_sha256": interval.film_coefficient_configuration_sha256,
            "film_coefficient_result_sha256": interval.film_coefficient_result_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
        })
        cumulative_moles = cumulative_candidate
        concentration = next_concentration
        history.append({
            "time_s": interval.end_time_s,
            "co2star_concentration_mol_m3": concentration,
            "cumulative_signed_gas_to_liquid_transfer_mol": cumulative_moles,
            "origin": "integrated_two_film_transfer",
        })

    return Calculation(values=base | {
        "status": "computed",
        "committed_interval_count": len(ledger),
        "concentration_history": history,
        "interval_transfer_ledger": ledger,
        "final_co2star_concentration_mol_m3": concentration,
        "cumulative_signed_gas_to_liquid_transfer_mol": cumulative_moles,
        "transfer_sign_convention": "positive means net transfer from gas reservoir into liquid",
        "interval_model": "constant Henry equilibrium state and two-film coefficients; exact first-order liquid inventory update",
        "interpretation_boundary": "The liquid is a well-mixed fixed-volume compartment exchanging CO2star with a prescribed non-depleting gas reservoir. This provides a dissolved neutral CO2star history only; it is not total inorganic carbon, carbonate equilibrium, pH, reaction kinetics or corrosion loss.",
        "not_inferred": [
            "gas-reservoir depletion or pressure/composition feedback",
            "aqueous carbonate speciation, alkalinity, pH or ionic activity",
            "liquid outflow, reaction, scale precipitation or wall consumption",
            "spatial liquid gradients, changing interfacial area or changing volume",
            "corrosion rate, metal loss, wall thickness, acceptance or risk probability",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2FiniteLiquidTransferHistoryRequest,
        evaluator=evaluate_wet_co2_finite_liquid_transfer_history,
        units={
            "interfacial_area_m2": "m2",
            "fixed_liquid_volume_m3": "m3",
            "initial_co2star_concentration_mol_m3": "mol/m3",
            "concentration_history[].time_s": "s",
            "concentration_history[].co2star_concentration_mol_m3": "mol/m3",
            "concentration_history[].cumulative_signed_gas_to_liquid_transfer_mol": "mol",
            "interval_transfer_ledger[].overall_liquid_basis_coefficient_m_s": "m/s",
            "interval_transfer_ledger[].signed_gas_to_liquid_transfer_mol": "mol",
            "interval_transfer_ledger[].interval_average_gas_to_liquid_flux_mol_m2_s": "mol/(m2 s)",
        },
        assumptions=(
            "Gas fugacity, Henry convention, interface area, liquid volume and two-film coefficients are constant within each exact interval and may change only at supplied interval boundaries.",
            "The liquid is well mixed, single phase, non-flowing and fixed in volume; the gas is an effectively infinite reservoir whose prescribed fugacity does not respond to transferred moles.",
            "The overall coefficient is the series combination of the gas and liquid film resistances on a liquid-concentration basis.",
            "The exact state update integrates only neutral dissolved CO2star; carbonate species, alkalinity, reactions, precipitation and wall consumption are excluded.",
            "All external states, properties and calculation uses are caller attributed and reviewed; no physical qualification is implied.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
