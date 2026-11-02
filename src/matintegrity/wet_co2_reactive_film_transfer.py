"""Two-film CO2 transfer with a caller-parameterized first-order liquid-film sink."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_reactive_film_transfer"
SOURCE_ID = "caller_pseudofirst_order_co2_film_kinetics"


class WetCo2ReactiveFilmTransferRequest(Contract):
    """Steady CO2 uptake across a gas film and reactive liquid film."""

    schema_version: Literal["matintegrity.wet_co2_reactive_film_transfer.v1"] = (
        "matintegrity.wet_co2_reactive_film_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    temperature_K: float = Field(gt=0)
    gas_co2_fugacity_Pa: float = Field(ge=0)
    bulk_co2star_concentration_mol_m3: float = Field(ge=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_physical_film_coefficient_m_s: float = Field(gt=0)
    co2star_diffusivity_m2_s: float = Field(gt=0)
    apparent_irreversible_first_order_sink_s: float = Field(ge=0)
    state_provider_id: str = Field(min_length=1)
    state_provider_revision: str = Field(min_length=1)
    state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetics_provider_id: str = Field(min_length=1)
    kinetics_provider_revision: str = Field(min_length=1)
    kinetics_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetics_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=64)
    state_units_and_alignment_reviewed: bool
    first_order_irreversible_sink_scope_reviewed: bool
    excess_reactant_and_constant_rate_reviewed: bool
    film_model_and_co2star_basis_reviewed: bool
    temperature_and_property_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def finite_and_evidenced(self):
        numeric = (
            self.time_s, self.temperature_K, self.gas_co2_fugacity_Pa,
            self.bulk_co2star_concentration_mol_m3,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa,
            self.liquid_physical_film_coefficient_m_s,
            self.co2star_diffusivity_m2_s,
            self.apparent_irreversible_first_order_sink_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all transfer and reaction inputs must be finite")
        evidence_ids = {row.source_id for row in self.evidence}
        if not {self.state_provider_id, self.kinetics_provider_id}.issubset(evidence_ids):
            raise ValueError("Evidence must identify state and kinetic providers")
        return self


def _film_factors(hatta: float) -> tuple[float, float]:
    """Return Ha*coth(Ha) and Ha*csch(Ha) with stable small/large limits."""
    if hatta == 0.0:
        return 1.0, 1.0
    if hatta < 1e-4:
        h2 = hatta * hatta
        h4 = h2 * h2
        return 1.0 + h2 / 3.0 - h4 / 45.0, 1.0 - h2 / 6.0 + 7.0 * h4 / 360.0
    if hatta > 40.0:
        return hatta, 0.0
    return hatta / math.tanh(hatta), hatta / math.sinh(hatta)


def evaluate_wet_co2_reactive_film_transfer(request: WetCo2ReactiveFilmTransferRequest) -> Calculation:
    """Solve steady film diffusion/reaction and gas-film resistance in series."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "time_s": request.time_s,
        "temperature_K": request.temperature_K,
        "input_sha256": input_sha,
        "state_provider_id": request.state_provider_id,
        "state_provider_revision": request.state_provider_revision,
        "state_configuration_sha256": request.state_configuration_sha256,
        "state_result_sha256": request.state_result_sha256,
        "kinetics_provider_id": request.kinetics_provider_id,
        "kinetics_provider_revision": request.kinetics_provider_revision,
        "kinetics_configuration_sha256": request.kinetics_configuration_sha256,
        "kinetics_result_sha256": request.kinetics_result_sha256,
    }
    reviews = (
        "state_units_and_alignment_reviewed", "first_order_irreversible_sink_scope_reviewed",
        "excess_reactant_and_constant_rate_reviewed", "film_model_and_co2star_basis_reviewed",
        "temperature_and_property_applicability_reviewed", "computational_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    k_l = request.liquid_physical_film_coefficient_m_s
    diffusivity = request.co2star_diffusivity_m2_s
    k_rxn = request.apparent_irreversible_first_order_sink_s
    if k_rxn == 0.0:
        hatta = 0.0
    else:
        log_hatta = 0.5 * (math.log(k_rxn) + math.log(diffusivity)) - math.log(k_l)
        if log_hatta > math.log(sys.float_info.max):
            return Calculation(status="out_of_scope", values=base | {
                "failure_reason": "Hatta number exceeds finite numeric support",
            })
        hatta = math.exp(log_hatta) if log_hatta > math.log(float.fromhex("0x0.0000000000001p-1022")) else 0.0
    factor_a, factor_b = _film_factors(hatta)
    liquid_a = k_l * factor_a
    liquid_b = k_l * factor_b
    henry = request.henry_concentration_over_fugacity_mol_m3_Pa
    gas_k = request.gas_film_coefficient_mol_m2_s_Pa
    denominator = gas_k + liquid_a * henry
    numerator = gas_k * request.gas_co2_fugacity_Pa + liquid_b * request.bulk_co2star_concentration_mol_m3
    if (
        not all(math.isfinite(value) for value in (liquid_a, liquid_b, denominator, numerator))
        or denominator <= 0.0
    ):
        return Calculation(status="out_of_scope", values=base | {
            "hatta_number": hatta,
            "failure_reason": "interface-state algebra exceeds finite numeric support",
        })
    interface_fugacity = numerator / denominator
    interface_co2star = henry * interface_fugacity
    gas_uptake_flux = gas_k * (request.gas_co2_fugacity_Pa - interface_fugacity)
    liquid_bulk_flux = liquid_b * interface_co2star - liquid_a * request.bulk_co2star_concentration_mol_m3

    # Film-integrated sink follows the exact 1-D steady first-order profile.
    if hatta == 0.0 or k_rxn == 0.0:
        reaction_sink_flux = 0.0
    else:
        sink_factor = math.tanh(hatta / 2.0)
        reaction_sink_flux = k_l * hatta * sink_factor * (interface_co2star + request.bulk_co2star_concentration_mol_m3)
    values_to_check = (
        interface_fugacity, interface_co2star, gas_uptake_flux,
        liquid_bulk_flux, reaction_sink_flux,
    )
    if not all(math.isfinite(value) for value in values_to_check):
        return Calculation(status="out_of_scope", values=base | {
            "hatta_number": hatta,
            "failure_reason": "reactive film outputs exceed finite numeric support",
        })
    balance_residual = gas_uptake_flux - liquid_bulk_flux - reaction_sink_flux
    if not math.isfinite(balance_residual):
        return Calculation(status="out_of_scope", values=base | {
            "hatta_number": hatta,
            "failure_reason": "reactive-film material-balance residual exceeds finite numeric support",
        })
    return Calculation(values=base | {
        "status": "computed",
        "gas_co2_fugacity_Pa": request.gas_co2_fugacity_Pa,
        "bulk_co2star_concentration_mol_m3": request.bulk_co2star_concentration_mol_m3,
        "henry_concentration_over_fugacity_mol_m3_Pa": henry,
        "gas_film_coefficient_mol_m2_s_Pa": gas_k,
        "liquid_physical_film_coefficient_m_s": k_l,
        "co2star_diffusivity_m2_s": diffusivity,
        "apparent_irreversible_first_order_sink_s": k_rxn,
        "hatta_number": hatta,
        "interface_co2_fugacity_Pa": interface_fugacity,
        "interface_co2star_concentration_mol_m3": interface_co2star,
        "gas_to_liquid_co2_uptake_flux_mol_m2_s": gas_uptake_flux,
        "liquid_film_to_bulk_co2star_flux_mol_m2_s": liquid_bulk_flux,
        "liquid_film_reaction_sink_flux_mol_m2_s": reaction_sink_flux,
        "interfacial_flux_balance_residual_mol_m2_s": balance_residual,
        "model": "steady two-film resistance coupled to a one-dimensional stagnant liquid-film first-order irreversible sink",
        "interpretation_boundary": "Net gas uptake splits into neutral CO2star transport to bulk liquid and caller-declared reaction within the liquid film; it is not a corrosion rate or automatically a bulk CO2star source.",
        "not_inferred": [
            "reaction mechanism, kinetic constants or reaction products",
            "bulk chemistry evolution, carbonate speciation or pH",
            "liquid hydrodynamics, film thickness beyond D/kL, interfacial area or transient renewal",
            "electrode current, metal loss, corrosion rate, localized damage or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2ReactiveFilmTransferRequest,
        evaluator=evaluate_wet_co2_reactive_film_transfer,
        units={
            "time_s": "s", "temperature_K": "K", "hatta_number": "1",
            "gas_to_liquid_co2_uptake_flux_mol_m2_s": "mol/(m2 s)",
            "liquid_film_to_bulk_co2star_flux_mol_m2_s": "mol/(m2 s)",
            "liquid_film_reaction_sink_flux_mol_m2_s": "mol/(m2 s)",
            "interfacial_flux_balance_residual_mol_m2_s": "mol/(m2 s)",
        },
        assumptions=(
            "One-dimensional steady stagnant liquid-film diffusion with constant diffusivity and a caller-supplied irreversible first-order sink in CO2star.",
            "Gas-side film is physical; local Henry relation is linear and both phase bulk states remain fixed during the calculation.",
            "The liquid film sink kinetics are valid and pseudo-first-order across the film; no competing reactions or reagent depletion are represented.",
            "The result is a local instantaneous flux split and carries no geometry, corrosion, or lifetime interpretation.",
        ),
        source_ids=(SOURCE_ID, "rsc_fast_gas_liquid_reaction_kinetics"),
        qualification="user_model",
    )]
