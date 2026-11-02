"""Synthetic end-to-end crevice electrochemistry wiring; never material data."""

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.registry import default_registry
from matintegrity.models.aqueous_mass_action import AqueousMassActionSystem
from matintegrity.models.external_crevice_solver import (
    ExternalCreviceSolverHistory,
    ExternalCreviceVelocityProvider,
)

registry = default_registry()
activity_evidence = Evidence(
    source_id="synthetic-activity-source",
    origin="synthetic",
    citation="Synthetic activity fixture for API wiring only; not measured or validated.",
)
standard_evidence = Evidence(
    source_id="synthetic-standard-potential-source",
    origin="synthetic",
    citation="Synthetic standard-potential fixture for API wiring only.",
)
kinetics_evidence = {
    "redox_A": Evidence(
        source_id="synthetic-fe-kinetics",
        origin="synthetic",
        citation="Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
    ),
    "redox_B": Evidence(
        source_id="synthetic-h-kinetics",
        origin="synthetic",
        citation="Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
    ),
}
asset_id = "synthetic-loop"
location_id = "synthetic-crevice"
physical_scope_id = "synthetic-wet-surface"
clock_id = "synthetic-elapsed-seconds"
source_inventory_sha256 = "a" * 64
times = (0.0, 30.0, 60.0)
temperatures = (298.15, 298.15, 298.15)
context = RunContext(
    asset_id=asset_id,
    location_id=location_id,
    time_basis=clock_id,
    evidence=(activity_evidence, standard_evidence, *kinetics_evidence.values()),
)

# Two separate Nernst profiles share the same asset, scope, clock, knots,
# temperature and source inventory, while caller parameters set distinct E0.
redox_profiles = {}
for reaction_id, species_id, standard_potential_V in (
    ("redox_A", "OxidizedA", 0.0),
    ("redox_B", "OxidizedB", 0.30),
):
    nernst_inputs = {
        "assessment_id": f"synthetic-{reaction_id}-nernst",
        "asset_id": asset_id,
        "location_id": location_id,
        "physical_scope_id": physical_scope_id,
        "clock_id": clock_id,
        "source_inventory_sha256": source_inventory_sha256,
        "reaction_id": reaction_id,
        "standard_potential_reference_id": "SHE",
        "reaction_quotient_stoichiometry": {species_id: 1.0},
        "electron_number": 1,
        "elapsed_time_s": times,
        "temperature_K": temperatures,
        "standard_potential_V": (standard_potential_V,) * len(times),
        "species_activity_history": {species_id: (1.0,) * len(times)},
        "activity_provider_id": activity_evidence.source_id,
        "activity_provider_revision": "synthetic-1",
        "activity_configuration_sha256": "b" * 64,
        "activity_record_sha256": "c" * 64,
        "standard_potential_provider_id": standard_evidence.source_id,
        "standard_potential_provider_revision": "synthetic-1",
        "standard_potential_configuration_sha256": "d" * 64,
        "standard_potential_record_sha256": "e" * 64,
        "redox_reaction_direction_and_electron_number_reviewed": True,
        "activity_standard_state_and_species_mapping_reviewed": True,
        "standard_potential_temperature_history_reviewed": True,
        "local_activity_history_applicability_reviewed": True,
        "potential_only_no_rate_or_acceptance_reviewed": True,
        "computational_use_authorized": True,
        "evidence": (activity_evidence, standard_evidence),
    }
    redox_profiles[reaction_id] = registry.run(
        "degradation.crevice_nernst_potential_history", nernst_inputs, context
    )

# Same area basis and kinetic support yield a shared potential between the two
# equilibrium potentials for this synthetic symmetric fixture.
branches = []
for reaction_id, species_id, pool_species in (("redox_A", "OxidizedA", "PoolA"), ("redox_B", "OxidizedB", "PoolB")):
    profile = redox_profiles[reaction_id]
    branches.append({
        "reaction_id": reaction_id,
        "nernst_result": profile.model_dump(mode="json"),
        "nernst_result_sha256": canonical_digest(profile.model_dump(mode="json")),
        "reference_electrode_id": "SHE",
        "exposed_area_m2": 1.0,
        "exchange_current_density_A_m2": 1.0e-5,
        "electron_number": 1,
        "anodic_transfer_coefficient": 0.5,
        "cathodic_transfer_coefficient": 0.5,
        "minimum_overpotential_V": -0.5,
        "maximum_overpotential_V": 0.5,
        "stoichiometric_species_coefficients": {pool_species: 1.0},
        "kinetics_provider_id": kinetics_evidence[reaction_id].source_id,
        "kinetics_provider_revision": "synthetic-1",
        "kinetics_calibration_sha256": "f" * 64,
        "kinetics_and_anodic_direction_reviewed": True,
        "species_flux_mapping_and_area_basis_reviewed": True,
        "evidence": (kinetics_evidence[reaction_id],),
    })
