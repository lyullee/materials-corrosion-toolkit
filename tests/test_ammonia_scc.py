import pytest

from matintegrity.models.ammonia_scc import (
    AmmoniaSCCApplicability,
    ammonia_scc_applicability,
)

EVIDENCE = {
    "source_id": "caller-ammonia-scc",
    "origin": "user_declared",
    "citation": "caller-controlled service and qualification evidence",
}
IDENTITY = {
    "material_condition_id": "material-1",
    "metallurgy_id": "metallurgy-1",
    "heat_treatment_id": "heat-treatment-1",
}


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
        "envelope_id": "ammonia-envelope-1",
        **IDENTITY,
        "supported_ammonia_phases": ("liquid",),
        "ammonia_concentration_unit": "mass_fraction",
        "minimum_ammonia_concentration": 0.8,
        "maximum_ammonia_concentration": 1.0,
        "supported_water_state_descriptors": ("water-band-a",),
        "supported_oxygen_state_descriptors": ("oxygen-band-a",),
        "supported_impurity_state_descriptors": ("impurity-profile-a",),
        "minimum_temperature_K": 250.0,
        "maximum_temperature_K": 330.0,
        "supported_applied_stress_descriptors": ("operating-stress-a",),
        "supported_residual_stress_descriptors": ("fabrication-state-a",),
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
        "ammonia_phase": "liquid",
        "ammonia_concentration": 0.95,
        "ammonia_concentration_unit": "mass_fraction",
        "water_state_descriptor": "water-band-a",
        "oxygen_state_descriptor": "oxygen-band-a",
        "impurity_state_descriptor": "impurity-profile-a",
        "temperature_K": 290.0,
        "applied_stress_descriptor": "operating-stress-a",
        "residual_stress_descriptor": "fabrication-state-a",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def request(**updates):
    values = {
        "assessment_id": "ammonia-scc-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "physical_scope_id": "wetted-scope-1",
        "clock_id": "service-clock-1",
        **IDENTITY,
        "exposures": (exposure(),),
        "qualification_envelope": envelope(),
        "material_metallurgy_and_heat_treatment_reviewed": True,
        "ammonia_phase_concentration_and_units_reviewed": True,
        "water_oxygen_and_impurity_states_reviewed": True,
        "stress_descriptors_reviewed": True,
        "clock_and_duration_reviewed": True,
        "qualification_evidence_reviewed": True,
    }
    values.update(updates)
    return AmmoniaSCCApplicability(**values)


def test_inside_caller_support_computes_without_scc_claim():
    result = ammonia_scc_applicability(request())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["test_evidence_summary"]["specimen_ids"] == ["specimen-1"]


def test_reviewed_unsupported_descriptor_is_out_of_scope():
    result = ammonia_scc_applicability(request(exposures=(exposure(water_state_descriptor="different"),)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_exposure_ids"] == ["exposure-1"]
    assert result.values["exposure_comparisons"][0]["unsupported_fields"] == ["water_state_descriptor"]


def test_unit_identity_invalid_evidence_and_review_need_data():
    unit = ammonia_scc_applicability(request(exposures=(exposure(ammonia_concentration_unit="kg/m^3"),)))
    assert unit.status == "needs_data"
    assert ammonia_scc_applicability(request(metallurgy_id="different")).status == "needs_data"
    invalid = ammonia_scc_applicability(
        request(qualification_envelope=envelope(test_evidence=(evidence_record(record_valid=False),)))
    )
    assert invalid.status == "needs_data"
    assert ammonia_scc_applicability(request(stress_descriptors_reviewed=False)).status == "needs_data"


def test_clock_and_envelope_contracts_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        request(
            exposures=(
                exposure("e1", start_time_s=0.0, end_time_s=20.0),
                exposure("e2", start_time_s=10.0, end_time_s=30.0),
            )
        )
    with pytest.raises(ValueError, match="concentration envelope"):
        request(qualification_envelope=envelope(minimum_ammonia_concentration=1.1))
