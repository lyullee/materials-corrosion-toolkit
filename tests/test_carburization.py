import pytest

from matintegrity.models.carburization import (
    CarburizationApplicability,
    carburization_applicability,
)

EVIDENCE = {
    "source_id": "caller-carburization",
    "origin": "user_declared",
    "citation": "caller-controlled exposure and qualification evidence",
}
IDENTITY = {"material_condition_id": "material-1", "alloy_condition_id": "alloy-state-1"}


def evidence_record(**updates):
    values = {
        "evidence_record_id": "evidence-1",
        "test_id": "test-1",
        "specimen_id": "specimen-1",
        "source_group_id": "group-1",
        **IDENTITY,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def envelope(**updates):
    values = {
        "envelope_id": "carburization-envelope-1",
        **IDENTITY,
        "carbon_basis": "carbon_activity",
        "carbon_unit": "1",
        "minimum_carbon_value": 0.0,
        "maximum_carbon_value": 1.0,
        "minimum_temperature_K": 800.0,
        "maximum_temperature_K": 1200.0,
        "minimum_pressure_Pa_abs": 1e5,
        "maximum_pressure_Pa_abs": 5e5,
        "supported_gas_composition_descriptors": ("gas-profile-a",),
        "maximum_cumulative_exposure_s": 2000.0,
        "test_evidence": (evidence_record(),),
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def exposure(identifier="exposure-1", **updates):
    values = {
        "exposure_id": identifier,
        "start_time_s": 0.0,
        "end_time_s": 1000.0,
        "carbon_basis": "carbon_activity",
        "carbon_value": 0.5,
        "carbon_unit": "1",
        "temperature_K": 1000.0,
        "pressure_Pa_abs": 2e5,
        "gas_composition_descriptor": "gas-profile-a",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def request(**updates):
    values = {
        "assessment_id": "carburization-1",
        "asset_id": "asset-1",
        "location_id": "hot-zone-1",
        "physical_scope_id": "surface-region-1",
        "clock_id": "service-clock-1",
        **IDENTITY,
        "exposures": (exposure(),),
        "qualification_envelope": envelope(),
        "material_and_alloy_condition_reviewed": True,
        "carbon_basis_and_units_reviewed": True,
        "temperature_pressure_and_gas_reviewed": True,
        "clock_and_duration_reviewed": True,
        "qualification_evidence_reviewed": True,
    }
    values.update(updates)
    return CarburizationApplicability(**values)


def test_inside_declared_support_computes():
    result = carburization_applicability(request())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["test_evidence_summary"]["specimen_ids"] == ["specimen-1"]


def test_reviewed_outside_state_is_out_of_scope():
    result = carburization_applicability(
        request(exposures=(exposure(gas_composition_descriptor="different"),))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_exposure_ids"] == ["exposure-1"]
    assert result.values["exposure_comparisons"][0]["unsupported_fields"] == ["gas_composition_descriptor"]


def test_basis_unit_identity_invalid_evidence_and_review_need_data():
    assert (
        carburization_applicability(
            request(exposures=(exposure(carbon_basis="carburizing_potential"),))
        ).status
        == "needs_data"
    )
    assert carburization_applicability(request(alloy_condition_id="different")).status == "needs_data"
    invalid = carburization_applicability(
        request(qualification_envelope=envelope(test_evidence=(evidence_record(record_valid=False),)))
    )
    assert invalid.status == "needs_data"
    assert carburization_applicability(request(carbon_basis_and_units_reviewed=False)).status == "needs_data"


def test_clock_and_envelope_contracts_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        request(
            exposures=(
                exposure("e1", start_time_s=0.0, end_time_s=20.0),
                exposure("e2", start_time_s=10.0, end_time_s=30.0),
            )
        )
    with pytest.raises(ValueError, match="carbon envelope"):
        request(qualification_envelope=envelope(minimum_carbon_value=2.0))
