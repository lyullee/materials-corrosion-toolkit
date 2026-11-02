import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.pressure_test_eligibility import (
    PressureTestEligibilityAssessment,
    pressure_test_eligibility,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def requirement(requirement_id="boundary", disposition="satisfied"):
    missing = disposition == "missing"
    return {
        "requirement_id": requirement_id,
        "requirement_definition": f"authored {requirement_id} requirement",
        "disposition": disposition,
        "physical_source_group_id": f"source-{requirement_id}",
        "method_id": "review-method-1",
        "provider_id": "provider-1",
        "provider_version": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": None if missing else DIGEST_B,
        "disposition_basis": "record unavailable" if missing else "authored review",
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    value = {
        "assessment_id": "pressure-test-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "component_type_id": "vessel",
        "material_condition_id": "condition-1",
        "test_method_id": "hydro-method-1",
        "test_medium_id": "water-1",
        "pressure_basis": "gauge",
        "proposed_test_pressure_Pa": 1.5e6,
        "minimum_test_temperature_K": 290.0,
        "maximum_test_temperature_K": 300.0,
        "stored_energy_value": 12.0,
        "stored_energy_unit_token": "caller-energy-unit",
        "boundary_and_isolation_definition": "authored boundary and isolation",
        "requirement_records": (requirement("boundary"), requirement("instrumentation")),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "component_type_id": "vessel",
                "supported_material_condition_ids": ("condition-1",),
                "test_method_id": "hydro-method-1",
                "supported_test_medium_ids": ("water-1",),
                "pressure_basis": "gauge",
                "minimum_test_pressure_Pa": 1.0e6,
                "maximum_test_pressure_Pa": 2.0e6,
                "minimum_test_temperature_K": 280.0,
                "maximum_test_temperature_K": 320.0,
                "maximum_stored_energy_value": 20.0,
                "stored_energy_unit_token": "caller-energy-unit",
                "required_requirement_ids": ("boundary", "instrumentation"),
                "provider_id": "envelope-provider",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "authority_basis": "authored eligibility plan",
                "evidence": (EVIDENCE,),
            },
        ),
        "component_material_and_scope_reviewed": True,
        "test_method_medium_and_pressure_basis_reviewed": True,
        "pressure_and_temperature_plan_reviewed": True,
        "boundary_isolation_and_stored_energy_reviewed": True,
        "requirement_records_and_source_groups_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "eligibility_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return PressureTestEligibilityAssessment(**value)


def test_supported_plan_reports_caller_requirement_outcome():
    result = pressure_test_eligibility(payload())
    assert result.status == "computed"
    assert result.values["declared_eligibility_outcome"] == "requirements_satisfied"


def test_not_satisfied_is_computed_and_not_hidden_as_missing():
    result = pressure_test_eligibility(
        payload(
            requirement_records=(requirement("boundary", "not_satisfied"), requirement("instrumentation"))
        )
    )
    assert result.status == "computed"
    assert result.values["declared_eligibility_outcome"] == "requirements_not_satisfied"
    assert result.values["unsatisfied_requirement_ids"] == ["boundary"]


def test_missing_record_needs_data_and_support_is_not_extrapolated():
    assert (
        pressure_test_eligibility(
            payload(requirement_records=(requirement("boundary", "missing"), requirement("instrumentation")))
        ).status
        == "needs_data"
    )
    result = pressure_test_eligibility(payload(proposed_test_pressure_Pa=3.0e6))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_reasons"] == ["test_pressure"]


def test_exact_units_and_context_identity_are_enforced():
    assert pressure_test_eligibility(payload(stored_energy_unit_token="other-unit")).status == "needs_data"
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.pressure_test_eligibility",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
