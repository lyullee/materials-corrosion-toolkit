import json
import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.fabrication import CoatingCoverage, coating_coverage
from matintegrity.models.fabrication_surface import SurfaceProfileRoughness, surface_profile_roughness
from matintegrity.registry import default_registry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored piecewise-linear profiles"}


def profile(positions=(0.0, 1.0, 3.0), heights=(0.0, 2e-6, 0.0), **updates):
    values = {
        "asset_id": "asset",
        "location_id": "location",
        "profile_id": "trace",
        "physical_specimen_id": "specimen",
        "coordinate_frame_id": "frame",
        "measurement_direction_id": "direction",
        "position_m": positions,
        "height_m": heights,
        "profile_digest": canonical_digest({"position_m": positions, "height_m": heights}),
        "processing_basis": "authored already-filtered trace",
        "profile_filter_form_removal_and_direction_reviewed": True,
        "piecewise_linear_interpretation_reviewed": True,
        "evidence": [E],
    } | updates
    return SurfaceProfileRoughness.model_validate_json(json.dumps(values))


def coating():
    return CoatingCoverage(
        area_m2=2.0, dry_thickness_m=1e-4, volume_solids_fraction=0.5, transfer_efficiency=0.8
    )


def test_length_weighted_mean_and_exact_triangular_integrals():
    result = surface_profile_roughness(profile())
    assert result.status == "computed"
    assert result.values["removed_length_weighted_mean_height_m"] == pytest.approx(1e-6)
    assert result.values["profile_Ra_m"] == pytest.approx(0.5e-6)
    assert result.values["profile_Rq_m"] == pytest.approx(1e-6 / math.sqrt(3))
    assert result.values["evaluation_peak_height_Rp_m"] == pytest.approx(1e-6)
    assert result.values["evaluation_valley_depth_Rv_m"] == pytest.approx(1e-6)
    assert result.values["evaluation_total_height_Rt_m"] == pytest.approx(2e-6)


def test_absolute_height_integral_resolves_zero_crossing_inside_segment():
    result = surface_profile_roughness(profile((0.0, 2.0), (-1e-6, 1e-6)))
    assert result.values["profile_Ra_m"] == pytest.approx(0.5e-6)
    assert result.values["profile_Rq_m"] == pytest.approx(1e-6 / math.sqrt(3))


def test_collinear_resampling_and_coordinate_translation_preserve_metrics():
    baseline = surface_profile_roughness(profile())
    refined = surface_profile_roughness(profile((10.0, 10.5, 11.0, 12.0, 13.0), (0.0, 1e-6, 2e-6, 1e-6, 0.0)))
    for name in (
        "profile_Ra_m",
        "profile_Rq_m",
        "evaluation_peak_height_Rp_m",
        "evaluation_valley_depth_Rv_m",
        "evaluation_total_height_Rt_m",
    ):
        assert refined.values[name] == pytest.approx(baseline.values[name], rel=1e-12, abs=1e-20)


@pytest.mark.parametrize("height", [0.0, 1e100])
def test_constant_profile_has_zero_centered_roughness(height):
    result = surface_profile_roughness(profile(heights=(height, height, height)))
    assert result.status == "computed"
    assert result.values["profile_Ra_m"] == result.values["profile_Rq_m"] == 0.0


def test_missing_preprocessing_review_withholds_roughness():
    assert (
        surface_profile_roughness(profile(profile_filter_form_removal_and_direction_reviewed=False)).status
        == "needs_data"
    )


@pytest.mark.parametrize("case", ["digest", "order"])
def test_profile_identity_and_coordinate_order_are_strict(case):
    with pytest.raises(ValueError):
        profile(profile_digest="a" * 64) if case == "digest" else profile((0.0, 3.0, 1.0))


def test_unrepresentable_extent_is_out_of_scope():
    result = surface_profile_roughness(profile((-1e308, 0.0, 1e308)))
    assert result.status == "out_of_scope"
    json.dumps(result.values, allow_nan=False)


def test_coating_solid_volume_and_declared_transfer_loss():
    result = coating_coverage(coating())
    assert result.values["dry_volume_m3"] == pytest.approx(2e-4)
    assert result.values["wet_thickness_m"] == pytest.approx(2e-4)
    assert result.values["required_wet_volume_m3"] == pytest.approx(5e-4)
    assert coating_coverage(coating().model_copy(update={"area_m2": 1e308})).status == "computed"
    assert (
        coating_coverage(coating().model_copy(update={"area_m2": 1e308, "dry_thickness_m": 1e308})).status
        == "out_of_scope"
    )


@pytest.mark.parametrize(
    "model_id,factory",
    [("inspection.surface_profile_roughness", profile), ("protection.coating_coverage", coating)],
)
def test_default_registry_python_json(model_id, factory):
    registry = default_registry()
    value = factory()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    result = registry.run(model_id, value, context)
    assert result.status == "computed"
    assert result.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
