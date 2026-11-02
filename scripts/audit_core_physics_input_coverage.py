"""Reconcile core-physics input-validation evidence manifests against the 116-model scope.

This inventory tool does not execute model calculations or infer physical validity. It
reports manifest rows, distinct target models, fixture availability, and models for
which each evidence class still has no recorded case.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "data"


def read_json(name: str) -> object:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    targets = set(read_json("core_physics_missing_input_targets.json")["model_ids"])
    inventory_rows = read_json("core_physics_input_contract_inventory.json")
    inventory = {row["model_id"]: row for row in inventory_rows}
    baselines = read_json("core_physics_valid_input_baselines.json")["model_inputs"]
    review_rows = read_json("core_physics_review_gate_probe_results.json")
    cross_rows = read_json("core_physics_cross_field_rejection_cases.json")["cases"]
    cross_na = read_json("core_physics_cross_field_not_applicable.json")["models"]
    evidence_probes = read_json("core_physics_evidence_removal_probe_manifest.json")["cases"]

    review_applicable = {
        model_id for model_id in targets if inventory.get(model_id, {}).get("review_fields")
    }
    review_covered = {
        row[0] for row in review_rows if row[0] in review_applicable
    }
    review_in_scope_rows = [row for row in review_rows if row[0] in targets]
    cross_covered = {row["model_id"] for row in cross_rows if row["model_id"] in targets}
    cross_na_ids = {row["model_id"] for row in cross_na}
    cross_overlap = cross_covered & cross_na_ids
    if cross_overlap:
        raise ValueError(f"cross-field models cannot be both tested and not applicable: {sorted(cross_overlap)}")
    unknown_na = cross_na_ids - targets
    if unknown_na:
        raise ValueError(f"cross-field not-applicable manifest has out-of-scope models: {sorted(unknown_na)}")
    cross_in_scope_rows = [row for row in cross_rows if row["model_id"] in targets]
    evidence_models = {
        model_id for model_id in targets if inventory.get(model_id, {}).get("evidence_fields")
    }
    evidence_probe_models = {row["model_id"] for row in evidence_probes if row["model_id"] in targets}
    evidence_probe_rows = [row for row in evidence_probes if row["model_id"] in targets]

    print(f"target_models={len(targets)}")
    print(f"valid_baselines={len(set(baselines) & targets)}/{len(targets)}")
    print(
        "review_gate="
        f"{len(review_covered)}/{len(review_applicable)} applicable models; "
        f"{len(review_in_scope_rows)} in-scope rows / {len(review_rows)} total rows"
    )
    print(f"review_missing_baseline={len(review_applicable - review_covered)}")
    for model_id in sorted(review_applicable - review_covered):
        print(f"  review_pending {model_id} baseline={'yes' if model_id in baselines else 'no'}")
    review_without_baseline = review_covered - set(baselines)
    print(f"review_covered_without_full_baseline={len(review_without_baseline)}")
    for model_id in sorted(review_without_baseline):
        print(f"  review_direct_probe {model_id}")
    print(
        "cross_field="
        f"{len(cross_covered)}/{len(targets)} target models; "
        f"{len(cross_in_scope_rows)} in-scope rows / {len(cross_rows)} total rows"
    )
    print(
        "cross_field_classification="
        f"{len(cross_covered)} tested + {len(cross_na_ids & targets)} not applicable + "
        f"{len(targets - cross_covered - cross_na_ids)} pending = {len(targets)} targets"
    )
    for model_id in sorted(cross_na_ids - targets):
        print(f"  cross_not_applicable_outside_target {model_id}")
    cross_pending = targets - cross_covered - cross_na_ids
    print(f"cross_pending={len(cross_pending)}")
    print(f"cross_pending_with_baseline={len(cross_pending & set(baselines))}")
    for model_id in sorted(cross_pending):
        print(f"  cross_pending {model_id} baseline={'yes' if model_id in baselines else 'no'}")
    print(
        f"evidence_models={len(evidence_models)}; "
        f"required_evidence_probes={len(evidence_probe_rows)} rows / "
        f"{len(evidence_probe_models)} models; "
        f"unprobed={len(evidence_models - evidence_probe_models)}"
    )
    for model_id in sorted(evidence_models - evidence_probe_models):
        print(f"  evidence_pending {model_id} baseline={'yes' if model_id in baselines else 'no'}")
    evidence_probe_without_baseline = evidence_probe_models - set(baselines)
    print(f"evidence_probed_without_full_baseline={len(evidence_probe_without_baseline)}")
    for model_id in sorted(evidence_probe_without_baseline):
        print(f"  evidence_direct_probe {model_id}")


if __name__ == "__main__":
    main()
