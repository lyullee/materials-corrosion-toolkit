from __future__ import annotations

import hashlib

import pytest

from matintegrity.tribology_metadata_data import audit_tribology_metadata_dataset


def _asset(tmp_path, name, content):
    path = tmp_path / name
    path.write_bytes(content)
    return {
        "filename": name,
        "bytes": len(content),
        "checksum": f"md5:{hashlib.md5(content).hexdigest()}",  # noqa: S324 -- provider format
    }


def test_audit_preserves_metadata_only_boundary(tmp_path):
    manifest = (
        _asset(tmp_path, "copper-under-constant-normal-load.ttl", b"@prefix x: <x>.\n"),
        _asset(tmp_path, "laboratory-equipment.ttl", b"@prefix y: <y>.\n"),
    )
    audit = audit_tribology_metadata_dataset(tmp_path, manifest=manifest)
    assert audit.file_count == 2
    assert audit.total_bytes == sum(row["bytes"] for row in manifest)
    assert audit.all_provider_md5_verified is True
    assert audit.numerical_use_status == "metadata_only_linked_measurements_not_acquired"


def test_audit_rejects_checksum_or_directory_manifest_mismatch(tmp_path):
    manifest = (_asset(tmp_path, "software.ttl", b"software"),)
    (tmp_path / "software.ttl").write_bytes(b"changed!")
    with pytest.raises(ValueError, match="MD5|byte count"):
        audit_tribology_metadata_dataset(tmp_path, manifest=manifest)
    (tmp_path / "software.ttl").write_bytes(b"software")
    (tmp_path / "extra.ttl").write_bytes(b"extra")
    with pytest.raises(ValueError, match="complete pinned manifest"):
        audit_tribology_metadata_dataset(tmp_path, manifest=manifest)


def test_audit_rejects_duplicate_manifest_names(tmp_path):
    asset = _asset(tmp_path, "consumables.ttl", b"consumables")
    with pytest.raises(ValueError, match="unique"):
        audit_tribology_metadata_dataset(tmp_path, manifest=(asset, asset))
