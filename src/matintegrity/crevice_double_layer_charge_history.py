"""Caller-parameterized double-layer charge and interval-current history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_double_layer_charge_history"
SOURCE_ID = "caller_reviewed_crevice_double_layer_capacitance_charge_integration"
MAX_RECORDS = 20_000_000


class CreviceDoubleLayerChargeHistoryRequest(Contract):
    """Integrate tabulated differential capacitance over a supplied potential path.

    Potential and active area are knot histories in source order. Capacitance is
    a caller-supplied differential-capacitance density curve; no electrochemical
    potential, area, or capacitance is inferred by this calculator.
    """

    schema_version: Literal["matintegrity.crevice_double_layer_charge_history.v1"] = (
        "matintegrity.crevice_double_layer_charge_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=300)
    potential_V_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    active_area_m2_by_knot_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    reference_potential_V_by_cell: tuple[float, ...] = Field(min_length=1, max_length=300)
    differential_capacitance_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    potential_axis_V: tuple[float, ...] = Field(min_length=2, max_length=1000)
    differential_capacitance_F_m2: tuple[Positive, ...] = Field(min_length=2, max_length=1000)
    curve_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    area_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    area_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    positive_current_direction_basis: Literal["into_electrode"] = "into_electrode"
    tabulated_differential_capacitance_reviewed: bool
    active_area_and_potential_alignment_reviewed: bool
    linear_charge_interpolation_between_knots_reviewed: bool
    double_layer_only_interpretation_reviewed: bool
    computation_budget_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        nt, nc = len(self.time_s), len(self.cell_ids)
        if len(set(self.cell_ids)) != nc:
            raise ValueError("cell IDs must be unique and remain in source order")
        if len(self.potential_V_by_knot_and_cell) != nt or any(
            len(row) != nc for row in self.potential_V_by_knot_and_cell
        ):
            raise ValueError("potential history must align with exact knots and cells")
        if len(self.active_area_m2_by_knot_and_cell) != nt or any(
            len(row) != nc for row in self.active_area_m2_by_knot_and_cell
        ):
            raise ValueError("active-area history must align with exact knots and cells")
        if len(self.reference_potential_V_by_cell) != nc:
            raise ValueError("reference potential must align with cells")
        if len(self.potential_axis_V) != len(self.differential_capacitance_F_m2):
            raise ValueError("capacitance axis and ordinate arrays must have the same length")
        if (nt - 1) * nc * len(self.potential_axis_V) > MAX_RECORDS:
            raise ValueError("potential-cell-curve operation count exceeds the finite budget")
        if any(not math.isfinite(t) or t < 0 for t in self.time_s) or self.time_s[0] != 0.0:
            raise ValueError("time knots must be finite, nonnegative and start at zero")
        if any(b <= a for a, b in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("time knots must increase strictly")
        if any(not math.isfinite(v) for row in self.potential_V_by_knot_and_cell for v in row):
            raise ValueError("potential histories must be finite")
        if any(not math.isfinite(float(v)) for row in self.active_area_m2_by_knot_and_cell for v in row):
            raise ValueError("active-area history must be finite")
        if any(not math.isfinite(v) for v in self.reference_potential_V_by_cell):
            raise ValueError("reference potentials must be finite")
        if any(not math.isfinite(float(v)) for v in self.differential_capacitance_F_m2):
            raise ValueError("differential-capacitance ordinates must be finite")
        if any(not math.isfinite(v) for v in self.potential_axis_V) or any(
            b <= a for a, b in zip(self.potential_axis_V, self.potential_axis_V[1:], strict=True)
        ):
            raise ValueError("capacitance potential axis must be finite and strictly increasing")
        curve = {
            "potential_axis_V": list(self.potential_axis_V),
            "differential_capacitance_F_m2": list(self.differential_capacitance_F_m2),
        }
        if canonical_digest(curve) != self.differential_capacitance_curve_sha256:
            raise ValueError("capacitance-curve digest must bind the exact ordered curve")
        if not any(
            row.sha256 == self.differential_capacitance_curve_sha256
            and row.source_id == SOURCE_ID and row.license_id
            for row in self.curve_evidence
        ):
            raise ValueError("curve Evidence must license and pin the capacitance record")
        area_record = {
            "cell_ids": list(self.cell_ids),
            "time_s": list(self.time_s),
            "active_area_m2_by_knot_and_cell": [list(row) for row in self.active_area_m2_by_knot_and_cell],
            "reference_potential_V_by_cell": list(self.reference_potential_V_by_cell),
        }
        if canonical_digest(area_record) != self.area_record_sha256:
            raise ValueError("area-record digest must bind the ordered cell/clock/area/reference mapping")
        if not any(
            row.sha256 == self.area_record_sha256 and row.source_id == SOURCE_ID and row.license_id
            for row in self.area_evidence
        ):
            raise ValueError("area Evidence must license and pin the exact area mapping")
        lower, upper = self.potential_axis_V[0], self.potential_axis_V[-1]
        for value in (*self.reference_potential_V_by_cell,
                      *(v for row in self.potential_V_by_knot_and_cell for v in row)):
            if not lower <= value <= upper:
                raise ValueError("potential or reference lies outside tabulated capacitance support")
        if not all((self.tabulated_differential_capacitance_reviewed,
                    self.active_area_and_potential_alignment_reviewed,
                    self.linear_charge_interpolation_between_knots_reviewed,
                    self.double_layer_only_interpretation_reviewed,
                    self.computation_budget_reviewed)):
            raise ValueError("all curve, geometry, interpolation, interpretation and budget reviews are required")
        return self


def _integrated_areal_charge(potential: float, reference: float,
                             axis: tuple[float, ...], capacitance: tuple[float, ...]) -> float:
    """Integrate a piecewise-linear differential capacitance exactly."""
    if potential == reference:
        return 0.0
    direction = 1.0 if potential > reference else -1.0
    low, high = (reference, potential) if direction > 0 else (potential, reference)
    total = 0.0
    for index, (left, right) in enumerate(zip(axis[:-1], axis[1:], strict=True)):
        a, b = max(low, left), min(high, right)
        if b <= a:
            continue
        slope = (capacitance[index + 1] - capacitance[index]) / (right - left)
        ca = capacitance[index] + slope * (a - left)
        cb = capacitance[index] + slope * (b - left)
        total += (b - a) * (ca + cb) * 0.5
    return direction * total


def evaluate_crevice_double_layer_charge_history(
    request: CreviceDoubleLayerChargeHistoryRequest,
) -> Calculation:
    """Return stored charge at knots and mean capacitive current per interval.

    The signed current is the change in the caller-mapped stored charge divided
    by interval duration. It is not a Faradaic current or a kinetic law.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    charges = []
    for knot, (potentials, areas) in enumerate(zip(
        request.potential_V_by_knot_and_cell, request.active_area_m2_by_knot_and_cell, strict=True
    )):
        row = []
        for cell, (potential, area, reference) in enumerate(zip(
            potentials, areas, request.reference_potential_V_by_cell, strict=True
        )):
            areal_charge = _integrated_areal_charge(
                potential, reference, request.potential_axis_V, request.differential_capacitance_F_m2
            )
            charge = float(area) * areal_charge
            if not math.isfinite(charge):
                return Calculation(status="out_of_scope", values={
                    "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_knot_index": knot, "failed_cell_id": request.cell_ids[cell],
                    "reason": "nonfinite double-layer charge", "committed": False,
                })
            row.append(charge)
        charges.append(row)
    intervals = []
    for index, (left, right) in enumerate(zip(charges[:-1], charges[1:], strict=True)):
        duration = request.time_s[index + 1] - request.time_s[index]
        delta = [b - a for a, b in zip(left, right, strict=True)]
        current = [value / duration for value in delta]
        if not all(math.isfinite(value) for value in (*delta, *current)):
            return Calculation(status="out_of_scope", values={
                "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": index, "reason": "nonfinite interval charge/current", "committed": False,
            })
        intervals.append({
            "start_time_s": request.time_s[index],
            "end_time_s": request.time_s[index + 1],
            "charge_change_C_by_cell": delta,
            "mean_capacitive_current_A_by_cell": current,
            "mean_capacitive_current_A": math.fsum(current),
            "charge_balance_residual_C": math.fsum(delta) - math.fsum(current) * duration,
        })
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "time_s": list(request.time_s),
        "cell_ids": list(request.cell_ids),
        "stored_double_layer_charge_C_by_knot_and_cell": charges,
        "intervals": intervals,
        "positive_current_direction_basis": request.positive_current_direction_basis,
        "capacitance_curve_sha256": request.differential_capacitance_curve_sha256,
        "area_record_sha256": request.area_record_sha256,
        "double_layer_current_is_faradic": False,
        "charge_closure_checked": True,
        "qualification_claimed": False,
    }, notes=(
        "The tabulated differential capacitance is caller supplied and integrated exactly segment by segment as a piecewise-linear curve.",
        "Returned currents are interval-mean double-layer charging currents from caller potential and area histories; they are not coupled into ionic transport or a mixed-potential solution.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        CreviceDoubleLayerChargeHistoryRequest,
        evaluate_crevice_double_layer_charge_history,
        {
            "stored_double_layer_charge_C_by_knot_and_cell[][]": "C",
            "intervals[].charge_change_C_by_cell[]": "C",
            "intervals[].mean_capacitive_current_A_by_cell[]": "A",
            "intervals[].mean_capacitive_current_A": "A",
            "intervals[].charge_balance_residual_C": "C",
        },
        (
            "Potential, active area, reference potential and differential-capacitance curve are caller records pinned by licensed Evidence.",
            "Differential capacitance is piecewise-linear in potential and its integral is evaluated exactly on each tabulation segment.",
            "Capacitive current is the interval-average change in stored charge; no Faradaic kinetics, mixed potential, ionic transport or material qualification is inferred.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
    )]
