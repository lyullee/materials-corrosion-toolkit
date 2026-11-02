"""Deterministic receipts for reviewed JSON handoffs between repositories."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, canonical_digest, check_finite

CheckCategory = Literal["schema", "unit", "identity", "probability_semantics"]
CheckStatus = Literal["passed", "failed", "not_applicable"]
DecisionStatus = Literal["accepted", "rejected"]


class ExchangeEndpoint(Contract):
    repository_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_commit: str = Field(pattern=r"^[a-fA-F0-9]{7,64}$")
    provider_revision: str = Field(min_length=1)


class ExchangeCompatibilityCheck(Contract):
    check_id: str = Field(min_length=1)
    category: CheckCategory
    status: CheckStatus
    paths: tuple[str, ...]
    expected_descriptor: str | None = None
    observed_descriptor: str | None = None
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_check(self):
        if len(set(self.paths)) != len(self.paths):
            raise ValueError("compatibility-check paths must be unique")
        if any(not _is_json_pointer(path) for path in self.paths):
            raise ValueError("compatibility-check paths must be non-root RFC 6901 JSON pointers")
        if self.status in {"passed", "failed"}:
            if not self.paths:
                raise ValueError("passed or failed compatibility checks require at least one path")
            if self.expected_descriptor is None or self.observed_descriptor is None:
                raise ValueError("passed or failed checks require expected and observed descriptors")
        elif self.expected_descriptor is not None or self.observed_descriptor is not None:
            raise ValueError("not-applicable checks cannot report expected or observed descriptors")
        return self


class ExchangeFieldDecision(Contract):
    path: str
    status: DecisionStatus
    check_categories: tuple[CheckCategory, ...] = Field(min_length=1)
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_path_and_categories(self):
        if not _is_json_pointer(self.path):
            raise ValueError("exchange field paths must be non-root RFC 6901 JSON pointers")
        if len(set(self.check_categories)) != len(self.check_categories):
            raise ValueError("field-decision check categories must be unique")
        return self


class ExchangeCompatibilityReceipt(Contract):
    """Digest-bound evidence of declared JSON compatibility checks.

    The receipt records review outcomes only.  It is not a signature, transport
    acknowledgement, physical validation, or proof that either repository ran.
    """

    schema_version: Literal["matintegrity.exchange_compatibility_receipt.v1"] = (
        "matintegrity.exchange_compatibility_receipt.v1"
    )
    receipt_id: str = Field(pattern=r"^exchange-[a-f0-9]{64}$")
    producer: ExchangeEndpoint
    consumer: ExchangeEndpoint
    payload_canonical_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["accepted", "rejected"]
    checks: tuple[ExchangeCompatibilityCheck, ...]
    field_decisions: tuple[ExchangeFieldDecision, ...] = Field(min_length=1)
    accepted_paths: tuple[str, ...]
    rejected_paths: tuple[str, ...]
    compatibility_scope: str = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)
    signature_verified: Literal[False] = False
    network_transfer_executed: Literal[False] = False
    cross_repository_execution_claimed: Literal[False] = False
    physical_validation_claimed: Literal[False] = False
    receipt_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"receipt_id", "receipt_digest"})

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"receipt_digest"})

    @model_validator(mode="after")
    def coherent_and_bound(self, info: ValidationInfo):
        categories = [row.category for row in self.checks]
        required_categories = {"schema", "unit", "identity", "probability_semantics"}
        if len(categories) != len(set(categories)):
            raise ValueError("compatibility-check categories must be unique")
        if set(categories) != required_categories:
            raise ValueError(
                "receipt requires exactly schema, unit, identity and probability-semantics checks"
            )
        check_ids = [row.check_id for row in self.checks]
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("compatibility-check identifiers must be unique")
        decision_paths = [row.path for row in self.field_decisions]
        if len(decision_paths) != len(set(decision_paths)):
            raise ValueError("each JSON path must have exactly one field decision")
        accepted = tuple(sorted(row.path for row in self.field_decisions if row.status == "accepted"))
        rejected = tuple(sorted(row.path for row in self.field_decisions if row.status == "rejected"))
        if self.accepted_paths != accepted or self.rejected_paths != rejected:
            raise ValueError("accepted and rejected path summaries must match field decisions")
        checks_by_category = {row.category: row for row in self.checks}
        for decision in self.field_decisions:
            for category in decision.check_categories:
                check = checks_by_category[category]
                if decision.path not in check.paths:
                    raise ValueError("field-decision paths must be covered by their declared checks")
                if decision.status == "rejected" and check.status != "failed":
                    raise ValueError("rejected field decisions must correspond to failed checks")
                if decision.status == "accepted" and check.status == "failed":
                    raise ValueError("accepted field decisions cannot correspond to failed checks")
        for check in self.checks:
            if check.status == "failed" and not any(
                row.status == "rejected"
                and check.category in row.check_categories
                and row.path in check.paths
                for row in self.field_decisions
            ):
                raise ValueError("each failed check requires a corresponding rejected field path")
        expected_status = (
            "rejected" if rejected or any(row.status == "failed" for row in self.checks) else "accepted"
        )
        if self.status != expected_status:
            raise ValueError("receipt status must be derived from checks and field decisions")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("exchange receipt limitations must be nonempty statements")
        if not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest")):
            expected_id = f"exchange-{canonical_digest(self.identity_payload())}"
            if self.receipt_id != expected_id:
                raise ValueError("exchange receipt identifier does not match canonical content")
            if self.receipt_digest != canonical_digest(self.digest_payload()):
                raise ValueError("exchange receipt digest does not match canonical content")
        return self


def _is_json_pointer(path: str) -> bool:
    if not path.startswith("/"):
        return False
    tokens = path[1:].split("/")
    return all(_valid_pointer_token(token) for token in tokens)


def _valid_pointer_token(token: str) -> bool:
    index = 0
    while index < len(token):
        if token[index] == "~":
            if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
                return False
            index += 2
        else:
            index += 1
    return True


def _resolve_json_pointer(payload: Any, path: str) -> Any:
    if not _is_json_pointer(path):
        raise ValueError(f"invalid JSON pointer: {path!r}")
    current = payload
    for encoded in path[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(f"JSON pointer does not resolve in payload: {path!r}")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise ValueError(f"JSON pointer list index is invalid: {path!r}")
            index = int(token)
            if index >= len(current):
                raise ValueError(f"JSON pointer does not resolve in payload: {path!r}")
            current = current[index]
        else:
            raise ValueError(f"JSON pointer traverses a scalar payload value: {path!r}")
    return current


def build_exchange_compatibility_receipt(
    *,
    producer: ExchangeEndpoint | dict[str, Any],
    consumer: ExchangeEndpoint | dict[str, Any],
    payload: Any,
    configuration_digest: str,
    checks: tuple[ExchangeCompatibilityCheck | dict[str, Any], ...],
    field_decisions: tuple[ExchangeFieldDecision | dict[str, Any], ...],
    compatibility_scope: str,
    limitations: tuple[str, ...],
) -> ExchangeCompatibilityReceipt:
    """Build a deterministic receipt without signing, networking or executing a repository."""

    check_finite(payload)
    payload_digest = canonical_digest(payload)
    normalized_checks = tuple(
        row if isinstance(row, ExchangeCompatibilityCheck) else ExchangeCompatibilityCheck.model_validate(row)
        for row in checks
    )
    normalized_decisions = tuple(
        row if isinstance(row, ExchangeFieldDecision) else ExchangeFieldDecision.model_validate(row)
        for row in field_decisions
    )
    for path in {path for row in normalized_checks for path in row.paths} | {
        row.path for row in normalized_decisions
    }:
        _resolve_json_pointer(payload, path)
    accepted_paths = tuple(sorted(row.path for row in normalized_decisions if row.status == "accepted"))
    rejected_paths = tuple(sorted(row.path for row in normalized_decisions if row.status == "rejected"))
    status = (
        "rejected"
        if rejected_paths or any(row.status == "failed" for row in normalized_checks)
        else "accepted"
    )
    content = {
        "producer": producer,
        "consumer": consumer,
        "payload_canonical_sha256": payload_digest,
        "configuration_digest": configuration_digest,
        "status": status,
        "checks": normalized_checks,
        "field_decisions": normalized_decisions,
        "accepted_paths": accepted_paths,
        "rejected_paths": rejected_paths,
        "compatibility_scope": compatibility_scope,
        "limitations": limitations,
    }
    unsigned = ExchangeCompatibilityReceipt.model_validate(
        {
            **content,
            "receipt_id": f"exchange-{'0' * 64}",
            "receipt_digest": "0" * 64,
        },
        context={"allow_unbound_digest": True},
    )
    receipt_id = f"exchange-{canonical_digest(unsigned.identity_payload())}"
    bound_id = ExchangeCompatibilityReceipt.model_validate(
        {**content, "receipt_id": receipt_id, "receipt_digest": "0" * 64},
        context={"allow_unbound_digest": True},
    )
    return ExchangeCompatibilityReceipt.model_validate(
        {
            **content,
            "receipt_id": receipt_id,
            "receipt_digest": canonical_digest(bound_id.digest_payload()),
        }
    )
