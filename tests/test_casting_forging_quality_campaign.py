import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.casting_forging_quality_campaign import (
    CastingForgingQualityCampaignAssessment,
    CastingForgingQualityCampaignReport,
    casting_forging_quality_campaign,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored quality campaign"}


def digest(character):
    return character * 64


def treatment(index=1, **updates):
    row = {
        "treatment_id": f"treatment-{index}",
        "sequence_index": 0,
        "treatment_type": "caller heat-treatment description",
        "furnace_or_provider_id": "furnace-1",
        "start_time_s": 0.0,
        "end_time_s": 3600.0,
        "minimum_recorded_temperature_K": 1000.0,
        "maximum_recorded_temperature_K": 1010.0,
        "temperature_uncertainty_K": 2.0,
        "cooling_route_definition": "caller controlled cooling route",
        "controller_data_digest": digest("a"),
        "treatment_record_digest": digest("b"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def product(index, kind):
    forging = kind == "forging"
    return {
        "product_id": f"product-{index}",
        "product_kind": kind,
        "heat_id": f"heat-{index}",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "product_form_descriptor": f"caller {kind} product form",
        "manufacturing_route_id": f"route-{index}",
        "manufacturing_route_revision": "rev-1",
        "route_configuration_digest": digest("c"),
        "forging_ratio": 3.0 if forging else None,
        "forging_ratio_definition": "caller area-ratio definition" if forging else None,
        "forging_ratio_unit_token": "1" if forging else None,
        "casting_process_id": None if forging else "casting-process-1",
        "casting_process_definition": None if forging else "caller casting process description",
        "heat_treatments": (treatment(index),),
        "product_record_digest": digest("d"),
        "evidence": (EVIDENCE,),
    }


def sample(index):
    return {
        "sample_id": f"sample-{index}",
        "product_id": f"product-{index}",
        "sampling_plan_id": "sampling-plan-1",
        "physical_location_definition": f"caller location {index}",
        "orientation_id": "longitudinal",
        "thickness_or_depth_coordinate": 0.5,
        "coordinate_unit_token": "fraction",
        "replicate_group_id": "replicate-group-1",
        "source_group_id": f"source-group-{index}",
        "independence_group_id": f"independence-group-{index}",
        "sampling_record_digest": digest("e"),
        "evidence": (EVIDENCE,),
    }


def observation(index, category, metric=None, value=None, unit=None, **updates):
    quantitative = metric is not None
    character = "0123456789abcdef"[index]
    row = {
        "observation_id": f"observation-{index}",
        "product_id": "product-1",
        "sample_id": "sample-1",
        "observation_category": category,
        "examination_or_test_method_id": f"method-{category}",
        "method_revision": "rev-1",
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}" if quantitative else None,
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 5.0 if quantitative else None,
        "uncertainty_basis": "caller uncertainty budget" if quantitative else None,
        "reported_finding": f"caller-reported {category} finding",
        "caller_disposition_id": None,
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("f"),
        "raw_data_digest": digest(character),
        "observation_record_digest": digest("0123456789abcdef"[(index + 8) % 16]),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def observations(strength=450.0, strength_unit="MPa"):
    return (
        observation(0, "dimensional", "dimension_deviation", 0.2, "mm"),
        observation(1, "surface"),
        observation(2, "internal"),
        observation(3, "nde"),
        observation(4, "macro"),
        observation(5, "micro"),
        observation(6, "chemistry", "element_fraction", 0.1, "%"),
        observation(7, "mechanical", "yield_strength", strength, strength_unit),
    )


def campaign_criterion(identifier, metric, direction, accept, reject, unit):
    return {
        "criterion_id": identifier,
        "criterion_source": "campaign",
        "campaign_metric": metric,
        "aggregation": "minimum",
        "direction": direction,
        "accept_limit": accept,
        "reject_limit": reject,
        "unit_token": unit,
        "criterion_basis": "caller-authored quality criterion",
    }


def observation_criterion():
    return {
        "criterion_id": "strength-criterion",
        "criterion_source": "observation",
        "observation_category": "mechanical",
        "observation_metric_id": "yield_strength",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 400.0,
        "reject_limit": 300.0,
        "unit_token": "MPa",
        "criterion_basis": "caller-authored strength criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_product_kinds": ("forging", "casting"),
        "required_observation_categories": (
            "dimensional",
            "surface",
            "internal",
            "nde",
            "macro",
            "micro",
            "chemistry",
            "mechanical",
        ),
        "criteria": (
            campaign_criterion("sample-count", "sample_count", "minimum", 2, 1, "count"),
            campaign_criterion(
                "independent-count", "independent_source_group_count", "minimum", 2, 1, "count"
            ),
            observation_criterion(),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("a"),
        "caller_acceptance_authority": "caller material review group",
        "built_in_specification_table_used": False,
        "minimum_forging_ratio_embedded": False,
        "allowable_defect_rule_embedded": False,
        "material_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "products": (product(1, "forging"), product(2, "casting")),
        "samples": (sample(1), sample(2)),
        "observations": observations(),
        "caller_profile": profile(),
        "product_heat_route_and_process_identity_reviewed": True,
        "forging_ratio_or_casting_process_basis_reviewed": True,
        "heat_treatment_sequence_and_digests_reviewed": True,
        "sampling_location_orientation_and_groups_reviewed": True,
        "observation_method_units_uncertainty_and_findings_reviewed": True,
        "replicate_source_and_independence_claims_reviewed": True,
        "provider_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return CastingForgingQualityCampaignAssessment.model_validate(row)


def test_campaign_accepts_only_caller_profile_without_material_qualification():
    result = casting_forging_quality_campaign(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["metric_values"]["observation:mechanical:yield_strength"] == 450.0
    assert result.values["specification_or_forging_ratio_limit_embedded"] is False
    assert result.values["automatic_defect_acceptance"] is False
    assert result.values["material_qualification"] is False


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = casting_forging_quality_campaign(payload(observations=observations(strength=350)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = casting_forging_quality_campaign(payload(observations=observations(strength=250)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_category_invalid_treatment_and_exact_unit_conflict_are_insufficient():
    without_nde = tuple(row for row in observations() if row["observation_category"] != "nde")
    result = casting_forging_quality_campaign(payload(observations=without_nde))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["missing_required_observation_categories"] == ["nde"]

    products = list(payload().model_dump()["products"])
    products[0]["heat_treatments"][0]["record_valid"] = False
    products[0]["heat_treatments"][0]["invalid_or_missing_basis"] = "review rejected cycle"
    result = casting_forging_quality_campaign(payload(products=tuple(products)))
    assert result.status == "needs_data"

    result = casting_forging_quality_campaign(payload(observations=observations(strength_unit="ksi")))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["criterion_unit_conflict_ids"] == ["strength-criterion"]


def test_route_specific_identity_linkage_and_report_digest_are_strict():
    bad = product(1, "forging")
    bad["casting_process_id"] = "not-permitted"
    bad["casting_process_definition"] = "not-permitted"
    with pytest.raises(ValueError, match="forging products require only"):
        payload(products=(bad, product(2, "casting")))

    linked = list(observations())
    linked[0] = {**linked[0], "sample_id": "sample-2", "product_id": "product-1"}
    with pytest.raises(ValueError, match="match their declared sample"):
        payload(observations=tuple(linked))

    first = casting_forging_quality_campaign(payload())
    second = casting_forging_quality_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    CastingForgingQualityCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        CastingForgingQualityCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "materials.casting_forging_quality"
    assert spec.source_ids == ("authored_casting_forging_quality_campaign_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="campaign clock")
        )
