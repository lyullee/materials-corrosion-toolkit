"""Synthetic exact-knot external activity history wiring example; not a physical dataset."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.registry import default_registry

root = Path(__file__).resolve().parents[1]
inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
payload = inputs["models"]["integration.aqueous_external_activity_speciation_history"]
provider_id = "synthetic-external-activity-provider"
provider_revision = "example-only-1"
configuration_sha256 = "e" * 64
parameter_record_sha256 = "f" * 64
convention_id = "synthetic_identity_gamma_convention"


def synthetic_provider(state):
    """Return identity gamma values only to demonstrate callback wiring."""
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
context = RunContext(
    asset_id=payload["asset_id"],
    location_id=payload["location_id"],
    time_basis=payload["time_basis"],
)
result = default_registry().run(
    "integration.aqueous_external_activity_speciation_history",
    payload,
    context,
    runtime_dependencies={"activity_provider": synthetic_provider},
)
print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
