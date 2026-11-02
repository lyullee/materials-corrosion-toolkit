"""Build a synthetic multicomponent transport/solid-equilibrium wiring request."""

from pathlib import Path
from runpy import run_path

from matintegrity.multiphase_equilibrium_transport import CompetitiveSolidEquilibriumTransport
from matintegrity.models.competitive_solid_activity_iteration import CompetitiveSolidDaviesIteration
from matintegrity.restricted_transport import RestrictedTransportRequest


fixed_gamma = run_path(str(Path(__file__).with_name("competitive_solid_equilibrium.py")))["inputs"]
fixed_gamma["aqueous_species"][2]["initial_concentration_mol_m3"] = 10.0
species = fixed_gamma["aqueous_species"]
concentrations = [row["initial_concentration_mol_m3"] for row in species]
temperature_K = fixed_gamma["temperature_K"]
activity_digest = "a" * 64

transport = RestrictedTransportRequest(
    simulation_id="synthetic-competitive-solid-transport",
    species_ids=tuple(row["species_id"] for row in species),
    length_m=2e-4,
    cell_count=2,
    diffusivity_m2_s=(1e-9, 1e-9, 1e-9),
    initial_concentration_mol_m3=tuple((value, value) for value in concentrations),
    mouth_concentration_mol_m3=tuple(concentrations),
    output_times_s=(0.0, 1.0, 2.0),
    reaction_provider_id="synthetic-zero-transport-reaction",
    reaction_configuration_sha256="b" * 64,
    geometry_diffusion_reaction_basis_reviewed=True,
    charge_numbers=(2, -2, -2),
    activity_provider_id="synthetic-davies-provider",
    activity_configuration_sha256=activity_digest,
    activity_chemical_potential_and_tracer_diffusivity_reviewed=True,
    callbacks_cell_locality_reviewed=True,
)

cells = []
for index in range(transport.cell_count):
    equilibrium = dict(fixed_gamma, equilibrium_id=f"synthetic-cell-{index}")
    cells.append(CompetitiveSolidDaviesIteration(
        equilibrium=equilibrium,
        water_mass_per_solution_volume_kg_L=0.997,
        davies_A_at_temperature=0.509,
        davies_A_provider_id="synthetic-davies-provider",
        davies_A_provider_revision="fixture-1",
        davies_A_configuration_digest=activity_digest,
        davies_A_record_digest="c" * 64,
        ionic_strength_limit_mol_kg=0.5,
        charge_balance_tolerance_mol_kg=1e-10,
        maximum_outer_iterations=100,
        log_gamma_tolerance=1e-8,
        damping_fraction=0.5,
        water_mass_conversion_reviewed=True,
        davies_A_temperature_solvent_basis_reviewed=True,
        molarity_standard_state_and_molality_mapping_reviewed=True,
        Davies_applicability_to_competing_solids_reviewed=True,
        charge_scope_and_solver_settings_reviewed=True,
    ))

request = CompetitiveSolidEquilibriumTransport(
    campaign_id="synthetic-competitive-solid-transport",
    physical_scope_id="synthetic-fixture-only",
    transport=transport,
    initial_cell_equilibria=tuple(cells),
    uniform_temperature_K=temperature_K,
    initial_equilibrium_projection_reviewed=True,
    instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed=True,
    fixed_geometry_and_immobile_solid_basis_reviewed=True,
    transport_activity_to_phase_davies_mapping_reviewed=True,
)

if __name__ == "__main__":
    # This only validates and prints the contract; transport callbacks are not run.
    print(request.model_dump_json(indent=2))
