"""Synthetic calibration followed by a component no-indication update."""

import json
from pathlib import Path

from matintegrity.composition import OutputBinding, WorkflowStep, run_workflow
from matintegrity.contracts import Evidence, RunContext
from matintegrity.registry import default_registry


def main():
    parameters = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))[
        "models"
    ]["inspection.hit_miss_pod"]
    context = RunContext(
        asset_id="synthetic",
        location_id="synthetic",
        time_basis="synthetic current inspection",
        evidence=(
            Evidence(
                source_id="synthetic",
                origin="synthetic",
                citation="Authored hit/miss trials and three-bin prior",
                license_id="MIT",
            ),
        ),
        metadata={
            "calibration_scope": "synthetic independent test specimens",
            "component_prior": "three sizes matching query_sizes_m",
        },
    )
    steps = [
        WorkflowStep(id="calibration", model_id="inspection.hit_miss_pod", inputs=parameters),
        WorkflowStep(
            id="current_inspection",
            model_id="inspection.no_indication_update",
            inputs={"prior_weights": [0.2, 0.5, 0.3], "coverage_fraction": 1.0},
            bindings={
                "probabilities_of_detection": OutputBinding(
                    step_id="calibration", output_key="probability_of_detection"
                )
            },
        ),
    ]
    print(json.dumps(run_workflow(default_registry(), steps, context), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
