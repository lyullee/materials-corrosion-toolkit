import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.polymer_compatibility import (
    PolymerCompatibilityAssessment,
    PolymerCompatibilityEnvelope,
    polymer_compatibility_envelope_match,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def envelope(**updates):
    payload = {
        "envelope_id": "qualified-envelope-1",
        "polymer_grade_id": "PTFE-grade-A",
        "polymer_condition_id": "as-molded",
        "lot_applicability": "exact_lots",
        "applicable_lot_ids": ["lot-1"],
        "media_id": "authored-medium",
        "concentration_min": 5.0,
        "concentration_max": 15.0,
        "concentration_unit_token": "mass_percent",
        "temperature_min_K": 280.0,
        "temperature_max_K": 350.0,
        "pressure_min_Pa_abs": 90000.0,
        "pressure_max_Pa_abs": 500000.0,
        "maximum_exposure_duration_s": 1000000.0,
        "applicable_mechanical_loading_descriptors": ["static-seal-compression"],
        "qualification_source_id": "caller-study-1",
        "applicability_basis": "caller-qualified exposure matrix",
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return PolymerCompatibilityEnvelope(**payload)


def request(**updates):
    payload = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "seal-1",
        "polymer_grade_id": "PTFE-grade-A",
        "polymer_lot_id": "lot-1",
        "polymer_condition_id": "as-molded",
        "media_id": "authored-medium",
        "media_composition_description": "single authored solute in water",
        "concentration": 10.0,
        "concentration_unit_token": "mass_percent",
        "temperature_K": 320.0,
        "pressure_Pa_abs": 200000.0,
        "exposure_duration_s": 100000.0,
        "mechanical_loading_descriptor": "static-seal-compression",
        "candidate_envelopes": [envelope()],
        "material_identity_reviewed": True,
        "media_identity_and_concentration_reviewed": True,
        "temperature_pressure_duration_reviewed": True,
        "mechanical_loading_reviewed": True,
        "envelope_authority_reviewed": True,
        "lot_transfer_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return PolymerCompatibilityAssessment(**payload)


def test_unique_exact_identity_and_range_match_computes():
    result = polymer_compatibility_envelope_match(request())
    assert result.status == "computed"
    assert result.values["selected_envelope_id"] == "qualified-envelope-1"
    assert result.values["candidate_diagnostics"][0]["within_declared_ranges"] is True


def test_identity_match_outside_range_is_out_of_scope():
    result = polymer_compatibility_envelope_match(request(temperature_K=360.0))
    assert result.status == "out_of_scope"
    assert result.values["identity_matching_envelope_ids"] == ["qualified-envelope-1"]
    assert result.values["selected_envelope_id"] is None


def test_unmatched_identity_or_missing_review_needs_data():
    unmatched = polymer_compatibility_envelope_match(request(concentration_unit_token="volume_percent"))
    assert unmatched.status == "needs_data"
    assert unmatched.values["identity_matching_envelope_ids"] == []
    unreviewed = polymer_compatibility_envelope_match(request(envelope_authority_reviewed=False))
    assert unreviewed.status == "needs_data"


def test_invalid_envelope_ranges_and_lot_scope_are_rejected():
    with pytest.raises(ValueError, match="temperature range"):
        envelope(temperature_min_K=360.0)
    with pytest.raises(ValueError, match="at least one lot"):
        envelope(applicable_lot_ids=[])
