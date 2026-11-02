"""Synthetic neutral-contract example; replace with a reviewed process-history export."""

import json
from pathlib import Path

from matintegrity import evaluate
from matintegrity.contracts import Evidence, RunContext, canonical_digest


def main():
    models = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))["models"]
    inputs = models["workflow.pressure_fatigue"]
    source = {k: v for k, v in inputs["history"].items() if k != "source_digest"}
    inputs["history"]["source_digest"] = canonical_digest(source)
    context = RunContext(
        asset_id="synthetic",
        location_id="synthetic",
        time_basis="elapsed seconds on synthetic-seconds",
        evidence=(
            Evidence(
                source_id="synthetic",
                origin="synthetic",
                citation="Project-authored model history and fatigue coefficients",
                license_id="MIT",
            ),
        ),
    )
    result = evaluate("workflow.pressure_fatigue", inputs, context)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
