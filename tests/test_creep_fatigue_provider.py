import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.creep_fatigue_provider import (
    CreepFatigueInteractionProviderAssessment,
    creep_fatigue_interaction_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def qualification_record(identifier, partition, source, independence, **updates):
    value = {
        "evidence_record_id": identifier,
        "partition": partition,
        "physical_specimen_id": f"specimen-{identifier}",
        "source_group_id": source,
        "independence_group_id": independence,
        "material_condition_id": "condition-1",
        "interaction_basis_id": "interaction-basis-1",
        "creep_exposure_definition": "caller hold-time quantity",
        "creep_exposure_unit_token": "s",
        "fatigue_exposure_definition": "caller counted-cycle quantity",
        "fatigue_exposure_unit_token": "cycle",
        "result_metric_definition": "caller interaction metric",
        "result_unit_token": "custom-interaction-unit",
        "observed_value": 0.8,
        "predicted_value": 0.82,
        "expanded_observation_uncertainty": 0.05,
        "uncertainty_coverage_factor": 2.0,
        "provider_model_id": "model-1",
        "provider_model_revision": "model-revision-1",
        "provider_id": "provider-1",
        "provider_revision": "provider-revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "interaction_basis_id": "interaction-basis-1",
        "creep_exposure_definition": "caller hold-time quantity",
        "creep_exposure_unit_token": "s",
        "fatigue_exposure_definition": "caller counted-cycle quantity",
        "fatigue_exposure_unit_token": "cycle",
        "minimum_temperature_K": 600.0,
        "maximum_temperature_K": 900.0,
        "supported_stress_history_descriptors": ("stress-history-a",),
        "supported_strain_history_descriptors": ("strain-history-a",),
        "supported_cycle_or_block_descriptors": ("cycle-block-a",),
        "maximum_single_block_duration_s": 1000.0,
        "maximum_cumulative_duration_s": 2000.0,
        "provider_model_id": "model-1",
        "provider_model_revision": "model-revision-1",
        "provider_id": "provider-1",
        "provider_revision": "provider-revision-1",
        "provider_configuration_digest": DIGEST_A,
        "result_metric_definition": "caller interaction metric",
        "result_unit_token": "custom-interaction-unit",
        "minimum_supported_result_value": 0.0,
        "maximum_supported_result_value": 1.0,
        "qualification_evidence": (
            qualification_record("cal-1", "calibration", "source-cal", "ind-cal"),
            qualification_record("hold-1", "holdout", "source-hold", "ind-hold"),
        ),
        "minimum_calibration_source_group_count": 1,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "qualification_basis": "caller validation plan",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def block(identifier="block-1", start=0.0, end=500.0, **updates):
    value = {
        "block_id": identifier,
        "start_time_s": start,
        "end_time_s": end,
        "minimum_temperature_K": 650.0,
        "maximum_temperature_K": 800.0,
        "stress_history_descriptor": "stress-history-a",
        "strain_history_descriptor": "strain-history-a",
        "cycle_or_block_descriptor": "cycle-block-a",
        "history_data_digest": DIGEST_D,
        "creep_exposure_definition": "caller hold-time quantity",
        "creep_exposure_value": 100.0,
        "creep_exposure_unit_token": "s",
        "fatigue_exposure_definition": "caller counted-cycle quantity",
        "fatigue_exposure_value": 10.0,
        "fatigue_exposure_unit_token": "cycle",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def result_record(**updates):
    value = {
        "result_record_id": "result-1",
        "interaction_basis_id": "interaction-basis-1",
        "block_history_digest": DIGEST_D,
        "provider_model_id": "model-1",
        "provider_model_revision": "model-revision-1",
        "provider_id": "provider-1",
        "provider_revision": "provider-revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "result_metric_definition": "caller interaction metric",
        "result_value": 0.7,
        "result_unit_token": "custom-interaction-unit",
        "expanded_uncertainty": 0.05,
        "uncertainty_coverage_factor": 2.0,
        "solution_state": "caller-reviewed completed state",
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
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "interaction_basis_id": "interaction-basis-1",
        "creep_exposure_definition": "caller hold-time quantity",
        "creep_exposure_unit_token": "s",
        "fatigue_exposure_definition": "caller counted-cycle quantity",
        "fatigue_exposure_unit_token": "cycle",
        "exposure_blocks": (block(),),
        "provider_result": result_record(),
        "candidate_envelopes": (envelope(),),
        "material_condition_and_physical_scope_reviewed": True,
        "clock_block_order_and_history_digests_reviewed": True,
        "temperature_stress_strain_and_cycle_descriptors_reviewed": True,
        "separate_creep_and_fatigue_quantity_definitions_reviewed": True,
        "interaction_basis_and_provider_model_reviewed": True,
        "result_metric_units_and_uncertainty_reviewed": True,
        "specimen_source_independence_and_partitions_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return CreepFatigueInteractionProviderAssessment(**value)


def test_qualified_interaction_result_is_preserved_without_damage_sum():
    calculated = creep_fatigue_interaction_provider_evidence(payload())
    assert calculated.status == "computed"
    assert calculated.values["declared_applicability_outcome"] == "within_support"
    assert calculated.values["provider_reported_result_value"] == pytest.approx(0.7)
    assert calculated.values["holdout_independence_group_ids"] == ["ind-hold"]


def test_block_or_result_outside_support_is_out_of_scope():
    calculated = creep_fatigue_interaction_provider_evidence(
        payload(exposure_blocks=(block(maximum_temperature_K=950.0),))
    )
    assert calculated.status == "out_of_scope"
    assert calculated.values["outside_support_block_ids"] == ["block-1"]

    assert (
        creep_fatigue_interaction_provider_evidence(
            payload(provider_result=result_record(result_value=1.2))
        ).status
        == "out_of_scope"
    )


def test_interaction_basis_identity_is_exact():
    calculated = creep_fatigue_interaction_provider_evidence(
        payload(interaction_basis_id="independent-linear-sum")
    )
    assert calculated.status == "out_of_scope"
    assert calculated.values["identity_matching_envelope_ids"] == []


def test_quantity_unit_provider_or_partition_problem_needs_data():
    calculated = creep_fatigue_interaction_provider_evidence(
        payload(exposure_blocks=(block(creep_exposure_unit_token="h"),))
    )
    assert calculated.status == "needs_data"
    assert calculated.values["block_quantity_definition_or_unit_mismatch_ids"] == ["block-1"]

    assert (
        creep_fatigue_interaction_provider_evidence(
            payload(provider_result=result_record(provider_revision="other"))
        ).status
        == "needs_data"
    )
    only_calibration = envelope(
        qualification_evidence=(qualification_record("cal-1", "calibration", "source-cal", "ind-cal"),)
    )
    calculated = creep_fatigue_interaction_provider_evidence(payload(candidate_envelopes=(only_calibration,)))
    assert calculated.status == "needs_data"
    assert calculated.values["qualification_partition_counts_sufficient"] is False


def test_block_clock_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(exposure_blocks=(block(), block("block-2", 400.0, 800.0)))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "structural.creep_fatigue_interaction_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
