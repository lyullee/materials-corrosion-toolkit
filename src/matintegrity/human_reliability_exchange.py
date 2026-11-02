"""Portable records for human-reliability estimates without probability relabelling."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Fraction, canonical_digest, check_finite

EVENT_FIELDS = {
    "id",
    "task_id",
    "step_ids",
    "role",
    "failure_definition",
    "opportunity_definition",
    "conditioning",
    "deadline_s",
    "includes_recovery",
    "includes_timing",
    "dependency_group",
}
ESTIMATE_FIELDS = {
    "event_id",
    "method",
    "probability",
    "conditioning",
    "evidence_ids",
    "uncertainty",
    "includes",
    "status",
    "trace",
}


class HumanReliabilityEstimateRecord(Contract):
    """A complete task-opportunity estimate received from an independent provider."""

    schema_version: Literal["matintegrity.human_reliability_estimate.v1"] = (
        "matintegrity.human_reliability_estimate.v1"
    )
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    assessment_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    task_id: str = Field(min_length=1)
    procedure_version: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    step_ids: list[str] = Field(min_length=1)
    role: Literal["initiating", "latent", "response"]
    failure_definition: str = Field(min_length=1)
    opportunity_definition: str = Field(min_length=1)
    conditioning: str = Field(min_length=1)
    dependency_group: str | None = None
    method: str = Field(min_length=1)
    probability_per_opportunity: Fraction
    probability_semantics: Literal["failure_probability_per_defined_opportunity"] = (
        "failure_probability_per_defined_opportunity"
    )
    evidence_ids: list[str] = Field(min_length=1)
    estimate_status: Literal["assumed", "empirical", "method_estimate", "research"]
    includes: list[Literal["recovery", "timing", "dependency"]]
    empirical_plant_validation_claim: Literal[False] = False
    source_event: dict[str, Any]
    source_estimate: dict[str, Any]
    source_event_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_estimate_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    limitations: list[str] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def aligned_and_bound(self, info: ValidationInfo):
        if set(self.source_event) != EVENT_FIELDS:
            raise ValueError("source human-failure event must use the reviewed provider field set")
        if set(self.source_estimate) != ESTIMATE_FIELDS:
            raise ValueError("source human-reliability estimate must use the reviewed provider field set")
        check_finite(self.source_event)
        check_finite(self.source_estimate)
        if len(set(self.step_ids)) != len(self.step_ids) or any(not value.strip() for value in self.step_ids):
            raise ValueError("human-reliability step IDs must be nonempty and unique")
        if len(set(self.evidence_ids)) != len(self.evidence_ids) or any(
            not value.strip() for value in self.evidence_ids
        ):
            raise ValueError("human-reliability evidence IDs must be nonempty and unique")
        event = self.source_event
        estimate = self.source_estimate
        if (
            event["id"] != self.event_id
            or event["task_id"] != self.task_id
            or event["step_ids"] != self.step_ids
            or event["role"] != self.role
            or event["failure_definition"] != self.failure_definition
            or event["opportunity_definition"] != self.opportunity_definition
            or event["conditioning"] != self.conditioning
            or event["dependency_group"] != self.dependency_group
        ):
            raise ValueError("flattened human-failure event identity differs from its source event")
        if (
            estimate["event_id"] != self.event_id
            or estimate["method"] != self.method
            or estimate["probability"] != self.probability_per_opportunity
            or estimate["conditioning"] != self.conditioning
            or estimate["evidence_ids"] != self.evidence_ids
            or estimate["status"] != self.estimate_status
            or estimate["includes"] != self.includes
        ):
            raise ValueError("flattened estimate identity differs from its source estimate")
        if bool(event["includes_recovery"]) != ("recovery" in self.includes):
            raise ValueError("recovery scope differs between the event and estimate")
        if bool(event["includes_timing"]) != ("timing" in self.includes):
            raise ValueError("timing scope differs between the event and estimate")
        if canonical_digest(event) != self.source_event_digest:
            raise ValueError("source human-failure event digest does not match its content")
        if canonical_digest(estimate) != self.source_estimate_digest:
            raise ValueError("source human-reliability estimate digest does not match its content")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("human-reliability limitations must be nonempty statements")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("human-reliability payload digest does not match its content")
        return self


def human_reliability_estimate_record(
    *,
    provider_id: str,
    provider_revision: str,
    assessment_input_digest: str,
    procedure_version: str,
    context_id: str,
    source_event: dict[str, Any],
    source_estimate: dict[str, Any],
    limitations: list[str],
) -> HumanReliabilityEstimateRecord:
    """Bind one provider event and estimate without changing its opportunity semantics."""

    payload = {
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "assessment_input_digest": assessment_input_digest,
        "task_id": source_event.get("task_id"),
        "procedure_version": procedure_version,
        "context_id": context_id,
        "event_id": source_event.get("id"),
        "step_ids": source_event.get("step_ids"),
        "role": source_event.get("role"),
        "failure_definition": source_event.get("failure_definition"),
        "opportunity_definition": source_event.get("opportunity_definition"),
        "conditioning": source_event.get("conditioning"),
        "dependency_group": source_event.get("dependency_group"),
        "method": source_estimate.get("method"),
        "probability_per_opportunity": source_estimate.get("probability"),
        "evidence_ids": source_estimate.get("evidence_ids"),
        "estimate_status": source_estimate.get("status"),
        "includes": source_estimate.get("includes"),
        "source_event": source_event,
        "source_estimate": source_estimate,
        "source_event_digest": canonical_digest(source_event),
        "source_estimate_digest": canonical_digest(source_estimate),
        "limitations": limitations,
    }
    unsigned = HumanReliabilityEstimateRecord.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return HumanReliabilityEstimateRecord.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )
