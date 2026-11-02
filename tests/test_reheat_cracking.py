import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.reheat_cracking import (
    ReheatCrackingApplicability,
    reheat_cracking_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def observation(**updates):
    value = {
        "observation_id": "obs-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "partition": "qualification",
        "region_id": "haz-1",
        "method_id": "method-1",
        "metric_definition": "caller-defined examination metric",
        "reported_value": 0.1,
        "unit_token": "custom-metric",
        "expanded_uncertainty": 0.01,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "material_condition_id": "material-1",
        "weld_condition_id": "weld-1",
        "haz_condition_id": "haz-condition-1",
        "welding_process_id": "process-1",
        "heat_input_unit_token": "custom-heat-input",
        "minimum_heat_input_value": 0.5,
        "maximum_heat_input_value": 2.0,
        "minimum_reheat_temperature_K": 700.0,
        "maximum_reheat_temperature_K": 1000.0,
        "maximum_cumulative_reheat_duration_s": 7200.0,
        "stress_unit_token": "custom-stress",
        "minimum_stress_value": 0.0,
        "maximum_stress_value": 200.0,
        "supported_stress_descriptors": ("residual-plus-applied",),
        "supported_restraint_descriptors": ("high-restraint",),
        "supported_region_ids": ("haz-1",),
        "supported_method_ids": ("method-1",),
        "minimum_qualification_source_group_count": 1,
        "qualification_observations": (observation(),),
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "reheat-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "physical_scope_id": "haz-scope-1",
        "clock_id": "clock-1",
        "material_condition_id": "material-1",
        "weld_condition_id": "weld-1",
        "haz_condition_id": "haz-condition-1",
        "welding_process_id": "process-1",
        "heat_input_value": 1.0,
        "heat_input_unit_token": "custom-heat-input",
        "thermal_history": (
            {
                "interval_id": "interval-1",
                "stage_kind": "postweld_heat_treatment",
                "start_time_s": 0.0,
                "end_time_s": 3600.0,
                "minimum_temperature_K": 750.0,
                "maximum_temperature_K": 800.0,
                "record_digest": DIGEST_A,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "stress_descriptor": "residual-plus-applied",
        "stress_value": 100.0,
        "stress_unit_token": "custom-stress",
        "restraint_descriptor": "high-restraint",
        "candidate_envelopes": (envelope(),),
        "material_weld_and_haz_identity_reviewed": True,
        "welding_process_and_heat_input_reviewed": True,
        "heat_treatment_clock_and_temperature_reviewed": True,
        "stress_and_restraint_basis_reviewed": True,
        "specimen_region_and_source_groups_reviewed": True,
        "observation_method_units_and_uncertainty_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ReheatCrackingApplicability(**value)


def test_reviewed_case_is_within_caller_support():
    result = reheat_cracking_applicability(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["cumulative_reheat_duration_s"] == pytest.approx(3600.0)


def test_temperature_or_restraint_outside_support_is_visible():
    base = payload()
    hot = base.thermal_history[0].model_copy(update={"maximum_temperature_K": 1100.0})
    result = reheat_cracking_applicability(
        base.model_copy(update={"thermal_history": (hot,), "restraint_descriptor": "other"})
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_reasons"] == [
        "restraint_descriptor",
        "reheat_temperature_range",
    ]


def test_missing_review_invalid_evidence_and_unit_mismatch_need_data():
    assert (
        reheat_cracking_applicability(payload(stress_and_restraint_basis_reviewed=False)).status
        == "needs_data"
    )
    invalid = observation(
        record_valid=False,
        supports_declared_envelope=False,
        invalid_or_limiting_basis="authored invalid record",
    )
    assert (
        reheat_cracking_applicability(
            payload(candidate_envelopes=(envelope(qualification_observations=(invalid,)),))
        ).status
        == "needs_data"
    )
    assert reheat_cracking_applicability(payload(stress_unit_token="other-unit")).status == "needs_data"


def test_interval_order_and_context_identity_are_enforced():
    base = payload()
    later = base.thermal_history[0].model_copy(
        update={"interval_id": "interval-2", "start_time_s": 1800.0, "end_time_s": 4000.0}
    )
    with pytest.raises(ValueError, match="cannot overlap"):
        ReheatCrackingApplicability(
            **base.model_dump(exclude={"thermal_history"}),
            thermal_history=(base.thermal_history[0], later),
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.reheat_cracking_applicability",
            base,
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
