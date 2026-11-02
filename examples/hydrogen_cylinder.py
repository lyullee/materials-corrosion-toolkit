"""Run the authored finite-cylinder hydrogen example; values are not material recommendations."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "transport.hydrogen_finite_cylinder_kinetic"

payload = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][MODEL_ID]
result = default_registry().run_json(
    MODEL_ID,
    json.dumps(payload),
    RunContext(
        asset_id="synthetic-cylinder",
        location_id="authored-example",
        time_basis="elapsed seconds from declared release start",
    ),
)
print(result.model_dump_json(indent=2))
