import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fabrication_surface import SurfaceProfileDeviation, surface_profile_deviation
from matintegrity.registry import default_registry


def payload(displacement=0.002, uncertainty=0.0):
    evidence = {"source_id": "authored", "origin": "synthetic", "citation": "synthetic coordinate geometry"}
    return {
        "asset_id": "asset",
        "location_id": "location",
        "coordinate_frame_id": "frame",
        "reference_geometry_id": "shape",
        "measurement_digest": "a" * 64,
        "reference_geometry_digest": "b" * 64,
        "reference_length_m": 2.0,
        "points": [
            {
                "point_id": "point",
                "reference_position_m": [0.0, 0.0, 0.0],
                "measured_position_m": [0.0, 0.0, displacement],
                "outward_unit_normal": [0.0, 0.0, 1.0],
                "normal_deviation_expanded_uncertainty_m": uncertainty,
                "evidence": [evidence],
            }
        ],
        "caller_minimum_signed_deviation_m": -0.003,
        "caller_maximum_signed_deviation_m": 0.004,
        "point_correspondence_coordinate_frame_and_normals_reviewed": True,
        "measurement_uncertainty_and_limit_authority_reviewed": True,
        "limit_basis": "authored toy limits",
        "evidence": [evidence],
    }


def calculate(raw):
    return surface_profile_deviation(SurfaceProfileDeviation.model_validate_json(json.dumps(raw)))


@pytest.mark.parametrize(
    "deviation,uncertainty,outcome",
    [
        (0.002, 0.001, "within_bounds"),
        (-0.005, 0.001, "outside_bounds"),
        (0.004, 0.001, "overlaps_boundary"),
        (-0.003, 0.0, "within_bounds"),
    ],
)
def test_signed_projection_and_interval_boundaries(deviation, uncertainty, outcome):
    result = calculate(payload(deviation, uncertainty))
    assert result.status == "computed"
    row = result.values["point_results"][0]
    assert row["signed_normal_deviation_m"] == deviation
    assert row["normalized_signed_deviation"] == deviation / 2
    assert row["declared_interval_outcome"] == outcome


def test_oblique_projection_and_normal_sign():
    raw = payload()
    raw["points"][0]["outward_unit_normal"] = [0.6, 0.8, 0.0]
    raw["points"][0]["measured_position_m"] = [0.003, 0.004, 100.0]
    assert calculate(raw).values["point_results"][0]["signed_normal_deviation_m"] == pytest.approx(0.005)


@pytest.mark.parametrize("change", ["normal", "duplicate", "bounds"])
def test_invalid_geometry_contracts_are_rejected(change):
    raw = payload()
    if change == "normal":
        raw["points"][0]["outward_unit_normal"] = [0.0, 0.0, 2.0]
    elif change == "duplicate":
        raw["points"].append(raw["points"][0].copy())
    else:
        raw["caller_minimum_signed_deviation_m"] = 1.0
    with pytest.raises(ValueError):
        calculate(raw)


def test_review_and_unrepresentable_coordinate_difference():
    raw = payload()
    raw["point_correspondence_coordinate_frame_and_normals_reviewed"] = False
    assert calculate(raw).status == "needs_data"
    raw = payload()
    raw["points"][0]["reference_position_m"][2] = -1e308
    raw["points"][0]["measured_position_m"][2] = 1e308
    assert calculate(raw).status == "out_of_scope"


def test_rigid_rotation_preserves_projection():
    raw = payload()
    angle = 0.7
    raw["points"][0]["measured_position_m"] = [0.002 * math.sin(angle), 0.0, 0.002 * math.cos(angle)]
    raw["points"][0]["outward_unit_normal"] = [math.sin(angle), 0.0, math.cos(angle)]
    assert calculate(raw).values["point_results"][0]["signed_normal_deviation_m"] == pytest.approx(0.002)


def test_default_registry_exchange_and_context():
    registry = default_registry()
    request = SurfaceProfileDeviation.model_validate_json(json.dumps(payload()))
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    result = registry.run("fabrication.surface_profile_deviation", request, context)
    assert (
        result.model_dump()
        == registry.run_json(
            "fabrication.surface_profile_deviation", request.model_dump_json(), context
        ).model_dump()
    )
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.surface_profile_deviation", request, context.model_copy(update={"asset_id": "other"})
        )