mixed_result = registry.run(
    "electrochemistry.crevice_mixed_potential_history",
    {
        "assessment_id": "synthetic-two-reaction-mixed-potential",
        "asset_id": asset_id,
        "location_id": location_id,
        "physical_scope_id": physical_scope_id,
        "clock_id": clock_id,
        "common_reference_electrode_id": "SHE",
        "reference_area_m2": 2.0,
        "reactions": tuple(branches),
        "quasi_steady_local_balance_reviewed": True,
        "negligible_solution_ohmic_drop_reviewed": True,
        "common_electronic_potential_basis_reviewed": True,
        "reaction_set_and_area_partition_complete_reviewed": True,
        "computational_use_authorized": True,
        "evidence": (activity_evidence, standard_evidence, *kinetics_evidence.values()),
    },
    context,
)

transfer_result = registry.run(
    "integration.crevice_electrochemical_inventory_transfer",
    {
        "assessment_id": "synthetic-reference-area-transfer",
        "mixed_potential_result": mixed_result.model_dump(mode="json"),
        "mixed_potential_result_sha256": canonical_digest(mixed_result.model_dump(mode="json")),
        "reference_area_m2": 2.0,
        "piecewise_linear_flux_between_knots_reviewed": True,
        "constant_reference_area_reviewed": True,
        "stoichiometric_inward_sign_convention_reviewed": True,
        "computational_use_authorized": True,
    },
    context,
)

metal_data_sha256 = canonical_digest({
    "material_condition_id": "synthetic-fe-condition-v1",
    "molar_mass_kg_mol": 0.055845,
    "density_kg_m3": 7870.0,
})
metal_data_evidence = Evidence(
    source_id="synthetic-metal-property-source",
    origin="synthetic",
    citation="Synthetic metal-property values for API wiring only; not material data.",
    sha256=metal_data_sha256,
    locator="examples/crevice_electrochemical_composition.py",
)
metal_loss_result = registry.run(
    "integration.electrochemical_partial_current_metal_loss",
    {
        "assessment_id": "synthetic-electrochemical-metal-loss",
        "material_condition_id": "synthetic-fe-condition-v1",
        "mixed_potential_result": mixed_result.model_dump(mode="json"),
        "mixed_potential_result_sha256": canonical_digest(mixed_result.model_dump(mode="json")),
        "metal_reactions": ({
            "reaction_id": "redox_A",
            "metal_species_id": "Fe2+",
            "metal_atoms_per_reaction_extent": 1.0,
            "molar_mass_kg_mol": 0.055845,
            "density_kg_m3": 7870.0,
            "metal_data_provider_id": metal_data_evidence.source_id,
            "metal_data_provider_revision": "synthetic-1",
            "metal_data_record_id": "synthetic-fe-property-record-v1",
            "metal_data_sha256": metal_data_sha256,
            "anodic_direction_is_metal_dissolution_reviewed": True,
            "alloy_and_metal_basis_reviewed": True,
            "evidence": (metal_data_evidence,),
        },),
        "linear_current_reconstruction_reviewed": True,
        "mixed_potential_reference_area_reviewed": True,
        "reaction_to_removed_metal_mapping_reviewed": True,
        "uniform_recession_over_mapped_area_reviewed": True,
        "computational_use_authorized": True,
    },
    context,
)

composition_result = registry.run(
    "integration.crevice_electrochemical_composition_history",
    {
        "assessment_id": "synthetic-well-mixed-composition",
        "transfer_result": transfer_result.model_dump(mode="json"),
        "transfer_result_sha256": canonical_digest(transfer_result.model_dump(mode="json")),
        "initial_inventory": (
            {"species_id": "PoolA", "initial_amount_mol": 0.01},
            {"species_id": "PoolB", "initial_amount_mol": 0.02},
        ),
        "liquid_volume_history": tuple(
            {"time_s": time_s, "liquid_volume_m3": 1.0e-3}
            for time_s in times
        ),
        "complete_species_inventory_reviewed": True,
        "all_other_sources_and_sinks_included_reviewed": True,
        "well_mixed_single_volume_reviewed": True,
        "fixed_basis_and_interval_transfer_mapping_reviewed": True,
        "computational_use_authorized": True,
    },
    context,
)

