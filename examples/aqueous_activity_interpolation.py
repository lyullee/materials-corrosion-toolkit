"""Show how to select reviewed interpolation for a synthetic activity table."""

import json
from pathlib import Path

from matintegrity.models.aqueous_tabulated_activity import AqueousTabulatedActivityIteration


fixture_path = Path(__file__).with_name("model_inputs.json")
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
payload = fixture["models"]["chemistry.aqueous_tabulated_activity_speciation"]
payload["interpolation_method"] = "shape_preserving_pchip"
payload["interpolation_method_reviewed"] = True

request = AqueousTabulatedActivityIteration.model_validate(payload)
print({
    "interpolation_method": request.interpolation_method,
    "explicit_method_review": request.interpolation_method_reviewed,
    "species_table_count": len(request.species_activity_curves),
    "basis": "synthetic input wiring only; no physical validation or calculation",
})
