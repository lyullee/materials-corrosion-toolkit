"""Run a synthetic axial loss profile with explicit replaceable pressure/factor providers."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    inputs = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))["models"][
        "structural.profile_capacity"
    ]
    context = RunContext(
        asset_id="synthetic", location_id="axial-profile", time_basis="one synthetic static profile"
    )
    result = default_registry().run_json("structural.profile_capacity", json.dumps(inputs), context)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
