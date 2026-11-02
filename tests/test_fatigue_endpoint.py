import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-fatigue-test",
        location_id="pressure-boundary",
        time_basis="reviewed cumulative loading cycles",
    )


def segment(segment_id="s1", specimen_id="p1", load_case_id="l1", cycles=1000.0):
    return {
        "segment_id": segment_id,
        "physical_specimen_id": specimen_id,
        "load_case_id": load_case_id,
        "valid_loading_cycles": cycles,
        "cycle_count_basis": "segment_local_counter",
    }


def run(context, **overrides):
    inputs = {
        "segments": [segment()],
        "initial_pressure_Pa": 60e6,
        "observed_pressure_drop_Pa": 10e6,
        "declared_drop_fraction_threshold": 0.1,
        "event_origin": "specimen",
        "specimen_event_kind": "through_wall_crack",
        "specimen_pressure_loss_confirmed": True,
        "same_physical_specimen_across_segments_declared": True,
        "loading_history_reconstructable": True,
        "runout_limit_cycles": 2e6,
        "observation_window_closed": True,
    }
    return default_registry().run("fatigue.pressure_loss_endpoint", inputs | overrides, context)


def test_confirmed_specimen_event_is_failure_endpoint(context):
    result = run(context)
    assert result.status == "computed"
    assert result.values["endpoint_classification"] == "confirmed_specimen_pressure_loss_endpoint"
    assert result.values["usable_as_fatigue_observation"] is True
    assert result.values["censoring_role"] == "failure_endpoint"
    assert result.values["cycles_at_confirmed_endpoint"] == 1000.0


def test_declared_pressure_drop_threshold_is_inclusive(context):
    result = run(context, observed_pressure_drop_Pa=6e6)
    assert result.status == "computed"
    assert result.values["pressure_drop_fraction"] == pytest.approx(0.1)
    assert result.values["threshold_met"] is True
    assert result.values["endpoint_classification"] == "confirmed_specimen_pressure_loss_endpoint"


def test_pressure_threshold_alone_does_not_turn_system_event_into_failure(context):
    result = run(
        context,
        event_origin="pressure_system",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert result.status == "computed"
    assert result.values["threshold_met"] is True
    assert result.values["endpoint_classification"] == "system_or_instrument_interruption"
    assert result.values["resume_eligible"] is True
    assert result.values["usable_as_fatigue_observation"] is False


def test_valid_segments_accumulate_for_same_specimen_and_load_case(context):
    result = run(
        context,
        segments=[segment("s1", cycles=600.0), segment("s2", cycles=400.0)],
        event_origin="instrumentation",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert result.values["cumulative_valid_cycles"] == 1000.0
    assert result.values["resume_eligible"] is True


@pytest.mark.parametrize(
    "segments",
    [
        [segment("s1", "p1"), segment("s2", "p2")],
        [segment("s1", load_case_id="l1"), segment("s2", load_case_id="l2")],
        [segment("duplicate"), segment("duplicate")],
    ],
)
def test_inconsistent_segment_identity_is_rejected(context, segments):
    with pytest.raises(ValidationError):
        run(context, segments=segments)


def test_unresolved_event_and_unreconstructable_history_need_data(context):
    unresolved = run(
        context,
        event_origin="unresolved",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert unresolved.status == "needs_data"
    assert unresolved.values["endpoint_classification"] == "unresolved_event_origin"

    history = run(context, loading_history_reconstructable=False)
    assert history.status == "needs_data"
    assert history.values["endpoint_classification"] == "invalid_or_ambiguous_history"


def test_unconfirmed_or_subthreshold_specimen_event_needs_review(context):
    unconfirmed = run(context, specimen_pressure_loss_confirmed=False)
    assert unconfirmed.status == "needs_data"
    assert unconfirmed.values["endpoint_classification"] == "specimen_event_needs_review"

    subthreshold = run(context, observed_pressure_drop_Pa=1e6)
    assert subthreshold.status == "needs_data"
    assert subthreshold.values["threshold_met"] is False


def test_closed_no_event_at_limit_is_right_censored_runout(context):
    result = run(
        context,
        segments=[segment(cycles=2e6)],
        observed_pressure_drop_Pa=0.0,
        event_origin="none",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert result.status == "computed"
    assert result.values["endpoint_classification"] == "runout"
    assert result.values["censoring_role"] == "right_censored_runout"
    assert result.values["usable_as_fatigue_observation"] is True


def test_below_limit_or_unattributed_pressure_loss_is_not_runout(context):
    incomplete = run(
        context,
        observed_pressure_drop_Pa=0.0,
        event_origin="none",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert incomplete.status == "needs_data"
    assert incomplete.values["endpoint_classification"] == "ongoing_or_incomplete"

    unattributed = run(
        context,
        event_origin="none",
        specimen_event_kind="none",
        specimen_pressure_loss_confirmed=False,
    )
    assert unattributed.status == "needs_data"
    assert unattributed.values["endpoint_classification"] == "unresolved_pressure_loss"


def test_impossible_pressure_drop_and_cross_origin_confirmation_are_rejected(context):
    with pytest.raises(ValidationError):
        run(context, observed_pressure_drop_Pa=61e6)
    with pytest.raises(ValidationError):
        run(context, event_origin="pressure_system")


def test_endpoint_contract_does_not_infer_strength_life_or_probability(context):
    result = run(context)
    assert not any(
        token in key for key in result.values for token in ("strength", "predicted_life", "probability")
    )
    assert result.probability_semantics == {}
