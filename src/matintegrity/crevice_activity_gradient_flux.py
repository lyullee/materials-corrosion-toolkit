"""Activity-corrected zero-current Nernst–Planck flux across one crevice face."""

from __future__ import annotations

import math

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_activity_gradient_nernst_planck_flux_1d"
SPECIES_SOURCE_ID = "caller_crevice_activity_gradient_species_face_state"
METHOD_SOURCE_ID = "activity_corrected_zero_current_nernst_planck_face_flux"


class CreviceActivityGradientSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    diffusivity_m2_s: Positive
    left_concentration_mol_m3: Positive
    right_concentration_mol_m3: Positive
    left_activity_coefficient: Positive
    right_activity_coefficient: Positive


class CreviceActivityGradientFluxRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    face_id: str = Field(min_length=1)
    face_distance_m: Positive
    axial_velocity_m_s: float
    species: tuple[CreviceActivityGradientSpecies, ...] = Field(min_length=2, max_length=64)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    activity_standard_state_and_single_ion_convention_reviewed: bool
    activity_gradient_thermodynamic_consistency_reviewed: bool
    diffusivity_and_face_mapping_reviewed: bool
    local_electroneutrality_and_zero_current_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_basis(self):
        if not math.isfinite(self.axial_velocity_m_s):
            raise ValueError("axial face velocity must be finite")
        ids = [row.species_id for row in self.species]
        if len(ids) != len(set(ids)):
            raise ValueError("species identifiers must be unique")
        if not any(row.charge_number > 0 for row in self.species) or not any(
            row.charge_number < 0 for row in self.species
        ):
            raise ValueError("zero-current closure requires positive and negative charged species")
        for side in ("left", "right"):
            values = [getattr(row, f"{side}_concentration_mol_m3") for row in self.species]
            charge = math.fsum(row.charge_number * value for row, value in zip(self.species, values))
            scale = math.fsum(abs(row.charge_number) * value for row, value in zip(self.species, values))
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError(f"{side} face state must be locally electroneutral")
        if not all((
            self.activity_standard_state_and_single_ion_convention_reviewed,
            self.activity_gradient_thermodynamic_consistency_reviewed,
            self.diffusivity_and_face_mapping_reviewed,
            self.local_electroneutrality_and_zero_current_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all transport, activity, convention and authorization reviews are required")
        if not any(row.source_id == self.provider_id and row.sha256 for row in self.provider_evidence):
            raise ValueError("provider Evidence must bind the declared provider to a content digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must identify a license or permitted-use basis")
        return self


def evaluate_crevice_activity_gradient_flux(request: CreviceActivityGradientFluxRequest) -> Calculation:
    """Compute one face's species fluxes and the dimensionless potential gradient for zero current."""
    rows = request.species
    z = [float(row.charge_number) for row in rows]
    d = [row.diffusivity_m2_s for row in rows]
    c_left = [row.left_concentration_mol_m3 for row in rows]
    c_right = [row.right_concentration_mol_m3 for row in rows]
    c_face = [(a + b) * 0.5 for a, b in zip(c_left, c_right)]
    grad_c = [(b - a) / request.face_distance_m for a, b in zip(c_left, c_right)]
    grad_ln_gamma = [
        math.log(row.right_activity_coefficient / row.left_activity_coefficient) / request.face_distance_m
        for row in rows
    ]
    # Upwind advection uses the left state for positive axial velocity and right for negative velocity.
    c_upwind = c_left if request.axial_velocity_m_s >= 0 else c_right
    numerator = math.fsum(
        -charge * diffusivity * (gradient + concentration * gamma_gradient)
        + request.axial_velocity_m_s * charge * upwind
        for charge, diffusivity, gradient, concentration, gamma_gradient, upwind
        in zip(z, d, grad_c, c_face, grad_ln_gamma, c_upwind)
    )
    denominator = math.fsum(charge * charge * diffusivity * concentration
                             for charge, diffusivity, concentration in zip(z, d, c_face))
    if not math.isfinite(denominator) or denominator <= 0:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "zero_ionic_mobility_at_face",
            "input_sha256": canonical_digest(request.model_dump(mode="json")),
        })
    grad_psi = numerator / denominator
    flux = [
        -diffusivity * (gradient + concentration * gamma_gradient + charge * concentration * grad_psi)
        + request.axial_velocity_m_s * upwind
        for charge, diffusivity, gradient, concentration, gamma_gradient, upwind
        in zip(z, d, grad_c, c_face, grad_ln_gamma, c_upwind)
    ]
    current = math.fsum(charge * value for charge, value in zip(z, flux))
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "face_id": request.face_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "dimensionless_electric_potential_gradient_per_m": grad_psi,
        "species_molar_flux_mol_m2_s_by_id": {row.species_id: value for row, value in zip(rows, flux)},
        "activity_log_gradient_per_m_by_species": {row.species_id: value for row, value in zip(rows, grad_ln_gamma)},
        "zero_current_residual_mol_eq_m2_s": current,
        "interpretation": "caller_activity_corrected_single_face_zero_current_transport",
        "limitations": [
            "Uses caller-provided concentrations, single-ion activity coefficients and constant diffusivities at one face; no activity law or speciation is solved.",
            "The arithmetic face concentration and log-gamma difference are discrete choices that require review for the application and mesh.",
            "Zero current is imposed locally and does not represent an externally imposed electrical circuit or transient charge storage.",
            "No spatial integration, reaction, phase equilibrium, wall loss, corrosion rate, life, probability or acceptance is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceActivityGradientFluxRequest,
        evaluator=evaluate_crevice_activity_gradient_flux,
        units={
            "dimensionless_electric_potential_gradient_per_m": "m^-1",
            "species_molar_flux_mol_m2_s_by_id.*": "mol/(m^2*s)",
            "activity_log_gradient_per_m_by_species.*": "m^-1",
            "zero_current_residual_mol_eq_m2_s": "mol_eq/(m^2*s)",
        },
        assumptions=(
            "One-dimensional local face law with caller-resolved electroneutral states, linear concentration gradient and log-activity-coefficient gradient.",
            "A local dimensionless electric-potential gradient is chosen to make the summed ionic current zero; advection is upwinded from the caller face direction.",
            "Caller reviews the single-ion activity convention, thermodynamic consistency, diffusivities and face-state mapping.",
        ),
        source_ids=(SPECIES_SOURCE_ID, METHOD_SOURCE_ID),
    )]
