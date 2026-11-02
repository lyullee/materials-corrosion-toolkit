from matintegrity.contracts import RunContext
from matintegrity.models.tensile_offset_yield_campaign import (
    TensileCampaignCallerProfile,
    TensileMachineConfiguration,
    TensileMetricCriterion,
    TensileOffsetYieldCampaign,
    TensileReportedResult,
    TensileSpecimenIdentity,
    TensileTestRecord,
    specifications,
    tensile_offset_yield_campaign,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller tensile data"}
D = "4" * 64


def reported(value=300e6, status="reported"):
    return TensileReportedResult(
        result_id="yield-result",
        metric="offset_yield_strength",
        metric_definition="reported caller offset yield",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=5e6 if status == "reported" else None,
        unit_token="Pa",
        result_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not reported",
        evidence=(E,),
    )


def tensile_test(tid, sid, value=300e6, status="reported", independence="ind-1"):
    return TensileTestRecord(
        test_id=tid,
        specimen_id=sid,
        sequence_index=int(tid[-1]),
        test_temperature_K=300.0,
        expanded_temperature_uncertainty_K=1.0,
        strain_rate_per_s=0.001,
        expanded_strain_rate_uncertainty_per_s=0.0001,
        offset_definition_id="offset-0.2-percent",
        offset_strain=0.002,
        raw_curve_digest=D,
        result_set_digest=D,
        results=(reported(value, status),),
        replicate_group_id="rep-1",
        source_group_id=f"source-{tid}",
        independence_group_id=independence,
        caller_validity_status="valid",
        caller_validity_basis="caller validity review",
        evidence=(E,),
    )


def profile(minimum=250e6):
    return TensileCampaignCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        product_id="product-1",
        heat_id="heat-1",
        material_condition_id="condition-1",
        supported_orientation_ids=("longitudinal",),
        supported_geometry_ids=("round-1",),
        geometry_unit_token="mm",
        area_unit_token="mm^2",
        required_machine_id="machine-1",
        required_load_cell_id="load-cell-1",
        required_extensometer_id="extenso-1",
        minimum_temperature_K=290.0,
        maximum_temperature_K=310.0,
        minimum_strain_rate_per_s=0.0005,
        maximum_strain_rate_per_s=0.002,
        required_offset_definition_id="offset-0.2-percent",
        required_offset_strain=0.002,
        offset_strain_tolerance=0.0,
        required_metrics=("offset_yield_strength",),
        metric_criteria=(
            TensileMetricCriterion(
                criterion_id="yield-rule",
                metric="offset_yield_strength",
                unit_token="Pa",
                minimum_acceptable=minimum,
                criterion_basis="caller yield criterion",
                evidence=(E,),
            ),
        ),
        minimum_valid_test_count=2,
        minimum_independence_group_count=2,
        caller_validity_policy_id="caller-validity-1",
        profile_source_digest=D,
        evidence=(E,),
    )


def specimen(sid):
    return TensileSpecimenIdentity(
        specimen_id=sid,
        product_id="product-1",
        heat_id="heat-1",
        material_condition_id="condition-1",
        orientation_id="longitudinal",
        geometry_id="round-1",
        initial_gauge_length=50.0,
        initial_cross_section_area=20.0,
        geometry_unit_token="mm",
        area_unit_token="mm^2",
        specimen_record_digest=D,
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
        "machine": TensileMachineConfiguration(
            machine_id="machine-1",
            machine_revision="1",
            load_cell_id="load-cell-1",
            load_cell_revision="1",
            extensometer_id="extenso-1",
            extensometer_revision="1",
            machine_configuration_digest=D,
            load_cell_calibration_id="lc-cal-1",
            load_cell_calibration_status="valid",
            load_cell_calibration_digest=D,
            extensometer_calibration_id="ex-cal-1",
            extensometer_calibration_status="valid",
            extensometer_calibration_digest=D,
            evidence=(E,),
        ),
        "tests": tests
        or (tensile_test("t1", "s1", independence="ind-1"), tensile_test("t2", "s2", independence="ind-2")),
        "caller_profile": caller_profile or profile(),
        "specimen_product_heat_orientation_and_geometry_reviewed": True,
        "machine_load_cell_extensometer_and_calibration_reviewed": True,
        "temperature_strain_rate_and_offset_definition_reviewed": True,
        "raw_curve_and_reported_result_digests_reviewed": True,
        "result_units_uncertainties_and_validity_flags_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "caller_profile_and_missing_evidence_policy_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return TensileOffsetYieldCampaign(**value)


def test_accept_reject_review_are_caller_driven_without_recalculation():
    accepted = tensile_offset_yield_campaign(payload())
    rejected = tensile_offset_yield_campaign(payload(caller_profile=profile(320e6)))
    reviewed = tensile_offset_yield_campaign(payload(caller_profile=profile(302e6)))
    assert (accepted.values["quality_outcome"], rejected.values["quality_outcome"]) == ("accept", "reject")
    assert reviewed.values["quality_outcome"] == "review"
    assert accepted.values["raw_curve_recomputed"] is False
    assert accepted.values["offset_yield_automatically_calculated"] is False
    assert accepted.values["design_acceptance_claim"] is False


def test_missing_result_or_shared_independence_is_insufficient():
    missing = (tensile_test("t1", "s1", status="missing"), tensile_test("t2", "s2", independence="ind-2"))
    assert tensile_offset_yield_campaign(payload(tests=missing)).status == "needs_data"
    shared = (tensile_test("t1", "s1", independence="same"), tensile_test("t2", "s2", independence="same"))
    assert (
        tensile_offset_yield_campaign(payload(tests=shared)).values["quality_outcome"]
        == "insufficient_evidence"
    )


def test_local_specification_and_source_id():
    spec = specifications()[0]
    assert spec.model_id == "inspection.tensile_offset_yield_campaign"
    assert spec.input_type is TensileOffsetYieldCampaign
    assert spec.source_ids == ("authored_tensile_offset_yield_campaign_evidence_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign")
    )
