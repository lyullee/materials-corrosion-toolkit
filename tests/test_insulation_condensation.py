import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.insulation_condensation import (
    InsulationCondensationExposure,
    InsulationCondensationInterval,
    insulation_condensation_exposure,
)
from matintegrity.thermo import insulation_condensation_inputs_from_coolprop

EVIDENCE = Evidence(source_id="synthetic", origin="synthetic", citation="synthetic focused test")


def interval(identifier, start, end, surface, dew, state="open", valid=True):
    return InsulationCondensationInterval(
        interval_id=identifier,
        start_time_s=start,
        end_time_s=end,
        outer_surface_temperature_K=surface if valid else None,
        ambient_dew_point_temperature_K=dew if valid else None,
        weather_barrier_state_id=state if valid else None,
        record_valid=valid,
        invalid_basis=None if valid else "sensor outage",
        evidence=(EVIDENCE,),
    )


def payload(**updates):
    values = dict(
        assessment_id="case-1",
        asset_id="asset",
        location_id="location",
        insulation_system_id="system-1",
        outer_surface_location_definition="weather-barrier outer surface",
        dew_point_definition="ambient thermodynamic dew point",
        dew_point_provider_state_digest="a" * 64,
        clock_id="clock-1",
        horizon_start_s=0.0,
        horizon_end_s=40.0,
        intervals=(
            interval("a", 0.0, 10.0, 280.0, 281.0),
            interval("b", 10.0, 20.0, 282.0, 281.0),
            interval("c", 20.0, 40.0, 283.0, 281.0, state="sealed"),
        ),
        barrier_states_allowing_external_moisture=("open",),
        temperature_measurement_uncertainty_K=0.6,
        dew_point_uncertainty_K=0.6,
        temperature_and_dew_point_units_reviewed=True,
        surface_location_reviewed=True,
        clock_and_coverage_reviewed=True,
        weather_barrier_mapping_reviewed=True,
        uncertainty_basis_reviewed=True,
        evidence=(EVIDENCE,),
    )
    values.update(updates)
    return InsulationCondensationExposure(**values)


def test_nominal_and_conservative_durations_keep_barrier_mapping():
    result = insulation_condensation_exposure(payload())
    assert result.status == "computed"
    assert result.values["nominal_condensation_possible_duration_s"] == 10.0
    assert result.values["conservative_condensation_possible_duration_s"] == 20.0
    assert result.values["maximum_continuous_conservative_condensation_possible_s"] == 20.0
    assert result.values["conservative_condensation_possible_interval_ids"] == ["a", "b"]


def test_gap_or_invalid_record_stops_complete_result():
    result = insulation_condensation_exposure(
        payload(
            intervals=(interval("a", 0.0, 10.0, 280.0, 281.0), interval("x", 20.0, 40.0, 0, 0, valid=False))
        )
    )
    assert result.status == "needs_data"
    assert result.values["uncovered_duration_s"] == 10.0
    assert result.values["invalid_duration_s"] == 20.0


def test_missing_review_stops_complete_result():
    result = insulation_condensation_exposure(payload(uncertainty_basis_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["uncertainty_basis_reviewed"]


def test_overlapping_intervals_are_rejected():
    with pytest.raises(ValueError, match="non-overlapping"):
        payload(intervals=(interval("a", 0.0, 15.0, 280.0, 281.0), interval("b", 10.0, 40.0, 282.0, 281.0)))


def test_coolprop_adapter_builds_strict_dew_point_intervals():
    pytest.importorskip("CoolProp")

    values = insulation_condensation_inputs_from_coolprop(
        assessment_id="coolprop-case",
        asset_id="asset",
        location_id="location",
        insulation_system_id="system-1",
        outer_surface_location_definition="weather-barrier outer surface",
        clock_id="clock-1",
        time_s=[0.0, 10.0, 20.0],
        outer_surface_temperature_K=[285.0, 295.0],
        ambient_dry_bulb_temperature_K=[293.15, 298.15],
        ambient_relative_humidity_fraction=[0.8, 0.5],
        ambient_pressure_Pa_abs=[101325.0, 101325.0],
        weather_barrier_state_id=["open", "open"],
        barrier_states_allowing_external_moisture=["open"],
        temperature_measurement_uncertainty_K=0.2,
        dew_point_uncertainty_K=0.3,
        evidence=[EVIDENCE],
    )
    model = InsulationCondensationExposure.model_validate(values)
    assert len(model.dew_point_provider_state_digest) == 64
    assert model.intervals[0].ambient_dew_point_temperature_K < 293.15
