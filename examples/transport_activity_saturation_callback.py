"""Synthetic wiring example for cellwise activities to transport saturation ratios."""

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.models.aqueous_saturation_screening import (
    AqueousSaturationScreen,
    CandidateSolid,
    SaturationScreenSpecies,
    SaturationScreenTerm,
    build_transport_saturation_callback_from_activity_provider,
)


standard_state = "synthetic dimensionless molarity standard state"
activity_provider_digest = canonical_digest(
    {"law": "synthetic identity activity", "standard_state": standard_state}
)


def activity_provider(time_s, cell_index, temperature_K, concentrations):
    del time_s, cell_index, temperature_K
    return {"M2+": concentrations[0] / 1000.0, "A-": concentrations[1] / 1000.0}


activity_provider.provider_id = "synthetic-activity"
activity_provider.provider_revision = "example-1"
activity_provider.configuration_sha256 = activity_provider_digest
activity_provider.activity_standard_state = standard_state

screen_template = AqueousSaturationScreen(
    assessment_id="synthetic-template",
    solution_id="synthetic-solution",
    temperature_K=298.15,
    activity_standard_state=standard_state,
    species=(
        SaturationScreenSpecies(species_id="M2+", dimensionless_activity=1.0),
        SaturationScreenSpecies(species_id="A-", dimensionless_activity=1.0),
    ),
    candidate_solids=(
        CandidateSolid(
            solid_id="MA2-solid",
            log10_solubility_product=-8.5,
            solubility_record_id="synthetic-ksp",
            solubility_evidence_source_id="synthetic-source",
            terms=(
                SaturationScreenTerm(species_id="M2+", stoichiometric_exponent=1),
                SaturationScreenTerm(species_id="A-", stoichiometric_exponent=2),
            ),
        ),
    ),
    activity_state_provider_id="synthetic-activity",
    activity_state_digest=activity_provider_digest,
    solubility_data_provider_id="synthetic-ksp-provider",
    solubility_data_digest="2" * 64,
    complete_species_inventory_reviewed=True,
    compatible_standard_states_reviewed=True,
    equilibrium_constants_temperature_reviewed=True,
    evidence=(
        Evidence(
            source_id="synthetic-source",
            origin="synthetic",
            citation="Synthetic demonstration only",
            license_id="CC0-1.0",
        ),
    ),
)

saturation_callback = build_transport_saturation_callback_from_activity_provider(
    screen_template,
    transport_species_ids=("M2+", "A-"),
    saturation_provider_id="synthetic-saturation-mapper",
    saturation_provider_revision="example-1",
    activity_provider_id=activity_provider.provider_id,
    activity_provider_revision=activity_provider.provider_revision,
    activity_provider_configuration_sha256=activity_provider.configuration_sha256,
    activity_provider=activity_provider,
)

print(
    {
        "provider_id": saturation_callback.provider_id,
        "provider_revision": saturation_callback.provider_revision,
        "configuration_sha256": saturation_callback.configuration_sha256,
        "activity_standard_state": saturation_callback.activity_standard_state,
        "note": "Synthetic wiring only; temperature is fixed by the saturation template.",
    }
)
