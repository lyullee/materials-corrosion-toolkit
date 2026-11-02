from __future__ import annotations

import hashlib
import math

import pytest
from openpyxl import Workbook

from matintegrity.pipeline_ili_data import (
    PIPELINE_ILI_HEADERS,
    audit_pipeline_ili_workbook,
    iter_pipeline_ili_features,
)


def _workbook(tmp_path, *, year=3, header=PIPELINE_ILI_HEADERS, second_year=None, formula=False):
    path = tmp_path / "ili.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(header)
    sheet.append([year, 14, 12.2, 0.175, None, 262.5, 210, None, 213, 0.184, 211, 7.1, 17, 24, 1.42])
    sheet.append(
        [
            second_year if second_year is not None else year,
            15,
            11.0,
            -0.1,
            30,
            280.0,
            40,
            281.0,
            50,
            0.2,
            45,
            8.0,
            20,
            30,
            "=1+1" if formula else 2.0,
        ]
    )
    workbook.save(path)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_iter_pipeline_ili_features_converts_explicit_units_and_preserves_missing(tmp_path):
    path, digest = _workbook(tmp_path)
    rows = list(
        iter_pipeline_ili_features(
            path,
            physical_pipeline_id="pipeline-1",
            inspection_run_id="run-3",
            expected_inspection_year_token=3,
            expected_sha256=digest,
        )
    )
    assert len(rows) == 2
    first = rows[0]
    assert first.provider_row_number == 2
    assert first.inspection_year_is_real_asset_age is False
    assert first.seam_orientation_rad is None
    assert first.end_absolute_distance_m is None
    assert first.start_circumferential_orientation_rad == pytest.approx(math.radians(210))
    assert first.nominal_wall_thickness_m == pytest.approx(0.0071)
    assert first.reported_maximum_depth_m == pytest.approx(0.00142)
    assert rows[1].quality_flags == ("negative_relative_location_preserved",)


def test_iter_pipeline_ili_features_supports_explicit_row_window(tmp_path):
    path, digest = _workbook(tmp_path)
    rows = list(
        iter_pipeline_ili_features(
            path,
            physical_pipeline_id="pipeline-1",
            inspection_run_id="run-3",
            expected_inspection_year_token=3,
            expected_sha256=digest,
            start_provider_row=3,
            stop_provider_row=3,
        )
    )
    assert [item.provider_row_number for item in rows] == [3]


def test_pipeline_ili_audit_counts_missing_range_and_year(tmp_path):
    path, digest = _workbook(tmp_path)
    audit = audit_pipeline_ili_workbook(
        path,
        expected_inspection_year_token=3,
        expected_sha256=digest,
    )
    assert audit.observation_count == 2
    assert audit.observed_inspection_year_tokens == (3,)
    assert audit.missing_count_by_header["SO.deg"] == 1
    assert audit.missing_count_by_header["EPD.m"] == 1
    assert audit.numeric_minimum_by_header["RD.m"] == -0.1
    assert audit.numeric_maximum_by_header["MD.mm"] == 2.0
    assert audit.formula_cell_count == 0
    assert audit.year_mismatch_count == 0


def test_pipeline_ili_audit_exposes_formula_and_year_mismatch(tmp_path):
    path, digest = _workbook(tmp_path, second_year=5, formula=True)
    audit = audit_pipeline_ili_workbook(
        path,
        expected_inspection_year_token=3,
        expected_sha256=digest,
    )
    assert audit.observed_inspection_year_tokens == (3, 5)
    assert audit.formula_cell_count == 1
    assert audit.nonnumeric_count_by_header["MD.mm"] == 1
    assert audit.year_mismatch_count == 1


def test_pipeline_ili_reader_rejects_formula_cells(tmp_path):
    path, digest = _workbook(tmp_path, formula=True)
    with pytest.raises(ValueError, match="rejects formula"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="pipeline-1",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256=digest,
            )
        )


def test_pipeline_ili_reader_rejects_hash_header_and_year_mismatch(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="pipeline-1",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256="0" * 64,
            )
        )
    bad_headers = list(PIPELINE_ILI_HEADERS)
    bad_headers[0] = "InspectionYear"
    path, digest = _workbook(tmp_path, header=tuple(bad_headers))
    with pytest.raises(ValueError, match="headers differ"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="pipeline-1",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256=digest,
            )
        )
    path, digest = _workbook(tmp_path, second_year=5)
    with pytest.raises(ValueError, match="row year"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="pipeline-1",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256=digest,
            )
        )


def test_pipeline_ili_reader_rejects_invalid_window_and_identity(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="identities"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256=digest,
            )
        )
    with pytest.raises(ValueError, match="at least two"):
        list(
            iter_pipeline_ili_features(
                path,
                physical_pipeline_id="pipeline-1",
                inspection_run_id="run-3",
                expected_inspection_year_token=3,
                expected_sha256=digest,
                start_provider_row=1,
            )
        )
