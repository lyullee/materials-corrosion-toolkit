from matintegrity.models.chemical_cleaning_campaign import (
    SOURCE_ID,
    ChemicalCleaningCampaign,
    assess_chemical_cleaning,
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
        "campaign_id": "c",
        "material_id": "m",
        "area_ids": ("a1",),
        "circuit_id": "cir",
        "precondition_id": "pre",
        "batches": (
            {
                "batch_id": "b",
                "composition": ({"component_id": "acid", "concentration": 0.1, "unit_token": "kg/kg"},),
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("b"),),
            },
        ),
        "events": (
            {
                "event_id": "fill",
                "sequence_position": 1,
                "event_kind": "fill",
                "batch_id": "b",
                "start_time_s": 0.0,
                "end_time_s": 10.0,
                "minimum_temperature_k": 290.0,
                "maximum_temperature_k": 320.0,
                "minimum_pressure_pa_abs": 1e5,
                "maximum_pressure_pa_abs": 2e5,
                "flow_m3_s": 0.01,
                "ph": 2.0,
                "conductivity_s_m": 1.0,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("event"),),
            },
        ),
        "measurements": (
            {
                "measurement_id": "res",
                "sample_location_id": "x",
                "metric_kind": "residue",
                "metric_id": "residue",
                "unit_token": "kg/m2",
                "status": "available",
                "value": 0.01,
                "standard_uncertainty": 0.001,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("res"),),
            },
        ),
        "waste_records": (
            {
                "waste_record_id": "w",
                "waste_stream_id": "ws",
                "disposition_method_id": "method",
                "destination_id": "dest",
                "manifest_digest": S,
                "record_reviewed": True,
                "evidence": (e("w"),),
            },
        ),
        "profile": {
            "profile_id": "pr",
            "profile_revision": "1",
            "source_digest": S,
            "permitted_material_ids": ("m",),
            "permitted_precondition_ids": ("pre",),
            "permitted_component_units": ("kg/kg",),
            "maximum_event_temperature_k": 350.0,
            "maximum_pressure_pa_abs": 3e5,
            "criteria": (
                {
                    "criterion_id": "r",
                    "metric_kind": "residue",
                    "metric_id": "residue",
                    "unit_token": "kg/m2",
                    "minimum_inclusive": 0.0,
                    "maximum_inclusive": 0.02,
                    "uncertainty_policy": "interval_must_fit",
                    "missing_disposition": "insufficient_evidence",
                },
            ),
            "profile_reviewed": True,
            "evidence": (e("pr"),),
        },
        "identity_precondition_batch_and_composition_reviewed": True,
        "event_sequence_state_units_and_time_reviewed": True,
        "measurement_uncertainty_provenance_and_digest_reviewed": True,
        "waste_disposition_evidence_reviewed": True,
        "caller_profile_reviewed": True,
        "evidence": (e("a"),),
    }
    d.update(u)
    return ChemicalCleaningCampaign.model_validate(d)


def test_campaign():
    r = assess_chemical_cleaning(p())
    assert r.disposition == "accept"
    assert not r.automatic_kinetics_corrosion_compatibility_or_standard_acceptance_claim
    assert specifications()[0].source_ids == (SOURCE_ID,)


def test_reject_and_insufficient():
    b = p()
    ev = b.events[0].model_copy(update={"maximum_temperature_k": 400.0})
    assert assess_chemical_cleaning(b.model_copy(update={"events": (ev,)})).disposition == "reject"
    assert (
        assess_chemical_cleaning(p(waste_disposition_evidence_reviewed=False)).disposition
        == "insufficient_evidence"
    )
