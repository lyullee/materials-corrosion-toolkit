"""Fourier-interpolant tensor work mapped to caller lives and Miner damage."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .multiaxial_fourier_tensor_work import PeriodicFourierTensorWork, evaluate_periodic_fourier_tensor_work
from .registry import ModelSpec


class FourierWorkLifeCycle(Contract):
    cycle_id: str = Field(min_length=1)
    work_request: PeriodicFourierTensorWork
    cycle_count_equivalents: Positive


class FourierTensorWorkLife(Contract):
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    cycles: tuple[FourierWorkLifeCycle, ...] = Field(min_length=1, max_length=10000)
    calibration_id: str = Field(min_length=1)
    calibration_material_condition_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: Evidence
    absolute_work_density_points_J_m3: list[Positive] = Field(min_length=2, max_length=10000)
    cycles_to_failure: list[Positive] = Field(min_length=2, max_length=10000)
    maximum_total_trigonometric_term_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    material_match_and_curve_basis_reviewed: bool
    rights_and_engineering_use_reviewed: bool
    cycle_decomposition_and_repetitions_reviewed: bool
    absolute_work_parameter_and_curve_fit_reviewed: bool
    linear_miner_rule_reviewed: bool

    @model_validator(mode="after")
    def validate_calibration_and_cycles(self):
        if self.material_condition_id != self.calibration_material_condition_id:
            raise ValueError("work-life calibration material condition must match all cycles")
        if self.calibration_evidence.source_id != self.calibration_source_id or self.calibration_evidence.sha256 != self.calibration_sha256:
            raise ValueError("calibration Evidence must match the declared source and digest")
        if len(self.absolute_work_density_points_J_m3) != len(self.cycles_to_failure):
            raise ValueError("work density and failure-life vectors must have equal lengths")
        if any(right <= left for left, right in zip(self.absolute_work_density_points_J_m3[:-1], self.absolute_work_density_points_J_m3[1:], strict=True)):
            raise ValueError("work calibration points must strictly increase")
        if any(right >= left for left, right in zip(self.cycles_to_failure[:-1], self.cycles_to_failure[1:], strict=True)):
            raise ValueError("cycles to failure must strictly decrease as absolute work increases")
        if len({cycle.cycle_id for cycle in self.cycles}) != len(self.cycles):
            raise ValueError("cycle IDs must be unique")
        if any(cycle.work_request.material_condition_id != self.material_condition_id for cycle in self.cycles):
            raise ValueError("every Fourier work request must use the declared material condition")
        return self


def _loglog_map(x: float, x_curve: list[float], y_curve: list[float]) -> tuple[float, int, float] | None:
    if x < x_curve[0] or x > x_curve[-1] or x <= 0.0:
        return None
    exact = next((i for i, value in enumerate(x_curve) if x == value), None)
    if exact is not None:
        return y_curve[exact], exact, 0.0
    index = next(i for i in range(len(x_curve) - 1) if x_curve[i] < x < x_curve[i + 1])
    fraction = (math.log(x) - math.log(x_curve[index])) / (math.log(x_curve[index + 1]) - math.log(x_curve[index]))
    log_y = math.log(y_curve[index]) + fraction * (math.log(y_curve[index + 1]) - math.log(y_curve[index]))
    return math.exp(log_y), index, fraction


def evaluate_fourier_tensor_work_life(request: FourierTensorWorkLife) -> Calculation:
    """Map each exact Fourier-interpolant work integral to life and linear damage."""
    curve_payload = {
        "calibration_id": request.calibration_id,
        "material_condition_id": request.calibration_material_condition_id,
        "source_id": request.calibration_source_id,
        "source_sha256": request.calibration_sha256,
        "absolute_work_density_points_J_m3": request.absolute_work_density_points_J_m3,
        "cycles_to_failure": request.cycles_to_failure,
    }
    curve_digest = canonical_digest(curve_payload)
    input_digest = canonical_digest(request.model_dump(mode="json"))
    work = sum(
        (len(cycle.work_request.sample_ids) - 1) * max(1, (len(cycle.work_request.sample_ids) - 1) // 2) * 12
        for cycle in request.cycles
    )
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "calibration_id": request.calibration_id,
        "calibration_source_id": request.calibration_source_id,
        "calibration_sha256": request.calibration_sha256,
        "normalized_curve_sha256": curve_digest,
        "input_sha256": input_digest,
        "cycle_count": len(request.cycles),
        "total_trigonometric_term_work": work,
    }
    if not all((
        request.material_match_and_curve_basis_reviewed,
        request.rights_and_engineering_use_reviewed,
        request.cycle_decomposition_and_repetitions_reviewed,
        request.absolute_work_parameter_and_curve_fit_reviewed,
        request.linear_miner_rule_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "material_curve_rights_cycle_work_parameter_and_miner_reviews_required",
            "cycle_damage_ledger": None,
            "cumulative_miner_damage": None,
        })
    if work > request.maximum_total_trigonometric_term_work:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "aggregate_fourier_work_budget_exceeded",
            "maximum_total_trigonometric_term_work": request.maximum_total_trigonometric_term_work,
            "cycle_damage_ledger": None,
            "cumulative_miner_damage": None,
        })
    ledger = []
    for cycle in request.cycles:
        result = evaluate_periodic_fourier_tensor_work(cycle.work_request)
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "reason": "underlying_fourier_work_cycle_unavailable",
                "failed_cycle_id": cycle.cycle_id,
                "underlying_values": result.values,
                "cycle_damage_ledger": None,
                "cumulative_miner_damage": None,
            })
        signed_work = result.values["signed_work_density_J_m3"]
        absolute_work = abs(signed_work)
        mapped = _loglog_map(absolute_work, request.absolute_work_density_points_J_m3, request.cycles_to_failure)
        if mapped is None:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "absolute_fourier_work_outside_curve_support_no_extrapolation",
                "failed_cycle_id": cycle.cycle_id,
                "absolute_signed_work_density_J_m3": absolute_work,
                "curve_support_J_m3": [request.absolute_work_density_points_J_m3[0], request.absolute_work_density_points_J_m3[-1]],
                "cycle_damage_ledger": None,
                "cumulative_miner_damage": None,
            })
        life, interval, fraction = mapped
        damage = cycle.cycle_count_equivalents / life
        if not all(math.isfinite(value) for value in (signed_work, absolute_work, life, damage)) or life <= 0.0 or damage < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "fourier_work_life_or_damage_outside_finite_support",
                "failed_cycle_id": cycle.cycle_id,
                "cycle_damage_ledger": None,
                "cumulative_miner_damage": None,
            })
        ledger.append({
            "cycle_id": cycle.cycle_id,
            "signed_work_density_J_m3": signed_work,
            "absolute_work_density_J_m3": absolute_work,
            "cycle_count_equivalents": cycle.cycle_count_equivalents,
            "cycles_to_failure": life,
            "curve_interval_index": interval,
            "interpolation_fraction": fraction,
            "miner_damage_fraction": damage,
            "work_result_sha256": result.values["input_sha256"],
        })
    try:
        cumulative = math.fsum(row["miner_damage_fraction"] for row in ledger)
    except (OverflowError, ValueError):
        cumulative = math.inf
    if not math.isfinite(cumulative):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "cumulative_damage_outside_finite_numeric_support",
            "cycle_damage_ledger": ledger,
            "cumulative_miner_damage": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "cycle_damage_ledger": ledger,
        "cumulative_miner_damage": cumulative,
        "failure_threshold_interpretation": "caller-selected linear Miner threshold; not probability or acceptance",
        "limitations": [
            "The curve is caller-owned and must map absolute signed Fourier-interpolant work to constant-amplitude life for the same material condition.",
            "Absolute work is used as a scalar calibration abscissa; it is not asserted to be irreversible plastic dissipation.",
            "Cycle decomposition, repetitions, curve transfer, linear Miner rule and threshold are caller assumptions.",
            "No interaction, sequence effect, scatter, probability, extrapolation or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.periodic_fourier_tensor_work_life",
        FourierTensorWorkLife,
        evaluate_fourier_tensor_work_life,
        {
            "cycle_damage_ledger[].absolute_work_density_J_m3": "J/m^3",
            "cycle_damage_ledger[].cycles_to_failure": "cycle",
            "cycle_damage_ledger[].miner_damage_fraction": "1",
            "cumulative_miner_damage": "1",
        },
        (
            "Each cycle's work is exact only for its declared full-bandwidth periodic trigonometric interpolant.",
            "Life comes from bounded log-log interpolation on a caller work-life curve matched to the material condition.",
            "Linear Miner accumulation and use of absolute signed net work are explicit caller-reviewed assumptions.",
        ),
        ("caller_periodic_fourier_tensor_work_life_curve_and_miner_bridge",),
        qualification="user_model",
    )]
