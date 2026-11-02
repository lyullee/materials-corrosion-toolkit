import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.forming_qualification import (
    FormingQualificationAssessment,
    forming_qualification,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def metric(**updates):
    value = {
        "metric_record_id": "metric-1",
        "metric_definition_id": "caller-thickness-reduction",
        "direction_id": "transverse",
        "value": 0.1,
        "unit_token": "fraction",
        "expanded_uncertainty": 0.01,
        "uncertainty_coverage_factor": 2.0,
        "measurement_or_derivation_method_id": "method-1",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def interval(identifier, stage, procedure, start, end, low, high, **updates):
    value = {
        "interval_id": identifier,
        "stage": stage,
        "procedure_id": procedure,
        "start_time_s": start,
        "end_time_s": end,
        "minimum_temperature_K": low,
        "maximum_temperature_K": high,
        "provider_id": "logger-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "data_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def property_evidence(**updates):
    value = {
        "evidence_record_id": "evidence-1",
        "evidence_kind": "property_test",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "independence_group_id": "independent-1",
        "physical_region_id": "region-1",
        "method_id": "property-method",
        "result_definition": "caller retained-property metric",
        "reported_value": 95.0,
        "unit_token": "custom-property-unit",
        "expanded_uncertainty": 2.0,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "product_form_id": "plate",
        "forming_mode": "hot",
        "forming_method_id": "method-hot-1",
        "minimum_thickness_m": 0.005,
        "maximum_thickness_m": 0.05,
        "supported_direction_ids": ("transverse",),
        "metric_requirements": (
            {
                "metric_definition_id": "caller-thickness-reduction",
                "direction_id": "transverse",
                "unit_token": "fraction",
                "minimum_value": 0.0,
                "maximum_value": 0.2,
                "requirement_basis": "caller plan",
            },
        ),
        "thermal_supports": (
            {
                "stage": "forming",
                "procedure_id": "forming-procedure",
                "minimum_temperature_K": 700.0,
                "maximum_temperature_K": 900.0,
                "maximum_single_interval_s": 100.0,
                "maximum_cumulative_duration_s": 100.0,
            },
            {
                "stage": "post_forming_heat_treatment",
                "procedure_id": "heat-treatment-1",
                "minimum_temperature_K": 600.0,
                "maximum_temperature_K": 800.0,
                "maximum_single_interval_s": 200.0,
                "maximum_cumulative_duration_s": 200.0,
            },
        ),
        "evidence_requirements": (
            {
                "requirement_id": "property-1",
                "evidence_kind": "property_test",
                "method_id": "property-method",
                "result_definition": "caller retained-property metric",
                "unit_token": "custom-property-unit",
                "minimum_record_count": 1,
                "minimum_value": 90.0,
                "maximum_value": 110.0,
                "requirement_basis": "caller plan",
            },
        ),
        "minimum_physical_specimen_count": 1,
        "minimum_source_group_count": 1,
        "minimum_independence_group_count": 1,
        "qualification_basis": "caller qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "component-1",
        "component_id": "component-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "product_form_id": "plate",
        "governing_thickness_m": 0.02,
        "governing_direction_id": "transverse",
        "forming_mode": "hot",
        "forming_method_id": "method-hot-1",
        "clock_id": "clock-1",
        "forming_metrics": (metric(),),
        "thermal_history": (
            interval("forming-1", "forming", "forming-procedure", 0.0, 50.0, 750.0, 850.0),
            interval(
                "pht-1",
                "post_forming_heat_treatment",
                "heat-treatment-1",
                60.0,
                160.0,
                650.0,
                750.0,
            ),
        ),
        "inspection_and_property_evidence": (property_evidence(),),
        "candidate_envelopes": (envelope(),),
        "component_material_product_and_thickness_reviewed": True,
        "forming_mode_method_and_direction_reviewed": True,
        "deformation_metric_definitions_units_and_uncertainty_reviewed": True,
        "temperature_time_history_reviewed": True,
        "post_forming_heat_treatment_reviewed": True,
        "inspection_property_and_partition_evidence_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return FormingQualificationAssessment(**value)


def test_inside_caller_support_computes_without_acceptance_claim():
    result = forming_qualification(payload())
    assert result.status == "computed"
    assert result.values["declared_qualification_outcome"] == "within_support"
    assert result.values["independence_group_ids"] == ["independent-1"]


def test_duplicate_metric_definitions_cannot_silently_overwrite_records():
    with pytest.raises(ValueError, match="one record per definition"):
        payload(forming_metrics=(metric(value=0.5), metric(metric_record_id="second", value=0.1)))


def test_competing_identity_matching_envelopes_require_explicit_selection():
    first = envelope()
    second = envelope(envelope_id="alternative", maximum_thickness_m=0.01)
    for candidates in ((first, second), (second, first)):
        result = forming_qualification(payload(candidate_envelopes=candidates))
        assert result.status == "needs_data"
        assert set(result.values["identity_matching_envelope_ids"]) == {first["envelope_id"], "alternative"}


def test_thickness_metric_temperature_or_property_outside_is_out_of_scope():
    assert forming_qualification(payload(governing_thickness_m=0.06)).status == "out_of_scope"
    assert forming_qualification(payload(forming_metrics=(metric(value=0.3),))).status == "out_of_scope"
    assert (
        forming_qualification(
            payload(inspection_and_property_evidence=(property_evidence(reported_value=80.0),))
        ).status
        == "out_of_scope"
    )


def test_missing_thermal_stage_unit_or_review_needs_data():
    one_interval = payload().thermal_history[:1]
    result = forming_qualification(payload(thermal_history=one_interval))
    assert result.status == "needs_data"
    assert result.values["missing_required_thermal_support_keys"] == [
        "post_forming_heat_treatment:heat-treatment-1"
    ]
    assert (
        forming_qualification(payload(forming_metrics=(metric(unit_token="other"),))).status == "needs_data"
    )
    assert forming_qualification(payload(post_forming_heat_treatment_reviewed=False)).status == "needs_data"


def test_exact_material_identity_without_envelope_is_out_of_scope():
    result = forming_qualification(payload(material_condition_id="other"))
    assert result.status == "out_of_scope"
    assert result.values["identity_matching_envelope_ids"] == []


def test_clock_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(
            thermal_history=(
                interval("forming-1", "forming", "forming-procedure", 0.0, 50.0, 750.0, 850.0),
                interval(
                    "pht-1",
                    "post_forming_heat_treatment",
                    "heat-treatment-1",
                    40.0,
                    100.0,
                    650.0,
                    750.0,
                ),
            )
        )
    registry = ModelRegistry()
    for spec in specifications():
        registry.register(spec)
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.forming_qualification",
            payload(),
            RunContext(asset_id="other", location_id="component-1", time_basis="authored"),
        )
