from matintegrity.models.repair_welding_campaign import (
    SOURCE_ID,
    RepairWeldingCampaign,
    assess_repair_welding,
    specifications,
)

S = "a" * 64


def e(x):
    return {"source_id": x, "origin": "user_declared", "citation": x, "sha256": S}


def p(**u):
    d = {
        "assessment_id": "a",
        "asset_id": "asset",
        "location_id": "l",
        "identity": {
            "component_id": "comp",
            "repair_id": "r",
            "weld_id": "w",
            "wps_id": "wps",
            "wps_revision": "1",
            "welder_ids": ("welder",),
            "base_heat_ids": ("h",),
            "consumable_lot_ids": ("f",),
            "repair_sequence_number": 1,
            "reviewed": True,
            "evidence": (e("id"),),
        },
        "excavations": (
            {
                "defect_id": "d",
                "removal_method_id": "grind",
                "excavation_geometry_id": "g",
                "length_m": 0.1,
                "depth_m": 0.005,
                "width_m": 0.02,
                "standard_uncertainty_m": 0.0001,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("d"),),
            },
        ),
        "events": (
            {
                "event_id": "ev",
                "sequence_position": 1,
                "event_kind": "deposition",
                "start_time_s": 0.0,
                "end_time_s": 10.0,
                "minimum_temperature_k": 300.0,
                "maximum_temperature_k": 500.0,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("ev"),),
            },
        ),
        "observations": (
            {
                "observation_id": "nde",
                "metric_kind": "nde",
                "metric_id": "indications",
                "unit_token": "count",
                "status": "available",
                "value": 0.0,
                "standard_uncertainty": 0.0,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("nde"),),
            },
        ),
        "profile": {
            "profile_id": "pr",
            "profile_revision": "1",
            "source_digest": S,
            "permitted_wps_ids": ("wps",),
            "permitted_base_heat_ids": ("h",),
            "permitted_consumable_lots": ("f",),
            "maximum_repair_count": 2,
            "maximum_excavation_depth_m": 0.01,
            "maximum_event_temperature_k": 600.0,
            "criteria": (
                {
                    "criterion_id": "nde-rule",
                    "metric_kind": "nde",
                    "metric_id": "indications",
                    "unit_token": "count",
                    "minimum_inclusive": 0.0,
                    "maximum_inclusive": 0.0,
                    "uncertainty_policy": "interval_must_fit",
                    "missing_disposition": "insufficient_evidence",
                },
            ),
            "profile_reviewed": True,
            "evidence": (e("pr"),),
        },
        "identity_and_repair_history_reviewed": True,
        "defect_removal_excavation_geometry_reviewed": True,
        "thermal_deposition_interpass_and_pwht_sequence_reviewed": True,
        "observation_units_uncertainty_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "evidence": (e("a"),),
    }
    d.update(u)
    return RepairWeldingCampaign.model_validate(d)


def test_campaign():
    r = assess_repair_welding(p())
    assert r.disposition == "accept"
    assert not r.code_wps_qualification_crack_growth_or_remaining_life_claim
    assert specifications()[0].source_ids == (SOURCE_ID,)


def test_reject_insufficient():
    b = p()
    i = b.identity.model_copy(update={"repair_sequence_number": 3})
    assert assess_repair_welding(b.model_copy(update={"identity": i})).disposition == "reject"
    assert assess_repair_welding(p(caller_profile_reviewed=False)).disposition == "insufficient_evidence"
