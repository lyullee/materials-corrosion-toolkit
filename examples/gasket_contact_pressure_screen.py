"""Compose a synthetic flange field with a caller pressure-window screen."""

import json
from pathlib import Path

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.gasket_contact_pressure_screen import GasketContactPressureScreen
from matintegrity.registry import default_registry


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    examples = json.loads((root / "examples" / "model_inputs.json").read_text(encoding="utf-8"))
    inputs = examples["models"]["fabrication.flange_contact_field"]
    context = RunContext(
        asset_id="synthetic-flange-asset",
        location_id="synthetic-gasket-region",
        time_basis="static-load-case",
    )
    registry = default_registry()
    contact = registry.run("fabrication.flange_contact_field", inputs, context)

    criterion_provider = "synthetic-pressure-window-provider"
    criterion_revision = "example-v1"
    criterion_record = "synthetic-window-1"
    minimum_pressure = 1.0e6
    maximum_pressure = 8.0e6
    criterion = {
        "criterion_provider_id": criterion_provider,
        "criterion_provider_revision": criterion_revision,
        "criterion_record_id": criterion_record,
        "physical_scope_id": inputs["physical_scope_id"],
        "minimum_contact_pressure_Pa": minimum_pressure,
        "maximum_contact_pressure_Pa": maximum_pressure,
    }
    criterion_digest = canonical_digest(criterion)
    license_id = "CC0-1.0"
    request = GasketContactPressureScreen.model_validate({
        "assessment_id": "synthetic-contact-pressure-screen",
        "asset_id": context.asset_id,
        "location_id": context.location_id,
        "physical_scope_id": inputs["physical_scope_id"],
        "contact_result": contact.model_dump(mode="json"),
        "contact_result_sha256": canonical_digest(contact.model_dump(mode="json")),
        "minimum_contact_pressure_Pa": minimum_pressure,
        "maximum_contact_pressure_Pa": maximum_pressure,
        "criterion_provider_id": criterion_provider,
        "criterion_provider_revision": criterion_revision,
        "criterion_record_id": criterion_record,
        "criterion_sha256": criterion_digest,
        "criterion_evidence": [{
            "source_id": criterion_provider,
            "origin": "synthetic",
            "citation": "Toy pressure window for API composition only; not a seal limit.",
            "license_id": license_id,
            "sha256": criterion_digest,
        }],
        "usage_rights_evidence": [{
            "source_id": "synthetic-example-rights",
            "origin": "synthetic",
            "citation": "Project-authored synthetic inputs; no third-party data included.",
            "license_id": license_id,
        }],
        "usage_license_id": license_id,
        "physical_scope_and_load_basis_reviewed": True,
        "criterion_applicability_reviewed": True,
        "pressure_basis_and_units_reviewed": True,
        "usage_rights_reviewed": True,
        "computational_use_authorized": True,
    })
    result = registry.run("fabrication.gasket_contact_pressure_screen", request, context)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
