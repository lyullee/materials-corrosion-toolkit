"""Ordered repair-welding evidence compared with a caller-owned workflow envelope."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

RepairStepKind = Literal[
    "removal",
    "pre_deposition_inspection",
    "deposition",
    "heat_treatment",
    "subsequent_examination",
]


class RepairStepMetric(Contract):
    metric_id: str = Field(min_length=1)
    value: float
    unit_token: str = Field(min_length=1)
    measurement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class RepairWeldingStep(Contract):
    step_record_id: str = Field(min_length=1)
    stage_id: str = Field(min_length=1)
    step_kind: RepairStepKind
    physical_scope_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_descriptor: str = Field(min_length=1)
    reported_finding_or_outcome: str | None = None
    caller_disposition_id: str | None = None
    metrics: tuple[RepairStepMetric, ...] = ()
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_and_complete(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("repair-welding steps must have positive duration")
        metric_ids = [row.metric_id for row in self.metrics]
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("repair-step metric identifiers must be unique")
        if self.step_kind in {"pre_deposition_inspection", "subsequent_examination"}:
            if self.record_valid and not self.reported_finding_or_outcome:
                raise ValueError("a valid repair examination step requires a reported finding or outcome")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid repair-welding step requires a basis")
        return self


class DeclaredRepairMetricEnvelope(Contract):
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    applicability_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def at_least_one_ordered_bound(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a repair metric envelope requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("repair metric envelope bounds must be ordered")
        return self


class RequiredRepairWorkflowStage(Contract):
    stage_id: str = Field(min_length=1)
    step_kind: RepairStepKind
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    required_provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    required_provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    metric_envelopes: tuple[DeclaredRepairMetricEnvelope, ...] = ()
    requirement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_metric_envelopes(self):
        identifiers = [row.metric_id for row in self.metric_envelopes]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("repair workflow metric-envelope identifiers must be unique per stage")
        return self


class DeclaredRepairWorkflowEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    repair_scope_id: str = Field(min_length=1)
    component_condition_id: str = Field(min_length=1)
    repair_location_id: str = Field(min_length=1)
    required_stages: tuple[RequiredRepairWorkflowStage, ...] = Field(min_length=1)
    declaration_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_stages(self):
        identifiers = [row.stage_id for row in self.required_stages]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("required repair workflow stage identifiers must be unique")
        return self


class RepairWeldingHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    repair_scope_id: str = Field(min_length=1)
    component_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    steps: tuple[RepairWeldingStep, ...] = Field(min_length=1)
    candidate_workflow_envelopes: tuple[DeclaredRepairWorkflowEnvelope, ...] = Field(min_length=1)
    repair_scope_and_location_reviewed: bool
    sequence_and_clock_reviewed: bool
    procedure_and_provider_identity_reviewed: bool
    provider_digests_reviewed: bool
    step_evidence_reviewed: bool
    workflow_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def ordered_history(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("repair-welding history horizon must have positive duration")
        step_ids = [row.step_record_id for row in self.steps]
        envelope_ids = [row.envelope_id for row in self.candidate_workflow_envelopes]
        if len(set(step_ids)) != len(step_ids):
            raise ValueError("repair-welding step-record identifiers must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("repair workflow envelope identifiers must be unique")
        envelope_keys = [_envelope_identity(row) for row in self.candidate_workflow_envelopes]
        if len(set(envelope_keys)) != len(envelope_keys):
            raise ValueError("repair workflow envelopes must have unique exact identities")
        previous_end = self.horizon_start_s
        for row in self.steps:
            if row.location_id != self.location_id:
                raise ValueError("repair-welding step location must match the history location")
            if row.start_time_s < self.horizon_start_s or row.end_time_s > self.horizon_end_s:
                raise ValueError("repair-welding steps must remain inside the history horizon")
            if row.start_time_s < previous_end:
                raise ValueError("repair-welding steps must be ordered and cannot overlap")
            previous_end = row.end_time_s
        return self


def _envelope_identity(envelope: DeclaredRepairWorkflowEnvelope) -> tuple[str, str, str]:
    return (envelope.repair_scope_id, envelope.component_condition_id, envelope.repair_location_id)


def repair_welding_history(x: RepairWeldingHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "repair_scope_and_location_reviewed",
            "sequence_and_clock_reviewed",
            "procedure_and_provider_identity_reviewed",
            "provider_digests_reviewed",
            "step_evidence_reviewed",
            "workflow_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_step_ids = [row.step_record_id for row in x.steps if not row.record_valid]
    target_identity = (x.repair_scope_id, x.component_condition_id, x.location_id)
    matches = [
        envelope
        for envelope in x.candidate_workflow_envelopes
        if _envelope_identity(envelope) == target_identity
    ]
    if missing_reviews or invalid_step_ids:
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "invalid_step_record_ids": invalid_step_ids,
                "missing_reviews": missing_reviews,
            },
            notes=("Invalid or unreviewed repair evidence is not bridged or treated as completed work.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                "identity_matching_envelope_ids": [],
                "invalid_step_record_ids": [],
                "missing_reviews": [],
            },
            notes=("No caller-owned workflow envelope has the exact repair scope and location identity.",),
        )

    envelope = matches[0]
    required_by_stage = {row.stage_id: row for row in envelope.required_stages}
    observed_stage_ids = [row.stage_id for row in x.steps]
    required_stage_ids = [row.stage_id for row in envelope.required_stages]
    sequence_matches = observed_stage_ids == required_stage_ids
    missing_stage_ids = [
        identifier for identifier in required_stage_ids if identifier not in observed_stage_ids
    ]
    unrecognized_stage_ids = [
        identifier for identifier in observed_stage_ids if identifier not in required_by_stage
    ]

    comparison_rows = []
    unit_mismatch_metric_ids = []
    missing_metric_ids = []
    outside_metric_ids = []
    identity_mismatch_stage_ids = []
    for step in x.steps:
        requirement = required_by_stage.get(step.stage_id)
        if requirement is None:
            continue
        identity_matches = (
            step.step_kind == requirement.step_kind
            and step.procedure_id == requirement.procedure_id
            and step.procedure_revision == requirement.procedure_revision
            and step.provider_id == requirement.provider_id
            and step.provider_revision == requirement.provider_revision
            and step.provider_state_digest == requirement.required_provider_state_digest
            and step.provider_configuration_digest == requirement.required_provider_configuration_digest
        )
        if not identity_matches:
            identity_mismatch_stage_ids.append(step.stage_id)
        metrics = {row.metric_id: row for row in step.metrics}
        metric_rows = []
        for limit in requirement.metric_envelopes:
            metric = metrics.get(limit.metric_id)
            qualified_metric_id = f"{step.stage_id}:{limit.metric_id}"
            if metric is None:
                missing_metric_ids.append(qualified_metric_id)
                metric_rows.append(
                    {
                        "metric_id": limit.metric_id,
                        "unit_matches_exactly": None,
                        "within_declared_envelope": None,
                    }
                )
                continue
            unit_matches = metric.unit_token == limit.unit_token
            if not unit_matches:
                unit_mismatch_metric_ids.append(qualified_metric_id)
                within = None
            else:
                within = not (
                    (limit.minimum_value is not None and metric.value < limit.minimum_value)
                    or (limit.maximum_value is not None and metric.value > limit.maximum_value)
                )
                if not within:
                    outside_metric_ids.append(qualified_metric_id)
            metric_rows.append(
                {
                    "metric_id": limit.metric_id,
                    "value": metric.value,
                    "unit_token": metric.unit_token,
                    "unit_matches_exactly": unit_matches,
                    "within_declared_envelope": within,
                }
            )
        comparison_rows.append(
            {
                "step_record_id": step.step_record_id,
                "stage_id": step.stage_id,
                "step_kind": step.step_kind,
                "duration_s": step.end_time_s - step.start_time_s,
                "procedure_provider_and_state_match": identity_matches,
                "metric_comparisons": metric_rows,
                "caller_disposition_id": step.caller_disposition_id,
            }
        )

    incomplete = (
        not sequence_matches
        or bool(missing_stage_ids)
        or bool(unrecognized_stage_ids)
        or bool(missing_metric_ids)
        or bool(unit_mismatch_metric_ids)
    )
    status = "needs_data" if incomplete else "computed"
    within = None
    if status == "computed":
        within = not identity_mismatch_stage_ids and not outside_metric_ids
    return Calculation(
        status=status,
        values={
            "history_id": x.history_id,
            "selected_workflow_envelope_id": envelope.envelope_id,
            "recorded_step_kind_counts": {
                kind: sum(row.step_kind == kind for row in x.steps)
                for kind in (
                    "removal",
                    "pre_deposition_inspection",
                    "deposition",
                    "heat_treatment",
                    "subsequent_examination",
                )
            },
            "recorded_stage_sequence": observed_stage_ids,
            "required_stage_sequence": required_stage_ids,
            "stage_sequence_matches_exactly": sequence_matches,
            "missing_required_stage_ids": missing_stage_ids,
            "unrecognized_stage_ids": unrecognized_stage_ids,
            "stage_comparisons": comparison_rows,
            "identity_mismatch_stage_ids": identity_mismatch_stage_ids,
            "missing_required_metric_ids": missing_metric_ids,
            "unit_mismatch_metric_ids": unit_mismatch_metric_ids,
            "outside_declared_metric_envelope_ids": outside_metric_ids,
            "all_steps_within_declared_workflow_envelope": within,
            "missing_reviews": [],
        },
        notes=(
            "Required stages, identities, digest pins and metric bounds are caller-owned declarations, not bundled welding-code requirements.",
            "A complete history or envelope match does not establish defect removal, weld quality, structural integrity, service life or production acceptance.",
            "Input and result digests preserve provider lineage but do not validate the provider method or its physical applicability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("repair-welding history asset and location must match the run context")

    return [
        ModelSpec(
            "welding.repair_welding_history",
            RepairWeldingHistory,
            repair_welding_history,
            {
                "history_id": "1",
                "selected_workflow_envelope_id": "1",
                "recorded_step_kind_counts": "count",
                "recorded_stage_sequence": "1",
                "required_stage_sequence": "1",
                "stage_sequence_matches_exactly": "1",
                "missing_required_stage_ids": "1",
                "unrecognized_stage_ids": "1",
                "stage_comparisons": "mixed",
                "identity_mismatch_stage_ids": "1",
                "missing_required_metric_ids": "1",
                "unit_mismatch_metric_ids": "1",
                "outside_declared_metric_envelope_ids": "1",
                "all_steps_within_declared_workflow_envelope": "1",
                "missing_reviews": "1",
            },
            (
                "Recorded repair steps use one reviewed clock, remain ordered and cannot overlap.",
                "The exact stage sequence, procedure/provider revisions, state digests and metric envelopes are supplied by the caller.",
                "Missing stages, metrics, units or invalid evidence remain explicit and prevent a complete result.",
            ),
            ("declared_repair_welding_workflow_accounting",),
            context_validator=same_identity,
        )
    ]
