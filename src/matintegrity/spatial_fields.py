"""Exchange and sample reviewed rectilinear fields without implicit registration."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract


def numeric_array_digest(values: np.ndarray) -> str:
    """Hash dtype, shape and C-order bytes without rescaling or canonicalizing values."""
    array = np.asarray(values)
    if array.dtype.hasobject:
        raise ValueError("object arrays cannot be bound to a numeric field")
    header = json.dumps(
        {"dtype": array.dtype.str, "shape": list(array.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(np.ascontiguousarray(array).tobytes(order="C"))
    return digest.hexdigest()


class RectilinearFieldMetadata(Contract):
    """Coordinates and provenance bound to one separately supplied numeric array."""

    schema_version: Literal["matintegrity.rectilinear_field_metadata.v1"] = (
        "matintegrity.rectilinear_field_metadata.v1"
    )
    field_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    array_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    missing_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    quantity_name: str = Field(min_length=1)
    quantity_unit: str = Field(min_length=1)
    quantity_basis: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_basis: str = Field(min_length=1)
    observation_clock: str = Field(min_length=1)
    x_coordinates_m: tuple[float, ...] = Field(min_length=2)
    y_coordinates_m: tuple[float, ...] = Field(min_length=2)
    value_shape: tuple[int, int]
    missing_value_meaning: str = Field(min_length=1)

    @model_validator(mode="after")
    def axes_and_shape_are_consistent(self):
        for axis, label in (
            (self.x_coordinates_m, "x"),
            (self.y_coordinates_m, "y"),
        ):
            if not all(math.isfinite(value) for value in axis):
                raise ValueError(f"{label} coordinates must be finite")
            if any(right <= left for left, right in zip(axis, axis[1:], strict=False)):
                raise ValueError(f"{label} coordinates must be strictly increasing")
        if self.value_shape != (len(self.y_coordinates_m), len(self.x_coordinates_m)):
            raise ValueError("field value shape must align as y rows by x columns")
        return self


class PlanarAffineCoordinateTransform(Contract):
    """Reviewed direct map from query coordinates into the source-field frame."""

    schema_version: Literal["matintegrity.planar_affine_coordinate_transform.v1"] = (
        "matintegrity.planar_affine_coordinate_transform.v1"
    )
    from_frame_id: str = Field(min_length=1)
    to_frame_id: str = Field(min_length=1)
    x_from_x: float
    x_from_y: float
    x_offset_m: float
    y_from_x: float
    y_from_y: float
    y_offset_m: float
    transform_basis: str = Field(min_length=1)
    registration_reviewed: Literal[True]

    @model_validator(mode="after")
    def finite_and_nonsingular(self):
        values = (
            self.x_from_x,
            self.x_from_y,
            self.x_offset_m,
            self.y_from_x,
            self.y_from_y,
            self.y_offset_m,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("affine-transform coefficients must be finite")
        determinant = self.x_from_x * self.y_from_y - self.x_from_y * self.y_from_x
        if not math.isfinite(determinant) or determinant == 0:
            raise ValueError("affine-transform linear part must be nonsingular")
        return self


class RectilinearFieldSamplingRequest(Contract):
    """Ordered target points and explicit interpolation/error policies."""

    schema_version: Literal["matintegrity.rectilinear_field_sampling_request.v1"] = (
        "matintegrity.rectilinear_field_sampling_request.v1"
    )
    query_id: str = Field(min_length=1)
    query_frame_id: str = Field(min_length=1)
    point_ids: tuple[str, ...] = Field(min_length=1)
    x_coordinates_m: tuple[float, ...] = Field(min_length=1)
    y_coordinates_m: tuple[float, ...] = Field(min_length=1)
    interpolation: Literal["nearest", "bilinear"]
    outside_support_policy: Literal["reject", "return_missing"]
    missing_support_policy: Literal["reject", "return_missing"]
    interpolation_review_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def points_are_aligned(self):
        size = len(self.point_ids)
        if len(self.x_coordinates_m) != size or len(self.y_coordinates_m) != size:
            raise ValueError("query point IDs and coordinates must align")
        if len(set(self.point_ids)) != size or any(not item.strip() for item in self.point_ids):
            raise ValueError("query point IDs must be unique and nonempty")
        if not all(math.isfinite(value) for value in self.x_coordinates_m + self.y_coordinates_m):
            raise ValueError("query coordinates must be finite")
        return self


class RectilinearFieldSamplingResult(Contract):
    """Ordered sampled values with explicit outside/missing statuses."""

    schema_version: Literal["matintegrity.rectilinear_field_sampling_result.v1"] = (
        "matintegrity.rectilinear_field_sampling_result.v1"
    )
    query_id: str = Field(min_length=1)
    field_id: str = Field(min_length=1)
    source_array_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_missing_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    query_frame_id: str = Field(min_length=1)
    source_frame_id: str = Field(min_length=1)
    transform_schema_version: str | None = None
    transform_basis: str | None = None
    interpolation: Literal["nearest", "bilinear"]
    quantity_name: str = Field(min_length=1)
    quantity_unit: str = Field(min_length=1)
    point_ids: tuple[str, ...]
    source_x_coordinates_m: tuple[float, ...]
    source_y_coordinates_m: tuple[float, ...]
    values: tuple[float | None, ...]
    statuses: tuple[Literal["sampled", "outside_support", "missing_support"], ...]

    @model_validator(mode="after")
    def outputs_are_aligned(self):
        size = len(self.point_ids)
        for values in (
            self.source_x_coordinates_m,
            self.source_y_coordinates_m,
            self.values,
            self.statuses,
        ):
            if len(values) != size:
                raise ValueError("field-sampling outputs must align with point IDs")
        for value, status in zip(self.values, self.statuses, strict=True):
            if (value is None) != (status != "sampled"):
                raise ValueError("only successfully sampled points may carry numeric values")
        if (self.transform_schema_version is None) != (self.transform_basis is None):
            raise ValueError("transform version and basis must be supplied together")
        return self


def _validated_arrays(
    values: np.ndarray,
    missing_mask: np.ndarray,
    metadata: RectilinearFieldMetadata,
) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(values)
    mask = np.asarray(missing_mask)
    if array.shape != metadata.value_shape or mask.shape != metadata.value_shape:
        raise ValueError("field values and missing mask must match the reviewed metadata shape")
    if array.dtype.kind not in "biuf" or np.iscomplexobj(array) or array.dtype.hasobject:
        raise ValueError("field values must be a real numeric array")
    if mask.dtype.kind != "b":
        raise ValueError("field missing mask must have Boolean dtype")
    if numeric_array_digest(array) != metadata.array_sha256:
        raise ValueError("field array digest differs from reviewed metadata")
    if numeric_array_digest(mask) != metadata.missing_mask_sha256:
        raise ValueError("field missing-mask digest differs from reviewed metadata")
    if np.any(~np.isfinite(array[~mask])):
        raise ValueError("unmasked field values must be finite")
    return array, mask


def _map_coordinates(
    metadata: RectilinearFieldMetadata,
    request: RectilinearFieldSamplingRequest,
    transform: PlanarAffineCoordinateTransform | None,
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(request.x_coordinates_m, dtype=float)
    y = np.asarray(request.y_coordinates_m, dtype=float)
    if request.query_frame_id == metadata.coordinate_frame_id:
        if transform is not None:
            raise ValueError(
                "a coordinate transform is not accepted when query and field frames already match"
            )
        return x, y
    if transform is None:
        raise ValueError("different query and field frames require a reviewed direct coordinate transform")
    if (transform.from_frame_id, transform.to_frame_id) != (
        request.query_frame_id,
        metadata.coordinate_frame_id,
    ):
        raise ValueError("coordinate-transform frames do not map the query frame into the field frame")
    mapped_x = transform.x_from_x * x + transform.x_from_y * y + transform.x_offset_m
    mapped_y = transform.y_from_x * x + transform.y_from_y * y + transform.y_offset_m
    if np.any(~np.isfinite(mapped_x)) or np.any(~np.isfinite(mapped_y)):
        raise ValueError("mapped field coordinates exceed the finite numerical range")
    return mapped_x, mapped_y


def _bracket(axis: np.ndarray, coordinate: float) -> tuple[int, int, float]:
    if coordinate <= axis[0]:
        return 0, 0, 0.0
    if coordinate >= axis[-1]:
        last = len(axis) - 1
        return last, last, 0.0
    upper = int(np.searchsorted(axis, coordinate, side="right"))
    lower = upper - 1
    fraction = (coordinate - axis[lower]) / (axis[upper] - axis[lower])
    return lower, upper, float(fraction)


def sample_rectilinear_field(
    values: np.ndarray,
    missing_mask: np.ndarray,
    metadata: RectilinearFieldMetadata,
    request: RectilinearFieldSamplingRequest,
    *,
    transform: PlanarAffineCoordinateTransform | None = None,
) -> RectilinearFieldSamplingResult:
    """Sample a reviewed field without implicit scaling, registration, or missing-value fill."""
    array, mask = _validated_arrays(values, missing_mask, metadata)
    query_x, query_y = _map_coordinates(metadata, request, transform)
    x_axis = np.asarray(metadata.x_coordinates_m, dtype=float)
    y_axis = np.asarray(metadata.y_coordinates_m, dtype=float)
    sampled_values: list[float | None] = []
    statuses = []

    for point_id, x_value, y_value in zip(request.point_ids, query_x, query_y, strict=True):
        inside = x_axis[0] <= x_value <= x_axis[-1] and y_axis[0] <= y_value <= y_axis[-1]
        if not inside:
            if request.outside_support_policy == "reject":
                raise ValueError(f"query point {point_id!r} lies outside field support")
            sampled_values.append(None)
            statuses.append("outside_support")
            continue

        if request.interpolation == "nearest":
            column = int(np.argmin(np.abs(x_axis - x_value)))
            row = int(np.argmin(np.abs(y_axis - y_value)))
            support = ((row, column, 1.0),)
        else:
            x0, x1, fx = _bracket(x_axis, float(x_value))
            y0, y1, fy = _bracket(y_axis, float(y_value))
            weights: dict[tuple[int, int], float] = {}
            for row, wy in ((y0, 1 - fy), (y1, fy)):
                for column, wx in ((x0, 1 - fx), (x1, fx)):
                    weights[(row, column)] = weights.get((row, column), 0.0) + wx * wy
            support = tuple((row, column, weight) for (row, column), weight in weights.items() if weight)

        if any(mask[row, column] for row, column, _weight in support):
            if request.missing_support_policy == "reject":
                raise ValueError(f"query point {point_id!r} uses missing source support")
            sampled_values.append(None)
            statuses.append("missing_support")
            continue
        sampled_values.append(
            float(sum(float(array[row, column]) * weight for row, column, weight in support))
        )
        statuses.append("sampled")

    return RectilinearFieldSamplingResult(
        query_id=request.query_id,
        field_id=metadata.field_id,
        source_array_sha256=metadata.array_sha256,
        source_missing_mask_sha256=metadata.missing_mask_sha256,
        query_frame_id=request.query_frame_id,
        source_frame_id=metadata.coordinate_frame_id,
        transform_schema_version=transform.schema_version if transform else None,
        transform_basis=transform.transform_basis if transform else None,
        interpolation=request.interpolation,
        quantity_name=metadata.quantity_name,
        quantity_unit=metadata.quantity_unit,
        point_ids=request.point_ids,
        source_x_coordinates_m=tuple(float(value) for value in query_x),
        source_y_coordinates_m=tuple(float(value) for value in query_y),
        values=tuple(sampled_values),
        statuses=tuple(statuses),
    )
