from __future__ import annotations

import hashlib

import numpy as np
import pytest

scipy_io = pytest.importorskip("scipy.io")

from matintegrity.pitting_data import read_local_pitting_numeric_mat  # noqa: E402


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path, **overrides):
    values = {
        "expected_sha256": _digest(path),
        "dataset_id": "authored-local-pitting",
        "physical_specimen_id": "specimen-01",
        "source_group_id": "one-study-one-specimen",
        "source_role": "stress_field",
    }
    values.update(overrides)
    return read_local_pitting_numeric_mat(path, **values)


def test_reads_only_real_numeric_arrays_and_preserves_nonfinite_values(tmp_path):
    path = tmp_path / "stress.mat"
    source = np.asarray([[1.0, np.nan], [-2.0, np.inf]], dtype=np.float32)
    scipy_io.savemat(path, {"sxx": source, "labels": np.asarray([[1, 2]], dtype=np.int16)})

    result = _read(path)
    metadata = result["metadata"]
    assert metadata.source_sha256 == _digest(path)
    assert metadata.coordinate_status == "unreviewed"
    assert metadata.interpretation_status == "file_structure_only"
    assert metadata.physical_specimen_independence == "one_specimen_repeated_locations"
    records = {record.variable_name: record for record in metadata.variables}
    assert records["sxx"].shape == (2, 2)
    assert records["sxx"].finite_count == 2
    assert records["sxx"].nonfinite_count == 2
    assert records["sxx"].finite_minimum == pytest.approx(-2.0)
    assert records["sxx"].finite_maximum == pytest.approx(1.0)
    np.testing.assert_array_equal(result["raw_arrays"]["labels"], [[1, 2]])
    assert np.isnan(result["raw_arrays"]["sxx"][0, 1])
    assert np.isposinf(result["raw_arrays"]["sxx"][1, 1])


def test_attaches_units_only_with_explicit_variable_specific_basis(tmp_path):
    path = tmp_path / "stress.mat"
    scipy_io.savemat(path, {"sxx": np.ones((2, 3), dtype=np.float32)})
    result = _read(
        path,
        declared_units={"sxx": ("Pa", "caller-reviewed experiment data dictionary revision 1")},
        interpretation_status="caller_reviewed_variable_meanings",
        interpretation_basis="caller-reviewed experiment data dictionary revision 1",
    )
    record = result["metadata"].variables[0]
    assert record.declared_unit == "Pa"
    assert record.unit_basis == "caller-reviewed experiment data dictionary revision 1"


def test_preserves_surface_exposure_without_claiming_grid_registration(tmp_path):
    path = tmp_path / "surface.mat"
    scipy_io.savemat(path, {"height": np.arange(6, dtype=float).reshape(2, 3)})
    metadata = _read(
        path,
        source_role="surface_morphology",
        exposure_duration_days=2.0,
    )["metadata"]
    assert metadata.exposure_duration_days == 2.0
    assert metadata.coordinate_status == "unreviewed"


def test_rejects_digest_mismatch_before_decoding(tmp_path):
    path = tmp_path / "stress.mat"
    scipy_io.savemat(path, {"sxx": np.ones((1, 1))})
    with pytest.raises(ValueError, match="SHA-256"):
        _read(path, expected_sha256="0" * 64)


def test_rejects_structs_cells_and_other_non_numeric_matlab_classes(tmp_path):
    path = tmp_path / "nested.mat"
    scipy_io.savemat(path, {"nested": {"height": np.ones((2, 2))}})
    with pytest.raises(ValueError, match="unsupported class"):
        _read(path)


def test_rejects_complex_arrays_instead_of_silently_reducing_them(tmp_path):
    path = tmp_path / "complex.mat"
    scipy_io.savemat(path, {"field": np.asarray([[1 + 2j]])})
    with pytest.raises(ValueError, match="real numeric"):
        _read(path)


def test_rejects_unreviewed_coordinate_claims_and_unknown_unit_variables(tmp_path):
    path = tmp_path / "stress.mat"
    scipy_io.savemat(path, {"sxx": np.ones((1, 1))})
    with pytest.raises(ValueError, match="coordinate basis"):
        _read(path, coordinate_status="same_grid_reviewed")
    with pytest.raises(ValueError, match="unknown variable"):
        _read(path, declared_units={"missing": ("Pa", "unsupported")})


def test_rejects_exposure_duration_on_non_morphology_file(tmp_path):
    path = tmp_path / "stress.mat"
    scipy_io.savemat(path, {"sxx": np.ones((1, 1))})
    with pytest.raises(ValueError, match="surface-morphology"):
        _read(path, exposure_duration_days=2.0)
