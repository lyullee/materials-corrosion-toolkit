"""Provider-neutral receipt for pipeline assessment results without acceptance relabelling."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, canonical_digest, check_finite

RESULT_FIELDS = {
    "schema_version",
    "model_id",
    "model_version",
    "status",
    "inputs",
    "values",
    "input_units",
    "output_units",
    "assumptions",
    "notes",
    "source_ids",
    "context",
    "input_digest",
    "model_source_digest",
    "runtime",
    "qualification",
}
CONTEXT_FIELDS = {"asset_id", "scenario_id", "clock_id", "origin", "evidence", "metadata"}


class PipelineAssessmentRecord(Contract):
    """One complete pipeline result bound to provider source and operating context."""

    schema_version: Literal["matintegrity.pipeline_assessment.v1"] = "matintegrity.pipeline_assessment.v1"
    provider_id: str = Field(min_length=1)
    provider_package_version: str = Field(min_length=1)
    provider_source_tree_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_source_file_count: int = Field(gt=0)
    source_schema_version: Literal["pipeline_integrity.result.v1"] = "pipeline_integrity.result.v1"
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    status: Literal["computed", "out_of_scope", "needs_data"]
    asset_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    origin: Literal["measured", "laboratory", "simulation", "user_declared", "synthetic"]
    input_units: dict[str, str]
    output_units: dict[str, str]
    qualification: Literal["engineering_screening", "user_model"]
    source_result: dict[str, Any]
    source_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    field_or_design_acceptance_claim: Literal[False] = False
    limitations: list[str] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def aligned_and_bound(self, info: ValidationInfo):
        if set(self.source_result) != RESULT_FIELDS:
            raise ValueError("source pipeline result must use the reviewed provider field set")
        check_finite(self.source_result)
        source = self.source_result
        context = source.get("context")
        if not isinstance(context, dict) or set(context) != CONTEXT_FIELDS:
            raise ValueError("source pipeline context must use the reviewed provider field set")
        if (
            source["schema_version"] != self.source_schema_version
            or source["model_id"] != self.model_id
            or source["model_version"] != self.model_version
            or source["status"] != self.status
            or source["input_units"] != self.input_units
            or source["output_units"] != self.output_units
            or source["qualification"] != self.qualification
            or context["asset_id"] != self.asset_id
            or context["scenario_id"] != self.scenario_id
            or context["clock_id"] != self.clock_id
            or context["origin"] != self.origin
        ):
            raise ValueError("flattened pipeline identity, units or context differs from its source result")
        evidence = context["evidence"]
        if not isinstance(evidence, list) or any(not isinstance(row, dict) for row in evidence):
            raise ValueError("source pipeline evidence must be a JSON array of objects")
        evidence_ids = [row.get("id") for row in evidence]
        if any(not isinstance(value, str) or not value.strip() for value in evidence_ids):
            raise ValueError("source pipeline evidence IDs must be nonempty strings")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("source pipeline evidence IDs must be unique")
        if canonical_digest(source) != self.source_result_digest:
            raise ValueError("source pipeline result digest does not match its content")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("pipeline exchange limitations must be nonempty statements")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("pipeline assessment payload digest does not match its content")
        return self


def pipeline_assessment_record(
    *,
    provider_id: str,
    provider_package_version: str,
    provider_source_tree_sha256: str,
    provider_source_file_count: int,
    source_result: dict[str, Any],
    limitations: list[str],
) -> PipelineAssessmentRecord:
    """Bind a provider result without treating screening output as design acceptance."""

    context = source_result.get("context", {})
    payload = {
        "provider_id": provider_id,
        "provider_package_version": provider_package_version,
        "provider_source_tree_sha256": provider_source_tree_sha256,
        "provider_source_file_count": provider_source_file_count,
        "source_schema_version": source_result.get("schema_version"),
        "model_id": source_result.get("model_id"),
        "model_version": source_result.get("model_version"),
        "status": source_result.get("status"),
        "asset_id": context.get("asset_id"),
        "scenario_id": context.get("scenario_id"),
        "clock_id": context.get("clock_id"),
        "origin": context.get("origin"),
        "input_units": source_result.get("input_units"),
        "output_units": source_result.get("output_units"),
        "qualification": source_result.get("qualification"),
        "source_result": source_result,
        "source_result_digest": canonical_digest(source_result),
        "limitations": limitations,
    }
    unsigned = PipelineAssessmentRecord.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return PipelineAssessmentRecord.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )
