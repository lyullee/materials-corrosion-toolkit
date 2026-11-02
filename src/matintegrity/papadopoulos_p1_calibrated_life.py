"""Bounded Papadopoulos P1 parameter-to-life mapping on caller S-N data."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .papadopoulos_p1_finite_integral_screen import (
    PapadopoulosP1FiniteIntegralScreen,
    evaluate_papadopoulos_p1_finite_integral_screen,
)
from .registry import ModelSpec


class PapadopoulosP1CalibratedLife(Contract):
    analysis_id: str = Field(min_length=1)
    p1_request: PapadopoulosP1FiniteIntegralScreen
    life_curve_id: str = Field(min_length=1)
    curve_material_condition_id: str = Field(min_length=1)
    curve_source_id: str = Field(min_length=1)
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_evidence: Evidence
    p1_parameter_points_Pa: list[Positive] = Field(min_length=2, max_length=10000)
    cycles_to_failure: list[Positive] = Field(min_length=2, max_length=10000)
    curve_material_match_and_test_basis_reviewed: bool
    curve_rights_and_engineering_use_reviewed: bool
    log_log_interpolation_and_finite_life_scope_reviewed: bool

    @model_validator(mode="after")
    def validated_curve_and_material(self):
        if self.curve_material_condition_id != self.p1_request.material_condition_id:
            raise ValueError("life-curve material condition must exactly match the P1 history")
        if self.curve_evidence.source_id != self.curve_source_id or self.curve_evidence.sha256 != self.curve_source_sha256:
            raise ValueError("life-curve Evidence must match its declared source and digest")
        if len(self.p1_parameter_points_Pa) != len(self.cycles_to_failure):
            raise ValueError("P1 parameter and life vectors must have equal lengths")
        if any(right <= left for left, right in zip(self.p1_parameter_points_Pa[:-1], self.p1_parameter_points_Pa[1:], strict=True)):
            raise ValueError("P1 parameter curve must be strictly increasing")
        if any(right >= left for left, right in zip(self.cycles_to_failure[:-1], self.cycles_to_failure[1:], strict=True)):
            raise ValueError("cycles to failure must strictly decrease as P1 parameter increases")
        return self


def evaluate_papadopoulos_p1_calibrated_life(request: PapadopoulosP1CalibratedLife) -> Calculation:
    """Map a computed P1 parameter to a caller life curve without extrapolation."""
    curve_payload = {
        "life_curve_id": request.life_curve_id,
        "material_condition_id": request.curve_material_condition_id,
        "source_id": request.curve_source_id,
        "source_sha256": request.curve_source_sha256,
        "p1_parameter_points_Pa": request.p1_parameter_points_Pa,
        "cycles_to_failure": request.cycles_to_failure,
    }
    curve_digest = canonical_digest(curve_payload)
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.curve_material_condition_id,
        "life_curve_id": request.life_curve_id,
        "curve_source_id": request.curve_source_id,
        "curve_source_sha256": request.curve_source_sha256,
        "normalized_curve_sha256": curve_digest,
        "input_sha256": input_digest,
        "p1_parameter_unit": "Pa",
    }
    if not all((
        request.curve_material_match_and_test_basis_reviewed,
        request.curve_rights_and_engineering_use_reviewed,
        request.log_log_interpolation_and_finite_life_scope_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "curve_material_rights_and_interpolation_reviews_required",
            "p1_parameter_Pa": None,
            "cycles_to_failure": None,
        })
    p1 = evaluate_papadopoulos_p1_finite_integral_screen(request.p1_request)
    if p1.status != "computed":
        return Calculation(status=p1.status, values=base | {
            "reason": "underlying_p1_screen_unavailable",
            "underlying_status": p1.status,
            "underlying_values": p1.values,
            "p1_parameter_Pa": None,
            "cycles_to_failure": None,
        })
    parameter = p1.values["criterion_parameter_Pa"]
    base.update({
        "p1_input_sha256": p1.values["input_sha256"],
        "p1_history_source_sha256": p1.values["history_source_sha256"],
        "p1_calibration_sha256": p1.values["calibration_sha256"],
    })
    if not math.isfinite(parameter) or parameter <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "p1_parameter_outside_positive_log_interpolation_support",
            "p1_parameter_Pa": parameter if math.isfinite(parameter) else None,
            "cycles_to_failure": None,
        })
    x = request.p1_parameter_points_Pa
    y = request.cycles_to_failure
    if parameter < x[0] or parameter > x[-1]:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "p1_parameter_outside_caller_curve_support_no_extrapolation",
            "p1_parameter_Pa": parameter,
            "supported_parameter_interval_Pa": [x[0], x[-1]],
            "cycles_to_failure": None,
        })
    exact = next((index for index, value in enumerate(x) if parameter == value), None)
    if exact is not None:
        life = y[exact]
        interval_index = exact
        interpolation_fraction = 0.0
        interpolation = "exact_curve_knot"
    else:
        interval_index = next(index for index in range(len(x) - 1) if x[index] < parameter < x[index + 1])
        fraction = (math.log(parameter) - math.log(x[interval_index])) / (
            math.log(x[interval_index + 1]) - math.log(x[interval_index])
        )
        log_life = math.log(y[interval_index]) + fraction * (
            math.log(y[interval_index + 1]) - math.log(y[interval_index])
        )
        life = math.exp(log_life)
        interpolation_fraction = fraction
        interpolation = "linear_in_log_p1_parameter_and_log_cycles"
    if not math.isfinite(life) or life <= 0.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "interpolated_life_outside_finite_positive_support",
            "p1_parameter_Pa": parameter,
            "cycles_to_failure": None,
        })
    return Calculation(values=base | {
        "status": "computed",
        "p1_parameter_Pa": parameter,
        "weighted_generalized_shear_amplitude_Pa": p1.values["weighted_generalized_shear_amplitude_Pa"],
        "maximum_sampled_hydrostatic_stress_Pa": p1.values["maximum_sampled_hydrostatic_stress_Pa"],
        "cycles_to_failure": life,
        "curve_interval_index": interval_index,
        "interpolation_fraction": interpolation_fraction,
        "interpolation_method": interpolation,
        "curve_support_Pa": [x[0], x[-1]],
        "fatigue_life_semantics": "caller_curve_cycles_to_failure_for_constant_amplitude_equivalent_P1_parameter",
        "limitations": [
            "The life value applies only to the caller's material-matched P1 constant-amplitude parameter curve and declared test basis.",
            "Log-log interpolation is bounded by curve support; no extrapolation, uncertainty, scatter quantile or transfer is estimated.",
            "A variable-amplitude history still needs an explicit cycle decomposition and caller-selected accumulation rule; none is applied here.",
            "The underlying orientation integral remains finite-quadrature approximate and material qualification is external.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.papadopoulos_p1_calibrated_life",
        PapadopoulosP1CalibratedLife,
        evaluate_papadopoulos_p1_calibrated_life,
        {"p1_parameter_Pa": "Pa", "cycles_to_failure": "cycle"},
        (
            "P1 parameter is computed from a separately reviewed finite orientation quadrature and closed sampled stress cycle.",
            "Life is interpolated only within a same-material caller P1 parameter/cycles-to-failure curve using log-log interpolation.",
            "No variable-amplitude cycle counting, damage accumulation, extrapolation or material qualification is implied.",
        ),
        ("caller_papadopoulos_p1_parameter_life_curve_loglog_mapping",),
        qualification="user_model",
    )]
