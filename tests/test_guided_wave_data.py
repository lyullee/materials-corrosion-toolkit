from __future__ import annotations

import hashlib
import io
import zipfile

import numpy as np
import pytest
import xlwt

import matintegrity.guided_wave_data as guided

FREQUENCIES = (14.0, 18.0, 24.0, 30.0, 37.0)


def _workbook(*, order=FREQUENCIES, bad_header=False, repeated_distance=False, decreasing=False) -> bytes:
    book = xlwt.Workbook()
    for frequency in order:
        sheet = book.add_sheet(f"V 0 {frequency:.3f}kHz 8.0cy")
        sheet.write(0, 0, "Window-test.sC.raw")
        headers = ["distance [m]", "torsional [V]", "flexural [V]", "pure DAC [V]"]
        if bad_header:
            headers[1] = "amplitude"
        for column, header in enumerate(headers):
            sheet.write(1, column, header)
        distances = [0.0, 0.25, 0.5]
        if repeated_distance:
            distances[-1] = distances[-2]
        if decreasing:
            distances[-1] = distances[-2] - 0.1
        for index, distance in enumerate(distances, 2):
            values = [distance, frequency + index, -frequency - index, index / 10]
            for column, value in enumerate(values):
                sheet.write(index, column, value)
    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def _archive(tmp_path, workbooks=None, *, nested_name="provider/data.zip", outer_member=None):
    workbooks = workbooks or {100: _workbook()}
    nested_stream = io.BytesIO()
    with zipfile.ZipFile(nested_stream, "w", zipfile.ZIP_DEFLATED) as nested:
        for acquisition_id, content in workbooks.items():
            name = f"root/Window-1.G4-288-{acquisition_id}-V-0-waveform.xls"
            nested.writestr(name, content)
    outer = tmp_path / "guided.zip"
    with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(outer_member or nested_name, nested_stream.getvalue())
    return outer, hashlib.sha256(outer.read_bytes()).hexdigest()


def _read(path, digest, acquisition_id=100):
    return guided.read_guided_wave_acquisition(
        path,
        acquisition_id,
        specimen_id="tube-1",
        require_pinned_hash=True,
        expected_archive_sha256=digest,
    )


def test_lists_acquisitions_without_parsing_workbooks(tmp_path):
    path, digest = _archive(tmp_path, {100: b"not parsed", 105: b"also not parsed"})
    result = guided.list_guided_wave_acquisitions(
        path, require_pinned_hash=True, expected_archive_sha256=digest
    )
    assert [row["acquisition_id"] for row in result["acquisitions"]] == [100, 105]
    assert {row["article_period_group"] for row in result["acquisitions"]} == {"unreviewed"}
    assert result["source_is_pinned"] is False
    assert result["nested_archive_bytes"] > 0


def test_reads_frequency_by_sheet_name_not_sheet_position(tmp_path):
    order = (37.0, 14.0, 30.0, 18.0, 24.0)
    path, digest = _archive(tmp_path, {100: _workbook(order=order)})
    result = _read(path, digest)
    assert result["source_sheet_frequency_order_Hz"] == tuple(value * 1000 for value in order)
    assert [signal["frequency_Hz"] for signal in result["signals"]] == list(guided.EXPECTED_FREQUENCIES_HZ)
    first = result["signals"][0]
    np.testing.assert_allclose(first["distance_m"], [0, 0.25, 0.5])
    np.testing.assert_allclose(first["torsional_V"], [16, 17, 18])
    np.testing.assert_allclose(first["flexural_V"], [-16, -17, -18])
    np.testing.assert_allclose(first["provider_pure_dac_V"], [0.2, 0.3, 0.4])
    assert first["source_matrix_shape"] == (5, 4)
    assert first["repeated_distance_intervals"] == 0
    assert first["article_shape_discrepancy"] is True
    assert result["machining_step_id"] is None
    assert result["outer_archive_sha256"] == digest
    assert len(result["nested_archive_sha256"]) == 64
    assert result["article_period_group_basis"] == "not_applied"
    assert result["timestamp"] is None
    assert result["temperature_K"] is None


