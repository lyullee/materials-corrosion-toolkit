"""Leave-one-source-group-out sensitivity diagnostics for crevice wall-sink calibration."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field

from .contracts import Calculation, Contract, canonical_digest
from .crevice_wall_sink_arrhenius_calibration import (
    CreviceWallSinkArrheniusCalibrationRequest,
    CreviceWallSinkRateObservations,
    fit_crevice_wall_sink_arrhenius,
)
from .registry import ModelSpec

MODEL_ID = "validation.crevice_wall_sink_source_group_stability"
SOURCE_ID = "caller_crevice_wall_sink_leave_one_group_out_diagnostic"
MAX_GROUPS = 100


class CreviceWallSinkGroupCVRequest(Contract):
    schema_version: Literal["matintegrity.crevice_wall_sink_group_cv.v1"] = (
        "matintegrity.crevice_wall_sink_group_cv.v1"
    )
    diagnostic_id: str = Field(min_length=1)
    calibration_request: CreviceWallSinkArrheniusCalibrationRequest
    calibration_result: dict
    calibration_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_group_independence_and_replication_reviewed: bool
    use_only_predeclared_calibration_rows_reviewed: bool
    diagnostic_is_not_qualification_reviewed: bool


def evaluate_crevice_wall_sink_group_cv(request: CreviceWallSinkGroupCVRequest) -> Calculation:
    """Refit once per calibration source group, reserving that group as a fold holdout."""
    calibration = request.calibration_request
    calibration_result = request.calibration_result
    digest = request.calibration_result_sha256
    values = calibration_result.get("values", calibration_result)
    request_digest = canonical_digest(calibration.model_dump(mode="json"))
    base = {
        "diagnostic_id": request.diagnostic_id,
        "calibration_id": calibration.calibration_id,
        "calibration_request_sha256": request_digest,
        "calibration_result_sha256": digest,
        "physical_scope_id": calibration.physical_scope_id,
        "material_condition_id": calibration.material_condition_id,
        "wall_surface_state_id": calibration.wall_surface_state_id,
        "fluid_chemistry_state_id": calibration.fluid_chemistry_state_id,
    }
    if canonical_digest(calibration_result) != digest:
        return Calculation(status="out_of_scope", values=base | {"reason": "calibration result digest mismatch"})
    if calibration_result.get("status") != "computed" or values.get("input_sha256") != request_digest:
        return Calculation(status="needs_data", values=base | {"reason": "computed result for the exact calibration request is required"})
    recomputed = fit_crevice_wall_sink_arrhenius(calibration)
    if recomputed.status != "computed" or canonical_digest(recomputed.model_dump(mode="json")) != digest:
        return Calculation(status="out_of_scope", values=base | {"reason": "calibration result is not reproducible from the pinned observations"})
    reviews = (
        "source_group_independence_and_replication_reviewed",
        "use_only_predeclared_calibration_rows_reviewed",
        "diagnostic_is_not_qualification_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    source = calibration.observations
    calibration_indices = [index for index, part in enumerate(source.partition) if part == "calibration"]
    groups = sorted({source.source_group_id[index] for index in calibration_indices})
    if len(groups) < 4 or len(groups) > MAX_GROUPS:
        return Calculation(status="needs_data", values=base | {
            "calibration_source_group_count": len(groups),
            "reason": "diagnostic requires 4..100 independent calibration source groups",
        })
    if not all((
        calibration.observation_to_effective_wall_velocity_mapping_reviewed,
        calibration.shared_surface_and_fluid_state_across_temperatures_reviewed,
        calibration.calibration_holdout_partition_predeclared,
        calibration.temperature_and_measurement_support_reviewed,
        calibration.arrhenius_law_applicability_reviewed,
        calibration.computational_use_and_data_rights_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {"reason": "source calibration is missing review gates"})

    folds: list[dict] = []
    out_of_fold_residuals: list[float] = []
    fitted_ln_reference: list[float] = []
    fitted_activation: list[float] = []
    for group in groups:
        selected = list(calibration_indices)
        # Original untouched holdout observations are deliberately excluded from every refit and fold.
        fold_partition = tuple(
            "holdout" if source.source_group_id[index] == group else "calibration"
            for index in selected
        )
        fold_observations = CreviceWallSinkRateObservations(
            observation_id=tuple(source.observation_id[index] for index in selected),
            source_group_id=tuple(source.source_group_id[index] for index in selected),
            partition=fold_partition,
            temperature_K=tuple(source.temperature_K[index] for index in selected),
            wall_transfer_velocity_m_s=tuple(source.wall_transfer_velocity_m_s[index] for index in selected),
            log_velocity_standard_uncertainty=(
                tuple(source.log_velocity_standard_uncertainty[index] for index in selected)
                if source.log_velocity_standard_uncertainty is not None else None
            ),
        )
        fold_request = calibration.model_copy(update={"observations": fold_observations})
        fit = fit_crevice_wall_sink_arrhenius(fold_request)
        if fit.status != "computed":
            return Calculation(status="needs_data", values=base | {
                "fold_count": len(folds), "folds": folds,
                "failed_source_group_id": group,
                "reason": "leave-one-group-out fit was not supported by the remaining calibration design",
                "failed_fold_values": fit.values,
            })
        fold_values = fit.values
        heldout_rows = [row for row in fold_values.get("observation_residuals", []) if row.get("partition") == "holdout"]
        if not heldout_rows:
            return Calculation(status="out_of_scope", values=base | {
                "fold_count": len(folds), "folds": folds,
                "failed_source_group_id": group,
                "reason": "excluded group did not appear as an out-of-fold observation",
            })
        residuals = [float(row["log_velocity_residual"]) for row in heldout_rows]
        if any(not math.isfinite(value) for value in residuals):
            return Calculation(status="out_of_scope", values=base | {
                "fold_count": len(folds), "folds": folds,
                "failed_source_group_id": group,
                "reason": "nonfinite out-of-fold residual",
            })
        out_of_fold_residuals.extend(residuals)
        reference_rate = float(fold_values["reference_wall_transfer_velocity_m_s"])
        fitted_ln_reference.append(math.log(reference_rate))
        fitted_activation.append(float(fold_values["activation_energy_J_mol"]))
        folds.append({
            "held_out_source_group_id": group,
            "held_out_observation_count": len(heldout_rows),
            "training_observation_count": int(sum(part == "calibration" for part in fold_partition)),
            "reference_wall_transfer_velocity_m_s": reference_rate,
            "activation_energy_J_mol": float(fold_values["activation_energy_J_mol"]),
            "held_out_rmse_log_velocity": float(math.sqrt(float(np.mean(np.square(residuals))))),
            "held_out_max_absolute_log_velocity_residual": max(abs(value) for value in residuals),
            "held_out_residuals": heldout_rows,
            "fold_calibration_result_sha256": canonical_digest(fit.model_dump(mode="json")),
        })

    residual_array = np.asarray(out_of_fold_residuals, dtype=float)
    return Calculation(values=base | {
        "status": "computed",
        "fold_count": len(folds),
        "folds": folds,
        "out_of_fold_observation_count": len(out_of_fold_residuals),
        "group_out_of_fold_rmse_log_velocity": float(math.sqrt(float(np.mean(np.square(residual_array))))),
        "group_out_of_fold_mean_log_velocity_bias": float(np.mean(residual_array)),
        "group_out_of_fold_max_absolute_log_velocity_residual": float(np.max(np.abs(residual_array))),
        "leave_one_group_out_standard_deviation_ln_reference_velocity": float(np.std(fitted_ln_reference, ddof=1)),
        "leave_one_group_out_standard_deviation_activation_energy_J_mol": float(np.std(fitted_activation, ddof=1)),
        "original_predeclared_holdout_used_in_group_cv": False,
        "interpretation_boundary": "These are group-deletion stability and out-of-fold residual diagnostics within the supplied calibration groups. They are not independent external validation, confidence limits, a qualification result, or a guarantee of transfer to new conditions.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceWallSinkGroupCVRequest,
        evaluator=evaluate_crevice_wall_sink_group_cv,
        units={
            "group_out_of_fold_rmse_log_velocity": "1",
            "group_out_of_fold_mean_log_velocity_bias": "1",
            "group_out_of_fold_max_absolute_log_velocity_residual": "1",
            "leave_one_group_out_standard_deviation_ln_reference_velocity": "1",
            "leave_one_group_out_standard_deviation_activation_energy_J_mol": "J/mol",
            "folds[].reference_wall_transfer_velocity_m_s": "m/s",
            "folds[].activation_energy_J_mol": "J/mol",
            "folds[].held_out_rmse_log_velocity": "1",
            "folds[].held_out_max_absolute_log_velocity_residual": "1",
        },
        assumptions=(
            "Only observations predeclared as calibration rows are partitioned; the original independent holdout is never included in any fold.",
            "Source-group identifiers represent independent measurement/campaign units and are caller-reviewed before group deletion.",
            "Each fold uses the same Arrhenius model, reference temperature, evidence and tolerances as the pinned source calibration request.",
            "Parameter spread and out-of-fold residuals describe sensitivity within supplied groups; they do not establish external transfer or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
