from matintegrity.contracts import RunContext
from matintegrity.models.hardness_testing_campaign import (
    HardnessCampaignCallerProfile,
    HardnessReading,
    HardnessReferenceBlockEvidence,
    HardnessTestConfiguration,
    HardnessTestingCampaign,
    HardnessTestSubject,
    hardness_testing_campaign,
    specifications,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller hardness data"}
D = "3" * 64


def reading(rid, value=200.0, independence="ind-1", validity="valid"):
    return HardnessReading(
        reading_id=rid,
        specimen_id="specimen-1",
        sequence_index=int(rid[-1]),
        hardness_value=value,
        expanded_hardness_uncertainty=5.0,
        hardness_unit_token="scale-X",
        surface_condition_id="prepared-1",
        nearest_indent_spacing=5.0,
        edge_distance=4.0,
        local_thickness=8.0,
        geometry_unit_token="mm",
        expanded_geometry_uncertainty=0.1,
        replicate_group_id="rep-1",
        source_group_id=f"source-{rid}",
        independence_group_id=independence,
        caller_validity_status=validity,
        caller_validity_basis="caller reviewed reading",
        reading_record_digest=D,
        evidence=(E,),
    )


def profile(minimum=150.0):
    return HardnessCampaignCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        supported_component_ids=("component-1",),
        supported_material_ids=("material-1",),
        supported_material_condition_ids=("condition-1",),
        supported_heat_ids=("heat-1",),
        required_method_id="method-1",
        required_scale_id="scale-X",
        required_hardness_unit_token="scale-X",
        required_applied_load=10.0,
        required_applied_load_unit_token="kgf",
        required_dwell_time_s=10.0,
        dwell_time_tolerance_s=0.5,
        required_indenter_id="indenter-1",
        required_instrument_id="instrument-1",
        required_reference_block_id="block-1",
        supported_surface_condition_ids=("prepared-1",),
        geometry_unit_token="mm",
        minimum_indent_spacing=4.0,
        minimum_edge_distance=3.0,
        minimum_local_thickness=7.0,
        minimum_hardness=minimum,
        minimum_valid_reading_count=2,
        minimum_independence_group_count=2,
        caller_validity_policy_id="caller-validity-1",
        profile_source_digest=D,
        evidence=(E,),
    )


def payload(caller_profile=None, readings=None, **updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "subjects": (
            HardnessTestSubject(
                specimen_id="specimen-1",
                component_id="component-1",
                location_id="location-1",
                material_id="material-1",
                material_condition_id="condition-1",
                heat_id="heat-1",
                subject_record_digest=D,
                evidence=(E,),
            ),
        ),
        "configuration": HardnessTestConfiguration(
            method_id="method-1",
            scale_id="scale-X",
            hardness_unit_token="scale-X",
            applied_load=10.0,
            applied_load_unit_token="kgf",
            dwell_time_s=10.0,
            indenter_id="indenter-1",
            indenter_definition="caller indenter identity",
            instrument_id="instrument-1",
            instrument_revision="1",
            configuration_digest=D,
            evidence=(E,),
        ),
        "reference_block": HardnessReferenceBlockEvidence(
            reference_block_id="block-1",
            reference_block_condition_id="condition-a",
            scale_id="scale-X",
            certified_value=200.0,
            certified_expanded_uncertainty=2.0,
            hardness_unit_token="scale-X",
            certificate_id="certificate-1",
            certificate_revision="1",
            certificate_digest=D,
            verification_status="valid",
            verification_record_digest=D,
            evidence=(E,),
        ),
        "readings": readings or (reading("r1", independence="ind-1"), reading("r2", independence="ind-2")),
        "caller_profile": caller_profile or profile(),
        "subject_component_location_material_and_heat_reviewed": True,
        "method_scale_load_dwell_indenter_and_instrument_reviewed": True,
        "calibration_and_reference_block_reviewed": True,
        "surface_spacing_thickness_and_uncertainty_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "caller_validity_flags_and_profile_reviewed": True,
        "provenance_and_record_digests_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return HardnessTestingCampaign(**value)


def test_campaign_accept_reject_review_use_only_caller_bounds():
    accepted = hardness_testing_campaign(payload())
    rejected = hardness_testing_campaign(payload(caller_profile=profile(220.0)))
    reviewed = hardness_testing_campaign(payload(caller_profile=profile(202.0)))
    assert (accepted.values["quality_outcome"], rejected.values["quality_outcome"]) == (
        "accept",
        "reject",
    )
    assert reviewed.values["quality_outcome"] == "review"
    assert accepted.values["official_scale_conversion_applied"] is False
    assert accepted.values["material_strength_inferred"] is False
    assert accepted.values["design_acceptance_claim"] is False


def test_invalid_reading_or_shared_independence_is_insufficient():
    invalid = (reading("r1", validity="invalid"), reading("r2", independence="ind-2"))
    assert hardness_testing_campaign(payload(readings=invalid)).status == "needs_data"
    shared = (reading("r1", independence="same"), reading("r2", independence="same"))
    assert hardness_testing_campaign(payload(readings=shared)).values["quality_outcome"] == (
        "insufficient_evidence"
    )


def test_local_specification_and_source_id():
    spec = specifications()[0]
    assert spec.model_id == "inspection.hardness_testing_campaign"
    assert spec.input_type is HardnessTestingCampaign
    assert spec.source_ids == ("authored_hardness_testing_campaign_evidence_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign")
    )
