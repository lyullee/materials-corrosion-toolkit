"""Gasket joint assembly, seating and relaxation evidence."""

from __future__ import annotations

from statistics import fmean, pstdev

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class BoltPreloadRecord(Contract):
    bolt_id: str = Field(min_length=1)
    preload_value: Positive
    preload_unit_token: str = Field(min_length=1)
    measurement_method_id: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_record_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid bolt-preload record requires a basis")
        return self


class GasketSeatingProviderResult(Contract):
    result_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_result_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid seating-provider result requires a basis")
        return self


class JointRelaxationObservation(Contract):
    observation_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_observation_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid joint-relaxation observation requires a basis")
        return self


class GasketMetricSupport(Contract):
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float
    maximum_supported_expanded_uncertainty: Nonnegative
    minimum_record_count: int = Field(ge=1)
    support_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("gasket metric support must be ordered")
        return self


class GasketQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: str = Field(min_length=1)
    supported_metric_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def limiting_basis(self):
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting gasket qualification evidence requires a basis")
        return self


class DeclaredGasketJointEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    flange_geometry_id: str = Field(min_length=1)
    flange_material_condition_id: str = Field(min_length=1)
    gasket_material_condition_id: str = Field(min_length=1)
    bolt_material_condition_id: str = Field(min_length=1)
    medium_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    minimum_pressure_Pa: Nonnegative
    maximum_pressure_Pa: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    preload_unit_token: str = Field(min_length=1)
    minimum_individual_preload_value: Positive
    maximum_individual_preload_value: Positive
    maximum_preload_coefficient_of_variation: Nonnegative
    seating_metric_support: GasketMetricSupport
    relaxation_metric_support: GasketMetricSupport
    qualification_evidence: tuple[GasketQualificationEvidence, ...] = Field(min_length=1)
    minimum_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_pressure_Pa < self.minimum_pressure_Pa:
            raise ValueError("gasket pressure support must be ordered")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("gasket temperature support must be ordered")
        if self.maximum_individual_preload_value < self.minimum_individual_preload_value:
            raise ValueError("bolt-preload support must be ordered")
        return self


class GasketJointAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    flange_geometry_id: str = Field(min_length=1)
    flange_material_condition_id: str = Field(min_length=1)
    gasket_material_condition_id: str = Field(min_length=1)
    gasket_lot_id: str = Field(min_length=1)
    bolt_material_condition_id: str = Field(min_length=1)
    bolt_lot_id: str = Field(min_length=1)
    medium_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    operating_pressure_Pa: Nonnegative
    operating_temperature_K: Positive
    bolt_preloads: tuple[BoltPreloadRecord, ...] = Field(min_length=2)
    seating_result: GasketSeatingProviderResult
    relaxation_observations: tuple[JointRelaxationObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredGasketJointEnvelope, ...] = Field(min_length=1)
    flange_gasket_bolt_material_and_lot_reviewed: bool
    medium_pressure_basis_and_temperature_reviewed: bool
    preload_method_units_uncertainty_and_bolt_identity_reviewed: bool
    seating_provider_revision_configuration_and_digests_reviewed: bool
    relaxation_clock_metrics_units_and_uncertainty_reviewed: bool
    qualification_specimens_partitions_and_source_groups_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_records(self):
        bolt_ids = [row.bolt_id for row in self.bolt_preloads]
        observation_ids = [row.observation_id for row in self.relaxation_observations]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        for values, label in (
            (bolt_ids, "bolt"),
            (observation_ids, "relaxation observation"),
            (envelope_ids, "gasket envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        times = [row.elapsed_time_s for row in self.relaxation_observations]
        if times != sorted(times):
            raise ValueError("joint-relaxation observations must be supplied in time order")
        return self


def gasket_joint_evidence(x: GasketJointAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "flange_gasket_bolt_material_and_lot_reviewed",
            "medium_pressure_basis_and_temperature_reviewed",
            "preload_method_units_uncertainty_and_bolt_identity_reviewed",
            "seating_provider_revision_configuration_and_digests_reviewed",
            "relaxation_clock_metrics_units_and_uncertainty_reviewed",
            "qualification_specimens_partitions_and_source_groups_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_preload_ids = [row.bolt_id for row in x.bolt_preloads if not row.record_valid]
    invalid_relaxation_ids = [row.observation_id for row in x.relaxation_observations if not row.record_valid]
    invalid_qualification_ids = [
        row.evidence_record_id
        for envelope in x.candidate_envelopes
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    if (
        missing_reviews
        or invalid_preload_ids
        or invalid_relaxation_ids
        or invalid_qualification_ids
        or not x.seating_result.record_valid
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "invalid_preload_bolt_ids": invalid_preload_ids,
                "invalid_seating_result_id": (
                    None if x.seating_result.record_valid else x.seating_result.result_id
                ),
                "invalid_relaxation_observation_ids": invalid_relaxation_ids,
                "invalid_qualification_evidence_ids": invalid_qualification_ids,
                "missing_reviews": missing_reviews,
            },
            notes=(
                "Complete valid reviewed assembly, seating, relaxation and qualification records are required.",
            ),
        )

    matching = [
        envelope
        for envelope in x.candidate_envelopes
        if envelope.flange_geometry_id == x.flange_geometry_id
        and envelope.flange_material_condition_id == x.flange_material_condition_id
        and envelope.gasket_material_condition_id == x.gasket_material_condition_id
        and envelope.bolt_material_condition_id == x.bolt_material_condition_id
        and envelope.medium_id == x.medium_id
        and envelope.pressure_basis == x.pressure_basis
    ]
    if not matching:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [],
                "outside_support_reasons": ["joint_or_service_identity"],
                "missing_reviews": [],
            },
            notes=("Reviewed joint or service identities are outside the supplied gasket envelopes.",),
        )
    if len(matching) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matching],
                "missing_reviews": [],
            },
            notes=("The caller envelopes must select exactly one gasket-joint support record.",),
        )
    envelope = matching[0]
    unit_mismatch_ids = [
        row.bolt_id for row in x.bolt_preloads if row.preload_unit_token != envelope.preload_unit_token
    ]
    seating_support = envelope.seating_metric_support
    seating_definition_match = (
        x.seating_result.metric_id == seating_support.metric_id
        and x.seating_result.metric_definition == seating_support.metric_definition
        and x.seating_result.unit_token == seating_support.unit_token
    )
    relaxation_support = envelope.relaxation_metric_support
    relaxation_definition_mismatch_ids = [
        row.observation_id
        for row in x.relaxation_observations
        if row.metric_id != relaxation_support.metric_id
        or row.metric_definition != relaxation_support.metric_definition
        or row.unit_token != relaxation_support.unit_token
    ]
    source_group_count = len(
        {
            record.source_group_id
            for record in envelope.qualification_evidence
            if record.record_valid and record.supports_declared_envelope
        }
    )
    supported_metrics = {
        metric for record in envelope.qualification_evidence for metric in record.supported_metric_ids
    }
    required_metric_ids = {seating_support.metric_id, relaxation_support.metric_id}
    if (
        unit_mismatch_ids
        or not seating_definition_match
        or relaxation_definition_mismatch_ids
        or seating_support.minimum_record_count > 1
        or len(x.relaxation_observations) < relaxation_support.minimum_record_count
        or source_group_count < envelope.minimum_source_group_count
        or not required_metric_ids.issubset(supported_metrics)
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "selected_envelope_id": envelope.envelope_id,
                "preload_unit_mismatch_bolt_ids": unit_mismatch_ids,
                "seating_definition_match": seating_definition_match,
                "seating_result_count": 1,
                "required_seating_result_count": seating_support.minimum_record_count,
                "relaxation_definition_mismatch_ids": relaxation_definition_mismatch_ids,
                "qualification_source_group_count": source_group_count,
                "missing_qualification_metric_ids": sorted(required_metric_ids - supported_metrics),
                "missing_reviews": [],
            },
            notes=(
                "Exact metric definitions, units, record counts and qualification coverage are required.",
            ),
        )

    preload_values = [float(row.preload_value) for row in x.bolt_preloads]
    preload_mean = fmean(preload_values)
    preload_std = pstdev(preload_values)
    preload_cov = preload_std / preload_mean
    outside_reasons = []
    if not envelope.minimum_pressure_Pa <= x.operating_pressure_Pa <= envelope.maximum_pressure_Pa:
        outside_reasons.append("operating_pressure")
    if not envelope.minimum_temperature_K <= x.operating_temperature_K <= envelope.maximum_temperature_K:
        outside_reasons.append("operating_temperature")
    outside_preload_ids = [
        row.bolt_id
        for row in x.bolt_preloads
        if not (
            envelope.minimum_individual_preload_value
            <= row.preload_value
            <= envelope.maximum_individual_preload_value
        )
    ]
    if outside_preload_ids:
        outside_reasons.append("individual_preload")
    if preload_cov > envelope.maximum_preload_coefficient_of_variation:
        outside_reasons.append("preload_scatter")
    seating_within = (
        seating_support.minimum_supported_value
        <= x.seating_result.reported_value
        <= seating_support.maximum_supported_value
        and x.seating_result.expanded_uncertainty <= seating_support.maximum_supported_expanded_uncertainty
    )
    if not seating_within:
        outside_reasons.append("seating_result")
    outside_relaxation_ids = [
        row.observation_id
        for row in x.relaxation_observations
        if not (
            relaxation_support.minimum_supported_value
            <= row.reported_value
            <= relaxation_support.maximum_supported_value
            and row.expanded_uncertainty <= relaxation_support.maximum_supported_expanded_uncertainty
        )
    ]
    if outside_relaxation_ids:
        outside_reasons.append("relaxation_observation")
    status = "out_of_scope" if outside_reasons else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "joint_id": x.joint_id,
            "selected_envelope_id": envelope.envelope_id,
            "declared_evidence_outcome": (
                "outside_declared_support" if outside_reasons else "within_support"
            ),
            "bolt_count": len(preload_values),
            "preload_mean": preload_mean,
            "preload_population_standard_deviation": preload_std,
            "preload_coefficient_of_variation": preload_cov,
            "outside_support_preload_bolt_ids": outside_preload_ids,
            "seating_result_within_support": seating_within,
            "outside_support_relaxation_observation_ids": outside_relaxation_ids,
            "outside_support_reasons": outside_reasons,
            "qualification_source_group_count": source_group_count,
            "missing_reviews": [],
        },
        notes=(
            "Bolt statistics summarize direct preload records in one exact unit; torque is never converted to preload.",
            "Gasket seating and relaxation metrics and support are caller-owned and are not extrapolated.",
            "This evidence model does not calculate gasket contact mechanics, leakage, bolt relaxation, structural capacity, acceptance, life, or probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("gasket-joint assessment asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.gasket_joint_evidence",
            GasketJointAssessment,
            gasket_joint_evidence,
            {
                "assessment_id": "1",
                "joint_id": "1",
                "selected_envelope_id": "1",
                "declared_evidence_outcome": "1",
                "bolt_count": "count",
                "preload_mean": "caller_preload_unit",
                "preload_population_standard_deviation": "caller_preload_unit",
                "preload_coefficient_of_variation": "1",
                "outside_support_preload_bolt_ids": "1",
                "seating_result_within_support": "1",
                "outside_support_relaxation_observation_ids": "1",
                "outside_support_reasons": "1",
                "qualification_source_group_count": "count",
                "missing_reviews": "1",
            },
            (
                "Flange, gasket, bolt lots, medium, pressure basis and operating state are caller reviewed.",
                "Bolt preload values are direct records in one exact unit and are not inferred from torque.",
                "Seating, relaxation and qualification metrics, uncertainty and support are caller-owned.",
            ),
            ("reviewed_gasket_joint_qualification_envelope",),
            version="1.0.1",
            context_validator=same_identity,
        )
    ]
