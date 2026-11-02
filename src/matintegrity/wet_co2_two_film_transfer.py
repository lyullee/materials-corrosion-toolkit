"""Two-film CO2 gas/liquid transfer using a caller-declared Henry convention."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.wet_co2_two_film_transfer"
SOURCE_ID = "caller_wet_co2_two_film_transfer_inputs"


class WetCo2TwoFilmTransferRequest(Contract):
    """One steady gas/liquid contact state with caller-supplied film coefficients."""

    schema_version: Literal["matintegrity.wet_co2_two_film_transfer.v1"] = (
        "matintegrity.wet_co2_two_film_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_s: Nonnegative
    temperature_K: Positive
    co2_fugacity_Pa: Nonnegative
    bulk_co2star_mol_m3: Nonnegative
    henry_concentration_over_fugacity_mol_m3_Pa: Positive
    gas_film_coefficient_mol_m2_s_Pa: Positive
    liquid_film_coefficient_m_s: Positive
    henry_record_id: str = Field(min_length=1)
    solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fugacity_provider_id: str = Field(min_length=1)
    fugacity_provider_revision: str = Field(min_length=1)
    gas_liquid_single_phase_and_area_basis_reviewed: bool
    fugacity_henry_convention_and_units_reviewed: bool
    solvent_temperature_and_condition_match_reviewed: bool
    stationary_film_coefficient_applicability_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


def evaluate_wet_co2_two_film_transfer(request: WetCo2TwoFilmTransferRequest) -> Calculation:
    """Compute signed steady CO2 transfer between two well-mixed film states.

    Gas-film flux is linear in fugacity difference. Liquid-film flux is linear
    in dissolved neutral CO2* concentration difference, with the declared
    Henry relation ``C*_interface = H*f_interface`` at the interface. This
    routine solves the two resistance balances algebraically and preserves a
    negative sign when the net direction is liquid-to-gas.
    """
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "time_s": request.time_s,
        "temperature_K": request.temperature_K,
        "co2_fugacity_Pa": request.co2_fugacity_Pa,
        "bulk_co2star_mol_m3": request.bulk_co2star_mol_m3,
        "henry_concentration_over_fugacity_mol_m3_Pa": request.henry_concentration_over_fugacity_mol_m3_Pa,
        "gas_film_coefficient_mol_m2_s_Pa": request.gas_film_coefficient_mol_m2_s_Pa,
        "liquid_film_coefficient_m_s": request.liquid_film_coefficient_m_s,
        "input_sha256": input_sha256,
        "fugacity_provider_id": request.fugacity_provider_id,
        "fugacity_provider_revision": request.fugacity_provider_revision,
        "henry_record_id": request.henry_record_id,
        "solvent_composition_sha256": request.solvent_composition_sha256,
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "source_ids": sorted({row.source_id for row in request.evidence}),
        "henry_convention": "aqueous_CO2star_concentration_over_gas_fugacity",
        "reviewed_assumptions": {
            "gas_liquid_single_phase_and_area_basis": request.gas_liquid_single_phase_and_area_basis_reviewed,
            "fugacity_henry_convention_and_units": request.fugacity_henry_convention_and_units_reviewed,
            "solvent_temperature_and_condition_match": request.solvent_temperature_and_condition_match_reviewed,
            "stationary_film_coefficient_applicability": request.stationary_film_coefficient_applicability_reviewed,
        },
    }
    missing = [name for name, reviewed in (
        ("gas_liquid_single_phase_and_area_basis_reviewed", request.gas_liquid_single_phase_and_area_basis_reviewed),
        ("fugacity_henry_convention_and_units_reviewed", request.fugacity_henry_convention_and_units_reviewed),
        ("solvent_temperature_and_condition_match_reviewed", request.solvent_temperature_and_condition_match_reviewed),
        ("stationary_film_coefficient_applicability_reviewed", request.stationary_film_coefficient_applicability_reviewed),
    ) if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    h = request.henry_concentration_over_fugacity_mol_m3_Pa
    kg = request.gas_film_coefficient_mol_m2_s_Pa
    kl = request.liquid_film_coefficient_m_s
    f_bulk = request.co2_fugacity_Pa
    c_bulk = request.bulk_co2star_mol_m3
    c_equilibrium = h * f_bulk
    if not math.isfinite(c_equilibrium) or (h > 0.0 and f_bulk > 0.0 and c_equilibrium == 0.0):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "bulk_Henry_equilibrium_concentration_exceeds_float_support",
        })

    # Refer the gas/liquid pair of resistances to liquid concentration. This
    # logarithmic harmonic combination avoids forming k_g*H or k_l/(k_g*H)
    # directly when their magnitudes differ substantially.
    log_ratio = math.log(kl) - math.log(kg) - math.log(h)
    if log_ratio > 40.0:
        log_overall_liquid_velocity = math.log(kg) + math.log(h) - math.log1p(math.exp(-log_ratio))
    elif log_ratio < -40.0:
        log_overall_liquid_velocity = math.log(kl) - math.log1p(math.exp(log_ratio))
    else:
        log_overall_liquid_velocity = math.log(kl) - math.log1p(math.exp(log_ratio))
    if log_overall_liquid_velocity > math.log(sys.float_info.max):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "overall_liquid_basis_transfer_coefficient_exceeds_float_support",
        })
    if log_overall_liquid_velocity < math.log(float.fromhex("0x0.0000000000001p-1022")):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "overall_liquid_basis_transfer_coefficient_underflows_float_support",
        })
    overall_liquid_velocity = math.exp(log_overall_liquid_velocity)
    flux = overall_liquid_velocity * (c_equilibrium - c_bulk)
    if not math.isfinite(overall_liquid_velocity) or not math.isfinite(flux) or (
        c_equilibrium != c_bulk and flux == 0.0
    ):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "two_film_flux_exceeds_float_support",
        })

    # Compute the interfacial fugacity as a convex conductance-weighted value.
    # It must stay between the two phase-equilibrium endpoint fugacities.
    liquid_equivalent_fugacity = c_bulk / h
    if not math.isfinite(liquid_equivalent_fugacity) or (c_bulk > 0.0 and liquid_equivalent_fugacity == 0.0):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "bulk_liquid_equivalent_fugacity_exceeds_float_support",
        })
    log_gas_conductance = math.log(kg)
    log_liquid_conductance = math.log(kl) + math.log(h)
    reference = max(log_gas_conductance, log_liquid_conductance)
    gas_weight = math.exp(log_gas_conductance - reference)
    liquid_weight = math.exp(log_liquid_conductance - reference)
    weight_sum = gas_weight + liquid_weight
    interfacial_fugacity = (
        (gas_weight / weight_sum) * f_bulk
        + (liquid_weight / weight_sum) * liquid_equivalent_fugacity
    )
    interfacial_concentration = h * interfacial_fugacity
    gas_side_flux = kg * (f_bulk - interfacial_fugacity)
    liquid_side_flux = kl * (interfacial_concentration - c_bulk)
    residual = gas_side_flux - liquid_side_flux
    if not all(math.isfinite(value) for value in (
        interfacial_fugacity, interfacial_concentration, gas_side_flux, liquid_side_flux, residual
    )) or (interfacial_fugacity > 0.0 and h > 0.0 and interfacial_concentration == 0.0):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "interfacial_state_or_flux_exceeds_float_support",
        })

    scale = max(abs(flux), abs(gas_side_flux), abs(liquid_side_flux), sys.float_info.min)
    return Calculation(values=base | {
        "units": {
            "time": "s",
            "temperature": "K",
            "fugacity": "Pa",
            "bulk_and_interface_CO2star": "mol/m^3",
            "Henry_coefficient": "mol/(m^3 Pa)",
            "gas_film_coefficient": "mol/(m^2 s Pa)",
            "liquid_film_coefficient": "m/s",
            "signed_CO2_flux": "mol/(m^2 s)",
        },
        "bulk_equilibrium_CO2star_at_gas_fugacity_mol_m3": c_equilibrium,
        "liquid_basis_overall_transfer_velocity_m_s": overall_liquid_velocity,
        "interfacial_fugacity_Pa": interfacial_fugacity,
        "interfacial_CO2star_mol_m3": interfacial_concentration,
        "signed_gas_to_liquid_CO2_flux_mol_m2_s": flux,
        "gas_film_flux_mol_m2_s": gas_side_flux,
        "liquid_film_flux_mol_m2_s": liquid_side_flux,
        "film_flux_relative_balance_residual": residual / scale,
        "net_direction": "gas_to_liquid" if flux > 0.0 else "liquid_to_gas" if flux < 0.0 else "zero",
        "carbonate_speciation_solved": False,
        "time_integration_performed": False,
        "corrosion_rate_or_wall_loss_inferred": False,
        "qualification_claimed": False,
    }, notes=(
        "The two-film interface is an algebraic steady transfer balance using caller-supplied Henry and film coefficients.",
        "This does not solve bulk carbonate chemistry, gas/liquid dynamics, surface reaction, scale transport, corrosion rate or qualification.",
    ))


def _validate_context(request: WetCo2TwoFilmTransferRequest, context: RunContext) -> None:
    if (request.asset_id, request.location_id) != (context.asset_id, context.location_id):
        raise ValueError("two-film transfer RunContext must match the request asset and location")


def specifications() -> list[ModelSpec]:
    """Expose the typed transfer calculator for registry integration."""
    return [ModelSpec(
        MODEL_ID,
        WetCo2TwoFilmTransferRequest,
        evaluate_wet_co2_two_film_transfer,
        {
            "time_s": "s",
            "temperature_K": "K",
            "co2_fugacity_Pa": "Pa",
            "bulk_co2star_mol_m3": "mol/m3",
            "henry_concentration_over_fugacity_mol_m3_Pa": "mol/(m3 Pa)",
            "gas_film_coefficient_mol_m2_s_Pa": "mol/(m2 s Pa)",
            "liquid_film_coefficient_m_s": "m/s",
            "bulk_equilibrium_CO2star_at_gas_fugacity_mol_m3": "mol/m3",
            "liquid_basis_overall_transfer_velocity_m_s": "m/s",
            "interfacial_fugacity_Pa": "Pa",
            "interfacial_CO2star_mol_m3": "mol/m3",
            "signed_gas_to_liquid_CO2_flux_mol_m2_s": "mol/m2/s",
            "gas_film_flux_mol_m2_s": "mol/m2/s",
            "liquid_film_flux_mol_m2_s": "mol/m2/s",
            "film_flux_relative_balance_residual": "1",
        },
        (
            "Caller-supplied fugacity, Henry coefficient and gas/liquid film coefficients share one reviewed condition and area basis.",
            "The interface uses the aqueous CO2star-concentration-over-gas-fugacity Henry convention; no alternate convention is converted.",
            "This is a steady two-film boundary calculation; bulk carbonate speciation, transient accumulation and corrosion response are outside scope.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
