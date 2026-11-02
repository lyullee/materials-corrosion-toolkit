import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.under_insulation import (
    UnderInsulationExposureHistory,
    specifications,
    under_insulation_exposure_history,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored CUI test"}


def interval(identifier, start, end, temperature=330.0, wetness="wet", condition="damaged", **updates):
    value = {
        "interval_id": identifier,
        "start_time_s": start,
        "end_time_s": end,
        "record_valid": True,
        "surface_temperature_K": temperature,
        "wetness_state_id": wetness,
        "insulation_condition_id": condition,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "record_id": "cui-1",
        "asset_id": "asset-1",
        "location_id": "line-1",
        "clock_id": "exposure-clock",
        "horizon_start_s": 0.0,
        "horizon_end_s": 300.0,
        "intervals": (
            interval("i1", 0.0, 100.0),
            interval("i2", 100.0, 200.0),
            interval("i3", 200.0, 300.0, wetness="dry"),
        ),
        "exposure_definition": {
            "definition_id": "caller-cui-window",
            "minimum_surface_temperature_K": 300.0,
            "maximum_surface_temperature_K": 360.0,
            "included_wetness_state_ids": ("wet",),
            "included_insulation_condition_ids": ("damaged",),
            "definition_basis": "caller-owned inspection program",
            "evidence": (EVIDENCE,),
        },
        "clock_and_coverage_reviewed": True,
        "temperature_measurement_reviewed": True,
        "wetness_state_mapping_reviewed": True,
        "insulation_condition_mapping_reviewed": True,
        "exposure_definition_reviewed": True,
    }
    value.update(updates)
    return UnderInsulationExposureHistory(**value)


def test_classified_duration_and_continuous_run_are_accounted():
    result = under_insulation_exposure_history(payload())
    assert result.status == "computed"
    assert result.values["classified_exposure_duration_s"] == pytest.approx(200.0)
    assert result.values["maximum_continuous_classified_exposure_s"] == pytest.approx(200.0)
    assert result.values["classified_exposure_interval_ids"] == ["i1", "i2"]


def test_gap_invalid_or_review_missing_needs_data_without_bridging():
    rows = (
        interval("i1", 0.0, 100.0),
        interval(
            "missing",
            150.0,
            200.0,
            record_valid=False,
            surface_temperature_K=None,
            wetness_state_id=None,
            insulation_condition_id=None,
            missing_basis="logger unavailable",
        ),
        interval("i3", 200.0, 300.0),
    )
    result = under_insulation_exposure_history(payload(intervals=rows))
    assert result.status == "needs_data"
    assert result.values["missing_interval_duration_s"] == pytest.approx(100.0)
    assert result.values["maximum_continuous_classified_exposure_s"] == pytest.approx(100.0)
    assert (
        under_insulation_exposure_history(payload(wetness_state_mapping_reviewed=False)).status
        == "needs_data"
    )


def test_overlap_and_definition_order_are_rejected():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(intervals=(interval("a", 0.0, 200.0), interval("b", 100.0, 300.0)))
    definition = payload().exposure_definition.model_copy(update={"minimum_surface_temperature_K": 400.0})
    with pytest.raises(ValueError, match="temperature bounds"):
        payload(exposure_definition=definition.model_dump())


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.under_insulation_exposure_history",
            payload(),
            RunContext(asset_id="other", location_id="line-1", time_basis="authored"),
        )