def test_derivative_archive_never_inherits_article_period_labels(tmp_path):
    path, digest = _archive(tmp_path)
    result = _read(path, digest)
    assert result["article_period_group"] == "unreviewed"
    assert result["observation_meaning"] == "guided_wave_voltage_response_not_direct_wall_thickness"


def test_review_can_be_disabled_even_for_matching_pinned_digest(tmp_path, monkeypatch):
    workbooks = {index: b"inventory-only" for index in range(236)}
    path, digest = _archive(tmp_path, workbooks)
    monkeypatch.setattr(guided, "GUIDED_WAVE_ARCHIVE_SHA256", digest)
    reviewed = guided.list_guided_wave_acquisitions(
        path, expected_archive_sha256=digest, article_state_review=True
    )
    unreviewed = guided.list_guided_wave_acquisitions(
        path, expected_archive_sha256=digest, article_state_review=False
    )
    assert (
        sum(row["article_period_group"] == "reported_healthy_period" for row in reviewed["acquisitions"])
        == 207
    )
    assert (
        sum(row["article_period_group"] == "post_machining_period" for row in reviewed["acquisitions"]) == 29
    )
    assert {row["article_period_group"] for row in unreviewed["acquisitions"]} == {"unreviewed"}


def test_rejects_outer_digest_mismatch(tmp_path):
    path, _ = _archive(tmp_path)
    with pytest.raises(ValueError, match="digest"):
        guided.list_guided_wave_acquisitions(path)


def test_rejects_unsafe_outer_member(tmp_path):
    path, digest = _archive(tmp_path, outer_member="../data.zip")
    with pytest.raises(ValueError, match="unsafe"):
        guided.list_guided_wave_acquisitions(path, expected_archive_sha256=digest, require_pinned_hash=True)


def test_rejects_duplicate_acquisition_ids(tmp_path):
    nested_stream = io.BytesIO()
    with zipfile.ZipFile(nested_stream, "w") as nested:
        nested.writestr("a/Window-1.G4-288-100-V-0-waveform.xls", b"a")
        nested.writestr("b/Window-1.G4-288-100-V-0-waveform.xls", b"b")
    path = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(path, "w") as outer:
        outer.writestr("nested.zip", nested_stream.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="duplicate.*ID"):
        guided.list_guided_wave_acquisitions(path, expected_archive_sha256=digest)


def test_rejects_unexpected_nested_member(tmp_path):
    nested_stream = io.BytesIO()
    with zipfile.ZipFile(nested_stream, "w") as nested:
        nested.writestr("readme.txt", "not a workbook")
    path = tmp_path / "unexpected.zip"
    with zipfile.ZipFile(path, "w") as outer:
        outer.writestr("nested.zip", nested_stream.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unexpected"):
        guided.list_guided_wave_acquisitions(path, expected_archive_sha256=digest)


@pytest.mark.parametrize(
    ("workbook", "message"),
    [
        (_workbook(bad_header=True), "schema changed"),
        (_workbook(decreasing=True), "decreases"),
        (b"not-an-xls", "OLE BIFF"),
    ],
)
def test_rejects_mutated_workbook_content(tmp_path, workbook, message):
    path, digest = _archive(tmp_path, {100: workbook})
    with pytest.raises(ValueError, match=message):
        _read(path, digest)


def test_requires_physical_specimen_identity(tmp_path):
    path, digest = _archive(tmp_path)
    with pytest.raises(ValueError, match="specimen ID"):
        guided.read_guided_wave_acquisition(
            path,
            100,
            specimen_id="",
            expected_archive_sha256=digest,
        )


def test_missing_acquisition_is_not_silently_substituted(tmp_path):
    path, digest = _archive(tmp_path)
    with pytest.raises(KeyError, match="not found"):
        _read(path, digest, acquisition_id=999)


def test_preserves_repeated_distance_interval_without_sorting(tmp_path):
    path, digest = _archive(tmp_path, {100: _workbook(repeated_distance=True)})
    result = _read(path, digest)
    for signal in result["signals"]:
        assert signal["repeated_distance_intervals"] == 1
        assert signal["distance_axis_order"] == "provider_nondecreasing_not_sorted"
        np.testing.assert_allclose(signal["distance_m"], [0, 0.25, 0.25])
