"""Estimate a liquid-side transfer coefficient from reviewed local pipe-flow state."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "degradation.wet_co2_liquid_side_mass_transfer"
SOURCE_ID = "paolinelli_nesic_2021_chilton_colburn_liquid_transfer"
DEFAULT_FRICTION_EXPONENT = 0.96
PUBLISHED_SCHMIDT_RANGE = (100.0, 1000.0)
MIN_REYNOLDS = 4000.0


class WetCo2LiquidSideMassTransferRequest(Contract):
    """A caller-reviewed liquid velocity/shear state from a pipe hydrodynamics solver."""

    schema_version: Literal["matintegrity.wet_co2_liquid_side_mass_transfer.v1"] = (
        "matintegrity.wet_co2_liquid_side_mass_transfer.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    liquid_flow_region: Literal[
        "single_phase_pipe", "stratified_layer", "slug_body", "slug_film", "annular_film", "other"
    ]
    liquid_mean_velocity_m_s: float = Field(gt=0)
    liquid_wall_shear_stress_Pa: float = Field(gt=0)
    liquid_density_kg_m3: float = Field(gt=0)
    liquid_dynamic_viscosity_Pa_s: float = Field(gt=0)
    corrosive_species_diffusivity_m2_s: float = Field(gt=0)
    hydraulic_diameter_m: float = Field(gt=0)
    friction_exponent: float = Field(default=DEFAULT_FRICTION_EXPONENT, ge=0.5, le=1.0)
    hydrodynamic_provider_id: str = Field(min_length=1)
    hydrodynamic_provider_revision: str = Field(min_length=1)
    hydrodynamic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hydrodynamic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    diffusivity_record_id: str = Field(min_length=1)
    diffusivity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=64)
    provider_state_and_time_alignment_reviewed: bool
    liquid_wetting_and_wall_area_basis_reviewed: bool
    turbulent_flow_and_local_shear_reviewed: bool
    diffusivity_species_temperature_and_solvent_match_reviewed: bool
    friction_exponent_and_scope_reviewed: bool
    outside_published_schmidt_range_reviewed: bool = False

    @model_validator(mode="after")
    def verify_finite_inputs_and_evidence(self):
        numeric = (
            self.time_s,
            self.liquid_mean_velocity_m_s,
            self.liquid_wall_shear_stress_Pa,
            self.liquid_density_kg_m3,
            self.liquid_dynamic_viscosity_Pa_s,
            self.corrosive_species_diffusivity_m2_s,
            self.hydraulic_diameter_m,
            self.friction_exponent,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all state and property values must be finite")
        evidence_ids = {row.source_id for row in self.evidence}
        required = {self.hydrodynamic_provider_id, self.diffusivity_record_id}
        if not required.issubset(evidence_ids):
            raise ValueError("Evidence must identify both the flow provider and diffusivity record")
        return self


def _finite_exp(log_value: float) -> float | None:
    if not math.isfinite(log_value) or log_value > math.log(sys.float_info.max):
        return None
    if log_value < math.log(float.fromhex("0x0.0000000000001p-1022")):
        return 0.0
    value = math.exp(log_value)
    return value if math.isfinite(value) and value > 0.0 else None


def evaluate_wet_co2_liquid_side_mass_transfer(
    request: WetCo2LiquidSideMassTransferRequest,
) -> Calculation:
    """Estimate km from liquid friction state using a reviewed Chilton-Colburn analogy."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "time_s": request.time_s,
        "input_sha256": digest,
        "liquid_flow_region": request.liquid_flow_region,
        "hydrodynamic_provider_id": request.hydrodynamic_provider_id,
        "hydrodynamic_provider_revision": request.hydrodynamic_provider_revision,
        "hydrodynamic_configuration_sha256": request.hydrodynamic_configuration_sha256,
        "hydrodynamic_result_sha256": request.hydrodynamic_result_sha256,
        "diffusivity_record_id": request.diffusivity_record_id,
        "diffusivity_record_sha256": request.diffusivity_record_sha256,
        "friction_exponent": request.friction_exponent,
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "source_ids": sorted({row.source_id for row in request.evidence}),
        "corrosion_rate_or_life_inferred": False,
    }
    reviews = (
        "provider_state_and_time_alignment_reviewed",
        "liquid_wetting_and_wall_area_basis_reviewed",
        "turbulent_flow_and_local_shear_reviewed",
        "diffusivity_species_temperature_and_solvent_match_reviewed",
        "friction_exponent_and_scope_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    log_re = (
        math.log(request.liquid_density_kg_m3)
        + math.log(request.liquid_mean_velocity_m_s)
        + math.log(request.hydraulic_diameter_m)
        - math.log(request.liquid_dynamic_viscosity_Pa_s)
    )
    log_sc = (
        math.log(request.liquid_dynamic_viscosity_Pa_s)
        - math.log(request.liquid_density_kg_m3)
        - math.log(request.corrosive_species_diffusivity_m2_s)
    )
    reynolds = _finite_exp(log_re)
    schmidt = _finite_exp(log_sc)
    if reynolds is None or schmidt is None or reynolds <= 0.0 or schmidt <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "dimensionless liquid-flow groups exceed finite numeric support"
        })
    if reynolds < MIN_REYNOLDS:
        return Calculation(status="out_of_scope", values=base | {
            "reynolds_number": reynolds,
            "minimum_reynolds_number": MIN_REYNOLDS,
            "reason": "the selected analogy is restricted here to fully turbulent liquid flow"
        })
    in_schmidt_support = PUBLISHED_SCHMIDT_RANGE[0] <= schmidt <= PUBLISHED_SCHMIDT_RANGE[1]
    if not in_schmidt_support and not request.outside_published_schmidt_range_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reynolds_number": reynolds,
            "schmidt_number": schmidt,
            "published_schmidt_support": list(PUBLISHED_SCHMIDT_RANGE),
            "reason": "caller review is required before using the analogy outside the cited exponent support"
        })

    # Chilton-Colburn form with Fanning f = 2*tau/(rho*u^2):
    # km = (f/2)^n * u * Sc^(-2/3).
    log_fanning_half = (
        math.log(request.liquid_wall_shear_stress_Pa)
        - math.log(request.liquid_density_kg_m3)
        - 2.0 * math.log(request.liquid_mean_velocity_m_s)
    )
    log_fanning = math.log(2.0) + log_fanning_half
    fanning = _finite_exp(log_fanning)
    km = _finite_exp(
        request.friction_exponent * log_fanning_half
        + math.log(request.liquid_mean_velocity_m_s)
        - (2.0 / 3.0) * math.log(schmidt)
    )
    if fanning is None or fanning <= 0.0 or km is None or km <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reynolds_number": reynolds,
            "schmidt_number": schmidt,
            "reason": "friction or liquid-side transfer estimate exceeds finite numeric support"
        })
    sherwood = _finite_exp(
        math.log(km)
        + math.log(request.hydraulic_diameter_m)
        - math.log(request.corrosive_species_diffusivity_m2_s)
    )
    if sherwood is None or sherwood <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reynolds_number": reynolds,
            "schmidt_number": schmidt,
            "fanning_friction_factor": fanning,
            "liquid_side_mass_transfer_coefficient_m_s": km,
            "reason": "Sherwood number exceeds finite numeric support"
        })

    return Calculation(values=base | {
        "status": "computed",
        "mean_liquid_velocity_m_s": request.liquid_mean_velocity_m_s,
        "liquid_wall_shear_stress_Pa": request.liquid_wall_shear_stress_Pa,
        "liquid_density_kg_m3": request.liquid_density_kg_m3,
        "liquid_dynamic_viscosity_Pa_s": request.liquid_dynamic_viscosity_Pa_s,
        "species_diffusivity_m2_s": request.corrosive_species_diffusivity_m2_s,
        "hydraulic_diameter_m": request.hydraulic_diameter_m,
        "reynolds_number": reynolds,
        "schmidt_number": schmidt,
        "fanning_friction_factor": fanning,
        "sherwood_number": sherwood,
        "liquid_side_mass_transfer_coefficient_m_s": km,
        "schmidt_range_within_cited_exponent_support": in_schmidt_support,
        "analogy": "Chilton-Colburn momentum/mass-transfer analogy with caller-selected friction exponent",
        "interpretation_boundary": "This is an integral liquid-side coefficient calculated from caller-supplied local mean velocity, wall shear stress and molecular diffusivity. It is not a multiphase-flow solver, interfacial-area model, reaction-layer solution or corrosion-rate prediction.",
        "not_inferred": [
            "gas-liquid flow pattern or hydrodynamic state",
            "wall wetting or wetted area",
            "gas-film coefficient or Henry/fugacity state",
            "aqueous speciation, charge migration or homogeneous reaction",
            "scale formation, corrosion rate, metal loss, wall thickness or service life",
            "model-form uncertainty or engineering qualification",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2LiquidSideMassTransferRequest,
        evaluator=evaluate_wet_co2_liquid_side_mass_transfer,
        units={
            "time_s": "s",
            "mean_liquid_velocity_m_s": "m/s",
            "liquid_wall_shear_stress_Pa": "Pa",
            "reynolds_number": "1",
            "schmidt_number": "1",
            "fanning_friction_factor": "1",
            "sherwood_number": "1",
            "liquid_side_mass_transfer_coefficient_m_s": "m/s",
        },
        assumptions=(
            "The caller supplies the liquid-phase mean velocity and wall shear stress for one exact region/time from a separately identified hydrodynamics provider.",
            "The aqueous species is dilute enough for a molecular-diffusivity-based Schmidt number and an integral coefficient to be meaningful.",
            "The liquid phase is turbulent and the pipe hydraulic diameter is the characteristic length used only for dimensionless reporting.",
            "The default friction exponent 0.96 is a literature-supported choice over a limited Schmidt-number range; any replacement exponent is caller-selected and reviewed.",
            "The result estimates liquid-side mass transfer only; the gas film, chemistry, reaction and corrosion response remain separate models.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
