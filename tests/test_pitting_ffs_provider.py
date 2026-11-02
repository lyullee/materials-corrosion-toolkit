import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.pitting_ffs_provider import (
    PittingFFSProviderEvidence,
    pitting_ffs_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
D = "a" * 64


def payload(**updates):
    v = {
        "assessment_id": "p-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "component_type_id": "pipe",
        "material_condition_id": "condition-1",
        "coordinate_frame_id": "frame-1",
        "wall_thickness_value": 0.01,
        "wall_thickness_unit_token": "m",
        "pressure_basis": "internal_minus_external",
        "load_case_id": "case-1",
        "pit_geometries": [
            {
                "pit_field_id": "field-1",
                "cluster_id": "cluster-1",
                "geometry_definition_id": "box-1",
                "coordinate_frame_id": "frame-1",
                "length_value": 0.01,
                "width_value": 0.005,
                "depth_value": 0.002,
                "geometry_unit_token": "m",
                "geometry_content_digest": D,
                "inspection_method_id": "method-1",
                "sizing_uncertainty_value": 0.0002,
                "sizing_uncertainty_unit_token": "m",
                "evidence": [E],
            }
        ],
        "provider_model_id": "provider-model",
        "provider_revision": "1",
        "provider_configuration_digest": D,
        "provider_input_digest": D,
        "provider_result_digest": D,
        "result_metric_id": "provider-output",
        "result_metric_definition": "authored external metric",
        "result_value": 1.2,
        "result_unit_token": "custom",
        "qualification_envelope": {
            "envelope_id": "env-1",
            "component_type_id": "pipe",
            "material_condition_id": "condition-1",
            "coordinate_frame_id": "frame-1",
            "pressure_basis": "internal_minus_external",
            "wall_thickness_unit_token": "m",
            "geometry_unit_token": "m",
            "supported_geometry_definition_ids": ["box-1"],
            "supported_inspection_method_ids": ["method-1"],
            "supported_load_case_ids": ["case-1"],
            "result_metric_id": "provider-output",
            "result_metric_definition": "authored external metric",
            "result_unit_token": "custom",
            "provider_model_id": "provider-model",
            "provider_revision": "1",
            "provider_configuration_digest": D,
            "qualification_records": [
                {
                    "record_id": "q1",
                    "partition": "calibration",
                    "physical_specimen_id": "s1",
                    "source_group_id": "g1",
                    "provider_result_digest": D,
                    "record_valid": True,
                    "evidence": [E],
                },
                {
                    "record_id": "q2",
                    "partition": "holdout",
                    "physical_specimen_id": "s2",
                    "source_group_id": "g2",
                    "provider_result_digest": D,
                    "record_valid": True,
                    "evidence": [E],
                },
            ],
            "qualification_basis": "authored",
            "evidence": [E],
        },
        "component_material_location_and_frame_reviewed": True,
        "wall_thickness_pressure_and_load_basis_reviewed": True,
        "pit_geometry_definition_units_and_clusters_reviewed": True,
        "inspection_uncertainty_and_pod_evidence_reviewed": True,
        "provider_model_revision_and_digests_reviewed": True,
        "result_metric_definition_and_unit_reviewed": True,
        "qualification_partitions_and_source_groups_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return PittingFFSProviderEvidence.model_validate_json(json.dumps(v))


def test_supported():
    assert pitting_ffs_provider_evidence(payload()).status == "computed"


def test_outside():
    b = payload()
    pit = b.pit_geometries[0].model_copy(update={"geometry_definition_id": "other"})
    assert (
        pitting_ffs_provider_evidence(b.model_copy(update={"pit_geometries": (pit,)})).status
        == "out_of_scope"
    )


def test_needs_data():
    assert pitting_ffs_provider_evidence(payload(result_unit_token="other")).status == "needs_data"
    assert (
        pitting_ffs_provider_evidence(payload(provider_model_revision_and_digests_reviewed=False)).status
        == "needs_data"
    )


def test_strict_context():
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "structural.pitting_ffs_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
