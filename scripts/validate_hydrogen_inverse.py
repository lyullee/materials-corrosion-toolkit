"""Verify one-parameter planar hydrogen-flow fitting and holdout exclusion."""

import copy
import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_kinetics import HydrogenSlab
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "transport.hydrogen_slab_flow_multiplier_fit"
INPUTS = runpy.run_path(str(ROOT / "examples/hydrogen_slab_flow_fit.py"))["INPUTS"]


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="authored-slab",
        location_id="authored-exit",
        time_basis="elapsed seconds",
    )
    result = registry.run_json(MODEL_ID, json.dumps(INPUTS), context)
    if result.status != "computed":
        raise ValueError(result.notes)
    expected_multiplier = 2.0
    multiplier_error = abs(result.values["fitted_multiplier"] - expected_multiplier)
    expected_history = np.asarray(INPUTS["base_slab"]["lattice_diffusivity_m2_s"]) * 2.0
    history_error = float(
        np.max(np.abs(np.asarray(result.values["fitted_target_history"]) - expected_history))
    )
    fitted = HydrogenSlab.model_validate_json(json.dumps(result.values["fitted_slab_contract"]))
    reusable_contract_error = float(
        np.max(np.abs(np.asarray(fitted.lattice_diffusivity_m2_s) - expected_history))
    )

    altered = copy.deepcopy(INPUTS)
    for index, partition in enumerate(altered["partition"]):
        if partition == "holdout":
            altered["outward_hydrogen_atoms_mol_s"][index] += 1.0
    altered_result = registry.run_json(MODEL_ID, json.dumps(altered), context)
    if altered_result.status != "computed":
        raise ValueError(altered_result.notes)
    holdout_exclusion_multiplier_error = abs(
        altered_result.values["fitted_multiplier"] - result.values["fitted_multiplier"]
    )
    holdout_exclusion_digest_unchanged = (
        altered_result.values["fitted_slab_digest"] == result.values["fitted_slab_digest"]
    )
    if (
        multiplier_error > 1e-10
        or history_error > 1e-10
        or reusable_contract_error > 1e-10
        or holdout_exclusion_multiplier_error > 1e-12
        or not holdout_exclusion_digest_unchanged
        or result.values["forward_relative_mass_balance_error"] > 1e-9
    ):
        raise ValueError("hydrogen inverse verification exceeds its declared checks")
    record = {
        "schema_version": "matintegrity.hydrogen_slab_flow_inverse_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": MODEL_ID,
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "src/matintegrity/models/hydrogen_inverse.py",
                "src/matintegrity/models/hydrogen_kinetics.py",
                "examples/hydrogen_slab_flow_fit.py",
            )
        },
        "status": "passed",
        "fit_request_digest": result.input_digest,
        "expected_diffusivity_multiplier": expected_multiplier,
        "fitted_diffusivity_multiplier": result.values["fitted_multiplier"],
        "multiplier_absolute_error": multiplier_error,
        "fitted_history_maximum_absolute_error_m2_s": history_error,
        "reusable_contract_maximum_absolute_error_m2_s": reusable_contract_error,
        "calibration_flow_rmse_mol_s": result.values["calibration_flow_rmse_mol_s"],
        "holdout_flow_rmse_mol_s": result.values["holdout_flow_rmse_mol_s"],
        "holdout_exclusion_multiplier_absolute_change": holdout_exclusion_multiplier_error,
        "holdout_exclusion_fitted_slab_digest_unchanged": holdout_exclusion_digest_unchanged,
        "maximum_forward_relative_mass_balance_error": result.values["forward_relative_mass_balance_error"],
        "qualification": (
            "Authored same-model parameter-recovery, contract-reuse, holdout-exclusion and mass-balance "
            "checks only. This is not experimental validation, global identifiability or uncertainty "
            "qualification for a material, detector or surface condition."
        ),
    }
    target = ROOT / "validation/hydrogen_slab_flow_inverse_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
