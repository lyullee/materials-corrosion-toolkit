import pytest

from matintegrity.models.chloride_scc import (
    ChlorideSCCApplicability,
    chloride_scc_applicability,
)

EVIDENCE = {
    "source_id": "caller-chloride-scc",
    "origin": "user_declared",
    "citation": "caller-controlled service and qualification evidence",
}


def evidence_record(**updates):
    values = {
        "evidence_record_id": "evidence-1",
        "test_id": "test-1",
        "specimen_id": "specimen-1",
        "source_group_id": "source-group-1",
        "material_condition_id": "material-1",
        "metallurgy_id": "metallurgy-1",
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def envelope(**updates):
    values = {
        "envelope_id": "scc-envelope-1",
        "material_condition_id": "material-1",
        "metallurgy_id": "metallurgy-1",
        "chloride_unit": "kg/m^3",
        "minimum_chloride_concentration": 0.0,
        "maximum_chloride_concentration": 1.0,
        "minimum_temperature_K": 280.0,
        "maximum_temperature_K": 350.0,
        "minimum_pH": 5.0,
        "maximum_pH": 9.0,
        "oxidizing_basis": "dissolved_oxygen",
        "dissolved_oxygen_unit": "kg/m^3",
        "minimum_dissolved_oxygen_concentration": 0.0,
        "maximum_dissolved_oxygen_concentration": 0.02,
        "supported_applied_stress_descriptors": ("operating-envelope-a",),
        "supported_residual_stress_descriptors": ("as-qualified-weld-a",),
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
        "chloride_concentration": 0.5,
        "chloride_unit": "kg/m^3",
        "temperature_K": 320.0,
        "pH": 7.0,
        "oxidizing_basis": "dissolved_oxygen",
        "dissolved_oxygen_concentration": 0.01,
        "dissolved_oxygen_unit": "kg/m^3",
        "applied_stress_descriptor": "operating-envelope-a",
        "residual_stress_descriptor": "as-qualified-weld-a",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def request(**updates):
    values = {
        "assessment_id": "scc-assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "physical_scope_id": "wetted-region-1",
        "clock_id": "service-clock-1",
        "material_condition_id": "material-1",
        "metallurgy_id": "metallurgy-1",
        "exposures": (exposure(),),
        "qualification_envelope": envelope(),
        "material_and_metallurgy_reviewed": True,
        "concentration_units_reviewed": True,
        "environment_records_reviewed": True,
        "stress_descriptors_reviewed": True,
        "clock_and_duration_reviewed": True,
        "qualification_evidence_reviewed": True,
    }
    values.update(updates)
    return ChlorideSCCApplicability(**values)


def test_reviewed_condition_inside_declared_support_computes():
    result = chloride_scc_applicability(request())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["test_evidence_summary"]["specimen_ids"] == ["specimen-1"]


def test_reviewed_condition_outside_support_is_out_of_scope():
    result = chloride_scc_applicability(request(exposures=(exposure(chloride_concentration=2.0),)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_exposure_ids"] == ["exposure-1"]
    assert result.values["exposure_comparisons"][0]["unsupported_fields"] == ["chloride_concentration"]


def test_unit_identity_invalid_evidence_and_review_mismatch_need_data():
    unit = chloride_scc_applicability(request(exposures=(exposure(chloride_unit="mg/L"),)))
    assert unit.status == "needs_data"
    identity = chloride_scc_applicability(request(metallurgy_id="different"))
    assert identity.status == "needs_data"
    invalid = chloride_scc_applicability(
        request(qualification_envelope=envelope(test_evidence=(evidence_record(record_valid=False),)))
    )
    assert invalid.status == "needs_data"
    assert chloride_scc_applicability(request(stress_descriptors_reviewed=False)).status == "needs_data"


def test_oxidizing_basis_and_clock_contracts_are_strict():
    with pytest.raises(ValueError, match="cannot be mixed"):
        request(exposures=(exposure(oxidizing_state_descriptor="oxidizing"),))
    with pytest.raises(ValueError, match="cannot overlap"):
        request(
            exposures=(
                exposure("e1", start_time_s=0.0, end_time_s=20.0),
                exposure("e2", start_time_s=10.0, end_time_s=30.0),
            )
        )
    with pytest.raises(ValueError, match="chloride envelope"):
        request(qualification_envelope=envelope(minimum_chloride_concentration=2.0))
