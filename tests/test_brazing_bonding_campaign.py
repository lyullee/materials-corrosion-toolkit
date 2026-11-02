from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.brazing_bonding_campaign import (
    SOURCE_ID,
    BrazingBondingCampaignResult,
    BrazingBondingProductionCampaign,
    assess_brazing_bonding_campaign,
    specifications,
)
from matintegrity.registry import ModelRegistry

S = "a" * 64


def e(x):
    return {"source_id": x, "origin": "user_declared", "citation": x, "sha256": S}


def payload(**u):
    d = {
        "assessment_id": "a",
        "asset_id": "asset",
        "location_id": "loc",
        "campaign_id": "c",
        "joints": (
            {
                "joint_id": "j",
                "process_kind": "brazing",
                "base_material_lot_ids": ("b1", "b2"),
                "filler_lot_id": "f1",
                "surface_preparation_id": "prep",
                "joint_geometry_id": "geom",
                "fitup_gap_m": 0.0001,
                "fitup_gap_standard_uncertainty_m": 0.00001,
                "atmosphere_id": "atm",
                "flux_lot_id": "flux",
                "fitup_and_identity_reviewed": True,
                "evidence": (e("j"),),
            },
        ),
        "cycle_history": (
            {
                "interval_id": "h",
                "sequence_position": 1,
                "interval_kind": "braze_heat",
                "start_time_s": 0.0,
                "end_time_s": 10.0,
                "minimum_temperature_k": 500.0,
                "maximum_temperature_k": 700.0,
                "minimum_pressure_pa_abs": 100000.0,
                "maximum_pressure_pa_abs": 100000.0,
                "atmosphere_id": "atm",
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("h"),),
            },
        ),
        "measurements": tuple(
            {
                "measurement_id": f"m{i}",
                "joint_id": "j",
                "replicate_group_id": "g",
                "metric_kind": "strength",
                "metric_id": "strength",
                "metric_definition": "caller strength",
                "unit_token": "Pa",
                "status": "available",
                "value": v,
                "standard_uncertainty": 1e5,
                "method_id": "m",
                "provider_id": "p",
                "provider_revision": "1",
                "input_digest": S,
                "result_digest": S,
                "evidence": (e(f"m{i}"),),
            }
            for i, v in ((1, 5e6), (2, 5.2e6))
        ),
        "profile": {
            "profile_id": "pr",
            "profile_revision": "1",
            "source_digest": S,
            "permitted_base_lot_ids": ("b1", "b2"),
            "permitted_filler_lot_ids": ("f1",),
            "permitted_surface_preparation_ids": ("prep",),
            "permitted_joint_geometry_ids": ("geom",),
            "minimum_fitup_gap_m": 0.00005,
            "maximum_fitup_gap_m": 0.0002,
            "fitup_uncertainty_policy": "interval_must_fit",
            "permitted_atmosphere_ids": ("atm",),
            "permitted_flux_lot_ids": ("flux",),
            "minimum_cycle_temperature_k": 400.0,
            "maximum_cycle_temperature_k": 800.0,
            "maximum_cycle_pressure_pa_abs": 200000.0,
            "maximum_interval_duration_s": 20.0,
            "criteria": (
                {
                    "criterion_id": "strength-rule",
                    "metric_kind": "strength",
                    "metric_id": "strength",
                    "unit_token": "Pa",
                    "aggregation": "replicate_mean",
                    "minimum_inclusive": 4e6,
                    "maximum_inclusive": None,
                    "uncertainty_policy": "interval_must_fit",
                    "minimum_replicates": 2,
                    "missing_disposition": "insufficient_evidence",
                    "description": "caller",
                },
            ),
            "profile_reviewed": True,
            "evidence": (e("pr"),),
        },
        "material_consumable_surface_prep_fitup_atmosphere_flux_and_geometry_reviewed": True,
        "ordered_heat_pressure_cure_cycle_reviewed": True,
        "destructive_nde_leak_strength_continuity_measurements_reviewed": True,
        "units_uncertainty_methods_provenance_and_digests_reviewed": True,
        "caller_profile_authority_and_criteria_reviewed": True,
        "evidence": (e("a"),),
    }
    d.update(u)
    return BrazingBondingProductionCampaign.model_validate(d)


def test_accept_and_source_spec():
    r = assess_brazing_bonding_campaign(payload())
    assert r.disposition == "accept"
    assert not r.automatic_material_compatibility_or_qualification_claim
    assert specifications()[0].source_ids == (SOURCE_ID,)


def test_reject_review_insufficient():
    b = payload()
    crit = b.profile.criteria[0].model_copy(update={"minimum_inclusive": 6e6})
    assert (
        assess_brazing_bonding_campaign(
            b.model_copy(update={"profile": b.profile.model_copy(update={"criteria": (crit,)})})
        ).disposition
        == "reject"
    )
    j = b.joints[0].model_copy(update={"filler_lot_id": "other"})
    assert assess_brazing_bonding_campaign(b.model_copy(update={"joints": (j,)})).disposition == "review"
    assert (
        assess_brazing_bonding_campaign(
            payload(units_uncertainty_methods_provenance_and_digests_reviewed=False)
        ).disposition
        == "insufficient_evidence"
    )


def test_digest_and_context():
    r = assess_brazing_bonding_campaign(payload())
    assert r.result_digest == assess_brazing_bonding_campaign(payload()).result_digest
    q = deepcopy(r.model_dump(mode="python"))
    q["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        BrazingBondingCampaignResult.model_validate(q)
    reg = ModelRegistry()
    reg.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        reg.run(
            specifications()[0].model_id,
            payload(),
            RunContext(asset_id="x", location_id="loc", time_basis="t"),
        )
