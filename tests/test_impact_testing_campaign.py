import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.impact_testing_campaign import (
    ImpactCampaignCallerProfile,
    ImpactMachineConfiguration,
    ImpactMetricCriterion,
    ImpactReportedResult,
    ImpactSpecimenIdentity,
    ImpactTestingCampaign,
    ImpactTestRecord,
    impact_testing_campaign,
    specifications,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller impact data"}
D = "2" * 64


def specimen(sid):
    return ImpactSpecimenIdentity(
        specimen_id=sid,
        product_id="product-1",
        heat_id="heat-1",
        material_condition_id="condition-1",
        orientation_id="orientation-1",
        notch_id="notch-1",
        notch_definition="caller notch identity",
        size_id="size-1",
        thickness=10.0,
        width=10.0,
        length=55.0,
        dimension_unit_token="mm",
        specimen_record_digest=D,
        evidence=(E,),
    )


def result(value=50.0, status="reported"):
    return ImpactReportedResult(
        result_id="energy-result",
        metric="absorbed_energy",
        metric_definition="reported machine absorbed energy",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=2.0 if status == "reported" else None,
        unit_token="J",
        result_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not reported",
        evidence=(E,),
    )


def impact_test_record(tid, sid, value=50.0, status="reported", independence="ind-1"):
    return ImpactTestRecord(
        test_id=tid,
        specimen_id=sid,
        test_temperature=250.0,
        expanded_temperature_uncertainty=1.0,
        replicate_group_id="rep-250K",
        source_group_id=f"source-{tid}",
        independence_group_id=independence,
        sequence_index=int(tid[-1]),
        results=(result(value, status),),
        caller_validity_status="valid",
        caller_validity_basis="caller reviewed record",
        test_record_digest=D,
        evidence=(E,),
    )


def profile(minimum=40.0):
    return ImpactCampaignCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        product_id="product-1",
        heat_id="heat-1",
        material_condition_id="condition-1",
        orientation_id="orientation-1",
        notch_id="notch-1",
        size_id="size-1",
        specimen_dimension_unit_token="mm",
        minimum_test_temperature_K=240.0,
        maximum_test_temperature_K=260.0,
        required_metrics=("absorbed_energy",),
        metric_criteria=(
            ImpactMetricCriterion(
                criterion_id="energy-rule",
                metric="absorbed_energy",
                unit_token="J",
                minimum_acceptable=minimum,
                criterion_basis="caller energy criterion",
                evidence=(E,),
            ),
        ),
        minimum_valid_replicates_per_exact_temperature=2,
        minimum_independence_group_count=2,
        required_machine_id="machine-1",
        required_striker_id="striker-1",
        required_calibration_id="cal-1",
        caller_validity_policy_id="caller-validity-1",
        profile_source_digest=D,
        evidence=(E,),
    )


def payload(caller_profile=None, tests=None, **updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "specimens": (specimen("s1"), specimen("s2")),
        "machine": ImpactMachineConfiguration(
            machine_id="machine-1",
            machine_revision="1",
            striker_id="striker-1",
            striker_definition="caller striker identity",
            striker_radius=2.0,
            striker_radius_unit_token="mm",
            machine_capacity=300.0,
            machine_capacity_unit_token="J",
            calibration_id="cal-1",
            calibration_revision="1",
            calibration_status="valid",
            calibration_record_digest=D,
            evidence=(E,),
        ),
        "tests": tests
        or (
            impact_test_record("t1", "s1", independence="ind-1"),
            impact_test_record("t2", "s2", independence="ind-2"),
        ),
        "caller_profile": caller_profile or profile(),
        "specimen_product_heat_orientation_notch_and_size_reviewed": True,
        "temperature_results_units_and_uncertainties_reviewed": True,
        "machine_striker_and_calibration_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "caller_validity_flags_and_profile_reviewed": True,
        "provenance_and_record_digests_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return ImpactTestingCampaign(**value)


def test_campaign_accept_reject_review_are_caller_driven():
    accepted = impact_testing_campaign(payload())
    rejected = impact_testing_campaign(payload(caller_profile=profile(60.0)))
    reviewed = impact_testing_campaign(payload(caller_profile=profile(51.0)))
    assert accepted.values["quality_outcome"] == "accept"
    assert rejected.values["quality_outcome"] == "reject"
    assert reviewed.values["quality_outcome"] == "review"
    assert accepted.values["transition_fit_performed"] is False
    assert accepted.values["temperature_correction_applied"] is False
    assert accepted.values["design_acceptance_claim"] is False


def test_missing_result_or_independence_is_insufficient():
    missing_tests = (
        impact_test_record("t1", "s1", status="missing", independence="ind-1"),
        impact_test_record("t2", "s2", independence="ind-2"),
    )
    assert impact_testing_campaign(payload(tests=missing_tests)).status == "needs_data"
    same_group = (
        impact_test_record("t1", "s1", independence="same"),
        impact_test_record("t2", "s2", independence="same"),
    )
    assert impact_testing_campaign(payload(tests=same_group)).values["quality_outcome"] == (
        "insufficient_evidence"
    )


def test_specification_is_local_and_has_authored_source_id():
    spec = specifications()[0]
    assert spec.model_id == "inspection.impact_testing_campaign"
    assert spec.input_type is ImpactTestingCampaign
    assert spec.source_ids == ("authored_impact_testing_campaign_evidence_audit",)
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign")
    spec.context_validator(payload(), context)


@pytest.mark.parametrize("groups", [("ind-1", "ind-2"), ("same", "same")])
def test_one_physical_specimen_cannot_be_recounted_as_impact_replicates(groups):
    repeated = (
        impact_test_record("t1", "s1", independence=groups[0]),
        impact_test_record("t2", "s1", independence=groups[1]),
    )
    with pytest.raises(ValueError, match="one impact test per physical specimen"):
        payload(tests=repeated)
