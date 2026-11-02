"""Bounded neutral-solid formula proposals from caller-declared aqueous ions."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "chemistry.wet_co2_neutral_solid_formula_proposals"
SOURCE_ID = "caller_ion_pair_charge_balanced_solid_formula_proposals"
MAX_ION_TYPES = 80


class WetCo2AqueousIon(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    elemental_composition: dict[str, StrictInt]
    source_record_id: str = Field(min_length=1)
    evidence: Evidence

    @model_validator(mode="after")
    def validate_formula_record(self):
        if self.charge_number == 0:
            raise ValueError("formula proposal inputs must be charged aqueous species")
        if not self.elemental_composition or any(not element.strip() or count < 0
                                                  for element, count in self.elemental_composition.items()) \
                or not any(self.elemental_composition.values()):
            raise ValueError("complete nonnegative elemental composition is required")
        if self.evidence.sha256 is None:
            raise ValueError("ion formula Evidence must carry a source digest")
        return self


class WetCo2NeutralSolidFormulaProposals(Contract):
    """Generate binary cation/anion formula proposals, not stable-phase claims."""

    schema_version: Literal["matintegrity.wet_co2_neutral_solid_formula_proposals.v1"] = (
        "matintegrity.wet_co2_neutral_solid_formula_proposals.v1"
    )
    proposal_set_id: str = Field(min_length=1)
    cations: tuple[WetCo2AqueousIon, ...] = Field(min_length=1, max_length=MAX_ION_TYPES)
    anions: tuple[WetCo2AqueousIon, ...] = Field(min_length=1, max_length=MAX_ION_TYPES)
    maximum_pair_proposals: StrictInt = Field(default=2000, ge=1, le=5000)
    ion_formula_and_charge_reviewed: bool
    binary_formula_scope_reviewed: bool
    proposal_only_manual_phase_review_required: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_ion_sets(self):
        ions = (*self.cations, *self.anions)
        ids = [row.species_id for row in ions]
        if len(ids) != len(set(ids)):
            raise ValueError("ion species IDs must be unique across cations and anions")
        if any(row.charge_number <= 0 for row in self.cations):
            raise ValueError("cation inputs must have positive declared charge")
        if any(row.charge_number >= 0 for row in self.anions):
            raise ValueError("anion inputs must have negative declared charge")
        if len(self.cations) * len(self.anions) > self.maximum_pair_proposals:
            raise ValueError("cation-anion Cartesian product exceeds the caller proposal budget")
        if any(row.evidence.origin == "synthetic" for row in ions):
            raise ValueError("synthetic ion formula evidence cannot substantiate physical phase proposals")
        return self


def _compose_formula(cation: WetCo2AqueousIon,
                     anion: WetCo2AqueousIon) -> dict[str, int]:
    divisor = math.gcd(cation.charge_number, abs(anion.charge_number))
    cation_count = abs(anion.charge_number) // divisor
    anion_count = cation.charge_number // divisor
    result: dict[str, int] = {}
    for ion, coefficient in ((cation, cation_count), (anion, anion_count)):
        for element, count in ion.elemental_composition.items():
            result[element] = result.get(element, 0) + coefficient * count
    return {element: count for element, count in sorted(result.items()) if count}


def propose_wet_co2_neutral_solid_formulas(request: WetCo2NeutralSolidFormulaProposals) -> Calculation:
    """Return reduced integer charge-neutral binary composition proposals."""
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "proposal_set_id": request.proposal_set_id,
        "model_id": MODEL_ID,
        "input_sha256": input_sha256,
        "cation_ids": [row.species_id for row in request.cations],
        "anion_ids": [row.species_id for row in request.anions],
        "ion_formula_evidence": [
            {"species_id": row.species_id, "source_id": row.evidence.source_id,
             "source_record_id": row.source_record_id, "sha256": row.evidence.sha256,
             "license_id": row.evidence.license_id}
            for row in (*request.cations, *request.anions)
        ],
        "phase_stability_assessed": False,
        "equilibrium_constants_assigned": False,
        "precipitation_predicted": False,
        "manual_thermodynamic_and_phase_review_required": True,
    }
    reviews = {
        "ion_formula_and_charge_reviewed": request.ion_formula_and_charge_reviewed,
        "binary_formula_scope_reviewed": request.binary_formula_scope_reviewed,
        "proposal_only_manual_phase_review_required": request.proposal_only_manual_phase_review_required,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    grouped: dict[tuple[tuple[str, int], ...], dict] = {}
    for cation in request.cations:
        for anion in request.anions:
            divisor = math.gcd(cation.charge_number, abs(anion.charge_number))
            cation_coefficient = abs(anion.charge_number) // divisor
            anion_coefficient = cation.charge_number // divisor
            composition = _compose_formula(cation, anion)
            key = tuple(composition.items())
            record = grouped.setdefault(key, {
                "composition": composition,
                "charge_balanced_ion_pairs": [],
            })
            record["charge_balanced_ion_pairs"].append({
                "cation_species_id": cation.species_id,
                "cation_coefficient": cation_coefficient,
                "anion_species_id": anion.species_id,
                "anion_coefficient": anion_coefficient,
                "net_charge": cation_coefficient * cation.charge_number + anion_coefficient * anion.charge_number,
            })

    proposals = []
    for key in sorted(grouped):
        record = grouped[key]
        digest = canonical_digest({"composition": record["composition"]})
        proposals.append({
            "proposal_id": f"neutral-binary-formula:{digest[:24]}",
            "proposal_sha256": digest,
            "elemental_composition": record["composition"],
            "charge_balanced_ion_pairs": sorted(
                record["charge_balanced_ion_pairs"],
                key=lambda row: (row["cation_species_id"], row["anion_species_id"]),
            ),
        })
    return Calculation(status="computed", values=base | {
        "unique_formula_proposal_count": len(proposals),
        "formula_proposals": proposals,
        "enumeration_complete_within_declared_binary_ion_pairs": True,
    }, notes=(
        "The formula set is exhaustive only for the declared cation-anion pairs and reduced charge-neutral binary stoichiometry.",
        "No mineral identity, aqueous reaction, phase stability, solubility product, precipitation, morphology or corrosion response is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        WetCo2NeutralSolidFormulaProposals,
        propose_wet_co2_neutral_solid_formulas,
        {"formula_proposals[].elemental_composition": "mole_ratio_atoms"},
        (
            "For every caller-listed positive cation and negative anion, reduce integer stoichiometric coefficients to the smallest charge-neutral pair and sum declared elemental formulae.",
            "Deduplicate identical elemental compositions while retaining every generating ion pair.",
            "The output is a bounded formula proposal list and carries no thermodynamic, phase-existence or precipitation conclusion.",
        ),
        (SOURCE_ID, "caller_declared_aqueous_ion_formula_and_charge"),
        qualification="user_model",
    )]
