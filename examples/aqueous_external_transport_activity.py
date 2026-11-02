"""Synthetic restricted-transport callback wiring; not a physical electrolyte model."""

import json
from pathlib import Path

import numpy as np

from matintegrity.contracts import canonical_digest
from matintegrity.models.aqueous_external_activity import (
    ExternalAqueousTransportActivity,
    build_external_aqueous_transport_activity_callback,
)

root = Path(__file__).resolve().parents[1]
models = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"]
system = models["chemistry.aqueous_mass_action_speciation"]
provider_id = "synthetic-external-transport-activity-provider"
provider_revision = "example-only-1"
configuration_sha256 = "a" * 64
parameter_record_sha256 = "b" * 64
convention_id = "synthetic_identity_gamma_convention"


def synthetic_provider(state):
    """Identity-gamma output demonstrates data mapping only."""
    return {
        "status": "computed",
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "configuration_sha256": configuration_sha256,
        "parameter_record_sha256": parameter_record_sha256,
        "request_sha256": canonical_digest(state),
        "activity_standard_state": "molality_1_mol_kg_water",
        "single_ion_activity_convention_id": convention_id,
        "species_ids": list(state["species_ids"]),
        "ionic_strength_mol_kg_water": state["ionic_strength_mol_kg_water"],
        "activity_coefficients_molality_standard_state": [1.0] * len(state["species_ids"]),
    }


synthetic_provider.provider_id = provider_id
synthetic_provider.provider_revision = provider_revision
synthetic_provider.configuration_sha256 = configuration_sha256
synthetic_provider.parameter_record_sha256 = parameter_record_sha256
request = ExternalAqueousTransportActivity.model_validate({
    "temperature_K": system["temperature_K"],
    "species_ids": [row["species_id"] for row in system["species"]],
    "charge_numbers": [row["charge_number"] for row in system["species"]],
    "water_mass_per_solution_volume_kg_L": 0.997,
    "ionic_strength_limit_mol_kg": 10.0,
    "activity_provider_id": provider_id,
    "activity_provider_revision": provider_revision,
    "activity_configuration_sha256": configuration_sha256,
    "activity_parameter_record_sha256": parameter_record_sha256,
    "single_ion_activity_convention_id": convention_id,
    "water_mass_and_molality_conversion_reviewed": True,
    "species_order_charge_and_inventory_reviewed": True,
    "temperature_solvent_and_parameter_coverage_reviewed": True,
    "single_ion_convention_and_transport_chemical_potential_reviewed": True,
    "no_precipitation_or_phase_change_reviewed": True,
    "deterministic_provider_re_evaluation_reviewed": True,
    "evidence": [{
        "source_id": provider_id,
        "origin": "synthetic",
        "citation": "Project-authored callback wiring fixture; no physical output is represented.",
        "sha256": parameter_record_sha256,
    }],
})
callback = build_external_aqueous_transport_activity_callback(
    request, activity_provider=synthetic_provider
)
state_mol_m3 = np.full((len(request.species_ids), 3), 100.0)
gamma_molality = callback(0.0, state_mol_m3)
print(json.dumps({
    "configuration_sha256": callback.configuration_sha256,
    "species_ids": list(callback.species_ids),
    "gamma_molality_shape": list(gamma_molality.shape),
    "runtime_trace": callback.runtime_trace,
}, ensure_ascii=False, indent=2))
