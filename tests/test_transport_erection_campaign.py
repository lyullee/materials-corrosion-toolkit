import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.transport_erection_campaign import (
    TransportErectionCampaignAssessment,
    TransportErectionCampaignReport,
    specifications,
    transport_erection_campaign,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored campaign"}


def digest(character):
    return character * 64


def observation(identifier, event_id, time_s, kind, metric, value, unit, **updates):
    row = {
        "observation_id": identifier,
        "event_id": event_id,
        "observation_time_s": time_s,
        "observation_kind": kind,
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}",
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 0.1,
        "sensor_or_instrument_id": f"instrument-{identifier}",
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "configuration_digest": digest("a"),
        "raw_data_digest": digest("b"),
        "observation_record_digest": digest("c"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def event(identifier, sequence, kind, start, end, observations=(), **updates):
    row = {
        "event_id": identifier,
        "sequence_index": sequence,
        "event_kind": kind,
        "activity_id": f"activity-{identifier}",
        "start_time_s": start,
        "end_time_s": end,
        "item_id": "item-1",
        "lift_id": "lift-1" if kind == "lift" else None,
        "transport_id": "transport-1" if kind == "transport" else None,
        "storage_id": "storage-1" if kind == "storage" else None,
        "erection_id": "erection-1" if kind == "erection" else None,
        "support_id": "support-1" if kind.startswith("temporary_support") else None,
        "orientation_definition": f"caller orientation for {identifier}",
        "event_configuration_digest": digest("d"),
        "observations": observations,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def measurement(identifier, event_id, time_s, kind, stage, metric=None, value=None, unit=None, **updates):
    quantitative = metric is not None
    row = {
        "measurement_id": identifier,
        "event_id": event_id,
        "measurement_time_s": time_s,
        "measurement_kind": kind,
        "stage_id": stage,
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}" if quantitative else None,
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 0.2 if quantitative else None,
        "reported_finding": f"caller-reported {kind} finding",
        "caller_disposition_id": None,
        "instrument_or_nde_procedure_id": f"procedure-{kind}",
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "raw_data_digest": digest("e"),
        "measurement_record_digest": digest("f"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def events(acceleration=1.5, acceleration_unit="m/s2"):
    transport_observations = (
        observation(
            "accel-1",
            "transport-event",
            5,
            "acceleration",
            "peak_acceleration",
            acceleration,
            acceleration_unit,
        ),
        observation("temp-1", "transport-event", 5, "temperature", "temperature", 295, "K"),
        observation("humidity-1", "transport-event", 5, "humidity", "relative_humidity", 40, "%"),
        observation("impact-1", "transport-event", 5, "impact", "impact_index", 0, "count"),
        observation("load-1", "transport-event", 5, "load", "transport_load", 10, "kN"),
        observation("orientation-1", "transport-event", 5, "orientation", "tilt", 0.01, "rad"),
    )
    return (
        event("transport-event", 0, "transport", 0, 10, transport_observations),
        event("storage-event", 1, "storage", 10, 20),
        event("support-install", 2, "temporary_support_install", 20, 21),
        event("lift-event", 3, "lift", 21, 30),
        event("erection-event", 4, "erection", 30, 40),
        event("support-remove", 5, "temporary_support_remove", 40, 41),
    )


def measurements(alignment=0.5, alignment_unit="mm"):
    return (
        measurement(
            "alignment-1",
            "erection-event",
            35,
            "alignment",
            "post_erection",
            "alignment_offset",
            alignment,
            alignment_unit,
        ),
        measurement("geometry-1", "erection-event", 35, "geometry", "post_erection"),
        measurement("damage-1", "erection-event", 35, "damage_survey", "post_erection"),
        measurement("nde-1", "erection-event", 35, "nde", "post_erection"),
    )


def criterion(identifier, source, metric, aggregation, direction, accept, reject, unit):
    return {
        "criterion_id": identifier,
        "evidence_source": source,
        "metric_id": metric,
        "aggregation": aggregation,
        "direction": direction,
        "accept_limit": accept,
        "reject_limit": reject,
        "unit_token": unit,
        "criterion_basis": "caller-authored handling criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_event_kinds": (
            "transport",
            "storage",
            "temporary_support_install",
            "lift",
            "erection",
            "temporary_support_remove",
        ),
        "required_measurement_kinds": ("alignment", "geometry", "damage_survey", "nde"),
        "required_measurement_stage_ids": ("post_erection",),
        "criteria": (
            criterion(
                "acceleration-limit", "observation", "peak_acceleration", "maximum", "maximum", 2, 4, "m/s2"
            ),
            criterion("alignment-limit", "measurement", "alignment_offset", "maximum", "maximum", 1, 3, "mm"),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("a"),
        "caller_acceptance_authority": "caller handling review team",
        "structural_solver_used": False,
        "allowable_load_or_code_table_embedded": False,
        "automatic_damage_determination_claimed": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "item_id": "item-1",
        "item_configuration_digest": digest("b"),
        "clock_id": "clock-1",
        "events": events(),
        "temporary_supports": (
            {
                "support_id": "support-1",
                "support_type_descriptor": "caller temporary support descriptor",
                "physical_location_definition": "reviewed item coordinate",
                "installation_event_id": "support-install",
                "removal_event_id": "support-remove",
                "final_state": "removed",
                "support_configuration_digest": digest("c"),
                "installation_record_digest": digest("d"),
                "removal_record_digest": digest("e"),
                "evidence": (EVIDENCE,),
            },
        ),
        "measurements": measurements(),
        "caller_profile": profile(),
        "item_lift_transport_storage_erection_identity_reviewed": True,
        "ordered_event_clock_and_orientation_reviewed": True,
        "observation_units_uncertainty_and_provenance_reviewed": True,
        "temporary_support_install_remove_state_reviewed": True,
        "alignment_geometry_damage_and_nde_evidence_reviewed": True,
        "caller_profile_and_criteria_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return TransportErectionCampaignAssessment.model_validate(row)


def test_campaign_accepts_only_under_caller_profile_without_damage_or_solver_claims():
    result = transport_erection_campaign(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["metric_values"]["observation:peak_acceleration"] == 1.5
    assert result.values["structural_solver_or_allowable_load"] is False
    assert result.values["automatic_damage_determination"] is False
    assert result.values["physical_qualification"] is False


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = transport_erection_campaign(payload(events=events(acceleration=3)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = transport_erection_campaign(payload(events=events(acceleration=5)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_required_evidence_invalid_record_and_unit_conflict_are_insufficient():
    missing_nde = tuple(row for row in measurements() if row["measurement_kind"] != "nde")
    result = transport_erection_campaign(payload(measurements=missing_nde))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["missing_required_measurement_kinds"] == ["nde"]

    invalid_measurements = list(measurements())
    invalid_measurements[0] = {
        **invalid_measurements[0],
        "record_valid": False,
        "invalid_or_missing_basis": "review rejected measurement",
    }
    result = transport_erection_campaign(payload(measurements=tuple(invalid_measurements)))
    assert result.status == "needs_data"

    result = transport_erection_campaign(payload(events=events(acceleration_unit="g")))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["criterion_unit_conflict_ids"] == ["acceleration-limit"]


def test_order_support_links_and_report_digest_are_strict():
    unordered = list(events())
    unordered[0], unordered[1] = unordered[1], unordered[0]
    with pytest.raises(ValueError, match="sequence order"):
        payload(events=tuple(unordered))

    bad_support = payload().model_dump()
    bad_support["temporary_supports"][0]["removal_event_id"] = "lift-event"
    with pytest.raises(ValueError, match="removal must link"):
        TransportErectionCampaignAssessment.model_validate(bad_support)

    first = transport_erection_campaign(payload())
    second = transport_erection_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    TransportErectionCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        TransportErectionCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "fabrication.transport_erection"
    assert spec.source_ids == ("authored_transport_erection_campaign_evidence_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="handling clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="handling clock")
        )