print("mixed-potential history:")
print(mixed_result.model_dump_json(indent=2))
print("area-scaled species inventory transfer:")
print(transfer_result.model_dump_json(indent=2))
print("synthetic partial-current metal-loss history:")
print(metal_loss_result.model_dump_json(indent=2))

# CREV-1: map each selected reaction's cumulative signed transferred volume to
# explicit slit cells. Equal fractions are synthetic wiring data, never a
# default spatial law. Real use must supply a reviewed distribution at each
# exact metal-loss knot.
crevice_geometry_result = registry.run(
    "integration.electrochemical_metal_loss_to_crevice_geometry",
    {
        "assessment_id": "synthetic-electrochemical-crevice-geometry",
        "metal_loss_result": metal_loss_result.model_dump(mode="json"),
        "metal_loss_result_sha256": canonical_digest(metal_loss_result.model_dump(mode="json")),
        "geometry_id": "synthetic-two-cell-slit",
        "geometry_source_sha256": "9" * 64,
        "cell_widths_m": (0.005, 0.005),
        "initial_cell_aperture_m": (1.0e-3, 1.0e-3),
        "transverse_width_m": 0.1,
        "reference_cross_section_m2": 1.0e-4,
        "reactive_broad_face_count": 1,
        "cell_volume_allocations": ({
            "reaction_id": "redox_A",
            "cumulative_cell_volume_fraction": ((0.5, 0.5), (0.5, 0.5), (0.5, 0.5)),
        },),
        "supported_minimum_aperture_m": 1.0e-5,
        "supported_maximum_aperture_m": 5.0e-3,
        "reaction_surface_to_slit_face_mapping_reviewed": True,
        "cell_volume_allocation_basis_reviewed": True,
        "reaction_volume_conservation_reviewed": True,
        "wall_recession_is_per_combined_reactive_area_reviewed": True,
        "opposing_face_recession_is_equal_reviewed": False,
        "cell_center_to_face_mapping_reviewed": True,
        "geometry_basis_reviewed": True,
        "computational_use_authorized": True,
    },
    context,
)
print("synthetic electrochemical metal-loss to crevice-geometry history:")
print(crevice_geometry_result.model_dump_json(indent=2))

# CREV-2: synthetic provider-neutral external solver receipt. It is only a
# schema/API fixture; no external CFD solver or transport consumer is run.
solver_result_sha256 = "f" * 64
solver_evidence = Evidence(
    source_id="synthetic-cfd-provider",
    origin="synthetic",
    citation="Synthetic solver receipt fixture; not CFD data or validation.",
    sha256=solver_result_sha256,
)
geometry_values = crevice_geometry_result.values
solver_receipt_input = {
    "assessment_id": "synthetic-external-crevice-solver-receipt",
    "provider_id": solver_evidence.source_id,
    "provider_revision": "synthetic-1",
    "provider_run_id": "synthetic-run-001",
    "time_basis_id": clock_id,
    "provider_result_sha256": solver_result_sha256,
    "mesh_revision": "synthetic-two-cell-mesh-v1",
    "geometry_result": crevice_geometry_result.model_dump(mode="json"),
    "geometry_result_sha256": canonical_digest(crevice_geometry_result.model_dump(mode="json")),
    "coordinate_system_id": "synthetic-slit-axial-m",
    "coordinate_origin": "mouth",
    "positive_axial_direction": "mouth_to_tip",
    "pressure_unit": "Pa",
    "velocity_unit": "m/s",
    "length_unit": "m",
    "time_unit": "s",
    "elapsed_time_s": tuple(row["elapsed_time_s"] for row in geometry_values["geometry_states"]),
    "face_positions_m": (0.0, 0.005, 0.01),
    "cell_widths_m": (0.005, 0.005),
    "cell_aperture_m": tuple(tuple(row["cell_aperture_m"]) for row in geometry_values["geometry_states"]),
    "face_pressure_Pa": ((1000.0, 750.0, 500.0), (1000.0, 750.0, 500.0), (1000.0, 750.0, 500.0)),
    "face_velocity_m_s": ((1e-5, 1e-5, 1e-5), (1e-5, 1e-5, 1e-5), (1e-5, 1e-5, 1e-5)),
    "time_interpolation": "piecewise_linear",
    "evidence": (solver_evidence,),
    "source_result_digest_reviewed": True,
    "coordinate_and_unit_mapping_reviewed": True,
    "face_order_and_velocity_sign_reviewed": True,
    "mesh_to_geometry_mapping_reviewed": True,
    "geometry_revision_and_time_alignment_reviewed": True,
    "piecewise_linear_velocity_interpolation_reviewed": True,
    "computational_use_authorized": True,
}
solver_receipt_result = registry.run(
    "integration.external_crevice_solver_receipt", solver_receipt_input, context
)
solver_velocity_provider = ExternalCreviceVelocityProvider(
    ExternalCreviceSolverHistory.model_validate(solver_receipt_input)
)
print("synthetic external solver exchange receipt:")
print(solver_receipt_result.model_dump_json(indent=2))
print("consumer callback contract:", solver_velocity_provider.configuration_sha256)

