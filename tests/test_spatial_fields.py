from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.spatial_fields import (
    PlanarAffineCoordinateTransform,
    RectilinearFieldMetadata,
    RectilinearFieldSamplingRequest,
    numeric_array_digest,
    sample_rectilinear_field,
)

SOURCE_SHA256 = "a" * 64


def _field():
    x = (0.0, 1.0, 3.0)
    y = (0.0, 2.0, 5.0)
    values = np.asarray([[1.0 + 2.0 * xv + 3.0 * yv for xv in x] for yv in y])
    mask = np.zeros(values.shape, dtype=bool)
    metadata = RectilinearFieldMetadata(
        field_id="field-1",
        physical_specimen_id="specimen-1",
        source_group_id="source-group-1",
        source_sha256=SOURCE_SHA256,
        array_sha256=numeric_array_digest(values),
        missing_mask_sha256=numeric_array_digest(mask),
        quantity_name="surface_height",
        quantity_unit="m",
        quantity_basis="reviewed laboratory export",
        coordinate_frame_id="source-frame",
        coordinate_basis="reviewed rectilinear stage coordinates",
        observation_clock="exposure day 2",
        x_coordinates_m=x,
        y_coordinates_m=y,
        value_shape=values.shape,
        missing_value_meaning="True marks unavailable source support",
    )
    return values, mask, metadata


def _request(**updates):
    values = dict(
        query_id="query-1",
        query_frame_id="source-frame",
        point_ids=("p1",),
        x_coordinates_m=(0.5,),
        y_coordinates_m=(1.0,),
        interpolation="bilinear",
        outside_support_policy="reject",
        missing_support_policy="reject",
        interpolation_review_basis="bilinear interpolation accepted for this quantity",
    )
    values.update(updates)
    return RectilinearFieldSamplingRequest(**values)


def test_numeric_array_digest_binds_dtype_shape_and_content():
    base = np.asarray([[1, 2]], dtype=np.int32)
    assert numeric_array_digest(base) == numeric_array_digest(base.copy())
    assert numeric_array_digest(base) != numeric_array_digest(base.astype(np.int64))
    assert numeric_array_digest(base) != numeric_array_digest(base.reshape(2, 1))
    changed = base.copy()
    changed[0, 0] = 3
    assert numeric_array_digest(base) != numeric_array_digest(changed)
    with pytest.raises(ValueError, match="object arrays"):
        numeric_array_digest(np.asarray([object()], dtype=object))


def test_bilinear_sampling_recovers_linear_plane_on_irregular_axes():
    values, mask, metadata = _field()
    result = sample_rectilinear_field(values, mask, metadata, _request())
    assert result.values == pytest.approx((5.0,))
    assert result.statuses == ("sampled",)
    assert result.transform_schema_version is None


def test_nearest_sampling_is_deterministic():
    values, mask, metadata = _field()
    request = _request(
        x_coordinates_m=(2.6,),
        y_coordinates_m=(1.6,),
        interpolation="nearest",
    )
    result = sample_rectilinear_field(values, mask, metadata, request)
    assert result.values == pytest.approx((13.0,))


def test_reviewed_affine_transform_maps_query_into_source_frame():
    values, mask, metadata = _field()
    request = _request(
        query_frame_id="query-frame",
        x_coordinates_m=(0.25,),
        y_coordinates_m=(0.5,),
    )
    transform = PlanarAffineCoordinateTransform(
        from_frame_id="query-frame",
        to_frame_id="source-frame",
        x_from_x=2.0,
        x_from_y=0.0,
        x_offset_m=0.0,
        y_from_x=0.0,
        y_from_y=2.0,
        y_offset_m=0.0,
        transform_basis="reviewed fiducial registration",
        registration_reviewed=True,
    )
    result = sample_rectilinear_field(values, mask, metadata, request, transform=transform)
    assert result.source_x_coordinates_m == pytest.approx((0.5,))
    assert result.source_y_coordinates_m == pytest.approx((1.0,))
    assert result.values == pytest.approx((5.0,))
    assert result.transform_basis == transform.transform_basis


