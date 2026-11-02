from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.surface_cleanliness_campaign import (
    SOURCE_ID,
    SurfaceCleanlinessCampaign,
    SurfaceCleanlinessResult,
    assess_surface_cleanliness,
    specifications,
)

S = "a" * 64


def e(x):
    return {"source_id": x, "origin": "user_declared", "citation": x, "sha256": S}


def payload(**u):
    d = {
        "assessment_id": "a",
        "asset_id": "asset",
        "location_id": "loc",
        "campaign_id": "c",
        "substrate_id": "steel",
        "area_ids": ("area",),
        "previous_coating_id": "old",
        "contaminant_ids": ("salt",),
        "preparation_events": (
            {
                "event_id": "event",
                "sequence_position": 1,
                "process_id": "blast",
                "start_time_s": 0.0,
                "end_time_s": 10.0,
                "ambient_temperature_k": 295.0,
                "surface_temperature_k": 300.0,
                "dewpoint_temperature_k": 290.0,
                "provider_id": "p",
                "result_digest": S,
                "evidence": (e("event"),),
            },
        ),
        "measurements": tuple(
            {
                "measurement_id": f"m{i}",
                "area_id": "area",
                "sample_location_id": f"x{i}",
                "replica_group_id": "g",
                "metric_kind": "soluble_salt",
                "metric_id": "salt",
                "metric_definition": "caller salt",
                "unit_token": "kg/m^2",
                "status": "available",
                "value": v,
                "standard_uncertainty": 1e-7,
                "method_id": "m",
                "provider_id": "p",
                "provider_revision": "1",
                "input_digest": S,
                "result_digest": S,
                "evidence": (e(f"m{i}"),),
            }
            for i, v in ((1, 1e-5), (2, 1.1e-5))
        ),
        "profile": {
            "profile_id": "p",
            "profile_revision": "1",
            "source_digest": S,
            "permitted_substrate_ids": ("steel",),
            "permitted_previous_coating_ids": ("old",),
            "permitted_contaminant_ids": ("salt",),
            "permitted_process_ids": ("blast",),
            "minimum_surface_above_dewpoint_k": 5.0,
            "criteria": (
                {
                    "criterion_id": "salt-rule",
                    "metric_kind": "soluble_salt",
                    "metric_id": "salt",
                    "unit_token": "kg/m^2",
                    "aggregation": "replica_mean",
                    "minimum_inclusive": 0.0,
                    "maximum_inclusive": 2e-5,
                    "uncertainty_policy": "interval_must_fit",
                    "minimum_replicas": 2,
                    "missing_disposition": "insufficient_evidence",
                    "description": "caller",
                },
            ),
            "profile_reviewed": True,
            "evidence": (e("profile"),),
        },
        "identity_and_area_mapping_reviewed": True,
        "preparation_event_order_process_and_environment_reviewed": True,
        "measurement_locations_replicas_units_uncertainty_and_provenance_reviewed": True,
        "caller_profile_authority_and_criteria_reviewed": True,
        "evidence": (e("a"),),
    }
    d.update(u)
    return SurfaceCleanlinessCampaign.model_validate(d)


def test_accept_spec():
    r = assess_surface_cleanliness(payload())
    assert r.disposition == "accept"
    assert not r.automatic_image_interpretation_or_standard_comparator_claim
    assert specifications()[0].source_ids == (SOURCE_ID,)


def test_reject_review_insufficient():
    b = payload()
    ev = b.preparation_events[0].model_copy(update={"surface_temperature_k": 292.0})
    assert (
        assess_surface_cleanliness(b.model_copy(update={"preparation_events": (ev,)})).disposition == "reject"
    )
    assert assess_surface_cleanliness(payload(substrate_id="other")).disposition == "review"
    assert (
        assess_surface_cleanliness(
            payload(measurement_locations_replicas_units_uncertainty_and_provenance_reviewed=False)
        ).disposition
        == "insufficient_evidence"
    )


def test_digest_links():
    b = payload()
    m = b.measurements[0].model_copy(update={"area_id": "missing"})
    with pytest.raises(ValidationError, match="declared areas"):
        payload(measurements=(m, b.measurements[1]))
    r = assess_surface_cleanliness(payload())
    q = deepcopy(r.model_dump(mode="python"))
    q["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        SurfaceCleanlinessResult.model_validate(q)
