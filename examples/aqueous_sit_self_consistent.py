"""Wire a synthetic mass-action system to a caller-owned SIT table."""

import json
from pathlib import Path

import numpy as np

from matintegrity.models.aqueous_activity_iteration import (
    AqueousSITIteration,
    aqueous_sit_self_consistent_speciation,
    build_sit_transport_activity_callback,
    build_sit_transport_saturation_callback,
)
from matintegrity.models.aqueous_mass_action import AqueousMassActionSystem
from matintegrity.models.aqueous_saturation_screening import AqueousSaturationScreen


root = Path(__file__).resolve().parents[1]
all_inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
system = all_inputs["models"]["chemistry.aqueous_mass_action_speciation"]
system["assessment_id"] = "synthetic-sit-mass-action-coupling"

evidence = [{
    "source_id": "synthetic-sit-coupling-fixture",
    "origin": "synthetic",
    "citation": "Project-authored synthetic activity-coupling fixture",
    "sha256": "f" * 64,
}]
request_data = {
    "schema_version": "matintegrity.aqueous_sit_iteration.v2",
    "system": system,
    "water_mass_per_solution_volume_kg_L": 0.997,
    "debye_huckel_A_at_temperature": 0.5,
    "A_evidence_source_id": "synthetic-sit-coupling-fixture",
    "sit_provider_id": "synthetic-SIT-provider",
    "sit_provider_revision": "example-only-1",
    "sit_configuration_sha256": "e" * 64,
    "sit_record_sha256": "f" * 64,
    "ionic_strength_limit_mol_kg": 1.0,
    "charge_balance_tolerance_mol_kg": 1e-8,
    "interactions": [
        {
            "target_species_id": "h_plus",
            "counter_species_id": "ha_minus",
            "epsilon_kg_mol": 0.04,
            "evidence_source_id": "synthetic-sit-coupling-fixture",
            "source_record_id": "synthetic-h-ha",
            "evidence_sha256": "f" * 64,
        },
        {
            "target_species_id": "ha_minus",
            "counter_species_id": "h_plus",
            "epsilon_kg_mol": 0.02,
            "evidence_source_id": "synthetic-sit-coupling-fixture",
            "source_record_id": "synthetic-ha-h",
            "evidence_sha256": "f" * 64,
        },
        {
            "target_species_id": "a2_minus",
            "counter_species_id": "h_plus",
            "epsilon_kg_mol": 0.03,
            "evidence_source_id": "synthetic-sit-coupling-fixture",
            "source_record_id": "synthetic-a2-h",
            "evidence_sha256": "f" * 64,
        },
    ],
    "maximum_outer_iterations": 100,
    "log_gamma_tolerance": 1e-8,
    "damping_fraction": 0.5,
    "water_mass_conversion_reviewed": True,
    "temperature_solvent_and_A_basis_reviewed": True,
    "molarity_to_molality_standard_state_mapping_reviewed": True,
    "complete_inventory_and_charge_scope_reviewed": True,
    "interaction_parameter_set_completeness_and_applicability_reviewed": True,
    "fixed_point_solver_settings_reviewed": True,
    "single_liquid_no_precipitation_scope_reviewed": True,
    "evidence": evidence,
}

request = AqueousSITIteration.model_validate(request_data)
result = aqueous_sit_self_consistent_speciation(request)
print(result.model_dump(mode="json"))

# Transport adapter wiring: gamma is evaluated per mouth/cell from
# species-by-location concentrations expressed in mol/m3.
transport_species_ids = tuple(row["species_id"] for row in system["species"])
activity_callback = build_sit_transport_activity_callback(
    request,
    transport_species_ids=transport_species_ids,
    temperature_K=system["temperature_K"],
)
print({
    "transport_activity_coefficients": activity_callback(
        0.0,
        np.ones((len(transport_species_ids), 2), dtype=float),
    ).tolist(),
    "provider_id": activity_callback.provider_id,
    "configuration_sha256": activity_callback.configuration_sha256,
})

# Synthetic Ksp fixture: these values demonstrate composition only and have
# no thermodynamic or engineering interpretation.
screen_template = AqueousSaturationScreen.model_validate({
    "assessment_id": "synthetic-sit-solid-screen",
    "solution_id": request.system.solution_id,
    "temperature_K": request.system.temperature_K,
    "activity_standard_state": "molality_relative_to_1_mol_per_kg_water",
    "species": [
        {"species_id": species_id, "dimensionless_activity": 1.0}
        for species_id in transport_species_ids
    ],
    "candidate_solids": [
        {
            "solid_id": "synthetic-phase-a",
            "log10_solubility_product": -2.0,
            "solubility_record_id": "synthetic-ksp-a",
            "solubility_evidence_source_id": evidence[0]["source_id"],
            "terms": [{"species_id": transport_species_ids[0], "stoichiometric_exponent": 1.0}],
        },
        {
            "solid_id": "synthetic-phase-b",
            "log10_solubility_product": -3.0,
            "solubility_record_id": "synthetic-ksp-b",
            "solubility_evidence_source_id": evidence[0]["source_id"],
            "terms": [{"species_id": transport_species_ids[1], "stoichiometric_exponent": 1.0}],
        },
    ],
    "activity_state_provider_id": request.sit_provider_id,
    "activity_state_digest": "0" * 64,
    "solubility_data_provider_id": "synthetic-ksp-provider",
    "solubility_data_digest": "a" * 64,
    "complete_species_inventory_reviewed": True,
    "compatible_standard_states_reviewed": True,
    "equilibrium_constants_temperature_reviewed": True,
    "evidence": evidence,
})
saturation_callback = build_sit_transport_saturation_callback(
    request,
    screen_template=screen_template,
    transport_species_ids=transport_species_ids,
    saturation_provider_id="synthetic-sit-saturation",
    saturation_provider_revision="example-only-1",
)
print({
    "cell_saturation_ratios": saturation_callback(
        0.0,
        0,
        np.ones(len(transport_species_ids), dtype=float),
        {},
    ),
    "provider_id": saturation_callback.provider_id,
    "configuration_sha256": saturation_callback.configuration_sha256,
})
