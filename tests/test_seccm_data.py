from __future__ import annotations

import csv
import hashlib
import io
import zipfile

import numpy as np
import pytest

from matintegrity.seccm_data import (
    EXPECTED_MEMBERS,
    audit_seccm_archive,
    read_seccm_ca_trace,
)


def _raw_ca(*, times=(0.0, 0.5, 1.0), mutate=None):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["Unnamed: 0", *(f"MAP_Point_{value}" for value in range(1, 206))])
    writer.writerow(["Time_Hold_s", *(f"I_Substrate_A_LN_{1000 + value}" for value in range(1, 206))])
    for row_index, time_value in enumerate(times):
        row = [str(time_value), *(str(value * 1e-12 + row_index * 1e-15) for value in range(1, 206))]
        writer.writerow(row)
    rows = list(csv.reader(io.StringIO(stream.getvalue())))
    if mutate is not None:
        mutate(rows)
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().encode()


def _archive(tmp_path, *, raw=None, extra_name=None):
    path = tmp_path / "seccm.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in EXPECTED_MEMBERS:
            archive.writestr(name, raw if name == "SS_NaCl_CA_M_1031_C.csv" else b"fixture\n")
        if extra_name is not None:
            archive.writestr(extra_name, b"unexpected\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, digest


def test_archive_audit_and_trace_preserve_raw_units_and_values(tmp_path):
    path, digest = _archive(tmp_path, raw=_raw_ca())
    audit = audit_seccm_archive(path, expected_archive_sha256=digest, dataset_id="fixture")
    assert audit.map_ids == tuple(range(1, 206))
    assert audit.sample_count_per_trace == 3
    assert audit.time_min_s == 0.0
    assert audit.time_max_s == 1.0
    assert audit.substrate_current_min_A == pytest.approx(1e-12)
    assert audit.substrate_current_max_A == pytest.approx(205e-12 + 2e-15)
    assert len(audit.members) == 10

    result = read_seccm_ca_trace(
        path,
        7,
        physical_specimen_id="provider-map-scope-unresolved",
        source_group_id="fixture-group",
        expected_archive_sha256=digest,
        dataset_id="fixture",
    )
    assert result["metadata"].map_point_label == "MAP_Point_7"
    assert result["metadata"].provider_signal_label == "I_Substrate_A_LN_1007"
    assert result["metadata"].current_unit == "A"
    assert result["time_s"] == pytest.approx(np.asarray([0.0, 0.5, 1.0]))
    assert result["substrate_current_A"] == pytest.approx(np.asarray([7e-12, 7e-12 + 1e-15, 7e-12 + 2e-15]))


def test_archive_checksum_and_exact_membership_are_required(tmp_path):
    path, digest = _archive(tmp_path, raw=_raw_ca())
    with pytest.raises(ValueError, match="SHA-256"):
        audit_seccm_archive(path, expected_archive_sha256="0" * 64)
    extra, extra_digest = _archive(tmp_path, raw=_raw_ca(), extra_name="extra.csv")
    assert extra == path
    with pytest.raises(ValueError, match="ten-file manifest"):
        audit_seccm_archive(extra, expected_archive_sha256=extra_digest)
    assert digest != extra_digest


def test_unsafe_archive_member_is_rejected_before_manifest_comparison(tmp_path):
    path, digest = _archive(tmp_path, raw=_raw_ca(), extra_name="../escape.csv")
    with pytest.raises(ValueError, match="unsafe"):
        audit_seccm_archive(path, expected_archive_sha256=digest)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda rows: rows[0].__setitem__(1, "site-1"), "map-point header"),
        (lambda rows: rows[1].__setitem__(0, "time"), "quantity/unit header"),
        (lambda rows: rows[2].__setitem__(2, "not-a-number"), "nonnumeric text"),
        (lambda rows: rows[2].__setitem__(2, "nan"), "nonfinite"),
        (lambda rows: rows[3].pop(), "does not have 206"),
    ],
)
def test_changed_raw_ca_schema_or_values_are_rejected(tmp_path, mutate, message):
    path, digest = _archive(tmp_path, raw=_raw_ca(mutate=mutate))
    with pytest.raises(ValueError, match=message):
        audit_seccm_archive(path, expected_archive_sha256=digest)


def test_time_and_map_identity_must_remain_in_scope(tmp_path):
    path, digest = _archive(tmp_path, raw=_raw_ca(times=(0.0, 1.0, 0.5)))
    with pytest.raises(ValueError, match="strictly increasing"):
        audit_seccm_archive(path, expected_archive_sha256=digest)

    valid, valid_digest = _archive(tmp_path, raw=_raw_ca())
    with pytest.raises(ValueError, match="between 1 and 205"):
        read_seccm_ca_trace(
            valid,
            206,
            physical_specimen_id="scope",
            source_group_id="group",
            expected_archive_sha256=valid_digest,
        )
    with pytest.raises(ValueError, match="identities are required"):
        read_seccm_ca_trace(
            valid,
            1,
            physical_specimen_id="",
            source_group_id="group",
            expected_archive_sha256=valid_digest,
        )
