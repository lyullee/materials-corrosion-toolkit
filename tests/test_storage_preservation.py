import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.storage_preservation import (
    StoragePreservationHistory,
    specifications,
    storage_preservation_history,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {
    "source_id": "authored-preservation-record",
    "origin": "synthetic",
    "citation": "authored preservation workflow test",
}


def interval(identifier, start, end, temperature=290.0, humidity=0.4, state="intact", **updates):
    row = {
        "interval_id": identifier,
        "start_time_s": start,
        "end_time_s": end,
        "record_valid": True,
        "temperature_K": temperature,
        "relative_humidity_fraction": humidity,
        "preservation_state_id": state,
        "evidence": [EVIDENCE],
    }
    row.update(updates)
    return row


def inputs(**updates):
    payload = {
        "record_id": "storage-001",
        "asset_id": "asset-001",
        "location_id": "warehouse-a",
        "clock_id": "elapsed-storage-clock",
        "horizon_start_s": 0.0,
        "horizon_end_s": 300.0,
        "environment_intervals": [
            interval("i0", 0.0, 100.0),
            interval("i1", 100.0, 200.0, temperature=305.0, state="degraded"),
            interval("i2", 200.0, 300.0, temperature=306.0, state="degraded"),
        ],
        "inspections": [
            {
                "inspection_id": "inspection-1",
                "inspection_time_s": 80.0,
                "reported_disposition": "caller reported intact",
                "evidence": [EVIDENCE],
            }
        ],
        "minimum_allowed_temperature_K": 280.0,
        "maximum_allowed_temperature_K": 300.0,
        "minimum_allowed_relative_humidity_fraction": 0.2,
        "maximum_allowed_relative_humidity_fraction": 0.6,
        "allowed_preservation_state_ids": ["intact"],
        "maximum_inspection_interval_s": 100.0,
        "clock_and_coverage_reviewed": True,
        "environment_units_reviewed": True,
        "preservation_state_mapping_reviewed": True,
        "declared_limits_reviewed": True,
        "inspection_records_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return payload


def test_complete_history_summarizes_exposure_and_inspection_overdue_time():
    result = storage_preservation_history(StoragePreservationHistory.model_validate(inputs()))
    assert result.status == "computed"
    assert result.values["temperature_outside_duration_s"] == pytest.approx(200.0)
    assert result.values["preservation_state_outside_duration_s"] == pytest.approx(200.0)
    assert result.values["maximum_continuous_any_declared_limit_outside_s"] == pytest.approx(200.0)
    assert result.values["outside_limit_interval_ids"] == ["i1", "i2"]
    assert result.values["inspection_gap_s"] == [80.0, 220.0]
    assert result.values["total_inspection_overdue_duration_s"] == pytest.approx(120.0)
    assert result.values["inspection_interval_exceeded"] is True


def test_gap_and_invalid_interval_are_preserved_as_needs_data_without_bridging():
    rows = [
        interval("i0", 0.0, 100.0),
        interval(
            "missing",
            150.0,
            200.0,
            record_valid=False,
            temperature=None,
            humidity=None,
            state=None,
            missing_basis="logger unavailable",
        ),
        interval("i2", 200.0, 300.0, temperature=305.0),
    ]
    result = storage_preservation_history(
        StoragePreservationHistory.model_validate(inputs(environment_intervals=rows))
    )
    assert result.status == "needs_data"
    assert result.values["uncovered_environment_duration_s"] == pytest.approx(50.0)
    assert result.values["invalid_environment_duration_s"] == pytest.approx(50.0)
    assert result.values["missing_environment_duration_s"] == pytest.approx(100.0)
    assert result.values["invalid_interval_ids"] == ["missing"]
    assert result.values["temperature_outside_duration_s"] == pytest.approx(100.0)
    assert result.values["maximum_continuous_temperature_outside_s"] == pytest.approx(100.0)


def test_missing_review_withholds_complete_status_but_retains_observations():
    result = storage_preservation_history(
        StoragePreservationHistory.model_validate(inputs(environment_units_reviewed=False))
    )
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["environment_units_reviewed"]
    assert result.values["valid_environment_duration_s"] == pytest.approx(300.0)


def test_history_contract_rejects_overlap_and_invalid_interval_without_basis():
    with pytest.raises(ValueError, match="cannot overlap"):
        StoragePreservationHistory.model_validate(
            inputs(environment_intervals=[interval("a", 0.0, 200.0), interval("b", 100.0, 300.0)])
        )
    with pytest.raises(ValueError, match="missing-data basis"):
        StoragePreservationHistory.model_validate(
            inputs(
                environment_intervals=[
                    interval(
                        "missing",
                        0.0,
                        300.0,
                        record_valid=False,
                        temperature=None,
                        humidity=None,
                        state=None,
                    )
                ]
            )
        )


def test_model_spec_enforces_asset_and_location_identity():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    request = StoragePreservationHistory.model_validate(inputs())
    good = registry.run(
        "fabrication.storage_preservation_history",
        request,
        RunContext(asset_id="asset-001", location_id="warehouse-a", time_basis="elapsed storage"),
    )
    assert good.status == "computed"
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.storage_preservation_history",
            request,
            RunContext(asset_id="other", location_id="warehouse-a", time_basis="elapsed storage"),
        )


def test_timeline_partitions_uncovered_invalid_and_limit_breach_spans():
    rows = [
        interval("i0", 0.0, 100.0),
        interval(
            "missing",
            150.0,
            200.0,
            record_valid=False,
            temperature=None,
            humidity=None,
            state=None,
            missing_basis="logger unavailable",
        ),
        interval("i2", 200.0, 300.0, temperature=305.0),
    ]
    result = storage_preservation_history(
        StoragePreservationHistory.model_validate(inputs(environment_intervals=rows))
    )
    timeline = result.values["environment_timeline"]
    assert [(row["start_time_s"], row["end_time_s"], row["coverage_status"]) for row in timeline] == [
        (0.0, 80.0, "observed"),
        (80.0, 100.0, "observed"),
        (100.0, 150.0, "uncovered"),
        (150.0, 200.0, "invalid_record"),
        (200.0, 300.0, "observed"),
    ]
    assert timeline[2]["missing_basis"] == "no environment interval supplied"
    assert timeline[3]["missing_basis"] == "logger unavailable"
    assert timeline[4]["outside_limit_dimensions"] == ["temperature"]
    assert sum(row["duration_s"] for row in timeline) == pytest.approx(300.0)
    assert result.values["inspection_schedule"][0]["gap_s"] == pytest.approx(80.0)
    assert result.values["inspection_schedule"][1]["overdue_duration_s"] == pytest.approx(120.0)
