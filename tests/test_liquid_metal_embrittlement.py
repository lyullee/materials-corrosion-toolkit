import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.liquid_metal_embrittlement import (
    LiquidMetalEmbrittlementApplicability,
    liquid_metal_embrittlement_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
IDENTITY = {
    "structural_material_id": "material-1",
    "material_condition_id": "condition-1",
}
LIQUID = {
    "liquid_metal_species_id": "liquid-metal-1",
    "liquid_metal_composition_id": "composition-1",
    "impurity_profile_id": "impurity-profile-1",
}


def qualification_test_evidence(**updates):
    value = {
        "evidence_record_id": "evidence-1",
        "test_id": "test-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-group-1",
        **IDENTITY,
        **LIQUID,
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "observations": (
            {
                "observation_id": "observation-1",
                "observation_kind": "caller-defined examination",
                "method_id": "method-1",
                "physical_region_id": "region-1",
                "reported_endpoint": "caller-reported test endpoint",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        **IDENTITY,
        **LIQUID,
        "supported_contact_state_descriptors": ("continuous-contact",),
        "supported_wetting_descriptors": ("caller-wetting-state",),
        "minimum_temperature_K": 300.0,
        "maximum_temperature_K": 500.0,
        "minimum_stress_value": 0.0,
        "maximum_stress_value": 200.0,
        "stress_unit_token": "custom-stress-unit",
        "minimum_strain_rate_value": 0.0,
        "maximum_strain_rate_value": 0.1,
        "strain_rate_unit_token": "custom-rate-unit",
        "maximum_single_exposure_s": 1000.0,
        "maximum_cumulative_exposure_s": 2000.0,
        "test_evidence": (qualification_test_evidence(),),
        "qualification_basis": "caller-owned qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def exposure(identifier="interval-1", **updates):
    value = {
        "interval_id": identifier,
        "start_time_s": 0.0,
        "end_time_s": 500.0,
        **LIQUID,
        "contact_state_descriptor": "continuous-contact",
        "wetting_descriptor": "caller-wetting-state",
        "minimum_temperature_K": 350.0,
        "maximum_temperature_K": 450.0,
        "minimum_stress_value": 50.0,
        "maximum_stress_value": 150.0,
        "stress_unit_token": "custom-stress-unit",
        "minimum_strain_rate_value": 0.001,
        "maximum_strain_rate_value": 0.01,
        "strain_rate_unit_token": "custom-rate-unit",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        **IDENTITY,
        "exposures": (exposure(),),
        "qualification_envelope": envelope(),
        "structural_material_and_condition_reviewed": True,
        "liquid_metal_composition_and_impurities_reviewed": True,
        "contact_state_and_wetting_reviewed": True,
        "temperature_stress_and_strain_rate_reviewed": True,
        "exposure_clock_and_duration_reviewed": True,
        "observation_and_test_evidence_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return LiquidMetalEmbrittlementApplicability(**value)


def test_inside_caller_support_computes_without_susceptibility_claim():
    result = liquid_metal_embrittlement_applicability(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["test_evidence_summary"]["physical_specimen_ids"] == ["specimen-1"]


def test_reviewed_outside_range_or_wetting_is_out_of_scope():
    result = liquid_metal_embrittlement_applicability(
        payload(exposures=(exposure(maximum_temperature_K=550.0, wetting_descriptor="different"),))
    )
    assert result.status == "out_of_scope"
    reasons = result.values["exposure_comparisons"][0]["outside_support_reasons"]
    assert reasons == ["wetting_descriptor", "temperature_range"]


def test_unit_identity_invalid_evidence_and_review_need_data():
    assert (
        liquid_metal_embrittlement_applicability(
            payload(exposures=(exposure(stress_unit_token="other"),))
        ).status
        == "needs_data"
    )
    assert (
        liquid_metal_embrittlement_applicability(payload(material_condition_id="other")).status
        == "needs_data"
    )

    invalid = qualification_test_evidence(
        record_valid=False,
        supports_declared_envelope=False,
        invalid_or_limiting_basis="caller marked invalid",
    )
    result = liquid_metal_embrittlement_applicability(
        payload(qualification_envelope=envelope(test_evidence=(invalid,)))
    )
    assert result.status == "needs_data"
    assert result.values["invalid_test_evidence_ids"] == ["evidence-1"]
    assert (
        liquid_metal_embrittlement_applicability(payload(contact_state_and_wetting_reviewed=False)).status
        == "needs_data"
    )


def test_clock_and_range_contracts_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(
            exposures=(
                exposure("interval-1", start_time_s=0.0, end_time_s=20.0),
                exposure("interval-2", start_time_s=10.0, end_time_s=30.0),
            )
        )
    with pytest.raises(ValueError, match="strain-rate ranges must be ordered"):
        payload(exposures=(exposure(minimum_strain_rate_value=0.2),))


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.liquid_metal_embrittlement_applicability",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="exposure clock"),
        )
