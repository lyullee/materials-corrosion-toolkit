"""Hydrogen-cracking provider evidence without fracture acceptance inference."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class HydrogenCrackingExposure(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    hydrogen_state_id: str = Field(min_length=1)
    pressure_or_fugacity_basis: str = Field(min_length=1)
    pressure_or_fugacity_value: Nonnegative
    pressure_or_fugacity_unit_token: str = Field(min_length=1)
    temperature_K: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("hydrogen-cracking exposure intervals must have positive duration")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid hydrogen exposure requires a basis")
        return self


class HydrogenToughnessResult(Contract):
    result_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout", "application"]
    endpoint_kind: Literal["K", "J", "CTOD", "user_defined"]
    endpoint_definition_id: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_result(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid hydrogen toughness result requires a basis")
        return self


class HydrogenCrackDrivingResult(Contract):
    result_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    metric_kind: Literal["K", "J", "CTOD", "user_defined"]
    metric_definition_id: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_result(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid crack-driving result requires a basis")
        return self


class HydrogenCrackingQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    supported_toughness_endpoint_definition_ids: tuple[str, ...] = Field(min_length=1)
    supported_driving_metric_definition_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_evidence(self):
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting hydrogen-cracking evidence requires a basis")
        return self


class HydrogenCrackingEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    hydrogen_state_id: str = Field(min_length=1)
    pressure_or_fugacity_basis: str = Field(min_length=1)
    pressure_or_fugacity_unit_token: str = Field(min_length=1)
    minimum_pressure_or_fugacity_value: Nonnegative
    maximum_pressure_or_fugacity_value: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    maximum_cumulative_exposure_s: Positive
    supported_crack_geometry_ids: tuple[str, ...] = Field(min_length=1)
    supported_crack_location_ids: tuple[str, ...] = Field(min_length=1)
    supported_crack_orientation_ids: tuple[str, ...] = Field(min_length=1)
    toughness_endpoint_kind: Literal["K", "J", "CTOD", "user_defined"]
    toughness_endpoint_definition_id: str = Field(min_length=1)
    toughness_unit_token: str = Field(min_length=1)
    minimum_supported_toughness_value: float
    maximum_supported_toughness_value: float
    maximum_toughness_expanded_uncertainty: Nonnegative
    toughness_provider_id: str = Field(min_length=1)
    toughness_provider_revision: str = Field(min_length=1)
    toughness_provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    driving_metric_kind: Literal["K", "J", "CTOD", "user_defined"]
    driving_metric_definition_id: str = Field(min_length=1)
    driving_unit_token: str = Field(min_length=1)
    minimum_supported_driving_value: float
    maximum_supported_driving_value: float
    maximum_driving_expanded_uncertainty: Nonnegative
    driving_provider_id: str = Field(min_length=1)
    driving_provider_revision: str = Field(min_length=1)
    driving_provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_evidence: tuple[HydrogenCrackingQualificationEvidence, ...] = Field(min_length=2)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_independent_support(self):
        for minimum, maximum, label in (
            (
                self.minimum_pressure_or_fugacity_value,
                self.maximum_pressure_or_fugacity_value,
                "pressure or fugacity",
            ),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (
                self.minimum_supported_toughness_value,
                self.maximum_supported_toughness_value,
                "toughness",
            ),
            (
                self.minimum_supported_driving_value,
                self.maximum_supported_driving_value,
                "driving metric",
            ),
        ):
            if maximum < minimum:
                raise ValueError(f"hydrogen-cracking {label} support bounds must be ordered")
        for values, label in (
            (self.supported_crack_geometry_ids, "crack geometry identifiers"),
            (self.supported_crack_location_ids, "crack location identifiers"),
            (self.supported_crack_orientation_ids, "crack orientation identifiers"),
            ([row.evidence_record_id for row in self.qualification_evidence], "evidence identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"hydrogen-cracking {label} must be unique")
        partitions = {row.partition for row in self.qualification_evidence}
        if partitions != {"calibration", "holdout"}:
            raise ValueError("hydrogen-cracking qualification requires calibration and holdout evidence")
        calibration = {
            row.source_group_id for row in self.qualification_evidence if row.partition == "calibration"
        }
        holdout = {row.source_group_id for row in self.qualification_evidence if row.partition == "holdout"}
        if calibration & holdout:
            raise ValueError("hydrogen-cracking calibration and holdout source groups must be disjoint")
        return self


class HydrogenCrackingProviderEvidence(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    crack_geometry_id: str = Field(min_length=1)
    crack_location_id: str = Field(min_length=1)
    crack_orientation_id: str = Field(min_length=1)
    exposure_intervals: tuple[HydrogenCrackingExposure, ...] = Field(min_length=1)
    toughness_result: HydrogenToughnessResult
    crack_driving_result: HydrogenCrackDrivingResult
    candidate_envelopes: tuple[HydrogenCrackingEnvelope, ...] = Field(min_length=1)
    material_condition_and_heat_reviewed: bool
    hydrogen_state_pressure_or_fugacity_basis_reviewed: bool
    temperature_exposure_clock_reviewed: bool
    crack_geometry_location_and_orientation_reviewed: bool
    toughness_endpoint_units_uncertainty_and_provider_reviewed: bool
    driving_metric_load_case_units_and_provider_reviewed: bool
    physical_specimens_source_groups_and_partitions_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_records(self):
        interval_ids = [row.interval_id for row in self.exposure_intervals]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(interval_ids) != len(set(interval_ids)):
            raise ValueError("hydrogen-cracking exposure interval identifiers must be unique")
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("hydrogen-cracking envelope identifiers must be unique")
        for first, second in zip(self.exposure_intervals, self.exposure_intervals[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("hydrogen-cracking exposure intervals must be ordered and cannot overlap")
        return self


def _identity(x: HydrogenCrackingProviderEvidence) -> tuple[str, str]:
    return x.material_condition_id, x.heat_id


def _envelope_identity(x: HydrogenCrackingEnvelope) -> tuple[str, str]:
    return x.material_condition_id, x.heat_id


def hydrogen_cracking_provider_evidence(x: HydrogenCrackingProviderEvidence) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_condition_and_heat_reviewed",
            "hydrogen_state_pressure_or_fugacity_basis_reviewed",
            "temperature_exposure_clock_reviewed",
            "crack_geometry_location_and_orientation_reviewed",
            "toughness_endpoint_units_uncertainty_and_provider_reviewed",
            "driving_metric_load_case_units_and_provider_reviewed",
            "physical_specimens_source_groups_and_partitions_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_exposure_ids = [row.interval_id for row in x.exposure_intervals if not row.record_valid]
    invalid_result_ids = [
        row.result_id for row in (x.toughness_result, x.crack_driving_result) if not row.record_valid
    ]
    matches = [row for row in x.candidate_envelopes if _envelope_identity(row) == _identity(x)]
    if missing_reviews or invalid_exposure_ids or invalid_result_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_exposure_ids": invalid_exposure_ids,
                "invalid_result_ids": invalid_result_ids,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Reviewed hydrogen exposure, toughness and crack-driving records are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller envelope has the exact material-condition and heat identity.",),
        )

    envelope = matches[0]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    exposure_identity_or_unit_mismatch_ids = [
        row.interval_id
        for row in x.exposure_intervals
        if row.hydrogen_state_id != envelope.hydrogen_state_id
        or row.pressure_or_fugacity_basis != envelope.pressure_or_fugacity_basis
        or row.pressure_or_fugacity_unit_token != envelope.pressure_or_fugacity_unit_token
    ]
    toughness = x.toughness_result
    toughness_compatible = (
        toughness.endpoint_kind == envelope.toughness_endpoint_kind
        and toughness.endpoint_definition_id == envelope.toughness_endpoint_definition_id
        and toughness.unit_token == envelope.toughness_unit_token
        and toughness.provider_id == envelope.toughness_provider_id
        and toughness.provider_revision == envelope.toughness_provider_revision
        and toughness.provider_state_digest == envelope.toughness_provider_state_digest
    )
    driving = x.crack_driving_result
    driving_compatible = (
        driving.metric_kind == envelope.driving_metric_kind
        and driving.metric_definition_id == envelope.driving_metric_definition_id
        and driving.unit_token == envelope.driving_unit_token
        and driving.provider_id == envelope.driving_provider_id
        and driving.provider_revision == envelope.driving_provider_revision
        and driving.provider_configuration_digest == envelope.driving_provider_configuration_digest
    )
    if (
        invalid_evidence_ids
        or exposure_identity_or_unit_mismatch_ids
        or not toughness_compatible
        or not driving_compatible
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "envelope_id": envelope.envelope_id,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "exposure_identity_or_unit_mismatch_ids": exposure_identity_or_unit_mismatch_ids,
                "toughness_endpoint_and_provider_compatible": toughness_compatible,
                "driving_metric_and_provider_compatible": driving_compatible,
            },
            notes=(
                "Toughness endpoints and crack-driving metrics require exact, separate definitions and units.",
            ),
        )

    cumulative_exposure_s = sum(row.end_time_s - row.start_time_s for row in x.exposure_intervals)
    outside_exposure_ids = [
        row.interval_id
        for row in x.exposure_intervals
        if not envelope.minimum_pressure_or_fugacity_value
        <= row.pressure_or_fugacity_value
        <= envelope.maximum_pressure_or_fugacity_value
        or not envelope.minimum_temperature_K <= row.temperature_K <= envelope.maximum_temperature_K
    ]
    toughness_within = (
        envelope.minimum_supported_toughness_value
        <= toughness.reported_value
        <= envelope.maximum_supported_toughness_value
        and toughness.expanded_uncertainty <= envelope.maximum_toughness_expanded_uncertainty
    )
    driving_within = (
        envelope.minimum_supported_driving_value
        <= driving.reported_value
        <= envelope.maximum_supported_driving_value
        and driving.expanded_uncertainty <= envelope.maximum_driving_expanded_uncertainty
    )
    qualified_toughness_ids = {
        identifier
        for row in envelope.qualification_evidence
        for identifier in row.supported_toughness_endpoint_definition_ids
    }
    qualified_driving_ids = {
        identifier
        for row in envelope.qualification_evidence
        for identifier in row.supported_driving_metric_definition_ids
    }
    outside_support_reasons = []
    if x.crack_geometry_id not in envelope.supported_crack_geometry_ids:
        outside_support_reasons.append("crack_geometry_id")
    if x.crack_location_id not in envelope.supported_crack_location_ids:
        outside_support_reasons.append("crack_location_id")
    if x.crack_orientation_id not in envelope.supported_crack_orientation_ids:
        outside_support_reasons.append("crack_orientation_id")
    if outside_exposure_ids:
        outside_support_reasons.append("hydrogen_exposure_range")
    if cumulative_exposure_s > envelope.maximum_cumulative_exposure_s:
        outside_support_reasons.append("cumulative_exposure")
    if not toughness_within:
        outside_support_reasons.append("toughness_result_range_or_uncertainty")
    if not driving_within:
        outside_support_reasons.append("driving_result_range_or_uncertainty")
    if envelope.toughness_endpoint_definition_id not in qualified_toughness_ids:
        outside_support_reasons.append("toughness_qualification_coverage")
    if envelope.driving_metric_definition_id not in qualified_driving_ids:
        outside_support_reasons.append("driving_qualification_coverage")
    return Calculation(
        status="out_of_scope" if outside_support_reasons else "computed",
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id,
            "envelope_id": envelope.envelope_id,
            "cumulative_exposure_s": cumulative_exposure_s,
            "outside_exposure_ids": outside_exposure_ids,
            "toughness_result_within_declared_support": toughness_within,
            "driving_result_within_declared_support": driving_within,
            "outside_support_reasons": outside_support_reasons,
            "declared_applicability_outcome": (
                "outside_support" if outside_support_reasons else "within_support"
            ),
        },
        notes=(
            "Toughness and crack-driving endpoints remain separate provider results; no comparison is an acceptance test.",
            "No fracture acceptance, initiation, growth, remaining life or probability is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("hydrogen-cracking assessment asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.hydrogen_cracking_provider_evidence",
            HydrogenCrackingProviderEvidence,
            hydrogen_cracking_provider_evidence,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "envelope_id": "1",
                "cumulative_exposure_s": "s",
                "outside_exposure_ids": "1",
                "toughness_result_within_declared_support": "1",
                "driving_result_within_declared_support": "1",
                "outside_support_reasons": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Pressure or fugacity basis and unit are exact caller-reviewed tokens and are never interchanged.",
                "Toughness and crack-driving endpoints retain separate definitions, units and provider identities.",
                "Calibration and holdout evidence retain disjoint physical source groups.",
            ),
            ("reviewed_hydrogen_cracking_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