print("caller-volume composition history:")
print(composition_result.model_dump_json(indent=2))


# Each exact output knot receives a caller-owned aqueous network and a
# temperature-specific parameter set. PoolA/PoolB are neutral synthetic
# bookkeeping species used only to demonstrate the adapter interface.
reaction_evidence = Evidence(
    source_id="synthetic-aqueous-equilibrium",
    origin="synthetic",
    citation="Synthetic equilibrium constant for API wiring only; not chemical data.",
)
aqueous_systems = tuple(
    AqueousMassActionSystem.model_validate({
        "assessment_id": f"synthetic-aqueous-knot-{index}",
        "solution_id": "synthetic-well-mixed-pool",
        "temperature_K": state["temperature_K"],
        "activity_standard_state": "molarity_1_mol_L",
        "species": (
            {"species_id": "PoolA", "charge_number": 0, "activity_coefficient": 1.0, "initial_activity": 1.0e-3},
            {"species_id": "PoolB", "charge_number": 0, "activity_coefficient": 1.0, "initial_activity": 1.0e-3},
        ),
        "reactions": ({
            "reaction_id": "synthetic_pool_exchange",
            "log10_equilibrium_constant": 0.0,
            "terms": (
                {"species_id": "PoolA", "coefficient": -1.0},
                {"species_id": "PoolB", "coefficient": 1.0},
            ),
        },),
        "constraints": ({
            "constraint_id": "synthetic_pool_total",
            "target_mol_L": 1.0e-3,
            "residual_scale_mol_L": 1.0e-3,
            "terms": (
                {"species_id": "PoolA", "coefficient": 1.0},
                {"species_id": "PoolB", "coefficient": 1.0},
            ),
        },),
        "activity_provider_id": activity_evidence.source_id,
        "activity_provider_revision": "synthetic-1",
        "activity_configuration_digest": "1" * 64,
        "activity_record_digest": "2" * 64,
        "equilibrium_provider_id": reaction_evidence.source_id,
        "equilibrium_provider_revision": "synthetic-1",
        "equilibrium_configuration_digest": "3" * 64,
        "equilibrium_record_digest": "4" * 64,
        "complete_aqueous_species_inventory_reviewed": True,
        "reaction_stoichiometry_and_constant_reviewed": True,
        "balance_constraints_and_charge_scope_reviewed": True,
        "fixed_activity_coefficients_and_standard_state_reviewed": True,
        "temperature_and_provider_lineage_reviewed": True,
        "initial_activity_guess_and_solver_tolerance_reviewed": True,
        "single_liquid_phase_and_no_precipitation_reviewed": True,
        "evidence": (activity_evidence, reaction_evidence),
    })
    for index, state in enumerate(composition_result.values["composition_history"])
)
aqueous_history_result = registry.run(
    "integration.crevice_composition_to_aqueous_mass_action_history",
    {
        "assessment_id": "synthetic-crevice-aqueous-speciation-history",
        "composition_result": composition_result.model_dump(mode="json"),
        "composition_result_sha256": canonical_digest(composition_result.model_dump(mode="json")),
        "mass_action_systems_by_knot": aqueous_systems,
        "composition_derived_constraint_ids": ("synthetic_pool_total",),
        "composition_mapping_and_constraint_basis_reviewed": True,
        "composition_derived_constraint_semantics_reviewed": True,
        "zero_concentration_seed_is_numerical_only_reviewed": True,
        "each_temperature_specific_parameter_set_reviewed": True,
        "no_automatic_phase_change_or_kinetic_interpretation_reviewed": True,
        "computational_use_authorized": True,
    },
    context.model_copy(update={"evidence": (*context.evidence, reaction_evidence)}),
)
print("caller-supplied knotwise aqueous mass-action history:")
print(aqueous_history_result.model_dump_json(indent=2))


