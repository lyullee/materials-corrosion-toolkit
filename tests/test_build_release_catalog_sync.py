import pytest

from scripts.build_release import PACKAGE_CATALOGS, validate_catalog_sync


def test_release_catalog_sync_accepts_identical_source_and_package_files(tmp_path):
    for source_relative, package_relative in PACKAGE_CATALOGS.values():
        source = tmp_path / source_relative
        packaged = tmp_path / package_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        packaged.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b'{"schema":"synthetic"}\n')
        packaged.write_bytes(source.read_bytes())

    validate_catalog_sync(tmp_path)


def test_release_catalog_sync_rejects_a_stale_installed_package_copy(tmp_path):
    for source_relative, package_relative in PACKAGE_CATALOGS.values():
        source = tmp_path / source_relative
        packaged = tmp_path / package_relative
        source.parent.mkdir(parents=True, exist_ok=True)
        packaged.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b'{"schema":"new"}\n')
        packaged.write_bytes(
            b'{"schema":"old"}\n' if source_relative.endswith("datasets.json") else source.read_bytes()
        )

    with pytest.raises(ValueError, match="stale packaged datasets catalog"):
        validate_catalog_sync(tmp_path)
