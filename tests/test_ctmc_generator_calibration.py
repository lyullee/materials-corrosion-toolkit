import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.ctmc_generator_calibration import (
    CTMCGeneratorCalibration,
    ctmc_generator_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def observation(identifier, partition, exposures, counts, weight=1.0, **updates):
    value = {
        "observation_id": identifier,
        "physical_sequence_id": f"sequence-{identifier}",
        "source_group_id": f"source-{identifier}",
        "independence_group_id": f"independence-{identifier}",
        "partition": partition,
        "observation_start_s": 0.0,
        "observation_end_s": 100.0,
        "sample_weight": weight,
        "exposure_unit_token": "h",
        "state_exposures": tuple(
            {"state_id": state_id, "exposure_duration": duration} for state_id, duration in exposures.items()
        ),
        "transition_counts": tuple(
            {"transition_id": transition_id, "transition_count": count}
            for transition_id, count in counts.items()
        ),
        "record_digest": identifier[0] * 64,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def calibration_record(identifier="a-cal", **updates):
    return observation(
        identifier,
        "calibration",
        {"healthy": 10.0, "degraded": 5.0, "failed": 0.0},
        {"healthy-degraded": 2, "healthy-failed": 1, "degraded-failed": 1},
        **updates,
    )


def holdout_record(identifier="b-hold", **updates):
    return observation(
        identifier,
        "holdout",
        {"healthy": 5.0, "degraded": 2.0, "failed": 1.0},
        {"healthy-degraded": 1, "healthy-failed": 0, "degraded-failed": 1},
        **updates,
    )


def payload(observations=None, **updates):
    if observations is None:
        observations = (calibration_record(), holdout_record())
    value = {
        "calibration_id": "ctmc-calibration-1",
        "asset_id": "asset-1",
        "location_id": "scope-location-1",
        "physical_scope_id": "scope-1",
        "observation_clock_id": "clock-1",
        "time_basis": "observation-clock",
        "state_ids": ("healthy", "degraded", "failed"),
        "state_definitions": (
            "caller healthy state",
            "caller degraded state",
            "caller failed state",
        ),
        "transition_definitions": (
            {
                "transition_id": "healthy-degraded",
                "origin_state_id": "healthy",
                "destination_state_id": "degraded",
                "transition_definition": "caller observed healthy to degraded transition",
            },
            {
                "transition_id": "healthy-failed",
                "origin_state_id": "healthy",
                "destination_state_id": "failed",
                "transition_definition": "caller observed healthy to failed transition",
            },
            {
                "transition_id": "degraded-failed",
                "origin_state_id": "degraded",
                "destination_state_id": "failed",
                "transition_definition": "caller observed degraded to failed transition",
            },
        ),
        "observations": observations,
        "minimum_calibration_record_count": 1,
        "minimum_holdout_record_count": 1,
        "minimum_calibration_sequence_count": 1,
        "minimum_holdout_sequence_count": 1,
        "minimum_calibration_source_group_count": 1,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "state_and_transition_definitions_reviewed": True,
        "observation_clock_scope_and_exposure_units_reviewed": True,
        "transition_counts_exposures_and_weights_reviewed": True,
        "partition_assignments_reviewed": True,
        "physical_sequence_source_and_independence_groups_reviewed": True,
        "single_generator_calibration_scope_reviewed": True,
        "pseudocount_choice_reviewed": True,
        "record_digests_and_missingness_reviewed": True,
    }
    value.update(updates)
    return CTMCGeneratorCalibration(**value)


def test_rates_generator_and_holdout_scores_are_computed():
    result = ctmc_generator_calibration(payload())
    assert result.status == "computed"
    assert result.values["estimated_transition_rates"] == {
        "healthy-degraded": pytest.approx(0.2),
        "healthy-failed": pytest.approx(0.1),
        "degraded-failed": pytest.approx(0.2),
    }
    assert result.values["estimated_generator"] == [
        [pytest.approx(-0.3), pytest.approx(0.2), pytest.approx(0.1)],
        [0.0, pytest.approx(-0.2), pytest.approx(0.2)],
        [0.0, 0.0, 0.0],
    ]
    assert result.values["holdout_total_negative_log_likelihood"] is not None
    assert result.values["holdout_total_poisson_deviance"] is not None
    assert result.values["generator_rate_unit_token"] == "1/(h)"


def test_explicit_pseudocount_changes_zero_count_rate():
    calibration = calibration_record()
    zero_count = tuple(
        {**row, "transition_count": 0} if row["transition_id"] == "healthy-failed" else row
        for row in calibration["transition_counts"]
    )
    calibration["transition_counts"] = zero_count
    result = ctmc_generator_calibration(
        payload(
            (calibration, holdout_record()),
            transition_count_pseudocount=1.0,
            pseudocount_basis="caller symmetric transition-count smoothing",
        )
    )
    assert result.status == "computed"
    assert result.values["estimated_transition_rates"]["healthy-failed"] == pytest.approx(0.1)

    with pytest.raises(ValueError, match="requires a caller-declared basis"):
        payload(transition_count_pseudocount=1.0)


def test_zero_expected_positive_holdout_count_is_not_clipped():
    calibration = calibration_record()
    calibration["transition_counts"] = tuple(
        {**row, "transition_count": 0} if row["transition_id"] == "healthy-failed" else row
        for row in calibration["transition_counts"]
    )
    holdout = holdout_record()
    holdout["transition_counts"] = tuple(
        {**row, "transition_count": 2} if row["transition_id"] == "healthy-failed" else row
        for row in holdout["transition_counts"]
    )
    result = ctmc_generator_calibration(payload((calibration, holdout)))
    assert result.status == "computed"
    assert result.values["holdout_total_negative_log_likelihood"] is None
    assert result.values["holdout_total_poisson_deviance"] is None
    assert result.values["holdout_zero_expected_positive_count_weight"] == pytest.approx(2.0)


def test_missing_review_count_or_origin_exposure_needs_data():
    assert (
        ctmc_generator_calibration(payload(state_and_transition_definitions_reviewed=False)).status
        == "needs_data"
    )
    assert ctmc_generator_calibration(payload(minimum_holdout_record_count=2)).status == "needs_data"

    calibration = calibration_record()
    calibration["state_exposures"] = tuple(
        {**row, "exposure_duration": 0.0} if row["state_id"] == "degraded" else row
        for row in calibration["state_exposures"]
    )
    result = ctmc_generator_calibration(payload((calibration, holdout_record())))
    assert result.status == "needs_data"
    assert result.values["zero_calibration_exposure_transition_ids"] == ["degraded-failed"]


def test_partition_leakage_and_context_identity_are_enforced():
    calibration = calibration_record(physical_sequence_id="shared-sequence")
    holdout = holdout_record(physical_sequence_id="shared-sequence")
    with pytest.raises(ValueError, match="cannot cross"):
        payload((calibration, holdout))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "reliability.ctmc_generator_calibration",
            payload(),
            RunContext(asset_id="other", location_id="scope-location-1", time_basis="observation-clock"),
        )
    with pytest.raises(ValueError, match="time basis"):
        registry.run(
            "reliability.ctmc_generator_calibration",
            payload(),
            RunContext(asset_id="asset-1", location_id="scope-location-1", time_basis="other"),
        )
