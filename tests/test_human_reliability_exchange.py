from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.human_reliability_exchange import (
    HumanReliabilityEstimateRecord,
    human_reliability_estimate_record,
)


def event():
    return {
        "id": "manual-isolation-failure",
        "task_id": "isolate-release",
        "step_ids": ["detect", "close-valve"],
        "role": "response",
        "failure_definition": "operator does not complete the reviewed isolation action",
        "opportunity_definition": "one detected release requiring manual isolation",
        "conditioning": "automatic isolation failed and cues are available",
        "deadline_s": 30.0,
        "includes_recovery": True,
        "includes_timing": True,
        "dependency_group": "shared-cues",
    }


def estimate():
    return {
        "event_id": "manual-isolation-failure",
        "method": "authored-test-method",
        "probability": 0.1,
        "conditioning": "automatic isolation failed and cues are available",
        "evidence_ids": ["procedure-review", "authored-observation"],
        "uncertainty": {"basis": "authored exchange test only"},
        "includes": ["recovery", "timing"],
        "status": "research",
        "trace": {"test_case": "not empirical plant validation"},
    }


def record():
    return human_reliability_estimate_record(
        provider_id="human-reliability-toolkit",
        provider_revision="d2754bbea16e12d00240e88d13cb4badbe672ac3",
        assessment_input_digest="1" * 64,
        procedure_version="authored-procedure-1",
        context_id="authored-context",
        source_event=event(),
        source_estimate=estimate(),
        limitations=["Synthetic exchange record; not an operator or plant-performance claim."],
    )


def test_human_reliability_record_round_trip_preserves_opportunity_semantics():
    source = record()
    restored = HumanReliabilityEstimateRecord.model_validate_json(source.model_dump_json())

    assert restored.probability_per_opportunity == 0.1
    assert restored.probability_semantics == "failure_probability_per_defined_opportunity"
    assert restored.opportunity_definition == event()["opportunity_definition"]
    assert not restored.empirical_plant_validation_claim


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("probability_per_opportunity",), 0.2),
        (("source_estimate", "probability"), 0.2),
        (("source_event", "conditioning"), "different conditioning"),
        (("provider_revision",), "tampered"),
    ],
)
def test_human_reliability_record_rejects_tampering(path, replacement):
    payload = deepcopy(record().model_dump(mode="json"))
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement

    with pytest.raises(ValidationError):
        HumanReliabilityEstimateRecord.model_validate(payload)


def test_event_and_estimate_must_agree_on_recovery_and_timing_scope():
    value = estimate()
    value["includes"] = ["timing"]

    with pytest.raises(ValidationError, match="recovery scope"):
        human_reliability_estimate_record(
            provider_id="human-reliability-toolkit",
            provider_revision="revision",
            assessment_input_digest="2" * 64,
            procedure_version="procedure",
            context_id="context",
            source_event=event(),
            source_estimate=value,
            limitations=["authored negative control"],
        )


def test_period_first_failure_semantics_cannot_be_substituted():
    payload = record().model_dump(mode="json")
    payload["probability_semantics"] = "conditional_first_failure_in_period"

    with pytest.raises(ValidationError):
        HumanReliabilityEstimateRecord.model_validate(payload)
