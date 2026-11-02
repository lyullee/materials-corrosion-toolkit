import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.nozzle_local_stress import (
    NozzleLocalStressProviderEvidence,
    nozzle_local_stress_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def qualification(record_id, specimen, source_group, partition):
    return {
        "evidence_record_id": record_id,
        "physical_specimen_id": specimen,
        "source_group_id": source_group,
        "partition": partition,
        "supported_metric_ids": ("membrane-hoop",),
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_configuration_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "vessel_geometry_id": "vessel-geometry-1",
        "nozzle_geometry_id": "nozzle-geometry-1",
        "opening_geometry_id": "opening-geometry-1",
        "material_condition_id": "material-1",
        "coordinate_frame_id": "frame-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_configuration_digest": DIGEST_A,
        "supported_mesh_ids": ("mesh-1",),
        "geometry_support": (
            {
                "quantity_id": "shell-thickness",
                "unit_token": "m",
                "minimum_supported_value": 0.005,
                "maximum_supported_value": 0.05,
            },
        ),
        "load_support": (
            {
                "quantity_id": "radial-force",
                "unit_token": "N",
                "minimum_supported_value": -10000.0,
                "maximum_supported_value": 10000.0,
            },
        ),
        "result_support": (
            {
                "representation_kind": "linearized_membrane",
                "metric_id": "membrane-hoop",
                "unit_token": "Pa",
                "minimum_supported_value": -300000000.0,
                "maximum_supported_value": 300000000.0,
                "maximum_supported_expanded_uncertainty": 20000000.0,
                "supported_result_location_ids": ("path-1",),
                "supported_spatial_averaging_bases": ("through-thickness-linearization",),
            },
        ),
        "qualification_evidence": (
            qualification("evidence-cal", "specimen-cal", "source-cal", "calibration"),
            qualification("evidence-hold", "specimen-hold", "source-hold", "holdout"),
        ),
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "nozzle-1",
        "vessel_geometry_id": "vessel-geometry-1",
        "nozzle_geometry_id": "nozzle-geometry-1",
        "opening_geometry_id": "opening-geometry-1",
        "material_condition_id": "material-1",
        "coordinate_frame_id": "frame-1",
        "load_case_id": "load-case-1",
        "geometry_quantities": (
            {
                "quantity_id": "shell-thickness",
                "value": 0.02,
                "unit_token": "m",
                "basis": "authored geometry",
                "evidence": (EVIDENCE,),
            },
        ),
        "load_components": (
            {
                "component_id": "radial-force",
                "component_kind": "force",
                "value": 1000.0,
                "unit_token": "N",
                "sign_and_basis": "positive along authored radial axis",
                "evidence": (EVIDENCE,),
            },
        ),
        "provider_results": (
            {
                "result_id": "result-1",
                "load_case_id": "load-case-1",
                "mesh_id": "mesh-1",
                "result_location_id": "path-1",
                "spatial_averaging_basis": "through-thickness-linearization",
                "coordinate_frame_id": "frame-1",
                "representation_kind": "linearized_membrane",
                "metric_id": "membrane-hoop",
                "metric_definition": "authored hoop membrane stress",
                "reported_value": 100000000.0,
                "unit_token": "Pa",
                "expanded_uncertainty": 10000000.0,
                "provider_id": "provider-1",
                "provider_revision": "1",
                "provider_configuration_digest": DIGEST_A,
                "input_digest": DIGEST_B,
                "result_digest": DIGEST_C,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (envelope(),),
        "vessel_nozzle_opening_geometry_and_units_reviewed": True,
        "material_condition_reviewed": True,
        "coordinate_frame_and_load_basis_reviewed": True,
        "mesh_location_and_averaging_reviewed": True,
        "stress_representation_metrics_units_and_uncertainty_reviewed": True,
        "provider_revision_configuration_and_digests_reviewed": True,
        "calibration_holdout_and_source_groups_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return NozzleLocalStressProviderEvidence(**value)


def test_reviewed_provider_result_is_within_support():
    result = nozzle_local_stress_provider_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"


def test_geometry_or_result_range_outside_support_is_visible():
    base = payload()
    geometry = base.geometry_quantities[0].model_copy(update={"value": 0.1})
    stress = base.provider_results[0].model_copy(update={"reported_value": 400000000.0})
    result = nozzle_local_stress_provider_evidence(
        base.model_copy(update={"geometry_quantities": (geometry,), "provider_results": (stress,)})
    )
    assert result.status == "out_of_scope"
    assert result.values["geometry_outside_support_ids"] == ["shell-thickness"]
    assert result.values["outside_result_ids"] == ["result-1"]


def test_missing_review_or_provider_mismatch_needs_data():
    assert (
        nozzle_local_stress_provider_evidence(payload(mesh_location_and_averaging_reviewed=False)).status
        == "needs_data"
    )
    base = payload()
    mismatch = base.provider_results[0].model_copy(update={"provider_revision": "other"})
    result = nozzle_local_stress_provider_evidence(base.model_copy(update={"provider_results": (mismatch,)}))
    assert result.status == "needs_data"
    assert result.values["provider_mismatch_result_ids"] == ["result-1"]


def test_partition_leakage_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="disjoint"):
        payload(
            candidate_envelopes=(
                envelope(
                    qualification_evidence=(
                        qualification("evidence-cal", "specimen-cal", "same-source", "calibration"),
                        qualification("evidence-hold", "specimen-hold", "same-source", "holdout"),
                    )
                ),
            )
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "structural.nozzle_local_stress_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="nozzle-1", time_basis="authored"),
        )
