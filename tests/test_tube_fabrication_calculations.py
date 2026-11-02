import json

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    TubeBendPreformThickness,
    TubeExpansionWallReduction,
    tube_bend_preform_thickness,
    tube_expansion_wall_reduction,
)
from matintegrity.registry import default_registry


def bind(contract, values):
    normalized = contract.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(normalized)
    basis = {
        "source_id": "authored",
        "revision": "1",
        "license_id": "authored-test",
        "record_sha256": digest,
        "applicability_and_units_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [
            {
                "source_id": "authored",
                "origin": "synthetic",
                "citation": "authored geometry",
                "license_id": "authored-test",
                "sha256": digest,
            }
        ],
    }
    return contract.model_validate_json(json.dumps(values | {"basis": basis}))


def expansion(**updates):
    return bind(
        TubeExpansionWallReduction,
        {
            "tube_id": "tube",
            "tubesheet_hole_id": "hole",
            "initial_outer_diameter_m": 0.02,
            "initial_inner_diameter_m": 0.016,
            "hole_diameter_m": 0.0204,
            "expanded_inner_diameter_m": 0.0168,
            "final_outer_surface_contact_with_hole_reviewed": True,
        }
        | updates,
    )


def bend(**updates):
    return bind(
        TubeBendPreformThickness,
        {
            "tube_id": "tube",
            "minimum_straight_wall_m": 0.002,
            "tube_outer_diameter_m": 0.02,
            "mean_bend_radius_m": 0.05,
            "curvature_allowance_coefficient": 0.3,
        }
        | updates,
    )


def test_expansion_clearance_take_up_is_not_wall_reduction():
    result = tube_expansion_wall_reduction(expansion(expanded_inner_diameter_m=0.0164))
    assert result.status == "computed"
    assert result.values["wall_reduction_fraction"] == pytest.approx(0.0, abs=2e-15)
    result = tube_expansion_wall_reduction(expansion())
    assert result.values["original_wall_thickness_m"] == pytest.approx(0.002)
    assert result.values["expanded_wall_thickness_m"] == pytest.approx(0.0018)
    assert result.values["wall_reduction_percent"] == pytest.approx(10.0)


def test_expansion_contact_review_and_negative_reduction():
    assert (
        tube_expansion_wall_reduction(expansion(final_outer_surface_contact_with_hole_reviewed=False)).status
        == "needs_data"
    )
    assert (
        tube_expansion_wall_reduction(expansion(expanded_inner_diameter_m=0.016)).values[
            "wall_reduction_fraction"
        ]
        < 0
    )


@pytest.mark.parametrize(
    "updates",
    [{"initial_inner_diameter_m": 0.02}, {"hole_diameter_m": 0.019}, {"expanded_inner_diameter_m": 0.021}],
)
def test_impossible_expansion_geometry_is_rejected(updates):
    with pytest.raises(ValueError):
        expansion(**updates)


@pytest.mark.parametrize("scale", [1e-100, 1.0, 1e100])
def test_preform_curvature_allowance_is_scale_consistent(scale):
    result = tube_bend_preform_thickness(
        bend(
            minimum_straight_wall_m=0.002 * scale,
            tube_outer_diameter_m=0.02 * scale,
            mean_bend_radius_m=0.05 * scale,
        )
    )
    assert result.status == "computed"
    assert result.values["curvature_allowance_multiplier"] == pytest.approx(1.12)
    assert result.values["preform_wall_thickness_m"] / scale == pytest.approx(0.00224)


def test_preform_zero_coefficient_and_impossible_required_bore():
    assert (
        tube_bend_preform_thickness(bend(curvature_allowance_coefficient=0.0)).values[
            "preform_wall_thickness_m"
        ]
        == 0.002
    )
    assert tube_bend_preform_thickness(bend(curvature_allowance_coefficient=100.0)).status == "out_of_scope"
    with pytest.raises(ValueError, match="mean bend radius"):
        bend(mean_bend_radius_m=0.01)


@pytest.mark.parametrize(
    "model_id,factory",
    [
        ("fabrication.tube_expansion_wall_reduction", expansion),
        ("fabrication.tube_bend_preform_thickness", bend),
    ],
)
def test_default_registry_python_json_exchange(model_id, factory):
    registry = default_registry()
    value = factory()
    context = RunContext(asset_id="asset", location_id="bundle", time_basis="synthetic")
    direct = registry.run(model_id, value, context)
    assert direct.status == "computed"
    assert direct.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
