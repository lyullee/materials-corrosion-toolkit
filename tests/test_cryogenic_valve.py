import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.cryogenic_valve import (
    CryogenicValveEvidenceAssessment,
    cryogenic_valve_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def cycle(identifier="cycle-1", **updates):
    value = {
        "cycle_id": identifier,
        "start_time_s": 0.0,
        "end_time_s": 100.0,
        "minimum_temperature_K": 80.0,
        "maximum_temperature_K": 300.0,
        "minimum_pressure_value": 1.0,
        "maximum_pressure_value": 2.0,
        "pressure_unit_token": "custom-pressure",
        "actuation_count": 5,
        "actuation_mode_descriptor": "full-open-close",
        "thermal_stabilization_basis": "authored plateau",
        "acquisition_state_digest": "a" * 64,
        "data_digest": "b" * 64,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def observation(identifier="leak-1", **updates):
    value = {
        "observation_id": identifier,
        "cycle_id": "cycle-1",
        "physical_component_id": "seat-1",
        "source_group_id": "run-1",
        "observation_role": "test",
        "observation_kind": "leakage",
        "method_id": "method-1",
        "metric_id": "leak-rate",
        "metric_definition": "authored leak signal",
        "unit_token": "custom-leak-unit",
        "reporting_status": "below_detection",
        "detection_limit": 0.01,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": "c" * 64,
        "result_digest": "d" * 64,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "valve_type_id": "valve-type-1",
        "body_material_id": "body-material-1",
        "seat_component_id": "seat-1",
        "seat_material_id": "seat-material-1",
        "stem_component_id": "stem-1",
        "stem_material_id": "stem-material-1",
        "seal_system_id": "seal-1",
        "test_medium_id": "medium-1",
        "pressure_basis": "absolute",
        "minimum_temperature_K": 70.0,
        "maximum_temperature_K": 310.0,
        "minimum_pressure_value": 0.5,
        "maximum_pressure_value": 2.5,
        "pressure_unit_token": "custom-pressure",
        "supported_actuation_mode_descriptors": ("full-open-close",),
        "maximum_single_cycle_duration_s": 200.0,
        "maximum_cumulative_actuation_count": 10,
        "observation_requirements": (
            {
                "requirement_id": "leak-test",
                "observation_kind": "leakage",
                "observation_role": "test",
                "method_id": "method-1",
                "metric_id": "leak-rate",
                "metric_definition": "authored leak signal",
                "unit_token": "custom-leak-unit",
                "minimum_record_count": 1,
                "requirement_basis": "caller evidence plan",
            },
        ),
        "physical_specimen_ids": ("specimen-1",),
        "source_group_ids": ("source-1",),
        "provider_id": "qualification-provider",
        "provider_revision": "1",
        "provider_state_digest": "e" * 64,
        "qualification_result_digest": "f" * 64,
        "qualification_basis": "caller qualification programme",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "valve-assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        "valve_id": "valve-1",
        "valve_type_id": "valve-type-1",
        "body_material_id": "body-material-1",
        "seat_component_id": "seat-1",
        "seat_material_id": "seat-material-1",
        "stem_component_id": "stem-1",
        "stem_material_id": "stem-material-1",
        "seal_system_id": "seal-1",
        "test_medium_id": "medium-1",
        "pressure_basis": "absolute",
        "cycles": (cycle(),),
        "observations": (observation(),),
        "qualification_envelope": envelope(),
        "valve_component_material_and_seal_identity_reviewed": True,
        "medium_and_pressure_basis_reviewed": True,
        "clock_cycle_and_actuation_alignment_reviewed": True,
        "thermal_stabilization_reviewed": True,
        "observation_roles_metrics_and_units_reviewed": True,
        "uncertainty_detection_limits_and_missingness_reviewed": True,
        "physical_specimen_and_source_group_partitions_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CryogenicValveEvidenceAssessment(**value)


def test_supported_cycle_preserves_below_detection_without_service_claim():
    result = cryogenic_valve_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_evidence_outcome"] == "within_support"
    assert result.values["observation_summaries"][0]["reported_or_conservative_value"] == 0.01


def test_reviewed_temperature_or_actuation_outside_support_is_out_of_scope():
    result = cryogenic_valve_evidence(
        payload(cycles=(cycle(minimum_temperature_K=60.0, actuation_count=12),))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_cycle_ids"] == ["cycle-1"]
    assert result.values["cumulative_actuation_within_support"] is False


def test_missing_review_observation_or_unit_needs_data():
    assert cryogenic_valve_evidence(payload(medium_and_pressure_basis_reviewed=False)).status == "needs_data"
    missing = observation(
        reporting_status="missing",
        detection_limit=None,
        result_digest=None,
        missing_basis="result unavailable",
    )
    assert cryogenic_valve_evidence(payload(observations=(missing,))).status == "needs_data"
    assert (
        cryogenic_valve_evidence(payload(cycles=(cycle(pressure_unit_token="other"),))).status == "needs_data"
    )


def test_cycle_linkage_order_and_context_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(
            cycles=(
                cycle("cycle-1", start_time_s=0.0, end_time_s=20.0),
                cycle("cycle-2", start_time_s=10.0, end_time_s=30.0),
            )
        )
    with pytest.raises(ValueError, match="declared cycle"):
        payload(observations=(observation(cycle_id="other"),))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.cryogenic_valve_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
