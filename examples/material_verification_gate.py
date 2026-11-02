"""Synthetic certificate/measurement verification with an explicit procedure gate."""

import copy
import json
from pathlib import Path

from matintegrity.composition import SatisfactionGate, WorkflowStep, run_workflow
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    examples = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))["models"]
    context = RunContext(
        asset_id="synthetic", location_id="synthetic", time_basis="synthetic material verification"
    )
    for case in ("provided", "carbon_unmeasured"):
        chemistry = copy.deepcopy(examples["materials.chemistry_reconciliation"])
        if case == "carbon_unmeasured":
            chemistry["verification"]["element_intervals"]["C"] = None
        steps = [
            WorkflowStep(
                id="material",
                model_id="materials.chemistry_reconciliation",
                inputs=chemistry,
                satisfaction_gate=SatisfactionGate(),
            ),
            WorkflowStep(
                id="dimensions",
                model_id="fabrication.thickness_budget",
                inputs=examples["fabrication.thickness_budget"],
            ),
        ]
        result = run_workflow(default_registry(), steps, context)
        print(json.dumps(dict(case=case, workflow=result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
