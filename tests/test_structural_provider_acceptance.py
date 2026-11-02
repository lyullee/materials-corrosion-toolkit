import pytest
from pydantic import ValidationError

from matintegrity.structural_provider_acceptance import (
    RequiredStructuralField,
    StructuralAcceptanceProfile,
    StructuralDiagnosticCriterion,
    StructuralDiagnosticEvidence,
    StructuralMeshReceipt,
    StructuralResultFieldReceipt,
    evaluate_structural_provider_receipt,
    structural_provider_result_receipt,
)

E = {"source_id": "caller", "origin": "user_declared", "citation": "caller verification"}
D = "d" * 64


def receipt(**updates):
    value = {
        "receipt_id": "receipt-1",
        "analysis_kind": "nozzle_local_stress",
        "asset_id": "asset-1",
        "component_id": "nozzle-1",
        "location_id": "junction-1",
        "physical_scope_id": "scope-1",
        "analysis_id": "analysis-1",
        "model_id": "model-1",
        "model_revision": "1",
        "mesh": StructuralMeshReceipt(
            mesh_id="mesh-1",
            mesh_revision="1",
            coordinate_frame_id="frame-1",
            dimensionality="3d",
            element_family_ids=("solid",),
            node_count=100,
            element_count=50,
            mesh_content_digest=D,
        ),
        "load_case_ids": ("case-1",),
        "load_case_digest": D,
        "result_fields": (
            StructuralResultFieldReceipt(
                field_id="stress",
                load_case_id="case-1",
                step_id="step-1",
                coordinate_frame_id="frame-1",
                region_id="junction",
                result_location="integration_point",
                averaging_basis="unaveraged",
                quantity_id="stress_tensor",
                quantity_definition="caller-defined stress tensor",
                unit_token="Pa",
                component_ids=("s11", "s22", "s33", "s12", "s13", "s23"),
                array_shape=(50, 6),
                array_order="C",
                array_content_digest=D,
                result_record_digest=D,
            ),
        ),
        "diagnostics": (
            StructuralDiagnosticEvidence(
                diagnostic_id="eq-1",
                category="equilibrium",
                metric_id="relative_force_residual",
                metric_definition="caller-defined normalized residual",
                status="reported",
                value=0.01,
                expanded_uncertainty=0.002,
                unit_token="1",
                provider_record_digest=D,
                evidence=(E,),
            ),
        ),
        "provider_id": "solver-provider",
        "provider_revision": "1",
        "provider_configuration_digest": D,
        "provider_input_digest": D,
        "provider_result_digest": D,
        "evidence": (E,),
    }
    value.update(updates)
    return structural_provider_result_receipt(**value)


def profile(maximum=0.02):
    return StructuralAcceptanceProfile(
        profile_id="profile-1",
        profile_revision="1",
        supported_analysis_kinds=("external_pressure", "nozzle_local_stress", "finite_element"),
        supported_model_ids=("model-1",),
        supported_element_family_ids=("solid",),
        maximum_node_count=1000,
        maximum_element_count=1000,
        required_fields=(
            RequiredStructuralField(
                requirement_id="stress-field",
                field_id="stress",
                quantity_id="stress_tensor",
                unit_token="Pa",
                result_location="integration_point",
                coordinate_frame_id="frame-1",
            ),
        ),
        diagnostic_criteria=(
            StructuralDiagnosticCriterion(
                criterion_id="equilibrium-limit",
                category="equilibrium",
                metric_id="relative_force_residual",
                unit_token="1",
                maximum_acceptable=maximum,
                basis="caller acceptance profile",
                evidence=(E,),
            ),
        ),
        profile_source_digest=D,
        evidence=(E,),
    )


def test_accept_reject_and_review_use_only_caller_diagnostic_bounds():
    accepted = evaluate_structural_provider_receipt(receipt(), profile())
    rejected = evaluate_structural_provider_receipt(receipt(), profile(0.005))
    reviewed = evaluate_structural_provider_receipt(receipt(), profile(0.011))
    assert (accepted.decision, rejected.decision, reviewed.decision) == ("accept", "reject", "review")
    assert accepted.qualification_claim is False
    assert accepted.physical_validation_claim is False
    assert accepted == evaluate_structural_provider_receipt(receipt(), profile())


def test_missing_or_mismatched_field_is_insufficient_evidence():
    missing_profile = profile().model_copy(
        update={
            "required_fields": (
                profile().required_fields[0].model_copy(update={"field_id": "missing-field"}),
            )
        }
    )
    result = evaluate_structural_provider_receipt(receipt(), missing_profile)
    assert result.decision == "insufficient_evidence"
    assert any(row.state == "missing" for row in result.findings)


def test_receipt_digest_detects_tampering():
    original = receipt()
    tampered = original.model_dump(mode="python")
    tampered["model_revision"] = "2"
    with pytest.raises(ValidationError, match="payload digest mismatch"):
        original.model_validate(tampered)

    report = evaluate_structural_provider_receipt(original, profile())
    changed_report = report.model_dump(mode="python")
    changed_report["decision"] = "review"
    with pytest.raises(ValidationError, match="report digest mismatch"):
        report.model_validate(changed_report)


def test_missing_diagnostic_status_cannot_carry_numeric_value():
    with pytest.raises(ValidationError, match="cannot carry numeric"):
        StructuralDiagnosticEvidence(
            diagnostic_id="bad",
            category="convergence",
            metric_id="residual",
            metric_definition="caller residual",
            status="missing",
            value=1.0,
            expanded_uncertainty=None,
            unit_token="1",
            provider_record_digest=D,
            evidence=(E,),
        )
