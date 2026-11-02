from matintegrity.contracts import RunContext
from matintegrity.models.storage_preservation_campaign import (
    PreservationCampaignFact,
    PreservationFactCriterion,
    PreservationSystemIdentity,
    StoragePreservationCallerProfile,
    StoragePreservationCampaign,
    StoragePreservationEvent,
    specifications,
    storage_preservation_campaign,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller storage data"}
D = "6" * 64


def humidity(value=0.4, status="reported"):
    return PreservationCampaignFact(
        fact_id="humidity",
        fact_kind="relative_humidity",
        quantity_id="relative_humidity",
        result_mode="quantitative",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=0.02 if status == "reported" else None,
        unit_token="1",
        method_id="sensor-1",
        fact_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not recorded",
        evidence=(E,),
    )


def exposure(value=0.4, status="reported"):
    return StoragePreservationEvent(
        event_id="exposure-1",
        sequence_index=1,
        event_kind="exposure",
        start_time_s=0.0,
        end_time_s=100.0,
        storage_location_id="store-1",
        preservation_system_id="system-1",
        facts=(humidity(value, status),),
        caller_validity_status="valid",
        caller_validity_basis="caller reviewed event",
        event_record_digest=D,
        source_group_id="logger-1",
        evidence=(E,),
    )


def instant(eid, sequence, kind, time):
    return StoragePreservationEvent(
        event_id=eid,
        sequence_index=sequence,
        event_kind=kind,
        start_time_s=time,
        storage_location_id="store-1",
        preservation_system_id="system-1",
        caller_validity_status="valid",
        caller_validity_basis="caller reviewed event",
        event_record_digest=D,
        source_group_id=f"source-{eid}",
        evidence=(E,),
    )


def profile(maximum=0.6):
    return StoragePreservationCallerProfile(
        profile_id="profile-1",
        profile_revision="1",
        item_id="item-1",
        material_id="material-1",
        storage_area_id="area-1",
        storage_location_id="store-1",
        supported_preservation_system_ids=("system-1",),
        maximum_uncovered_duration_s=0.0,
        minimum_inspection_count=1,
        minimum_renewal_count=1,
        fact_criteria=(
            PreservationFactCriterion(
                criterion_id="humidity-rule",
                fact_kind="relative_humidity",
                quantity_id="relative_humidity",
                result_mode="quantitative",
                unit_token="1",
                maximum_acceptable=maximum,
                required_event_kinds=("exposure",),
                criterion_basis="caller humidity criterion",
                evidence=(E,),
            ),
        ),
        profile_source_digest=D,
        evidence=(E,),
    )


def payload(caller_profile=None, events=None, **updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "campaign_id": "campaign-1",
        "item_id": "item-1",
        "material_id": "material-1",
        "storage_area_id": "area-1",
        "storage_location_id": "store-1",
        "horizon_start_s": 0.0,
        "horizon_end_s": 100.0,
        "preservation_systems": (
            PreservationSystemIdentity(
                preservation_system_id="system-1",
                preservation_method_id="method-1",
                preservation_material_id="material-preservative-1",
                preservation_material_batch_id="batch-1",
                application_procedure_id="procedure-1",
                system_record_digest=D,
                evidence=(E,),
            ),
        ),
        "events": events
        or (
            instant("start", 0, "storage_start", 0.0),
            exposure(),
            instant("inspection", 2, "inspection", 50.0),
            instant("renewal", 3, "renewal", 60.0),
            instant("end", 4, "storage_end", 100.0),
        ),
        "caller_profile": caller_profile or profile(),
        "item_material_area_and_storage_location_reviewed": True,
        "preservation_methods_material_batches_and_procedures_reviewed": True,
        "event_clock_order_and_interval_coverage_reviewed": True,
        "environment_and_preservation_fact_units_uncertainties_reviewed": True,
        "inspections_renewals_surface_and_corrosion_observations_reviewed": True,
        "caller_validity_profile_missingness_and_digests_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return StoragePreservationCampaign(**value)


def test_accept_reject_review_use_only_caller_profile():
    accepted = storage_preservation_campaign(payload())
    rejected = storage_preservation_campaign(payload(caller_profile=profile(0.3)))
    reviewed = storage_preservation_campaign(payload(caller_profile=profile(0.41)))
    assert (accepted.values["quality_outcome"], rejected.values["quality_outcome"]) == ("accept", "reject")
    assert reviewed.values["quality_outcome"] == "review"
    assert accepted.values["corrosion_rate_inferred"] is False
    assert accepted.values["remaining_life_inferred"] is False
    assert accepted.values["automatic_acceptance_claim"] is False


def test_missing_fact_or_uncovered_interval_is_not_silently_accepted():
    missing_events = (
        instant("start", 0, "storage_start", 0.0),
        exposure(status="missing"),
        instant("inspection", 2, "inspection", 50.0),
        instant("renewal", 3, "renewal", 60.0),
    )
    assert storage_preservation_campaign(payload(events=missing_events)).status == "needs_data"
    short = exposure().model_copy(update={"end_time_s": 80.0})
    short_events = (
        instant("start", 0, "storage_start", 0.0),
        short,
        instant("inspection", 2, "inspection", 50.0),
        instant("renewal", 3, "renewal", 60.0),
    )
    assert storage_preservation_campaign(payload(events=short_events)).values["quality_outcome"] == "reject"


def test_local_specification_and_source_id():
    spec = specifications()[0]
    assert spec.model_id == "fabrication.storage_preservation"
    assert spec.input_type is StoragePreservationCampaign
    assert spec.source_ids == ("authored_storage_preservation_campaign_evidence_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign")
    )
