"""Run an authored area-dependent mixed-potential example; no external data or service needed."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    examples = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))
    inputs = examples["models"]["corrosion.mixed_potential"]
    result = default_registry().run_json(
        "corrosion.mixed_potential",
        json.dumps(inputs),
        RunContext(asset_id="authored-couple", location_id="electrodes", time_basis="static interpolant"),
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