# The solved dimensionless activities can be passed to a new caller-defined
# redox reaction at the exact same knots. This remains a sequential handoff.
redox_activity_results = []
for branch_id, standard_potential, record_sha in (
    ("redox_A", 0.0, "6" * 64),
    ("redox_B", 0.30, "7" * 64),
):
    redox_activity_results.append(registry.run(
        "integration.aqueous_mass_action_to_crevice_nernst_history",
        {
            "assessment_id": f"synthetic-aqueous-activity-to-nernst-{branch_id}",
            "mass_action_history_result": aqueous_history_result.model_dump(mode="json"),
            "mass_action_history_result_sha256": canonical_digest(aqueous_history_result.model_dump(mode="json")),
            "asset_id": asset_id,
            "location_id": location_id,
            "physical_scope_id": physical_scope_id,
            "clock_id": clock_id,
            "reaction_id": f"synthetic_pool_{branch_id}",
            "standard_potential_reference_id": "SHE",
            "reaction_quotient_stoichiometry": {"PoolA": -1.0, "PoolB": 1.0},
            "electron_number": 1,
            "standard_potential_V": (standard_potential,) * len(times),
            "standard_potential_provider_id": standard_evidence.source_id,
            "standard_potential_provider_revision": "synthetic-1",
            "standard_potential_configuration_sha256": "5" * 64,
            "standard_potential_record_sha256": record_sha,
            "redox_reaction_direction_and_electron_number_reviewed": True,
            "activity_standard_state_and_species_mapping_reviewed": True,
            "standard_potential_temperature_history_reviewed": True,
            "local_activity_history_applicability_reviewed": True,
            "potential_only_no_rate_or_acceptance_reviewed": True,
            "computational_use_authorized": True,
            "evidence": (standard_evidence,),
        },
        context.model_copy(update={"evidence": (*context.evidence, reaction_evidence)}),
    ))
print("aqueous mass-action activities to two caller-defined redox potentials:")
for result in redox_activity_results:
    print(result.model_dump_json(indent=2))

# Couple the two derived Nernst histories through caller-owned kinetics to a
# second mixed-potential history. The parameters are synthetic API-wiring data.
second_kinetic_branches = tuple({
    "reaction_id": f"synthetic_pool_{branch_id}",
    "nernst_result": result.model_dump(mode="json"),
    "nernst_result_sha256": canonical_digest(result.model_dump(mode="json")),
    "reference_electrode_id": "SHE",
    "exposed_area_m2": 1.0,
    "exchange_current_density_A_m2": 1.0e-5,
    "electron_number": 1,
    "anodic_transfer_coefficient": 0.5,
    "cathodic_transfer_coefficient": 0.5,
    "minimum_overpotential_V": -0.5,
    "maximum_overpotential_V": 0.5,
    "stoichiometric_species_coefficients": {"PoolA": -1.0, "PoolB": 1.0},
    "kinetics_provider_id": kinetics_evidence[branch_id].source_id,
    "kinetics_provider_revision": "synthetic-1",
    "kinetics_calibration_sha256": "8" * 64,
    "kinetics_and_anodic_direction_reviewed": True,
    "species_flux_mapping_and_area_basis_reviewed": True,
    "evidence": (kinetics_evidence[branch_id],),
} for branch_id, result in zip(("redox_A", "redox_B"), redox_activity_results, strict=True))
second_mixed_result = registry.run(
    "electrochemistry.crevice_mixed_potential_history",
    {
        "assessment_id": "synthetic-composition-redox-mixed-potential",
        "asset_id": asset_id,
        "location_id": location_id,
        "physical_scope_id": physical_scope_id,
        "clock_id": clock_id,
        "common_reference_electrode_id": "SHE",
        "reference_area_m2": 2.0,
        "reactions": second_kinetic_branches,
        "quasi_steady_local_balance_reviewed": True,
        "negligible_solution_ohmic_drop_reviewed": True,
        "common_electronic_potential_basis_reviewed": True,
        "reaction_set_and_area_partition_complete_reviewed": True,
        "computational_use_authorized": True,
        "evidence": tuple(kinetics_evidence.values()),
    },
    context,
)
print("second mixed-potential history from composition-derived activities:")
print(second_mixed_result.model_dump_json(indent=2))
