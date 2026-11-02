"""Digest-pinned numeric NPY FMC matrices with bounded working point chunks."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID
from .fmc_tfm import (
    FmcElement,
    HomogeneousFmcTfm,
    TfmImagePoint,
    _fmc_from_times,
    _fmc_lineage,
    _validate_fmc_membership,
)
from .planar_multiview_tfm import PlanarMultiviewFmcTfm, _planar_multiview_from_reader


class StoredFmcTrace(Contract):
    trace_id: str = Field(min_length=1)
    transmit_element_id: str = Field(min_length=1)
    receive_element_id: str = Field(min_length=1)
    storage_row_index: int = Field(ge=0)
    sample_bytes_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class FmcNpyMatrix(Contract):
    path: str = Field(min_length=1)
    file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    derivation_basis_id: str = Field(min_length=1)
    layout: Literal["trace_by_sample"]
    dtype: Literal["<f4", "<f8", ">f4", ">f8", "<i2", ">i2", "<i4", ">i4"]
    immutable_during_run_confirmed: bool
    maximum_file_bytes: int = Field(default=2147483648, ge=1, le=68719476736)
    maximum_frame_samples: int = Field(default=50000000, ge=2, le=4000000000)
    maximum_points_per_chunk: int = Field(default=16, ge=1, le=4096)
    maximum_working_contributions: int = Field(default=1000000, ge=1, le=16000000)
    cached_trace_rows: int = Field(default=16, ge=0, le=4096)


def _validate_stored_frame(x):
    _validate_fmc_membership(x)
    if {row.storage_row_index for row in x.traces} != set(range(len(x.traces))):
        raise ValueError("storage row mapping must be a unique complete permutation of matrix rows")
    return x


class FileHomogeneousFmcTfm(HomogeneousFmcTfm):
    propagation_model: Literal["file_homogeneous_isotropic_direct_longitudinal"]
    elements: tuple[FmcElement, ...] = Field(min_length=1, max_length=256)
    traces: tuple[StoredFmcTrace, ...] = Field(min_length=1, max_length=65536)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=131072)
    image_points: tuple[TfmImagePoint, ...] = Field(min_length=1, max_length=65536)
    maximum_point_trace_evaluations: int = Field(default=100000000, ge=1, le=10000000000)
    matrix: FmcNpyMatrix

    @model_validator(mode="after")
    def exact_frame_membership(self):
        # Replaces the in-memory sample validator: the file reader verifies actual rows.
        return _validate_stored_frame(self)


class FilePlanarMultiviewFmcTfm(PlanarMultiviewFmcTfm):
    propagation_model: Literal["file_planar_two_medium_transmission_and_same_mode_backwall"]
    elements: tuple[FmcElement, ...] = Field(min_length=1, max_length=256)
    traces: tuple[StoredFmcTrace, ...] = Field(min_length=1, max_length=65536)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=131072)
    image_points: tuple[TfmImagePoint, ...] = Field(min_length=1, max_length=65536)
    maximum_point_trace_evaluations: int = Field(default=100000000, ge=1, le=10000000000)
    matrix: FmcNpyMatrix

    @model_validator(mode="after")
    def exact_frame_membership(self):
        return _validate_stored_frame(self)


def _file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8388608), b""):
            digest.update(block)
    return digest.hexdigest()


def _signature(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ino


class _FmcStoredDataError(ValueError):
    pass


def _file_fmc_tfm(x, *, planar):
    import numpy as np

    matrix_spec = x.matrix
    base = _fmc_lineage(x) | {
        "matrix_file_sha256": matrix_spec.file_sha256,
        "matrix_derivation_basis_id": matrix_spec.derivation_basis_id,
        "matrix_layout": matrix_spec.layout,
        "matrix_dtype": matrix_spec.dtype,
    }
    if not matrix_spec.immutable_during_run_confirmed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Caller confirmation that the matrix remains immutable during this read is required.",),
        )
    nviews = len(x.views) if planar else 1
    total = len(x.image_points) * len(x.traces) * nviews
    if (
        total > x.maximum_point_trace_evaluations
        or len(x.traces) * len(x.time_s) > matrix_spec.maximum_frame_samples
    ):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The total reconstruction or frame-sample budget is exceeded.",),
        )
    chunk_size = min(
        matrix_spec.maximum_points_per_chunk,
        matrix_spec.maximum_working_contributions // len(x.traces),
        len(x.image_points),
    )
    if chunk_size < 1:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The working contribution budget cannot hold one complete FMC point.",),
        )
    path = Path(matrix_spec.path).expanduser().resolve()
    matrix = None
    read_samples = None
    try:
        before = _signature(path)
        if before[0] > matrix_spec.maximum_file_bytes:
            return Calculation(
                status="out_of_scope",
                values=base,
                notes=("The numeric matrix file exceeds the caller byte budget.",),
            )
        if _file_sha256(path) != matrix_spec.file_sha256:
            return Calculation(status="out_of_scope", values=base, notes=("Matrix file digest mismatch.",))
        matrix = np.load(path, mmap_mode="r", allow_pickle=False, max_header_size=10000)
        if not isinstance(matrix, np.memmap):
            raise _FmcStoredDataError("Only a standalone memory-mapped numeric NPY array is supported.")
        if matrix.shape != (len(x.traces), len(x.time_s)) or matrix.dtype.str != matrix_spec.dtype:
            raise _FmcStoredDataError("Matrix shape/dtype disagrees with the explicit trace/sample manifest.")

        @lru_cache(maxsize=matrix_spec.cached_trace_rows)
        def read_samples(index):
            record = x.traces[index]
            row = matrix[record.storage_row_index, :]
            if hashlib.sha256(row.tobytes(order="C")).hexdigest() != record.sample_bytes_sha256:
                raise _FmcStoredDataError("Stored trace row byte digest mismatch.")
            samples = np.asarray(row, dtype=float)
            if not np.all(np.isfinite(samples)):
                raise _FmcStoredDataError("Stored trace contains nonfinite samples.")
            return samples

        image = []
        views = None
        summaries = {}
        common = None
        chunks = 0
        for start in range(0, len(x.image_points), chunk_size):
            points = x.image_points[start : start + chunk_size]
            if planar:
                result = _planar_multiview_from_reader(x, sample_reader=read_samples, image_points=points)
            else:
                coords = np.asarray([row.position_m for row in points])
                elements = np.asarray([row.position_m for row in x.elements])
                with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
                    one_way = (
                        np.hypot.reduce(coords[:, None, :] - elements[None, :, :], axis=2)
                        / x.longitudinal_velocity_m_s
                    )
                result = _fmc_from_times(
                    x, one_way, one_way, path_notes=(), sample_reader=read_samples, image_points=points
                )
            if result.status != "computed":
                values = {key: value for key, value in result.values.items() if key not in ("image", "views")}
                return Calculation(
                    status=result.status,
                    values=values | base | {"unsupported_chunk_start_index": start},
                    notes=result.notes,
                )
            chunks += 1
            common = {
                key: value
                for key, value in result.values.items()
                if key not in ("image", "views", "ray_summaries", "point_trace_evaluations")
            }
            if planar:
                if views is None:
                    views = [
                        {key: value for key, value in view.items() if key != "image"} | {"image": []}
                        for view in result.values["views"]
                    ]
                for target, source in zip(views, result.values["views"], strict=True):
                    if target["view_id"] != source["view_id"]:
                        raise _FmcStoredDataError("View identity changed across point chunks.")
                    target["image"].extend(source["image"])
                for row in result.values["ray_summaries"]:
                    key = row["material_mode"], row["backwall_reflection"]
                    if key not in summaries:
                        summaries[key] = dict(row)
                    else:
                        for field in (
                            "maximum_normalized_snell_residual",
                            "maximum_fraction_bracket_width",
                            "maximum_iterations_used",
                            "maximum_one_way_time_s",
                        ):
                            summaries[key][field] = max(summaries[key][field], row[field])
                        summaries[key]["minimum_one_way_time_s"] = min(
                            summaries[key]["minimum_one_way_time_s"], row["minimum_one_way_time_s"]
                        )
            else:
                image.extend(result.values["image"])
        if _signature(path) != before or _file_sha256(path) != matrix_spec.file_sha256:
            raise _FmcStoredDataError("Matrix file changed during reconstruction.")
        payload = {"views": views, "ray_summaries": list(summaries.values())} if planar else {"image": image}
        return Calculation(
            values=common
            | base
            | payload
            | {
                "point_trace_evaluations": total,
                "point_chunks_processed": chunks,
                "effective_points_per_chunk": chunk_size,
                "maximum_working_contributions_used": chunk_size * len(x.traces),
                "matrix_file_bytes": before[0],
                "matrix_rechecked_after_run": True,
            },
            notes=(
                "Read-only numeric NPY mapping with exact file/row hashes, explicit dtype and trace/sample roles; no pickle, scaling, missing-pair synthesis or waveform-matrix copy is used.",
                "All point chunks and all views must succeed before any image is returned. Point order, trace lineage and signed amplitudes are preserved.",
                "Working contribution arrays are bounded; final images and metadata still occupy memory. File consistency checks rely on caller immutability and do not establish physical inspection qualification.",
            ),
        )
    except FileNotFoundError:
        return Calculation(
            status="needs_data", values=base, notes=("The declared local numeric FMC matrix is unavailable.",)
        )
    except (OSError, ValueError, EOFError) as exc:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=(f"Numeric FMC matrix read withheld: {type(exc).__name__}: {exc}",),
        )
    finally:
        if read_samples is not None:
            read_samples.cache_clear()
        if isinstance(matrix, np.memmap):
            matrix._mmap.close()
        elif matrix is not None and hasattr(matrix, "close"):
            matrix.close()


def file_homogeneous_fmc_tfm(x: FileHomogeneousFmcTfm) -> Calculation:
    if x.propagation_model != "file_homogeneous_isotropic_direct_longitudinal":
        return Calculation(
            status="out_of_scope",
            values=_fmc_lineage(x),
            notes=("The file direct-path evaluator requires its declared propagation model.",),
        )
    return _file_fmc_tfm(x, planar=False)


def file_planar_multiview_fmc_tfm(x: FilePlanarMultiviewFmcTfm) -> Calculation:
    if x.propagation_model != "file_planar_two_medium_transmission_and_same_mode_backwall":
        return Calculation(
            status="out_of_scope",
            values=_fmc_lineage(x),
            notes=("The file planar evaluator requires its declared propagation model.",),
        )
    return _file_fmc_tfm(x, planar=True)


def specifications():
    assumptions = (
        "Numeric NPY storage, dtype, complete ordered-pair row manifest and a common sample clock are explicit and digest-bound.",
        "The caller confirms the file is immutable; full-file hashes and metadata are checked before and after reading, and each accessed row is checked.",
        "Every requested point and view must be inside the selected propagation and observed-clock scope; no partial image is published.",
    )
    return [
        ModelSpec(
            identifier,
            contract,
            evaluator,
            {
                (
                    "views[].image[].position_m"
                    if contract is FilePlanarMultiviewFmcTfm
                    else "image[].position_m"
                ): "m",
                (
                    "views[].image[].coherent_amplitude"
                    if contract is FilePlanarMultiviewFmcTfm
                    else "image[].coherent_amplitude"
                ): "caller_declared",
                "point_trace_evaluations": "1",
                "maximum_working_contributions_used": "1",
                "matrix_file_bytes": "byte",
            },
            assumptions,
            (SOURCE_ID,),
            qualification="user_model",
        )
        for identifier, contract, evaluator in (
            ("inspection.file_homogeneous_fmc_tfm", FileHomogeneousFmcTfm, file_homogeneous_fmc_tfm),
            (
                "inspection.file_planar_multiview_fmc_tfm",
                FilePlanarMultiviewFmcTfm,
                file_planar_multiview_fmc_tfm,
            ),
        )
    ]
