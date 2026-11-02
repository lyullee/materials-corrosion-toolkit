"""Derive the Papadopoulos P1 hydrostatic coefficient from matched endurance limits."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec


class PapadopoulosP1Calibration(Contract):
    calibration_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    fully_reversed_axial_limit_Pa: Positive
    axial_source_id: str = Field(min_length=1)
    axial_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    axial_evidence: Evidence
    fully_reversed_torsional_limit_Pa: Positive
    torsion_source_id: str = Field(min_length=1)
    torsion_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    torsion_evidence: Evidence
    matched_material_and_condition_reviewed: bool
    fully_reversed_ratio_minus_one_reviewed: bool
    smooth_specimen_endurance_limit_basis_reviewed: bool
    calibration_method_and_use_reviewed: bool

    @model_validator(mode="after")
    def check_evidence(self):
        if self.axial_evidence.source_id != self.axial_source_id or self.axial_evidence.sha256 != self.axial_source_sha256:
            raise ValueError("axial Evidence must match its declared source and digest")
        if self.torsion_evidence.source_id != self.torsion_source_id or self.torsion_evidence.sha256 != self.torsion_source_sha256:
            raise ValueError("torsion Evidence must match its declared source and digest")
        return self


def derive_papadopoulos_p1_calibration(request: PapadopoulosP1Calibration) -> Calculation:
    """Calculate a_C = 3*tau_-1/sigma_-1 - sqrt(3) within declared support."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "calibration_id": request.calibration_id,
        "material_condition_id": request.material_condition_id,
        "axial_source_id": request.axial_source_id,
        "axial_source_sha256": request.axial_source_sha256,
        "torsion_source_id": request.torsion_source_id,
        "torsion_source_sha256": request.torsion_source_sha256,
        "input_sha256": digest,
        "formula_id": "papadopoulos_p1_aC=3_tau_minus1_over_sigma_minus1_minus_sqrt3",
        "fully_reversed_torsional_limit_Pa": request.fully_reversed_torsional_limit_Pa,
    }
    if not all((
        request.matched_material_and_condition_reviewed,
        request.fully_reversed_ratio_minus_one_reviewed,
        request.smooth_specimen_endurance_limit_basis_reviewed,
        request.calibration_method_and_use_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "matched_fully_reversed_smooth_specimen_and_method_reviews_required",
            "hydrostatic_coefficient": None,
        })
    ratio = request.fully_reversed_torsional_limit_Pa / request.fully_reversed_axial_limit_Pa
    coefficient = 3.0 * ratio - math.sqrt(3.0)
    if not math.isfinite(ratio) or not math.isfinite(coefficient):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "finite_endurance_limits_produce_nonfinite_coefficient",
            "hydrostatic_coefficient": None,
            "endurance_limit_ratio_torsion_over_axial": None,
        })
    if coefficient < 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "derived_coefficient_is_negative_outside_nonnegative_P1_screen_contract",
            "hydrostatic_coefficient": coefficient,
            "endurance_limit_ratio_torsion_over_axial": ratio,
            "minimum_ratio_for_nonnegative_coefficient": 1.0 / math.sqrt(3.0),
        })
    return Calculation(values=base | {
        "status": "computed",
        "hydrostatic_coefficient": coefficient,
        "endurance_limit_ratio_torsion_over_axial": ratio,
        "axial_limit_basis_Pa": request.fully_reversed_axial_limit_Pa,
        "coefficient_unit": "1",
        "use_handoff": {
            "hydrostatic_coefficient": coefficient,
            "fully_reversed_torsional_fatigue_limit_Pa": request.fully_reversed_torsional_limit_Pa,
            "calibration_id": request.calibration_id,
            "calibration_sha256": digest,
        },
        "limitations": [
            "Requires smooth-specimen, same-condition fully reversed axial and torsion endurance limits per the declared method basis.",
            "The computed parameter is a calibration input for a P1 limit screen, not a direct fatigue-life or damage result.",
            "Do not transfer endurance limits across heat treatment, surface, environment, temperature, geometry basis or stress-ratio definitions without independent justification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.papadopoulos_p1_calibration",
        PapadopoulosP1Calibration,
        derive_papadopoulos_p1_calibration,
        {"hydrostatic_coefficient": "1", "fully_reversed_torsional_limit_Pa": "Pa"},
        (
            "Uses caller-supplied fully reversed axial and torsional endurance limits from a matched material condition and smooth-specimen basis.",
            "Derives only the P1 hydrostatic coefficient; it does not assess multiaxial history or fatigue life.",
            "Negative derived coefficients are outside the paired nonnegative P1 finite-screen contract and are reported out of scope.",
        ),
        ("papadopoulos_1995_p1_endurance_limit_parameter_relation", "papadopoulos_long_life_multiaxial_2001"),
        qualification="user_model",
    )]
