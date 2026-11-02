from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.overlay_cladding_campaign import (
    OverlayCladdingCampaign,
    OverlayCladdingCampaignResult,
    assess_overlay_cladding,
)

SHA = "a" * 64


def ev(x):
    return {"source_id": x, "origin": "user_declared", "citation": x, "sha256": SHA}


def measurement(i, kind, metric, value, unit, group):
    return {
        "measurement_id": f"{metric}-{i}",
        "layer_id": "layer-1",
        "pass_id": f"pass-{i}",
        "replicate_group_id": group,
        "location_id": f"loc-{i}",
        "metric_kind": kind,
        "metric_id": metric,
        "metric_definition": metric,
        "unit_token": unit,
        "status": "available",
        "value": value,
        "standard_uncertainty": abs(value) * 0.01,
        "method_id": "method",
        "provider_id": "lab",
        "provider_revision": "1",
        "input_digest": SHA,
        "result_digest": SHA,
        "evidence": (ev(f"m-{i}"),),
    }


def payload(**changes):
    data = {
        "assessment_id": "a1",
        "asset_id": "asset",
        "location_id": "loc",
        "campaign_id": "campaign",
        "substrate_id": "substrate",
        "substrate_condition_id": "prepared",
        "passes": tuple(
            {
                "pass_id": f"pass-{i}",
                "sequence_position": i,
                "layer_id": "layer-1",
                "layer_sequence_position": 1,
                "substrate_or_parent_id": "substrate",
                "filler_lot_id": "filler-1",
                "process_id": "process-1",
                "procedure_id": "procedure-1",
                "heat_input_j_m": 1000.0,
                "provider_result_digest": SHA,
                "evidence": (ev(f"p-{i}"),),
            }
            for i in (1, 2)
        ),
        "measurements": (
            measurement(1, "dilution", "dilution-fraction", 0.10, "1", "dilution"),
            measurement(2, "dilution", "dilution-fraction", 0.11, "1", "dilution"),
            measurement(1, "layer_thickness", "thickness", 0.003, "m", "thickness"),
            measurement(2, "layer_thickness", "thickness", 0.0031, "m", "thickness"),
            measurement(1, "ferrite", "ferrite-metric", 5.0, "caller-unit", "ferrite"),
            measurement(2, "ferrite", "ferrite-metric", 5.2, "caller-unit", "ferrite"),
        ),
        "heat_history": (
            {
                "interval_id": "h1",
                "sequence_position": 1,
                "interval_kind": "deposition",
                "start_time_s": 0.0,
                "end_time_s": 10.0,
                "minimum_temperature_k": 300.0,
                "maximum_temperature_k": 500.0,
                "provider_id": "heat",
                "result_digest": SHA,
                "evidence": (ev("h"),),
            },
        ),
        "profile": {
            "profile_id": "profile",
            "profile_revision": "1",
            "source_digest": SHA,
            "permitted_substrate_ids": ("substrate",),
            "permitted_filler_lot_ids": ("filler-1",),
            "permitted_process_ids": ("process-1",),
            "criteria": (
                {
                    "criterion_id": "dilution-rule",
                    "metric_kind": "dilution",
                    "metric_id": "dilution-fraction",
                    "unit_token": "1",
                    "aggregation": "replicate_mean",
                    "minimum_inclusive": 0.0,
                    "maximum_inclusive": 0.2,
                    "uncertainty_policy": "interval_must_fit",
                    "minimum_replicates": 2,
                    "missing_disposition": "insufficient_evidence",
                    "description": "caller rule",
                },
                {
                    "criterion_id": "thickness-rule",
                    "metric_kind": "layer_thickness",
                    "metric_id": "thickness",
                    "unit_token": "m",
                    "aggregation": "replicate_minimum",
                    "minimum_inclusive": 0.002,
                    "maximum_inclusive": None,
                    "uncertainty_policy": "point_value",
                    "minimum_replicates": 2,
                    "missing_disposition": "insufficient_evidence",
                    "description": "caller rule",
                },
            ),
            "profile_reviewed": True,
            "evidence": (ev("profile"),),
        },
        "substrate_filler_process_layer_and_pass_identity_reviewed": True,
        "dilution_composition_thickness_ferrite_bond_continuity_and_nde_reviewed": True,
        "measurement_units_uncertainty_methods_and_provenance_reviewed": True,
        "heat_history_time_temperature_and_sequence_reviewed": True,
        "caller_profile_authority_and_criteria_reviewed": True,
        "evidence": (ev("assessment"),),
    }
    data.update(changes)
    return OverlayCladdingCampaign.model_validate(data)


def test_campaign_accepts_only_caller_criteria():
    result = assess_overlay_cladding(payload())
    assert result.disposition == "accept"
    assert not result.automatic_material_compatibility_or_qualification_claim
    assert not result.corrosion_life_or_standard_acceptance_claim


def test_caller_limit_rejects_and_identity_mismatch_reviews():
    base = payload()
    criteria = list(base.profile.criteria)
    criteria[0] = criteria[0].model_copy(update={"maximum_inclusive": 0.09})
    assert (
        assess_overlay_cladding(
            base.model_copy(update={"profile": base.profile.model_copy(update={"criteria": tuple(criteria)})})
        ).disposition
        == "reject"
    )
    assert assess_overlay_cladding(payload(substrate_id="other")).disposition == "review"


def test_missing_exact_unit_or_replicate_is_insufficient_and_links_are_strict():
    rows = tuple(row for row in payload().measurements if row.measurement_id != "dilution-fraction-2")
    assert assess_overlay_cladding(payload(measurements=rows)).disposition == "insufficient_evidence"
    rows = list(payload().measurements)
    rows[0] = rows[0].model_copy(update={"layer_id": "missing"})
    with pytest.raises(ValidationError, match="declared layers"):
        payload(measurements=tuple(rows))


def test_digest_is_deterministic_and_tamper_evident():
    first = assess_overlay_cladding(payload())
    assert first.result_digest == assess_overlay_cladding(payload()).result_digest
    assert OverlayCladdingCampaignResult.model_validate_json(first.model_dump_json()) == first
    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        OverlayCladdingCampaignResult.model_validate(changed)
