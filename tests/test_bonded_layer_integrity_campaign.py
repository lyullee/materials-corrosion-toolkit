import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.bonded_layer_integrity_campaign import (
    BondedLayerIntegrityCampaignAssessment,
    BondedLayerIntegrityCampaignReport,
    bonded_layer_integrity_campaign,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored bonded-layer campaign"}


def digest(character):
    return character * 64


def process_event(index, kind, **updates):
    row = {
        "event_id": f"event-{index}",
        "sequence_index": index,
        "process_kind": kind,
        "process_step_id": f"step-{index}",
        "start_time_s": index * 100.0,
        "end_time_s": (index + 1) * 100.0,
        "minimum_recorded_temperature_K": 290.0 + index,
        "maximum_recorded_temperature_K": 300.0 + index,
        "expanded_temperature_uncertainty_K": 1.0,
        "applied_pressure": 1.0 if kind == "bonding" else None,
        "pressure_unit_token": "MPa" if kind == "bonding" else None,
        "expanded_pressure_uncertainty": 0.05 if kind == "bonding" else None,
        "process_configuration_digest": digest("a"),
        "process_record_digest": digest("b"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def assembly():
    return {
        "assembly_id": "assembly-1",
        "product_id": "product-1",
        "substrate_id": "substrate-1",
        "substrate_material_id": "substrate-material-1",
        "substrate_material_lot_id": "substrate-lot-1",
        "substrate_condition_id": "substrate-condition-1",
        "layer_id": "layer-1",
        "layer_material_id": "layer-material-1",
        "layer_material_lot_id": "layer-lot-1",
        "layer_condition_id": "layer-condition-1",
        "interface_id": "interface-1",
        "interface_definition": "caller substrate-to-layer interface definition",
        "bond_process_id": "bond-process-1",
        "bond_process_revision": "rev-1",
        "bond_process_provider_id": "provider-1",
        "bond_process_route_digest": digest("c"),
        "geometry": {
            "geometry_id": "geometry-1",
            "substrate_thickness": 10.0,
            "layer_nominal_thickness": 1.0,
            "bonded_area": 100.0,
            "thickness_unit_token": "mm",
            "area_unit_token": "cm2",
            "geometry_uncertainty": 0.05,
            "coordinate_frame_id": "frame-1",
            "geometry_record_digest": digest("d"),
        },
        "process_events": (
            process_event(0, "surface_preparation"),
            process_event(1, "layer_application"),
            process_event(2, "bonding"),
            process_event(3, "heat_treatment"),
        ),
        "assembly_record_digest": digest("e"),
        "evidence": (EVIDENCE,),
    }


def sample():
    return {
        "sample_id": "sample-1",
        "assembly_id": "assembly-1",
        "interface_id": "interface-1",
        "sampling_plan_id": "sampling-plan-1",
        "physical_location_definition": "caller reviewed center location",
        "orientation_id": "normal-to-interface",
        "coordinate_frame_id": "frame-1",
        "replicate_group_id": "replicate-group-1",
        "source_group_id": "source-group-1",
        "independence_group_id": "independence-group-1",
        "sampling_record_digest": digest("f"),
        "evidence": (EVIDENCE,),
    }


def observation(index, category, metric=None, value=None, unit=None, **updates):
    quantitative = metric is not None
    row = {
        "observation_id": f"observation-{index}",
        "assembly_id": "assembly-1",
        "sample_id": "sample-1",
        "interface_id": "interface-1",
        "observation_category": category,
        "test_or_examination_method_id": f"method-{category}",
        "method_revision": "rev-1",
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}" if quantitative else None,
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 0.1 if quantitative else None,
        "uncertainty_basis": "caller uncertainty budget" if quantitative else None,
        "reported_finding": f"caller-reported {category} finding",
        "caller_reported_failure_descriptor": "caller descriptor retained"
        if category == "adhesion"
        else None,
        "caller_disposition_id": None,
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("a"),
        "raw_data_digest": digest("0123456789abcdef"[index]),
        "observation_record_digest": digest("0123456789abcdef"[index + 8]),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def observations(adhesion=6.0, adhesion_unit="MPa"):
    return (
        observation(0, "thickness", "layer_thickness", 1.0, "mm"),
        observation(1, "adhesion", "adhesion_strength", adhesion, adhesion_unit),
        observation(2, "shear", "shear_strength", 10.0, "MPa"),
        observation(3, "peel", "peel_force", 20.0, "N/mm"),
        observation(4, "porosity", "porosity_fraction", 0.01, "1"),
        observation(5, "disbond", "disbond_area_fraction", 0.0, "1"),
        observation(6, "continuity"),
        observation(7, "nde"),
    )


def campaign_criterion():
    return {
        "criterion_id": "sample-count",
        "criterion_source": "campaign",
        "campaign_metric": "sample_count",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 1,
        "reject_limit": 0,
        "unit_token": "count",
        "criterion_basis": "caller campaign coverage criterion",
    }


def adhesion_criterion():
    return {
        "criterion_id": "adhesion-strength",
        "criterion_source": "observation",
        "observation_category": "adhesion",
        "observation_metric_id": "adhesion_strength",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 5.0,
        "reject_limit": 3.0,
        "unit_token": "MPa",
        "criterion_basis": "caller-authored adhesion criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_process_kinds": ("surface_preparation", "layer_application", "bonding", "heat_treatment"),
        "required_observation_categories": (
            "thickness",
            "adhesion",
            "shear",
            "peel",
            "porosity",
            "disbond",
            "continuity",
            "nde",
        ),
        "criteria": (campaign_criterion(), adhesion_criterion()),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("b"),
        "caller_acceptance_authority": "caller bonded-layer review group",
        "built_in_code_or_specification_limits_used": False,
        "automatic_cohesive_or_adhesive_mechanism_claimed": False,
        "service_life_claimed": False,
        "physical_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "assemblies": (assembly(),),
        "samples": (sample(),),
        "observations": observations(),
        "caller_profile": profile(),
        "substrate_layer_lot_interface_and_geometry_reviewed": True,
        "bond_process_provider_route_and_order_reviewed": True,
        "process_time_temperature_pressure_and_digests_reviewed": True,
        "sampling_location_orientation_and_groups_reviewed": True,
        "observation_method_units_uncertainty_and_findings_reviewed": True,
        "replicate_source_and_independence_claims_reviewed": True,
        "provider_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return BondedLayerIntegrityCampaignAssessment.model_validate(row)


def test_campaign_accepts_only_caller_profile_without_mechanism_or_life_claims():
    result = bonded_layer_integrity_campaign(payload())
    assert result.status == "computed"
    assert result.values["campaign_outcome"] == "accept"
    assert result.values["metric_values"]["observation:adhesion:adhesion_strength"] == 6.0
    assert result.values["automatic_failure_mechanism"] is False
    assert result.values["service_life_or_specification_acceptance"] is False
    assert result.values["physical_qualification"] is False
    assert result.values["diagnostics"]["caller_reported_failure_descriptors"] == [
        "caller descriptor retained"
    ]


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = bonded_layer_integrity_campaign(payload(observations=observations(adhesion=4.0)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = bonded_layer_integrity_campaign(payload(observations=observations(adhesion=2.0)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_category_invalid_process_and_exact_unit_conflict_are_insufficient():
    without_nde = tuple(row for row in observations() if row["observation_category"] != "nde")
    result = bonded_layer_integrity_campaign(payload(observations=without_nde))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["missing_required_observation_categories"] == ["nde"]

    bad_assembly = assembly()
    process_rows = list(bad_assembly["process_events"])
    process_rows[0] = {
        **process_rows[0],
        "record_valid": False,
        "invalid_or_missing_basis": "review rejected process record",
    }
    bad_assembly["process_events"] = tuple(process_rows)
    result = bonded_layer_integrity_campaign(payload(assemblies=(bad_assembly,)))
    assert result.status == "needs_data"

    result = bonded_layer_integrity_campaign(payload(observations=observations(adhesion_unit="psi")))
    assert result.status == "needs_data"
    assert result.values["diagnostics"]["criterion_unit_conflict_ids"] == ["adhesion-strength"]


def test_process_order_interface_links_and_report_digest_are_strict():
    bad_assembly = assembly()
    process_rows = list(bad_assembly["process_events"])
    process_rows[0], process_rows[1] = process_rows[1], process_rows[0]
    bad_assembly["process_events"] = tuple(process_rows)
    with pytest.raises(ValueError, match="sequence order"):
        payload(assemblies=(bad_assembly,))

    bad_observations = list(observations())
    bad_observations[0] = {**bad_observations[0], "interface_id": "other-interface"}
    with pytest.raises(ValueError, match="match their declared sample"):
        payload(observations=tuple(bad_observations))

    first = bonded_layer_integrity_campaign(payload())
    second = bonded_layer_integrity_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    BondedLayerIntegrityCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        BondedLayerIntegrityCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "materials.bonded_layer_integrity"
    assert spec.source_ids == ("authored_bonded_layer_integrity_campaign_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="campaign clock")
        )
