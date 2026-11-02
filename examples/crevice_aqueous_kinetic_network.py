"""Synthetic contract example for a balanced aqueous kinetic network."""

from hashlib import sha256

from matintegrity.contracts import Evidence
from matintegrity.models.crevice_kinetic_network import (
    CreviceAqueousKineticNetwork,
    CreviceKineticInterval,
    CreviceKineticReaction,
    CreviceKineticSpecies,
    CreviceKineticTerm,
    solve_crevice_aqueous_kinetic_network,
)


fixture_digest = sha256(b"matintegrity synthetic crevice kinetic example v1").hexdigest()
request = CreviceAqueousKineticNetwork(
    assessment_id="synthetic-crevice-kinetic-1",
    asset_id="synthetic-asset",
    physical_scope_id="synthetic-mixed-volume",
    clock_id="synthetic-clock",
    control_volume_m3=1e-6,
    species=(
        CreviceKineticSpecies(
            species_id="H2CO3",
            charge_number=0,
            elemental_composition={"H": 2.0, "C": 1.0, "O": 3.0},
            initial_concentration_mol_m3=1.0,
        ),
        CreviceKineticSpecies(
            species_id="H_plus",
            charge_number=1,
            elemental_composition={"H": 1.0},
            initial_concentration_mol_m3=0.0,
        ),
        CreviceKineticSpecies(
            species_id="HCO3_minus",
            charge_number=-1,
            elemental_composition={"H": 1.0, "C": 1.0, "O": 3.0},
            initial_concentration_mol_m3=0.0,
        ),
    ),
    reactions=(CreviceKineticReaction(
        reaction_id="synthetic-carbonic-dissociation",
        reactants=(CreviceKineticTerm(species_id="H2CO3", stoichiometric_coefficient=1),),
        products=(
            CreviceKineticTerm(species_id="H_plus", stoichiometric_coefficient=1),
            CreviceKineticTerm(species_id="HCO3_minus", stoichiometric_coefficient=1),
        ),
        forward_rate_constant_by_interval=(1e-4,),
        forward_rate_constant_units="s^-1 for this first-order reactant term",
        reverse_rate_constant_by_interval=(1e-7,),
        reverse_rate_constant_units="m3 mol^-1 s^-1 for this second-order product term",
    ),),
    intervals=(CreviceKineticInterval(
        interval_id="synthetic-step-1",
        start_time_s=0.0,
        end_time_s=3600.0,
        temperature_K=298.15,
        exchange_flow_m3_s=0.0,
        bulk_concentration_mol_m3_by_species={"H2CO3": 0.0, "H_plus": 0.0, "HCO3_minus": 0.0},
    ),),
    solver_method="BDF",
    relative_tolerance=1e-8,
    absolute_tolerance_mol_m3=1e-12,
    maximum_function_evaluations=100000,
    maximum_step_s=300.0,
    temperature_support_min_K=290.0,
    temperature_support_max_K=310.0,
    model_provider_id="synthetic-crevice-kinetics",
    model_revision="example-v1",
    evidence=(Evidence(
        source_id="synthetic-crevice-kinetics",
        origin="synthetic",
        citation="Project-authored synthetic API fixture; not measured data",
        sha256=fixture_digest,
    ),),
    usage_rights_evidence=(Evidence(
        source_id="synthetic-crevice-kinetics",
        origin="synthetic",
        citation="Invented example values with project-authored unrestricted reuse",
        license_id="synthetic-example-only",
        sha256=fixture_digest,
    ),),
    reaction_network_and_conservation_reviewed=True,
    kinetic_parameter_units_and_calibration_reviewed=True,
    mixed_volume_and_exchange_boundary_reviewed=True,
    temperature_knot_mapping_and_parameter_support_reviewed=True,
    usage_rights_reviewed=True,
    computational_use_authorized=True,
)

if __name__ == "__main__":
    print(solve_crevice_aqueous_kinetic_network(request).model_dump(mode="json"))
