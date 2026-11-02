"""Validate the portable hydrogen-transport history contract and negative controls."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from matintegrity import hydrogen_exchange
from matintegrity.hydrogen_exchange import HydrogenTransportHistory, hydrogen_transport_history

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_PROVIDER_REVISION = "785dae74dad4771e76e2a8e8aad3731e3dfa799e"


def main() -> None:
    payload = dict(
        provider_id="hydrogen-physical-models",
        provider_revision=REVIEWED_PROVIDER_REVISION,
        solver_id="materials.DiffusionDomain",
        result_id="authored-planar-conservation-example",
        native_result_sha256="2" * 64,
        material_condition_id="synthetic-uniform-metal",
        reference_lattice_id="synthetic-lattice",
        carrier="atomic_hydrogen",
        carrier_molar_mass_kg_mol=0.001,
        geometry="planar",
        trap_population_ids=[],
        elapsed_time_origin_id="authored-zero",
        time_s=[0.0, 1.0],
        face_positions_m=[0.0, 0.25, 0.5, 0.75],
        cell_centers_m=[0.125, 0.375, 0.625],
        face_areas_m2=[1.0, 1.0, 1.0, 1.0],
        cell_volumes_m3=[0.25, 0.25, 0.25],
        mobile_entity_mol_m3=[[1.0, 1.0, 1.0], [0.9, 1.0, 1.1]],
        trapped_entity_mol_m3=[[], []],
        left_integrated_coordinate_flow_mol=[0.0, -0.01],
        right_integrated_coordinate_flow_mol=[0.0, -0.01],
        wall_inventory_mol=[0.75, 0.75],
        wall_inventory_residual_mol=[0.0, 0.0],
        total_inventory_residual_mol=[0.0, 0.0],
        concentration_numerical_tolerance_mol_m3=1e-10,
        function_evaluations=10,
        coefficient_basis="authored constant coefficient; exchange test only",
        boundary_basis="authored equal net coordinate flow; exchange test only",
        limitations=["Synthetic conservation identity; no experiment, damage, or failure probability."],
    )
    record = hydrogen_transport_history(**payload)
    restored = HydrogenTransportHistory.model_validate_json(record.model_dump_json())
    if restored.digest_payload() != record.digest_payload():
        raise AssertionError("hydrogen transport JSON round trip changed the physical payload")

    tampered = deepcopy(record.model_dump(mode="json"))
    tampered["wall_inventory_mol"][1] = 0.7
    try:
        HydrogenTransportHistory.model_validate(tampered)
    except ValidationError:
        tamper_rejected = True
    else:
        raise AssertionError("changed hydrogen inventory passed the payload digest")

    misaligned = deepcopy(payload)
    misaligned["mobile_entity_mol_m3"][1].pop()
    try:
        hydrogen_transport_history(**misaligned)
    except ValidationError:
        shape_rejected = True
    else:
        raise AssertionError("misaligned hydrogen concentration passed the exchange contract")

    validation = {
        "schema_version": "matintegrity.hydrogen_transport_exchange_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "contract_source_sha256": hashlib.sha256(Path(hydrogen_exchange.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "payload_digest": record.payload_digest,
        "json_round_trip_preserved": True,
        "tampered_inventory_rejected": tamper_rejected,
        "misaligned_concentration_rejected": shape_rejected,
        "reviewed_provider_revision": REVIEWED_PROVIDER_REVISION,
        "reviewed_provider_result_type": "h2physics.materials.TransportResult",
        "provider_exporter_for_exchange_schema_present_at_reviewed_revision": False,
        "qualification": (
            "Authored exchange-shape, conservation identity, JSON round-trip, and negative-control validation. "
            "The reviewed provider revision was inspected read-only. This is not an end-to-end repository run, "
            "coefficient qualification, experimental validation, damage assessment, or failure-probability validation."
        ),
    }
    target = ROOT / "validation/hydrogen_transport_exchange_contract.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
