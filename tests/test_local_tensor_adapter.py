import json
import math

import pytest
from pydantic import ValidationError

from matintegrity.adapters import (
    LocalTensorHistory,
    critical_plane_inputs_from_local_tensor_history,
)
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

CONTEXT = RunContext(
    asset_id="synthetic-coupon",
    location_id="notch-integration-point",
    time_basis="one reviewed synthetic cycle",
)
PLANE = (
    {
        "plane_id": "normal-x",
        "normal": [1.0, 0.0, 0.0],
        "in_plane_direction": [0.0, 1.0, 0.0],
    },
)


def history(**overrides):
    points = [
        (1.0, 0.0),
        (-0.5, math.sqrt(3) / 2),
        (-0.5, -math.sqrt(3) / 2),
        (1.0, 0.0),
    ]
    base = {
        "history_id": "qualified-local-cycle",
        "asset_id": "synthetic-coupon",
        "material_condition_id": "synthetic-condition",
        "location_id": "notch-integration-point",
        "load_case_id": "nonproportional-cycle",
        "tensor_source_id": "synthetic-fe-export",
        "provider_id": "example-fe-adapter",
        "provider_version": "1.0.0",
        "solver_name": "synthetic-solver",
        "solver_version": "1.0",
        "analysis_id": "analysis-001",
        "solution_revision": "rev-a",
        "mesh_id": "mesh-001",
        "field_location_kind": "integration_point",
        "field_location_id": "element-42:ip-3",
        "spatial_averaging": "none",
        "coordinate_frame_id": "global-cartesian",
        "coordinate_basis_vectors_global": (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        "stress_measure": "cauchy",
        "strain_measure": "infinitesimal",
        "strain_shear_convention": "engineering",
        "sample_ids": ["v0", "v1", "v2", "v0-close"],
        "sample_times_s": [0.0, 1.0, 2.0, 3.0],
        "sample_valid": [True, True, True, True],
        "stress_tensor_components_Pa": [[0.0, 0.0, 0.0, 40e6 * x, 0.0, 40e6 * y] for x, y in points],
        "strain_tensor_components": [[0.0, 0.0, 0.0, 0.002 * x, 0.0, 0.002 * y] for x, y in points],
        "representative_cycle_declared": True,
        "tensor_field_review_status": "qualified_by_caller",
        "source_content_sha256": "a" * 64,
        "provider_configuration_digest": "b" * 64,
    }
    return LocalTensorHistory(**(base | overrides))


def adapt(record, context=CONTEXT):
    return critical_plane_inputs_from_local_tensor_history(
        record,
        context=context,
        candidate_planes=PLANE,
        maximum_stress_closure_error_Pa=0.0,
        maximum_strain_closure_error=0.0,
        fatemi_socie_coefficient=0.3,
        normalization_stress_Pa=400e6,
    )


def test_engineering_shear_is_converted_and_provenance_is_retained():
    payload = adapt(history())
    assert payload["strain_tensor_components"][0][3] == pytest.approx(0.001)
    assert payload["load_case_id"] == "nonproportional-cycle"
    assert payload["analysis_id"] == "analysis-001"
    assert payload["mesh_id"] == "mesh-001"
    assert payload["field_location_id"] == "element-42:ip-3"
    assert payload["coordinate_frame_id"] == "global-cartesian"
    assert payload["sample_times_s"] == [0.0, 1.0, 2.0, 3.0]
    assert payload["tensor_provider_id"] == "example-fe-adapter"
    assert payload["solver_name"] == "synthetic-solver"
    assert payload["solution_revision"] == "rev-a"
    assert payload["field_location_kind"] == "integration_point"
    assert payload["spatial_averaging"] == "none"
    assert payload["coordinate_basis_vectors_global"] == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    assert payload["input_strain_shear_convention"] == "engineering"
    assert payload["source_content_sha256"] == "a" * 64
    assert payload["provider_configuration_digest"] == "b" * 64
    assert len(payload["tensor_history_record_digest"]) == 64


def test_exchange_record_round_trips_as_strict_json():
    record = history()
    encoded = json.dumps(record.model_dump(mode="json"))
    assert LocalTensorHistory.model_validate_json(encoded) == record


def test_adapted_nonproportional_path_runs_both_range_definitions():
    payload = adapt(history())
    registry = default_registry()
    chord = registry.run("fatigue.critical_plane_vector_path_factors", payload, CONTEXT)
    circle = registry.run("fatigue.critical_plane_minimum_enclosing_circle_factors", payload, CONTEXT)
    chord_row = chord.values["candidate_factors"][0]
    circle_row = circle.values["candidate_factors"][0]
    assert chord_row["shear_strain_vector_chord_amplitude"] == pytest.approx(0.002 * math.sqrt(3) / 2)
    assert circle_row["shear_strain_minimum_enclosing_circle_amplitude"] == pytest.approx(0.002)
    assert circle_row["shear_strain_circle_to_chord_amplitude_ratio"] == pytest.approx(2 / math.sqrt(3))
    assert circle.inputs["tensor_history_record_digest"] == payload["tensor_history_record_digest"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"tensor_field_review_status": "unreviewed"},
        {"sample_valid": [True, False, True, True]},
        {"stress_measure": "second_piola_kirchhoff"},
        {"strain_measure": "green_lagrange"},
    ],
)
def test_unqualified_or_incompatible_fields_are_not_adapted(overrides):
    with pytest.raises(ValueError):
        adapt(history(**overrides))


def test_context_identity_mismatch_is_rejected():
    other = CONTEXT.model_copy(update={"location_id": "other-point"})
    with pytest.raises(ValueError, match="asset and location"):
        adapt(history(), other)


@pytest.mark.parametrize(
    "basis",
    [
        ((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)),
    ],
)
def test_coordinate_frame_must_be_orthonormal_and_right_handed(basis):
    with pytest.raises(ValidationError):
        history(coordinate_basis_vectors_global=basis)


def test_record_digest_changes_with_provider_configuration():
    first = adapt(history())
    second = adapt(history(provider_configuration_digest="c" * 64))
    assert first["tensor_history_record_digest"] != second["tensor_history_record_digest"]
