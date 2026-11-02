"""Summarize residuals from a computed gasket leakage-map fit."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from .gasket_leakage_map_fit import GasketLeakageMapFit

_FIT_MODEL = "fabrication.gasket_leakage_map_fit"


class GasketLeakageFitDiagnostics(Contract):
    """Compute descriptive fit residual summaries without refitting a surface."""

    assessment_id: str = Field(min_length=1)
    fit_result: AssessmentResult
    fit_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    residual_interpretation_reviewed: bool
    source_group_roles_and_scope_reviewed: bool
    diagnostic_use_authorized: bool

    @model_validator(mode="after")
    def verify_fit_result(self):
        result = self.fit_result
        if result.model_id != _FIT_MODEL or result.status != "computed":
            raise ValueError("a computed gasket leakage-map fit result is required")
        if canonical_digest(result.model_dump(mode="json")) != self.fit_result_sha256:
            raise ValueError("fit result digest does not match the supplied assessment")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("fit result input/context digest mismatch")
        fit_request = GasketLeakageMapFit.model_validate(result.inputs)
        if result.values.get("input_sha256") != canonical_digest(fit_request.model_dump(mode="json")):
            raise ValueError("fit result request digest does not match the original fit inputs")
        table = result.values.get("calibration_map")
        if not isinstance(table, dict) or result.values.get("calibration_map_sha256") != canonical_digest(table):
            raise ValueError("fitted leakage-map digest mismatch")
        return self


def _finite_metric(values: list[float], *, square: bool = False) -> float:
    magnitudes = [abs(value) for value in values]
    if not magnitudes:
        raise ValueError("cannot summarize an empty residual group")
    maximum = max(magnitudes)
    if square:
        if maximum == 0.0:
            return 0.0
        normalized_sum = math.fsum((value / maximum) ** 2 for value in values)
        metric = maximum * math.sqrt(normalized_sum / len(values))
    else:
        metric = math.fsum(values) / len(values)
    if not math.isfinite(metric):
        raise OverflowError("residual summary exceeds finite numeric support")
    return metric


def _summarize(rows: list[dict], observations_by_id: dict[str, dict]) -> dict:
    raw_errors: list[float] = []
    scaled_errors: list[float] = []
    for row in rows:
        observation = observations_by_id[row["observation_id"]]
        error = float(row["signed_residual_mol_s_m2"])
        scale = float(observation["residual_scale_mol_s_m2"])
        scaled = error / scale
        if not math.isfinite(scaled):
            raise OverflowError("standardized residual exceeds finite numeric support")
        raw_errors.append(error)
        scaled_errors.append(scaled)
    rmse = _finite_metric(raw_errors, square=True)
    mean_error = _finite_metric(raw_errors)
    mean_standardized_error = _finite_metric(scaled_errors)
    max_abs_error = max(abs(value) for value in raw_errors)
    max_abs_standardized = max(abs(value) for value in scaled_errors)
    weighted_rms = _finite_metric(scaled_errors, square=True)
    if not all(math.isfinite(value) for value in (mean_error, max_abs_error, max_abs_standardized)):
        raise OverflowError("residual diagnostic exceeds finite numeric support")
    return {
        "row_count": len(rows),
        "mean_signed_error_mol_s_m2": mean_error,
        "mean_absolute_error_mol_s_m2": _finite_metric([abs(value) for value in raw_errors]),
        "root_mean_square_error_mol_s_m2": rmse,
        "maximum_absolute_error_mol_s_m2": max_abs_error,
        "mean_standardized_error": mean_standardized_error,
        "weighted_root_mean_square_error": weighted_rms,
        "maximum_absolute_standardized_error": max_abs_standardized,
    }


def diagnose_gasket_leakage_fit(x: GasketLeakageFitDiagnostics) -> Calculation:
    """Report residual summaries by declared data role and source/specimen labels."""

    source = x.fit_result
    fit_request = GasketLeakageMapFit.model_validate(source.inputs)
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "joint_scope_id": fit_request.joint_scope_id,
        "calibration_id": fit_request.calibration_id,
        "fit_model_id": source.model_id,
        "fit_result_sha256": x.fit_result_sha256,
        "fit_input_digest": source.input_digest,
        "calibration_map_sha256": source.values["calibration_map_sha256"],
        "fit_source_ids": list(source.source_ids),
        "fit_input_evidence": [row.model_dump(mode="json") for row in fit_request.evidence],
        "diagnostic_kind": "descriptive_residual_summary",
        "physical_validation_or_acceptance_inferred": False,
        "specimen_independence_inferred": False,
        "probability_or_uncertainty_interval_inferred": False,
    }
    reviews = {
        "residual_interpretation_reviewed": x.residual_interpretation_reviewed,
        "source_group_roles_and_scope_reviewed": x.source_group_roles_and_scope_reviewed,
        "diagnostic_use_authorized": x.diagnostic_use_authorized,
    }
    missing_reviews = [key for key, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "review_flags": reviews,
        })

    input_observations = [row.model_dump(mode="json") for row in fit_request.observations]
    observations_by_id = {row["observation_id"]: row for row in input_observations}
    output_rows = source.values.get("observation_results")
    if not isinstance(output_rows, list) or len(output_rows) != len(input_observations):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fit_result_row_count_does_not_match_input",
            "input_row_count": len(input_observations),
            "fit_output_row_count": len(output_rows) if isinstance(output_rows, list) else None,
        })
    seen: set[str] = set()
    grouped: dict[str, dict[str, list[dict]]] = {"calibration": {}, "holdout": {}}
    for index, row in enumerate(output_rows):
        if not isinstance(row, dict):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "malformed_fit_output_row",
                "failed_row_index": index,
                "validated_prefix_count": index,
            })
        observation_id = row.get("observation_id")
        observation = observations_by_id.get(observation_id)
        if observation is None or observation_id in seen:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "missing_extra_or_duplicate_fit_observation_id",
                "failed_row_index": index,
                "validated_prefix_count": index,
                "observation_id": observation_id,
            })
        seen.add(observation_id)
        if any(row.get(key) != observation.get(key) for key in (
            "physical_specimen_id", "source_group_id", "source_sha256", "role",
        )):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "fit_output_row_identity_or_partition_mismatch",
                "failed_row_index": index,
                "validated_prefix_count": index,
                "observation_id": observation_id,
            })
        predicted, residual = row.get("predicted_flux_mol_s_m2"), row.get("signed_residual_mol_s_m2")
        measured = observation.get("molar_leak_flux_mol_s_m2")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in (predicted, residual, measured)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "nonfinite_or_missing_residual_value",
                "failed_row_index": index,
                "validated_prefix_count": index,
                "observation_id": observation_id,
            })
        if predicted < 0 or residual != predicted - measured:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "fit_residual_does_not_reconcile_to_measured_value",
                "failed_row_index": index,
                "validated_prefix_count": index,
                "observation_id": observation_id,
            })
        role = observation["role"]
        grouped[role].setdefault(observation["source_group_id"], []).append(row)
    if len(seen) != len(observations_by_id):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fit_output_omits_input_observations",
            "validated_row_count": len(seen),
        })

    calibration_rows = [row for row in output_rows if row["role"] == "calibration"]
    holdout_rows = [row for row in output_rows if row["role"] == "holdout"]
    try:
        role_summaries = {
            "calibration": _summarize(calibration_rows, observations_by_id),
            "holdout": None if not holdout_rows else _summarize(holdout_rows, observations_by_id),
        }
        source_group_summaries = []
        for role in ("calibration", "holdout"):
            for source_group_id in sorted(grouped[role]):
                summary = _summarize(grouped[role][source_group_id], observations_by_id)
                source_group_summaries.append({
                    "role": role,
                    "source_group_id": source_group_id,
                    **summary,
                })
        specimen_groups: dict[tuple[str, str], list[dict]] = {}
        for row in output_rows:
            key = (row["role"], row["physical_specimen_id"])
            specimen_groups.setdefault(key, []).append(row)
        specimen_summaries = []
        for (role, specimen_id), rows in sorted(specimen_groups.items()):
            specimen_summaries.append({
                "role": role,
                "caller_specimen_label": specimen_id,
                **_summarize(rows, observations_by_id),
            })
    except (OverflowError, ValueError) as exc:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "residual_metric_exceeds_numeric_support",
            "error_type": type(exc).__name__,
        })

    if role_summaries["holdout"] is None:
        return Calculation(status="needs_data", values=base | {
            "reason": "no_predeclared_holdout_observations",
            "role_residual_summaries": role_summaries,
            "source_group_residual_summaries": source_group_summaries,
            "caller_specimen_label_residual_summaries": specimen_summaries,
        }, notes=("Calibration residuals are descriptive only; a disjoint predeclared holdout is required for holdout diagnostics.",))

    return Calculation(values=base | {
        "role_residual_summaries": role_summaries,
        "source_group_residual_summaries": source_group_summaries,
        "caller_specimen_label_residual_summaries": specimen_summaries,
        "holdout_rows_used_for_map_fit": False,
        "source_group_and_specimen_counts_are_descriptive_labels_only": True,
    }, notes=(
        "Residual metrics summarize the already computed map fit; this function does not refit coefficients or change the map.",
        "Holdout metrics are descriptive for the supplied rows and do not establish independent physical replication, transferability, physical validation, sealing acceptance, or qualification.",
    ))


def _validate_context(request: GasketLeakageFitDiagnostics, context: RunContext) -> None:
    source = request.fit_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis,
    ):
        raise ValueError("fit diagnostics RunContext must match the source fit assessment")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_leakage_fit_diagnostics",
        GasketLeakageFitDiagnostics,
        diagnose_gasket_leakage_fit,
        {
            "role_residual_summaries.calibration.mean_signed_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.calibration.mean_absolute_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.calibration.root_mean_square_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.calibration.maximum_absolute_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.holdout.mean_signed_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.holdout.mean_absolute_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.holdout.root_mean_square_error_mol_s_m2": "mol/s/m2",
            "role_residual_summaries.holdout.maximum_absolute_error_mol_s_m2": "mol/s/m2",
        },
        (
            "Compute descriptive raw and residual-scale-normalized error summaries from a digest-pinned completed gasket leakage-map fit.",
            "The fit is never changed; calibration and holdout results stay separated, and holdout metrics are not physical qualification or acceptance.",
        ),
        ("caller_gasket_leakage_fit_residual_diagnostics",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
