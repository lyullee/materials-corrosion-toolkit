import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.external_pressure_campaign import (
    ExternalPressureCampaignAssessment,
    ExternalPressureCampaignReport,
    external_pressure_campaign,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored receipt"}


def digest(character):
    return character * 64


def qualification(identifier, partition, source, independence):
    return {
        "evidence_record_id": identifier,
        "partition": partition,
        "physical_benchmark_id": f"benchmark-{identifier}",
        "source_group_id": source,
        "independence_group_id": independence,
        "result_kind": "nonlinear_limit_pressure",
        "pressure_basis": "external-minus-internal",
        "observed_value": 1.0,
        "predicted_value": 1.05,
        "unit_token": "MPa",
        "expanded_observation_uncertainty": 0.05,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("a"),
        "input_digest": digest("b"),
        "result_digest": digest("c"),
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }


def provider_assessment(thickness=0.02, result_valid=True, **updates):
    row = {
        "assessment_id": "provider-assessment-1",
        "asset_id": "asset-1",
        "location_id": "shell-1",
        "component_id": "component-1",
        "shell_type_id": "cylindrical-shell",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "thickness_m": thickness,
        "geometry_metrics": (
            {
                "metric_id": "diameter",
                "value": 1.0,
                "unit_token": "m",
                "measurement_basis": "caller measurement",
                "expanded_uncertainty": 0.001,
                "uncertainty_coverage_factor": 2.0,
                "evidence": (EVIDENCE,),
            },
        ),
        "boundary_support_id": "support-1",
        "load_case_id": "load-1",
        "pressure_basis": "external-minus-internal",
        "imperfection": {
            "imperfection_field_id": "field-1",
            "physical_surface_id": "surface-1",
            "coordinate_frame_id": "frame-1",
            "field_definition": "caller radial deviation field",
            "field_data_digest": digest("d"),
            "metric_definition_id": "peak-radial-deviation",
            "metric_value": 0.002,
            "metric_unit_token": "m",
            "expanded_uncertainty": 0.0002,
            "uncertainty_coverage_factor": 2.0,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "provider_result": {
            "result_record_id": "provider-result-1",
            "analysis_id": "analysis-1",
            "result_kind": "nonlinear_limit_pressure",
            "pressure_basis": "external-minus-internal",
            "result_value": 1.1,
            "result_unit_token": "MPa",
            "mesh_id": "mesh-1",
            "mesh_digest": digest("e"),
            "geometry_model_id": "geometry-model-1",
            "material_model_id": "material-model-1",
            "imperfection_model_id": "imperfection-model-1",
            "boundary_model_id": "boundary-model-1",
            "load_model_id": "load-model-1",
            "solver_id": "solver-1",
            "solver_revision": "solver-rev-1",
            "provider_id": "provider-1",
            "provider_revision": "rev-1",
            "provider_configuration_digest": digest("a"),
            "input_digest": digest("b"),
            "result_digest": digest("f"),
            "convergence_or_solution_state": "caller-reviewed converged state",
            "record_valid": result_valid,
            "invalid_or_missing_basis": None if result_valid else "provider result invalid",
            "evidence": (EVIDENCE,),
        },
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "shell_type_id": "cylindrical-shell",
                "material_condition_id": "condition-1",
                "boundary_support_id": "support-1",
                "load_case_id": "load-1",
                "pressure_basis": "external-minus-internal",
                "minimum_thickness_m": 0.005,
                "maximum_thickness_m": 0.05,
                "geometry_support": (
                    {
                        "metric_id": "diameter",
                        "unit_token": "m",
                        "minimum_value": 0.5,
                        "maximum_value": 2.0,
                    },
                ),
                "imperfection_metric_definition_id": "peak-radial-deviation",
                "imperfection_metric_unit_token": "m",
                "minimum_imperfection_metric_value": 0.0,
                "maximum_imperfection_metric_value": 0.005,
                "supported_result_kinds": ("nonlinear_limit_pressure",),
                "result_unit_token": "MPa",
                "solver_id": "solver-1",
                "solver_revision": "solver-rev-1",
                "provider_id": "provider-1",
                "provider_revision": "rev-1",
                "provider_configuration_digest": digest("a"),
                "qualification_evidence": (
                    qualification("calibration-1", "calibration", "source-cal", "ind-cal"),
                    qualification("holdout-1", "holdout", "source-hold", "ind-hold"),
                ),
                "minimum_calibration_source_group_count": 1,
                "minimum_holdout_source_group_count": 1,
                "minimum_holdout_independence_group_count": 1,
                "qualification_basis": "caller validation plan",
                "evidence": (EVIDENCE,),
            },
        ),
        "component_material_geometry_and_thickness_reviewed": True,
        "boundary_support_load_case_and_pressure_basis_reviewed": True,
        "imperfection_field_metric_and_units_reviewed": True,
        "mesh_and_model_identity_reviewed": True,
        "solver_provider_revision_and_digests_reviewed": True,
        "result_kind_units_and_solution_state_reviewed": True,
        "calibration_holdout_partitions_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    row.update(updates)
    return row


def convergence(value=0.03, **updates):
    row = {
        "convergence_record_id": "convergence-1",
        "provider_assessment_id": "provider-assessment-1",
        "analysis_id": "analysis-1",
        "result_kind": "nonlinear_limit_pressure",
        "mesh_family_id": "mesh-family-1",
        "model_family_id": "model-family-1",
        "pressure_basis": "external-minus-internal",
        "convergence_metric_definition": "caller adjacent-refinement relative change",
        "convergence_metric_value": value,
        "convergence_metric_unit_token": "1",
        "comparison_result_ids": ("coarse-result", "fine-result"),
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "provider_configuration_digest": digest("a"),
        "comparison_input_digest": digest("b"),
        "comparison_result_digest": digest("c"),
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def criterion(metric, direction, accept, reject, unit):
    return {
        "criterion_id": f"criterion-{metric}",
        "metric_id": metric,
        "direction": direction,
        "accept_limit": accept,
        "reject_limit": reject,
        "unit_token": unit,
        "criterion_basis": "caller provider-receipt quality criterion",
    }


def profile():
    return {
        "profile_id": "profile-1",
        "profile_version": "1.0.0",
        "required_result_kinds": ("nonlinear_limit_pressure",),
        "convergence_metric_definition": "caller adjacent-refinement relative change",
        "convergence_metric_unit_token": "1",
        "criteria": (
            criterion("supported_receipt_count", "minimum", 1, 0, "count"),
            criterion("out_of_support_receipt_count", "maximum", 0, 1, "count"),
            criterion("maximum_convergence_metric", "maximum", 0.05, 0.1, "1"),
            criterion("maximum_holdout_absolute_relative_error", "maximum", 0.1, 0.2, "1"),
        ),
        "profile_provider_id": "caller-provider",
        "profile_revision": "rev-1",
        "profile_configuration_digest": digest("d"),
        "caller_review_authority": "caller structural review group",
        "buckling_analysis_executed": False,
        "code_curve_or_safety_factor_used": False,
        "automatic_acceptance_claimed": False,
        "field_qualification_claimed": False,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "assessment_id": "campaign-assessment-1",
        "asset_id": "asset-1",
        "location_id": "shell-1",
        "campaign_id": "campaign-1",
        "component_id": "component-1",
        "provider_assessments": (provider_assessment(),),
        "convergence_evidence": (convergence(),),
        "caller_profile": profile(),
        "component_geometry_material_imperfection_identity_reviewed": True,
        "boundary_load_pressure_basis_and_support_reviewed": True,
        "provider_solver_revision_configuration_and_digests_reviewed": True,
        "mesh_and_model_identity_reviewed": True,
        "applicability_and_envelope_support_reviewed": True,
        "convergence_definition_units_and_records_reviewed": True,
        "calibration_holdout_validation_evidence_reviewed": True,
        "caller_profile_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ExternalPressureCampaignAssessment.model_validate(row)


def test_supported_receipt_preserves_provider_result_without_analysis_or_acceptance():
    result = external_pressure_campaign(payload())
    assert result.status == "computed"
    assert result.values["evidence_outcome"] == "supported"
    assert result.values["metric_values"]["maximum_holdout_absolute_relative_error"] == pytest.approx(0.05)
    assert result.values["buckling_analysis_executed"] is False
    assert result.values["allowable_pressure_or_safety_factor_produced"] is False
    assert result.values["automatic_acceptance_or_field_qualification"] is False


def test_caller_review_and_not_supported_receipt_bands_are_explainable():
    reviewed = external_pressure_campaign(payload(convergence_evidence=(convergence(0.075),)))
    assert reviewed.values["evidence_outcome"] == "review"

    outside = external_pressure_campaign(payload(provider_assessments=(provider_assessment(thickness=0.1),)))
    assert outside.status == "computed"
    assert outside.values["evidence_outcome"] == "not_supported"
    assert outside.values["receipt_summaries"][0]["receipt_status"] == "out_of_scope"


def test_incomplete_provider_or_convergence_identity_is_insufficient():
    invalid = external_pressure_campaign(
        payload(provider_assessments=(provider_assessment(result_valid=False),))
    )
    assert invalid.status == "needs_data"
    assert invalid.values["diagnostics"]["incomplete_provider_receipt_ids"] == ["provider-assessment-1"]

    conflict = external_pressure_campaign(
        payload(convergence_evidence=(convergence(convergence_metric_unit_token="percent"),))
    )
    assert conflict.status == "needs_data"
    assert conflict.values["diagnostics"]["convergence_identity_conflict_ids"] == ["convergence-1"]


def test_linkage_and_report_digest_are_strict():
    with pytest.raises(ValueError, match="preserve provider result identity"):
        payload(convergence_evidence=(convergence(provider_revision="other"),))

    first = external_pressure_campaign(payload())
    second = external_pressure_campaign(payload())
    assert first.values["report_digest"] == second.values["report_digest"]
    ExternalPressureCampaignReport.model_validate(first.values)
    tampered = dict(first.values)
    tampered["evidence_outcome"] = "not_supported"
    with pytest.raises(ValueError, match="digest does not match"):
        ExternalPressureCampaignReport.model_validate(tampered)


def test_local_spec_identity_and_source_are_stable():
    spec = specifications()[0]
    assert spec.model_id == "structural.external_pressure"
    assert spec.source_ids == ("authored_external_pressure_provider_receipt_campaign_audit",)
    spec.context_validator(
        payload(), RunContext(asset_id="asset-1", location_id="shell-1", time_basis="campaign snapshot")
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="shell-1", time_basis="campaign snapshot")
        )
