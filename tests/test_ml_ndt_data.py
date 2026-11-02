from __future__ import annotations

import json

import numpy as np
import pytest

from matintegrity.ml_ndt_data import (
    ML_NDT_PINNED_REVISION,
    list_ml_ndt_batches,
    read_ml_ndt_batch,
    read_ml_ndt_image,
)

BATCH_UUID = "0275DE06-7EB3-4D99-B71D-39F259B64862"
OTHER_REVISION = "1" * 40


def _record(equivalent_size: str, source_size: str = "1.6") -> dict:
    return {
        "flaws": [
            {
                "noise_threshold": "12",
                "original_location": "10-20",
                "equivalent_flawsize": equivalent_size,
                "location_max": "40",
                "size": source_size,
                "max_amplitude": "100",
                "location": "30-40",
                "location_min": "30",
                "noise_flawsize": "0.2",
                "factor": "0.75",
            }
        ]
    }


def _clone(tmp_path, *, mismatch=False, incomplete=False, malformed_json=False):
    root = tmp_path / "clone"
    for partition in ("training", "validation"):
        (root / "data" / partition).mkdir(parents=True)
    directory = root / "data" / "training"
    prefix = directory / BATCH_UUID
    pixels = np.arange(12, dtype="<u2").reshape(3, 2, 2)
    pixels.tofile(prefix.with_suffix(".bins"))
    prefix.with_suffix(".meta").write_text("UInt16, 2 x 2 x 3\n", encoding="utf-8")
    prefix.with_suffix(".labels").write_text("1\t1.5\n0\t0.0\n1\t2.5\n", encoding="utf-8")
    records = [_record("1.5"), _record("0.25" if mismatch else "0.0", "0.0"), _record("2.5")]
    json_text = "".join(json.dumps(row, separators=(",", ":")) for row in records)
    if malformed_json:
        json_text += "{"
    prefix.with_suffix(".jsons").write_text(json_text, encoding="utf-8")
    if incomplete:
        prefix.with_suffix(".labels").unlink()
    return root


def _read(root):
    return read_ml_ndt_batch(
        root,
        "training",
        BATCH_UUID,
        repository_revision=OTHER_REVISION,
        require_pinned_revision=False,
    )


def test_lists_complete_provider_partitions_without_opening_binary(tmp_path):
    root = _clone(tmp_path)
    result = list_ml_ndt_batches(
        root,
        repository_revision=OTHER_REVISION,
        require_pinned_revision=False,
    )
    assert result["batch_count"] == 1
    assert result["partitions"]["validation"] == []
    batch = result["partitions"]["training"][0]
    assert batch["batch_uuid"] == BATCH_UUID
    assert set(batch["filenames"]) == {"bins", "jsons", "labels", "meta"}
    assert batch["source_bytes"]["bins"] == 24


def test_reads_concatenated_json_and_preserves_provider_strings(tmp_path):
    result = _read(_clone(tmp_path))
    assert (result.rows, result.columns, result.image_count) == (2, 2, 3)
    assert result.storage_order == "provider_code_c_order"
    assert result.byte_order_status == "not_declared_by_meta"
    assert result.metadata_size_mismatch_count == 0
    assert result.labels[0].provider_hit_label == 1
    assert result.labels[0].flaws[0].raw_fields["original_location"] == "10-20"
    assert result.labels[0].flaws[0].source_flaw_size_value == pytest.approx(1.6)
    assert len(result.source_sha256["bins"]) == 64
    assert result.qualification == "augmented_images_not_independent_physical_specimens"


def test_reads_one_image_only_after_explicit_byte_order(tmp_path):
    root = _clone(tmp_path)
    batch = _read(root)
    image = read_ml_ndt_image(root, batch, 1, byte_order="little")
    np.testing.assert_array_equal(image, [[4, 5], [6, 7]])
    assert image.dtype == np.dtype("uint16")


def test_reports_label_metadata_disagreement_without_repair(tmp_path):
    result = _read(_clone(tmp_path, mismatch=True))
    assert result.metadata_size_mismatch_count == 1
    assert result.labels[1].provider_equivalent_size_value == 0.0
    assert result.labels[1].metadata_equivalent_size_value == 0.25
    assert result.labels[1].label_metadata_size_match is False


def test_rejects_unpinned_revision_by_default(tmp_path):
    root = _clone(tmp_path)
    with pytest.raises(ValueError, match="revision"):
        list_ml_ndt_batches(root, repository_revision=OTHER_REVISION)
    with pytest.raises(ValueError, match="revision"):
        read_ml_ndt_batch(root, "training", BATCH_UUID, repository_revision=OTHER_REVISION)


def test_pinned_revision_requires_reviewed_provider_shape(tmp_path):
    root = _clone(tmp_path)
    with pytest.raises(ValueError, match="shape"):
        read_ml_ndt_batch(
            root,
            "training",
            BATCH_UUID,
            repository_revision=ML_NDT_PINNED_REVISION,
        )


def test_rejects_incomplete_batch_before_use(tmp_path):
    root = _clone(tmp_path, incomplete=True)
    with pytest.raises(ValueError, match="incomplete"):
        list_ml_ndt_batches(
            root,
            repository_revision=OTHER_REVISION,
            require_pinned_revision=False,
        )


def test_rejects_noncanonical_uuid_and_malformed_concatenated_json(tmp_path):
    root = _clone(tmp_path)
    directory = root / "data" / "training"
    for path in list(directory.iterdir()):
        path.rename(path.with_name(path.name.lower()))
    with pytest.raises(ValueError, match="canonical"):
        list_ml_ndt_batches(
            root,
            repository_revision=OTHER_REVISION,
            require_pinned_revision=False,
        )

    broken = _clone(tmp_path / "broken", malformed_json=True)
    with pytest.raises(ValueError, match="concatenated"):
        _read(broken)


def test_rechecks_binary_digest_before_image_read(tmp_path):
    root = _clone(tmp_path)
    batch = _read(root)
    binary = root / "data" / "training" / f"{BATCH_UUID}.bins"
    with binary.open("r+b") as stream:
        stream.write(b"\xff\xff")
    with pytest.raises(ValueError, match="digest changed"):
        read_ml_ndt_image(root, batch, 0, byte_order="little")


def test_rejects_sidecar_count_and_binary_size_mismatch(tmp_path):
    root = _clone(tmp_path)
    labels = root / "data" / "training" / f"{BATCH_UUID}.labels"
    labels.write_text("1\t1.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="align"):
        _read(root)

    other = _clone(tmp_path / "other")
    binary = other / "data" / "training" / f"{BATCH_UUID}.bins"
    with binary.open("ab") as stream:
        stream.write(b"\x00\x00")
    with pytest.raises(ValueError, match="binary size"):
        _read(other)
