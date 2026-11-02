"""Synthetic wiring from exact-knot B-dot speciation through Nernst and mixed potential."""

from __future__ import annotations

import json
from pathlib import Path

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.aqueous_saturation_screening import (
    CandidateSolid,
    SaturationScreenTerm,
    screen_mass_action_calculation,
)
from matintegrity.registry import default_registry


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    payload = json.loads((project_root / "examples" / "model_inputs.json").read_text(encoding="utf-8"))
    history_id = "integration.aqueous_bdot_speciation_history"
    context = RunContext.model_validate(payload["run_contexts"][history_id])
    history_result = default_registry().run(history_id, payload["models"][history_id], context)
    history_digest = canonical_digest(history_result.model_dump(mode="json"))

    standard_potential = Evidence(
        source_id="synthetic-standard-potential-record",
        origin="synthetic",
        citation="Fabricated E0 values for API wiring only; not a sourced or validated redox parameter.",
        sha256="c" * 64,
    )
    request = {
        "assessment_id": "synthetic-bdot-to-nernst",
        "mass_action_history_result": history_result.model_dump(mode="json"),
        "mass_action_history_result_sha256": history_digest,
        "asset_id": context.asset_id,
        "location_id": context.location_id,
        "physical_scope_id": payload["models"][history_id]["physical_scope_id"],
        "clock_id": context.time_basis,
        "reaction_id": "synthetic-acid-redox-reaction",
        "standard_potential_reference_id": "synthetic-reference-electrode",
        "reaction_quotient_stoichiometry": {"h_plus": 1.0, "ha_minus": 1.0, "h2a": -1.0},
        "electron_number": 1,
        "standard_potential_V": [0.123, 0.124],
        "standard_potential_provider_id": standard_potential.source_id,
        "standard_potential_provider_revision": "fabricated-example-only-1",
        "standard_potential_configuration_sha256": "d" * 64,
        "standard_potential_record_sha256": "c" * 64,
        "redox_reaction_direction_and_electron_number_reviewed": True,
        "activity_standard_state_and_species_mapping_reviewed": True,
        "standard_potential_temperature_history_reviewed": True,
        "local_activity_history_applicability_reviewed": True,
        "potential_only_no_rate_or_acceptance_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [standard_potential.model_dump(mode="json")],
    }
    registry = default_registry()
    result = registry.run(
        "integration.aqueous_mass_action_to_crevice_nernst_history",
        request,
        context,
    )

    second_standard_potential = Evidence(
        source_id="synthetic-second-standard-potential-record",
        origin="synthetic",
        citation="Fabricated E0 values for API wiring only; not a sourced or validated redox parameter.",
        sha256="e" * 64,
    )
    second_request = request | {
        "assessment_id": "synthetic-bdot-to-second-nernst",
        "reaction_id": "synthetic-second-redox-reaction",
        "reaction_quotient_stoichiometry": {"h_plus": -1.0, "ha_minus": 1.0},
        "standard_potential_V": [0.223, 0.224],
        "standard_potential_provider_id": second_standard_potential.source_id,
        "standard_potential_provider_revision": "fabricated-example-only-1",
        "standard_potential_configuration_sha256": "f" * 64,
        "standard_potential_record_sha256": second_standard_potential.sha256,
        "evidence": [second_standard_potential.model_dump(mode="json")],
    }
    second_result = registry.run(
        "integration.aqueous_mass_action_to_crevice_nernst_history",
        second_request,
        context,
    )

    solubility_evidence = Evidence(
        source_id="synthetic-bdot-solubility-record",
        origin="synthetic",
        citation="Fabricated Ksp value for API wiring only; not a sourced or validated phase property.",
        sha256="9" * 64,
    )
    phase_screen = screen_mass_action_calculation(
        history_result,
        assessment_id="synthetic-bdot-exact-knot-phase-screen",
        solution_id="synthetic-bdot-solution",
        candidate_solids=(CandidateSolid(
            solid_id="synthetic-neutral-solid",
            log10_solubility_product=-5.0,
            solubility_record_id="synthetic-ksp-record",
            solubility_evidence_source_id=solubility_evidence.source_id,
            terms=(
                SaturationScreenTerm(species_id="h_plus", stoichiometric_exponent=1.0),
                SaturationScreenTerm(species_id="ha_minus", stoichiometric_exponent=1.0),
            ),
        ),),
        solubility_data_provider_id=solubility_evidence.source_id,
        solubility_data_digest=solubility_evidence.sha256,
        speciation_knot_index=0,
        complete_species_inventory_reviewed=True,
        compatible_standard_states_reviewed=True,
        equilibrium_constants_temperature_reviewed=True,
        evidence=(solubility_evidence,),
    )

    kinetics_evidence = [
        Evidence(
            source_id=provider_id,
            origin="synthetic",
            citation="Fabricated kinetic record for API wiring only; not measured or calibrated.",
            sha256=record_sha,
        )
        for provider_id, record_sha in (
            ("synthetic-first-kinetics", "1" * 64),
            ("synthetic-second-kinetics", "2" * 64),
        )
    ]

    def kinetic_branch(reaction_id, nernst_result, evidence):
        return {
            "reaction_id": reaction_id,
            "nernst_result": nernst_result.model_dump(mode="json"),
            "nernst_result_sha256": canonical_digest(nernst_result.model_dump(mode="json")),
            "reference_electrode_id": "synthetic-reference-electrode",
            "exposed_area_m2": 1.0e-4,
            "exchange_current_density_A_m2": 1.0e-6,
            "electron_number": 1,
            "anodic_transfer_coefficient": 0.5,
            "cathodic_transfer_coefficient": 0.5,
            "minimum_overpotential_V": -0.5,
            "maximum_overpotential_V": 0.5,
            "stoichiometric_species_coefficients": {"h_plus": -1.0},
            "kinetics_provider_id": evidence.source_id,
            "kinetics_provider_revision": "fabricated-example-only-1",
            "kinetics_calibration_sha256": evidence.sha256,
            "kinetics_and_anodic_direction_reviewed": True,
            "species_flux_mapping_and_area_basis_reviewed": True,
            "evidence": [evidence.model_dump(mode="json")],
        }

    mixed = registry.run(
        "electrochemistry.crevice_mixed_potential_history",
        {
            "assessment_id": "synthetic-bdot-mixed-potential",
            "asset_id": context.asset_id,
            "location_id": context.location_id,
            "physical_scope_id": request["physical_scope_id"],
            "clock_id": context.time_basis,
            "common_reference_electrode_id": "synthetic-reference-electrode",
            "reference_area_m2": 2.0e-4,
            "reactions": [
                kinetic_branch("synthetic-acid-redox-reaction", result, kinetics_evidence[0]),
                kinetic_branch("synthetic-second-redox-reaction", second_result, kinetics_evidence[1]),
            ],
            "quasi_steady_local_balance_reviewed": True,
            "negligible_solution_ohmic_drop_reviewed": True,
            "common_electronic_potential_basis_reviewed": True,
            "reaction_set_and_area_partition_complete_reviewed": True,
            "computational_use_authorized": True,
            "evidence": [
                standard_potential.model_dump(mode="json"),
                second_standard_potential.model_dump(mode="json"),
                *(item.model_dump(mode="json") for item in kinetics_evidence),
            ],
        },
        context,
    )
    print(json.dumps({
        "first_nernst_result": result.model_dump(mode="json"),
        "second_nernst_result": second_result.model_dump(mode="json"),
        "phase_screen_result": phase_screen.model_dump(mode="json"),
        "mixed_potential_result": mixed.model_dump(mode="json"),
    }, indent=2))


if __name__ == "__main__":
    main()
