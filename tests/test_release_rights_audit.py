from datetime import date

from scripts.audit_release_rights import audit_rights_metadata


def valid_catalogs():
    return (
        {
            "datasets": [
                {
                    "id": "data-1",
                    "title": "Public observations",
                    "category": "test",
                    "citation": "Provider (2026)",
                    "license": "CC-BY-4.0",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "rights_evidence_url": "https://example.org/record",
                    "rights_status": "reviewed_license",
                    "acquisition_policy": "allowed",
                    "checked_on": "2026-10-28",
                    "limitations": ["Synthetic test metadata only."],
                    "assets": [
                        {
                            "filename": "data.csv",
                            "url": "https://example.org/data.csv",
                            "checksum": "sha256:" + "a" * 64,
                            "bytes": 12,
                            "max_bytes": 12,
                        }
                    ],
                }
            ]
        },
        {
            "sources": [
                {
                    "id": "source-1",
                    "basis": "independent_algebraic_implementation",
                    "derivation": "Caller values are combined without external tables.",
                    "reuse": "Independently authored implementation.",
                }
            ]
        },
    )


def test_complete_metadata_passes_without_claiming_legal_clearance():
    datasets, sources = valid_catalogs()
    report = audit_rights_metadata(datasets, sources)
    assert report["status"] == "passed"
    assert report["findings"] == []
    assert report["legal_clearance_claimed"] is False


def test_missing_rights_fields_and_credentialed_url_fail():
    datasets, sources = valid_catalogs()
    row = datasets["datasets"][0]
    row.pop("license")
    row["rights_evidence_url"] = "https://user:secret@example.org/record"
    report = audit_rights_metadata(datasets, sources)
    assert report["status"] == "failed"
    fields = {item["field"] for item in report["findings"]}
    assert "license" in fields
    assert "rights_evidence_url" in fields


def test_do_not_download_cannot_expose_assets():
    datasets, sources = valid_catalogs()
    datasets["datasets"][0]["acquisition_policy"] = "do_not_download"
    report = audit_rights_metadata(datasets, sources)
    assert report["status"] == "failed"
    assert any(item["field"] == "assets" for item in report["findings"])


def test_stale_rights_review_is_reported_separately_from_legal_clearance():
    datasets, sources = valid_catalogs()
    report = audit_rights_metadata(datasets, sources, as_of=date(2028, 1, 1), freshness_days=365)
    assert report["status"] == "passed"
    assert report["review_date_freshness"]["status"] == "older_than_threshold"
    assert report["review_date_freshness"]["stale_dataset_reviews"][0]["id"] == "data-1"
    assert report["legal_clearance_claimed"] is False


def test_invalid_or_future_review_dates_fail_structural_audit():
    datasets, sources = valid_catalogs()
    datasets["datasets"][0]["checked_on"] = "2026-02-30"
    report = audit_rights_metadata(datasets, sources, as_of=date(2026, 1, 1))
    assert report["status"] == "failed"
    assert any(item["field"] == "checked_on" for item in report["findings"])

    datasets, sources = valid_catalogs()
    report = audit_rights_metadata(datasets, sources, as_of=date(2026, 1, 1))
    assert report["status"] == "failed"
    assert any("future" in item["detail"] for item in report["findings"])
