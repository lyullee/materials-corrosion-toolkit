"""Caller-evidence-bound saturation index for one pure electrolyte."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .models.pitzer_single_salt import PitzerSingleSaltActivity, pitzer_single_salt_activity
from .registry import ModelSpec

MODEL_ID = "chemistry.pitzer_salt_saturation_index"
SOURCE_ID = "caller_pitzer_salt_saturation_index"


class PitzerSaltSaturationIndex(Contract):
    """Compare one Pitzer pure-salt ionic activity product with caller Ksp."""

    schema_version: Literal["matintegrity.pitzer_salt_saturation_index.v1"] = (
        "matintegrity.pitzer_salt_saturation_index.v1"
    )
    assessment_id: str = Field(min_length=1)
    activity_request: PitzerSingleSaltActivity
    log10_solubility_product: float
    solubility_product_temperature_K: float = Field(gt=0.0)
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0.0, le=5.0)
    solubility_product_source_id: str = Field(min_length=1)
    solubility_product_record_id: str = Field(min_length=1)
    solubility_product_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_tolerance_log10: float = Field(default=1e-8, ge=0.0, le=0.1)
    salt_formula_and_standard_state_reviewed: bool
    solubility_product_temperature_and_applicability_reviewed: bool
    complete_single_salt_scope_reviewed: bool
    solubility_product_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def check_ksp_provenance_and_temperature(self):
        if not math.isfinite(self.log10_solubility_product):
            raise ValueError("log10 solubility product must be finite")
        if abs(self.activity_request.temperature_K - self.solubility_product_temperature_K) > self.temperature_match_tolerance_K:
            raise ValueError("solubility product is outside its caller-declared temperature match")
        if not any(
            row.source_id == self.solubility_product_source_id
            and row.sha256 == self.solubility_product_record_sha256
            for row in self.evidence
        ):
            raise ValueError("Evidence must identify and hash-match the solubility-product record")
        return self


def evaluate_pitzer_salt_saturation_index(request: PitzerSaltSaturationIndex) -> Calculation:
    """Return log10(Q/Ksp) for the caller-declared pure-salt standard state."""
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    salt = request.activity_request
    activity_request_sha256 = canonical_digest(salt.model_dump(mode="json"))
    reviews = {
        "salt_formula_and_standard_state_reviewed": request.salt_formula_and_standard_state_reviewed,
        "solubility_product_temperature_and_applicability_reviewed": request.solubility_product_temperature_and_applicability_reviewed,
        "complete_single_salt_scope_reviewed": request.complete_single_salt_scope_reviewed,
        "solubility_product_use_authorized": request.solubility_product_use_authorized,
    }
    base = {
        "assessment_id": request.assessment_id,
        "salt_id": salt.salt_id,
        "input_sha256": input_sha256,
        "activity_request_sha256": activity_request_sha256,
        "solubility_product_source_id": request.solubility_product_source_id,
        "solubility_product_record_id": request.solubility_product_record_id,
        "solubility_product_record_sha256": request.solubility_product_record_sha256,
        "temperature_K": salt.temperature_K,
        "solubility_product_temperature_K": request.solubility_product_temperature_K,
        "log10_solubility_product": request.log10_solubility_product,
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "single_ion_activity_coefficients_assigned": False,
        "phase_amount_or_kinetics_computed": False,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    activity = pitzer_single_salt_activity(salt)
    if activity.status != "computed":
        return Calculation(status=activity.status, values=base | {
            "activity_status": activity.status,
            "activity_values": activity.values,
            "saturation_index": None,
        }, notes=("The saturation screen is withheld unless the nested pure-salt activity calculation completes.",))
    mean_activity = activity.values["mean_ionic_activity_mol_kg_water"]
    if not math.isfinite(mean_activity) or mean_activity <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "mean_ionic_activity_not_positive_finite",
            "saturation_index": None,
        })

    exponent = salt.cation_stoichiometric_number + salt.anion_stoichiometric_number
    # The Pitzer provider reports mean ionic activity on the 1 mol/kg standard
    # state, so its numerical value is dimensionless in the log-product below.
    log10_ion_activity_product = exponent * math.log10(mean_activity)
    log10_ratio = log10_ion_activity_product - request.log10_solubility_product
    tolerance = request.boundary_tolerance_log10
    state = (
        "undersaturated" if log10_ratio < -tolerance
        else "supersaturated" if log10_ratio > tolerance
        else "near_saturation_boundary"
    )
    return Calculation(values=base | {
        "status": "computed",
        "activity_status": "computed",
        "activity_result_sha256": canonical_digest(activity.model_dump(mode="json")),
        "mean_ionic_activity_mol_kg_water": mean_activity,
        "mean_ionic_activity_standard_state_mol_kg_water": 1.0,
        "ion_activity_product_exponent": exponent,
        "log10_ion_activity_product": log10_ion_activity_product,
        "log10_activity_quotient_over_solubility_product": log10_ratio,
        "boundary_tolerance_log10": tolerance,
        "screening_state": state,
        "interpretation": "pure-salt equilibrium screening against only the caller-supplied Ksp and standard state",
        "precipitation_or_dissolution_amount_inferred": False,
        "corrosion_or_qualification_inferred": False,
    }, notes=(
        "This screen compares a caller-parameterized pure-salt mean ionic activity with caller-supplied Ksp under an explicitly reviewed standard state.",
        "A saturation index does not compute phase amount, nucleation, kinetics, corrosion, acceptance, or qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=PitzerSaltSaturationIndex,
        evaluator=evaluate_pitzer_salt_saturation_index,
        units={
            "mean_ionic_activity_mol_kg_water": "mol/kg",
            "log10_ion_activity_product": "1",
            "log10_activity_quotient_over_solubility_product": "1",
            "boundary_tolerance_log10": "1",
        },
        assumptions=(
            "One caller-reviewed pure-salt Pitzer calculation and one temperature-matched caller Ksp record share the declared mean-ionic standard state.",
            "Only the finite pure-salt equilibrium saturation index is screened; no phase amount, precipitation kinetics, mixed electrolyte behavior, corrosion, probability, or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
