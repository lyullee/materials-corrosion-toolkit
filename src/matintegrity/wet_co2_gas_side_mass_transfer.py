"""Estimate a gas-side CO2 transfer coefficient from a reviewed turbulent-flow state."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.wet_co2_gas_side_mass_transfer"
SOURCE_ID = "paolinelli_nesic_2021_chilton_colburn_gas_film"


class WetCo2GasSideMassTransferRequest(Contract):
    """Caller-reviewed gas hydrodynamic and fugacity-to-concentration state."""

    schema_version: Literal["matintegrity.wet_co2_gas_side_mass_transfer.v1"] = (
        "matintegrity.wet_co2_gas_side_mass_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    gas_flow_regime: Literal["single_phase_turbulent", "two_phase_gas_core", "other"]
    gas_mean_velocity_m_s: float = Field(gt=0)
    gas_wall_shear_stress_Pa: float = Field(gt=0)
    gas_density_kg_m3: float = Field(gt=0)
    gas_dynamic_viscosity_Pa_s: float = Field(gt=0)
    co2_gas_diffusivity_m2_s: float = Field(gt=0)
    hydraulic_diameter_m: float = Field(gt=0)
    gas_molar_concentration_sensitivity_mol_m3_Pa: float = Field(gt=0)
    friction_exponent: float = Field(ge=0.5, le=1.0)
    hydrodynamics_provider_id: str = Field(min_length=1)
    hydrodynamics_provider_revision: str = Field(min_length=1)
    hydrodynamics_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hydrodynamics_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gas_property_provider_id: str = Field(min_length=1)
    gas_property_provider_revision: str = Field(min_length=1)
    gas_property_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gas_property_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    diffusivity_record_id: str = Field(min_length=1)
    diffusivity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    provider_state_and_time_alignment_reviewed: bool
    gas_phase_regime_and_shear_reviewed: bool
    gas_diffusivity_species_temperature_and_mixture_reviewed: bool
    fugacity_sensitivity_and_units_reviewed: bool
    analogy_exponent_and_scope_reviewed: bool
    extrapolation_use_reviewed: bool = False

    @model_validator(mode="after")
    def verify_inputs_and_evidence(self):
        numeric = (
            self.time_s, self.gas_mean_velocity_m_s, self.gas_wall_shear_stress_Pa,
            self.gas_density_kg_m3, self.gas_dynamic_viscosity_Pa_s,
            self.co2_gas_diffusivity_m2_s, self.hydraulic_diameter_m,
            self.gas_molar_concentration_sensitivity_mol_m3_Pa, self.friction_exponent,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all flow and property values must be finite")
        evidence_ids = {row.source_id for row in self.evidence}
        required = {self.hydrodynamics_provider_id, self.gas_property_provider_id, self.diffusivity_record_id}
        if not required.issubset(evidence_ids):
            raise ValueError("Evidence must identify hydrodynamics, gas properties and diffusivity")
        return self


def _finite_exp(log_value: float) -> float | None:
    if not math.isfinite(log_value) or log_value > math.log(sys.float_info.max):
        return None
    if log_value < math.log(float.fromhex("0x0.0000000000001p-1022")):
        return 0.0
    value = math.exp(log_value)
    return value if math.isfinite(value) else None


def evaluate_wet_co2_gas_side_mass_transfer(request: WetCo2GasSideMassTransferRequest) -> Calculation:
    """Compute concentration-basis km, then convert using caller-supplied dCgas/dfCO2."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "time_s": request.time_s,
        "input_sha256": digest,
        "gas_flow_regime": request.gas_flow_regime,
        "hydrodynamics_provider_id": request.hydrodynamics_provider_id,
        "hydrodynamics_provider_revision": request.hydrodynamics_provider_revision,
        "hydrodynamics_result_sha256": request.hydrodynamics_result_sha256,
        "gas_property_provider_id": request.gas_property_provider_id,
        "gas_property_provider_revision": request.gas_property_provider_revision,
        "gas_property_result_sha256": request.gas_property_result_sha256,
        "diffusivity_record_id": request.diffusivity_record_id,
        "diffusivity_record_sha256": request.diffusivity_record_sha256,
        "friction_exponent": request.friction_exponent,
        "evidence": [item.model_dump(mode="json") for item in request.evidence],
        "corrosion_rate_or_life_inferred": False,
    }
    checks = (
        "provider_state_and_time_alignment_reviewed", "gas_phase_regime_and_shear_reviewed",
        "gas_diffusivity_species_temperature_and_mixture_reviewed",
        "fugacity_sensitivity_and_units_reviewed", "analogy_exponent_and_scope_reviewed",
    )
    missing = [name for name in checks if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    log_re = (
        math.log(request.gas_density_kg_m3) + math.log(request.gas_mean_velocity_m_s)
        + math.log(request.hydraulic_diameter_m) - math.log(request.gas_dynamic_viscosity_Pa_s)
    )
    log_sc = (
        math.log(request.gas_dynamic_viscosity_Pa_s) - math.log(request.gas_density_kg_m3)
        - math.log(request.co2_gas_diffusivity_m2_s)
    )
    re_g = _finite_exp(log_re)
    sc_g = _finite_exp(log_sc)
    if re_g is None or sc_g is None or re_g <= 0.0 or sc_g <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "gas Reynolds or Schmidt number outside finite numeric support",
        })
    if re_g < 4000.0:
        return Calculation(status="out_of_scope", values=base | {
            "gas_reynolds_number": re_g,
            "reason": "this turbulent-flow analogy is not applied below the caller-selected Re threshold",
        })
    if request.gas_flow_regime == "other" and not request.extrapolation_use_reviewed:
        return Calculation(status="needs_data", values=base | {
            "gas_reynolds_number": re_g,
            "reason": "review is required for an unclassified gas-side flow regime",
        })

    # Fanning friction factor f/2 = tau_w/(rho*u^2); j_D = (f/2)^n.
    log_fanning_half = (
        math.log(request.gas_wall_shear_stress_Pa) - math.log(request.gas_density_kg_m3)
        - 2.0 * math.log(request.gas_mean_velocity_m_s)
    )
    log_km = (
        request.friction_exponent * log_fanning_half
        + math.log(request.gas_mean_velocity_m_s) - (2.0 / 3.0) * math.log(sc_g)
    )
    km = _finite_exp(log_km)
    fanning = _finite_exp(math.log(2.0) + log_fanning_half)
    if km is None or km <= 0.0 or fanning is None or fanning <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "gas_reynolds_number": re_g, "gas_schmidt_number": sc_g,
            "reason": "gas-side transfer estimate exceeds finite numeric support",
        })
    pressure_basis_k = _finite_exp(
        math.log(km) + math.log(request.gas_molar_concentration_sensitivity_mol_m3_Pa)
    )
    if pressure_basis_k is None or pressure_basis_k <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "gas_reynolds_number": re_g, "gas_schmidt_number": sc_g,
            "gas_side_concentration_coefficient_m_s": km,
            "reason": "fugacity-basis gas coefficient exceeds finite numeric support",
        })
    return Calculation(values=base | {
        "status": "computed",
        "gas_reynolds_number": re_g,
        "gas_schmidt_number": sc_g,
        "fanning_friction_factor": fanning,
        "gas_side_concentration_coefficient_m_s": km,
        "gas_molar_concentration_sensitivity_mol_m3_Pa": request.gas_molar_concentration_sensitivity_mol_m3_Pa,
        "gas_side_fugacity_basis_coefficient_mol_m2_s_Pa": pressure_basis_k,
        "analogy": "caller-selected Chilton-Colburn friction/mass-transfer analogy for the gas phase",
        "interpretation_boundary": "A gas-side integral transfer coefficient from one reviewed gas state. It does not solve multiphase hydrodynamics, interfacial area or corrosion response.",
        "not_inferred": [
            "gas flow regime, wall shear or local near-interface turbulence",
            "gas-side concentration response to CO2 fugacity; supplied independently by caller",
            "liquid-side transfer, Henry equilibrium, aqueous chemistry or reaction enhancement",
            "wetted wall area, corrosion rate, metal loss, remaining life or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2GasSideMassTransferRequest,
        evaluator=evaluate_wet_co2_gas_side_mass_transfer,
        units={
            "time_s": "s", "gas_reynolds_number": "1", "gas_schmidt_number": "1",
            "fanning_friction_factor": "1", "gas_side_concentration_coefficient_m_s": "m/s",
            "gas_side_fugacity_basis_coefficient_mol_m2_s_Pa": "mol/(m2 s Pa)",
        },
        assumptions=(
            "Caller supplies one turbulent gas state with mean velocity, wall shear, density, viscosity and CO2 diffusivity.",
            "The friction analogy exponent is explicit and caller reviewed; no multiphase or flow-pattern correlation is inferred.",
            "The fugacity-basis coefficient uses caller-provided dCgas/d(fCO2), which may come from a thermodynamic provider.",
            "Only a gas-side coefficient is calculated; interfacial area, liquid film, aqueous reaction and corrosion remain separate.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
