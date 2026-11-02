"""Tube-bundle inspection evidence compared with caller-owned support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class TubeBundleOperatingInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    operating_state_id: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("tube-bundle operating intervals must have positive duration")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid operating interval requires a basis")
        return self


class TubeBundleObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: Literal["defect_or_condition_inspection", "vibration_observation"]
    physical_source_group_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float | None = None
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    detection_status: Literal["detected", "not_detected", "below_detection", "not_evaluated"]
    detection_limit: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        if self.detection_status in {"detected", "not_detected"} and self.reported_value is None:
            raise ValueError("evaluated tube-bundle observations require a reported value")
        if self.detection_status == "below_detection" and self.detection_limit is None:
            raise ValueError("below-detection observations require a detection limit")
        if self.detection_status == "not_evaluated" and not self.invalid_or_missing_basis:
            raise ValueError("not-evaluated observations require a missingness basis")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid observations require a basis")
        return self


class TubeBundleDispositionRecord(Contract):
    disposition_id: str = Field(min_length=1)
    disposition_kind: Literal["repair", "plug", "retube", "monitor", "no_action"]
    disposition_time_s: Nonnegative
    caller_decision_record_id: str = Field(min_length=1)
    affected_tube_id: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_disposition(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid tube-bundle disposition requires a basis")
        return self


class TubeBundleMetricSupport(Contract):
    observation_kind: Literal["defect_or_condition_inspection", "vibration_observation"]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    supported_method_ids: tuple[str, ...] = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float
    maximum_supported_expanded_uncertainty: Nonnegative
    support_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("tube-bundle metric support bounds must be ordered")
        if len(self.supported_method_ids) != len(set(self.supported_method_ids)):
            raise ValueError("supported tube-bundle method identifiers must be unique")
        return self


class TubeBundleQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["qualification", "holdout", "application"]
    supported_metric_ids: tuple[str, ...] = Field(min_length=1)
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
        if len(self.supported_metric_ids) != len(set(self.supported_metric_ids)):
            raise ValueError("tube-bundle evidence metric identifiers must be unique")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting tube-bundle evidence requires a basis")
        return self


class TubeBundleIntegrityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    tube_material_condition_id: str = Field(min_length=1)
    minimum_outer_diameter_m: Positive
    maximum_outer_diameter_m: Positive
    minimum_wall_thickness_m: Positive
    maximum_wall_thickness_m: Positive
    supported_support_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_baffle_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_vibration_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_operating_state_ids: tuple[str, ...] = Field(min_length=1)
    metric_support: tuple[TubeBundleMetricSupport, ...] = Field(min_length=1)
    qualification_evidence: tuple[TubeBundleQualificationEvidence, ...] = Field(min_length=1)
    minimum_qualification_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_outer_diameter_m < self.minimum_outer_diameter_m:
            raise ValueError("tube outer-diameter support bounds must be ordered")
        if self.maximum_wall_thickness_m < self.minimum_wall_thickness_m:
            raise ValueError("tube wall-thickness support bounds must be ordered")
        for values, label in (
            (self.supported_support_descriptors, "support descriptors"),
            (self.supported_baffle_descriptors, "baffle descriptors"),
            (self.supported_vibration_descriptors, "vibration descriptors"),
            (self.supported_operating_state_ids, "operating-state identifiers"),
            ([row.metric_id for row in self.metric_support], "metric identifiers"),
            ([row.evidence_record_id for row in self.qualification_evidence], "evidence identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"tube-bundle {label} must be unique")
        return self


class TubeBundleIntegrityEvidence(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    exchanger_id: str = Field(min_length=1)
    bundle_id: str = Field(min_length=1)
    tube_id: str = Field(min_length=1)
    row_id: str = Field(min_length=1)
    tube_location_definition: str = Field(min_length=1)
    tube_material_condition_id: str = Field(min_length=1)
    tube_outer_diameter_m: Positive
    tube_wall_thickness_m: Positive
    support_descriptor: str = Field(min_length=1)
    baffle_descriptor: str = Field(min_length=1)
    vibration_descriptor: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    operating_intervals: tuple[TubeBundleOperatingInterval, ...] = Field(min_length=1)
    observations: tuple[TubeBundleObservation, ...] = Field(min_length=1)
    disposition_records: tuple[TubeBundleDispositionRecord, ...] = ()
    candidate_envelopes: tuple[TubeBundleIntegrityEnvelope, ...] = Field(min_length=1)
    exchanger_bundle_tube_row_and_location_reviewed: bool
    tube_material_condition_and_geometry_reviewed: bool
    support_baffle_and_vibration_descriptors_reviewed: bool
    operating_clock_and_states_reviewed: bool
    observation_metrics_units_uncertainty_and_detection_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    disposition_records_reviewed_as_caller_decisions: bool
    qualification_specimens_and_source_groups_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_records(self):
        for values, label in (
            ([row.interval_id for row in self.operating_intervals], "operating interval"),
            ([row.observation_id for row in self.observations], "observation"),
            ([row.disposition_id for row in self.disposition_records], "disposition"),
            ([row.envelope_id for row in self.candidate_envelopes], "envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"tube-bundle {label} identifiers must be unique")
        for first, second in zip(self.operating_intervals, self.operating_intervals[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("tube-bundle operating intervals must be ordered and cannot overlap")
        if any(row.affected_tube_id != self.tube_id for row in self.disposition_records):
            raise ValueError("tube-bundle disposition records must reference the assessed tube")
        return self


def tube_bundle_integrity_evidence(x: TubeBundleIntegrityEvidence) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "exchanger_bundle_tube_row_and_location_reviewed",
            "tube_material_condition_and_geometry_reviewed",
            "support_baffle_and_vibration_descriptors_reviewed",
            "operating_clock_and_states_reviewed",
            "observation_metrics_units_uncertainty_and_detection_reviewed",
            "provider_lineage_and_digests_reviewed",
            "disposition_records_reviewed_as_caller_decisions",
            "qualification_specimens_and_source_groups_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_operating_interval_ids = [
        row.interval_id for row in x.operating_intervals if not row.record_valid
    ]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    invalid_disposition_ids = [row.disposition_id for row in x.disposition_records if not row.record_valid]
    matches = [
        row for row in x.candidate_envelopes if row.tube_material_condition_id == x.tube_material_condition_id
    ]
    if (
        missing_reviews
        or invalid_operating_interval_ids
        or invalid_observation_ids
        or invalid_disposition_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_operating_interval_ids": invalid_operating_interval_ids,
                "invalid_observation_ids": invalid_observation_ids,
                "invalid_disposition_ids": invalid_disposition_ids,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Reviewed operating, observation and caller-disposition records are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller envelope has the exact tube material-condition identity.",),
        )

    envelope = matches[0]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    support = {row.metric_id: row for row in envelope.metric_support}
    missing_metric_ids = sorted(set(support) - {row.metric_id for row in x.observations})
    unsupported_observation_ids = []
    outside_observation_ids = []
    comparisons = []
    for row in x.observations:
        metric = support.get(row.metric_id)
        incompatible = (
            metric is None
            or row.observation_kind != metric.observation_kind
            or row.unit_token != metric.unit_token
            or row.method_id not in metric.supported_method_ids
        )
        if incompatible:
            unsupported_observation_ids.append(row.observation_id)
            within = None
        elif row.detection_status == "not_evaluated" or row.reported_value is None:
            within = None
        else:
            within = (
                metric.minimum_supported_value <= row.reported_value <= metric.maximum_supported_value
                and row.expanded_uncertainty is not None
                and row.expanded_uncertainty <= metric.maximum_supported_expanded_uncertainty
            )
            if not within:
                outside_observation_ids.append(row.observation_id)
        comparisons.append(
            {
                "observation_id": row.observation_id,
                "metric_id": row.metric_id,
                "detection_status": row.detection_status,
                "reported_value": row.reported_value,
                "unit_token": row.unit_token,
                "within_declared_support": within,
            }
        )
    if invalid_evidence_ids or missing_metric_ids or unsupported_observation_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "envelope_id": envelope.envelope_id,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "missing_metric_ids": missing_metric_ids,
                "unsupported_observation_ids": unsupported_observation_ids,
                "observation_comparisons": comparisons,
            },
            notes=(
                "Exact observation metric, method and unit support plus valid qualification evidence are required.",
            ),
        )

    qualification_rows = [row for row in envelope.qualification_evidence if row.partition == "qualification"]
    source_group_count = len({row.source_group_id for row in qualification_rows})
    covered_metrics = {metric for row in qualification_rows for metric in row.supported_metric_ids}
    uncovered_metric_ids = sorted(set(support) - covered_metrics)
    outside_support_reasons = []
    if not envelope.minimum_outer_diameter_m <= x.tube_outer_diameter_m <= envelope.maximum_outer_diameter_m:
        outside_support_reasons.append("tube_outer_diameter")
    if not envelope.minimum_wall_thickness_m <= x.tube_wall_thickness_m <= envelope.maximum_wall_thickness_m:
        outside_support_reasons.append("tube_wall_thickness")
    for value, supported, label in (
        (x.support_descriptor, envelope.supported_support_descriptors, "support_descriptor"),
        (x.baffle_descriptor, envelope.supported_baffle_descriptors, "baffle_descriptor"),
        (x.vibration_descriptor, envelope.supported_vibration_descriptors, "vibration_descriptor"),
    ):
        if value not in supported:
            outside_support_reasons.append(label)
    if any(
        row.operating_state_id not in envelope.supported_operating_state_ids for row in x.operating_intervals
    ):
        outside_support_reasons.append("operating_state")
    if outside_observation_ids:
        outside_support_reasons.append("observation_range_or_uncertainty")
    if source_group_count < envelope.minimum_qualification_source_group_count:
        outside_support_reasons.append("qualification_source_group_count")
    if uncovered_metric_ids:
        outside_support_reasons.append("qualification_metric_coverage")
    return Calculation(
        status="out_of_scope" if outside_support_reasons else "computed",
        values={
            "assessment_id": x.assessment_id,
            "exchanger_id": x.exchanger_id,
            "bundle_id": x.bundle_id,
            "tube_id": x.tube_id,
            "row_id": x.row_id,
            "clock_id": x.clock_id,
            "envelope_id": envelope.envelope_id,
            "observation_comparisons": comparisons,
            "outside_observation_ids": outside_observation_ids,
            "qualification_source_group_count": source_group_count,
            "uncovered_metric_ids": uncovered_metric_ids,
            "caller_disposition_summary": [
                {
                    "disposition_id": row.disposition_id,
                    "disposition_kind": row.disposition_kind,
                    "disposition_time_s": row.disposition_time_s,
                    "caller_decision_record_id": row.caller_decision_record_id,
                }
                for row in x.disposition_records
            ],
            "outside_support_reasons": outside_support_reasons,
            "declared_applicability_outcome": (
                "outside_support" if outside_support_reasons else "within_support"
            ),
        },
        notes=(
            "Disposition records are caller decisions retained for traceability, not decisions made by this model.",
            "No defect sizing inference, vibration model, retubing decision, acceptance, life or probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("tube-bundle assessment asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.tube_bundle_integrity_evidence",
            TubeBundleIntegrityEvidence,
            tube_bundle_integrity_evidence,
            {
                "assessment_id": "1",
                "exchanger_id": "1",
                "bundle_id": "1",
                "tube_id": "1",
                "row_id": "1",
                "clock_id": "1",
                "envelope_id": "1",
                "observation_comparisons": "mixed",
                "outside_observation_ids": "1",
                "qualification_source_group_count": "1",
                "uncovered_metric_ids": "1",
                "caller_disposition_summary": "mixed",
                "outside_support_reasons": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Exchanger, bundle, tube, row and physical location are exact caller-reviewed identities.",
                "Inspection and vibration values retain metric definitions, units, uncertainty and detection status.",
                "Repair, plug and retube records are caller decisions and are never inferred by the model.",
            ),
            ("reviewed_tube_bundle_integrity_evidence_envelope",),
            context_validator=same_identity,
        )
    ]
