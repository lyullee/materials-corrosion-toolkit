import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.test_water_quality_campaign import (
    TestWaterQualityCampaignAssessment as WaterQualityCampaignAssessment,
)
from matintegrity.models.test_water_quality_campaign import (
    TestWaterQualityCampaignReport as WaterQualityCampaignReport,
)
from matintegrity.models.test_water_quality_campaign import (
    specifications,
)
from matintegrity.models.test_water_quality_campaign import (
    test_water_quality_campaign as evaluate_water_quality_campaign,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored water campaign"}


def digest(character):
    return character * 64


ANALYTES = (
    ("ph", "hydrogen-ion activity pH", 7.0, "1"),
    ("conductivity", "electrical conductivity", 10.0, "uS/cm"),
    ("chloride", "chloride ion mass concentration", 10.0, "mg/L"),
    ("halide", "caller total halide mass concentration", 12.0, "mg/L"),
    ("oxygen", "dissolved molecular oxygen", 2.0, "mg/L"),
    ("solids", "total suspended solids", 1.0, "mg/L"),
    ("microbiology", "caller culturable count", 5.0, "CFU/mL"),
    ("inhibitor", "inhibitor active component", 100.0, "mg/L"),
    ("temperature", "sample temperature", 298.0, "K"),
)


def result(index, analyte, definition, value, unit, **updates):
    row = {
        "result_id": f"result-{index}",
        "sample_id": "sample-1",
        "analyte": analyte,
        "species_or_quantity_definition": definition,
        "value": value,
        "unit_token": unit,
        "expanded_uncertainty": 0.1,
        "uncertainty_basis": "caller laboratory uncertainty budget",
        "analysis_method_id": f"method-{analyte}",
        "analysis_method_revision": "rev-1",
        "provider_id": "laboratory-1",
        "provider_revision": "lab-rev-1",
        "provider_configuration_digest": digest("a"),
        "raw_data_digest": digest("0123456789abcdef"[index]),
        "result_record_digest": digest("0123456789abcdef"[index + 7]),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def results(chloride=10.0, chloride_unit="mg/L"):
    rows = []
    for index, (analyte, definition, value, unit) in enumerate(ANALYTES):
        if analyte == "chloride":
            value, unit = chloride, chloride_unit
        rows.append(result(index, analyte, definition, value, unit))
    return tuple(rows)


def history():
    values = []
    for index, kind in enumerate(("fill", "hold", "drain", "dry")):
        values.append(
            {
                "event_id": f"event-{kind}",
                "sequence_index": index,
                "event_kind": kind,
                "state_definition": f"caller {kind} state definition",
                "start_time_s": index * 100.0,
                "end_time_s": (index + 1) * 100.0,
                "water_batch_id": None if kind == "dry" else "water-batch-1",
                "event_configuration_digest": digest("b"),
                "event_record_digest": digest("c"),
                "record_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            }
        )
    return tuple(values)


def sample(rows=None, **updates):
    row = {
        "sample_id": "sample-1",
        "event_id": "event-hold",
        "sampling_time_s": 150.0,
        "sampling_location_id": "outlet-1",
        "sampling_location_definition": "caller circuit outlet sample point",
        "sampling_method_id": "sampling-method-1",
        "laboratory_id": "laboratory-1",
        "calibration_id": "calibration-1",
        "calibration_valid": True,
        "invalid_calibration_basis": None,
        "calibration_digest": digest("d"),
        "replicate_group_id": "replicate-group-1",
        "source_group_id": "source-group-1",
        "independence_group_id": "independence-group-1",
        "results": rows or results(),
        "sample_record_digest": digest("e"),
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def criterion(analyte, definition, value, unit):
    if analyte == "inhibitor":
        direction, aggregation, accept, reject = "minimum", "minimum", 90.0, 50.0
    elif analyte == "temperature":
        direction, aggregation, accept, reject = "maximum", "maximum", 300.0, 320.0
    elif analyte == "ph":
        direction, aggregation, accept, reject = "minimum", "minimum", 6.5, 5.0
    else:
        direction, aggregation, accept, reject = "maximum", "maximum", value * 1.5, value * 2.0
    return {
        "criterion_id": f"criterion-{analyte}",
        "analyte": analyte,
        "species_or_quantity_definition": definition,
        "aggregation": aggregation,
        "direction": direction,
        "accept_limit": accept,
        "reject_limit": reject,
        "unit_token": unit,
        "criterion_basis": "caller-authored water-quality criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_history_kinds": ("fill", "hold", "drain", "dry"),
        "required_analytes": tuple(row[0] for row in ANALYTES),
        "minimum_sample_count": 1,
        "minimum_independent_source_group_count": 1,
        "criteria": tuple(criterion(*row) for row in ANALYTES),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("f"),
        "caller_acceptance_authority": "caller hydrotest review group",
        "chemical_species_conversion_used": False,
        "corrosion_rate_inference_claimed": False,
        "microbiological_risk_inference_claimed": False,
        "built_in_code_or_standard_limits_used": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "campaign_id": "campaign-1",
        "circuit_identity": {
            "source_id": "source-1",
            "water_batch_id": "water-batch-1",
            "source_type_descriptor": "caller supplied source water",
            "tank_id": "tank-1",
            "circuit_id": "circuit-1",
            "circuit_scope_definition": "caller hydrotest circuit boundary",
            "contacted_material_ids": ("material-1", "material-2"),
            "contact_configuration_digest": digest("a"),
            "source_batch_record_digest": digest("b"),
            "evidence": (EVIDENCE,),
        },
        "history": history(),
        "samples": (sample(),),
        "caller_profile": profile(),
        "source_batch_tank_circuit_material_contact_identity_reviewed": True,
        "ordered_fill_hold_drain_dry_history_reviewed": True,
        "sampling_time_location_method_lab_and_calibration_reviewed": True,
        "analyte_species_units_uncertainty_and_methods_reviewed": True,
        "replicate_source_and_independence_claims_reviewed": True,
        "provider_provenance_and_digests_reviewed": True,
        "caller_profile_reviewed": True,
        "invalid_and_missing_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return WaterQualityCampaignAssessment.model_validate(row)


def test_campaign_accepts_exact_caller_results_without_conversion_or_risk_inference():
    output = evaluate_water_quality_campaign(payload())
    assert output.status == "computed"
    assert output.values["campaign_outcome"] == "accept"
    assert output.values["analyte_metric_values"]["chloride"] == 10.0
    assert output.values["chemical_species_converted"] is False
    assert output.values["corrosion_rate_or_microbiological_risk_inferred"] is False
    assert output.values["automatic_standard_acceptance"] is False


def test_caller_review_and_reject_bands_are_explainable():
    reviewed = evaluate_water_quality_campaign(payload(samples=(sample(results(chloride=17.0)),)))
    assert reviewed.values["campaign_outcome"] == "review"
    rejected = evaluate_water_quality_campaign(payload(samples=(sample(results(chloride=25.0)),)))
    assert rejected.values["campaign_outcome"] == "reject"


def test_missing_analyte_invalid_calibration_and_exact_species_unit_conflict_are_insufficient():
    no_microbiology = tuple(row for row in results() if row["analyte"] != "microbiology")
    output = evaluate_water_quality_campaign(payload(samples=(sample(no_microbiology),)))
    assert output.status == "needs_data"
    assert output.values["diagnostics"]["missing_required_analytes"] == ["microbiology"]

    output = evaluate_water_quality_campaign(
        payload(
            samples=(
                sample(calibration_valid=False, invalid_calibration_basis="caller rejected calibration"),
            )
        )
    )
    assert output.status == "needs_data"

    output = evaluate_water_quality_campaign(payload(samples=(sample(results(chloride_unit="ppm")),)))
    assert output.status == "needs_data"
    assert output.values["diagnostics"]["criterion_species_or_unit_conflict_ids"] == ["criterion-chloride"]


def test_history_sample_link_and_report_digest_are_strict():
    unordered = list(history())
    unordered[0], unordered[1] = unordered[1], unordered[0]
    with pytest.raises(ValueError, match="sequence order"):
        payload(history=tuple(unordered))

    with pytest.raises(ValueError, match="cannot be assigned to a dry event"):
        payload(samples=(sample(event_id="event-dry", sampling_time_s=350.0),))

    first = evaluate_water_quality_campaign(payload())
    second = evaluate_water_quality_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    WaterQualityCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["campaign_outcome"] = "reject"
    with pytest.raises(ValueError, match="digest does not match"):
        WaterQualityCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "inspection.test_water_quality"
    assert spec.source_ids == ("authored_test_water_quality_campaign_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="location-1", time_basis="campaign clock")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="campaign clock")
        )
