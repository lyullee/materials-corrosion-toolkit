"""Synthetic contract example for SIT solid projections during transport."""

from pathlib import Path
from runpy import run_path

from matintegrity.contracts import Evidence
from matintegrity.models.competitive_solid_sit_iteration import (
    CompetitiveSolidSITIteration,
    SITInteraction,
)
from matintegrity.multiphase_equilibrium_transport import CompetitiveSolidEquilibriumTransport


base = run_path(str(Path(__file__).with_name("competitive_solid_equilibrium_transport.py")))
source_request = base["request"]
evidence_sha = "d" * 64
provider_id = "synthetic-sit-provider"
configuration_sha = "e" * 64
transport = source_request.transport.model_copy(update={
    "activity_provider_id": provider_id,
    "activity_configuration_sha256": configuration_sha,
})

cells = []
for index, template in enumerate(source_request.initial_cell_equilibria):
    interactions = (
        SITInteraction(target_species_id="Ca2+", counter_species_id="CO3--", epsilon_kg_mol=0.08, evidence_source_id="synthetic-sit-table", source_record_id="eps-Ca-carbonate", evidence_sha256=evidence_sha),
        SITInteraction(target_species_id="CO3--", counter_species_id="Ca2+", epsilon_kg_mol=0.06, evidence_source_id="synthetic-sit-table", source_record_id="eps-carbonate-Ca", evidence_sha256=evidence_sha),
    )
    cells.append(CompetitiveSolidSITIteration(
        equilibrium=template.equilibrium.model_copy(update={"equilibrium_id": f"synthetic-SIT-cell-{index}"}),
        water_mass_per_solution_volume_kg_L=template.water_mass_per_solution_volume_kg_L,
        debye_huckel_A_at_temperature=0.509,
        A_evidence_source_id="synthetic-sit-table",
        provider_id=provider_id,
        provider_revision="fixture-1",
        configuration_sha256=configuration_sha,
        record_sha256="f" * 64,
        interactions=interactions,
        evidence=(Evidence(source_id="synthetic-sit-table", origin="synthetic", citation="Synthetic wiring values only; not a chemical parameter source.", sha256=evidence_sha),),
        ionic_strength_limit_mol_kg=1.0,
        charge_balance_tolerance_mol_kg=1e-10,
        maximum_outer_iterations=100,
        log_gamma_tolerance=1e-8,
        damping_fraction=0.5,
        water_mass_conversion_reviewed=True,
        temperature_solvent_A_and_standard_state_reviewed=True,
        molarity_standard_state_mapping_reviewed=True,
        complete_interaction_set_and_applicability_reviewed=True,
        competing_solid_sit_applicability_reviewed=True,
        charge_scope_and_solver_settings_reviewed=True,
    ))

request = CompetitiveSolidEquilibriumTransport(
    campaign_id="synthetic-SIT-solid-transport",
    physical_scope_id="synthetic-fixture-only",
    transport=transport,
    initial_cell_equilibria=tuple(cells),
    uniform_temperature_K=source_request.uniform_temperature_K,
    initial_equilibrium_projection_reviewed=True,
    instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed=True,
    fixed_geometry_and_immobile_solid_basis_reviewed=True,
    transport_activity_to_phase_davies_mapping_reviewed=True,
)

if __name__ == "__main__":
    # Contract-only example: no transport or equilibrium calculation is executed.
    print(request.model_dump_json(indent=2))
