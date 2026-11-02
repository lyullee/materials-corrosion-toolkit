"""Bind a charge-consistent double-layer current schedule to component-state BDF."""
from __future__ import annotations

import math

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_component_state_bdf import (
    CALLER_CAPACITIVE_CURRENT_SOURCE_ID,
    CapacitiveCellCurrentSchedule,
    CreviceComponentStateBDFRequest,
)
from .crevice_double_layer_charge_history import (
    CreviceDoubleLayerChargeHistoryRequest,
    evaluate_crevice_double_layer_charge_history,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_double_layer_to_component_bdf_binding"
METHOD_SOURCE_ID = "charge_conserving_double_layer_current_schedule_to_component_bdf"


class CreviceDoubleLayerBDFBindingRequest(Contract):
    """Charge-conservative, operator-split binding of caller current knots.

    Double-layer stored charge is positive into the electrode. The BDF
    capacitive source uses current positive into aqueous solution, so integrated
    BDF charge must equal the negative stored-electrode-charge change.
    """

    schema_version: Literal["matintegrity.crevice_double_layer_bdf_binding.v1"] = (
        "matintegrity.crevice_double_layer_bdf_binding.v1"
    )
    assessment_id: str = Field(min_length=1)
    component_state_request: CreviceComponentStateBDFRequest
    double_layer_request: CreviceDoubleLayerChargeHistoryRequest
    current_A_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    current_schedule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_schedule_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    absolute_charge_closure_tolerance_C: float = Field(gt=0.0)
    relative_charge_closure_tolerance: float = Field(gt=0.0, le=1e-2)
    cell_time_geometry_alignment_reviewed: bool
    electrode_to_aqueous_current_sign_reviewed: bool
    piecewise_linear_current_reconstruction_reviewed: bool
    charge_closure_and_operator_split_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_binding_inputs(self):
        bdf = self.component_state_request
        dl = self.double_layer_request
        if bdf.assessment_id != self.assessment_id or dl.assessment_id != self.assessment_id:
            raise ValueError("binding assessment ID must match both source requests")
        cell_ids = tuple(cell.cell_id for cell in bdf.cells)
        if tuple(bdf.time_s) != tuple(dl.time_s) or cell_ids != tuple(dl.cell_ids):
            raise ValueError("BDF and double-layer exact times and ordered cell IDs must match")
        if bdf.capacitive_current_schedule is not None or bdf.capacitive_current_schedule_reviewed:
            raise ValueError("component-state request must not already contain capacitive-current forcing")
        nt, nc = len(bdf.time_s), len(cell_ids)
        if len(self.current_A_by_knot_and_cell) != nt or any(len(row) != nc for row in self.current_A_by_knot_and_cell):
            raise ValueError("current knots must align exactly with BDF time and cell order")
        if any(not math.isfinite(value) for row in self.current_A_by_knot_and_cell for value in row):
            raise ValueError("capacitive current knots must be finite signed values")
        schedule_record = {
            "time_s": list(bdf.time_s),
            "current_A_by_knot_and_cell": [list(row) for row in self.current_A_by_knot_and_cell],
        }
        if canonical_digest(schedule_record) != self.current_schedule_sha256:
            raise ValueError("current schedule digest must bind exact ordered time and per-cell values")
        if not any(
            row.sha256 == self.current_schedule_sha256
            and row.source_id == CALLER_CAPACITIVE_CURRENT_SOURCE_ID
            and row.license_id
            for row in self.current_schedule_evidence
        ):
            raise ValueError("current schedule Evidence must license and pin its exact schedule digest")
        if not all((self.cell_time_geometry_alignment_reviewed,
                    self.electrode_to_aqueous_current_sign_reviewed,
                    self.piecewise_linear_current_reconstruction_reviewed,
                    self.charge_closure_and_operator_split_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("alignment, sign, interpolation, closure and computational-use reviews are required")
        return self


def evaluate_crevice_double_layer_bdf_binding(
    request: CreviceDoubleLayerBDFBindingRequest,
) -> Calculation:
    """Recompute double-layer charge and bind a caller current schedule if it closes."""
    digest = canonical_digest(request.model_dump(mode="json"))
    bdf = request.component_state_request
    dl_result = evaluate_crevice_double_layer_charge_history(request.double_layer_request)
    if dl_result.status != "computed":
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "double_layer_charge_history_not_computed",
            "double_layer_result": dl_result.model_dump(mode="json"), "committed": False,
        })
    charges = dl_result.values["stored_double_layer_charge_C_by_knot_and_cell"]
    times = tuple(bdf.time_s)
    currents = request.current_A_by_knot_and_cell
    interval_rows = []
    maximum_abs_residual = 0.0
    maximum_normalized_residual = 0.0
    for k, (t0, t1) in enumerate(zip(times[:-1], times[1:], strict=True)):
        dt = t1 - t0
        per_cell = []
        for cell_index in range(len(bdf.cells)):
            # BDF current is positive into aqueous; electrode stored-charge
            # increase is balanced by an equal negative aqueous charge transfer.
            expected_aqueous_charge_C = -(float(charges[k + 1][cell_index]) - float(charges[k][cell_index]))
            integrated_aqueous_charge_C = 0.5 * dt * (
                float(currents[k][cell_index]) + float(currents[k + 1][cell_index])
            )
            residual = integrated_aqueous_charge_C - expected_aqueous_charge_C
            scale = max(abs(integrated_aqueous_charge_C), abs(expected_aqueous_charge_C))
            allowed = request.absolute_charge_closure_tolerance_C + request.relative_charge_closure_tolerance * scale
            ratio = abs(residual) / allowed
            maximum_abs_residual = max(maximum_abs_residual, abs(residual))
            maximum_normalized_residual = max(maximum_normalized_residual, ratio)
            per_cell.append({
                "cell_id": bdf.cells[cell_index].cell_id,
                "expected_aqueous_charge_change_C": expected_aqueous_charge_C,
                "integrated_BDF_capacitive_charge_C": integrated_aqueous_charge_C,
                "charge_residual_C": residual,
                "allowed_residual_C": allowed,
                "normalized_residual": ratio,
                "closed": abs(residual) <= allowed,
            })
        interval_rows.append({"start_time_s": t0, "end_time_s": t1, "cells": per_cell})
    if maximum_normalized_residual > 1.0:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "double_layer_input_sha256": canonical_digest(
                request.double_layer_request.model_dump(mode="json")
            ), "current_schedule_sha256": request.current_schedule_sha256,
            "maximum_absolute_charge_residual_C": maximum_abs_residual,
            "maximum_normalized_charge_residual": maximum_normalized_residual,
            "interval_charge_closure": interval_rows, "committed": False,
            "qualification_claimed": False,
        })
    schedule = CapacitiveCellCurrentSchedule(
        time_s=times,
        current_A_by_knot_and_cell=currents,
        schedule_sha256=request.current_schedule_sha256,
        evidence=request.current_schedule_evidence,
    )
    try:
        payload = bdf.model_dump(mode="python")
        payload.update({
            "capacitive_current_schedule": schedule,
            "capacitive_current_schedule_reviewed": True,
        })
        bound = CreviceComponentStateBDFRequest.model_validate(payload)
    except (TypeError, ValueError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "reason": f"bound_component_state_request_validation_failed:{error}",
            "maximum_absolute_charge_residual_C": maximum_abs_residual,
            "maximum_normalized_charge_residual": maximum_normalized_residual,
            "committed": False,
            "qualification_claimed": False,
        })
    bound_sha = canonical_digest(bound.model_dump(mode="json"))
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "double_layer_input_sha256": canonical_digest(request.double_layer_request.model_dump(mode="json")),
        "double_layer_result_sha256": canonical_digest(dl_result.model_dump(mode="json")),
        "current_schedule_sha256": request.current_schedule_sha256,
        "component_state_request": bound.model_dump(mode="json"),
        "component_state_request_sha256": bound_sha,
        "maximum_absolute_charge_residual_C": maximum_abs_residual,
        "maximum_normalized_charge_residual": maximum_normalized_residual,
        "interval_charge_closure": interval_rows,
        "charge_conserving_schedule_bound": True,
        "potential_is_caller_prescribed": True,
        "qualification_claimed": False,
        "limitations": [
            "The potential, active-area, capacitance and knot-current histories are caller supplied; this adapter verifies their integrated charge consistency but does not solve an electrode-potential state.",
            "The BDF uses a piecewise-linear prescribed current between exact knots. Charge is conserved intervalwise against the independently recomputed double-layer stored-charge change; instantaneous constitutive current is not established within each interval.",
            "Faradaic-current coupling remains governed by the component-state BDF charge-continuity solver and its caller reviews; this binding does not infer capacitance, potential or material kinetics.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceDoubleLayerBDFBindingRequest,
        evaluator=evaluate_crevice_double_layer_bdf_binding,
        units={
            "current_A_by_knot_and_cell[][]": "A",
            "component_state_request.capacitive_current_schedule.current_A_by_knot_and_cell[][]": "A",
            "interval_charge_closure[].cells[].expected_aqueous_charge_change_C": "C",
            "interval_charge_closure[].cells[].integrated_BDF_capacitive_charge_C": "C",
            "interval_charge_closure[].cells[].charge_residual_C": "C",
            "maximum_absolute_charge_residual_C": "C",
        },
        assumptions=(
            "The double-layer history uses caller-pinned potential, reference potential, active area and differential capacitance; its stored charge is positive into the electrode.",
            "The component-state BDF capacitive source is positive into aqueous solution and must integrate to the negative electrode charge change on every exact interval and cell.",
            "Caller current knots are reconstructed linearly between exact knots; only interval charge closure is established, not instantaneous current constitutive fidelity.",
            "The adapter produces a typed BDF request and does not solve electrode potential or infer Faradaic kinetics.",
        ),
        source_ids=(METHOD_SOURCE_ID, CALLER_CAPACITIVE_CURRENT_SOURCE_ID),
        version="0.1.0",
        qualification="user_model",
    ),)
