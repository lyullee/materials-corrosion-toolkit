"""Bind pinned-schema validation reports to deterministic exchange receipts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, canonical_digest
from .exchange_receipt import (
    CheckCategory,
    ExchangeCompatibilityCheck,
    ExchangeCompatibilityReceipt,
    ExchangeEndpoint,
    ExchangeFieldDecision,
    build_exchange_compatibility_receipt,
)
from .external_schema_audit import ExternalSchemaAuditRecord

FindingStatus = Literal["passed", "failed", "not_applicable"]
_CATEGORY_ORDER: tuple[CheckCategory, ...] = (
    "schema",
    "unit",
    "identity",
    "probability_semantics",
)


class PinnedSchemaPathFinding(Contract):
    finding_id: str = Field(min_length=1)
    category: CheckCategory
    path: str | None = None
    status: FindingStatus
    expected_descriptor: str | None = None
    observed_descriptor: str | None = None
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_finding(self):
        if self.status in {"passed", "failed"}:
            if self.path is None or not self.path.startswith("/"):
                raise ValueError("passed or failed pinned-schema findings require a JSON pointer path")
            if self.expected_descriptor is None or self.observed_descriptor is None:
                raise ValueError("passed or failed findings require expected and observed descriptors")
        elif self.expected_descriptor is not None or self.observed_descriptor is not None:
            raise ValueError("not-applicable findings cannot report expected or observed descriptors")
        if self.path is not None and not self.path.startswith("/"):
            raise ValueError("pinned-schema finding paths must be JSON pointers")
        return self


class PinnedSchemaValidationReport(Contract):
    schema_version: Literal["matintegrity.pinned_schema_validation_report.v1"] = (
        "matintegrity.pinned_schema_validation_report.v1"
    )
    report_id: str = Field(pattern=r"^pinned-schema-report-[a-f0-9]{64}$")
    schema_audit_id: str = Field(pattern=r"^external-schema-[a-f0-9]{64}$")
    schema_audit_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_repository_id: str = Field(min_length=1)
    schema_pinned_commit: str = Field(pattern=r"^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$")
    schema_repository_path: str = Field(min_length=1)
    schema_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_compatibility_summary_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    json_schema_id: str = Field(min_length=1)
    json_schema_version: str = Field(min_length=1)
    producer_payload_canonical_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    validator_id: str = Field(min_length=1)
    validator_revision: str = Field(min_length=1)
    validator_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_validation_status: Literal["valid", "invalid"]
    findings: tuple[PinnedSchemaPathFinding, ...]
    limitations: tuple[str, ...] = Field(min_length=1)
    network_download_performed: Literal[False] = False
    consumer_executed: Literal[False] = False
    end_to_end_qualification_claimed: Literal[False] = False
    physical_validation_claimed: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_id", "report_digest"})

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def coherent_and_bound(self, info: ValidationInfo):
        finding_ids = [row.finding_id for row in self.findings]
        if len(set(finding_ids)) != len(finding_ids):
            raise ValueError("pinned-schema finding identifiers must be unique")
        finding_keys = [(row.category, row.path) for row in self.findings]
        if len(set(finding_keys)) != len(finding_keys):
            raise ValueError("pinned-schema findings must be unique by category and path")
        if {row.category for row in self.findings} != set(_CATEGORY_ORDER):
            raise ValueError("pinned-schema report requires all compatibility-check categories")
        schema_findings = [row for row in self.findings if row.category == "schema"]
        expected_schema_status = (
            "invalid" if any(row.status == "failed" for row in schema_findings) else "valid"
        )
        if self.schema_validation_status != expected_schema_status:
            raise ValueError("schema validation status must match schema-category findings")
        if self.schema_validation_status == "valid" and not any(
            row.status == "passed" for row in schema_findings
        ):
            raise ValueError("valid schema reports require at least one passed schema finding")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("pinned-schema report limitations must be nonempty statements")
        if not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest")):
            expected_id = f"pinned-schema-report-{canonical_digest(self.identity_payload())}"
            if self.report_id != expected_id:
                raise ValueError("pinned-schema report identifier does not match canonical content")
            if self.report_digest != canonical_digest(self.digest_payload()):
                raise ValueError("pinned-schema report digest does not match canonical content")
        return self


def build_pinned_schema_validation_report(
    *,
    schema_audit: ExternalSchemaAuditRecord,
    producer_payload: Any,
    validator_id: str,
    validator_revision: str,
    validator_configuration_digest: str,
    findings: tuple[PinnedSchemaPathFinding | dict[str, Any], ...],
    limitations: tuple[str, ...],
) -> PinnedSchemaValidationReport:
    """Bind a caller-supplied validation report to pinned schema and payload digests."""

    normalized_findings = tuple(
        row if isinstance(row, PinnedSchemaPathFinding) else PinnedSchemaPathFinding.model_validate(row)
        for row in findings
    )
    schema_status = (
        "invalid"
        if any(row.category == "schema" and row.status == "failed" for row in normalized_findings)
        else "valid"
    )
    content = {
        "schema_audit_id": schema_audit.audit_id,
        "schema_audit_digest": schema_audit.audit_digest,
        "schema_repository_id": schema_audit.repository_id,
        "schema_pinned_commit": schema_audit.pinned_commit,
        "schema_repository_path": schema_audit.repository_path,
        "schema_content_sha256": schema_audit.content_sha256,
        "schema_compatibility_summary_digest": schema_audit.compatibility_summary_digest,
        "json_schema_id": schema_audit.json_schema_id,
        "json_schema_version": schema_audit.json_schema_version,
        "producer_payload_canonical_sha256": canonical_digest(producer_payload),
        "validator_id": validator_id,
        "validator_revision": validator_revision,
        "validator_configuration_digest": validator_configuration_digest,
        "schema_validation_status": schema_status,
        "findings": normalized_findings,
        "limitations": limitations,
    }
    unsigned = PinnedSchemaValidationReport.model_validate(
        {
            **content,
            "report_id": f"pinned-schema-report-{'0' * 64}",
            "report_digest": "0" * 64,
        },
        context={"allow_unbound_digest": True},
    )
    report_id = f"pinned-schema-report-{canonical_digest(unsigned.identity_payload())}"
    bound_id = PinnedSchemaValidationReport.model_validate(
        {**content, "report_id": report_id, "report_digest": "0" * 64},
        context={"allow_unbound_digest": True},
    )
    return PinnedSchemaValidationReport.model_validate(
        {
            **content,
            "report_id": report_id,
            "report_digest": canonical_digest(bound_id.digest_payload()),
        }
    )


def _aggregate_check(
    category: CheckCategory,
    findings: tuple[PinnedSchemaPathFinding, ...],
) -> ExchangeCompatibilityCheck:
    rows = tuple(row for row in findings if row.category == category)
    status: Literal["passed", "failed", "not_applicable"]
    if any(row.status == "failed" for row in rows):
        status = "failed"
    elif any(row.status == "passed" for row in rows):
        status = "passed"
    else:
        status = "not_applicable"
    paths = tuple(sorted({row.path for row in rows if row.path is not None}))
    expected = None
    observed = None
    if status != "not_applicable":
        active = sorted(
            (row for row in rows if row.status != "not_applicable"),
            key=lambda row: (row.path or "", row.finding_id),
        )
        expected = "; ".join(f"{row.path}={row.expected_descriptor}" for row in active)
        observed = "; ".join(f"{row.path}={row.observed_descriptor}" for row in active)
    basis = "; ".join(
        f"{row.finding_id}: {row.basis}" for row in sorted(rows, key=lambda row: row.finding_id)
    )
    return ExchangeCompatibilityCheck(
        check_id=f"pinned-{category.replace('_', '-')}-check",
        category=category,
        status=status,
        paths=paths,
        expected_descriptor=expected,
        observed_descriptor=observed,
        basis=basis,
    )


def build_pinned_exchange_validation_receipt(
    *,
    producer_payload: Any,
    schema_audit: ExternalSchemaAuditRecord,
    validation_report: PinnedSchemaValidationReport,
    producer: ExchangeEndpoint | dict[str, Any],
    consumer: ExchangeEndpoint | dict[str, Any],
    compatibility_scope: str,
    limitations: tuple[str, ...],
) -> ExchangeCompatibilityReceipt:
    """Create a compatibility receipt without executing the consumer or schema provider."""

    producer_endpoint = (
        producer if isinstance(producer, ExchangeEndpoint) else ExchangeEndpoint.model_validate(producer)
    )
    consumer_endpoint = (
        consumer if isinstance(consumer, ExchangeEndpoint) else ExchangeEndpoint.model_validate(consumer)
    )
    audit_identity = (
        schema_audit.audit_id,
        schema_audit.audit_digest,
        schema_audit.repository_id,
        schema_audit.pinned_commit.lower(),
        schema_audit.repository_path,
        schema_audit.content_sha256,
        schema_audit.compatibility_summary_digest,
        schema_audit.json_schema_id,
        schema_audit.json_schema_version,
    )
    report_identity = (
        validation_report.schema_audit_id,
        validation_report.schema_audit_digest,
        validation_report.schema_repository_id,
        validation_report.schema_pinned_commit.lower(),
        validation_report.schema_repository_path,
        validation_report.schema_content_sha256,
        validation_report.schema_compatibility_summary_digest,
        validation_report.json_schema_id,
        validation_report.json_schema_version,
    )
    if report_identity != audit_identity:
        raise ValueError("pinned validation report does not match external schema audit identity")
    if canonical_digest(producer_payload) != validation_report.producer_payload_canonical_sha256:
        raise ValueError("producer payload digest does not match pinned validation report")
    if (
        consumer_endpoint.repository_id != schema_audit.repository_id
        or consumer_endpoint.provider_commit.lower() != schema_audit.pinned_commit.lower()
    ):
        raise ValueError("consumer repository and commit must match the pinned external schema audit")
    if (
        consumer_endpoint.schema_id != schema_audit.json_schema_id
        or consumer_endpoint.schema_version != schema_audit.json_schema_version
    ):
        raise ValueError("consumer schema identity and version must match the pinned audit")

    checks = tuple(_aggregate_check(category, validation_report.findings) for category in _CATEGORY_ORDER)
    checks_by_category = {row.category: row for row in checks}
    paths = sorted({path for check in checks for path in check.paths})
    field_decisions = []
    for path in paths:
        categories = tuple(
            category for category in _CATEGORY_ORDER if path in checks_by_category[category].paths
        )
        rejected = any(checks_by_category[category].status == "failed" for category in categories)
        field_decisions.append(
            ExchangeFieldDecision(
                path=path,
                status="rejected" if rejected else "accepted",
                check_categories=categories,
                basis=(
                    "at least one applicable pinned compatibility category failed"
                    if rejected
                    else "all applicable pinned compatibility categories passed or were not applicable"
                ),
            )
        )
    receipt_limitations = (
        *limitations,
        "Schema-report compatibility is not end-to-end execution or physical qualification.",
        "The consumer and external schema repository were not executed by this builder.",
    )
    return build_exchange_compatibility_receipt(
        producer=producer_endpoint,
        consumer=consumer_endpoint,
        payload=producer_payload,
        configuration_digest=validation_report.validator_configuration_digest,
        checks=checks,
        field_decisions=tuple(field_decisions),
        compatibility_scope=compatibility_scope,
        limitations=receipt_limitations,
    )
