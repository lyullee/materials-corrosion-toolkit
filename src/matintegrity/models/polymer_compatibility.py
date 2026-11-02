"""Match polymer service conditions to caller-qualified compatibility envelopes."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PolymerCompatibilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    polymer_grade_id: str = Field(min_length=1)
    polymer_condition_id: str = Field(min_length=1)
    lot_applicability: Literal["exact_lots", "all_lots_of_grade"]
    applicable_lot_ids: list[str] = Field(default_factory=list)
    media_id: str = Field(min_length=1)
    concentration_min: Nonnegative
    concentration_max: Nonnegative
    concentration_unit_token: str = Field(min_length=1)
    temperature_min_K: Positive
    temperature_max_K: Positive
    pressure_min_Pa_abs: Nonnegative
    pressure_max_Pa_abs: Positive
    maximum_exposure_duration_s: Positive
    applicable_mechanical_loading_descriptors: list[str] = Field(min_length=1)
    qualification_source_id: str = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges_and_lots(self):
        if self.concentration_max < self.concentration_min:
            raise ValueError("compatibility concentration range must be ordered")
        if self.temperature_max_K < self.temperature_min_K:
            raise ValueError("compatibility temperature range must be ordered")
        if self.pressure_max_Pa_abs < self.pressure_min_Pa_abs:
            raise ValueError("compatibility absolute-pressure range must be ordered")
        if self.lot_applicability == "exact_lots" and not self.applicable_lot_ids:
            raise ValueError("exact-lot applicability requires at least one lot ID")
        if self.lot_applicability == "all_lots_of_grade" and self.applicable_lot_ids:
            raise ValueError("grade-level lot applicability cannot also list exact lots")
        if len(set(self.applicable_lot_ids)) != len(self.applicable_lot_ids):
            raise ValueError("applicable polymer lot IDs must be unique")
        if len(set(self.applicable_mechanical_loading_descriptors)) != len(
            self.applicable_mechanical_loading_descriptors
        ):
            raise ValueError("mechanical loading descriptors must be unique")
        return self


class PolymerCompatibilityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    polymer_grade_id: str = Field(min_length=1)
    polymer_lot_id: str = Field(min_length=1)
    polymer_condition_id: str = Field(min_length=1)
    media_id: str = Field(min_length=1)
    media_composition_description: str = Field(min_length=1)
    concentration: Nonnegative
    concentration_unit_token: str = Field(min_length=1)
    temperature_K: Positive
    pressure_Pa_abs: Nonnegative
    exposure_duration_s: Positive
    mechanical_loading_descriptor: str = Field(min_length=1)
    candidate_envelopes: list[PolymerCompatibilityEnvelope] = Field(min_length=1)
    material_identity_reviewed: bool
    media_identity_and_concentration_reviewed: bool
    temperature_pressure_duration_reviewed: bool
    mechanical_loading_reviewed: bool
    envelope_authority_reviewed: bool
    lot_transfer_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_envelopes(self):
        identifiers = [item.envelope_id for item in self.candidate_envelopes]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("polymer compatibility envelope IDs must be unique")
        return self


def _identity_checks(x: PolymerCompatibilityAssessment, envelope: PolymerCompatibilityEnvelope) -> dict:
    lot_matches = (
        x.polymer_lot_id in envelope.applicable_lot_ids
        if envelope.lot_applicability == "exact_lots"
        else True
    )
    return {
        "polymer_grade_id": x.polymer_grade_id == envelope.polymer_grade_id,
        "polymer_condition_id": x.polymer_condition_id == envelope.polymer_condition_id,
        "polymer_lot_id": lot_matches,
        "media_id": x.media_id == envelope.media_id,
        "concentration_unit_token": (x.concentration_unit_token == envelope.concentration_unit_token),
        "mechanical_loading_descriptor": (
            x.mechanical_loading_descriptor in envelope.applicable_mechanical_loading_descriptors
        ),
    }


def _range_checks(x: PolymerCompatibilityAssessment, envelope: PolymerCompatibilityEnvelope) -> dict:
    return {
        "concentration": envelope.concentration_min <= x.concentration <= envelope.concentration_max,
        "temperature_K": envelope.temperature_min_K <= x.temperature_K <= envelope.temperature_max_K,
        "pressure_Pa_abs": envelope.pressure_min_Pa_abs <= x.pressure_Pa_abs <= envelope.pressure_max_Pa_abs,
        "exposure_duration_s": x.exposure_duration_s <= envelope.maximum_exposure_duration_s,
    }


def polymer_compatibility_envelope_match(x: PolymerCompatibilityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_identity_reviewed",
            "media_identity_and_concentration_reviewed",
            "temperature_pressure_duration_reviewed",
            "mechanical_loading_reviewed",
            "envelope_authority_reviewed",
            "lot_transfer_reviewed",
        )
        if not getattr(x, name)
    ]
    diagnostics = []
    identity_matches = []
    full_matches = []
    for envelope in x.candidate_envelopes:
        identity = _identity_checks(x, envelope)
        ranges = _range_checks(x, envelope)
        identity_ok = all(identity.values())
        range_ok = all(ranges.values())
        diagnostics.append(
            {
                "envelope_id": envelope.envelope_id,
                "identity_checks": identity,
                "range_checks": ranges,
                "identity_match": identity_ok,
                "within_declared_ranges": range_ok,
            }
        )
        if identity_ok:
            identity_matches.append(envelope.envelope_id)
        if identity_ok and range_ok:
            full_matches.append(envelope.envelope_id)

    selected = full_matches[0] if len(full_matches) == 1 else None
    if missing_reviews or not identity_matches or len(full_matches) > 1:
        status = "needs_data"
    elif not full_matches:
        status = "out_of_scope"
    else:
        status = "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "polymer_grade_id": x.polymer_grade_id,
            "polymer_lot_id": x.polymer_lot_id,
            "polymer_condition_id": x.polymer_condition_id,
            "media_id": x.media_id,
            "selected_envelope_id": selected,
            "identity_matching_envelope_ids": identity_matches,
            "fully_matching_envelope_ids": full_matches,
            "candidate_diagnostics": diagnostics,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "A unique match means only that the declared service point lies inside a caller-qualified envelope.",
            "This model does not predict swelling, permeation, degradation rate, lifetime or chemical-mixture interaction.",
            "The result is not a material-selection, design-code or service-acceptance decision.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.polymer_compatibility_envelope_match",
            PolymerCompatibilityAssessment,
            polymer_compatibility_envelope_match,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "polymer_grade_id": "1",
                "polymer_lot_id": "1",
                "polymer_condition_id": "1",
                "media_id": "1",
                "selected_envelope_id": "1",
                "identity_matching_envelope_ids": "1",
                "fully_matching_envelope_ids": "1",
                "candidate_diagnostics": "mixed",
                "missing_reviews": "1",
            },
            (
                "Material, media, unit and loading identifiers are compared exactly without aliases or hidden conversions.",
                "Temperature, absolute pressure, concentration and exposure duration are checked only against caller-qualified ranges.",
                "Grade-level transfer across lots requires an explicit reviewed declaration.",
            ),
            ("declared_polymer_compatibility_envelope",),
        )
    ]
