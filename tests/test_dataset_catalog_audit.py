from scripts.audit_dataset_catalog import audit


def test_dataset_catalog_audit_reports_checksum_and_rights_boundaries():
    result = audit()
    assert result["schema"] == "matintegrity.dataset_catalog_audit.v1"
    assert result["datasets"] == 83
    assert result["assets"] == 510
    assert result["publisher_checksums_missing"] == 5
    assert result["local_assets_without_publisher_checksum"] <= result["publisher_checksums_missing"]
    assert result["acquisition_policies"]["do_not_download"] == 1
    assert result["rights_statuses"]["review_required"] == 3
