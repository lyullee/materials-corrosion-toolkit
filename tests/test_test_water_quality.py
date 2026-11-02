import pytest

from matintegrity.models.test_water_quality import TestWaterQualityRecord as WaterQualityRecord
from matintegrity.models.test_water_quality import test_water_quality as evaluate_water_quality

EVIDENCE = {
    "source_id": "caller-test-water",
    "origin": "measured",
    "citation": "caller-controlled laboratory and sampling record",
}


def sample(identifier, location, time_s, **updates):
    values = {
        "sample_id": identifier,
        "location_id": location,
        "sample_time_s": time_s,
        "temperature_K": 295.0,
        "pH": 7.0,
        "conductivity_S_m": 0.02,
        "chloride_kg_m3": 0.01,
        "measurement_method_id": "caller-method-1",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def envelope(**updates):
    values = {
        "envelope_id": "caller-envelope",
        "material_condition_id": "material-1",
        "minimum_temperature_K": 280.0,
        "maximum_temperature_K": 310.0,
        "minimum_pH": 6.0,
        "maximum_pH": 8.0,
        "minimum_conductivity_S_m": 0.0,
        "maximum_conductivity_S_m": 0.05,
        "minimum_chloride_kg_m3": 0.0,
        "maximum_chloride_kg_m3": 0.02,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def record(**updates):
    values = {
        "record_id": "water-record-1",
        "test_id": "hydrotest-1",
        "asset_id": "asset-1",
        "material_condition_id": "material-1",
        "clock_id": "test-clock-1",
        "test_start_time_s": 0.0,
        "test_end_time_s": 100.0,
        "required_location_ids": ("inlet", "outlet"),
        "maximum_sampling_gap_s": 50.0,
        "samples": (
            sample("i1", "inlet", 25.0),
            sample("i2", "inlet", 75.0),
            sample("o1", "outlet", 25.0),
            sample("o2", "outlet", 75.0),
        ),
        "envelope": envelope(),
        "sampling_plan_reviewed": True,
        "sample_identity_and_location_reviewed": True,
        "clock_and_units_reviewed": True,
        "measurement_methods_reviewed": True,
        "material_envelope_reviewed": True,
        "record_completeness_reviewed": True,
    }
    values.update(updates)
    return WaterQualityRecord(**values)


def test_complete_record_reports_coverage_and_ranges():
    result = evaluate_water_quality(record())
    assert result.status == "computed"
    assert result.values["declared_envelope_outcome"] == "within"
    assert result.values["observed_pH_range"] == [7.0, 7.0]
    assert all(row["coverage_sufficient"] for row in result.values["coverage"])


def test_outside_observation_is_preserved_without_acceptance_claim():
    samples = list(record().samples)
    samples[-1] = sample("o2", "outlet", 75.0, chloride_kg_m3=0.03)
    result = evaluate_water_quality(record(samples=tuple(samples)))
    assert result.values["declared_envelope_outcome"] == "outside"
    assert result.values["violating_sample_ids"] == ["o2"]
    assert result.values["sample_comparisons"][-1]["violations"] == ["chloride"]


def test_missing_location_gap_invalid_sample_or_review_needs_data():
    missing = evaluate_water_quality(
        record(samples=(sample("i1", "inlet", 25.0), sample("i2", "inlet", 75.0)))
    )
    assert missing.status == "needs_data"
    sparse = evaluate_water_quality(
        record(
            maximum_sampling_gap_s=20.0,
        )
    )
    assert sparse.status == "needs_data"
    invalid = evaluate_water_quality(
        record(
            samples=(
                sample("i1", "inlet", 25.0, record_valid=False),
                sample("i2", "inlet", 75.0),
                sample("o1", "outlet", 25.0),
                sample("o2", "outlet", 75.0),
            )
        )
    )
    assert invalid.status == "needs_data"
    assert evaluate_water_quality(record(clock_and_units_reviewed=False)).status == "needs_data"


def test_identity_clock_and_envelope_contracts_are_strict():
    with pytest.raises(ValueError, match="inside the declared test interval"):
        record(samples=(sample("i1", "inlet", 101.0),))
    with pytest.raises(ValueError, match="tested material condition"):
        record(envelope=envelope(material_condition_id="different"))
    with pytest.raises(ValueError, match="chloride envelope"):
        record(envelope=envelope(minimum_chloride_kg_m3=0.1))
