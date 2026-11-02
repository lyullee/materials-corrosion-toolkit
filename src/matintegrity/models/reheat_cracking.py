"""Reheat-cracking applicability against caller-owned qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ReheatThermalInterval(Contract):
    interval_id: str = Field(min_length=1)
    stage_kind: Literal["welding", "postweld_heat_treatment", "service_thermal_exposure"]
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_record(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("reheat thermal intervals must have positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("reheat thermal interval temperature bounds must be ordered")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid reheat thermal record requires a basis")
        return self


class ReheatQualificationObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["qualification", "holdout", "application"]
    region_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_state(self):
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting reheat-cracking evidence requires a basis")
        return self


class ReheatCrackingEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    weld_condition_id: str = Field(min_length=1)
    haz_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    heat_input_unit_token: str = Field(min_length=1)
    minimum_heat_input_value: Nonnegative
    maximum_heat_input_value: Nonnegative
    minimum_reheat_temperature_K: Positive
    maximum_reheat_temperature_K: Positive
    maximum_cumulative_reheat_duration_s: Positive
    stress_unit_token: str = Field(min_length=1)
    minimum_stress_value: float
    maximum_stress_value: float
    supported_stress_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_restraint_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_region_ids: tuple[str, ...] = Field(min_length=1)
    supported_method_ids: tuple[str, ...] = Field(min_length=1)
    minimum_qualification_source_group_count: int = Field(ge=1)
    qualification_observations: tuple[ReheatQualificationObservation, ...] = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_heat_input_value < self.minimum_heat_input_value:
            raise ValueError("heat-input support bounds must be ordered")
        if self.maximum_reheat_temperature_K < self.minimum_reheat_temperature_K:
            raise ValueError("reheat temperature support bounds must be ordered")
        if self.maximum_stress_value < self.minimum_stress_value:
            raise ValueError("reheat stress support bounds must be ordered")
        for values, label in (
            (self.supported_stress_descriptors, "stress descriptors"),
            (self.supported_restraint_descriptors, "restraint descriptors"),
            (self.supported_region_ids, "region identifiers"),
            (self.supported_method_ids, "method identifiers"),
            ([row.observation_id for row in self.qualification_observations], "observation identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"reheat {label} must be unique")
        return self


class ReheatCrackingApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    weld_condition_id: str = Field(min_length=1)
    haz_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    heat_input_value: Nonnegative
    heat_input_unit_token: str = Field(min_length=1)
    thermal_history: tuple[ReheatThermalInterval, ...] = Field(min_length=1)
    stress_descriptor: str = Field(min_length=1)
    stress_value: float
    stress_unit_token: str = Field(min_length=1)
    restraint_descriptor: str = Field(min_length=1)
    candidate_envelopes: tuple[ReheatCrackingEnvelope, ...] = Field(min_length=1)
    material_weld_and_haz_identity_reviewed: bool
    welding_process_and_heat_input_reviewed: bool
    heat_treatment_clock_and_temperature_reviewed: bool
    stress_and_restraint_basis_reviewed: bool
    specimen_region_and_source_groups_reviewed: bool
    observation_method_units_and_uncertainty_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_history(self):
        interval_ids = [row.interval_id for row in self.thermal_history]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(interval_ids) != len(set(interval_ids)):
            raise ValueError("reheat thermal interval identifiers must be unique")
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("reheat qualification envelope identifiers must be unique")
        for first, second in zip(self.thermal_history, self.thermal_history[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("reheat thermal intervals must be ordered and cannot overlap")
        return self


def _identity(x: ReheatCrackingApplicability) -> tuple[str, ...]:
    return (
        x.material_condition_id,
        x.weld_condition_id,
        x.haz_condition_id,
        x.welding_process_id,
    )


def _envelope_identity(x: ReheatCrackingEnvelope) -> tuple[str, ...]:
    return (
        x.material_condition_id,
        x.weld_condition_id,
        x.haz_condition_id,
        x.welding_process_id,
    )


def reheat_cracking_applicability(x: ReheatCrackingApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_weld_and_haz_identity_reviewed",
            "welding_process_and_heat_input_reviewed",
            "heat_treatment_clock_and_temperature_reviewed",
            "stress_and_restraint_basis_reviewed",
            "specimen_region_and_source_groups_reviewed",
            "observation_method_units_and_uncertainty_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_interval_ids = [row.interval_id for row in x.thermal_history if not row.record_valid]
    matches = [row for row in x.candidate_envelopes if _envelope_identity(row) == _identity(x)]
    if missing_reviews or invalid_interval_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_thermal_interval_ids": invalid_interval_ids,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Reviewed thermal history and caller-owned qualification evidence are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": [],
                "invalid_thermal_interval_ids": [],
                "identity_matching_envelope_ids": [],
            },
            notes=("No caller-declared envelope has the exact material, weld, HAZ and process identity.",),
        )

    envelope = matches[0]
    invalid_observation_ids = [
        row.observation_id
        for row in envelope.qualification_observations
        if not row.record_valid or not row.supports_declared_envelope
    ]
    unit_mismatch_fields = []
    if x.heat_input_unit_token != envelope.heat_input_unit_token:
        unit_mismatch_fields.append("heat_input_unit_token")
    if x.stress_unit_token != envelope.stress_unit_token:
        unit_mismatch_fields.append("stress_unit_token")
    if invalid_observation_ids or unit_mismatch_fields:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "envelope_id": envelope.envelope_id,
                "invalid_qualification_observation_ids": invalid_observation_ids,
                "unit_mismatch_fields": unit_mismatch_fields,
            },
            notes=("Exact units and valid caller qualification observations are required.",),
        )

    qualification_rows = [
        row for row in envelope.qualification_observations if row.partition == "qualification"
    ]
    source_group_count = len({row.source_group_id for row in qualification_rows})
    unsupported_observation_ids = [
        row.observation_id
        for row in qualification_rows
        if row.region_id not in envelope.supported_region_ids
        or row.method_id not in envelope.supported_method_ids
    ]
    reheat_intervals = [
        row
        for row in x.thermal_history
        if row.stage_kind in {"postweld_heat_treatment", "service_thermal_exposure"}
    ]
    cumulative_reheat_duration_s = sum(row.end_time_s - row.start_time_s for row in reheat_intervals)
    outside_thermal_interval_ids = [
        row.interval_id
        for row in reheat_intervals
        if row.minimum_temperature_K < envelope.minimum_reheat_temperature_K
        or row.maximum_temperature_K > envelope.maximum_reheat_temperature_K
    ]
    outside_support_reasons = []
    if not envelope.minimum_heat_input_value <= x.heat_input_value <= envelope.maximum_heat_input_value:
        outside_support_reasons.append("heat_input")
    if x.stress_descriptor not in envelope.supported_stress_descriptors:
        outside_support_reasons.append("stress_descriptor")
    if not envelope.minimum_stress_value <= x.stress_value <= envelope.maximum_stress_value:
        outside_support_reasons.append("stress_value")
    if x.restraint_descriptor not in envelope.supported_restraint_descriptors:
        outside_support_reasons.append("restraint_descriptor")
    if cumulative_reheat_duration_s > envelope.maximum_cumulative_reheat_duration_s:
        outside_support_reasons.append("cumulative_reheat_duration")
    if source_group_count < envelope.minimum_qualification_source_group_count:
        outside_support_reasons.append("qualification_source_group_count")
    if unsupported_observation_ids:
        outside_support_reasons.append("qualification_observation_support")
    if outside_thermal_interval_ids:
        outside_support_reasons.append("reheat_temperature_range")

    return Calculation(
        status="out_of_scope" if outside_support_reasons else "computed",
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id,
            "envelope_id": envelope.envelope_id,
            "cumulative_reheat_duration_s": cumulative_reheat_duration_s,
            "outside_thermal_interval_ids": outside_thermal_interval_ids,
            "qualification_source_group_count": source_group_count,
            "unsupported_qualification_observation_ids": unsupported_observation_ids,
            "outside_support_reasons": outside_support_reasons,
            "declared_applicability_outcome": (
                "outside_support" if outside_support_reasons else "within_support"
            ),
        },
        notes=(
            "The result compares reviewed records with a caller-owned qualification envelope.",
            "No susceptibility, crack initiation or growth, probability, life or acceptance criterion is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("reheat-cracking assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.reheat_cracking_applicability",
            ReheatCrackingApplicability,
            reheat_cracking_applicability,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "envelope_id": "1",
                "cumulative_reheat_duration_s": "s",
                "outside_thermal_interval_ids": "1",
                "qualification_source_group_count": "1",
                "unsupported_qualification_observation_ids": "1",
                "outside_support_reasons": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Material, weld, HAZ and welding-process identities are exact caller-reviewed tokens.",
                "Temperature, time, stress, restraint and heat-input support comes from caller-owned evidence.",
                "Qualification observations preserve specimen, source group, method, units, uncertainty and digests.",
            ),
            ("reviewed_reheat_cracking_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
