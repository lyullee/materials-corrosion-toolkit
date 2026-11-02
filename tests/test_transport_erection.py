import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.transport_erection import (
    TransportErectionHistory,
    specifications,
    transport_erection_history,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-handling-record",
    "origin": "synthetic",
    "citation": "authored handling and erection test record",
}


def interval(identifier, activity, kind, start, end, **updates):
    row = {
        "interval_id": identifier,
        "activity_id": activity,
        "activity_kind": kind,
        "start_time_s": start,
        "end_time_s": end,
        "record_valid": True,
        "evidence": [EVIDENCE],
    }
    row.update(updates)
    return row


def observation(identifier, interval_id, time_s, metric, value, unit, **updates):
    row = {
        "observation_id": identifier,
        "interval_id": interval_id,
        "observation_time_s": time_s,
        "metric_id": metric,
        "value": value,
        "unit": unit,
        "record_valid": True,
        "evidence": [EVIDENCE],
    }
    row.update(updates)
    return row


def inspection(identifier, stage, time_s, disposition=None, **updates):
    row = {
        "inspection_id": identifier,
        "stage_id": stage,
        "inspection_time_s": time_s,
        "inspection_type": "caller procedure visual check",
        "reported_finding": "caller reported no visible change",
        "caller_disposition_id": disposition,
        "record_valid": True,
        "evidence": [EVIDENCE],
    }
    row.update(updates)
    return row


def inputs(**updates):
    payload = {
        "record_id": "transport-001",
        "asset_id": "vessel-001",
        "location_id": "whole-asset-handling",
        "clock_id": "shipment-elapsed-clock",
        "horizon_start_s": 0.0,
        "horizon_end_s": 200.0,
        "activity_intervals": [
            interval("road", "road-leg-1", "transport", 0.0, 100.0),
            interval("erection", "lift-1", "lifting_and_erection", 100.0, 200.0),
        ],
        "metric_observations": [
            observation("shock-1", "road", 50.0, "peak_acceleration", 6.0, "m/s^2"),
            observation("tilt-1", "erection", 150.0, "tilt_angle", 0.05, "rad"),
        ],
        "metric_limits": [
            {
                "metric_id": "peak_acceleration",
                "metric_definition": "caller-defined signed sensor-axis peak magnitude",
                "unit": "m/s^2",
                "maximum_value": 5.0,
                "limit_basis": "caller engineering plan",
                "caller_disposition_id_if_outside": "review-shock-record",
            },
            {
                "metric_id": "tilt_angle",
                "metric_definition": "caller-defined inclination from installation datum",
                "unit": "rad",
                "minimum_value": -0.1,
                "maximum_value": 0.1,
                "limit_basis": "caller erection plan",
                "caller_disposition_id_if_outside": "review-erection-alignment",
            },
        ],
        "inspections": [
            inspection("pre-lift", "pre_lift", 100.0),
            inspection("post-set", "post_erection", 200.0, "release-to-next-caller-stage"),
        ],
        "required_inspection_stage_ids": ["pre_lift", "post_erection"],
        "clock_and_activity_coverage_reviewed": True,
        "metric_identity_and_units_reviewed": True,
        "metric_limits_reviewed": True,
        "inspection_stage_mapping_reviewed": True,
        "disposition_mapping_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_complete_history_preserves_outside_limit_as_caller_disposition_not_acceptance():
    result = transport_erection_history(TransportErectionHistory.model_validate(inputs()))
    assert result.status == "computed"
    assert result.values["missing_activity_duration_s"] == pytest.approx(0.0)
    assert result.values["outside_declared_limit_count"] == 1
    row = result.values["outside_declared_limit_observations"][0]
    assert row["observation_id"] == "shock-1"
    assert row["above_declared_maximum"] is True
    assert row["caller_disposition_id"] == "review-shock-record"
    assert result.values["missing_required_inspection_stage_ids"] == []


def test_gap_invalid_observation_and_missing_stage_remain_needs_data():
    activities = [
        interval("road", "road-leg-1", "transport", 0.0, 80.0),
        interval("erection", "lift-1", "erection", 100.0, 200.0),
    ]
    observations = [
        observation(
            "missing-shock",
            "road",
            50.0,
            "peak_acceleration",
            None,
            "m/s^2",
            record_valid=False,
            invalid_basis="sensor power interruption",
        )
    ]
    result = transport_erection_history(
        TransportErectionHistory.model_validate(
            inputs(
                activity_intervals=activities,
                metric_observations=observations,
                inspections=[inspection("pre-lift", "pre_lift", 100.0)],
            )
        )
    )
    assert result.status == "needs_data"
    assert result.values["uncovered_activity_duration_s"] == pytest.approx(20.0)
    assert result.values["invalid_metric_observation_ids"] == ["missing-shock"]
    assert result.values["missing_required_inspection_stage_ids"] == ["post_erection"]


def test_unmatched_metric_and_unit_conflict_are_not_silently_compared():
    rows = [
        observation("unknown", "road", 20.0, "custom_metric", 1.0, "custom-unit"),
        observation("wrong-unit", "road", 30.0, "peak_acceleration", 6.0, "g"),
    ]
    result = transport_erection_history(
        TransportErectionHistory.model_validate(inputs(metric_observations=rows))
    )
    assert result.status == "needs_data"
    assert result.values["unmatched_metric_observation_ids"] == ["unknown"]
    assert result.values["unit_mismatch_observation_ids"] == ["wrong-unit"]
    assert result.values["outside_declared_limit_count"] == 0


def test_contract_rejects_orphan_and_out_of_interval_observations():
    with pytest.raises(ValueError, match="declared activity interval"):
        TransportErectionHistory.model_validate(
            inputs(
                metric_observations=[
                    observation("orphan", "not-declared", 50.0, "peak_acceleration", 1.0, "m/s^2")
                ]
            )
        )
    with pytest.raises(ValueError, match="inside its activity interval"):
        TransportErectionHistory.model_validate(
            inputs(
                metric_observations=[observation("late", "road", 150.0, "peak_acceleration", 1.0, "m/s^2")]
            )
        )


def test_model_spec_enforces_context_identity():
    registry = ModelRegistry()
    for spec in specifications():
        registry.register(spec)
    request = TransportErectionHistory.model_validate(inputs())
    result = registry.run(
        "fabrication.transport_erection_history",
        request,
        RunContext(
            asset_id="vessel-001",
            location_id="whole-asset-handling",
            time_basis="shipment elapsed clock",
        ),
    )
    assert result.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.transport_erection_history",
            request,
            RunContext(asset_id="other", location_id="whole-asset-handling", time_basis="clock"),
        )
