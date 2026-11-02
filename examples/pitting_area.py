"""Synthetic same-exposure surface extrapolation; no automatic time or risk conversion."""

import argparse
import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        choices=("gumbel", "gev"),
        default="gumbel",
        help="block-maximum distribution family (default: gumbel)",
    )
    arguments = parser.parse_args()
    inputs = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))["models"][
        "corrosion.gumbel_area_maximum"
    ]
    inputs["extreme_value_family"] = arguments.family
    result = default_registry().run_json(
        "corrosion.gumbel_area_maximum",
        json.dumps(inputs),
        RunContext(
            asset_id="synthetic", location_id="surface", time_basis="one synthetic exposure condition"
        ),
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
