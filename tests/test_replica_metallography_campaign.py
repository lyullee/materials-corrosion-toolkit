from matintegrity.contracts import RunContext
from matintegrity.models.replica_metallography_campaign import (
    ReplicaAcquisitionConfiguration,
    ReplicaCampaignCallerProfile,
    ReplicaCampaignField,
    ReplicaCampaignObservation,
    ReplicaMetallographyCampaign,
    ReplicaObservationCriterion,
    ReplicaServiceInterval,
    replica_metallography_campaign,
    specifications,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller replica data"}
D = "5" * 64


def observation(value=2.0, status="reported"):
    return ReplicaCampaignObservation(
        observation_id="cavity-density",
        observation_kind="cavity",
        metric_id="cavity_density",
        metric_definition="caller-reported cavity count density",
        result_mode="quantitative",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=0.2 if status == "reported" else None,
        unit_token="1/mm^2",
        observer_id="observer-1",
        observation_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not reported",
        evidence=(E,),
    )


def field(fid, value=2.0, status="reported", independence="ind-1"):
    return ReplicaCampaignField(
        field_id=fid,
        replica_id=f"replica-{fid}",
        replica_site_id="site-1",
        sequence_index=int(fid[-1]),
        configuration=ReplicaAcquisitionConfiguration(
            surface_preparation_id="prep-1",
            surface_preparation_definition="caller preparation",
            replication_medium_id="medium-1",
            replication_medium_lot_id="lot-1",
            magnification=500.0,
            instrument_id="microscope-1",
            instrument_revision="1",
            instrument_configuration_digest=D,
            calibration_id="cal-1",
            calibration_revision="1",
            calibration_status="valid",
            calibration_record_digest=D,
            evidence=(E,),
        ),
        image_digest=D,
        field_record_digest=D,
        observations=(observation(value, status),),
        replicate_group_id="rep-group",
        source_group_id=f"source-{fid}",
        independence_group_id=independence,
        caller_validity_status="valid",
        caller_validity_basis="caller reviewed field",
        evidence=(E,),
    )


def profile(maximum=3.0):
    return ReplicaCampaignCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        component_id="component-1",
        material_id="material-1",
        material_condition_id="condition-1",
        heat_id="heat-1",
        supported_replica_site_ids=("site-1",),
        supported_environment_descriptor_ids=("service-1",),
        required_surface_preparation_id="prep-1",
        required_replication_medium_id="medium-1",
        required_magnification=500.0,
        magnification_tolerance=0.0,
        required_instrument_id="microscope-1",
        required_calibration_id="cal-1",
        criteria=(
            ReplicaObservationCriterion(
                criterion_id="cavity-rule",
                observation_kind="cavity",
                metric_id="cavity_density",
                metric_definition="caller-reported cavity count density",
                result_mode="quantitative",
                unit_token="1/mm^2",
                maximum_acceptable=maximum,
                criterion_basis="caller cavity criterion",
                evidence=(E,),
            ),
        ),
        minimum_valid_field_count=2,
        minimum_independence_group_count=2,
        caller_validity_policy_id="validity-1",
        profile_source_digest=D,
        evidence=(E,),
    )


def payload(caller_profile=None, fields=None, **updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "component_id": "component-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "heat_id": "heat-1",
        "service_history": (
            ReplicaServiceInterval(
                interval_id="service-interval-1",
                start_time_s=0.0,
                end_time_s=1000.0,
                minimum_temperature_K=700.0,
                maximum_temperature_K=800.0,
                environment_descriptor_id="service-1",
                service_record_digest=D,
                evidence=(E,),
            ),
        ),
        "fields": fields or (field("f1", independence="ind-1"), field("f2", independence="ind-2")),
        "caller_profile": caller_profile or profile(),
        "component_location_material_heat_and_service_history_reviewed": True,
        "surface_preparation_medium_magnification_and_instrument_reviewed": True,
        "calibration_image_and_record_digests_reviewed": True,
        "observation_definitions_units_classes_and_uncertainties_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "caller_validity_flags_profile_and_missingness_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return ReplicaMetallographyCampaign(**value)


def test_accept_reject_review_are_caller_driven_without_image_analysis():
    accepted = replica_metallography_campaign(payload())
    rejected = replica_metallography_campaign(payload(caller_profile=profile(1.0)))
    reviewed = replica_metallography_campaign(payload(caller_profile=profile(2.1)))
    assert (accepted.values["quality_outcome"], rejected.values["quality_outcome"]) == ("accept", "reject")
    assert reviewed.values["quality_outcome"] == "review"
    assert accepted.values["image_automatic_analysis_performed"] is False
    assert accepted.values["creep_life_inferred"] is False
    assert accepted.values["standard_acceptance_claim"] is False


def test_missing_observation_or_shared_independence_is_insufficient():
    missing = (field("f1", status="missing"), field("f2", independence="ind-2"))
    assert replica_metallography_campaign(payload(fields=missing)).status == "needs_data"
    shared = (field("f1", independence="same"), field("f2", independence="same"))
    assert (
        replica_metallography_campaign(payload(fields=shared)).values["quality_outcome"]
        == "insufficient_evidence"
    )


def test_local_specification_and_source_id():
    spec = specifications()[0]
    assert spec.model_id == "inspection.replica_metallography_campaign"
    assert spec.input_type is ReplicaMetallographyCampaign
    assert spec.source_ids == ("authored_replica_metallography_campaign_evidence_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign")
    )
