"""Synthetic wiring example for charge- and element-balanced aqueous reactions."""

import json
from pathlib import Path

from matintegrity.models.aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation


root = Path(__file__).resolve().parents[1]
all_inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
request = all_inputs["models"]["chemistry.aqueous_mass_action_speciation"]
request["assessment_id"] = "synthetic-element-balanced-dissociation"
request["species"] = [
    {
        "species_id": "h2a",
        "charge_number": 0,
        "activity_coefficient": 1.0,
        "initial_activity": 0.009,
        "elemental_composition": {"H": 2, "C": 1},
    },
    {
        "species_id": "ha_minus",
        "charge_number": -1,
        "activity_coefficient": 0.9,
        "initial_activity": 0.0001,
        "elemental_composition": {"H": 1, "C": 1},
    },
    {
        "species_id": "h_plus",
        "charge_number": 1,
        "activity_coefficient": 0.9,
        "initial_activity": 0.0001,
        "elemental_composition": {"H": 1},
    },
]
request["reactions"] = [
    {
        "reaction_id": "first-dissociation",
        "log10_equilibrium_constant": -3.5,
        "terms": [
            {"species_id": "h_plus", "coefficient": 1.0},
            {"species_id": "ha_minus", "coefficient": 1.0},
            {"species_id": "h2a", "coefficient": -1.0},
        ],
    }
]
request["constraints"] = [
    {
        "constraint_id": "total-acid",
        "target_mol_L": 0.01,
        "residual_scale_mol_L": 0.01,
        "terms": [
            {"species_id": "h2a", "coefficient": 1.0},
            {"species_id": "ha_minus", "coefficient": 1.0},
        ],
    },
    {
        "constraint_id": "electroneutrality",
        "target_mol_L": 0.0,
        "residual_scale_mol_L": 0.01,
        "terms": [
            {"species_id": "h_plus", "coefficient": 1.0},
            {"species_id": "ha_minus", "coefficient": -1.0},
        ],
    },
]
request["elemental_formula_and_reaction_balance_reviewed"] = True

result = aqueous_mass_action_speciation(AqueousMassActionSystem.model_validate(request))
print(result.model_dump(mode="json"))
