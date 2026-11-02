"""Caller-calibrated elastic redistribution during a sequential gasket-bolt tightening plan."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_bolt_preload_sequence_redistribution"


class GasketBoltTighteningOperation(Contract):
    operation_id: str = Field(min_length=1)
    pass_id: str = Field(min_length=1)
    tightened_bolt_id: str = Field(min_length=1)
    applied_preload_increment_N: Positive


class GasketBoltPreloadSequenceRedistribution(Contract):
    schema_version: Literal["matintegrity.gasket_bolt_preload_sequence_redistribution.v1"] = (
        "matintegrity.gasket_bolt_preload_sequence_redistribution.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    ordered_bolt_ids: tuple[str, ...] = Field(min_length=2, max_length=256)
    initial_preload_N_by_bolt: tuple[Nonnegative, ...] = Field(min_length=2, max_length=256)
    elastic_interaction_coefficients: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=256)
    operations: tuple[GasketBoltTighteningOperation, ...] = Field(min_length=1, max_length=10000)
    interaction_provider_id: str = Field(min_length=1)
    interaction_provider_revision: str = Field(min_length=1)
    interaction_record_id: str = Field(min_length=1)
    interaction_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    computational_use_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    coefficient_sign_and_order_reviewed: bool
    linear_elastic_superposition_reviewed: bool
    fixed_joint_configuration_and_contact_regime_reviewed: bool
    interaction_matrix_applicability_reviewed: bool
    target_increment_basis_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_sequence(self):
        count = len(self.ordered_bolt_ids)
        if len(set(self.ordered_bolt_ids)) != count or any(not value for value in self.ordered_bolt_ids):
            raise ValueError("ordered bolt IDs must be nonempty and unique")
        if len(self.initial_preload_N_by_bolt) != count:
            raise ValueError("initial preload vector must match ordered bolt IDs")
        if len(self.elastic_interaction_coefficients) != count or any(
            len(row) != count for row in self.elastic_interaction_coefficients
        ):
            raise ValueError("interaction matrix must be square and match ordered bolt IDs")
        if not all(math.isfinite(value) for row in self.elastic_interaction_coefficients for value in row):
            raise ValueError("interaction coefficients must be finite")
        tolerance = 1e-9
        if any(abs(self.elastic_interaction_coefficients[i][i] - 1.0) > tolerance for i in range(count)):
            raise ValueError("each interaction matrix diagonal coefficient must be one for the directly tightened bolt")
        known = set(self.ordered_bolt_ids)
        operation_ids = [row.operation_id for row in self.operations]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("operation IDs must be unique")
        if any(row.tightened_bolt_id not in known for row in self.operations):
            raise ValueError("every operation must reference a bolt in ordered_bolt_ids")
        record = {
            "joint_id": self.joint_id,
            "ordered_bolt_ids": list(self.ordered_bolt_ids),
            "provider_id": self.interaction_provider_id,
            "provider_revision": self.interaction_provider_revision,
            "record_id": self.interaction_record_id,
            "interaction_coefficients": [list(row) for row in self.elastic_interaction_coefficients],
        }
        if canonical_digest(record) != self.interaction_record_sha256:
            raise ValueError("interaction digest must bind joint, bolt order, provider revision and coefficient matrix")
        if not any(row.source_id == self.interaction_provider_id and row.sha256 == self.interaction_record_sha256
                   and row.license_id == self.computational_use_license_id for row in self.evidence):
            raise ValueError("Evidence must bind the interaction provider, record digest and computational-use license")
        return self


def evaluate_gasket_bolt_preload_sequence_redistribution(
    request: GasketBoltPreloadSequenceRedistribution,
) -> Calculation:
    """Apply a caller elastic interaction matrix to sequential single-bolt increments."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.joint_id,
        "model_id": MODEL_ID,
        "input_sha256": input_digest,
        "interaction_record_sha256": request.interaction_record_sha256,
    }
    review = {
        "coefficient_sign_and_order_reviewed": request.coefficient_sign_and_order_reviewed,
        "linear_elastic_superposition_reviewed": request.linear_elastic_superposition_reviewed,
        "fixed_joint_configuration_and_contact_regime_reviewed": request.fixed_joint_configuration_and_contact_regime_reviewed,
        "interaction_matrix_applicability_reviewed": request.interaction_matrix_applicability_reviewed,
        "target_increment_basis_reviewed": request.target_increment_basis_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in review.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    bolt_index = {bolt_id: index for index, bolt_id in enumerate(request.ordered_bolt_ids)}
    loads = list(request.initial_preload_N_by_bolt)
    rows = [{"stage": "initial", "operation_id": None, "pass_id": None,
             "bolt_preload_N_by_id": dict(zip(request.ordered_bolt_ids, loads, strict=True))}]
    operation_results = []
    try:
        for operation in request.operations:
            tightened_index = bolt_index[operation.tightened_bolt_id]
            delta = operation.applied_preload_increment_N
            increment_vector = [request.elastic_interaction_coefficients[i][tightened_index] * delta
                                for i in range(len(loads))]
            updated = [load + change for load, change in zip(loads, increment_vector, strict=True)]
            if not all(math.isfinite(value) for value in (*increment_vector, *updated)):
                raise OverflowError("tightening sequence generated nonfinite preload")
            if any(value < 0 for value in updated):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "linear_interaction_predicts_non_tensile_final_bolt_load",
                    "failed_operation_id": operation.operation_id,
                    "preload_N_by_bolt": dict(zip(request.ordered_bolt_ids, updated, strict=True)),
                    "completed_operation_count": len(operation_results),
                })
            loads = updated
            state = dict(zip(request.ordered_bolt_ids, loads, strict=True))
            operation_results.append({
                "operation_id": operation.operation_id,
                "pass_id": operation.pass_id,
                "tightened_bolt_id": operation.tightened_bolt_id,
                "applied_preload_increment_N": delta,
                "preload_increment_N_by_bolt": dict(zip(request.ordered_bolt_ids, increment_vector, strict=True)),
                "preload_N_by_bolt": state,
            })
            rows.append({"stage": "after_operation", **operation_results[-1]})
    except (ArithmeticError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "elastic_interaction_sequence_outside_finite_numeric_support",
            "detail": str(error),
            "completed_operation_count": len(operation_results),
        })
    try:
        mean = math.fsum(loads) / len(loads)
        variance = math.fsum((value - mean) ** 2 for value in loads) / len(loads)
        standard_deviation = math.sqrt(variance)
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "final_preload_statistics_outside_finite_numeric_support",
            "detail": str(error),
            "completed_operation_count": len(operation_results),
        })
    if not all(math.isfinite(value) for value in (mean, variance, standard_deviation)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "final_preload_statistics_outside_finite_numeric_support",
            "completed_operation_count": len(operation_results),
        })
    coefficient_of_variation = standard_deviation / mean if mean > 0 else None
    return Calculation(status="computed", values=base | {
        "ordered_bolt_ids": list(request.ordered_bolt_ids),
        "final_preload_N_by_bolt": dict(zip(request.ordered_bolt_ids, loads, strict=True)),
        "final_preload_statistics": {
            "mean_N": mean,
            "population_standard_deviation_N": standard_deviation,
            "coefficient_of_variation": coefficient_of_variation,
            "minimum_N": min(loads),
            "maximum_N": max(loads),
            "range_N": max(loads) - min(loads),
        },
        "operation_history": rows,
        "calculation_method": "sequential_linear_superposition_of_caller_elastic_interaction_matrix_columns",
        "limitations": [
            "Each operation represents one positive incremental preload applied to one bolt; the same fixed interaction matrix is applied at every pass.",
            "Matrix coefficients must originate from caller evidence applicable to this joint geometry, gasket/contact state and tightening method.",
            "Torque conversion, nonlinear joint response, contact changes, settling, plasticity, torque scatter distributions, residual stress, seal acceptance and failure probability are not inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketBoltPreloadSequenceRedistribution,
        evaluate_gasket_bolt_preload_sequence_redistribution,
        {
            "operation_history[].applied_preload_increment_N": "N",
            "operation_history[].preload_N_by_bolt": "N",
            "final_preload_N_by_bolt": "N",
            "final_preload_statistics.mean_N": "N",
            "final_preload_statistics.population_standard_deviation_N": "N",
            "final_preload_statistics.range_N": "N",
        },
        (
            "Each tightening operation adds its applied target increment multiplied by the corresponding caller interaction-matrix column to the complete bolt preload vector.",
            "The same interaction matrix and linear superposition assumption are held across every ordered operation.",
            "The model does not calculate the interaction matrix, torque-to-preload response, nonlinear contact or sealing acceptance.",
        ),
        (
            "caller_joint_specific_elastic_interaction_matrix",
            "caller_ordered_bolt_tightening_operations_and_preload_increments",
            "sequential_linear_superposition_of_elastic_bolt_load_transfer",
        ),
        qualification="user_model",
    )]
