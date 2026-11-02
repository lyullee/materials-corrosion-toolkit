"""Safely audit numeric MATLAB arrays from local-pitting research datasets.

The reader preserves file and array structure.  It deliberately does not infer
coordinates, units, registration, pit geometry, growth, or state transitions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract

MAX_REVIEWED_MAT_BYTES = 128 * 1024 * 1024
MAX_REVIEWED_DECODED_BYTES = 512 * 1024 * 1024
_NUMERIC_MATLAB_CLASSES = frozenset(
    {
        "double",
        "single",
        "int8",
        "uint8",
        "int16",
        "uint16",
        "int32",
        "uint32",
        "int64",
        "uint64",
        "logical",
    }
)
_MATLAB_CLASS_BYTES = {
    "double": 8,
    "single": 4,
    "int8": 1,
    "uint8": 1,
    "int16": 2,
    "uint16": 2,
    "int32": 4,
    "uint32": 4,
    "int64": 8,
    "uint64": 8,
    "logical": 1,
}


class NumericMatVariableRecord(Contract):
    """Structural and finite-value audit for one numeric MATLAB variable."""

    schema_version: Literal["matintegrity.numeric_mat_variable_record.v1"] = (
        "matintegrity.numeric_mat_variable_record.v1"
    )
    variable_name: str = Field(min_length=1)
    matlab_class: str = Field(min_length=1)
    numpy_dtype: str = Field(min_length=1)
    shape: tuple[int, ...]
    element_count: int = Field(ge=0)
    finite_count: int = Field(ge=0)
    nonfinite_count: int = Field(ge=0)
    finite_minimum: float | int | None = None
    finite_maximum: float | int | None = None
    declared_unit: str | None = None
    unit_basis: str | None = None

    @model_validator(mode="after")
    def counts_and_units_are_consistent(self):
        expected = 1
        for size in self.shape:
            if size < 0:
                raise ValueError("MAT variable dimensions cannot be negative")
            expected *= size
        if expected != self.element_count:
            raise ValueError("MAT variable shape does not match its element count")
        if self.finite_count + self.nonfinite_count != self.element_count:
            raise ValueError("MAT finite and nonfinite counts must cover every element")
        if (self.declared_unit is None) != (self.unit_basis is None):
            raise ValueError("a MAT variable unit and its basis must be supplied together")
        return self


class LocalPittingMatRecord(Contract):
    """File-level provenance for one numeric local-pitting MAT file."""

    schema_version: Literal["matintegrity.local_pitting_mat_record.v1"] = (
        "matintegrity.local_pitting_mat_record.v1"
    )
    dataset_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_role: Literal["surface_morphology", "stress_field", "strain_field", "user_numeric_field"]
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bytes: int = Field(gt=0)
    mat_format: Literal["matlab_level_5_numeric"]
    exposure_duration_days: float | None = Field(default=None, gt=0)
    variables: tuple[NumericMatVariableRecord, ...]
    coordinate_status: Literal[
        "unreviewed",
        "same_grid_reviewed",
        "registered_with_transform_reviewed",
    ] = "unreviewed"
    coordinate_basis: str | None = None
    physical_specimen_independence: Literal["one_specimen_repeated_locations"] = (
        "one_specimen_repeated_locations"
    )
    interpretation_status: Literal["file_structure_only", "caller_reviewed_variable_meanings"] = (
        "file_structure_only"
    )
    interpretation_basis: str | None = None

    @model_validator(mode="after")
    def review_claims_have_bases(self):
        if not self.variables:
            raise ValueError("at least one numeric MAT variable is required")
        names = [item.variable_name for item in self.variables]
        if len(names) != len(set(names)):
            raise ValueError("MAT variable names must be unique")
        if self.coordinate_status != "unreviewed" and not self.coordinate_basis:
            raise ValueError("reviewed MAT coordinates require a coordinate basis")
        if self.coordinate_status == "unreviewed" and self.coordinate_basis is not None:
            raise ValueError("unreviewed MAT coordinates cannot carry a reviewed basis")
        if (
            self.interpretation_status == "caller_reviewed_variable_meanings"
            and not self.interpretation_basis
        ):
            raise ValueError("reviewed MAT variable meanings require an interpretation basis")
        if self.interpretation_status == "file_structure_only" and self.interpretation_basis is not None:
            raise ValueError("file-structure-only records cannot carry an interpretation basis")
        if self.source_role != "surface_morphology" and self.exposure_duration_days is not None:
            raise ValueError("exposure duration is only attached to surface-morphology files")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_local_pitting_numeric_mat(
    path: str | Path,
    *,
    expected_sha256: str,
    dataset_id: str,
    physical_specimen_id: str,
    source_group_id: str,
    source_role: Literal["surface_morphology", "stress_field", "strain_field", "user_numeric_field"],
    exposure_duration_days: float | None = None,
    declared_units: dict[str, tuple[str, str]] | None = None,
    coordinate_status: Literal[
        "unreviewed",
        "same_grid_reviewed",
        "registered_with_transform_reviewed",
    ] = "unreviewed",
    coordinate_basis: str | None = None,
    interpretation_status: Literal[
        "file_structure_only", "caller_reviewed_variable_meanings"
    ] = "file_structure_only",
    interpretation_basis: str | None = None,
) -> dict:
    """Read only top-level real numeric arrays from a checksum-pinned level-5 MAT file.

    MATLAB structs, cells, objects, sparse arrays, complex arrays, nested content,
    and HDF5/v7.3 files are rejected.  Returned arrays are copies and are not
    rescaled, transposed, registered, thresholded, or interpreted.
    """
    for value, label in (
        (expected_sha256, "expected SHA-256"),
        (dataset_id, "dataset identity"),
        (physical_specimen_id, "physical specimen identity"),
        (source_group_id, "source-group identity"),
    ):
        if not value.strip():
            raise ValueError(f"{label} is required")
    if len(expected_sha256) != 64 or any(char not in "0123456789abcdef" for char in expected_sha256):
        raise ValueError("expected SHA-256 must be 64 lowercase hexadecimal characters")

    source = Path(path).resolve()
    source_bytes = source.stat().st_size
    if source_bytes <= 0 or source_bytes > MAX_REVIEWED_MAT_BYTES:
        raise ValueError("MAT file is empty or exceeds the reviewed reader safety limit")
    source_sha256 = _sha256(source)
    if source_sha256 != expected_sha256:
        raise ValueError("MAT file SHA-256 differs from the caller-pinned digest")

    try:
        import h5py
        from scipy.io import loadmat, whosmat
    except ImportError as exc:
        raise ImportError("MAT reading requires the optional science dependencies scipy and h5py") from exc
    if h5py.is_hdf5(source):
        raise ValueError("MATLAB v7.3/HDF5 files are outside this reviewed numeric reader")

    declarations = whosmat(source)
    if not declarations:
        raise ValueError("MAT file contains no declared variables")
    if len(declarations) > 256:
        raise ValueError("MAT file contains too many top-level variables")
    names = []
    classes: dict[str, str] = {}
    estimated_decoded_bytes = 0
    for name, shape, matlab_class in declarations:
        if not name or name.startswith("__"):
            raise ValueError("MAT file contains an invalid user variable name")
        if matlab_class not in _NUMERIC_MATLAB_CLASSES:
            raise ValueError(f"MAT variable {name!r} has unsupported class {matlab_class!r}")
        names.append(name)
        classes[name] = matlab_class
        elements = 1
        for size in shape:
            if size < 0:
                raise ValueError("MAT file declares a negative array dimension")
            elements *= size
        estimated_decoded_bytes += elements * _MATLAB_CLASS_BYTES[matlab_class]
        if estimated_decoded_bytes > MAX_REVIEWED_DECODED_BYTES:
            raise ValueError("MAT variables exceed the reviewed decoded-memory limit")
    if len(names) != len(set(names)):
        raise ValueError("MAT file declares duplicate variable names")

    loaded = loadmat(
        source,
        variable_names=names,
        appendmat=False,
        chars_as_strings=False,
        mat_dtype=False,
        squeeze_me=False,
        struct_as_record=True,
        verify_compressed_data_integrity=True,
    )
    units = declared_units or {}
    if set(units) - set(names):
        raise ValueError("declared MAT units contain unknown variable names")
    arrays: dict[str, np.ndarray] = {}
    records = []
    for name in names:
        value = np.asarray(loaded[name])
        if value.dtype.kind not in "biuf" or np.iscomplexobj(value) or value.dtype.hasobject:
            raise ValueError(f"MAT variable {name!r} did not decode as a real numeric array")
        value = value.copy()
        finite = np.isfinite(value)
        finite_values = value[finite]
        unit = units.get(name)
        records.append(
            NumericMatVariableRecord(
                variable_name=name,
                matlab_class=classes[name],
                numpy_dtype=value.dtype.str,
                shape=tuple(int(size) for size in value.shape),
                element_count=int(value.size),
                finite_count=int(finite.sum()),
                nonfinite_count=int(value.size - finite.sum()),
                finite_minimum=(finite_values.min().item() if finite_values.size else None),
                finite_maximum=(finite_values.max().item() if finite_values.size else None),
                declared_unit=unit[0] if unit else None,
                unit_basis=unit[1] if unit else None,
            )
        )
        arrays[name] = value

    metadata = LocalPittingMatRecord(
        dataset_id=dataset_id,
        physical_specimen_id=physical_specimen_id,
        source_group_id=source_group_id,
        source_role=source_role,
        source_filename=source.name,
        source_sha256=source_sha256,
        source_bytes=source_bytes,
        mat_format="matlab_level_5_numeric",
        exposure_duration_days=exposure_duration_days,
        variables=tuple(records),
        coordinate_status=coordinate_status,
        coordinate_basis=coordinate_basis,
        interpretation_status=interpretation_status,
        interpretation_basis=interpretation_basis,
    )
    return {"metadata": metadata, "raw_arrays": arrays}
