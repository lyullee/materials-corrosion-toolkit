import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.binary_event_pair_calibration import (
    BinaryEventPairCalibration,
    binary_event_pair_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def observation(identifier, partition, first, second, weight=1.0, **updates):
    value = {
        "observation_id": identifier,
        "physical_sequence_id": f"sequence-{identifier}",
        "source_group_id": f"source-{identifier}",
        "independence_group_id": f"independence-{identifier}",
        "partition": partition,
        "observation_start_s": 0.0,
        "observation_end_s": 10.0,
        "event_a_occurs": first,
        "event_b_occurs": second,
        "sample_weight": weight,
        "record_digest": identifier[0] * 64,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(observations=None, **updates):
    if observations is None:
        observations = (
            observation("a-cal-00", "calibration", False, False),
            observation("b-cal-01", "calibration", False, True),
            observation("c-cal-10", "calibration", True, False),
            observation("d-cal-11", "calibration", True, True),
            observation("e-hold-00", "holdout", False, False),
            observation("f-hold-11", "holdout", True, True),
        )
    value = {
        "calibration_id": "calibration-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "observation_clock_id": "clock-1",
        "time_basis": "observation-clock",
        "event_a_id": "event-a",
        "event_a_definition": "caller observed event A in one observation interval",
        "event_b_id": "event-b",
        "event_b_definition": "caller observed event B in one observation interval",
        "observations": observations,
        "minimum_calibration_record_count": 1,
        "minimum_holdout_record_count": 1,
        "minimum_calibration_sequence_count": 1,
        "minimum_holdout_sequence_count": 1,
        "minimum_calibration_source_group_count": 1,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "event_definitions_reviewed": True,
        "observation_clock_and_scope_reviewed": True,
        "partition_assignments_reviewed": True,
        "physical_sequence_source_and_independence_groups_reviewed": True,
        "sample_weights_and_missingness_reviewed": True,
        "pseudocount_choice_reviewed": True,
        "record_digests_reviewed": True,
    }
    value.update(updates)
    return BinaryEventPairCalibration(**value)


def test_weighted_joint_table_phi_and_holdout_scores():
    result = binary_event_pair_calibration(payload())
    assert result.status == "computed"
    assert result.values["calibration_cell_probabilities"] == {
        "00": 0.25,
        "01": 0.25,
        "10": 0.25,
        "11": 0.25,
    }
    assert result.values["calibration_event_a_probability"] == pytest.approx(0.5)
    assert result.values["calibration_event_b_probability"] == pytest.approx(0.5)
    assert result.values["calibration_joint_probability"] == pytest.approx(0.25)
    assert result.values["calibration_covariance"] == pytest.approx(0.0)
    assert result.values["calibration_phi"] == pytest.approx(0.0)
    assert result.values["holdout_mean_negative_log_score"] == pytest.approx(math.log(4.0))
    assert result.values["holdout_multiclass_brier_score"] == pytest.approx(0.75)


def test_caller_pseudocount_is_explicit_and_changes_cells():
    observations = (
        observation("a-cal-00", "calibration", False, False),
        observation("b-hold-11", "holdout", True, True),
    )
    result = binary_event_pair_calibration(
        payload(
            observations,
            symmetric_cell_pseudocount=1.0,
            pseudocount_basis="caller symmetric smoothing for finite holdout score",
        )
    )
    assert result.status == "computed"
    assert result.values["calibration_cell_probabilities"] == {
        "00": 0.4,
        "01": 0.2,
        "10": 0.2,
        "11": 0.2,
    }
    assert result.values["holdout_mean_negative_log_score"] == pytest.approx(-math.log(0.2))

    with pytest.raises(ValueError, match="requires a caller-declared basis"):
        payload(observations, symmetric_cell_pseudocount=1.0)


def test_zero_probability_holdout_cell_is_not_clipped():
    observations = (
        observation("a-cal-00", "calibration", False, False),
        observation("b-cal-11", "calibration", True, True),
        observation("c-hold-01", "holdout", False, True, weight=2.0),
    )
    result = binary_event_pair_calibration(payload(observations))
    assert result.status == "computed"
    assert result.values["holdout_mean_negative_log_score"] is None
    assert result.values["holdout_zero_probability_observation_weight"] == pytest.approx(2.0)
    assert result.values["holdout_multiclass_brier_score"] == pytest.approx(1.5)


def test_missing_review_invalid_record_or_count_requirement_needs_data():
    assert binary_event_pair_calibration(payload(event_definitions_reviewed=False)).status == "needs_data"
    invalid = observation(
        "a-cal-00",
        "calibration",
        False,
        False,
        record_valid=False,
        invalid_or_missing_basis="caller marked invalid",
    )
    valid_holdout = observation("b-hold-11", "holdout", True, True)
    assert binary_event_pair_calibration(payload((invalid, valid_holdout))).status == "needs_data"
    assert binary_event_pair_calibration(payload(minimum_holdout_record_count=3)).status == "needs_data"


def test_partition_leakage_and_context_identity_are_enforced():
    leaked = (
        observation(
            "a-cal-00",
            "calibration",
            False,
            False,
            physical_sequence_id="same-sequence",
        ),
        observation(
            "b-hold-11",
            "holdout",
            True,
            True,
            physical_sequence_id="same-sequence",
        ),
    )
    with pytest.raises(ValueError, match="cannot cross"):
        payload(leaked)

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "reliability.binary_event_pair_calibration",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="observation-clock"),
        )
    with pytest.raises(ValueError, match="time basis"):
        registry.run(
            "reliability.binary_event_pair_calibration",
            payload(),
            RunContext(asset_id="asset-1", location_id="location-1", time_basis="other"),
        )
