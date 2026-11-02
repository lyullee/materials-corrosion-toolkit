import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.casting_forging_quality import (
    CastingForgingQualityRecord,
    casting_forging_quality_record,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-quality-record",
    "origin": "synthetic",
    "citation": "authored casting and forging quality test record",
}


def inputs(**updates):
    payload = {
        "record_id": "quality-001",
        "asset_id": "component-asset-001",
        "location_id": "forged-nozzle-body",
        "component_id": "nozzle-forging-001",
        "heat_id": "heat-001",
        "manufacturing_route_id": "route-001",
        "manufacturing_route_description": "caller-recorded forging and machining route",
        "material_condition_id": "caller-condition-001",
        "heat_treatments": [
            {
                "treatment_id": "ht-1",
                "treatment_type": "caller-recorded treatment",
                "start_time_s": 0.0,
                "end_time_s": 7200.0,
                "minimum_recorded_temperature_K": 850.0,
                "maximum_recorded_temperature_K": 900.0,
                "record_valid": True,
                "evidence": [EVIDENCE],
            }
        ],
        "inspection_regions": [
            {
                "region_id": "region-a",
                "physical_location_id": "body-volume-a",
                "examination_method_id": "caller-ut-procedure",
                "target_extent": 1.0,
                "examined_extent": 0.8,
                "extent_unit": "m^3",
                "record_valid": True,
                "unexamined_basis": "caller-recorded inaccessible geometry",
                "evidence": [EVIDENCE],
            }
        ],
        "observations": [
            {
                "observation_id": "ind-1",
                "region_id": "region-a",
                "reported_indication_type": "caller-reported volumetric indication",
                "measurement_definition": "caller-defined equivalent dimension",
                "measured_value": 0.009,
                "expanded_uncertainty": 0.002,
                "unit": "m",
                "caller_limit_id": "dimension-screen",
                "caller_reported_disposition_id": "engineering-review-open",
                "record_valid": True,
                "evidence": [EVIDENCE],
            },
            {
                "observation_id": "surface-note",
                "region_id": "region-a",
                "reported_indication_type": "caller qualitative surface note",
                "caller_reported_disposition_id": "document-only",
                "record_valid": True,
                "evidence": [EVIDENCE],
            },
        ],
        "caller_limits": [
            {
                "limit_id": "dimension-screen",
                "metric_definition": "caller-defined equivalent dimension",
                "unit": "m",
                "maximum_value": 0.01,
                "limit_basis": "caller engineering screen",
                "caller_disposition_id_if_outside": "engineering-review-required",
            }
        ],
        "component_heat_and_route_reviewed": True,
        "heat_treatment_history_reviewed": True,
        "inspection_region_mapping_reviewed": True,
        "examination_coverage_reviewed": True,
        "indication_classification_reviewed": True,
        "measurement_units_and_uncertainty_reviewed": True,
        "caller_limit_mapping_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_complete_record_preserves_coverage_and_uncertainty_overlap_without_acceptance():
    result = casting_forging_quality_record(CastingForgingQualityRecord.model_validate(inputs()))
    assert result.status == "computed"
    coverage = result.values["coverage_by_extent_unit"][0]
    assert coverage["coverage_fraction"] == pytest.approx(0.8)
    assert result.values["incomplete_coverage_region_ids"] == ["region-a"]
    comparison = result.values["caller_limit_comparisons"][0]
    assert comparison["nominal_above_declared_maximum"] is False
    assert comparison["uncertainty_interval_extends_above_declared_maximum"] is True
    assert comparison["caller_disposition_id_if_outside"] == "engineering-review-required"


def test_invalid_records_and_unmapped_numeric_measurement_remain_needs_data():
    invalid_treatment = {
        "treatment_id": "ht-missing",
        "treatment_type": "record unavailable",
        "record_valid": False,
        "invalid_basis": "furnace file unavailable",
        "evidence": [EVIDENCE],
    }
    observations = list(inputs()["observations"])
    observations[0] = {**observations[0], "caller_limit_id": None}
    result = casting_forging_quality_record(
        CastingForgingQualityRecord.model_validate(
            inputs(heat_treatments=[invalid_treatment], observations=observations)
        )
    )
    assert result.status == "needs_data"
    assert result.values["invalid_heat_treatment_ids"] == ["ht-missing"]
    assert result.values["missing_limit_mapping_observation_ids"] == ["ind-1"]


def test_definition_and_unit_mismatch_are_not_silently_compared():
    observations = list(inputs()["observations"])
    observations[0] = {**observations[0], "measurement_definition": "different dimension"}
    definition = casting_forging_quality_record(
        CastingForgingQualityRecord.model_validate(inputs(observations=observations))
    )
    assert definition.status == "needs_data"
    assert definition.values["limit_definition_mismatch_observation_ids"] == ["ind-1"]

    observations[0] = {**inputs()["observations"][0], "unit": "mm"}
    unit = casting_forging_quality_record(
        CastingForgingQualityRecord.model_validate(inputs(observations=observations))
    )
    assert unit.status == "needs_data"
    assert unit.values["limit_unit_mismatch_observation_ids"] == ["ind-1"]


def test_contract_rejects_orphan_observation_and_incoherent_measurement():
    observations = list(inputs()["observations"])
    observations[0] = {**observations[0], "region_id": "not-declared"}
    with pytest.raises(ValueError, match="declared inspection region"):
        CastingForgingQualityRecord.model_validate(inputs(observations=observations))

    observations[0] = {
        **inputs()["observations"][0],
        "expanded_uncertainty": None,
    }
    with pytest.raises(ValueError, match="requires definition"):
        CastingForgingQualityRecord.model_validate(inputs(observations=observations))


def test_model_spec_enforces_context_identity():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    request = CastingForgingQualityRecord.model_validate(inputs())
    result = registry.run(
        "materials.casting_forging_quality_record",
        request,
        RunContext(
            asset_id="component-asset-001",
            location_id="forged-nozzle-body",
            time_basis="manufacturing record clock",
        ),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.casting_forging_quality_record",
            request,
            RunContext(asset_id="other", location_id="forged-nozzle-body", time_basis="clock"),
        )
