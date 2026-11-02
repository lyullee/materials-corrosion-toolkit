"""Synthetic caller-activity Nernst profile; values are not material data."""

from matintegrity.contracts import Evidence, RunContext
from matintegrity.registry import default_registry
from matintegrity.contracts import canonical_digest

evidence = Evidence(
    source_id="synthetic-activity-provider",
    origin="synthetic",
    citation="Synthetic activity-provider wiring illustration only; not experimental data.",
)
standard_potential_evidence = Evidence(
    source_id="synthetic-standard-potential-provider",
    origin="synthetic",
    citation="Synthetic standard-potential wiring illustration only; not experimental data.",
)
inputs = {
    "assessment_id": "synthetic-crevice-redox-01",
    "asset_id": "synthetic-loop",
    "location_id": "synthetic-crevice",
    "physical_scope_id": "synthetic-scope-01",
    "clock_id": "synthetic-elapsed-time",
    "source_inventory_sha256": "0" * 64,
    "reaction_id": "Fe3+_plus_e_to_Fe2+",
    "standard_potential_reference_id": "SHE",
    # Products positive, reactants negative; electrons are counted separately.
    "reaction_quotient_stoichiometry": {"Fe3+": -1.0, "Fe2+": 1.0},
    "electron_number": 1,
    "elapsed_time_s": (0.0, 60.0, 120.0),
    "temperature_K": (298.15, 300.0, 302.0),
    "standard_potential_V": (0.77, 0.769, 0.768),
    # Dimensionless activities from a caller-owned activity/speciation provider.
    "species_activity_history": {
        "Fe3+": (0.01, 0.008, 0.006),
        "Fe2+": (0.02, 0.025, 0.03),
    },
    "activity_provider_id": "synthetic-activity-provider",
    "activity_provider_revision": "1",
    "activity_configuration_sha256": "1" * 64,
    "activity_record_sha256": "2" * 64,
    "standard_potential_provider_id": "synthetic-standard-potential-provider",
    "standard_potential_provider_revision": "1",
    "standard_potential_configuration_sha256": "3" * 64,
    "standard_potential_record_sha256": "4" * 64,
    "redox_reaction_direction_and_electron_number_reviewed": True,
    "activity_standard_state_and_species_mapping_reviewed": True,
    "standard_potential_temperature_history_reviewed": True,
    "local_activity_history_applicability_reviewed": True,
    "potential_only_no_rate_or_acceptance_reviewed": True,
    "computational_use_authorized": True,
    "evidence": (evidence, standard_potential_evidence),
}
context = RunContext(
    asset_id="synthetic-loop",
    location_id="synthetic-crevice",
    time_basis="elapsed_seconds",
    evidence=(evidence, standard_potential_evidence),
)
result = default_registry().run("degradation.crevice_nernst_potential_history", inputs, context)
print("Nernst history:")
print(result.model_dump_json(indent=2))

# Synthetic caller Butler-Volmer parameters are evaluated at the exact same
# knots; the reference IDs and kinetic direction are caller assertions.
kinetics_evidence = Evidence(
    source_id="synthetic-butler-volmer-provider",
    origin="synthetic",
    citation="Synthetic kinetic-provider wiring illustration only; not experimental data.",
)
kinetic_inputs = {
    "assessment_id": "synthetic-crevice-redox-flux-01",
    "nernst_result": result.model_dump(mode="json"),
    "nernst_result_sha256": canonical_digest(result.model_dump(mode="json")),
    "reaction_id": "Fe3+_plus_e_to_Fe2+",
    "clock_id": "synthetic-elapsed-time",
    "equilibrium_potential_reference_id": "SHE",
    "electrode_potential_reference_id": "SHE",
    "electrode_potential_difference_history_V": (0.78, 0.78, 0.78),
    "exchange_current_density_A_m2": 1.0e-4,
    "electron_number": 1,
    "anodic_transfer_coefficient": 0.5,
    "cathodic_transfer_coefficient": 0.5,
    "minimum_overpotential_V": -0.5,
    "maximum_overpotential_V": 0.5,
    "stoichiometric_species_coefficients": {"Fe3+": -1.0, "Fe2+": 1.0},
    "kinetics_provider_id": "synthetic-butler-volmer-provider",
    "kinetics_provider_revision": "1",
    "kinetics_calibration_sha256": "5" * 64,
    "redox_to_kinetics_mapping_reviewed": True,
    "reference_electrode_and_potential_basis_reviewed": True,
    "rate_parameter_and_temperature_applicability_reviewed": True,
    "reaction_direction_and_species_flux_basis_reviewed": True,
    "computational_use_authorized": True,
    "evidence": (kinetics_evidence,),
}
kinetic_context = RunContext(
    asset_id="synthetic-loop",
    location_id="synthetic-crevice",
    time_basis="elapsed_seconds",
    evidence=(kinetics_evidence,),
)
flux_result = default_registry().run(
    "electrochemistry.nernst_driven_butler_volmer_history",
    kinetic_inputs,
    kinetic_context,
)
print("Nernst-driven reaction flux history:")
print(flux_result.model_dump_json(indent=2))
