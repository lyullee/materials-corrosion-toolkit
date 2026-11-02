from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.hydrogen_exchange import HydrogenTransportHistory, hydrogen_transport_history


def payload():
    return dict(
        provider_id="hydrogen-physical-models",
        provider_revision="785dae74dad4771e76e2a8e8aad3731e3dfa799e",
        solver_id="materials.DiffusionDomain",
        result_id="authored-planar-example",
        native_result_sha256="1" * 64,
        material_condition_id="synthetic-metal-state",
        reference_lattice_id="synthetic-lattice",
        carrier="atomic_hydrogen",
        carrier_molar_mass_kg_mol=0.001,
        geometry="planar",
        trap_population_ids=["trap-a"],
        elapsed_time_origin_id="authored-zero",
        time_s=[0.0, 1.0],
        face_positions_m=[0.0, 0.25, 0.5, 0.75],
        cell_centers_m=[0.125, 0.375, 0.625],
        face_areas_m2=[2.0, 2.0, 2.0, 2.0],
        cell_volumes_m3=[0.5, 0.5, 0.5],
        mobile_entity_mol_m3=[[1.0, 1.0, 1.0], [0.9, 1.0, 1.1]],
        trapped_entity_mol_m3=[[[0.1, 0.1, 0.1]], [[0.1, 0.1, 0.1]]],
        left_integrated_coordinate_flow_mol=[0.0, -0.01],
        right_integrated_coordinate_flow_mol=[0.0, -0.01],
        wall_inventory_mol=[1.65, 1.65],
        wall_inventory_residual_mol=[0.0, 0.0],
        total_inventory_residual_mol=[0.0, 0.0],
        concentration_numerical_tolerance_mol_m3=1e-10,
        function_evaluations=12,
        coefficient_basis="authored coefficients for exchange testing only",
        boundary_basis="authored fixed concentrations for exchange testing only",
        limitations=["Synthetic record; not a material validation or damage assessment."],
    )


def test_transport_history_round_trip_preserves_units_identity_and_shape():
    record = hydrogen_transport_history(**payload())
    restored = HydrogenTransportHistory.model_validate_json(record.model_dump_json())

    assert restored.provider_revision == payload()["provider_revision"]
    assert restored.carrier == "atomic_hydrogen"
    assert len(restored.mobile_entity_mol_m3) == len(restored.time_s)
    assert restored.payload_digest == record.payload_digest


def test_transport_history_digest_rejects_changed_physical_value():
    record = hydrogen_transport_history(**payload()).model_dump(mode="json")
    record["mobile_entity_mol_m3"][1][0] = 99.0

    with pytest.raises(ValidationError, match="digest does not match"):
        HydrogenTransportHistory.model_validate(record)


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value["time_s"].append(2.0),
        lambda value: value["face_areas_m2"].pop(),
        lambda value: value["trapped_entity_mol_m3"][0][0].pop(),
        lambda value: value["trap_population_ids"].append("trap-a"),
    ],
)
def test_transport_history_rejects_misaligned_or_ambiguous_arrays(change):
    value = deepcopy(payload())
    change(value)

    with pytest.raises(ValidationError):
        hydrogen_transport_history(**value)


def test_transport_history_allows_only_declared_numerical_negative_tolerance():
    value = payload()
    value["mobile_entity_mol_m3"][1][0] = -5e-11
    assert hydrogen_transport_history(**value).mobile_entity_mol_m3[1][0] == -5e-11

    value["mobile_entity_mol_m3"][1][0] = -2e-10
    with pytest.raises(ValidationError, match="negative numerical tolerance"):
        hydrogen_transport_history(**value)
