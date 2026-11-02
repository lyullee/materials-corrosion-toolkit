"""Synthetic callback wiring for an external composition-dependent activity model."""

import json
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.models.aqueous_external_activity import (
    ExternalAqueousActivityIteration,
    aqueous_external_activity_self_consistent_speciation,
)


root = Path(__file__).resolve().parents[1]
payloads = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
system_data = payloads["models"]["chemistry.aqueous_mass_action_speciation"]
system_data["assessment_id"] = "synthetic-external-activity-coupling"

provider_id = "synthetic-external-activity-provider"
provider_revision = "example-only-1"
configuration_sha256 = "e" * 64
parameter_record_sha256 = "f" * 64
single_ion_convention_id = "synthetic_identity_gamma_convention"


def synthetic_provider(state):
    """Return a shape-only identity-gamma response; no physical model is implied."""
    return {
        "status": "computed",
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "configuration_sha256": configuration_sha256,
        "parameter_record_sha256": parameter_record_sha256,
        "request_sha256": canonical_digest(state),
        "activity_standard_state": "molality_1_mol_kg_water",
        "single_ion_activity_convention_id": single_ion_convention_id,
        "species_ids": list(state["species_ids"]),
        "ionic_strength_mol_kg_water": state["ionic_strength_mol_kg_water"],
        "activity_coefficients_molality_standard_state": [1.0] * len(state["species_ids"]),
    }


synthetic_provider.provider_id = provider_id
synthetic_provider.provider_revision = provider_revision
synthetic_provider.configuration_sha256 = configuration_sha256
synthetic_provider.parameter_record_sha256 = parameter_record_sha256

request = ExternalAqueousActivityIteration.model_validate({
    "system": system_data,
    "water_mass_per_solution_volume_kg_L": 0.997,
    "ionic_strength_limit_mol_kg": 10.0,
    "charge_balance_tolerance_mol_kg": 1e-8,
    "activity_provider_id": provider_id,
    "activity_provider_revision": provider_revision,
    "activity_configuration_sha256": configuration_sha256,
    "activity_parameter_record_sha256": parameter_record_sha256,
    "single_ion_activity_convention_id": single_ion_convention_id,
    "maximum_outer_iterations": 20,
    "log_gamma_tolerance": 1e-8,
    "damping_fraction": 0.5,
    "water_mass_conversion_reviewed": True,
    "molarity_to_molality_standard_state_mapping_reviewed": True,
    "temperature_and_parameter_support_reviewed": True,
    "complete_inventory_and_charge_scope_reviewed": True,
    "provider_species_order_and_unit_mapping_reviewed": True,
    "single_ion_activity_convention_reviewed": True,
    "provider_parameter_coverage_and_applicability_reviewed": True,
    "deterministic_provider_re_evaluation_reviewed": True,
    "fixed_point_solver_settings_reviewed": True,
    "single_liquid_no_precipitation_scope_reviewed": True,
    "evidence": [{
        "source_id": provider_id,
        "origin": "synthetic",
        "citation": "Project-authored synthetic callback wiring fixture",
        "sha256": parameter_record_sha256,
    }],
})

result = aqueous_external_activity_self_consistent_speciation(
    request, activity_provider=synthetic_provider
)
print(result.model_dump(mode="json"))
