import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.chemical_cleaning_bath_inventory import (
    ChemicalCleaningBathHistory,
    chemical_cleaning_bath_component_inventory,
)
from matintegrity.models.fabrication_surface import CoatingDamageAreaInventory, coating_damage_area_inventory
from matintegrity.registry import default_registry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored measured inventory"}


def coating(**updates):
    raw = {
        "asset_id": "asset",
        "location_id": "location",
        "coated_component_id": "component",
        "original_coated_area_m2": 10.0,
        "inspected_area_m2": 5.0,
        "patches": [
            {
                "patch_id": "wide",
                "physical_location_id": "wide-site",
                "damaged_area_m2": 0.2,
                "maximum_length_m": 0.3,
                "record_digest": "a" * 64,
                "evidence": [E],
            },
            {
                "patch_id": "long",
                "physical_location_id": "long-site",
                "damaged_area_m2": 0.1,
                "maximum_length_m": 0.5,
                "record_digest": "b" * 64,
                "evidence": [E],
            },
        ],
        "patch_identity_and_nonoverlapping_area_basis_reviewed": True,
        "inspected_and_original_area_scope_reviewed": True,
        "evidence": [E],
    } | updates
    return CoatingDamageAreaInventory.model_validate_json(json.dumps(raw))


def bath(**updates):
    raw = {
        "history_id": "bath",
        "asset_id": "asset",
        "location_id": "location",
        "clock_id": "clock",
        "initial_liquid_volume_m3": 2.0,
        "initial_components": [{"component_id": "solute", "mass_kg": 4.0}],
        "initial_evidence": [E],
        "events": [],
        "component_identity_reviewed": True,
        "event_order_and_volume_basis_reviewed": True,
        "consumption_terms_reviewed": True,
    } | updates
    return ChemicalCleaningBathHistory.model_validate_json(json.dumps(raw))


def event(**updates):
    return {
        "event_id": "event",
        "sequence_position": 1,
        "time_s": 0.0,
        "withdrawn_liquid_volume_m3": 1.0,
        "evidence": [E],
    } | updates


def test_partial_damage_extent_and_separate_patch_extrema():
    result = coating_damage_area_inventory(coating())
    assert result.status == "computed"
    assert result.values["known_damaged_area_m2"] == pytest.approx(0.3)
    assert result.values["known_damage_fraction_of_original_coated_area"] == pytest.approx(0.03)
    assert result.values["damage_fraction_of_inspected_area"] == pytest.approx(0.06)
    assert not result.values["full_declared_area_inspected"]
    assert result.values["maximum_area_patch_ids"] == ["wide"]
    assert result.values["maximum_length_patch_ids"] == ["long"]


def test_uninspected_area_is_not_zero_observed_damage_rate():
    result = coating_damage_area_inventory(coating(inspected_area_m2=0.0, patches=[]))
    assert result.values["known_damaged_area_m2"] == 0.0
    assert result.values["damage_fraction_of_inspected_area"] is None
    assert not result.values["full_declared_area_inspected"]


def test_overcoverage_and_unreviewed_overlap_are_not_accepted():
    assert coating_damage_area_inventory(coating(inspected_area_m2=0.1)).status == "out_of_scope"
    assert (
        coating_damage_area_inventory(
            coating(patch_identity_and_nonoverlapping_area_basis_reviewed=False)
        ).status
        == "needs_data"
    )
    with pytest.raises(ValueError):
        coating(inspected_area_m2=11.0)


def test_well_mixed_draw_and_complete_drain_preserve_mass_meaning():
    result = chemical_cleaning_bath_component_inventory(bath(events=[event()]))
    assert result.values["final_component_mass_kg"] == {"solute": 2.0}
    assert result.values["final_component_concentration_kg_m3"] == {"solute": 2.0}
    result = chemical_cleaning_bath_component_inventory(bath(events=[event(withdrawn_liquid_volume_m3=2.0)]))
    assert result.status == "computed"
    assert result.values["final_component_mass_kg"] == {"solute": 0.0}
    assert result.values["final_component_concentration_kg_m3"] == {"solute": None}
    assert result.values["event_history"][0]["component_concentration_kg_m3"] == {"solute": None}


def test_addition_draw_consumption_order_closes_expected_inventory():
    operation = event(
        added_liquid_volume_m3=2.0,
        added_components=[{"component_id": "solute", "mass_kg": 4.0}],
        withdrawn_liquid_volume_m3=1.0,
        caller_supplied_component_consumption=[{"component_id": "solute", "mass_kg": 1.0}],
    )
    result = chemical_cleaning_bath_component_inventory(bath(events=[operation]))
    assert result.status == "computed"
    assert result.values["final_liquid_volume_m3"] == 3.0
    assert result.values["final_component_mass_kg"] == {"solute": 5.0}
    assert result.values["final_component_concentration_kg_m3"]["solute"] == pytest.approx(5 / 3)


def test_shortfall_and_true_numeric_range_are_explicit():
    assert (
        chemical_cleaning_bath_component_inventory(
            bath(events=[event(withdrawn_liquid_volume_m3=3.0)])
        ).status
        == "needs_data"
    )
    result = chemical_cleaning_bath_component_inventory(bath(initial_liquid_volume_m3=1e-320))
    assert result.status == "out_of_scope"
    json.dumps(result.values, allow_nan=False)


@pytest.mark.parametrize(
    "model_id,factory",
    [
        ("fabrication.coating_damage_area_inventory", coating),
        ("fabrication.chemical_cleaning_bath_component_inventory", bath),
    ],
)
def test_registry_exchange_and_context(model_id, factory):
    registry = default_registry()
    value = factory()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    direct = registry.run(model_id, value, context)
    assert direct.status == "computed"
    assert direct.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
    with pytest.raises(ValueError, match="must match"):
        registry.run(model_id, value, context.model_copy(update={"location_id": "other"}))
