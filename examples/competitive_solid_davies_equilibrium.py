"""Synthetic wiring example for Davies-coupled competitive solid equilibrium."""

from pathlib import Path
from runpy import run_path

from matintegrity.registry import default_registry


fixed_gamma_inputs = run_path(str(Path(__file__).with_name("competitive_solid_equilibrium.py")))["inputs"]
inputs = {
    "equilibrium": fixed_gamma_inputs,
    "water_mass_per_solution_volume_kg_L": 0.997,
    "davies_A_at_temperature": 0.509,
    "davies_A_provider_id": "synthetic-example-only",
    "davies_A_provider_revision": "1",
    "davies_A_configuration_digest": "a" * 64,
    "davies_A_record_digest": "b" * 64,
    "ionic_strength_limit_mol_kg": 0.5,
    "charge_balance_tolerance_mol_kg": 1e-10,
    "maximum_outer_iterations": 100,
    "log_gamma_tolerance": 1e-8,
    "damping_fraction": 0.5,
    "water_mass_conversion_reviewed": True,
    "davies_A_temperature_solvent_basis_reviewed": True,
    "molarity_standard_state_and_molality_mapping_reviewed": True,
    "Davies_applicability_to_competing_solids_reviewed": True,
    "charge_scope_and_solver_settings_reviewed": True,
}

result = default_registry().run("chemistry.competitive_solid_davies_equilibrium", inputs)
print(result.model_dump(mode="json"))
