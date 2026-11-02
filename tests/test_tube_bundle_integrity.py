import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.tube_bundle_integrity import (
    TubeBundleIntegrityEvidence,
    specifications,
    tube_bundle_integrity_evidence,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def observation(**updates):
    value = {
        "observation_id": "obs-1",
        "observation_kind": "defect_or_condition_inspection",
        "physical_source_group_id": "inspection-run-1",
        "method_id": "inspection-1",
        "metric_id": "condition-metric",
        "metric_definition": "authored condition metric",
        "reported_value": 0.2,
        "unit_token": "custom-condition-unit",
        "expanded_uncertainty": 0.02,
        "detection_status": "detected",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "tube_material_condition_id": "material-1",
        "minimum_outer_diameter_m": 0.01,
        "maximum_outer_diameter_m": 0.04,
        "minimum_wall_thickness_m": 0.0005,
        "maximum_wall_thickness_m": 0.005,
        "supported_support_descriptors": ("support-1",),
        "supported_baffle_descriptors": ("baffle-1",),
        "supported_vibration_descriptors": ("vibration-state-1",),
        "supported_operating_state_ids": ("state-1",),
        "metric_support": (
            {
                "observation_kind": "defect_or_condition_inspection",
                "metric_id": "condition-metric",
                "unit_token": "custom-condition-unit",
                "supported_method_ids": ("inspection-1",),
                "minimum_supported_value": 0.0,
                "maximum_supported_value": 1.0,
                "maximum_supported_expanded_uncertainty": 0.1,
                "support_basis": "authored support",
            },
        ),
        "qualification_evidence": (
            {
                "evidence_record_id": "evidence-1",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "partition": "qualification",
                "supported_metric_ids": ("condition-metric",),
                "provider_id": "provider-1",
                "provider_revision": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "supports_declared_envelope": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "minimum_qualification_source_group_count": 1,
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "tube-location-1",
        "exchanger_id": "exchanger-1",
        "bundle_id": "bundle-1",
        "tube_id": "tube-1",
        "row_id": "row-1",
        "tube_location_definition": "authored mapped tube location",
        "tube_material_condition_id": "material-1",
        "tube_outer_diameter_m": 0.02,
        "tube_wall_thickness_m": 0.002,
        "support_descriptor": "support-1",
        "baffle_descriptor": "baffle-1",
        "vibration_descriptor": "vibration-state-1",
        "clock_id": "clock-1",
        "operating_intervals": (
            {
                "interval_id": "interval-1",
                "start_time_s": 0.0,
                "end_time_s": 3600.0,
                "operating_state_id": "state-1",
                "record_digest": DIGEST_A,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": (observation(),),
        "disposition_records": (
            {
                "disposition_id": "disposition-1",
                "disposition_kind": "monitor",
                "disposition_time_s": 3600.0,
                "caller_decision_record_id": "decision-1",
                "affected_tube_id": "tube-1",
                "record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (envelope(),),
        "exchanger_bundle_tube_row_and_location_reviewed": True,
        "tube_material_condition_and_geometry_reviewed": True,
        "support_baffle_and_vibration_descriptors_reviewed": True,
        "operating_clock_and_states_reviewed": True,
        "observation_metrics_units_uncertainty_and_detection_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "disposition_records_reviewed_as_caller_decisions": True,
        "qualification_specimens_and_source_groups_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return TubeBundleIntegrityEvidence(**value)


def test_reviewed_evidence_computes_and_keeps_caller_disposition():
    result = tube_bundle_integrity_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["caller_disposition_summary"][0]["disposition_kind"] == "monitor"


def test_geometry_descriptor_or_observation_range_exits_support():
    result = tube_bundle_integrity_evidence(
        payload(
            support_descriptor="different",
            observations=(observation(reported_value=2.0),),
        )
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_observation_ids"] == ["obs-1"]
    assert result.values["outside_support_reasons"] == [
        "support_descriptor",
        "observation_range_or_uncertainty",
    ]


def test_missing_review_or_metric_unit_mismatch_needs_data():
    assert (
        tube_bundle_integrity_evidence(payload(provider_lineage_and_digests_reviewed=False)).status
        == "needs_data"
    )
    result = tube_bundle_integrity_evidence(payload(observations=(observation(unit_token="other-unit"),)))
    assert result.status == "needs_data"
    assert result.values["unsupported_observation_ids"] == ["obs-1"]


def test_detection_contract_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="detection limit"):
        payload(
            observations=(
                observation(
                    detection_status="below_detection",
                    reported_value=None,
                    detection_limit=None,
                ),
            )
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.tube_bundle_integrity_evidence",
            payload(),
            RunContext(asset_id="other", location_id="tube-location-1", time_basis="authored"),
        )
