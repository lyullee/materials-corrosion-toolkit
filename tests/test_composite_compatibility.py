import pytest

from matintegrity.models.composite_compatibility import (
    CompositeCompatibility,
    composite_compatibility,
)

EVIDENCE = {
    "source_id": "caller-composite-record",
    "origin": "user_declared",
    "citation": "caller-controlled exposure and coupon qualification record",
}
IDENTITY = {
    "laminate_system_id": "laminate-a",
    "resin_system_id": "resin-a",
    "fiber_system_id": "fiber-a",
    "manufacturing_condition_id": "cure-cycle-a",
    "layup_id": "layup-a",
    "environment_id": "service-fluid-a",
}


def qualification(identifier, partition, group, **updates):
    values = {
        "record_id": identifier,
        "coupon_id": f"coupon-{identifier}",
        "source_group_id": group,
        "partition": partition,
        **IDENTITY,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def exposure(identifier, start, end, **updates):
    values = {
        "exposure_id": identifier,
        "start_time_s": start,
        "end_time_s": end,
        "temperature_K": 320.0,
        "moisture_mass_fraction": 0.02,
        "pressure_Pa_abs": 2e5,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def envelope(**updates):
    values = {
        "envelope_id": "qualification-a",
        **IDENTITY,
        "minimum_temperature_K": 280.0,
        "maximum_temperature_K": 350.0,
        "minimum_moisture_mass_fraction": 0.0,
        "maximum_moisture_mass_fraction": 0.05,
        "minimum_pressure_Pa_abs": 1e5,
        "maximum_pressure_Pa_abs": 5e5,
        "maximum_cumulative_exposure_s": 3000.0,
        "qualification_records": (
            qualification("cal-1", "calibration", "group-cal"),
            qualification("hold-1", "holdout", "group-hold"),
        ),
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def request(**updates):
    values = {
        "assessment_id": "composite-assessment-1",
        "asset_id": "asset-1",
        "location_id": "shell-course-1",
        "physical_scope_id": "laminate-region-1",
        "clock_id": "service-clock-1",
        **IDENTITY,
        "exposures": (exposure("e1", 0.0, 1000.0), exposure("e2", 1200.0, 2200.0)),
        "qualification_envelope": envelope(),
        "material_and_layup_identity_reviewed": True,
        "manufacturing_condition_reviewed": True,
        "environment_and_clock_reviewed": True,
        "exposure_records_reviewed": True,
        "qualification_evidence_reviewed": True,
        "calibration_holdout_partition_reviewed": True,
    }
    values.update(updates)
    return CompositeCompatibility(**values)


def test_exact_identity_and_separated_evidence_compute():
    result = composite_compatibility(request())
    assert result.status == "computed"
    assert result.values["declared_compatibility_outcome"] == "within"
    assert result.values["cumulative_exposure_s"] == 2000.0
    assert result.values["qualification_evidence_summary"]["holdout"]["coupon_ids"] == ["coupon-hold-1"]


def test_state_or_duration_outside_envelope_is_visible():
    result = composite_compatibility(
        request(
            exposures=(
                exposure("e1", 0.0, 2000.0, temperature_K=360.0),
                exposure("e2", 2000.0, 4000.0),
            )
        )
    )
    assert result.values["declared_compatibility_outcome"] == "outside"
    assert result.values["violating_exposure_ids"] == ["e1"]
    assert not result.values["cumulative_exposure_within_envelope"]


def test_identity_invalid_record_partition_leakage_and_review_need_data():
    mismatch = composite_compatibility(request(resin_system_id="different"))
    assert mismatch.status == "needs_data"
    invalid = composite_compatibility(request(exposures=(exposure("e1", 0.0, 10.0, record_valid=False),)))
    assert invalid.status == "needs_data"
    leaking = envelope(
        qualification_records=(
            qualification("cal-1", "calibration", "same-group"),
            qualification("hold-1", "holdout", "same-group"),
        )
    )
    assert composite_compatibility(request(qualification_envelope=leaking)).status == "needs_data"
    assert composite_compatibility(request(exposure_records_reviewed=False)).status == "needs_data"


def test_exposure_clock_and_envelope_ranges_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        request(exposures=(exposure("e1", 0.0, 20.0), exposure("e2", 10.0, 30.0)))
    with pytest.raises(ValueError, match="moisture envelope"):
        request(qualification_envelope=envelope(minimum_moisture_mass_fraction=0.1))
