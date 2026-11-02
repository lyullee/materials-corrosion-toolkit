import pytest
from pydantic import ValidationError

from matintegrity.wall_tolerances import (
    WallThicknessReplicate,
    WallToleranceCallerProfile,
    assess_wall_tolerances,
    wall_tolerance_assessment,
)

E = {"source_id": "caller", "origin": "measured", "citation": "caller thickness campaign"}
D = "1" * 64


def profile(lower=1.0, upper=2.0):
    return WallToleranceCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        product_id="product-1",
        product_form_id="pipe",
        region_id="region-1",
        nominal_thickness=10.0,
        thickness_unit_token="mm",
        lower_tolerance_from_nominal=lower,
        upper_tolerance_from_nominal=upper,
        forming_allowance=0.5,
        corrosion_allowance=1.0,
        profile_basis="caller-defined product tolerance profile",
        profile_source_digest=D,
        evidence=(E,),
    )


def replicate(rid="r1", value=10.0, uncertainty=0.1, status="reported", unit="mm"):
    return WallThicknessReplicate(
        replicate_id=rid,
        status=status,
        measured_thickness=value if status == "reported" else None,
        expanded_uncertainty=uncertainty if status == "reported" else None,
        unit_token=unit,
        measurement_location_id=f"point-{rid}",
        method_id="ut-1",
        instrument_id="instrument-1",
        measurement_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not available",
        evidence=(E,),
    )


def assessment(replicates=None, caller_profile=None, **updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "component_id": "component-1",
        "location_id": "location-1",
        "product_id": "product-1",
        "product_form_id": "pipe",
        "region_id": "region-1",
        "nominal_thickness": 10.0,
        "thickness_unit_token": "mm",
        "forming_allowance": 0.5,
        "corrosion_allowance": 1.0,
        "replicates": replicates or (replicate(),),
        "caller_profile": caller_profile or profile(),
        "product_region_nominal_and_units_reviewed": True,
        "allowances_and_nonapplication_policy_reviewed": True,
        "replicate_methods_uncertainties_and_provenance_reviewed": True,
        "caller_profile_and_missing_evidence_policy_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return wall_tolerance_assessment(**value)


def test_asymmetric_band_accepts_and_preserves_allowances_separately():
    result = assess_wall_tolerances(assessment())
    assert result.decision == "accept"
    assert (result.lower_tolerance_limit, result.upper_tolerance_limit) == (9.0, 12.0)
    assert (result.forming_allowance_recorded, result.corrosion_allowance_recorded) == (0.5, 1.0)
    assert result.allowances_applied_to_tolerance_decision is False
    assert result.specification_qualification_claim is False
    assert result.design_adequacy_claim is False
    assert result == assess_wall_tolerances(assessment())


def test_reject_review_and_insufficient_are_distinct():
    rejected = assess_wall_tolerances(assessment(replicates=(replicate(value=8.0),)))
    reviewed = assess_wall_tolerances(assessment(replicates=(replicate(value=9.05, uncertainty=0.1),)))
    missing = assess_wall_tolerances(assessment(replicates=(replicate(status="missing"),)))
    wrong_unit = assess_wall_tolerances(assessment(replicates=(replicate(unit="inch"),)))
    assert (rejected.decision, reviewed.decision) == ("reject", "review")
    assert missing.decision == wrong_unit.decision == "insufficient_evidence"


def test_conservative_summary_uses_lowest_reported_uncertainty_bound():
    result = assess_wall_tolerances(
        assessment(replicates=(replicate("a", 10.0, 0.2), replicate("b", 9.5, 0.1)))
    )
    assert result.conservative_reported_lower_bound == pytest.approx(9.4)


def test_input_and_report_tampering_are_rejected():
    item = assessment()
    changed = item.model_dump(mode="python")
    changed["component_id"] = "other"
    with pytest.raises(ValidationError, match="payload digest mismatch"):
        item.model_validate(changed)
    report = assess_wall_tolerances(item)
    changed_report = report.model_dump(mode="python")
    changed_report["decision"] = "review"
    with pytest.raises(ValidationError, match="report digest mismatch"):
        report.model_validate(changed_report)
