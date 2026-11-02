"""Audit release-rights metadata without claiming a legal clearance."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION_POLICIES = {
    "allowed",
    "allowed_selected_assets",
    "allowed_selected_text_assets",
    "metadata_only",
    "do_not_download",
}
CHECKSUM = re.compile(r"^(?:sha256|md5|git-blob-sha1):[a-f0-9]+$")


def _https(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def audit_rights_metadata(
    datasets: dict,
    sources: dict,
    *,
    as_of: date | None = None,
    freshness_days: int = 365,
) -> dict:
    if isinstance(freshness_days, bool) or not isinstance(freshness_days, int) or freshness_days < 0:
        raise ValueError("freshness_days must be a nonnegative integer")
    review_date = as_of or date.today()
    findings: list[dict] = []
    stale_reviews: list[dict] = []

    def issue(kind: str, identifier: str, field: str, detail: str) -> None:
        findings.append({"kind": kind, "id": identifier, "field": field, "detail": detail})

    dataset_rows = datasets.get("datasets")
    source_rows = sources.get("sources")
    if not isinstance(dataset_rows, list) or not isinstance(source_rows, list):
        raise ValueError("dataset and source catalogs must contain arrays")
    dataset_ids = [row.get("id") for row in dataset_rows]
    source_ids = [row.get("id") for row in source_rows]
    for kind, identifiers in (("dataset", dataset_ids), ("source", source_ids)):
        duplicates = sorted({value for value in identifiers if value and identifiers.count(value) > 1})
        for identifier in duplicates:
            issue(kind, identifier, "id", "duplicate identifier")

    for row in dataset_rows:
        identifier = row.get("id") or "<missing>"
        for field in (
            "id",
            "title",
            "category",
            "citation",
            "license",
            "license_url",
            "rights_evidence_url",
            "rights_status",
            "acquisition_policy",
            "checked_on",
        ):
            if not isinstance(row.get(field), str) or not row[field].strip():
                issue("dataset", identifier, field, "required nonempty string is missing")
        checked_on = row.get("checked_on")
        if isinstance(checked_on, str) and checked_on.strip():
            try:
                checked_date = date.fromisoformat(checked_on)
            except ValueError:
                issue("dataset", identifier, "checked_on", "must be a valid ISO calendar date")
            else:
                age_days = (review_date - checked_date).days
                if age_days < 0:
                    issue("dataset", identifier, "checked_on", "review date cannot be in the future")
                elif age_days > freshness_days:
                    stale_reviews.append({"id": identifier, "checked_on": checked_on, "age_days": age_days})
        for field in ("license_url", "rights_evidence_url"):
            value = row.get(field)
            if isinstance(value, str) and not _https(value):
                issue("dataset", identifier, field, "must be an HTTPS URL without credentials")
        policy = row.get("acquisition_policy")
        if policy not in ACQUISITION_POLICIES:
            issue("dataset", identifier, "acquisition_policy", "unknown acquisition policy")
        limitations = row.get("limitations")
        if (
            not isinstance(limitations, list)
            or not limitations
            or any(not isinstance(item, str) or not item.strip() for item in limitations)
        ):
            issue("dataset", identifier, "limitations", "at least one explicit limitation is required")
        assets = row.get("assets", [])
        if not isinstance(assets, list):
            issue("dataset", identifier, "assets", "assets must be an array")
            continue
        if policy == "do_not_download" and assets:
            issue("dataset", identifier, "assets", "do_not_download datasets cannot expose fetch assets")
        for index, asset in enumerate(assets):
            asset_id = f"assets[{index}]"
            if not isinstance(asset.get("filename"), str) or not asset["filename"].strip():
                issue("dataset", identifier, f"{asset_id}.filename", "filename is required")
            url = asset.get("url")
            if not isinstance(url, str) or not _https(url):
                issue("dataset", identifier, f"{asset_id}.url", "HTTPS URL without credentials required")
            checksum = asset.get("checksum")
            if checksum is not None and (not isinstance(checksum, str) or not CHECKSUM.fullmatch(checksum)):
                issue(
                    "dataset",
                    identifier,
                    f"{asset_id}.checksum",
                    "checksum must be md5:, sha256: or pinned git-blob-sha1: hex",
                )
            if checksum is None and "checksum" not in row.get("rights_status", ""):
                issue(
                    "dataset",
                    identifier,
                    f"{asset_id}.checksum",
                    "missing checksum must be explicit in rights_status",
                )
            for size_field in ("bytes", "max_bytes"):
                size = asset.get(size_field)
                if size is not None and (not isinstance(size, int) or isinstance(size, bool) or size <= 0):
                    issue("dataset", identifier, f"{asset_id}.{size_field}", "must be a positive integer")

    for row in source_rows:
        identifier = row.get("id") or "<missing>"
        for field in ("id", "basis", "reuse"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                issue("source", identifier, field, "required nonempty string is missing")
        url = row.get("url")
        if url is not None and not (
            isinstance(url, str) and (_https(url) or url.startswith("project://docs/"))
        ):
            issue(
                "source",
                identifier,
                "url",
                "reference URL must use HTTPS without credentials or an internal project://docs path",
            )
        if not any(isinstance(row.get(field), str) and row[field].strip() for field in ("url", "derivation")):
            issue(
                "source", identifier, "basis", "a public reference URL or independent derivation is required"
            )

    return {
        "schema_version": "matintegrity.release_rights_metadata_audit.v1",
        "status": "passed" if not findings else "failed",
        "dataset_records": len(dataset_rows),
        "source_records": len(source_rows),
        "review_date_freshness": {
            "status": "older_than_threshold" if stale_reviews else "within_threshold",
            "as_of": review_date.isoformat(),
            "freshness_days": freshness_days,
            "stale_dataset_reviews": stale_reviews,
        },
        "findings": findings,
        "legal_clearance_claimed": False,
        "scientific_qualification_claimed": False,
        "meaning": "Structural metadata completeness check only; legal review remains record-specific.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="validation/release_rights_metadata_audit.json")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--freshness-days", type=int, default=365)
    args = parser.parse_args()
    report = audit_rights_metadata(
        json.loads((ROOT / "data/catalogs/datasets.json").read_text(encoding="utf-8")),
        json.loads((ROOT / "data/catalogs/sources.json").read_text(encoding="utf-8")),
        as_of=args.as_of,
        freshness_days=args.freshness_days,
    )
    target = (ROOT / args.output).resolve()
    if ROOT not in target.parents:
        raise ValueError("output must remain inside the project")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
