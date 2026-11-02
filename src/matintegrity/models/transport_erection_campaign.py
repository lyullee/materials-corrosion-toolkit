"""Caller-owned campaign evidence audit for transport, handling, and erection."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

EventKind = Literal[
    "lift",
    "transport",
    "storage",
    "erection",
    "temporary_support_install",
    "temporary_support_remove",
    "other",
]
ObservationKind = Literal["acceleration", "load", "orientation", "temperature", "humidity", "impact", "other"]
MeasurementKind = Literal["alignment", "geometry", "damage_survey", "nde", "other"]


class HandlingObservation(Contract):
    observation_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    observation_time_s: Nonnegative
    observation_kind: ObservationKind
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    value: float | None = None
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    sensor_or_instrument_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def value_and_validity(self):
        if self.record_valid and (self.value is None or self.expanded_uncertainty is None):
            raise ValueError("valid handling observations require value and uncertainty")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid handling observations require a basis")
        return self


class OrderedHandlingEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    event_kind: EventKind
    activity_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    item_id: str = Field(min_length=1)
    lift_id: str | None = Field(default=None, min_length=1)
    transport_id: str | None = Field(default=None, min_length=1)
    storage_id: str | None = Field(default=None, min_length=1)
    erection_id: str | None = Field(default=None, min_length=1)
    support_id: str | None = Field(default=None, min_length=1)
    orientation_definition: str = Field(min_length=1)
    event_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: tuple[HandlingObservation, ...] = ()
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_event(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("handling events require positive duration")
        identity_field = {
            "lift": self.lift_id,
            "transport": self.transport_id,
            "storage": self.storage_id,
            "erection": self.erection_id,
            "temporary_support_install": self.support_id,
            "temporary_support_remove": self.support_id,
        }.get(self.event_kind, True)
        if identity_field is None:
            raise ValueError(f"{self.event_kind} events require their specific identity")
        observation_ids = [row.observation_id for row in self.observations]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("handling observation identities must be unique within an event")
        if any(row.event_id != self.event_id for row in self.observations):
            raise ValueError("handling observations must reference their containing event")
        if any(
            not self.start_time_s <= row.observation_time_s <= self.end_time_s for row in self.observations
        ):
            raise ValueError("handling observations must occur inside their event interval")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid handling events require a basis")
        return self


class TemporarySupportEvidence(Contract):
    support_id: str = Field(min_length=1)
    support_type_descriptor: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    installation_event_id: str = Field(min_length=1)
    removal_event_id: str | None = Field(default=None, min_length=1)
    final_state: Literal["installed", "removed"]
    support_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    installation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    removal_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_state(self):
        if self.final_state == "removed" and (
            self.removal_event_id is None or self.removal_record_digest is None
        ):
            raise ValueError("removed temporary supports require removal event and digest")
        if self.final_state == "installed" and (
            self.removal_event_id is not None or self.removal_record_digest is not None
        ):
            raise ValueError("installed temporary supports cannot carry removal evidence")
        return self


class ErectionMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    measurement_time_s: Nonnegative
    measurement_kind: MeasurementKind
    stage_id: str = Field(min_length=1)
    metric_id: str | None = Field(default=None, min_length=1)
    metric_definition: str | None = Field(default=None, min_length=1)
    value: float | None = None
    unit_token: str | None = Field(default=None, min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    reported_finding: str = Field(min_length=1)
    caller_disposition_id: str | None = Field(default=None, min_length=1)
    instrument_or_nde_procedure_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    measurement_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        quantitative = (
            self.metric_id,
            self.metric_definition,
            self.value,
            self.unit_token,
            self.expanded_uncertainty,
        )
        if any(value is not None for value in quantitative) and any(value is None for value in quantitative):
            raise ValueError(
                "quantitative erection measurements require metric, value, unit, and uncertainty"
            )
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid erection measurements require a basis")
        return self


class TransportErectionCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    evidence_source: Literal["observation", "measurement"]
    metric_id: str = Field(min_length=1)
    aggregation: Literal["minimum", "maximum"]
    direction: Literal["minimum", "maximum"]
    accept_limit: float
    reject_limit: float
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum handling criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum handling criteria require accept <= reject")
        return self


class TransportErectionCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_event_kinds: tuple[EventKind, ...] = Field(min_length=1)
    required_measurement_kinds: tuple[MeasurementKind, ...] = Field(min_length=1)
    required_measurement_stage_ids: tuple[str, ...] = Field(min_length=1)
    criteria: tuple[TransportErectionCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    structural_solver_used: Literal[False] = False
    allowable_load_or_code_table_embedded: Literal[False] = False
    automatic_damage_determination_claimed: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile_items(self):
        for values, label in (
            (self.required_event_kinds, "event kinds"),
            (self.required_measurement_kinds, "measurement kinds"),
            (self.required_measurement_stage_ids, "measurement stages"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"required handling {label} must be unique")
        keys = [(row.evidence_source, row.metric_id) for row in self.criteria]
        ids = [row.criterion_id for row in self.criteria]
        if len(set(keys)) != len(keys) or len(set(ids)) != len(ids):
            raise ValueError("transport and erection criteria must have unique identities and metric sources")
        return self


class TransportErectionCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    item_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    clock_id: str = Field(min_length=1)
    events: tuple[OrderedHandlingEvent, ...] = Field(min_length=1)
    temporary_supports: tuple[TemporarySupportEvidence, ...] = ()
    measurements: tuple[ErectionMeasurement, ...] = Field(min_length=1)
    caller_profile: TransportErectionCallerProfile
    item_lift_transport_storage_erection_identity_reviewed: bool
    ordered_event_clock_and_orientation_reviewed: bool
    observation_units_uncertainty_and_provenance_reviewed: bool
    temporary_support_install_remove_state_reviewed: bool
    alignment_geometry_damage_and_nde_evidence_reviewed: bool
    caller_profile_and_criteria_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        event_ids = [row.event_id for row in self.events]
        sequence = [row.sequence_index for row in self.events]
        observation_ids = [obs.observation_id for event in self.events for obs in event.observations]
        measurement_ids = [row.measurement_id for row in self.measurements]
        support_ids = [row.support_id for row in self.temporary_supports]
        for values, label in (
            (event_ids, "event"),
            (sequence, "event sequence"),
            (observation_ids, "observation"),
            (measurement_ids, "measurement"),
            (support_ids, "temporary support"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"transport and erection {label} identities must be unique")
        ordered = sorted(self.events, key=lambda row: row.sequence_index)
        if tuple(ordered) != self.events:
            raise ValueError("handling events must be supplied in sequence order")
        if any(
            next_row.start_time_s < row.start_time_s
            for row, next_row in zip(ordered, ordered[1:], strict=False)
        ):
            raise ValueError("handling event start times must not reverse sequence order")
        by_id = {row.event_id: row for row in self.events}
        if any(row.item_id != self.item_id for row in self.events):
            raise ValueError("all handling events must reference the campaign item")
        for measurement in self.measurements:
            event = by_id.get(measurement.event_id)
            if event is None or not event.start_time_s <= measurement.measurement_time_s <= event.end_time_s:
                raise ValueError("erection measurements must occur inside a declared event")
        for support in self.temporary_supports:
            install = by_id.get(support.installation_event_id)
            if (
                install is None
                or install.event_kind != "temporary_support_install"
                or install.support_id != support.support_id
            ):
                raise ValueError("temporary support installation must link to its install event")
            if support.removal_event_id is not None:
                removal = by_id.get(support.removal_event_id)
                if (
                    removal is None
                    or removal.event_kind != "temporary_support_remove"
                    or removal.support_id != support.support_id
                ):
                    raise ValueError("temporary support removal must link to its remove event")
                if removal.sequence_index <= install.sequence_index:
                    raise ValueError("temporary support removal must follow installation")
        return self


class TransportErectionCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.transport_erection_campaign_report.v1"] = (
        "matintegrity.transport_erection_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    structural_solver_or_allowable_load: Literal[False] = False
    automatic_damage_determination: Literal[False] = False
    physical_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("transport and erection campaign report digest does not match content")
        return self


def _bound_report(**payload: Any) -> TransportErectionCampaignReport:
    unsigned = TransportErectionCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return TransportErectionCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: TransportErectionCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def transport_erection_campaign(x: TransportErectionCampaignAssessment) -> Calculation:
    review_fields = (
        "item_lift_transport_storage_erection_identity_reviewed",
        "ordered_event_clock_and_orientation_reviewed",
        "observation_units_uncertainty_and_provenance_reviewed",
        "temporary_support_install_remove_state_reviewed",
        "alignment_geometry_damage_and_nde_evidence_reviewed",
        "caller_profile_and_criteria_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    observations = [obs for event in x.events for obs in event.observations]
    invalid_events = [row.event_id for row in x.events if not row.record_valid]
    invalid_observations = [row.observation_id for row in observations if not row.record_valid]
    invalid_measurements = [row.measurement_id for row in x.measurements if not row.record_valid]
    profile = x.caller_profile
    represented_events = {row.event_kind for row in x.events}
    represented_measurements = {row.measurement_kind for row in x.measurements}
    represented_stages = {row.stage_id for row in x.measurements}
    missing_event_kinds = sorted(set(profile.required_event_kinds) - represented_events)
    missing_measurement_kinds = sorted(set(profile.required_measurement_kinds) - represented_measurements)
    missing_stages = sorted(set(profile.required_measurement_stage_ids) - represented_stages)
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_event_ids": invalid_events,
        "invalid_observation_ids": invalid_observations,
        "invalid_measurement_ids": invalid_measurements,
        "missing_required_event_kinds": missing_event_kinds,
        "missing_required_measurement_kinds": missing_measurement_kinds,
        "missing_required_measurement_stage_ids": missing_stages,
        "event_ids_in_order": [row.event_id for row in x.events],
        "temporary_support_states": {row.support_id: row.final_state for row in x.temporary_supports},
        "observation_record_digests": [row.observation_record_digest for row in observations],
        "measurement_record_digests": [row.measurement_record_digest for row in x.measurements],
    }
    if any(
        (
            missing_reviews,
            invalid_events,
            invalid_observations,
            invalid_measurements,
            missing_event_kinds,
            missing_measurement_kinds,
            missing_stages,
        )
    ):
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Complete reviewed campaign evidence is required.",),
        )

    metric_values: dict[str, float] = {}
    metric_units: dict[str, str] = {}
    missing_criteria: list[str] = []
    unit_conflicts: list[str] = []
    for criterion in profile.criteria:
        rows = observations if criterion.evidence_source == "observation" else x.measurements
        matching = [row for row in rows if row.metric_id == criterion.metric_id]
        if not matching:
            missing_criteria.append(criterion.criterion_id)
            continue
        units = {row.unit_token for row in matching}
        if units != {criterion.unit_token}:
            unit_conflicts.append(criterion.criterion_id)
            continue
        values = [row.value for row in matching]
        key = f"{criterion.evidence_source}:{criterion.metric_id}"
        metric_values[key] = min(values) if criterion.aggregation == "minimum" else max(values)
        metric_units[key] = criterion.unit_token
    if missing_criteria or unit_conflicts:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={
                **diagnostics,
                "missing_criterion_evidence_ids": missing_criteria,
                "criterion_unit_conflict_ids": unit_conflicts,
            },
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Each caller criterion requires matching exact-unit quantitative evidence.",),
        )

    findings = tuple(
        {
            "criterion_id": row.criterion_id,
            "metric_key": f"{row.evidence_source}:{row.metric_id}",
            "aggregation": row.aggregation,
            "value": metric_values[f"{row.evidence_source}:{row.metric_id}"],
            "unit": metric_units[f"{row.evidence_source}:{row.metric_id}"],
            "direction": row.direction,
            "accept_limit": row.accept_limit,
            "reject_limit": row.reject_limit,
            "outcome": _criterion_outcome(metric_values[f"{row.evidence_source}:{row.metric_id}"], row),
            "criterion_basis": row.criterion_basis,
        }
        for row in profile.criteria
    )
    outcomes = {row["outcome"] for row in findings}
    campaign_outcome = "reject" if "reject" in outcomes else "review" if "review" in outcomes else "accept"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        campaign_outcome=campaign_outcome,
        caller_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Accept, review and reject reflect caller-authored campaign criteria only.",
            "Observations and reported findings do not invoke a structural solver, establish allowable load, or automatically determine damage.",
            "The campaign result is not physical qualification, remaining life, or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("transport and erection campaign asset and location must match run context")

    return [
        ModelSpec(
            "fabrication.transport_erection",
            TransportErectionCampaignAssessment,
            transport_erection_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "campaign_outcome": "1",
                "caller_profile_id": "1",
                "metric_values": "mixed",
                "criterion_findings": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "structural_solver_or_allowable_load": "1",
                "automatic_damage_determination": "1",
                "physical_qualification": "1",
                "report_digest": "1",
            },
            (
                "Ordered item, lift, transport, storage, support and erection evidence is caller supplied.",
                "No structural solver, allowable load table, automatic damage decision, or qualification is produced.",
            ),
            ("authored_transport_erection_campaign_evidence_audit",),
            context_validator=same_identity,
        )
    ]
