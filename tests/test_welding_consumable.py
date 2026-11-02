import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.welding_consumable import (
    WeldConsumableCompatibility,
    specifications,
    weld_consumable_compatibility,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def payload(**updates):
    value = {
        "assessment_id": "consumable-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "production_records": (
            {
                "weld_id": "weld-1",
                "base_material_condition_ids": ("base-a", "base-b"),
                "consumable_lot_id": "lot-1",
                "welding_process_id": "process-1",
                "service_environment_id": "service-1",
                "minimum_service_temperature_K": 280.0,
                "maximum_service_temperature_K": 350.0,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "compatibility_declarations": (
            {
                "declaration_id": "declaration-1",
                "base_material_condition_ids": ("base-b", "base-a"),
                "consumable_lot_id": "lot-1",
                "welding_process_id": "process-1",
                "service_environment_id": "service-1",
                "minimum_supported_temperature_K": 270.0,
                "maximum_supported_temperature_K": 360.0,
                "declaration_basis": "caller-owned qualification",
                "evidence": (EVIDENCE,),
            },
        ),
        "production_identity_reviewed": True,
        "material_identity_reviewed": True,
        "consumable_traceability_reviewed": True,
        "service_conditions_reviewed": True,
        "declaration_authority_reviewed": True,
    }
    value.update(updates)
    return WeldConsumableCompatibility(**value)


def test_exact_identity_and_non_directional_material_pair_match():
    result = weld_consumable_compatibility(payload())
    assert result.status == "computed"
    assert result.values["all_records_within_declared_compatibility"] is True
    assert result.values["comparison_rows"][0]["lower_temperature_margin_K"] == 10.0


def test_unmatched_or_unreviewed_record_needs_data():
    record = payload().production_records[0].model_copy(update={"consumable_lot_id": "unknown"})
    assert weld_consumable_compatibility(payload(production_records=(record,))).status == "needs_data"
    assert weld_consumable_compatibility(payload(material_identity_reviewed=False)).status == "needs_data"


def test_outside_temperature_is_reported_without_acceptance_language():
    record = payload().production_records[0].model_copy(update={"maximum_service_temperature_K": 370.0})
    result = weld_consumable_compatibility(payload(production_records=(record,)))
    assert result.status == "computed"
    assert result.values["outside_declared_temperature_support_weld_ids"] == ["weld-1"]
    assert result.values["all_records_within_declared_compatibility"] is False


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.consumable_compatibility",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
