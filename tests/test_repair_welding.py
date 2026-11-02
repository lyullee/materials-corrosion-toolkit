import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.repair_welding import (
    RepairWeldingHistory,
    repair_welding_history,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64

KINDS = (
    "removal",
    "pre_deposition_inspection",
    "deposition",
    "heat_treatment",
    "subsequent_examination",
)


def step(index, kind, **updates):
    value = {
        "step_record_id": f"record-{index}",
        "stage_id": f"stage-{index}",
        "step_kind": kind,
        "physical_scope_id": "repair-cavity-1",
        "location_id": "joint-1",
        "start_time_s": float((index - 1) * 10),
        "end_time_s": float(index * 10),
        "procedure_id": f"procedure-{index}",
        "procedure_revision": "revision-1",
        "provider_id": f"provider-{index}",
        "provider_revision": "provider-revision-1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "activity_descriptor": f"caller-recorded {kind}",
        "reported_finding_or_outcome": "caller-recorded observation"
        if "inspection" in kind or "examination" in kind
        else None,
        "metrics": (
            {
                "metric_id": "stage-metric",
                "value": float(index),
                "unit_token": "custom-unit",
                "measurement_basis": "caller measurement",
                "evidence": (EVIDENCE,),
            },
        ),
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def requirement(index, kind, **updates):
    value = {
        "stage_id": f"stage-{index}",
        "step_kind": kind,
        "procedure_id": f"procedure-{index}",
        "procedure_revision": "revision-1",
        "provider_id": f"provider-{index}",
        "provider_revision": "provider-revision-1",
        "required_provider_state_digest": DIGEST_A,
        "required_provider_configuration_digest": DIGEST_B,
        "metric_envelopes": (
            {
                "metric_id": "stage-metric",
                "unit_token": "custom-unit",
                "minimum_value": 0.0,
                "maximum_value": 10.0,
                "applicability_basis": "caller workflow",
            },
        ),
        "requirement_basis": "caller-owned workflow",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "workflow-1",
        "repair_scope_id": "repair-1",
        "component_condition_id": "component-condition-1",
        "repair_location_id": "joint-1",
        "required_stages": tuple(requirement(index, kind) for index, kind in enumerate(KINDS, 1)),
        "declaration_basis": "caller-owned repair workflow",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "history_id": "history-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "repair_scope_id": "repair-1",
        "component_condition_id": "component-condition-1",
        "clock_id": "repair-clock-1",
        "horizon_start_s": 0.0,
        "horizon_end_s": 50.0,
        "steps": tuple(step(index, kind) for index, kind in enumerate(KINDS, 1)),
        "candidate_workflow_envelopes": (envelope(),),
        "repair_scope_and_location_reviewed": True,
        "sequence_and_clock_reviewed": True,
        "procedure_and_provider_identity_reviewed": True,
        "provider_digests_reviewed": True,
        "step_evidence_reviewed": True,
        "workflow_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return RepairWeldingHistory(**value)


def test_full_ordered_history_is_compared_without_acceptance_claim():
    result = repair_welding_history(payload())
    assert result.status == "computed"
    assert result.values["stage_sequence_matches_exactly"] is True
    assert result.values["all_steps_within_declared_workflow_envelope"] is True
    assert result.values["recorded_step_kind_counts"]["subsequent_examination"] == 1


@pytest.mark.parametrize("index", [0, 4])
def test_step_from_another_location_cannot_satisfy_repair_history(index):
    steps = list(payload().steps)
    steps[index] = steps[index].model_copy(update={"location_id": "another-joint"})
    with pytest.raises(ValueError, match="step location must match"):
        payload(steps=tuple(steps))


def test_outside_metric_and_provider_mismatch_remain_visible():
    steps = list(payload().steps)
    steps[2] = steps[2].model_copy(
        update={
            "provider_revision": "other-revision",
            "metrics": (steps[2].metrics[0].model_copy(update={"value": 20.0}),),
        }
    )
    result = repair_welding_history(payload(steps=tuple(steps)))
    assert result.status == "computed"
    assert result.values["identity_mismatch_stage_ids"] == ["stage-3"]
    assert result.values["outside_declared_metric_envelope_ids"] == ["stage-3:stage-metric"]
    assert result.values["all_steps_within_declared_workflow_envelope"] is False


def test_missing_stage_unit_conflict_or_invalid_record_needs_data():
    assert repair_welding_history(payload(steps=payload().steps[:-1])).status == "needs_data"
    steps = list(payload().steps)
    steps[0] = steps[0].model_copy(
        update={"metrics": (steps[0].metrics[0].model_copy(update={"unit_token": "other"}),)}
    )
    result = repair_welding_history(payload(steps=tuple(steps)))
    assert result.status == "needs_data"
    assert result.values["unit_mismatch_metric_ids"] == ["stage-1:stage-metric"]

    steps = list(payload().steps)
    steps[0] = steps[0].model_copy(update={"record_valid": False, "invalid_or_missing_basis": "lost record"})
    assert repair_welding_history(payload(steps=tuple(steps))).status == "needs_data"


def test_contract_rejects_overlap_and_missing_examination_finding():
    steps = list(payload().steps)
    steps[1] = steps[1].model_copy(update={"start_time_s": 5.0})
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(steps=tuple(steps))

    steps = [step(index, kind) for index, kind in enumerate(KINDS, 1)]
    steps[1]["reported_finding_or_outcome"] = None
    with pytest.raises(ValueError, match="requires a reported finding"):
        payload(steps=tuple(steps))


def test_exact_scope_and_context_are_enforced():
    assert repair_welding_history(payload(repair_scope_id="other")).status == "out_of_scope"
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.repair_welding_history",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="repair clock"),
        )
