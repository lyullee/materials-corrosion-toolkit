import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.transport_erection import (
    EquipmentMassProperties,
    EquipmentTwoSupportLift,
    equipment_mass_properties,
    equipment_two_support_lift,
)
from matintegrity.registry import default_registry

E = {"source_id": "authored", "origin": "synthetic", "citation": "synthetic rigid-body inventory"}


def inventory():
    return {
        "asset_id": "asset",
        "location_id": "location",
        "assembly_id": "assembly",
        "coordinate_frame_id": "body",
        "components": [
            {
                "component_id": "first",
                "mass_kg": 25.0,
                "center_of_mass_position_m": [0.0, 1.0, 0.0],
                "record_digest": "a" * 64,
                "evidence": [E],
            },
            {
                "component_id": "second",
                "mass_kg": 75.0,
                "center_of_mass_position_m": [4.0, 1.0, 0.0],
                "record_digest": "b" * 64,
                "evidence": [E],
            },
        ],
        "complete_installed_inventory_and_common_frame_reviewed": True,
        "evidence": [E],
    }


def lift(**changes):
    raw = {
        "inventory": inventory(),
        "first_support_id": "support-a",
        "second_support_id": "support-b",
        "first_support_position_xy_m": [0.0, 0.0],
        "second_support_position_xy_m": [4.0, 0.0],
        "body_to_world_rotation_rad": 0.0,
        "gravity_m_s2": 10.0,
        "caller_load_multiplier": 1.0,
        "minimum_supported_horizontal_span_m": 1e-6,
        "planar_xy_projection_parallel_vertical_reactions_and_rigid_body_reviewed": True,
        "load_multiplier_and_orientation_applicability_reviewed": True,
        "evidence": [E],
    } | changes
    return EquipmentTwoSupportLift.model_validate_json(json.dumps(raw))


def test_mass_and_centroid_preserve_installed_component_inventory():
    value = EquipmentMassProperties.model_validate_json(json.dumps(inventory()))
    result = equipment_mass_properties(value)
    assert result.status == "computed"
    assert result.values["total_mass_kg"] == 100.0
    assert result.values["center_of_mass_position_m"] == [3.0, 1.0, 0.0]
    assert result.values["component_ids"] == ["first", "second"]


def test_missing_inventory_review_and_duplicate_components():
    raw = inventory()
    raw["complete_installed_inventory_and_common_frame_reviewed"] = False
    assert (
        equipment_mass_properties(EquipmentMassProperties.model_validate_json(json.dumps(raw))).status
        == "needs_data"
    )
    raw = inventory()
    raw["components"][1]["component_id"] = "first"
    with pytest.raises(ValueError, match="unique"):
        EquipmentMassProperties.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize(
    "angle,first,second", [(0.0, 250.0, 750.0), (math.pi / 4, 500.0, 500.0), (math.pi, 250.0, 750.0)]
)
def test_rotation_specific_force_and_moment_balance(angle, first, second):
    result = equipment_two_support_lift(lift(body_to_world_rotation_rad=angle))
    assert result.status == "computed"
    values = result.values
    assert values["first_vertical_reaction_N"] == pytest.approx(first)
    assert values["second_vertical_reaction_N"] == pytest.approx(second)
    assert first + second == pytest.approx(values["factored_vertical_load_N"])
    assert values["second_vertical_reaction_N"] * values["signed_horizontal_support_span_m"] == pytest.approx(
        values["factored_vertical_load_N"] * values["center_of_mass_horizontal_lever_m"]
    )


def test_uplift_and_near_singular_projection_are_out_of_scope():
    result = equipment_two_support_lift(lift(second_support_position_xy_m=[2.0, 0.0]))
    assert result.status == "out_of_scope" and result.values["uplift_required"]
    assert result.values["first_vertical_reaction_N"] < 0
    assert equipment_two_support_lift(lift(body_to_world_rotation_rad=math.pi / 2)).status == "out_of_scope"


def test_translation_and_support_order_preserve_reactions():
    value = lift()
    raw = value.model_dump(mode="json")
    for row in raw["inventory"]["components"]:
        row["center_of_mass_position_m"][0] += 100.0
    for key in ("first_support_position_xy_m", "second_support_position_xy_m"):
        raw[key][0] += 100.0
    translated = equipment_two_support_lift(EquipmentTwoSupportLift.model_validate_json(json.dumps(raw)))
    assert translated.values["first_vertical_reaction_N"] == 250.0
    reverse = equipment_two_support_lift(
        lift(first_support_position_xy_m=[4.0, 0.0], second_support_position_xy_m=[0.0, 0.0])
    )
    assert reverse.values["first_vertical_reaction_N"] == 750.0


def test_load_multiplier_and_missing_review():
    assert (
        equipment_two_support_lift(lift(caller_load_multiplier=2.0)).values["first_vertical_reaction_N"]
        == 500.0
    )
    assert (
        equipment_two_support_lift(lift(load_multiplier_and_orientation_applicability_reviewed=False)).status
        == "needs_data"
    )


def test_numeric_mass_and_load_range_are_explicit():
    raw = inventory()
    for row in raw["components"]:
        row["mass_kg"] = 1e308
    assert (
        equipment_mass_properties(EquipmentMassProperties.model_validate_json(json.dumps(raw))).status
        == "out_of_scope"
    )
    assert equipment_two_support_lift(lift(caller_load_multiplier=1e308)).status == "out_of_scope"


@pytest.mark.parametrize(
    "model_id", ["fabrication.equipment_mass_properties", "fabrication.equipment_two_support_lift"]
)
def test_registry_python_json_exchange_and_context(model_id):
    registry = default_registry()
    value = lift() if model_id.endswith("lift") else lift().inventory
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    direct = registry.run(model_id, value, context)
    assert direct.status == "computed"
    assert direct.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
    with pytest.raises(ValueError, match="must match"):
        registry.run(model_id, value, context.model_copy(update={"asset_id": "other"}))
