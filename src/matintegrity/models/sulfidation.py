"""Sulfidation exposure applicability without embedded rate or acceptance curves."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class SulfidationQualificationRecord(Contract):
    test_record_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_composition_condition_id: str = Field(min_length=1)
    sulfur_species_id: str = Field(min_length=1)
    sulfur_quantity_kind: Literal["activity", "concentration", "partial_pressure"]
    sulfur_quantity_value: Nonnegative
    sulfur_quantity_unit_token: str = Field(min_length=1)
    sulfur_quantity_basis: str = Field(min_length=1)
    temperature_K: Positive
    pressure_Pa_abs: Nonnegative
    flow_descriptor: str = Field(min_length=1)
    deposit_descriptor: str = Field(min_length=1)
    exposure_duration_s: Positive
    reported_observation: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @field_validator(
        "test_record_id",
        "source_group_id",
        "material_id",
        "material_composition_condition_id",
        "sulfur_species_id",
        "sulfur_quantity_unit_token",
        "sulfur_quantity_basis",
        "flow_descriptor",
        "deposit_descriptor",
        "reported_observation",
    )
    @classmethod
    def nonblank_record_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("sulfidation qualification record text fields cannot be blank")
        return value


class SulfidationApplicabilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_composition_condition_id: str = Field(min_length=1)
    sulfur_species_id: str = Field(min_length=1)
    sulfur_quantity_kind: Literal["activity", "concentration", "partial_pressure"]
    sulfur_quantity_min: Nonnegative
    sulfur_quantity_max: Nonnegative
    sulfur_quantity_unit_token: str = Field(min_length=1)
    sulfur_quantity_basis: str = Field(min_length=1)
    temperature_min_K: Positive
    temperature_max_K: Positive
    pressure_min_Pa_abs: Nonnegative
    pressure_max_Pa_abs: Nonnegative
    applicable_flow_descriptors: list[str] = Field(min_length=1)
    applicable_deposit_descriptors: list[str] = Field(min_length=1)
    exposure_duration_min_s: Nonnegative
    exposure_duration_max_s: Positive
    qualification_test_record_ids: list[str] = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @field_validator(
        "envelope_id",
        "material_id",
        "material_composition_condition_id",
        "sulfur_species_id",
        "sulfur_quantity_unit_token",
        "sulfur_quantity_basis",
        "applicability_basis",
    )
    @classmethod
    def nonblank_envelope_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("sulfidation envelope text fields cannot be blank")
        return value

    @field_validator("applicable_flow_descriptors", "applicable_deposit_descriptors")
    @classmethod
    def nonblank_unique_descriptors(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("sulfidation descriptors cannot be blank")
        return values

    @model_validator(mode="after")
    def ordered_ranges_and_unique_ids(self):
        ranges = (
            (self.sulfur_quantity_min, self.sulfur_quantity_max, "sulfur quantity"),
            (self.temperature_min_K, self.temperature_max_K, "temperature"),
            (self.pressure_min_Pa_abs, self.pressure_max_Pa_abs, "absolute pressure"),
            (self.exposure_duration_min_s, self.exposure_duration_max_s, "exposure duration"),
        )
        for lower, upper, label in ranges:
            if upper < lower:
                raise ValueError(f"sulfidation applicability {label} range must be ordered")
        for values in (
            self.applicable_flow_descriptors,
            self.applicable_deposit_descriptors,
            self.qualification_test_record_ids,
        ):
            if len(set(values)) != len(values):
                raise ValueError("sulfidation envelope identifier lists must be unique")
        return self


class SulfidationExposureApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_heat_or_lot_id: str = Field(min_length=1)
    material_composition_condition_id: str = Field(min_length=1)
    sulfur_species_id: str = Field(min_length=1)
    sulfur_quantity_kind: Literal["activity", "concentration", "partial_pressure"]
    sulfur_quantity_value: Nonnegative
    sulfur_quantity_unit_token: str = Field(min_length=1)
    sulfur_quantity_basis: str = Field(min_length=1)
    temperature_K: Positive
    pressure_Pa_abs: Nonnegative
    flow_descriptor: str = Field(min_length=1)
    deposit_descriptor: str = Field(min_length=1)
    exposure_duration_s: Positive
    qualification_test_records: list[SulfidationQualificationRecord] = Field(min_length=1)
    candidate_envelopes: list[SulfidationApplicabilityEnvelope] = Field(min_length=1)
    material_identity_and_composition_reviewed: bool
    sulfur_species_quantity_and_basis_reviewed: bool
    absolute_pressure_and_temperature_reviewed: bool
    flow_and_deposit_condition_reviewed: bool
    exposure_duration_reviewed: bool
    qualification_evidence_and_envelope_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_and_evidence_links(self):
        for value in (self.assessment_id, self.asset_id, self.location_id, self.material_heat_or_lot_id):
            if not value.strip():
                raise ValueError("sulfidation assessment identifiers cannot be blank")
        record_ids = [item.test_record_id for item in self.qualification_test_records]
        envelope_ids = [item.envelope_id for item in self.candidate_envelopes]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("sulfidation qualification test record IDs must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("sulfidation applicability envelope IDs must be unique")
        known_records = set(record_ids)
        for envelope in self.candidate_envelopes:
            if set(envelope.qualification_test_record_ids) - known_records:
                raise ValueError("every envelope qualification record must be supplied")
        return self


def _identity_checks(x: SulfidationExposureApplicability, envelope: SulfidationApplicabilityEnvelope) -> dict:
    return {
        "material_id": x.material_id == envelope.material_id,
        "material_composition_condition_id": (
            x.material_composition_condition_id == envelope.material_composition_condition_id
        ),
        "sulfur_species_id": x.sulfur_species_id == envelope.sulfur_species_id,
        "sulfur_quantity_kind": x.sulfur_quantity_kind == envelope.sulfur_quantity_kind,
        "sulfur_quantity_unit_token": (x.sulfur_quantity_unit_token == envelope.sulfur_quantity_unit_token),
        "sulfur_quantity_basis": x.sulfur_quantity_basis == envelope.sulfur_quantity_basis,
        "flow_descriptor": x.flow_descriptor in envelope.applicable_flow_descriptors,
        "deposit_descriptor": x.deposit_descriptor in envelope.applicable_deposit_descriptors,
    }


def _range_checks(x: SulfidationExposureApplicability, envelope: SulfidationApplicabilityEnvelope) -> dict:
    return {
        "sulfur_quantity_value": (
            envelope.sulfur_quantity_min <= x.sulfur_quantity_value <= envelope.sulfur_quantity_max
        ),
        "temperature_K": envelope.temperature_min_K <= x.temperature_K <= envelope.temperature_max_K,
        "pressure_Pa_abs": envelope.pressure_min_Pa_abs <= x.pressure_Pa_abs <= envelope.pressure_max_Pa_abs,
        "exposure_duration_s": (
            envelope.exposure_duration_min_s <= x.exposure_duration_s <= envelope.exposure_duration_max_s
        ),
    }


def _qualification_record_checks(
    envelope: SulfidationApplicabilityEnvelope,
    record: SulfidationQualificationRecord,
) -> dict:
    """Check that cited qualification records actually describe envelope support."""
    exact_fields = (
        "material_id",
        "material_composition_condition_id",
        "sulfur_species_id",
        "sulfur_quantity_kind",
        "sulfur_quantity_unit_token",
        "sulfur_quantity_basis",
    )
    checks = {name: getattr(record, name) == getattr(envelope, name) for name in exact_fields}
    checks.update(
        {
            "flow_descriptor": record.flow_descriptor in envelope.applicable_flow_descriptors,
            "deposit_descriptor": record.deposit_descriptor in envelope.applicable_deposit_descriptors,
            "sulfur_quantity_value": (
                envelope.sulfur_quantity_min <= record.sulfur_quantity_value <= envelope.sulfur_quantity_max
            ),
            "temperature_K": envelope.temperature_min_K <= record.temperature_K <= envelope.temperature_max_K,
            "pressure_Pa_abs": envelope.pressure_min_Pa_abs
            <= record.pressure_Pa_abs
            <= envelope.pressure_max_Pa_abs,
            "exposure_duration_s": (
                envelope.exposure_duration_min_s
                <= record.exposure_duration_s
                <= envelope.exposure_duration_max_s
            ),
        }
    )
    return checks


def sulfidation_exposure_applicability(x: SulfidationExposureApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_identity_and_composition_reviewed",
            "sulfur_species_quantity_and_basis_reviewed",
            "absolute_pressure_and_temperature_reviewed",
            "flow_and_deposit_condition_reviewed",
            "exposure_duration_reviewed",
            "qualification_evidence_and_envelope_reviewed",
        )
        if not getattr(x, name)
    ]
    diagnostics = []
    qualification_record_diagnostics = []
    identity_matches = []
    full_matches = []
    records_by_id = {item.test_record_id: item for item in x.qualification_test_records}
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
                "qualification_test_record_ids": envelope.qualification_test_record_ids,
            }
        )
        record_checks = {
            record_id: _qualification_record_checks(envelope, records_by_id[record_id])
            for record_id in envelope.qualification_test_record_ids
        }
        qualification_record_diagnostics.append(
            {
                "envelope_id": envelope.envelope_id,
                "qualification_records": {
                    record_id: {
                        "source_group_id": records_by_id[record_id].source_group_id,
                        "record_sha256": canonical_digest(records_by_id[record_id].model_dump(mode="json")),
                        "record_evidence": [
                            item.model_dump(mode="json") for item in records_by_id[record_id].evidence
                        ],
                        "reported_observation": records_by_id[record_id].reported_observation,
                        "checks": record_checks[record_id],
                    }
                    for record_id in record_checks
                },
                "all_records_within_declared_support": bool(record_checks)
                and all(all(checks.values()) for checks in record_checks.values()),
            }
        )
        if identity_ok:
            identity_matches.append(envelope.envelope_id)
        if identity_ok and range_ok:
            full_matches.append(envelope.envelope_id)
    qualified_envelopes = {
        item["envelope_id"]
        for item in qualification_record_diagnostics
        if item["all_records_within_declared_support"]
    }
    qualified_full_matches = [item for item in full_matches if item in qualified_envelopes]
    if missing_reviews or not identity_matches or len(qualified_full_matches) > 1:
        status = "needs_data"
    elif not qualified_full_matches:
        status = "out_of_scope"
    else:
        status = "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "material_id": x.material_id,
            "material_heat_or_lot_id": x.material_heat_or_lot_id,
            "sulfur_species_id": x.sulfur_species_id,
            "selected_envelope_id": qualified_full_matches[0] if len(qualified_full_matches) == 1 else None,
            "identity_matching_envelope_ids": identity_matches,
            "fully_matching_envelope_ids": full_matches,
            "candidate_diagnostics": diagnostics,
            "qualification_record_diagnostics": qualification_record_diagnostics,
            "qualification_records_supporting_envelope_ids": sorted(qualified_envelopes),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "A unique match establishes only inclusion in a caller-owned qualification envelope.",
            "No standard curve or table, metal-loss rate, scale kinetics, lifetime or acceptance rule is calculated.",
            "Sulfur quantity units and basis, flow condition and deposit condition are matched exactly without hidden conversion.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "degradation.sulfidation_exposure_applicability",
            SulfidationExposureApplicability,
            sulfidation_exposure_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "material_id": "1",
                "material_heat_or_lot_id": "1",
                "sulfur_species_id": "1",
                "selected_envelope_id": "1",
                "identity_matching_envelope_ids": "1",
                "fully_matching_envelope_ids": "1",
                "candidate_diagnostics": "mixed",
                "qualification_record_diagnostics": "mixed",
                "qualification_records_supporting_envelope_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Material condition, sulfur definition, units, flow and deposit descriptors require exact identity matching.",
                "Temperature, absolute pressure, sulfur quantity and duration are checked only against caller-declared ranges.",
                "Qualification test records are preserved as evidence links and are not converted into an empirical rate law.",
                "Every linked qualification record is checked against the cited envelope identities and declared support ranges.",
            ),
            ("declared_sulfidation_applicability_envelope",),
        )
    ]
