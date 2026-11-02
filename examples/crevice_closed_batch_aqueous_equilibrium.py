from __future__ import annotations

"""Construct a synthetic closed-batch request without validating or solving it.

All values are API-shape fixtures only. They are not chemical data, and the
review/authorization fields intentionally remain false. A real workflow must
replace them with caller-approved evidence and explicit review decisions before
creating the typed request or evaluating the model.
"""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
system = base["models"]["chemistry.aqueous_mass_action_speciation"]
system["assessment_id"] = "synthetic-closed-batch-input-shape-only"
system["solution_id"] = "synthetic-acid-water-input-shape-only"

# The base fixture declares H2A <-> H+ + HA-; HA- <-> H+ + A2-;
# and water ionization. Initial neutral H2A inventory is 0.01 mol; all
# charged species start at zero, so the initial batch charge is exactly zero.
# The component map H2A + HA- + A2- is conserved by every declared reaction.
request_draft = {
    "schema_version": "matintegrity.crevice_closed_batch_aqueous_equilibrium.v1",
    "assessment_id": "synthetic-closed-batch-input-shape-only",
    "cell_id": "synthetic-cell-0",
    "solution_volume_L": 1.0,
    "aqueous_activity_request": {
        "schema_version": "matintegrity.aqueous_davies_iteration.v1",
        "system": system,
        "water_mass_per_solution_volume_kg_L": 0.997,
        "davies_A_at_temperature": 0.509,
        "davies_A_provider_id": "synthetic-only-provider",
        "davies_A_provider_revision": "fixture-1",
        "davies_A_configuration_digest": "b" * 64,
        "davies_A_record_digest": "a" * 64,
        "ionic_strength_limit_mol_kg": 0.5,
        "charge_balance_tolerance_mol_kg": 1e-8,
        "maximum_outer_iterations": 100,
        "log_gamma_tolerance": 1e-8,
        "damping_fraction": 0.5,
        "water_mass_conversion_reviewed": False,
        "Davies_A_temperature_solvent_basis_reviewed": False,
        "molarity_to_molality_standard_state_mapping_reviewed": False,
        "complete_inventory_and_charge_scope_reviewed": False,
        "fixed_point_solver_settings_reviewed": False,
        "single_liquid_no_precipitation_scope_reviewed": False,
        "evidence": [{
            "source_id": "synthetic-only-provider",
            "origin": "synthetic",
            "citation": "Illustrative API-shape fixture; not a thermodynamic source",
            "sha256": "a" * 64,
        }],
    },
    "initial_species_amounts": [
        {"species_id": "h2a", "amount_mol": 0.01},
        {"species_id": "ha_minus", "amount_mol": 0.0},
        {"species_id": "a2_minus", "amount_mol": 0.0},
        {"species_id": "h_plus", "amount_mol": 0.0},
        {"species_id": "oh_minus", "amount_mol": 0.0},
    ],
    "constraint_roles": [
        {"constraint_id": "total-dissolved-acid", "role": "conserved_component", "component_id": "acid-moiety"},
        {"constraint_id": "electroneutrality", "role": "charge_neutrality"},
    ],
    "conserved_components": [{
        "component_id": "acid-moiety",
        "species_coefficients": [
            {"species_id": "h2a", "coefficient": 1.0},
            {"species_id": "ha_minus", "coefficient": 1.0},
            {"species_id": "a2_minus", "coefficient": 1.0},
        ],
    }],
    "maximum_total_equilibrium_iterations": 20_000,
    "absolute_charge_inventory_tolerance_mol_eq": 1e-12,
    "absolute_component_closure_tolerance_mol": 1e-12,
    "relative_component_closure_tolerance": 1e-8,
    "role_map_and_charge_scope_reviewed": False,
    "closed_inventory_scope_reviewed": False,
    "single_liquid_no_precipitation_scope_reviewed": False,
    "equilibrium_and_activity_provider_scope_reviewed": False,
    "computational_use_authorized": False,
}

# This is an intentionally unapproved draft. Do not pass it to
# CreviceClosedBatchAqueousEquilibriumRequest.model_validate() or call the
# evaluator until the evidence and all review gates have been replaced by real,
# caller-approved values.
print(json.dumps(request_draft, ensure_ascii=False, indent=2))
