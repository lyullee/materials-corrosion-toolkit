"""Release guards must reject decoded paths and exclude machine-local receipts."""

import json

import pytest

from scripts import build_release


@pytest.fixture
def public_root(tmp_path, monkeypatch):
    for source_name, packaged_name in build_release.PACKAGE_CATALOGS.values():
        for name in (source_name, packaged_name):
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf8")
    monkeypatch.setattr(build_release, "ROOT", tmp_path)
    return tmp_path


def test_decoded_json_local_path_is_rejected(public_root):
    folder = public_root / "validation"
    folder.mkdir(exist_ok=True)
    # Construct a generic sentinel; no real user path is embedded in the source.
    marker = "C:" + chr(92) + "Users" + chr(92) + "synthetic"
    (folder / "unsafe.json").write_text(json.dumps({"path": marker}), encoding="utf8")
    with pytest.raises(ValueError, match="local research marker"):
        build_release.public_files()


def test_machine_local_validation_receipt_is_excluded(public_root):
    path = public_root / "validation/hpc-local/task/result.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"host": "synthetic"}), encoding="utf8")
    assert path not in build_release.public_files()


def test_ndjson_examples_are_decoded_and_allowed(public_root):
    path = public_root / "examples/synthetic.json"
    path.parent.mkdir()
    path.write_text('{"one":1}\n{"two":2}\n', encoding="utf8")
    assert path in build_release.public_files()
