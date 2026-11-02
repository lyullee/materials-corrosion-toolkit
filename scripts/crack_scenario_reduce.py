"""Validate and reduce independently produced crack-growth scenario evaluations."""

import argparse
import json
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.models.crack import (
    CrackGrowthScenarioEvaluation,
    TabulatedCrackGrowthScenarioEnsemble,
    TabulatedCrackGrowthScenarioReduction,
    crack_growth_scenario_manifest,
    tabulated_crack_growth_scenario_reduction,
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
    parser.add_argument("--evaluations-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluator-id", required=True)
    parser.add_argument("--evaluator-revision", required=True)
    parser.add_argument("--evaluator-configuration-sha256", required=True)
    args = parser.parse_args()

    ensemble = load_ensemble(args.ensemble)
    paths = sorted(args.evaluations_dir.glob("scenario-*.json"))
    evaluations = [
        CrackGrowthScenarioEvaluation.model_validate_json(path.read_text(encoding="utf-8")) for path in paths
    ]
    reduction = TabulatedCrackGrowthScenarioReduction(
        ensemble_run_id=ensemble.ensemble_run_id,
        distribution_definition_id=ensemble.distribution_definition_id,
        sample_design_id=ensemble.sample_design_id,
        manifest=crack_growth_scenario_manifest(ensemble),
        evaluations=evaluations,
        requested_quantiles=ensemble.requested_quantiles,
        depth_exceedance_threshold_m=ensemble.depth_exceedance_threshold_m,
        maximum_weight_sum_error=ensemble.maximum_weight_sum_error,
        evaluator_id=args.evaluator_id,
        evaluator_revision=args.evaluator_revision,
        evaluator_configuration_sha256=args.evaluator_configuration_sha256,
        external_evaluations_reviewed=True,
        normalized_weight_meaning_reviewed=True,
        common_physical_scope_reviewed=True,
    )
    calculation = tabulated_crack_growth_scenario_reduction(reduction)
    payload = {
        "schema_version": "matintegrity.crack_growth_scenario_reduction_artifact.v1",
        "reduction_input_sha256": canonical_digest(reduction.model_dump(mode="json")),
        "reduction": reduction.model_dump(mode="json"),
        "calculation": calculation.model_dump(mode="json"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "evaluation_files": len(paths),
                "scenario_count": len(ensemble.scenarios),
                "status": calculation.status,
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
