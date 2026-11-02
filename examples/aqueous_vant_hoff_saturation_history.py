"""Synthetic wiring example for per-knot aqueous activity/Ksp screening."""

import json
from pathlib import Path

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.aqueous_saturation_screening import CandidateSolid, SaturationScreenTerm
from matintegrity.models.aqueous_vant_hoff_saturation import (
    AqueousSolubilityKnot,
    AqueousVanTHoffSaturationHistory,
    TemperatureSupportedCandidate,
)
from matintegrity.registry import default_registry


root = Path(__file__).resolve().parents[1]
example_inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
context = RunContext(asset_id="synthetic-coupon", location_id="synthetic-cell", time_basis="elapsed-time-s")
registry = default_registry()
equilibrium = registry.run(
    "integration.aqueous_mass_action_vant_hoff_history",
    example_inputs["models"]["integration.aqueous_mass_action_vant_hoff_history"],
    context,
)

evidence = (Evidence(
    source_id="synthetic-example-ksp",
    origin="synthetic",
    citation="Synthetic solubility product for API wiring only; not a measured or validated value.",
    license_id="CC0-1.0",
),)
provider_id = "synthetic-ksp-provider"
solubility_rows = []
for index, (time_s, temperature_K, equilibrium_row) in enumerate(zip(
    equilibrium.values["times_s"],
    equilibrium.values["temperatures_K"],
    equilibrium.values["equilibrium_history"],
    strict=True,
)):
    species = equilibrium_row["calculation"]["values"]["species"]
    candidate = TemperatureSupportedCandidate(
        candidate=CandidateSolid(
            solid_id="synthetic-solid",
            log10_solubility_product=-2.0,
            solubility_record_id=f"synthetic-ksp-knot-{index}",
            solubility_evidence_source_id=evidence[0].source_id,
            terms=(SaturationScreenTerm(species_id=species[0]["species_id"], stoichiometric_exponent=1.0),),
        ),
        minimum_valid_temperature_K=270.0,
        maximum_valid_temperature_K=380.0,
    )
    digest = canonical_digest({
        "provider_id": provider_id,
        "candidates": [candidate.model_dump(mode="json")],
        "evidence": [item.model_dump(mode="json") for item in evidence],
    })
    solubility_rows.append(AqueousSolubilityKnot(
        time_s=time_s,
        provider_id=provider_id,
        data_sha256=digest,
        candidates=(candidate,),
        evidence=evidence,
    ))

request = AqueousVanTHoffSaturationHistory(
    assessment_id="synthetic-aqueous-saturation-history",
    equilibrium_history=equilibrium,
    equilibrium_history_sha256=canonical_digest(equilibrium.model_dump(mode="json")),
    solubility_by_knot=tuple(solubility_rows),
    complete_species_inventory_reviewed=True,
    compatible_standard_states_reviewed=True,
    equilibrium_constants_temperature_reviewed=True,
)
result = registry.run("integration.aqueous_vant_hoff_saturation_history", request, context)
print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
