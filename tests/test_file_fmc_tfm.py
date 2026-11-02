import hashlib

import numpy as np
import pytest
from pydantic import TypeAdapter

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models import file_fmc_tfm as module
from matintegrity.models.file_fmc_tfm import (
    FileHomogeneousFmcTfm,
    FilePlanarMultiviewFmcTfm,
    FmcNpyMatrix,
    StoredFmcTrace,
    file_homogeneous_fmc_tfm,
    file_planar_multiview_fmc_tfm,
)
from matintegrity.models.fmc_tfm import FmcElement, TfmImagePoint, homogeneous_fmc_tfm
from matintegrity.models.planar_multiview_tfm import PlanarTfmView, planar_multiview_fmc_tfm
from matintegrity.registry import default_registry


def bind(cls, raw):
    raw = {
        name: TypeAdapter(cls.model_fields[name].annotation).validate_python(value)
        for name, value in raw.items()
    }
    digest = canonical_digest(cls.model_construct(**raw).model_dump(mode="json", exclude={"basis"}))
    return cls(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored stored RF matrix.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def rebuild(x, **updates):
    raw = x.model_dump(exclude={"basis"})
    raw.update(updates)
    return bind(type(x), raw)


def frame(tmp_path, *, planar=False, dtype="<f8", chunk=1, permutation=(2, 0, 3, 1), n=2, points=None):
    path = tmp_path / ("planar.npy" if planar else "direct.npy")
    ids = [str(i) for i in range(n)]
    pairs = [(tx, rx) for tx in ids for rx in ids]
    permutation = tuple(range(len(pairs))) if n != 2 else permutation
    array = np.empty((len(pairs), 3), dtype=dtype)
    traces = []
    for i, (tx, rx) in enumerate(pairs):
        samples = np.asarray(
            (0.0, 10.0 * (i + 1), 20.0 * (i + 1)) if n == 2 else (2.0, 2.0, 2.0), dtype=dtype
        )
        array[permutation[i], :] = samples
        traces.append(
            StoredFmcTrace(
                trace_id=f"{tx}:{rx}",
                transmit_element_id=tx,
                receive_element_id=rx,
                storage_row_index=permutation[i],
                sample_bytes_sha256=hashlib.sha256(samples.tobytes(order="C")).hexdigest(),
            )
        )
    np.save(path, array, allow_pickle=False)
    elements = tuple(
        FmcElement(
            element_id=i,
            position_m=(float(index) * 3.0 if n == 2 else float(index) * 0.001, 0.0, -3.0 if planar else 0.0),
        )
        for index, i in enumerate(ids)
    )
    if points is None:
        positions = (
            ((0.0, 0.0, 2.0), (0.0, 0.0, 3.0))
            if planar
            else ((0.0, 0.0, 4.0), (3.0, 0.0, 4.0), (0.0, 0.0, 0.0))
        )
        points = tuple(
            TfmImagePoint(point_id=f"p{i}", position_m=position) for i, position in enumerate(positions)
        )
    raw = dict(
        acquisition_id="stored-frame",
        physical_specimen_id="coupon",
        physical_scope_id="volume",
        source_group_id="authored",
        material_condition_id="medium",
        probe_id="probe",
        coordinate_frame_id="frame",
        sample_clock_id="clock",
        time_zero_basis_id="t0",
        velocity_basis_id="c",
        raw_record_sha256="a" * 64,
        amplitude_unit="authored",
        aggregation="coherent_sum",
        excitation_time_origin_s=0.0,
        longitudinal_velocity_m_s=2.0 if planar else 1.0,
        time_s=(0.0, 10.0, 20.0),
        elements=elements,
        traces=tuple(traces),
        image_points=points,
        matrix=FmcNpyMatrix(
            path=str(path),
            file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            derivation_basis_id="authored-matrix",
            layout="trace_by_sample",
            dtype=dtype,
            immutable_during_run_confirmed=True,
            maximum_points_per_chunk=chunk,
        ),
    )
    if planar:
        raw.update(
            propagation_model="file_planar_two_medium_transmission_and_same_mode_backwall",
            couplant_condition_id="couplant",
            couplant_velocity_basis_id="c1",
            interface_geometry_basis_id="plane",
            interface_z_m=0.0,
            couplant_longitudinal_velocity_m_s=1.0,
            backwall_z_m=5.0,
            views=tuple(
                PlanarTfmView(
                    view_id=name,
                    transmit_material_mode="longitudinal",
                    receive_material_mode="longitudinal",
                    transmit_backwall_reflection=tb,
                    receive_backwall_reflection=rb,
                )
                for name, tb, rb in (
                    ("DD", False, False),
                    ("DR", False, True),
                    ("RD", True, False),
                    ("RR", True, True),
                )
            ),
        )
    else:
        raw["propagation_model"] = "file_homogeneous_isotropic_direct_longitudinal"
    return bind(FilePlanarMultiviewFmcTfm if planar else FileHomogeneousFmcTfm, raw)


def amplitudes(result):
    return [row["coherent_amplitude"] for row in result.values["image"]]


def test_explicit_permuted_row_roles_and_chunk_order(tmp_path):
    x = frame(tmp_path)
    result = file_homogeneous_fmc_tfm(x)
    assert result.status == "computed"
    assert amplitudes(result) == [93.0, 87.0, 39.0]
    assert result.values["point_chunks_processed"] == 3
    assert result.values["maximum_working_contributions_used"] == 4
    assert [r["storage_row_index"] for r in result.values["trace_records"]] == [2, 0, 3, 1]
    assert module._file_sha256(__import__("pathlib").Path(x.matrix.path)) == x.matrix.file_sha256


def test_larger_point_chunks_preserve_all_amplitudes(tmp_path):
    a = file_homogeneous_fmc_tfm(frame(tmp_path, chunk=1))
    b = file_homogeneous_fmc_tfm(frame(tmp_path, chunk=3))
    assert amplitudes(a) == amplitudes(b)
    assert b.values["point_chunks_processed"] == 1


@pytest.mark.parametrize("dtype", ["<f4", ">f8", "<i2", ">i4"])
def test_declared_float_integer_and_byte_order_are_preserved(tmp_path, dtype):
    result = file_homogeneous_fmc_tfm(frame(tmp_path, dtype=dtype))
    assert result.status == "computed"
    assert amplitudes(result) == [93.0, 87.0, 39.0]
    assert result.values["matrix_dtype"] == dtype


def test_planar_multiview_chunking_preserves_views_and_ray_summary(tmp_path):
    x = frame(tmp_path, planar=True, n=1)
    a = file_planar_multiview_fmc_tfm(x)
    b = file_planar_multiview_fmc_tfm(
        rebuild(x, matrix=x.matrix.model_copy(update={"maximum_points_per_chunk": 2}))
    )
    assert a.status == b.status == "computed"
    assert a.values["views"] == b.values["views"]
    assert a.values["ray_summaries"] == b.values["ray_summaries"]
    assert a.values["point_trace_evaluations"] == 8


def test_file_hash_mismatch_withholds_image(tmp_path):
    x = frame(tmp_path)
    result = file_homogeneous_fmc_tfm(
        rebuild(x, matrix=x.matrix.model_copy(update={"file_sha256": "b" * 64}))
    )
    assert result.status == "out_of_scope"
    assert "image" not in result.values


def test_row_byte_hash_mismatch_withholds_image(tmp_path):
    x = frame(tmp_path)
    traces = (x.traces[0].model_copy(update={"sample_bytes_sha256": "b" * 64}),) + x.traces[1:]
    assert file_homogeneous_fmc_tfm(rebuild(x, traces=traces)).status == "out_of_scope"


@pytest.mark.parametrize("kind", ["shape", "dtype", "object", "nonfinite"])
def test_wrong_or_nonfinite_numeric_storage_is_not_repaired(tmp_path, kind):
    x = frame(tmp_path)
    array = np.zeros((4, 3))
    if kind == "shape":
        array = np.zeros((3, 4))
    elif kind == "dtype":
        array = array.astype("<f4")
    elif kind == "object":
        array = np.asarray([[{}]], dtype=object)
    else:
        array[0, 0] = np.nan
    np.save(x.matrix.path, array, allow_pickle=True)
    x = rebuild(
        x,
        matrix=x.matrix.model_copy(
            update={
                "file_sha256": hashlib.sha256(
                    __import__("pathlib").Path(x.matrix.path).read_bytes()
                ).hexdigest()
            }
        ),
    )
    if kind == "nonfinite":
        traces = tuple(
            row.model_copy(
                update={
                    "sample_bytes_sha256": hashlib.sha256(array[row.storage_row_index].tobytes()).hexdigest()
                }
            )
            for row in x.traces
        )
        x = rebuild(x, traces=traces)
    result = file_homogeneous_fmc_tfm(x)
    assert result.status == "out_of_scope"
    assert "image" not in result.values


def test_reused_storage_row_mapping_is_rejected(tmp_path):
    x = frame(tmp_path)
    with pytest.raises(ValueError, match="row mapping"):
        rebuild(x, traces=(x.traces[0].model_copy(update={"storage_row_index": 0}),) + x.traces[1:])


@pytest.mark.parametrize(
    "field,value",
    [("maximum_file_bytes", 1), ("maximum_frame_samples", 2), ("maximum_working_contributions", 3)],
)
def test_file_sample_and_working_budgets_withhold_complete_image(tmp_path, field, value):
    x = frame(tmp_path)
    result = file_homogeneous_fmc_tfm(rebuild(x, matrix=x.matrix.model_copy(update={field: value})))
    assert result.status == "out_of_scope"
    assert "image" not in result.values


def test_unconfirmed_file_consistency_needs_data_before_read(tmp_path, monkeypatch):
    x = frame(tmp_path)

    def forbidden(*args):
        raise AssertionError("unconfirmed file must not be read")

    monkeypatch.setattr(module, "_file_sha256", forbidden)
    assert (
        file_homogeneous_fmc_tfm(
            rebuild(x, matrix=x.matrix.model_copy(update={"immutable_during_run_confirmed": False}))
        ).status
        == "needs_data"
    )


def test_missing_matrix_needs_data(tmp_path):
    x = frame(tmp_path)
    assert (
        file_homogeneous_fmc_tfm(
            rebuild(x, matrix=x.matrix.model_copy(update={"path": str(tmp_path / "missing.npy")}))
        ).status
        == "needs_data"
    )


def test_after_read_digest_change_discards_previously_computed_image(tmp_path, monkeypatch):
    x = frame(tmp_path)
    original = module._file_sha256
    calls = 0

    def changed(path):
        nonlocal calls
        calls += 1
        return original(path) if calls == 1 else "b" * 64

    monkeypatch.setattr(module, "_file_sha256", changed)
    result = file_homogeneous_fmc_tfm(x)
    assert result.status == "out_of_scope"
    assert "image" not in result.values


def test_late_chunk_failure_does_not_return_earlier_points(tmp_path):
    x = frame(tmp_path)
    points = x.image_points[:2] + (TfmImagePoint(point_id="far", position_m=(0.0, 0.0, 100.0)),)
    result = file_homogeneous_fmc_tfm(rebuild(x, image_points=points))
    assert result.status == "out_of_scope"
    assert result.values["unsupported_chunk_start_index"] == 2
    assert "image" not in result.values


def test_storage_change_breaks_full_request_digest(tmp_path):
    raw = frame(tmp_path).model_dump()
    raw["matrix"]["dtype"] = "<f4"
    with pytest.raises(ValueError, match="pin the complete"):
        FileHomogeneousFmcTfm.model_validate(raw)


def test_memory_evaluators_do_not_accept_file_storage_contracts(tmp_path):
    assert homogeneous_fmc_tfm(frame(tmp_path)).status == "out_of_scope"
    assert planar_multiview_fmc_tfm(frame(tmp_path, planar=True, n=1)).status == "out_of_scope"


def test_full_256_element_frame_is_reconstructed_with_bounded_working_array(tmp_path):
    point = (TfmImagePoint(point_id="target", position_m=(0.0, 0.0, 1.0)),)
    x = rebuild(frame(tmp_path, n=256, points=point), aggregation="coherent_mean")
    result = file_homogeneous_fmc_tfm(x)
    assert result.status == "computed"
    assert amplitudes(result) == [2.0]
    assert result.values["point_trace_evaluations"] == 65536
    assert result.values["maximum_working_contributions_used"] == 65536


@pytest.mark.parametrize("planar", [False, True])
def test_public_python_json_exchange(tmp_path, planar):
    x = frame(tmp_path, planar=planar, n=1 if planar else 2)
    identifier = (
        "inspection.file_planar_multiview_fmc_tfm" if planar else "inspection.file_homogeneous_fmc_tfm"
    )
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="coupon", time_basis="clock")
    a = registry.run(identifier, x, context)
    b = registry.run_json(identifier, x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
