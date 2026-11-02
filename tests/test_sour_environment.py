import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.sour_environment import (
    SourApplicabilityEnvelope,
    SourEnvironmentApplicability,
    SourEnvironmentTestRecord,
    sour_environment_applicability,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def record(identifier, partition, group):
    return SourEnvironmentTestRecord(
        test_record_id=identifier,
        source_group_id=group,
        partition=partition,
        material_grade_id="steel-A",
        material_heat_id="heat-1",
        microstructure_id="tempered",
        hardness_value=220.0,
        hardness_unit_token="HV",
        h2s_partial_pressure_Pa_abs=10000.0,
        h2s_partial_pressure_basis="gas-phase partial pressure from reviewed composition",
        pH=4.0,
        temperature_K=300.0,
        chloride_concentration=3.0,
        chloride_unit_token="mass_percent",
        exposure_duration_s=100000.0,
        stress_state_descriptor="constant-tensile",
        reported_outcome="caller-reported test outcome",
        evidence=[EVIDENCE],
    )


def envelope(**updates):
    payload = {
        "envelope_id": "sour-envelope-1",
        "material_grade_id": "steel-A",
        "heat_applicability": "exact_heats",
        "applicable_heat_ids": ["heat-1"],
        "applicable_microstructure_ids": ["tempered"],
        "hardness_min": 180.0,
        "hardness_max": 250.0,
        "hardness_unit_token": "HV",
        "h2s_partial_pressure_min_Pa_abs": 1000.0,
        "h2s_partial_pressure_max_Pa_abs": 20000.0,
        "h2s_partial_pressure_basis": "gas-phase partial pressure from reviewed composition",
        "pH_min": 3.0,
        "pH_max": 5.0,
        "temperature_min_K": 280.0,
        "temperature_max_K": 330.0,
        "chloride_min": 0.0,
        "chloride_max": 5.0,
        "chloride_unit_token": "mass_percent",
        "exposure_duration_min_s": 1000.0,
        "exposure_duration_max_s": 200000.0,
        "applicable_stress_state_descriptors": ["constant-tensile"],
        "qualification_test_record_ids": ["cal-1"],
        "applicability_basis": "caller-declared test matrix envelope",
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return SourApplicabilityEnvelope(**payload)


def request(**updates):
    payload = {
        "assessment_id": "sour-assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "material_grade_id": "steel-A",
        "material_heat_id": "heat-1",
        "microstructure_id": "tempered",
        "hardness_value": 220.0,
        "hardness_unit_token": "HV",
        "h2s_partial_pressure_Pa_abs": 10000.0,
        "h2s_partial_pressure_basis": "gas-phase partial pressure from reviewed composition",
        "pH": 4.0,
        "temperature_K": 300.0,
        "chloride_concentration": 3.0,
        "chloride_unit_token": "mass_percent",
        "exposure_duration_s": 100000.0,
        "stress_state_descriptor": "constant-tensile",
        "test_records": [
            record("cal-1", "calibration", "group-cal"),
            record("hold-1", "holdout", "group-hold"),
        ],
        "candidate_envelopes": [envelope()],
        "material_identity_and_hardness_reviewed": True,
        "media_composition_and_pH_reviewed": True,
        "absolute_partial_pressure_reviewed": True,
        "temperature_and_exposure_reviewed": True,
        "stress_state_reviewed": True,
        "test_partition_independence_reviewed": True,
        "envelope_authority_reviewed": True,
        "heat_transfer_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return SourEnvironmentApplicability(**payload)


def test_unique_service_point_match_preserves_test_partitions():
    result = sour_environment_applicability(request())
    assert result.status == "computed"
    assert result.values["selected_envelope_id"] == "sour-envelope-1"
    assert result.values["test_record_count_by_partition"] == {"calibration": 1, "holdout": 1}


def test_identity_match_outside_range_is_out_of_scope():
    result = sour_environment_applicability(request(pH=6.0))
    assert result.status == "out_of_scope"
    assert result.values["identity_matching_envelope_ids"] == ["sour-envelope-1"]


def test_unmatched_definition_or_missing_review_needs_data():
    unmatched = sour_environment_applicability(request(h2s_partial_pressure_basis="different basis"))
    assert unmatched.status == "needs_data"
    unreviewed = sour_environment_applicability(request(absolute_partial_pressure_reviewed=False))
    assert unreviewed.status == "needs_data"


def test_source_leakage_and_holdout_defined_envelope_are_rejected():
    with pytest.raises(ValueError, match="cannot cross"):
        request(test_records=[record("cal-1", "calibration", "same"), record("hold-1", "holdout", "same")])
    with pytest.raises(ValueError, match="Only calibration|only calibration"):
        request(candidate_envelopes=[envelope(qualification_test_record_ids=["hold-1"])])
