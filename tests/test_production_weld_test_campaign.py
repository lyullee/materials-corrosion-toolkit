from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.production_weld_test_campaign import (
    SOURCE_ID,
    ProductionWeldTestCampaign,
    ProductionWeldTestCampaignResult,
    assess_production_weld_tests,
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
        "welds": (
            {
                "weld_id": "w",
                "joint_id": "j",
                "wps_id": "wps",
                "wps_revision": "1",
                "welder_ids": ("welder",),
                "consumable_lot_ids": ("filler",),
                "base_material_heat_ids": ("h1", "h2"),
                "identity_reviewed": True,
                "evidence": (e("w"),),
            },
        ),
        "specimens": tuple(
            {
                "specimen_id": f"s{i}",
                "coupon_id": f"coupon{i}",
                "weld_id": "w",
                "extraction_location_id": f"x{i}",
                "extraction_orientation": "transverse",
                "source_group_id": f"source{i}",
                "independence_group_id": f"ind{i}",
                "extraction_reviewed": True,
                "evidence": (e(f"s{i}"),),
            }
            for i in (1, 2)
        ),
        "measurements": tuple(
            {
                "measurement_id": f"m{i}",
                "specimen_id": f"s{i}",
                "replicate_group_id": "g",
                "test_kind": "tensile",
                "metric_id": "strength",
                "metric_definition": "caller strength",
                "unit_token": "Pa",
                "status": "available",
                "value": v,
                "standard_uncertainty": 1e5,
                "method_id": "method",
                "provider_id": "lab",
                "provider_revision": "1",
                "input_digest": S,
                "result_digest": S,
                "evidence": (e(f"m{i}"),),
            }
            for i, v in ((1, 5e6), (2, 5.2e6))
        ),
        "profile": {
            "profile_id": "p",
            "profile_revision": "1",
            "source_digest": S,
            "permitted_wps_ids": ("wps",),
            "permitted_consumable_lot_ids": ("filler",),
            "permitted_base_material_heat_ids": ("h1", "h2"),
            "criteria": (
                {
                    "criterion_id": "strength-rule",
                    "test_kind": "tensile",
                    "metric_id": "strength",
                    "unit_token": "Pa",
                    "aggregation": "replicate_mean",
                    "minimum_inclusive": 4e6,
                    "maximum_inclusive": None,
                    "uncertainty_policy": "interval_must_fit",
                    "minimum_replicates": 2,
                    "minimum_independent_source_groups": 2,
                    "missing_disposition": "insufficient_evidence",
                    "description": "caller",
                },
            ),
            "profile_reviewed": True,
            "evidence": (e("p"),),
        },
        "weld_joint_wps_welder_consumable_and_heat_identity_reviewed": True,
        "coupon_specimen_extraction_location_and_orientation_reviewed": True,
        "test_metric_units_uncertainty_status_and_provenance_reviewed": True,
        "replicate_source_and_independence_groups_reviewed": True,
        "caller_profile_authority_and_criteria_reviewed": True,
        "evidence": (e("a"),),
    }
    d.update(u)
    return ProductionWeldTestCampaign.model_validate(d)


def test_accept_spec_source():
    r = assess_production_weld_tests(payload())
    assert r.disposition == "accept"
    assert not r.wps_or_code_qualification_claim
    assert specifications()[0].source_ids == (SOURCE_ID,)


def test_reject_review_insufficient():
    b = payload()
    c = b.profile.criteria[0].model_copy(update={"minimum_inclusive": 6e6})
    assert (
        assess_production_weld_tests(
            b.model_copy(update={"profile": b.profile.model_copy(update={"criteria": (c,)})})
        ).disposition
        == "reject"
    )
    w = b.welds[0].model_copy(update={"wps_id": "other"})
    assert assess_production_weld_tests(b.model_copy(update={"welds": (w,)})).disposition == "review"
    assert (
        assess_production_weld_tests(
            payload(replicate_source_and_independence_groups_reviewed=False)
        ).disposition
        == "insufficient_evidence"
    )


def test_links_digest_tamper():
    b = payload()
    m = b.measurements[0].model_copy(update={"specimen_id": "missing"})
    with pytest.raises(ValidationError, match="declared specimens"):
        payload(measurements=(m, b.measurements[1]))
    r = assess_production_weld_tests(payload())
    q = deepcopy(r.model_dump(mode="python"))
    q["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        ProductionWeldTestCampaignResult.model_validate(q)


@pytest.mark.parametrize(
    "aggregation,lower,upper",
    [
        ("replicate_minimum", 4e6, 5.201e6),
        ("replicate_maximum", 5.199e6, 6e6),
    ],
)
def test_extreme_aggregation_uses_interval_extrema_not_mean_uncertainty(aggregation, lower, upper):
    base = payload()
    measurements = (
        base.measurements[0].model_copy(update={"standard_uncertainty": 1e6}),
        base.measurements[1].model_copy(update={"standard_uncertainty": 1e3}),
    )
    criterion = base.profile.criteria[0].model_copy(update={"aggregation": aggregation})
    assessment = payload(
        measurements=measurements, profile=base.profile.model_copy(update={"criteria": (criterion,)})
    )
    finding = assess_production_weld_tests(assessment).findings[0]
    assert finding.evaluated_lower == pytest.approx(lower)
    assert finding.evaluated_upper == pytest.approx(upper)
    from matintegrity.contracts import RunContext
    from matintegrity.registry import ModelRegistry

    registry = ModelRegistry()
    registry.register(specifications()[0])
    context = RunContext(asset_id=assessment.asset_id, location_id=assessment.location_id, time_basis="test")
    direct = registry.run("welding.production_weld_test_campaign_evidence", assessment, context)
    serialized = registry.run_json(
        "welding.production_weld_test_campaign_evidence", assessment.model_dump_json(), context
    )
    assert direct.model_dump() == serialized.model_dump()


def test_different_source_labels_do_not_override_shared_independence_group():
    base = payload()
    dependent = base.specimens[1].model_copy(
        update={"independence_group_id": base.specimens[0].independence_group_id}
    )
    result = assess_production_weld_tests(payload(specimens=(base.specimens[0], dependent)))
    assert result.disposition == "insufficient_evidence"


@pytest.mark.parametrize("status", ["missing", "invalid"])
def test_absent_measurement_cannot_retain_result_digest(status):
    raw = payload().model_dump(mode="python")
    row = raw["measurements"][0]
    row.update(status=status, value=None, standard_uncertainty=None,
               missing_or_invalid_basis="No usable quantitative result")
    with pytest.raises(ValidationError, match="no value"):
        ProductionWeldTestCampaign(**raw)
    row["result_digest"] = None
    request = ProductionWeldTestCampaign(**raw)
    assert request.measurements[0].result_digest is None
