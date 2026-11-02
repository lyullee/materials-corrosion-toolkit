import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.acoustic_emission import (
    AcousticEmissionCampaign,
    acoustic_emission_campaign,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def digest(character):
    return character * 64


def payload(**updates):
    value = {
        "campaign_id": "ae-1",
        "asset_id": "asset-1",
        "location_id": "vessel-1",
        "zones": (
            {
                "zone_id": "zone-1",
                "coordinate_frame": "asset-cartesian",
                "geometry_description": "authored synthetic zone",
                "geometry_state_digest": digest("a"),
                "evidence": (EVIDENCE,),
            },
        ),
        "sensors": (
            {
                "sensor_id": "sensor-1",
                "channel_id": "channel-1",
                "zone_ids": ("zone-1",),
                "coordinate_frame": "asset-cartesian",
                "position_m": (0.0, 0.0, 0.0),
                "coupling_description": "authored coupling record",
                "calibration_id": "cal-1",
                "evidence": (EVIDENCE,),
            },
        ),
        "calibrations": (
            {
                "calibration_id": "cal-1",
                "channel_ids": ("channel-1",),
                "source_location_coordinate_frame": "asset-cartesian",
                "source_location_m": (0.1, 0.0, 0.0),
                "source_description": "authored artificial source",
                "method_id": "caller-method",
                "provider_id": "caller-provider",
                "provider_version": "1",
                "configuration_digest": digest("b"),
                "data_digest": digest("c"),
                "result_digest": digest("d"),
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "acquisition_intervals": (
            {
                "interval_id": "interval-1",
                "start_time_s": 0.0,
                "end_time_s": 60.0,
                "active_channel_ids": ("channel-1",),
                "operating_state_id": "state-1",
                "provider_id": "caller-provider",
                "provider_version": "1",
                "configuration_digest": digest("e"),
                "data_digest": digest("f"),
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "event_records": (
            {
                "event_id": "event-1",
                "interval_id": "interval-1",
                "zone_id": "zone-1",
                "channel_id": "channel-1",
                "event_time_s": 20.0,
                "feature_values": {"peak_voltage": 0.4, "duration": 0.01},
                "feature_units": {"peak_voltage": "V", "duration": "s"},
                "provider_id": "caller-provider",
                "provider_version": "1",
                "configuration_digest": digest("1"),
                "data_digest": digest("2"),
                "result_digest": digest("3"),
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "source_location_records": (
            {
                "location_record_id": "location-1",
                "event_id": "event-1",
                "zone_id": "zone-1",
                "coordinate_frame": "asset-cartesian",
                "reported_location_m": (0.2, 0.0, 0.0),
                "expanded_uncertainty_m": 0.05,
                "method_id": "caller-location-method",
                "provider_id": "caller-provider",
                "provider_version": "1",
                "configuration_digest": digest("4"),
                "data_digest": digest("5"),
                "result_digest": digest("6"),
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "support_envelope": {
            "envelope_id": "support-1",
            "applicable_zone_ids": ("zone-1",),
            "applicable_channel_ids": ("channel-1",),
            "feature_support": (
                {
                    "feature_id": "peak_voltage",
                    "unit_token": "V",
                    "minimum_value": 0.0,
                    "maximum_value": 1.0,
                },
                {
                    "feature_id": "duration",
                    "unit_token": "s",
                    "minimum_value": 0.0,
                    "maximum_value": 0.1,
                },
            ),
            "provider_id": "caller-support-provider",
            "provider_version": "1",
            "configuration_digest": digest("7"),
            "data_digest": digest("8"),
            "result_digest": digest("9"),
            "applicability_basis": "caller-reviewed support study",
            "evidence": (EVIDENCE,),
        },
        "asset_zone_geometry_reviewed": True,
        "sensor_channel_mapping_reviewed": True,
        "sensor_coupling_reviewed": True,
        "calibration_evidence_reviewed": True,
        "acquisition_intervals_reviewed": True,
        "event_feature_definitions_reviewed": True,
        "source_location_evidence_reviewed": True,
        "provider_and_digest_lineage_reviewed": True,
        "support_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return AcousticEmissionCampaign(**value)


def test_campaign_returns_technical_feature_summary():
    result = acoustic_emission_campaign(payload())
    assert result.status == "computed"
    assert result.values["valid_acquisition_duration_s"] == pytest.approx(60.0)
    assert result.values["valid_event_count"] == 1
    assert result.values["outside_declared_support_records"] == []


def test_feature_outside_caller_support_is_out_of_scope():
    campaign = payload()
    event = campaign.event_records[0].model_copy(
        update={"feature_values": {"peak_voltage": 1.5, "duration": 0.01}}
    )
    result = acoustic_emission_campaign(campaign.model_copy(update={"event_records": (event,)}))
    assert result.status == "out_of_scope"
    assert "event:event-1:feature:peak_voltage" in result.values["outside_declared_support_records"]


def test_invalid_missing_and_unreviewed_records_need_data():
    assert acoustic_emission_campaign(payload(sensor_coupling_reviewed=False)).status == "needs_data"
    campaign = payload()
    event = campaign.event_records[0].model_copy(
        update={"interval_id": "missing", "record_valid": False, "invalid_basis": "truncated"}
    )
    result = acoustic_emission_campaign(campaign.model_copy(update={"event_records": (event,)}))
    assert result.status == "needs_data"
    assert "event:event-1" in result.values["invalid_record_ids"]
    assert "event:event-1:interval:missing" in result.values["missing_reference_records"]


def test_feature_units_and_context_identity_are_enforced():
    campaign = payload()
    with pytest.raises(ValueError, match="identical keys"):
        campaign.event_records[0].model_copy(update={"feature_units": {"peak_voltage": "V"}}).model_validate(
            campaign.event_records[0].model_copy(update={"feature_units": {"peak_voltage": "V"}}).model_dump()
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.acoustic_emission_campaign",
            campaign,
            RunContext(asset_id="other", location_id="vessel-1", time_basis="authored"),
        )
