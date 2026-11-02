import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.finite_element_exchange import (
    FiniteElementResultExchange,
    finite_element_result_exchange,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
D = "a" * 64


def payload(**updates):
    value = {
        "exchange_id": "exchange-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "analysis_id": "analysis-1",
        "model_id": "model-1",
        "model_revision": "1",
        "mesh": {
            "mesh_id": "mesh-1",
            "mesh_revision": "1",
            "coordinate_frame_id": "frame-1",
            "dimensionality": "3d",
            "element_family_ids": ["solid-a"],
            "node_count": 10,
            "element_count": 4,
            "region_ids": ["region-1"],
            "node_identity_digest": D,
            "element_identity_digest": D,
            "connectivity_digest": D,
            "geometry_digest": D,
            "evidence": [E],
        },
        "material_assignments": [
            {
                "assignment_id": "assignment-1",
                "region_id": "region-1",
                "material_id": "material-1",
                "material_condition_id": "condition-1",
                "property_provider_id": "provider-1",
                "property_state_digest": D,
                "assignment_digest": D,
                "evidence": [E],
            }
        ],
        "load_boundary_cases": [
            {
                "case_id": "case-1",
                "load_definition_id": "load-1",
                "boundary_definition_id": "boundary-1",
                "load_basis": "authored",
                "load_digest": D,
                "boundary_digest": D,
                "evidence": [E],
            }
        ],
        "result_fields": [
            {
                "field_id": "field-1",
                "case_id": "case-1",
                "step_id": "step-1",
                "time_s": 1.0,
                "region_id": "region-1",
                "result_location": "integration_point",
                "averaging_basis": "unaveraged",
                "quantity_kind": "tensor",
                "quantity_id": "stress",
                "quantity_definition": "authored Cauchy stress",
                "unit_token": "Pa",
                "component_ids": ["xx", "yy", "zz", "xy", "yz", "zx"],
                "array_shape": [4, 6],
                "array_order": "C",
                "identity_axis_basis": "element then component",
                "array_content_digest": D,
                "result_digest": D,
                "record_valid": True,
                "evidence": [E],
            }
        ],
        "solver_id": "solver-1",
        "solver_revision": "1",
        "solver_configuration_digest": D,
        "solver_input_digest": D,
        "solver_result_digest": D,
        "convergence_definition": "authored residual and mesh review",
        "convergence_record_digest": D,
        "convergence_record_reviewed": True,
        "verification_records": [
            {
                "verification_id": "verify-1",
                "partition": "calibration",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "verification_kind": "authored comparison",
                "metric_id": "relative-error",
                "metric_value": 0.1,
                "metric_unit_token": "1",
                "provider_id": "provider-1",
                "result_digest": D,
                "record_valid": True,
                "evidence": [E],
            },
            {
                "verification_id": "verify-2",
                "partition": "holdout",
                "physical_specimen_id": "specimen-2",
                "source_group_id": "source-2",
                "verification_kind": "authored comparison",
                "metric_id": "relative-error",
                "metric_value": 0.2,
                "metric_unit_token": "1",
                "provider_id": "provider-1",
                "result_digest": D,
                "record_valid": True,
                "evidence": [E],
            },
        ],
        "qualification_envelope": {
            "envelope_id": "envelope-1",
            "supported_dimensionalities": ["3d"],
            "supported_element_family_ids": ["solid-a"],
            "supported_result_locations": ["integration_point"],
            "supported_quantity_ids": ["stress"],
            "supported_unit_tokens": ["Pa"],
            "maximum_node_count": 100,
            "maximum_element_count": 100,
            "required_partitions": ["calibration", "holdout"],
            "solver_id": "solver-1",
            "solver_revision": "1",
            "solver_configuration_digest": D,
            "qualification_basis": "authored envelope",
            "evidence": [E],
        },
        "model_mesh_and_coordinate_frame_reviewed": True,
        "material_assignments_reviewed": True,
        "load_and_boundary_cases_reviewed": True,
        "step_time_frequency_and_result_location_reviewed": True,
        "quantity_components_units_shape_and_order_reviewed": True,
        "solver_revision_configuration_and_digests_reviewed": True,
        "verification_partitions_and_source_groups_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return FiniteElementResultExchange.model_validate_json(json.dumps(value))


def test_supported_metadata_exchange_computes_without_qualification_claim():
    result = finite_element_result_exchange(payload())
    assert result.status == "computed"
    assert result.values["declared_exchange_outcome"] == "within_support"
    assert result.values["verification_partition_counts"] == {"calibration": 1, "holdout": 1}


def test_reviewed_mesh_or_field_outside_support_is_out_of_scope():
    base = payload()
    mesh = base.mesh.model_copy(update={"node_count": 101})
    field = base.result_fields[0].model_copy(update={"quantity_id": "strain"})
    result = finite_element_result_exchange(base.model_copy(update={"mesh": mesh, "result_fields": (field,)}))
    assert result.status == "out_of_scope"
    assert result.values["mesh_outside_support_reasons"] == ["node_count"]
    assert result.values["outside_support_field_ids"] == ["field-1"]


def test_missing_review_partition_or_solver_mismatch_needs_data():
    assert finite_element_result_exchange(payload(convergence_record_reviewed=False)).status == "needs_data"
    base = payload()
    one = base.model_copy(update={"verification_records": base.verification_records[:1]})
    assert finite_element_result_exchange(one).status == "needs_data"
    assert finite_element_result_exchange(payload(solver_revision="2")).status == "needs_data"


def test_links_partition_leakage_and_context_are_strict():
    base = payload()
    bad = base.result_fields[0].model_copy(update={"region_id": "other"})
    with pytest.raises(ValueError, match="declared mesh regions"):
        FiniteElementResultExchange(**base.model_dump(exclude={"result_fields"}), result_fields=(bad,))
    leaked = base.verification_records[1].model_copy(update={"source_group_id": "source-1"})
    with pytest.raises(ValueError, match="cannot cross"):
        FiniteElementResultExchange(
            **base.model_dump(exclude={"verification_records"}),
            verification_records=(base.verification_records[0], leaked),
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "structural.finite_element_result_exchange",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
