from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.coating_campaign_profile import (
    CoatingCampaignAssessment,
    CoatingCampaignAssessmentResult,
    assess_coating_campaign,
)

SHA = "a" * 64


def ev(label):
    return {"source_id": label, "origin": "user_declared", "citation": label, "sha256": SHA}


def measurement(index, kind, metric, value, unit, group):
    return {
        "measurement_id": f"{metric}-{index}",
        "replicate_group_id": group,
        "specimen_id": f"specimen-{index}",
        "location_id": f"location-{index}",
        "metric_kind": kind,
        "metric_id": metric,
        "metric_definition": f"caller {metric}",
        "unit_token": unit,
        "status": "available",
        "value": value,
        "standard_uncertainty": abs(value) * 0.01,
        "provider_id": "campaign-lab",
        "provider_revision": "1",
        "input_digest": SHA,
        "result_digest": SHA,
        "evidence": (ev(f"{metric}-{index}"),),
    }


def rule(rule_id, kind, metric, unit, minimum=None, maximum=None, aggregation="replicate_mean"):
    return {
        "rule_id": rule_id,
        "metric_kind": kind,
        "metric_id": metric,
        "unit_token": unit,
        "aggregation": aggregation,
        "minimum_inclusive": minimum,
        "maximum_inclusive": maximum,
        "uncertainty_policy": "interval_must_fit",
        "uncertainty_coverage_factor": 1.0,
        "minimum_replicates_per_group": 2,
        "missing_disposition": "insufficient_evidence",
        "rule_description": f"caller rule {rule_id}",
    }


def payload(**changes):
    measurements = (
        measurement(1, "dft", "dry-film-thickness", 200e-6, "m", "dft-group"),
        measurement(2, "dft", "dry-film-thickness", 205e-6, "m", "dft-group"),
        measurement(1, "adhesion", "pull-off-stress", 5e6, "Pa", "adhesion-group"),
        measurement(2, "adhesion", "pull-off-stress", 5.2e6, "Pa", "adhesion-group"),
        measurement(1, "porosity", "area-porosity", 0.03, "1", "porosity-group"),
        measurement(2, "porosity", "area-porosity", 0.032, "1", "porosity-group"),
        measurement(1, "holiday_count", "holiday-count", 0.0, "count", "holiday-group"),
        measurement(2, "holiday_count", "holiday-count", 0.0, "count", "holiday-group"),
    )
    data = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "coating-location-1",
        "campaign_id": "campaign-1",
        "coating_lot_id": "lot-1",
        "coating_system_id": "system-1",
        "substrate_condition_id": "substrate-1",
        "surface_preparation_id": "prep-1",
        "batch_id": "batch-1",
        "process_condition_id": "process-1",
        "application_environment_id": "environment-1",
        "measurements": measurements,
        "cure_heat_history": (
            {
                "interval_id": "cure-1",
                "sequence_position": 1,
                "clock_id": "cure-clock-1",
                "start_time_s": 0.0,
                "end_time_s": 3600.0,
                "minimum_temperature_k": 300.0,
                "maximum_temperature_k": 350.0,
                "environment_id": "environment-1",
                "provider_id": "cure-provider",
                "result_digest": SHA,
                "evidence": (ev("cure"),),
            },
        ),
        "profile": {
            "profile_id": "profile-1",
            "profile_revision": "1",
            "source_digest": SHA,
            "permitted_substrate_condition_ids": ("substrate-1",),
            "permitted_surface_preparation_ids": ("prep-1",),
            "permitted_coating_system_ids": ("system-1",),
            "permitted_process_condition_ids": ("process-1",),
            "permitted_environment_ids": ("environment-1",),
            "minimum_cure_temperature_k": 290.0,
            "maximum_cure_temperature_k": 400.0,
            "maximum_cure_interval_s": 7200.0,
            "metric_rules": (
                rule("dft-rule", "dft", "dry-film-thickness", "m", 180e-6, 230e-6),
                rule("adhesion-rule", "adhesion", "pull-off-stress", "Pa", 4e6, None),
                rule("porosity-rule", "porosity", "area-porosity", "1", 0.0, 0.05),
                rule("holiday-rule", "holiday_count", "holiday-count", "count", 0.0, 0.0),
            ),
            "profile_reviewed": True,
            "evidence": (ev("profile"),),
        },
        "campaign_lot_substrate_surface_prep_batch_and_process_identity_reviewed": True,
        "metric_definitions_units_replicates_uncertainty_and_provenance_reviewed": True,
        "cure_heat_clock_temperature_and_environment_reviewed": True,
        "caller_profile_authority_identity_and_rules_reviewed": True,
        "evidence": (ev("assessment"),),
    }
    data.update(changes)
    return CoatingCampaignAssessment.model_validate(data)


def test_complete_campaign_aggregates_existing_measurement_evidence_and_accepts():
    result = assess_coating_campaign(payload())
    assert result.disposition == "accept"
    assert all(row.outcome == "pass" for row in result.findings)
    assert not result.standard_or_code_qualification_claim
    assert not result.physical_validation_claim


def test_caller_metric_or_cure_envelope_can_reject():
    base = payload()
    profile = base.profile.model_copy(
        update={
            "metric_rules": tuple(
                row.model_copy(update={"maximum_inclusive": 0.02}) if row.rule_id == "porosity-rule" else row
                for row in base.profile.metric_rules
            )
        }
    )
    result = assess_coating_campaign(base.model_copy(update={"profile": profile}))
    assert result.disposition == "reject"
    assert any(row.rule_id == "porosity-rule" and row.outcome == "fail" for row in result.findings)

    cure = base.cure_heat_history[0].model_copy(update={"maximum_temperature_k": 450.0})
    assert (
        assess_coating_campaign(base.model_copy(update={"cure_heat_history": (cure,)})).disposition
        == "reject"
    )


def test_identity_mismatch_reviews_and_unit_or_replicate_gap_is_insufficient():
    assert assess_coating_campaign(payload(surface_preparation_id="unlisted")).disposition == "review"
    rows = tuple(row for row in payload().measurements if row.measurement_id != "dry-film-thickness-2")
    result = assess_coating_campaign(payload(measurements=rows))
    assert result.disposition == "insufficient_evidence"

    rows = list(payload().measurements)
    rows[0] = rows[0].model_copy(update={"unit_token": "um"})
    rows[1] = rows[1].model_copy(update={"unit_token": "um"})
    assert assess_coating_campaign(payload(measurements=tuple(rows))).disposition == "insufficient_evidence"


def test_duplicate_measurement_and_cure_clock_are_strict():
    base = payload()
    with pytest.raises(ValidationError, match="measurement IDs"):
        payload(measurements=(base.measurements[0], base.measurements[0]))


def test_deterministic_digest_round_trip_and_tamper_detection():
    first = assess_coating_campaign(payload())
    second = assess_coating_campaign(payload())
    assert first.input_digest == second.input_digest
    assert first.result_digest == second.result_digest
    assert CoatingCampaignAssessmentResult.model_validate_json(first.model_dump_json()) == first
    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        CoatingCampaignAssessmentResult.model_validate(changed)
