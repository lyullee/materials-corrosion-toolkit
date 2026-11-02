"""Build a deterministic metadata and source-archive boundary audit for dataset rights."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "catalogs" / "datasets.json"
MANIFEST = ROOT / "MANIFEST.in"
OUTPUT = ROOT / "data" / "catalogs" / "dataset_release_rights_audit.json"

REQUIRED_DATASET_FIELDS = (
    "id", "title", "category", "citation", "license", "license_url",
    "rights_evidence_url", "rights_status", "acquisition_policy", "checked_on",
    "limitations", "assets",
)
CHECKSUM_PATTERNS = {
    "md5": re.compile(r"^[a-fA-F0-9]{32}$"),
    "sha256": re.compile(r"^[a-fA-F0-9]{64}$"),
    "git-blob-sha1": re.compile(r"^[a-fA-F0-9]{40}$"),
}


def _is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _check_manifest(manifest_text: str) -> dict:
    directives = {line.strip() for line in manifest_text.splitlines() if line.strip()}
    expected_prunes = ("data/raw", "data/derived", "data/evidence")
    prune_rows = {
        name: f"prune {name}" in directives
        for name in expected_prunes
    }
    catalog_rule = "recursive-include data/catalogs *.json" in directives
    required_payload_metadata = all(
        directive in directives
        for directive in (
            "include data/acquisition_log.json data/data_inventory.json",
            "include README.md LICENSE THIRD_PARTY_NOTICES.md .gitignore setup.py",
        )
    )
    return {
        "manifest_sha256": hashlib.sha256(manifest_text.encode("utf-8")).hexdigest(),
        "dataset_catalog_json_included_by_declared_rule": catalog_rule,
        "raw_derived_evidence_prune_directives": prune_rows,
        "all_three_restricted_data_roots_declared_pruned": all(prune_rows.values()),
        "acquisition_and_inventory_metadata_declared_included": required_payload_metadata,
        "interpretation": "declared_MANIFEST_rules_only; source_archive_and_wheel_contents_not_built_or_inspected",
    }


def build_report() -> dict:
    source_bytes = SOURCE.read_bytes()
    catalog = json.loads(source_bytes.decode("utf-8"))
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    datasets = catalog.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("dataset catalog must contain a datasets array")
    if catalog.get("schema") != "matintegrity.datasets.v1":
        raise ValueError("unsupported or missing dataset catalog schema identifier")

    ids = [row.get("id") for row in datasets if isinstance(row, dict)]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if key and count > 1)
    errors: list[dict] = []
    warnings: list[dict] = []
    rows: list[dict] = []
    checksum_algorithm_counts: Counter[str] = Counter()
    rights_status_counts: Counter[str] = Counter()
    acquisition_policy_counts: Counter[str] = Counter()
    asset_count = 0
    missing_checksum_count = 0
    duplicate_asset_names: dict[str, list[str]] = {}
    asset_owners: dict[str, list[str]] = {}

    for index, row in enumerate(datasets):
        if not isinstance(row, dict):
            errors.append({"record_index": index, "issue": "dataset_record_not_object"})
            continue
        dataset_id = row.get("id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append({"record_index": index, "issue": "missing_dataset_id"})
            dataset_id = f"<record:{index}>"
        missing_fields = [key for key in REQUIRED_DATASET_FIELDS if key not in row]
        for key in missing_fields:
            errors.append({"dataset_id": dataset_id, "issue": "required_field_missing", "field": key})
        for key in ("id", "title", "category", "citation", "license", "rights_status", "acquisition_policy", "checked_on"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append({"dataset_id": dataset_id, "issue": "required_text_field_empty_or_invalid", "field": key})
        if not isinstance(row.get("limitations"), list) or any(not isinstance(value, str) for value in row["limitations"]):
            errors.append({"dataset_id": dataset_id, "issue": "limitations_must_be_an_array_of_text"})

        rights_status = row.get("rights_status")
        acquisition_policy = row.get("acquisition_policy")
        rights_status_counts[str(rights_status)] += 1
        acquisition_policy_counts[str(acquisition_policy)] += 1
        if not _is_https_url(row.get("license_url")):
            warnings.append({"dataset_id": dataset_id, "issue": "license_url_not_https_or_missing"})
        if not _is_https_url(row.get("rights_evidence_url")):
            warnings.append({"dataset_id": dataset_id, "issue": "rights_evidence_url_not_https_or_missing"})
        if acquisition_policy not in {"allowed", "allowed_selected_assets", "allowed_selected_text_assets", "metadata_only", "do_not_download"}:
            warnings.append({"dataset_id": dataset_id, "issue": "unrecognized_acquisition_policy", "value": acquisition_policy})

        assets = row.get("assets")
        if not isinstance(assets, list):
            errors.append({"dataset_id": dataset_id, "issue": "assets_not_array"})
            assets = []
        asset_rows = []
        for asset_index, asset in enumerate(assets):
            asset_count += 1
            if not isinstance(asset, dict):
                errors.append({"dataset_id": dataset_id, "asset_index": asset_index, "issue": "asset_not_object"})
                continue
            filename = asset.get("filename")
            if not isinstance(filename, str) or not filename.strip():
                errors.append({"dataset_id": dataset_id, "asset_index": asset_index, "issue": "asset_filename_missing"})
                filename = ""
            parsed_name = PurePosixPath(filename.replace("\\", "/"))
            if parsed_name.is_absolute() or ".." in parsed_name.parts or len(parsed_name.parts) != 1:
                errors.append({"dataset_id": dataset_id, "asset_index": asset_index, "issue": "asset_filename_not_basename", "filename": filename})
            if filename:
                asset_owners.setdefault(filename, []).append(dataset_id)

            checksum = asset.get("checksum")
            checksum_status = "not_provided"
            if checksum is None or checksum == "":
                missing_checksum_count += 1
                warnings.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_checksum_not_provided"})
            elif isinstance(checksum, str) and ":" in checksum:
                algorithm, digest = checksum.split(":", 1)
                matcher = CHECKSUM_PATTERNS.get(algorithm.lower())
                if matcher is None:
                    checksum_status = "unrecognized_algorithm"
                    warnings.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_checksum_algorithm_unrecognized", "algorithm": algorithm})
                elif not matcher.fullmatch(digest):
                    checksum_status = "invalid_digest_format"
                    errors.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_checksum_invalid_digest_format", "algorithm": algorithm})
                else:
                    checksum_status = "format_valid"
                    checksum_algorithm_counts[algorithm.lower()] += 1
            else:
                checksum_status = "invalid_format"
                errors.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_checksum_missing_algorithm_prefix"})

            asset_url = asset.get("url")
            if not _is_https_url(asset_url):
                warnings.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_url_not_https_or_missing"})
            byte_count = asset.get("bytes")
            if byte_count is None:
                warnings.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_byte_count_not_pinned"})
            elif isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
                errors.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_byte_count_invalid"})
            default_flag = asset.get("default")
            if default_flag is not None and not isinstance(default_flag, bool):
                errors.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_default_flag_not_boolean"})
            max_bytes = asset.get("max_bytes")
            if max_bytes is not None and (isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0):
                errors.append({"dataset_id": dataset_id, "filename": filename, "issue": "asset_max_bytes_invalid"})
            asset_rows.append({
                "filename": filename,
                "url": asset_url,
                "checksum": checksum,
                "checksum_format_status": checksum_status,
                "bytes": asset.get("bytes"),
                "asset_redistribution_conclusion": "not_inferred_from_dataset_catalog_or_public_access",
            })

        if rights_status == "not_approved_for_redistribution":
            redistribution_conclusion = "not_approved_for_redistribution"
        else:
            redistribution_conclusion = "not_assessed_by_this_audit"
        rows.append({
            "id": dataset_id,
            "title": row.get("title"),
            "citation": row.get("citation"),
            "license": row.get("license"),
            "license_url": row.get("license_url"),
            "rights_evidence_url": row.get("rights_evidence_url"),
            "rights_status": rights_status,
            "acquisition_policy": acquisition_policy,
            "checked_on": row.get("checked_on"),
            "limitations": row.get("limitations"),
            "assets": asset_rows,
            "redistribution_conclusion": redistribution_conclusion,
            "rights_interpretation": "Acquisition policy, public accessibility, and a dataset-level license declaration do not by themselves establish redistribution rights for underlying observations or third-party content.",
        })

    for filename, owners in sorted(asset_owners.items()):
        if len(owners) > 1:
            duplicate_asset_names[filename] = sorted(owners)
            warnings.append({"filename": filename, "dataset_ids": sorted(owners), "issue": "filename_reused_across_dataset_records"})

    if duplicate_ids:
        errors.append({"issue": "duplicate_dataset_ids", "dataset_ids": duplicate_ids})
    manifest_audit = _check_manifest(manifest_text)
    for key in ("dataset_catalog_json_included_by_declared_rule", "all_three_restricted_data_roots_declared_pruned", "acquisition_and_inventory_metadata_declared_included"):
        if not manifest_audit[key]:
            errors.append({"issue": "manifest_boundary_rule_missing", "rule": key})

    return {
        "schema_version": "matintegrity.dataset_release_rights_audit.v1",
        "dataset_catalog_schema": catalog.get("schema"),
        "dataset_catalog_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "dataset_count": len(datasets),
        "asset_count": asset_count,
        "rights_status_counts": dict(sorted(rights_status_counts.items())),
        "acquisition_policy_counts": dict(sorted(acquisition_policy_counts.items())),
        "asset_checksum_algorithm_counts": dict(sorted(checksum_algorithm_counts.items())),
        "assets_without_checksum_count": missing_checksum_count,
        "duplicate_dataset_ids": duplicate_ids,
        "duplicate_asset_filenames_across_records": duplicate_asset_names,
        "manifest_boundary": manifest_audit,
        "redistribution_policy": "This report records source declarations and archive rules; it never grants redistribution permission or resolves underlying observation rights.",
        "errors": errors,
        "warnings": warnings,
        "datasets": rows,
    }


def main() -> None:
    report = build_report()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"datasets={report['dataset_count']} assets={report['asset_count']} "
        f"errors={len(report['errors'])} warnings={len(report['warnings'])} "
        f"raw_pruned={report['manifest_boundary']['raw_derived_evidence_prune_directives']}"
    )
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
