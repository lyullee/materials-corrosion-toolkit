"""Evaluate one portable crack-growth scenario selected by a stable array index."""

import argparse
import json
from pathlib import Path

from matintegrity.models.crack import (
    TabulatedCrackGrowthScenarioEnsemble,
    evaluate_crack_growth_scenario_job,
)

MODEL_ID = "fracture.tabulated_crack_growth_scenario_ensemble"


def load_ensemble(path: Path) -> TabulatedCrackGrowthScenarioEnsemble:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "models" in payload:
        payload = payload["models"][MODEL_ID]
    return TabulatedCrackGrowthScenarioEnsemble.model_validate(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ensemble", type=Path, required=True)
    parser.add_argument("--scenario-index", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluator-id", required=True)
    parser.add_argument("--evaluator-revision", required=True)
    parser.add_argument("--evaluator-configuration-sha256", required=True)
    args = parser.parse_args()

    ensemble = load_ensemble(args.ensemble)
    if not 0 <= args.scenario_index < len(ensemble.scenarios):
        parser.error(f"scenario index must be inside [0, {len(ensemble.scenarios)})")
    evaluation = evaluate_crack_growth_scenario_job(
        ensemble.scenarios[args.scenario_index],
        evaluator_id=args.evaluator_id,
        evaluator_revision=args.evaluator_revision,
        evaluator_configuration_sha256=args.evaluator_configuration_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(evaluation.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "scenario_index": args.scenario_index,
                "scenario_id": evaluation.scenario_id,
                "status": evaluation.status,
                "input_sha256": evaluation.input_sha256,
            }
        )
    )


if __name__ == "__main__":
    main()
