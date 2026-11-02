"""Integrate caller-calibrated solid saturation laws over exact crevice intervals."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .multiphase_kinetic_ledger import SolidSaturationRateLaw, _derive_solid_saturation_rate
from .multiphase_kinetic_transport import CellwiseCompetingSolidRateInterval, CompetingSolidKineticTransport
from .registry import ModelSpec

MODEL_ID = "integration.crevice_saturation_interval_average_rates"
SOURCE_ID = "caller_crevice_saturation_path_average_rate"
MAX_RECORDS = 2_000_000


class CreviceLocalSaturationKnot(Contract):
    elapsed_time_s: float = Field(ge=0)
    saturation_result: dict
    saturation_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_result(self):
        if canonical_digest(self.saturation_result) != self.saturation_result_sha256:
            raise ValueError("local saturation result digest mismatch")
        if self.saturation_result.get("status") != "computed":
            raise ValueError("computed local saturation result is required")
        return self


class CreviceSaturationIntervalRateRequest(Contract):
    schema_version: Literal["matintegrity.crevice_saturation_interval_rate.v1"] = (
        "matintegrity.crevice_saturation_interval_rate.v1"
    )
    assessment_id: str = Field(min_length=1)
    kinetic_campaign: CompetingSolidKineticTransport
    saturation_knots: tuple[CreviceLocalSaturationKnot, ...] = Field(min_length=2, max_length=5001)
    quadrature_order: int = Field(default=16, ge=8, le=64)
    piecewise_linear_saturation_ratio_reviewed: bool
    exact_cell_phase_knot_mapping_reviewed: bool
    uniform_kinetic_temperature_mapping_reviewed: bool
    average_rate_applied_over_each_interval_reviewed: bool
    no_within_interval_saturation_feedback_reviewed: bool

    @model_validator(mode="after")
    def check_alignment_and_scope(self):
        campaign = self.kinetic_campaign
        if not campaign.phase_rate_laws or campaign.kinetic_intervals:
            raise ValueError("saturation-driven kinetic campaign with phase rate laws is required")
        times = campaign.transport.output_times_s
        if tuple(row.elapsed_time_s for row in self.saturation_knots) != times:
            raise ValueError("saturation knots must exactly match the kinetic transport output clock")
        if len(self.saturation_knots) * campaign.transport.cell_count * len(campaign.phase_rate_laws) > MAX_RECORDS:
            raise ValueError("phase-by-cell-by-knot record budget exceeded")
        expected_phases = {law.solid_species_id for law in campaign.phase_rate_laws}
        actual_phases = {row.solid_species_id for row in campaign.candidate_solid_phases}
        if expected_phases != actual_phases:
            raise ValueError("every saturation-rate law must match one declared kinetic solid phase")
        return self


def _rate(law: SolidSaturationRateLaw, ratio: float, temperature: float) -> float:
    return float(_derive_solid_saturation_rate(law, ratio, temperature_K=temperature)["signed_extent_rate_mol_m3_s"])


def _interval_mean_rate(
    law: SolidSaturationRateLaw,
    left_ratio: float,
    right_ratio: float,
    temperature_K: float,
    duration_s: float,
    nodes: np.ndarray,
    weights: np.ndarray,
) -> float:
    if left_ratio == right_ratio:
        return _rate(law, left_ratio, temperature_K)
    breakpoints = [0.0, 1.0]
    if (left_ratio - 1.0) * (right_ratio - 1.0) < 0.0:
        crossing = (1.0 - left_ratio) / (right_ratio - left_ratio)
        breakpoints.insert(1, crossing)
    integrated = 0.0
    delta = right_ratio - left_ratio
    for lower, upper in zip(breakpoints[:-1], breakpoints[1:], strict=True):
        fractions = lower + (nodes + 1.0) * (upper - lower) / 2.0
        ratios = left_ratio + fractions * delta
        rates = [_rate(law, float(value), temperature_K) for value in ratios]
        integrated += duration_s * (upper - lower) * 0.5 * float(np.dot(weights, rates))
    return integrated / duration_s


def evaluate_crevice_saturation_interval_rates(request: CreviceSaturationIntervalRateRequest) -> Calculation:
    """Produce exact-clock interval rates by quadraturing the declared saturation path."""
    campaign = request.kinetic_campaign
    transport = campaign.transport
    request_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "campaign_id": campaign.campaign_id,
        "physical_scope_id": campaign.physical_scope_id,
        "input_sha256": request_sha,
        "kinetic_campaign_input_sha256": canonical_digest(campaign.model_dump(mode="json")),
        "quadrature_order": request.quadrature_order,
        "rate_units": "mol/m3/s",
    }
    reviews = (
        "piecewise_linear_saturation_ratio_reviewed",
        "exact_cell_phase_knot_mapping_reviewed",
        "uniform_kinetic_temperature_mapping_reviewed",
        "average_rate_applied_over_each_interval_reviewed",
        "no_within_interval_saturation_feedback_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "completed_interval_count": 0, "intervals": [],
        })

    phases = [law.solid_species_id for law in campaign.phase_rate_laws]
    laws = {law.solid_species_id: law for law in campaign.phase_rate_laws}
    knots = []
    for index, knot in enumerate(request.saturation_knots):
        values = knot.saturation_result.get("values", knot.saturation_result)
        if (
            knot.saturation_result.get("status") != "computed"
            or values.get("physical_scope_id") != campaign.physical_scope_id
            or values.get("elapsed_time_s") != knot.elapsed_time_s
            or values.get("cell_count") != transport.cell_count
            or values.get("candidate_solid_ids") is None
            or set(values.get("candidate_solid_ids", ())) != set(phases)
        ):
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": 0,
                "failed_knot_index": index,
                "intervals": [],
                "reason": "local saturation result scope, time, cell or candidate phase identities do not match the kinetic campaign",
            })
        cells = values.get("completed_cells")
        if not isinstance(cells, list) or len(cells) != transport.cell_count:
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": 0,
                "failed_knot_index": index,
                "reason": "local saturation history does not contain every transport cell",
            })
        cell_map: list[dict[str, float]] = []
        for cell_index, cell in enumerate(cells):
            if not isinstance(cell, dict) or cell.get("cell_index") != cell_index:
                return Calculation(status="out_of_scope", values=base | {
                    "completed_interval_count": 0,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "reason": "local saturation cell order does not match transport",
                })
            candidates = cell.get("candidate_results")
            candidate_map = {row.get("solid_id"): row for row in candidates if isinstance(row, dict)} if isinstance(candidates, list) else {}
            if len(candidate_map) != len(candidates or ()) or set(candidate_map) != set(phases):
                return Calculation(status="out_of_scope", values=base | {
                    "completed_interval_count": 0,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "reason": "candidate saturation results are incomplete or duplicated",
                })
            ratios = {}
            if cell.get("temperature_K") != campaign.temperature_K:
                return Calculation(status="out_of_scope", values=base | {
                    "completed_interval_count": 0,
                    "failed_knot_index": index, "failed_cell_index": cell_index,
                    "reason": "local speciation temperature does not match the solid kinetic rate-law temperature",
                })
            for phase_id in phases:
                ratio = candidate_map[phase_id].get("saturation_ratio")
                if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio < 0:
                    return Calculation(status="out_of_scope", values=base | {
                        "completed_interval_count": 0,
                        "failed_knot_index": index, "failed_cell_index": cell_index,
                        "failed_solid_phase_id": phase_id,
                        "reason": "finite nonnegative saturation ratio is required; log-only out-of-float-range values are unsupported",
                    })
                ratios[phase_id] = float(ratio)
            cell_map.append(ratios)
        knots.append({
            "time_s": knot.elapsed_time_s,
            "result_sha256": knot.saturation_result_sha256,
            "cells": cell_map,
        })

    nodes, weights = np.polynomial.legendre.leggauss(request.quadrature_order)
    intervals: list[dict] = []
    for interval_index, (left, right) in enumerate(zip(knots[:-1], knots[1:], strict=True)):
        duration = right["time_s"] - left["time_s"]
        if not math.isfinite(duration) or duration <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": len(intervals), "intervals": intervals,
                "failed_interval_index": interval_index, "reason": "invalid exact time interval",
            })
        rates_by_phase: dict[str, list[float]] = {phase_id: [] for phase_id in phases}
        try:
            for cell_index in range(transport.cell_count):
                for phase_id in phases:
                    average = _interval_mean_rate(
                        laws[phase_id], left["cells"][cell_index][phase_id],
                        right["cells"][cell_index][phase_id], campaign.temperature_K,
                        duration, nodes, weights,
                    )
                    if not math.isfinite(average):
                        raise ArithmeticError("average phase extent rate exceeds finite support")
                    rates_by_phase[phase_id].append(average)
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": len(intervals), "intervals": intervals,
                "failed_interval_index": interval_index,
                "reason": f"saturation-rate interval integration failed: {type(error).__name__}",
            })
        typed_interval = CellwiseCompetingSolidRateInterval(
            interval_id=f"{campaign.campaign_id}:saturation-average:{interval_index}",
            start_time_s=left["time_s"],
            end_time_s=right["time_s"],
            phase_extent_rate_mol_m3_s_by_cell={key: tuple(value) for key, value in rates_by_phase.items()},
        )
        intervals.append({
            **typed_interval.model_dump(mode="json"),
            "left_saturation_result_sha256": left["result_sha256"],
            "right_saturation_result_sha256": right["result_sha256"],
            "path_basis": "piecewise_linear_saturation_ratio; Gauss-Legendre quadrature split at S=1",
        })
    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(intervals),
        "intervals": intervals,
        "quadrature_method": "Gauss-Legendre on each side of the saturation threshold",
        "quadrature_order_per_subinterval": request.quadrature_order,
        "phase_rate_law_source_sha256_by_phase": {law.solid_species_id: law.source_sha256 for law in campaign.phase_rate_laws},
        "transport_interval_clock_s": list(transport.output_times_s),
        "interpretation_boundary": "These are interval-average signed phase rates for the existing inventory-limited kinetic ledger under a caller-reviewed linear saturation-ratio path and fixed temperature. The path is prescribed; no within-interval chemistry/transport feedback or quadrature error bound is inferred.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSaturationIntervalRateRequest,
        evaluator=evaluate_crevice_saturation_interval_rates,
        units={
            "saturation_knots[].elapsed_time_s": "s",
            "quadrature_order_per_subinterval": "1",
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].phase_extent_rate_mol_m3_s_by_cell.*": "mol/(m3 s)",
        },
        assumptions=(
            "Exact local saturation results cover every transport cell and candidate solid at each exact transport clock knot.",
            "Saturation ratio is reconstructed piecewise linearly within each transport interval; the caller explicitly reviews this approximation.",
            "Existing caller-calibrated precipitation/dissolution constants and exponents are applied at their declared fixed campaign temperature/support.",
            "An even subdivision at S=1 is integrated with caller-selected finite-order Gauss-Legendre quadrature; no error estimate or exactness claim is provided.",
            "The resulting average rates feed only the existing solid inventory-limited, element/charge-balanced kinetic ledger; no within-interval saturation feedback or phase selection is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
