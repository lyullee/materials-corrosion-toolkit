"""Sour-service applicability matching without embedded damage or acceptance rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class SourEnvironmentTestRecord(Contract):
    test_record_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_grade_id: str = Field(min_length=1)
    material_heat_id: str = Field(min_length=1)
    microstructure_id: str = Field(min_length=1)
    hardness_value: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    h2s_partial_pressure_Pa_abs: Nonnegative
    h2s_partial_pressure_basis: str = Field(min_length=1)
    pH: float = Field(ge=0, le=14)
    temperature_K: Positive
    chloride_concentration: Nonnegative
    chloride_unit_token: str = Field(min_length=1)
    exposure_duration_s: Positive
    stress_state_descriptor: str = Field(min_length=1)
    reported_outcome: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class SourApplicabilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_grade_id: str = Field(min_length=1)
    heat_applicability: Literal["exact_heats", "all_heats_of_grade"]
    applicable_heat_ids: list[str] = Field(default_factory=list)
    applicable_microstructure_ids: list[str] = Field(min_length=1)
    hardness_min: Nonnegative
    hardness_max: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    h2s_partial_pressure_min_Pa_abs: Nonnegative
    h2s_partial_pressure_max_Pa_abs: Nonnegative
    h2s_partial_pressure_basis: str = Field(min_length=1)
    pH_min: float = Field(ge=0, le=14)
    pH_max: float = Field(ge=0, le=14)
    temperature_min_K: Positive
    temperature_max_K: Positive
    chloride_min: Nonnegative
    chloride_max: Nonnegative
    chloride_unit_token: str = Field(min_length=1)
    exposure_duration_min_s: Nonnegative
    exposure_duration_max_s: Positive
    applicable_stress_state_descriptors: list[str] = Field(min_length=1)
    qualification_test_record_ids: list[str] = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges(self):
        ranges = (
            (self.hardness_min, self.hardness_max, "hardness"),
            (
                self.h2s_partial_pressure_min_Pa_abs,
                self.h2s_partial_pressure_max_Pa_abs,
                "H2S partial pressure",
            ),
            (self.pH_min, self.pH_max, "pH"),
            (self.temperature_min_K, self.temperature_max_K, "temperature"),
            (self.chloride_min, self.chloride_max, "chloride"),
            (self.exposure_duration_min_s, self.exposure_duration_max_s, "exposure duration"),
        )
        for lower, upper, label in ranges:
            if upper < lower:
                raise ValueError(f"sour applicability {label} range must be ordered")
        if self.heat_applicability == "exact_heats" and not self.applicable_heat_ids:
            raise ValueError("exact-heat applicability requires at least one heat ID")
        if self.heat_applicability == "all_heats_of_grade" and self.applicable_heat_ids:
            raise ValueError("grade-level heat applicability cannot also list exact heats")
        for identifiers in (
            self.applicable_heat_ids,
            self.applicable_microstructure_ids,
            self.applicable_stress_state_descriptors,
            self.qualification_test_record_ids,
        ):
            if len(set(identifiers)) != len(identifiers):
                raise ValueError("sour applicability envelope identifier lists must be unique")
        return self


class SourEnvironmentApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_grade_id: str = Field(min_length=1)
    material_heat_id: str = Field(min_length=1)
    microstructure_id: str = Field(min_length=1)
    hardness_value: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    h2s_partial_pressure_Pa_abs: Nonnegative
    h2s_partial_pressure_basis: str = Field(min_length=1)
    pH: float = Field(ge=0, le=14)
    temperature_K: Positive
    chloride_concentration: Nonnegative
    chloride_unit_token: str = Field(min_length=1)
    exposure_duration_s: Positive
    stress_state_descriptor: str = Field(min_length=1)
    test_records: list[SourEnvironmentTestRecord] = Field(min_length=2)
    candidate_envelopes: list[SourApplicabilityEnvelope] = Field(min_length=1)
    material_identity_and_hardness_reviewed: bool
    media_composition_and_pH_reviewed: bool
    absolute_partial_pressure_reviewed: bool
    temperature_and_exposure_reviewed: bool
    stress_state_reviewed: bool
    test_partition_independence_reviewed: bool
    envelope_authority_reviewed: bool
    heat_transfer_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def records_envelopes_and_partitions(self):
        record_ids = [item.test_record_id for item in self.test_records]
        envelope_ids = [item.envelope_id for item in self.candidate_envelopes]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("sour test record IDs must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("sour applicability envelope IDs must be unique")
        if {item.partition for item in self.test_records} != {"calibration", "holdout"}:
            raise ValueError("both calibration and holdout sour test partitions are required")
        partitions_by_group = defaultdict(set)
        for item in self.test_records:
            partitions_by_group[item.source_group_id].add(item.partition)
        leaking = sorted(group for group, values in partitions_by_group.items() if len(values) > 1)
        if leaking:
            raise ValueError(f"source groups cannot cross sour test partitions: {leaking}")
        records = {item.test_record_id: item for item in self.test_records}
        for envelope in self.candidate_envelopes:
            unknown = set(envelope.qualification_test_record_ids) - records.keys()
            if unknown:
                raise ValueError("each envelope qualification record must be supplied")
            if any(
                records[item].partition != "calibration" for item in envelope.qualification_test_record_ids
            ):
                raise ValueError("only calibration records may define a sour applicability envelope")
        return self


def _identity_checks(x: SourEnvironmentApplicability, envelope: SourApplicabilityEnvelope) -> dict:
    heat_match = (
        x.material_heat_id in envelope.applicable_heat_ids
        if envelope.heat_applicability == "exact_heats"
        else True
    )
    return {
        "material_grade_id": x.material_grade_id == envelope.material_grade_id,
        "material_heat_id": heat_match,
        "microstructure_id": x.microstructure_id in envelope.applicable_microstructure_ids,
        "hardness_unit_token": x.hardness_unit_token == envelope.hardness_unit_token,
        "h2s_partial_pressure_basis": (x.h2s_partial_pressure_basis == envelope.h2s_partial_pressure_basis),
        "chloride_unit_token": x.chloride_unit_token == envelope.chloride_unit_token,
        "stress_state_descriptor": (
            x.stress_state_descriptor in envelope.applicable_stress_state_descriptors
        ),
    }


def _range_checks(x: SourEnvironmentApplicability, envelope: SourApplicabilityEnvelope) -> dict:
    return {
        "hardness": envelope.hardness_min <= x.hardness_value <= envelope.hardness_max,
        "h2s_partial_pressure_Pa_abs": (
            envelope.h2s_partial_pressure_min_Pa_abs
            <= x.h2s_partial_pressure_Pa_abs
            <= envelope.h2s_partial_pressure_max_Pa_abs
        ),
        "pH": envelope.pH_min <= x.pH <= envelope.pH_max,
        "temperature_K": envelope.temperature_min_K <= x.temperature_K <= envelope.temperature_max_K,
        "chloride_concentration": (
            envelope.chloride_min <= x.chloride_concentration <= envelope.chloride_max
        ),
        "exposure_duration_s": (
            envelope.exposure_duration_min_s <= x.exposure_duration_s <= envelope.exposure_duration_max_s
        ),
    }


def sour_environment_applicability(x: SourEnvironmentApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_identity_and_hardness_reviewed",
            "media_composition_and_pH_reviewed",
            "absolute_partial_pressure_reviewed",
            "temperature_and_exposure_reviewed",
            "stress_state_reviewed",
            "test_partition_independence_reviewed",
            "envelope_authority_reviewed",
            "heat_transfer_reviewed",
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
                "qualification_test_record_ids": envelope.qualification_test_record_ids,
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
            "material_grade_id": x.material_grade_id,
            "material_heat_id": x.material_heat_id,
            "selected_envelope_id": selected,
            "identity_matching_envelope_ids": identity_matches,
            "fully_matching_envelope_ids": full_matches,
            "test_record_count_by_partition": {
                partition: sum(item.partition == partition for item in x.test_records)
                for partition in ("calibration", "holdout")
            },
            "candidate_diagnostics": diagnostics,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "A unique match establishes only that the declared point lies within a caller-owned test applicability envelope.",
            "No standard threshold, SSC/HIC occurrence rate, crack growth, lifetime or acceptance rule is calculated.",
            "Holdout records remain separate and are not used to define candidate envelope ranges.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "degradation.sour_environment_applicability",
            SourEnvironmentApplicability,
            sour_environment_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "material_grade_id": "1",
                "material_heat_id": "1",
                "selected_envelope_id": "1",
                "identity_matching_envelope_ids": "1",
                "fully_matching_envelope_ids": "1",
                "test_record_count_by_partition": "1",
                "candidate_diagnostics": "mixed",
                "missing_reviews": "1",
            },
            (
                "Material, units, H2S partial-pressure definition and stress-state descriptors use exact matching.",
                "Numerical service conditions are compared only with caller-qualified ranges.",
                "Only calibration-partition records may be cited as defining an envelope.",
            ),
            ("declared_sour_environment_applicability_envelope",),
        )
    ]
