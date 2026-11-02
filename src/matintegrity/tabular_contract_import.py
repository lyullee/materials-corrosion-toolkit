"""Declarative CSV/JSONL mapping into public contracts without code evaluation or unit inference."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import Field, model_validator

from .contracts import Contract, canonical_digest

T = TypeVar("T", bound=Contract)
ValueType = Literal["string", "integer", "number", "boolean", "json", "json_tuple"]


class TabularFieldMapping(Contract):
    target_path: tuple[str, ...] = Field(min_length=1)
    source_path: tuple[str, ...] | None = Field(default=None, min_length=1)
    constant_value: Any | None = None
    value_type: ValueType = "string"
    required: bool = True
    empty_as_missing: bool = True

    @model_validator(mode="after")
    def exactly_one_source(self):
        if (self.source_path is None) == (self.constant_value is None):
            raise ValueError("mapping requires exactly one source_path or non-null constant_value")
        if any(not part or part in {".", ".."} for part in self.target_path):
            raise ValueError("target path components must be nonempty field names")
        return self


class TabularImportProfile(Contract):
    schema_version: Literal["matintegrity.tabular_import_profile.v1"] = (
        "matintegrity.tabular_import_profile.v1"
    )
    profile_id: str = Field(min_length=1)
    target_contract: str = Field(min_length=1)
    mappings: tuple[TabularFieldMapping, ...] = Field(min_length=1)
    delimiter: str = Field(default=",", min_length=1, max_length=1)
    allow_unmapped_source_fields: bool = False
    expected_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    expected_target_schema_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def unique_targets(self):
        targets = [row.target_path for row in self.mappings]
        if len(targets) != len(set(targets)):
            raise ValueError("mapping target paths must be unique")
        for left in targets:
            for right in targets:
                if left != right and len(left) < len(right) and right[: len(left)] == left:
                    raise ValueError("mapping target paths cannot be scalar/object prefixes")
        return self


class TabularRowFinding(Contract):
    row_number: int = Field(ge=1)
    status: Literal["imported", "rejected"]
    issue_paths: tuple[str, ...] = ()


class TabularImportReport(Contract):
    schema_version: Literal["matintegrity.tabular_import_report.v1"] = "matintegrity.tabular_import_report.v1"
    profile_id: str
    target_contract: str
    source_format: Literal["csv", "jsonl"]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    profile_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_schema_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    total_rows: int = Field(ge=0)
    imported_rows: int = Field(ge=0)
    rejected_rows: int = Field(ge=0)
    findings: tuple[TabularRowFinding, ...]
    imported_records_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    unit_conversion_performed: Literal[False] = False
    code_evaluation_performed: Literal[False] = False


def _lookup(record: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    value: Any = record
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _convert(value: Any, kind: ValueType) -> Any:
    if kind == "string":
        if not isinstance(value, str):
            raise ValueError("expected string")
        return value
    if kind == "integer":
        if isinstance(value, bool):
            raise ValueError("boolean is not an integer input")
        return int(value) if isinstance(value, str) else value
    if kind == "number":
        if isinstance(value, bool):
            raise ValueError("boolean is not a numeric input")
        return float(value) if isinstance(value, str) else value
    if kind == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        raise ValueError("boolean text must be true or false")
    parsed = json.loads(value) if isinstance(value, str) else value
    if kind == "json_tuple":
        if not isinstance(parsed, (list, tuple)):
            raise ValueError("JSON tuple input must be an array")
        return tuple(parsed)
    return parsed


def _assign(payload: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor = payload
    for part in path[:-1]:
        existing = cursor.setdefault(part, {})
        if not isinstance(existing, dict):
            raise ValueError("target paths collide at a scalar field")
        cursor = existing
    cursor[path[-1]] = value


def _import_records(
    records: list[dict[str, Any]],
    contract_type: type[T],
    profile: TabularImportProfile,
    *,
    source_format: Literal["csv", "jsonl"],
    source_sha256: str,
) -> tuple[tuple[T, ...], TabularImportReport]:
    if contract_type.__name__ != profile.target_contract:
        raise ValueError("profile target_contract does not match requested contract type")
    target_schema_digest = canonical_digest(contract_type.model_json_schema())
    if (
        profile.expected_target_schema_digest is not None
        and profile.expected_target_schema_digest != target_schema_digest
    ):
        raise ValueError("target contract schema digest does not match the profile expectation")
    imported: list[T] = []
    findings = []
    mapped_top_level = {row.source_path[0] for row in profile.mappings if row.source_path}
    for row_number, record in enumerate(records, 1):
        issues: set[str] = set()
        if not profile.allow_unmapped_source_fields:
            issues.update(f"source.{key}" for key in record if key not in mapped_top_level)
        payload: dict[str, Any] = {}
        for mapping in profile.mappings:
            present, value = (
                (True, mapping.constant_value)
                if mapping.source_path is None
                else _lookup(record, mapping.source_path)
            )
            if present and mapping.empty_as_missing and value == "":
                present = False
            target_name = ".".join(mapping.target_path)
            if not present:
                if mapping.required:
                    issues.add(target_name)
                continue
            try:
                _assign(payload, mapping.target_path, _convert(value, mapping.value_type))
            except (TypeError, ValueError, json.JSONDecodeError):
                issues.add(target_name)
        if not issues:
            try:
                # Mapped tabular values are JSON-native; validate them in JSON mode so
                # arrays remain accepted for tuple-backed public contracts.
                imported.append(contract_type.model_validate_json(json.dumps(payload, allow_nan=False)))
            except ValueError as error:
                for item in error.errors():
                    issues.add(".".join(str(part) for part in item["loc"]) or "<record>")
        status = "rejected" if issues else "imported"
        findings.append(
            TabularRowFinding(row_number=row_number, status=status, issue_paths=tuple(sorted(issues)))
        )
    record_payload = [row.model_dump(mode="json") for row in imported]
    report = TabularImportReport(
        profile_id=profile.profile_id,
        target_contract=profile.target_contract,
        source_format=source_format,
        source_sha256=source_sha256,
        profile_digest=canonical_digest(profile.model_dump(mode="json")),
        target_schema_digest=target_schema_digest,
        total_rows=len(records),
        imported_rows=len(imported),
        rejected_rows=len(records) - len(imported),
        findings=tuple(findings),
        imported_records_digest=canonical_digest(record_payload),
    )
    return tuple(imported), report


def read_csv_contracts(
    path: str | Path, contract_type: type[T], profile: TabularImportProfile
) -> tuple[tuple[T, ...], TabularImportReport]:
    raw = Path(path).read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    if profile.expected_source_sha256 is not None and profile.expected_source_sha256 != source_sha256:
        raise ValueError("source SHA-256 does not match the profile expectation")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=profile.delimiter, strict=True)
    if (
        reader.fieldnames is None
        or any(not name for name in reader.fieldnames)
        or len(reader.fieldnames) != len(set(reader.fieldnames))
    ):
        raise ValueError("CSV requires one nonempty, non-duplicate header row")
    records = [dict(row) for row in reader]
    return _import_records(
        records,
        contract_type,
        profile,
        source_format="csv",
        source_sha256=source_sha256,
    )


def read_jsonl_contracts(
    path: str | Path, contract_type: type[T], profile: TabularImportProfile
) -> tuple[tuple[T, ...], TabularImportReport]:
    raw = Path(path).read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    if profile.expected_source_sha256 is not None and profile.expected_source_sha256 != source_sha256:
        raise ValueError("source SHA-256 does not match the profile expectation")
    records = []
    for line_number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_number} must contain one object")
        records.append(value)
    return _import_records(
        records,
        contract_type,
        profile,
        source_format="jsonl",
        source_sha256=source_sha256,
    )
