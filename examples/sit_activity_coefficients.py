"""Illustrative SIT wiring with synthetic, non-calibrated parameters only."""

from matintegrity.contracts import Evidence
from matintegrity.models.sit_activity import (
    SITActivityCoefficientInput,
    SITInteraction,
    SITSpecies,
    sit_activity_coefficients,
)


def main():
    demo_source = Evidence(
        source_id="synthetic_sit_demo",
        origin="synthetic",
        citation="Synthetic API example; not a thermodynamic parameter source",
        sha256="a" * 64,
    )
    request = SITActivityCoefficientInput(
        assessment_id="sit-demo",
        solution_id="synthetic-binary-electrolyte",
        temperature_K=298.15,
        ionic_strength_limit_mol_kg=0.5,
        debye_huckel_A_at_temperature=0.51,
        A_evidence_source_id="synthetic_sit_demo",
        A_provider_id="illustrative-user-input",
        A_provider_revision="demo-1",
        A_configuration_sha256="0" * 64,
        A_record_sha256="0" * 64,
        species=(
            SITSpecies(species_id="cation", species_label="Synthetic +1 ion", charge_number=1, molality_mol_kg=0.1),
            SITSpecies(species_id="anion", species_label="Synthetic -1 ion", charge_number=-1, molality_mol_kg=0.1),
        ),
        interactions=(
            SITInteraction(
                target_species_id="cation",
                counter_species_id="anion",
                epsilon_kg_mol=0.03,
                evidence_source_id="synthetic_sit_demo",
                source_record_id="synthetic-epsilon-ca",
                evidence_sha256="a" * 64,
            ),
            SITInteraction(
                target_species_id="anion",
                counter_species_id="cation",
                epsilon_kg_mol=0.02,
                evidence_source_id="synthetic_sit_demo",
                source_record_id="synthetic-epsilon-ac",
                evidence_sha256="a" * 64,
            ),
        ),
        charge_balance_absolute_tolerance_mol_kg=1e-12,
        complete_ionic_inventory_reviewed=True,
        charge_balance_reviewed=True,
        ionic_strength_convention_reviewed=True,
        interaction_parameter_set_complete_and_applicable_reviewed=True,
        temperature_solvent_A_lineage_reviewed=True,
        evidence=(demo_source,),
    )
    print(sit_activity_coefficients(request).model_dump(mode="json"))


if __name__ == "__main__":
    main()
