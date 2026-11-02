from __future__ import annotations

import hashlib
import zipfile

import numpy as np
import pytest

from matintegrity.oxford_ebsd import read_oxford_ebsd_phase_labels
from matintegrity.spatial_fields import numeric_array_digest


class FakeOxfordReader:
    def __init__(self):
        self.loaded_data = type("Data", (), {})()
        self.loaded_metadata = {}

    def load(self, file_name):
        assert file_name.suffix == ".crc"
        assert file_name.with_suffix(".cpr").is_file()
        self.loaded_data.phase = np.array([[0, 1, 2], [1, 2, 2]], dtype=np.uint8)
        self.loaded_metadata = {
            "shape": (2, 3),
            "step_size": 0.1,
            "phases": [object(), object()],
        }


def _archive(tmp_path, *, unsafe_name=None):
    archive_path = tmp_path / "map.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("map.cpr", b"Oxford metadata fixture")
        archive.writestr("map.crc", b"binary fixture")
        if unsafe_name:
            archive.writestr(unsafe_name, b"unsafe")
    return archive_path, hashlib.sha256(archive_path.read_bytes()).hexdigest()


def test_reads_only_requested_pair_and_records_raw_labels(tmp_path):
    archive_path, archive_sha256 = _archive(tmp_path)
    result = read_oxford_ebsd_phase_labels(
        archive_path,
        "map",
        expected_archive_sha256=archive_sha256,
        loader_factory=FakeOxfordReader,
    )

    assert result.labels.shape == (2, 3)
    assert result.record.label_values == (0, 1, 2)
    assert result.record.nonindexed_label_value == 0
    assert result.record.provider_grid_step_value == 0.1
    assert result.record.provider_grid_step_unit_status == "not_declared_by_adapter"
    assert result.record.phase_descriptor_count == 2
    assert result.record.reader_compatibility_patch == "identity_rotation_placeholder_for_omitted_orientation"
    assert result.record.label_array_sha256 == numeric_array_digest(result.labels)
    assert result.record.reader_version == "injected-test-reader"
    assert not result.labels.flags.writeable


def test_rejects_archive_digest_mismatch_and_unsafe_members(tmp_path):
    archive_path, archive_sha256 = _archive(tmp_path)
    with pytest.raises(ValueError, match="digest differs"):
        read_oxford_ebsd_phase_labels(
            archive_path,
            "map",
            expected_archive_sha256="0" * 64,
            loader_factory=FakeOxfordReader,
        )

    unsafe_archive, unsafe_sha256 = _archive(tmp_path, unsafe_name="../escape.txt")
    with pytest.raises(ValueError, match="unsafe path"):
        read_oxford_ebsd_phase_labels(
            unsafe_archive,
            "map",
            expected_archive_sha256=unsafe_sha256,
            loader_factory=FakeOxfordReader,
        )


def test_rejects_reader_shape_that_disagrees_with_labels(tmp_path):
    archive_path, archive_sha256 = _archive(tmp_path)

    class BadShapeReader(FakeOxfordReader):
        def load(self, file_name):
            super().load(file_name)
            self.loaded_metadata["shape"] = (3, 2)

    with pytest.raises(ValueError, match="unexpected shape"):
        read_oxford_ebsd_phase_labels(
            archive_path,
            "map",
            expected_archive_sha256=archive_sha256,
            loader_factory=BadShapeReader,
        )
