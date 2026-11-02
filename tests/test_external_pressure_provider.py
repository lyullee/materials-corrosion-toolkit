import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.external_pressure_provider import (
    ExternalPressureProviderEvidenceAssessment,
    external_pressure_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def qualification_record(identifier, partition, source_group, independence_group, **updates):
    value = {
        "evidence_record_id": identifier,
        "partition": partition,
        "physical_benchmark_id": f"benchmark-{identifier}",
        "source_group_id": source_group,
        "independence_group_id": independence_group,
        "result_kind": "nonlinear_limit_pressure",
        "pressure_basis": "external_minus_internal_pressure",
        "observed_value": 1.0,
        "predicted_value": 1.05,
        "unit_token": "custom-pressure-unit",
        "expanded_observation_uncertainty": 0.05,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "solver-provider",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "shell_type_id": "cylindrical-shell",
        "material_condition_id": "condition-1",
        "boundary_support_id": "support-1",
        "load_case_id": "load-1",
        "pressure_basis": "external_minus_internal_pressure",
        "minimum_thickness_m": 0.005,
        "maximum_thickness_m": 0.05,
        "geometry_support": (
            {
                "metric_id": "outside-diameter",
                "unit_token": "m",
                "minimum_value": 0.5,
                "maximum_value": 2.0,
            },
            {
                "metric_id": "shell-length",
                "unit_token": "m",
                "minimum_value": 1.0,
                "maximum_value": 10.0,
            },
        ),
        "imperfection_metric_definition_id": "caller-peak-radial-deviation",
        "imperfection_metric_unit_token": "m",
        "minimum_imperfection_metric_value": 0.0,
        "maximum_imperfection_metric_value": 0.005,
        "supported_result_kinds": ("eigen_buckling_pressure", "nonlinear_limit_pressure"),
        "result_unit_token": "custom-pressure-unit",
        "solver_id": "solver-1",
        "solver_revision": "solver-revision-1",
        "provider_id": "solver-provider",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "qualification_evidence": (
            qualification_record("calibration-1", "calibration", "source-cal", "ind-cal"),
            qualification_record("holdout-1", "holdout", "source-hold", "ind-hold"),
        ),
        "minimum_calibration_source_group_count": 1,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "qualification_basis": "caller validation plan",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def result_record(**updates):
    value = {
        "result_record_id": "result-1",
        "analysis_id": "analysis-1",
        "result_kind": "nonlinear_limit_pressure",
        "pressure_basis": "external_minus_internal_pressure",
        "result_value": 1.1,
        "result_unit_token": "custom-pressure-unit",
        "mesh_id": "mesh-1",
        "mesh_digest": DIGEST_B,
        "geometry_model_id": "geometry-model-1",
        "material_model_id": "material-model-1",
        "imperfection_model_id": "imperfection-model-1",
        "boundary_model_id": "boundary-model-1",
        "load_model_id": "load-model-1",
        "solver_id": "solver-1",
        "solver_revision": "solver-revision-1",
        "provider_id": "solver-provider",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "convergence_or_solution_state": "caller-reviewed converged state",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "shell-1",
        "component_id": "component-1",
        "shell_type_id": "cylindrical-shell",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "thickness_m": 0.02,
        "geometry_metrics": (
            {
                "metric_id": "outside-diameter",
                "value": 1.0,
                "unit_token": "m",
                "measurement_basis": "caller measurement",
                "expanded_uncertainty": 0.001,
                "uncertainty_coverage_factor": 2.0,
                "evidence": (EVIDENCE,),
            },
            {
                "metric_id": "shell-length",
                "value": 5.0,
                "unit_token": "m",
                "measurement_basis": "caller measurement",
                "expanded_uncertainty": 0.002,
                "uncertainty_coverage_factor": 2.0,
                "evidence": (EVIDENCE,),
            },
        ),
        "boundary_support_id": "support-1",
        "load_case_id": "load-1",
        "pressure_basis": "external_minus_internal_pressure",
        "imperfection": {
            "imperfection_field_id": "field-1",
            "physical_surface_id": "surface-1",
            "coordinate_frame_id": "shell-frame",
            "field_definition": "caller measured radial deviation",
            "field_data_digest": DIGEST_B,
            "metric_definition_id": "caller-peak-radial-deviation",
            "metric_value": 0.002,
            "metric_unit_token": "m",
            "expanded_uncertainty": 0.0002,
            "uncertainty_coverage_factor": 2.0,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "provider_result": result_record(),
        "candidate_envelopes": (envelope(),),
        "component_material_geometry_and_thickness_reviewed": True,
        "boundary_support_load_case_and_pressure_basis_reviewed": True,
        "imperfection_field_metric_and_units_reviewed": True,
        "mesh_and_model_identity_reviewed": True,
        "solver_provider_revision_and_digests_reviewed": True,
        "result_kind_units_and_solution_state_reviewed": True,
        "calibration_holdout_partitions_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return ExternalPressureProviderEvidenceAssessment(**value)


def test_qualified_provider_result_is_preserved_without_allowable_claim():
    calculated = external_pressure_provider_evidence(payload())
    assert calculated.status == "computed"
    assert calculated.values["declared_applicability_outcome"] == "within_support"
    assert calculated.values["provider_reported_result_value"] == pytest.approx(1.1)
    assert calculated.values["holdout_independence_group_ids"] == ["ind-hold"]


def test_geometry_or_imperfection_outside_support_is_out_of_scope():
    assessment = payload()
    geometry = assessment.geometry_metrics[0].model_copy(update={"value": 3.0})
    calculated = external_pressure_provider_evidence(
        assessment.model_copy(update={"geometry_metrics": (geometry, assessment.geometry_metrics[1])})
    )
    assert calculated.status == "out_of_scope"
    assert calculated.values["outside_support_reasons"] == ["geometry_support"]

    imperfection = assessment.imperfection.model_copy(update={"metric_value": 0.01})
    assert (
        external_pressure_provider_evidence(
            assessment.model_copy(update={"imperfection": imperfection})
        ).status
        == "out_of_scope"
    )


def test_provider_unit_or_qualification_partition_problem_needs_data():
    assert (
        external_pressure_provider_evidence(
            payload(provider_result=result_record(result_unit_token="other"))
        ).status
        == "needs_data"
    )
    only_calibration = envelope(
        qualification_evidence=(
            qualification_record("calibration-1", "calibration", "source-cal", "ind-cal"),
        )
    )
    calculated = external_pressure_provider_evidence(payload(candidate_envelopes=(only_calibration,)))
    assert calculated.status == "needs_data"
    assert calculated.values["qualification_partition_counts_sufficient"] is False


def test_exact_pressure_basis_identity_without_envelope_is_out_of_scope():
    calculated = external_pressure_provider_evidence(payload(pressure_basis="absolute_external_pressure"))
    assert calculated.status == "out_of_scope"
    assert calculated.values["identity_matching_envelope_ids"] == []


def test_duplicate_geometry_and_context_identity_are_enforced():
    assessment = payload()
    with pytest.raises(ValueError, match="must be unique"):
        ExternalPressureProviderEvidenceAssessment(
            **assessment.model_dump(exclude={"geometry_metrics"}),
            geometry_metrics=(assessment.geometry_metrics[0], assessment.geometry_metrics[0]),
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "structural.external_pressure_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="shell-1", time_basis="authored"),
        )
