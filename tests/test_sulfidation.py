import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.sulfidation import (
    SulfidationApplicabilityEnvelope,
    SulfidationExposureApplicability,
    SulfidationQualificationRecord,
    sulfidation_exposure_applicability,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def record():
    return SulfidationQualificationRecord(
        test_record_id="test-1",
        source_group_id="source-1",
        material_id="alloy-A",
        material_composition_condition_id="solution-treated",
        sulfur_species_id="species-A",
        sulfur_quantity_kind="activity",
        sulfur_quantity_value=0.1,
        sulfur_quantity_unit_token="1",
        sulfur_quantity_basis="caller thermochemical definition",
        temperature_K=700.0,
        pressure_Pa_abs=200000.0,
        flow_descriptor="flow-regime-A",
        deposit_descriptor="deposit-state-A",
        exposure_duration_s=100000.0,
        reported_observation="caller-reported exposure observation",
        evidence=[EVIDENCE],
    )


def envelope(**updates):
    payload = {
        "envelope_id": "envelope-1",
        "material_id": "alloy-A",
        "material_composition_condition_id": "solution-treated",
        "sulfur_species_id": "species-A",
        "sulfur_quantity_kind": "activity",
        "sulfur_quantity_min": 0.05,
        "sulfur_quantity_max": 0.2,
        "sulfur_quantity_unit_token": "1",
        "sulfur_quantity_basis": "caller thermochemical definition",
        "temperature_min_K": 650.0,
        "temperature_max_K": 750.0,
        "pressure_min_Pa_abs": 100000.0,
        "pressure_max_Pa_abs": 500000.0,
        "applicable_flow_descriptors": ["flow-regime-A"],
        "applicable_deposit_descriptors": ["deposit-state-A"],
        "exposure_duration_min_s": 10000.0,
        "exposure_duration_max_s": 200000.0,
        "qualification_test_record_ids": ["test-1"],
        "applicability_basis": "caller qualification matrix",
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return SulfidationApplicabilityEnvelope(**payload)


def request(**updates):
    payload = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "hot-zone-1",
        "material_id": "alloy-A",
        "material_heat_or_lot_id": "heat-1",
        "material_composition_condition_id": "solution-treated",
        "sulfur_species_id": "species-A",
        "sulfur_quantity_kind": "activity",
        "sulfur_quantity_value": 0.1,
        "sulfur_quantity_unit_token": "1",
        "sulfur_quantity_basis": "caller thermochemical definition",
        "temperature_K": 700.0,
        "pressure_Pa_abs": 200000.0,
        "flow_descriptor": "flow-regime-A",
        "deposit_descriptor": "deposit-state-A",
        "exposure_duration_s": 100000.0,
        "qualification_test_records": [record()],
        "candidate_envelopes": [envelope()],
        "material_identity_and_composition_reviewed": True,
        "sulfur_species_quantity_and_basis_reviewed": True,
        "absolute_pressure_and_temperature_reviewed": True,
        "flow_and_deposit_condition_reviewed": True,
        "exposure_duration_reviewed": True,
        "qualification_evidence_and_envelope_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return SulfidationExposureApplicability(**payload)


def test_unique_applicability_match_computes():
    result = sulfidation_exposure_applicability(request())
    assert result.status == "computed"
    assert result.values["selected_envelope_id"] == "envelope-1"


def test_identity_match_outside_reviewed_support_is_out_of_scope():
    result = sulfidation_exposure_applicability(request(temperature_K=800.0))
    assert result.status == "out_of_scope"
    assert result.values["identity_matching_envelope_ids"] == ["envelope-1"]


def test_unmatched_basis_or_missing_review_needs_data():
    unmatched = sulfidation_exposure_applicability(request(sulfur_quantity_basis="different basis"))
    assert unmatched.status == "needs_data"
    unreviewed = sulfidation_exposure_applicability(
        request(qualification_evidence_and_envelope_reviewed=False)
    )
    assert unreviewed.status == "needs_data"


def test_invalid_ranges_and_missing_evidence_links_are_rejected():
    with pytest.raises(ValueError, match="temperature range"):
        envelope(temperature_min_K=800.0)
    with pytest.raises(ValueError, match="must be supplied"):
        request(candidate_envelopes=[envelope(qualification_test_record_ids=["unknown"])])


def test_qualification_record_must_be_within_the_envelope_support():
    mismatched_record = record().model_copy(update={"temperature_K": 900.0})
    result = sulfidation_exposure_applicability(request(qualification_test_records=[mismatched_record]))
    assert result.status == "out_of_scope"
    assert result.values["selected_envelope_id"] is None
    diagnostics = result.values["qualification_record_diagnostics"][0]
    record_diagnostic = diagnostics["qualification_records"]["test-1"]
    assert record_diagnostic["checks"]["temperature_K"] is False
    assert record_diagnostic["source_group_id"] == "source-1"
    assert record_diagnostic["record_sha256"]
    assert record_diagnostic["record_evidence"][0]["source_id"] == "authored"
    assert diagnostics["all_records_within_declared_support"] is False


def test_qualification_record_material_identity_must_match_envelope():
    mismatched_record = record().model_copy(
        update={"material_composition_condition_id": "different-condition"}
    )
    result = sulfidation_exposure_applicability(request(qualification_test_records=[mismatched_record]))
    assert result.status == "out_of_scope"
    checks = result.values["qualification_record_diagnostics"][0]["qualification_records"]["test-1"]
    assert checks["checks"]["material_composition_condition_id"] is False


def test_blank_evidence_identity_is_rejected():
    with pytest.raises(ValueError, match="cannot be blank"):
        SulfidationQualificationRecord.model_validate(record().model_dump() | {"source_group_id": " "})
