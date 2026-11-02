"""Closed carbonate alkalinity balance for a caller-supplied CO2-star state."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_carbonate_alkalinity_speciation"
SOURCE_ID = "caller_conditional_carbonate_constants_and_alkalinity"


class WetCo2CarbonateAlkalinityRequest(Contract):
    """Solve carbonate-only alkalinity at a fixed neutral dissolved CO2-star state."""

    schema_version: Literal["matintegrity.wet_co2_carbonate_alkalinity_speciation.v1"] = (
        "matintegrity.wet_co2_carbonate_alkalinity_speciation.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    temperature_K: float = Field(gt=0)
    co2star_concentration_mol_m3: float = Field(ge=0)
    total_alkalinity_mol_m3: float
    conditional_k1_mol_m3: float = Field(gt=0)
    conditional_k2_mol_m3: float = Field(gt=0)
    conditional_kw_mol2_m6: float = Field(gt=0)
    pH_lower_bound: float = Field(ge=-2, le=15)
    pH_upper_bound: float = Field(ge=-2, le=15)
    constant_provider_id: str = Field(min_length=1)
    constant_provider_revision: str = Field(min_length=1)
    constant_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    constant_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    constant_record_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    alkalinity_species_scope_reviewed: bool
    conditional_constant_convention_reviewed: bool
    ideal_concentration_activity_approximation_reviewed: bool
    state_and_use_authorized: bool

    @model_validator(mode="after")
    def validate_domain(self):
        numeric = (
            self.temperature_K,
            self.co2star_concentration_mol_m3,
            self.total_alkalinity_mol_m3,
            self.conditional_k1_mol_m3,
            self.conditional_k2_mol_m3,
            self.conditional_kw_mol2_m6,
            self.pH_lower_bound,
            self.pH_upper_bound,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all chemistry inputs must be finite")
        if self.pH_upper_bound <= self.pH_lower_bound:
            raise ValueError("pH bracket upper bound must exceed lower bound")
        if self.constant_provider_id not in {item.source_id for item in self.evidence}:
            raise ValueError("Evidence must identify the conditional-constant provider")
        return self


def _species_at_pH(request: WetCo2CarbonateAlkalinityRequest, pH: float) -> dict[str, float] | None:
    """Evaluate the ideal concentration-constant carbonate distribution at a trial pH."""
    # Convert the pH activity convention (mol/L standard state) to mol/m3.
    h = 1000.0 * (10.0 ** (-pH))
    if not math.isfinite(h) or h <= 0.0:
        return None
    co2 = request.co2star_concentration_mol_m3
    bicarbonate = request.conditional_k1_mol_m3 * co2 / h
    carbonate = request.conditional_k2_mol_m3 * bicarbonate / h
    hydroxide = request.conditional_kw_mol2_m6 / h
    values = (h, co2, bicarbonate, carbonate, hydroxide)
    if not all(math.isfinite(value) and value >= 0.0 for value in values):
        return None
    alkalinity = bicarbonate + 2.0 * carbonate + hydroxide - h
    if not math.isfinite(alkalinity):
        return None
    return {
        "hydrogen_ion_mol_m3": h,
        "co2star_mol_m3": co2,
        "bicarbonate_mol_m3": bicarbonate,
        "carbonate_mol_m3": carbonate,
        "hydroxide_mol_m3": hydroxide,
        "carbonate_only_alkalinity_mol_m3": alkalinity,
    }


def evaluate_wet_co2_carbonate_alkalinity_speciation(
    request: WetCo2CarbonateAlkalinityRequest,
) -> Calculation:
    """Invert the carbonate-only alkalinity equation for pH and species concentrations."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "input_sha256": digest,
        "temperature_K": request.temperature_K,
        "co2star_concentration_mol_m3": request.co2star_concentration_mol_m3,
        "total_alkalinity_mol_m3": request.total_alkalinity_mol_m3,
        "constant_provider_id": request.constant_provider_id,
        "constant_provider_revision": request.constant_provider_revision,
        "constant_configuration_sha256": request.constant_configuration_sha256,
        "constant_result_sha256": request.constant_result_sha256,
        "constant_record_id": request.constant_record_id,
    }
    reviews = (
        "alkalinity_species_scope_reviewed",
        "conditional_constant_convention_reviewed",
        "ideal_concentration_activity_approximation_reviewed",
        "state_and_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    lo, hi = request.pH_lower_bound, request.pH_upper_bound
    lo_species, hi_species = _species_at_pH(request, lo), _species_at_pH(request, hi)
    if lo_species is None or hi_species is None:
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "species concentrations are outside finite numeric support at pH bracket endpoints",
        })
    target = request.total_alkalinity_mol_m3
    f_lo = lo_species["carbonate_only_alkalinity_mol_m3"] - target
    f_hi = hi_species["carbonate_only_alkalinity_mol_m3"] - target
    if f_lo == 0.0:
        root_pH, species = lo, lo_species
    elif f_hi == 0.0:
        root_pH, species = hi, hi_species
    elif f_lo * f_hi > 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "pH_bracket": [lo, hi],
            "alkalinity_residual_at_lower_bound_mol_m3": f_lo,
            "alkalinity_residual_at_upper_bound_mol_m3": f_hi,
            "failure_reason": "caller pH bracket does not contain an alkalinity root",
        })
    else:
        species = None
        root_pH = math.nan
        for _ in range(160):
            mid = lo + (hi - lo) * 0.5
            mid_species = _species_at_pH(request, mid)
            if mid_species is None:
                return Calculation(status="out_of_scope", values=base | {
                    "failure_reason": "carbonate species left finite numeric support during bracket solve",
                })
            residual = mid_species["carbonate_only_alkalinity_mol_m3"] - target
            if residual == 0.0 or mid == lo or mid == hi:
                root_pH, species = mid, mid_species
                break
            if (residual > 0.0) == (f_lo > 0.0):
                lo, f_lo = mid, residual
            else:
                hi, f_hi = mid, residual
        if species is None:
            root_pH = lo + (hi - lo) * 0.5
            species = _species_at_pH(request, root_pH)
        if species is None:
            return Calculation(status="out_of_scope", values=base | {
                "failure_reason": "carbonate speciation did not produce finite concentrations",
            })

    residual = species["carbonate_only_alkalinity_mol_m3"] - target
    return Calculation(values=base | {
        "status": "computed",
        "pH_ideal_concentration_scale": root_pH,
        "species_mol_m3": species,
        "alkalinity_residual_mol_m3": residual,
        "conditional_equilibrium_constants": {
            "k1_mol_m3": request.conditional_k1_mol_m3,
            "k2_mol_m3": request.conditional_k2_mol_m3,
            "kw_mol2_m6": request.conditional_kw_mol2_m6,
        },
        "method": "bisection of carbonate-only alkalinity balance with caller-supplied conditional concentration constants",
        "interpretation_boundary": "Ideal concentration-scale carbonate speciation at one fixed CO2star state. Not a full electrolyte, activity-coefficient, mineral-equilibrium, kinetic or corrosion model.",
        "not_inferred": [
            "alkalinity from ammonia, phosphate, borate, silicate, organic acids or other non-carbonate buffers",
            "nonideal activity coefficients, salinity effects or ion pairing",
            "CO2star evolution, gas-liquid transfer, liquid inventory or kinetics",
            "metal dissolution, corrosion rate, damage, acceptance or risk probability",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CarbonateAlkalinityRequest,
        evaluator=evaluate_wet_co2_carbonate_alkalinity_speciation,
        units={
            "co2star_concentration_mol_m3": "mol/m3",
            "total_alkalinity_mol_m3": "mol/m3 as charge equivalents",
            "species_mol_m3.*": "mol/m3",
            "pH_ideal_concentration_scale": "dimensionless",
        },
        assumptions=(
            "Only CO2star, bicarbonate, carbonate, hydrogen and hydroxide contribute to the alkalinity balance.",
            "Caller-supplied conditional equilibrium constants use an ideal concentration convention and match the solution temperature and composition.",
            "The input CO2star state and total alkalinity are fixed for this equilibrium calculation.",
            "No thermodynamic or field qualification is implied by evidence identifiers or review flags.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
