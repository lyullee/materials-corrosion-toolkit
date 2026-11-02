import json
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DOCUMENT = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))
EXAMPLES = EXAMPLE_DOCUMENT["models"]
RUN_CONTEXTS = EXAMPLE_DOCUMENT.get("run_contexts", {})


def test_all_registered_models_have_a_reviewable_input_example():
    assert set(EXAMPLES) == set(default_registry().list_models())


@pytest.mark.parametrize("model_id", sorted(EXAMPLES))
def test_model_example_executes_finite_versioned_contract(model_id):
    example = EXAMPLES[model_id]
    context_values = RUN_CONTEXTS.get(model_id, {})
    context = RunContext(
        asset_id=context_values.get("asset_id", example.get("asset_id", "synthetic")),
        location_id=context_values.get("location_id", example.get("location_id", "synthetic")),
        time_basis=context_values.get("time_basis", example.get("time_basis", "API contract check")),
    )
    dependencies = {}
    if model_id == "integration.aqueous_external_activity_speciation_history":
        # Explicit authored ideal-solution test double, not a real activity library.
        knot = example["knot_requests"][0]
        assert knot["activity_provider_id"] == "synthetic-external-activity-provider"

        def ideal_activity(request):
            return dict(
                status="computed",
                provider_id=knot["activity_provider_id"],
                provider_revision=knot["activity_provider_revision"],
                configuration_sha256=knot["activity_configuration_sha256"],
                parameter_record_sha256=knot["activity_parameter_record_sha256"],
                request_sha256=canonical_digest(request),
                activity_standard_state=request["activity_standard_state"],
                single_ion_activity_convention_id=request["single_ion_activity_convention_id"],
                species_ids=request["species_ids"],
                ionic_strength_mol_kg_water=request["ionic_strength_mol_kg_water"],
                activity_coefficients_molality_standard_state=[1.0] * len(request["species_ids"]),
            )

        dependencies["activity_provider"] = ideal_activity
    result = default_registry().run_json(
        model_id, json.dumps(example), context, runtime_dependencies=dependencies
    )
    assert result.status == "computed", result.values
    encoded = result.model_dump_json()
    assert encoded
    assert len(result.input_digest) == 64
