import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.dissimilar_weld_evidence import (
    DissimilarWeldApplicabilityEvidence,
    dissimilar_weld_applicability_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def material(subject, role, **updates):
    value = {
        "material_subject_id": subject,
        "material_role": role,
        "material_id": f"material-{subject}",
        "material_condition_id": f"condition-{subject}",
        "material_lot_id": f"lot-{subject}",
        "composition_provider_id": "composition-provider",
        "composition_provider_revision": "1",
        "composition_result_digest": DIGEST_A,
        "property_provider_id": "property-provider",
        "property_provider_revision": "1",
        "property_result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def review(subject, kind, linked, status="reviewed_supported", **updates):
    value = {
        "review_id": f"review-{subject}",
        "review_subject_id": subject,
        "review_subject_kind": kind,
        "linked_identity_ids": linked,
        "review_status": status,
        "review_basis": "caller engineering review",
        "reviewer_or_provider_id": "reviewer-1",
        "reviewer_or_provider_revision": "1",
        "review_configuration_digest": DIGEST_C,
        "review_result_digest": DIGEST_D,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def reviews():
    return (
        review("material-pair", "base_material_pair", ("base-a", "base-b")),
        review("deposit", "filler_or_deposit", ("deposit-1", "layer-deposit")),
        review("buttering", "buttering_or_overlay", ("butter-1", "layer-butter")),
        review("boundary-a-review", "fusion_boundary", ("boundary-a",)),
        review("boundary-b-review", "fusion_boundary", ("boundary-b",)),
        review("pwht-review", "heat_treatment", ("pwht-1",)),
        review("service-review", "service_environment", ("environment-1",)),
    )


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-location-1",
        "joint_id": "joint-1",
        "joint_location_id": "joint-location-1",
        "coordinate_frame_id": "joint-frame-1",
        "service_environment_id": "environment-1",
        "service_environment_definition": "caller service environment",
        "thermal_clock_id": "thermal-clock-1",
        "base_material_a_subject_id": "base-a",
        "base_material_b_subject_id": "base-b",
        "material_evidence": (
            material("base-a", "base_a"),
            material("base-b", "base_b"),
            material("deposit-1", "filler_deposit"),
            material("butter-1", "buttering"),
        ),
        "layers": (
            {
                "layer_id": "layer-butter",
                "sequence_position": 1,
                "layer_role": "buttering",
                "applied_side": "base_a",
                "material_subject_id": "butter-1",
                "welding_procedure_id": "procedure-butter",
                "welding_procedure_revision": "1",
                "physical_region_id": "region-butter",
                "evidence": (EVIDENCE,),
            },
            {
                "layer_id": "layer-deposit",
                "sequence_position": 2,
                "layer_role": "filler_deposit",
                "applied_side": "joint",
                "material_subject_id": "deposit-1",
                "welding_procedure_id": "procedure-deposit",
                "welding_procedure_revision": "1",
                "physical_region_id": "region-deposit",
                "evidence": (EVIDENCE,),
            },
        ),
        "fusion_boundaries": (
            {
                "boundary_region_id": "boundary-a",
                "side": "base_a",
                "base_material_subject_id": "base-a",
                "adjacent_layer_id": "layer-butter",
                "joint_location_id": "joint-location-1",
                "coordinate_frame_id": "joint-frame-1",
                "transition_zone_definition": "caller side-A transition zone",
                "evidence": (EVIDENCE,),
            },
            {
                "boundary_region_id": "boundary-b",
                "side": "base_b",
                "base_material_subject_id": "base-b",
                "adjacent_layer_id": "layer-deposit",
                "joint_location_id": "joint-location-1",
                "coordinate_frame_id": "joint-frame-1",
                "transition_zone_definition": "caller side-B transition zone",
                "evidence": (EVIDENCE,),
            },
        ),
        "thermal_history": (
            {
                "interval_id": "welding-1",
                "interval_kind": "welding",
                "procedure_id": "procedure-deposit",
                "procedure_revision": "1",
                "start_time_s": 0.0,
                "end_time_s": 100.0,
                "minimum_temperature_K": 300.0,
                "maximum_temperature_K": 1600.0,
                "provider_id": "thermal-provider",
                "provider_revision": "1",
                "provider_state_digest": DIGEST_A,
                "data_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "interval_id": "pwht-1",
                "interval_kind": "post_weld_heat_treatment",
                "procedure_id": "pwht-procedure",
                "procedure_revision": "1",
                "start_time_s": 200.0,
                "end_time_s": 500.0,
                "minimum_temperature_K": 800.0,
                "maximum_temperature_K": 850.0,
                "provider_id": "thermal-provider",
                "provider_revision": "1",
                "provider_state_digest": DIGEST_A,
                "data_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "transition_measurements": (
            {
                "measurement_id": "measurement-1",
                "boundary_region_id": "boundary-a",
                "coordinate_frame_id": "joint-frame-1",
                "measurement_kind": "dilution_metric",
                "metric_definition": "caller dilution area fraction",
                "value": 0.2,
                "unit_token": "fraction",
                "expanded_uncertainty": 0.02,
                "uncertainty_coverage_factor": 2.0,
                "method_id": "method-1",
                "provider_id": "measurement-provider",
                "provider_revision": "1",
                "provider_configuration_digest": DIGEST_C,
                "result_digest": DIGEST_D,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "required_review_subject_ids": tuple(row["review_subject_id"] for row in reviews()),
        "compatibility_reviews": reviews(),
        "unresolved_items": (),
        "joint_material_layer_and_boundary_identity_reviewed": True,
        "location_coordinate_frame_and_region_mapping_reviewed": True,
        "procedure_pwht_and_thermal_history_reviewed": True,
        "service_environment_identity_reviewed": True,
        "composition_property_provider_lineage_reviewed": True,
        "transition_measurement_definitions_units_and_uncertainty_reviewed": True,
        "compatibility_review_authority_and_scope_reviewed": True,
        "unresolved_item_completeness_reviewed": True,
    }
    value.update(updates)
    return DissimilarWeldApplicabilityEvidence(**value)


def test_complete_caller_review_record_is_reconciled_without_compatibility_inference():
    result = dissimilar_weld_applicability_evidence(payload())
    assert result.status == "computed"
    assert result.values["review_record_reconciliation"] == "complete"
    assert result.values["fusion_boundary_ids_by_side"] == {
        "base_a": "boundary-a",
        "base_b": "boundary-b",
    }
    assert result.values["transition_measurements"][0]["unit_token"] == "fraction"


def test_unresolved_and_missing_review_subjects_need_data():
    unresolved_reviews = list(reviews())
    unresolved_reviews[0] = review(
        "material-pair",
        "base_material_pair",
        ("base-a", "base-b"),
        status="unresolved",
        limitation_or_unresolved_basis="composition comparison incomplete",
    )
    unresolved_item = {
        "unresolved_item_id": "open-1",
        "review_subject_id": "material-pair",
        "unresolved_category": "composition",
        "description": "transition chemistry remains unresolved",
        "required_evidence_or_decision": "reviewed composition evidence",
        "owner_or_authority_id": "authority-1",
        "evidence": (EVIDENCE,),
    }
    result = dissimilar_weld_applicability_evidence(
        payload(compatibility_reviews=tuple(unresolved_reviews), unresolved_items=(unresolved_item,))
    )
    assert result.status == "needs_data"
    assert result.values["unresolved_review_subject_ids"] == ["material-pair"]
    assert result.values["unresolved_items"][0]["unresolved_item_id"] == "open-1"

    result = dissimilar_weld_applicability_evidence(payload(compatibility_reviews=reviews()[:-1]))
    assert result.status == "needs_data"
    assert result.values["missing_required_review_subject_ids"] == ["service-review"]


def test_caller_out_of_scope_review_remains_out_of_scope():
    rows = list(reviews())
    rows[-1] = review(
        "service-review",
        "service_environment",
        ("environment-1",),
        status="reviewed_out_of_scope",
        limitation_or_unresolved_basis="caller service environment outside reviewed evidence",
    )
    result = dissimilar_weld_applicability_evidence(payload(compatibility_reviews=tuple(rows)))
    assert result.status == "out_of_scope"
    assert result.values["out_of_scope_review_subject_ids"] == ["service-review"]


def test_invalid_measurement_and_review_gate_need_data():
    assessment = payload()
    invalid = assessment.transition_measurements[0].model_copy(
        update={"record_valid": False, "invalid_or_missing_basis": "measurement invalid"}
    )
    result = dissimilar_weld_applicability_evidence(
        assessment.model_copy(update={"transition_measurements": (invalid,)})
    )
    assert result.status == "needs_data"
    assert result.values["invalid_transition_measurement_ids"] == ["measurement-1"]
    assert (
        dissimilar_weld_applicability_evidence(
            payload(composition_property_provider_lineage_reviewed=False)
        ).status
        == "needs_data"
    )


def test_boundary_frame_layer_sequence_and_context_are_strict():
    assessment = payload()
    wrong_frame = assessment.fusion_boundaries[0].model_copy(update={"coordinate_frame_id": "other-frame"})
    with pytest.raises(ValueError, match="declared joint location and frame"):
        DissimilarWeldApplicabilityEvidence(
            **assessment.model_dump(exclude={"fusion_boundaries"}),
            fusion_boundaries=(wrong_frame, assessment.fusion_boundaries[1]),
        )

    wrong_position = assessment.layers[1].model_copy(update={"sequence_position": 3})
    with pytest.raises(ValueError, match="consecutive sequence positions"):
        DissimilarWeldApplicabilityEvidence(
            **assessment.model_dump(exclude={"layers"}),
            layers=(assessment.layers[0], wrong_position),
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.dissimilar_weld_applicability_evidence",
            payload(),
            RunContext(asset_id="other", location_id="weld-location-1", time_basis="authored"),
        )
