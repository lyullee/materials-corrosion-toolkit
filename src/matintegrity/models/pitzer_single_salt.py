"""Caller-parameterized Pitzer mean activity for one pure aqueous electrolyte."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec


class PitzerSingleSaltActivity(Contract):
    schema_version: Literal["matintegrity.pitzer_single_salt_activity.v1"] = (
        "matintegrity.pitzer_single_salt_activity.v1"
    )
    assessment_id: str = Field(min_length=1)
    salt_id: str = Field(min_length=1)
    cation_id: str = Field(min_length=1)
    anion_id: str = Field(min_length=1)
    cation_charge_number: StrictInt = Field(gt=0, le=8)
    anion_charge_number: StrictInt = Field(ge=-8, lt=0)
    cation_stoichiometric_number: StrictInt = Field(ge=1, le=16)
    anion_stoichiometric_number: StrictInt = Field(ge=1, le=16)
    salt_molality_mol_kg_water: Positive
    temperature_K: Positive
    parameter_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0, le=5)
    maximum_supported_ionic_strength_mol_kg: Positive
    debye_huckel_A_phi: Positive
    debye_huckel_b_sqrt_kg_mol: Positive = 1.2
    beta_phi_0_kg_mol: float
    beta_phi_1_kg_mol: float
    beta_phi_2_kg_mol: float = 0.0
    alpha_1_sqrt_kg_mol: Positive
    alpha_2_sqrt_kg_mol: Positive
    c_phi_kg2_mol2: float
    parameter_set_id: str = Field(min_length=1)
    parameter_record_id: str = Field(min_length=1)
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_and_parameter_applicability_reviewed: bool
    single_pure_electrolyte_scope_reviewed: bool
    stoichiometry_and_charge_reviewed: bool
    parameter_values_and_units_reviewed: bool
    parameter_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_electroneutral_salt_and_parameter_lineage(self):
        if self.cation_id == self.anion_id:
            raise ValueError("cation and anion identities must be distinct")
        if (
            self.cation_stoichiometric_number * self.cation_charge_number
            + self.anion_stoichiometric_number * self.anion_charge_number
            != 0
        ):
            raise ValueError("declared salt formula must be electroneutral")
        if abs(self.temperature_K - self.parameter_temperature_K) > self.temperature_match_tolerance_K:
            raise ValueError("constant interaction parameters are restricted to their declared parameter temperature")
        if not any(
            row.source_id == self.parameter_set_id
            and row.sha256 == self.parameter_record_sha256
            for row in self.evidence
        ):
            raise ValueError("Evidence must identify the parameter set and match its record SHA-256")
        return self


def pitzer_single_salt_activity(x: PitzerSingleSaltActivity) -> Calculation:
    """Calculate mean ionic gamma and osmotic coefficient for one caller-defined salt."""
    input_digest = canonical_digest(x.model_dump(mode="json"))
    reviews = {
        "temperature_and_parameter_applicability_reviewed": x.temperature_and_parameter_applicability_reviewed,
        "single_pure_electrolyte_scope_reviewed": x.single_pure_electrolyte_scope_reviewed,
        "stoichiometry_and_charge_reviewed": x.stoichiometry_and_charge_reviewed,
        "parameter_values_and_units_reviewed": x.parameter_values_and_units_reviewed,
        "parameter_use_authorized": x.parameter_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    base = {
        "assessment_id": x.assessment_id,
        "salt_id": x.salt_id,
        "input_sha256": input_digest,
        "parameter_set_id": x.parameter_set_id,
        "parameter_record_id": x.parameter_record_id,
        "parameter_record_sha256": x.parameter_record_sha256,
        "temperature_K": x.temperature_K,
        "parameter_temperature_K": x.parameter_temperature_K,
        "temperature_match_tolerance_K": x.temperature_match_tolerance_K,
        "salt_molality_mol_kg_water": x.salt_molality_mol_kg_water,
        "activity_basis": "mean_ionic_molality_standard_state_1_mol_per_kg_water",
        "single_ion_activity_coefficients_assigned": False,
        "mixed_electrolyte_model": False,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    nu_c = x.cation_stoichiometric_number
    nu_a = x.anion_stoichiometric_number
    nu = nu_c + nu_a
    molality = x.salt_molality_mol_kg_water
    ionic_strength = 0.5 * molality * (
        nu_c * x.cation_charge_number**2 + nu_a * x.anion_charge_number**2
    )
    if not math.isfinite(ionic_strength):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "ionic_strength_not_representable",
        })
    if ionic_strength > x.maximum_supported_ionic_strength_mol_kg:
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "maximum_supported_ionic_strength_mol_kg": x.maximum_supported_ionic_strength_mol_kg,
            "reason": "ionic_strength_outside_parameter_support",
        })

    sqrt_i = math.sqrt(ionic_strength)
    b = x.debye_huckel_b_sqrt_kg_mol
    root_term = b * sqrt_i
    if not math.isfinite(root_term):
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "reason": "debye_huckel_argument_not_representable",
        })
    f_phi = -x.debye_huckel_A_phi * sqrt_i / (1.0 + root_term)
    f_gamma = -x.debye_huckel_A_phi * (
        sqrt_i / (1.0 + root_term) + (2.0 / b) * math.log1p(root_term)
    )
    alphas_and_betas = (
        (x.alpha_1_sqrt_kg_mol, x.beta_phi_1_kg_mol),
        (x.alpha_2_sqrt_kg_mol, x.beta_phi_2_kg_mol),
    )
    beta_phi = x.beta_phi_0_kg_mol
    beta_gamma = 2.0 * x.beta_phi_0_kg_mol
    for alpha, beta_phi_k in alphas_and_betas:
        beta_phi += beta_phi_k * math.exp(-alpha * sqrt_i)
        if beta_phi_k == 0.0:
            continue
        argument = alpha * sqrt_i
        if abs(argument) < 1e-3:
            ratio = 1.0 - (5.0 / 6.0) * argument + (3.0 / 8.0) * argument**2 - (7.0 / 60.0) * argument**3
        else:
            ratio = (
                1.0 - (1.0 + argument - 0.5 * argument**2) * math.exp(-argument)
            ) / argument**2
        beta_gamma += 2.0 * beta_phi_k * ratio

    c_gamma = 1.5 * x.c_phi_kg2_mol2
    pair_factor = 2.0 * nu_c * nu_a / nu
    triple_factor = 2.0 * (nu_c * nu_a) ** 1.5 / nu
    phi = 1.0 + abs(x.cation_charge_number * x.anion_charge_number) * f_phi
    phi += molality * pair_factor * beta_phi + molality**2 * triple_factor * x.c_phi_kg2_mol2
    ln_gamma_mean = abs(x.cation_charge_number * x.anion_charge_number) * f_gamma
    ln_gamma_mean += molality * pair_factor * beta_gamma + molality**2 * triple_factor * c_gamma
    if not math.isfinite(phi) or not math.isfinite(ln_gamma_mean):
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "reason": "pitzer_result_not_representable",
        })
    if phi <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "osmotic_coefficient": phi,
            "ln_mean_ionic_activity_coefficient": ln_gamma_mean,
            "reason": "nonphysical_or_nonfinite_pitzer_result",
        })
    try:
        gamma_mean = math.exp(ln_gamma_mean)
        mean_ionic_activity = gamma_mean * molality
        water_activity = math.exp(-0.01801528 * phi * nu * molality)
    except OverflowError:
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "ln_mean_ionic_activity_coefficient": ln_gamma_mean,
            "reason": "pitzer_result_exceeds_float_range",
        })
    if gamma_mean <= 0.0 or water_activity <= 0.0 or not all(
        math.isfinite(value) for value in (gamma_mean, mean_ionic_activity, water_activity)
    ):
        return Calculation(status="out_of_scope", values=base | {
            "ionic_strength_mol_kg": ionic_strength,
            "reason": "pitzer_output_not_finite",
        })
    return Calculation(status="computed", values=base | {
        "ionic_strength_mol_kg": ionic_strength,
        "ln_mean_ionic_activity_coefficient": ln_gamma_mean,
        "mean_ionic_activity_coefficient": gamma_mean,
        "mean_ionic_activity_mol_kg_water": mean_ionic_activity,
        "osmotic_coefficient": phi,
        "water_activity": water_activity,
        "debye_huckel_f_gamma": f_gamma,
        "debye_huckel_f_phi": f_phi,
        "beta_gamma_kg_mol": beta_gamma,
        "beta_phi_kg_mol": beta_phi,
        "c_gamma_kg2_mol2": c_gamma,
        "pitzer_b_sqrt_kg_mol": b,
        "formula": "single pure electrolyte Pitzer virial form with caller beta0/beta1/beta2/Cphi; no mixed-salt terms",
    }, notes=(
        "The output is a mean ionic activity coefficient and osmotic coefficient for one pure electrolyte using caller-supplied coefficients at the declared temperature. It does not assign individual-ion activity coefficients or model mixed electrolytes, complexes, solvent-specific interactions, precipitation, corrosion rate, or acceptance.",
        "Parameter completeness and thermodynamic consistency over the stated support are caller responsibilities; a parameter-range review gate does not independently qualify a coefficient set.",
    ))


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.pitzer_single_salt_activity",
            PitzerSingleSaltActivity,
            pitzer_single_salt_activity,
            {
                "ionic_strength_mol_kg": "mol/kg-water",
                "mean_ionic_activity_coefficient": "1",
                "ln_mean_ionic_activity_coefficient": "1",
                "mean_ionic_activity_mol_kg_water": "mol/kg-water",
                "osmotic_coefficient": "1",
                "water_activity": "1",
                "debye_huckel_f_gamma": "1",
                "debye_huckel_f_phi": "1",
                "beta_gamma_kg_mol": "kg/mol",
                "beta_phi_kg_mol": "kg/mol",
                "c_gamma_kg2_mol2": "(kg/mol)^2",
            },
            (
                "One pure aqueous electrolyte with a caller-reviewed electroneutral formula, molality-scale Pitzer-Debye-Huckel Aphi/b, beta0/beta1/beta2 and Cphi parameters inside caller-declared temperature and ionic-strength support.",
                "No mixed-salt theta/psi interactions, single-ion activity convention, parameter fitting, phase equilibrium, kinetic law or corrosion inference is included.",
            ),
            ("caller_single_salt_pitzer_mean_activity",),
        )
    ]