def test_frame_mismatch_requires_exact_reviewed_transform():
    values, mask, metadata = _field()
    request = _request(query_frame_id="query-frame")
    with pytest.raises(ValueError, match="require a reviewed direct"):
        sample_rectilinear_field(values, mask, metadata, request)

    wrong = PlanarAffineCoordinateTransform(
        from_frame_id="somewhere-else",
        to_frame_id="source-frame",
        x_from_x=1.0,
        x_from_y=0.0,
        x_offset_m=0.0,
        y_from_x=0.0,
        y_from_y=1.0,
        y_offset_m=0.0,
        transform_basis="reviewed but for another frame",
        registration_reviewed=True,
    )
    with pytest.raises(ValueError, match="do not map"):
        sample_rectilinear_field(values, mask, metadata, request, transform=wrong)
    with pytest.raises(ValueError, match="not accepted"):
        sample_rectilinear_field(values, mask, metadata, _request(), transform=wrong)


def test_outside_and_missing_support_policies_are_explicit():
    values, mask, metadata = _field()
    outside = _request(x_coordinates_m=(4.0,), outside_support_policy="return_missing")
    result = sample_rectilinear_field(values, mask, metadata, outside)
    assert result.values == (None,)
    assert result.statuses == ("outside_support",)
    with pytest.raises(ValueError, match="outside field support"):
        sample_rectilinear_field(
            values,
            mask,
            metadata,
            _request(x_coordinates_m=(4.0,)),
        )

    missing_mask = mask.copy()
    missing_mask[0, 0] = True
    missing_metadata = metadata.model_copy(update={"missing_mask_sha256": numeric_array_digest(missing_mask)})
    request = _request(missing_support_policy="return_missing")
    result = sample_rectilinear_field(values, missing_mask, missing_metadata, request)
    assert result.values == (None,)
    assert result.statuses == ("missing_support",)
    with pytest.raises(ValueError, match="missing source support"):
        sample_rectilinear_field(values, missing_mask, missing_metadata, _request())


def test_arrays_must_match_reviewed_shape_type_digest_and_finite_support():
    values, mask, metadata = _field()
    with pytest.raises(ValueError, match="metadata shape"):
        sample_rectilinear_field(values[:, :2], mask[:, :2], metadata, _request())
    with pytest.raises(ValueError, match="Boolean dtype"):
        sample_rectilinear_field(values, mask.astype(np.uint8), metadata, _request())
    changed = values.copy()
    changed[0, 0] += 1.0
    with pytest.raises(ValueError, match="array digest"):
        sample_rectilinear_field(changed, mask, metadata, _request())

    nonfinite = values.copy()
    nonfinite[0, 0] = np.nan
    nonfinite_metadata = metadata.model_copy(update={"array_sha256": numeric_array_digest(nonfinite)})
    with pytest.raises(ValueError, match="must be finite"):
        sample_rectilinear_field(nonfinite, mask, nonfinite_metadata, _request())


def test_contracts_reject_invalid_axes_points_and_transform():
    _values, _mask, metadata = _field()
    with pytest.raises(ValidationError, match="strictly increasing"):
        RectilinearFieldMetadata(**(metadata.model_dump() | {"x_coordinates_m": (0.0, 0.0, 3.0)}))
    with pytest.raises(ValidationError, match="must align"):
        _request(y_coordinates_m=(1.0, 2.0))
    with pytest.raises(ValidationError, match="nonsingular"):
        PlanarAffineCoordinateTransform(
            from_frame_id="a",
            to_frame_id="b",
            x_from_x=1.0,
            x_from_y=2.0,
            x_offset_m=0.0,
            y_from_x=2.0,
            y_from_y=4.0,
            y_offset_m=0.0,
            transform_basis="degenerate test",
            registration_reviewed=True,
        )
