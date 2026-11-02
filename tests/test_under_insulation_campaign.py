import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.under_insulation_campaign import (
    CUIEvidenceReceipt,
    UnderInsulationCampaignAssessment,
    UnderInsulationCampaignReport,
    cui_evidence_receipt,
    specifications,
    under_insulation_campaign,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored CUI campaign"}


def digest(character):
    return character * 64


def event(index, kind, **updates):
    is_repair = kind in ("repair", "reinstatement")
    row = {
        "event_id": f"event-{kind}",
        "sequence_index": index,
        "event_kind": kind,
        "start_time_s": index * 100.0,
        "end_time_s": (index + 1) * 100.0,
        "contractor_or_provider_id": "provider-1",
        "procedure_id": f"procedure-{kind}",
        "activity_definition": f"caller {kind} activity",
        "resulting_insulation_condition_id": "insulation-repaired" if is_repair else None,
        "resulting_jacketing_condition_id": "jacketing-repaired" if is_repair else None,
        "resulting_coating_condition_id": "coating-repaired" if is_repair else None,
        "event_configuration_digest": digest("a"),
        "event_record_digest": digest("b"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def coverage(accessed=80.0, unit="m2"):
    return {
        "access_region_id": "region-1",
        "access_event_id": "event-access",
        "physical_location_definition": "caller zone segment one",
        "coordinate_frame_id": "frame-1",
        "target_extent": 100.0,
        "accessed_extent": accessed,
        "extent_unit_token": unit,
        "coverage_uncertainty": 1.0,
        "overlap_group_id": "nonoverlap-group-1",
        "unaccessed_basis": None if accessed == 100.0 else "insulation not removed in remaining area",
        "coverage_record_digest": digest("c"),
        "evidence": (EVIDENCE,),
    }


def observation(index, category, metric=None, value=None, unit=None, **updates):
    quantitative = metric is not None
    row = {
        "observation_id": f"observation-{index}",
        "inspection_event_id": "event-inspection",
        "access_region_id": "region-1",
        "observation_category": category,
        "physical_location_definition": f"caller point {index} inside accessed region",
        "coordinate_frame_id": "frame-1",
        "orientation_definition": "surface normal",
        "method_id": f"method-{category}",
        "method_revision": "rev-1",
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}" if quantitative else None,
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 0.1 if quantitative else None,
        "uncertainty_basis": "caller uncertainty budget" if quantitative else None,
        "reported_finding": f"caller-reported {category} finding",
        "caller_disposition_id": None,
        "source_group_id": f"source-group-{index}",
        "independence_group_id": f"independence-group-{index}",
        "provider_id": "inspection-provider",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("d"),
        "raw_data_digest": digest("0123"[index]),
        "observation_record_digest": digest("89ab"[index]),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def observations(thickness=9.0, thickness_unit="mm"):
    return (
        observation(0, "moisture", "moisture_fraction", 0.1, "1"),
        observation(1, "visual"),
        observation(2, "thickness", "remaining_thickness", thickness, thickness_unit),
        observation(3, "nde"),
    )


def campaign_criterion():
    return {
        "criterion_id": "coverage-criterion",
        "criterion_source": "campaign",
        "campaign_metric": "coverage_fraction",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 0.8,
        "reject_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller CUI coverage criterion",
    }


def thickness_criterion():
    return {
        "criterion_id": "thickness-criterion",
        "criterion_source": "observation",
        "observation_category": "thickness",
        "observation_metric_id": "remaining_thickness",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 8.0,
        "reject_limit": 6.0,
        "unit_token": "mm",
        "criterion_basis": "caller measured-thickness criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_event_kinds": ("access", "inspection", "repair"),
        "required_observation_categories": ("moisture", "visual", "thickness", "nde"),
        "criteria": (campaign_criterion(), thickness_criterion()),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("e"),
        "caller_acceptance_authority": "caller CUI review group",
        "corrosion_rate_inference_claimed": False,
        "remaining_life_claimed": False,
        "hidden_area_extrapolation_claimed": False,
        "risk_or_pod_claimed": False,
        "built_in_code_or_standard_acceptance_used": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "scope": {
            "zone_id": "zone-1",
            "component_or_circuit_id": "circuit-1",
            "physical_scope_definition": "caller insulated piping zone",
            "coordinate_frame_id": "frame-1",
            "substrate_material_id": "material-1",
            "substrate_material_condition_id": "condition-1",
            "service_id": "service-1",
            "service_medium_definition": "caller service medium",
            "minimum_service_temperature_K": 300.0,
            "maximum_service_temperature_K": 400.0,
            "insulation_system_id": "insulation-1",
            "insulation_material_id": "insulation-material-1",
            "insulation_condition_id": "insulation-before-access",
            "jacketing_system_id": "jacketing-1",
            "jacketing_condition_id": "jacketing-before-access",
            "coating_system_id": "coating-1",
            "coating_condition_id": "coating-before-access",
            "external_environment_id": "environment-1",
            "external_environment_definition": "caller outdoor environment",
            "scope_configuration_digest": digest("f"),
            "evidence": (EVIDENCE,),
        },
        "events": (event(0, "access"), event(1, "inspection"), event(2, "repair")),
        "coverage_regions": (coverage(),),
        "observations": observations(),
        "caller_profile": profile(),
        "zone_insulation_jacketing_coating_material_service_environment_reviewed": True,
        "ordered_access_inspection_repair_events_reviewed": True,
        "access_coverage_regions_overlap_and_units_reviewed": True,
        "moisture_visual_thickness_nde_observations_reviewed": True,
        "locations_methods_units_uncertainty_and_findings_reviewed": True,
        "source_independence_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return UnderInsulationCampaignAssessment.model_validate(row)


def test_campaign_accepts_only_caller_profile_without_hidden_area_or_risk_claims():
    result = under_insulation_campaign(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["metric_values"]["campaign:coverage_fraction"] == 0.8
    assert result.values["diagnostics"]["unaccessed_region_ids"] == ["region-1"]
    assert result.values["corrosion_rate_or_remaining_life"] is False
    assert result.values["hidden_area_extrapolated"] is False
    assert result.values["risk_pod_or_standard_acceptance"] is False
    receipt = CUIEvidenceReceipt.model_validate(result.values["downstream_receipt"])
    assert receipt.assessment_id == "assessment-1"
    assert receipt.coverage_fraction == 0.8
    assert receipt.input_digest == result.values["input_digest"]
    assert receipt.report_digest == result.values["report_digest"]


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = under_insulation_campaign(payload(coverage_regions=(coverage(accessed=70),)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = under_insulation_campaign(payload(observations=observations(thickness=5)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_category_invalid_event_and_exact_unit_conflict_are_insufficient():
    no_nde = tuple(row for row in observations() if row["observation_category"] != "nde")
    result = under_insulation_campaign(payload(observations=no_nde))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["missing_required_observation_categories"] == ["nde"]

    invalid_event = event(
        1, "inspection", record_valid=False, invalid_or_missing_basis="review rejected event"
    )
    result = under_insulation_campaign(
        payload(events=(event(0, "access"), invalid_event, event(2, "repair")))
    )
    assert result.status == "needs_data"

    result = under_insulation_campaign(payload(observations=observations(thickness_unit="in")))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["criterion_unit_conflict_ids"] == ["thickness-criterion"]


def test_event_region_links_and_report_digest_are_strict():
    unordered = (event(1, "inspection"), event(0, "access"), event(2, "repair"))
    with pytest.raises(ValueError, match="sequence order"):
        payload(events=unordered)

    bad_region = {**coverage(), "access_event_id": "event-inspection"}
    with pytest.raises(ValueError, match="reference access events"):
        payload(coverage_regions=(bad_region,))

    first = under_insulation_campaign(payload())
    second = under_insulation_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    UnderInsulationCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        UnderInsulationCampaignReport.model_validate(tampered)


def test_cui_receipt_is_bound_to_input_and_report():
    assessment = payload()
    result = under_insulation_campaign(assessment)
    report = UnderInsulationCampaignReport.model_validate(result.values)
    receipt = cui_evidence_receipt(assessment, report)
    CUIEvidenceReceipt.model_validate(receipt.model_dump())
    altered_assessment = payload(coverage_regions=(coverage(accessed=90.0),))
    with pytest.raises(ValueError, match="input digest"):
        cui_evidence_receipt(altered_assessment, report)
    altered_receipt = receipt.model_dump()
    altered_receipt["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        CUIEvidenceReceipt.model_validate(altered_receipt)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "degradation.under_insulation"
    assert spec.source_ids == (
        "authored_cui_inspection_evidence_campaign_audit",
        "authored_cui_digest_bound_downstream_evidence_receipt",
    )
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="campaign clock")
        )
