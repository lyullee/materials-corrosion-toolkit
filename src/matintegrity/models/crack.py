"""Ordered tensile load blocks with bounded, geometry-dependent Paris growth."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class TensileLoadBlock(Contract):
    minimum_stress_Pa: Nonnegative
    maximum_stress_Pa: Nonnegative
    cycles: Positive

    @model_validator(mode="after")
    def ordered(self):
        if self.maximum_stress_Pa < self.minimum_stress_Pa:
            raise ValueError("load-block extrema are reversed")
        return self


class VariableParis(Contract):
    initial_depth_m: Positive
    terminal_depth_m: Positive
    geometry_depth_m: list[Positive] = Field(min_length=2)
    geometry_factor: list[Positive] = Field(min_length=2)
    blocks: list[TensileLoadBlock] = Field(min_length=1)
    coefficient_m_cycle_per_Pa_sqrt_m_power: Positive
    exponent: Positive
    threshold_delta_K_Pa_sqrt_m: Nonnegative
    minimum_calibrated_delta_K_Pa_sqrt_m: Positive
    maximum_calibrated_delta_K_Pa_sqrt_m: Positive
    minimum_calibrated_stress_ratio: float = Field(ge=0, lt=1)
    maximum_calibrated_stress_ratio: float = Field(ge=0, lt=1)
    fracture_toughness_Pa_sqrt_m: Positive
    relative_integration_tolerance: float = Field(gt=0, le=0.01)
    absolute_cycle_tolerance: Positive
    absolute_depth_tolerance_m: Positive

    @model_validator(mode="after")
    def applicability(self):
        if len(self.geometry_depth_m) != len(self.geometry_factor):
            raise ValueError("one geometry factor per depth is required")
        if any(b <= a for a, b in zip(self.geometry_depth_m, self.geometry_depth_m[1:], strict=False)):
            raise ValueError("geometry depths must strictly increase")
        if any(b < a for a, b in zip(self.geometry_factor, self.geometry_factor[1:], strict=False)):
            raise ValueError(
                "this solver requires nondecreasing geometry factors; use a different provider otherwise"
            )
        if (
            not self.geometry_depth_m[0]
            <= self.initial_depth_m
            <= self.terminal_depth_m
            <= self.geometry_depth_m[-1]
        ):
            raise ValueError("the full assessed depth interval must lie inside the supplied geometry table")
        if (
            self.minimum_calibrated_delta_K_Pa_sqrt_m > self.maximum_calibrated_delta_K_Pa_sqrt_m
            or self.minimum_calibrated_stress_ratio > self.maximum_calibrated_stress_ratio
        ):
            raise ValueError("calibration bounds are reversed")
        if self.threshold_delta_K_Pa_sqrt_m > self.maximum_calibrated_delta_K_Pa_sqrt_m:
            raise ValueError("threshold exceeds the supplied growth calibration domain")
        return self


def variable_paris(x: VariableParis) -> Calculation:
    from scipy.integrate import quad
    from scipy.optimize import brentq

    depth = x.initial_depth_m
    total = 0.0
    rows = []
    reason = "requested_blocks_completed"
    status = "computed"

    def geometry(a):
        return float(np.interp(a, x.geometry_depth_m, x.geometry_factor))

    def intensity(a, stress):
        return geometry(a) * stress * math.sqrt(math.pi * a)

    if depth == x.terminal_depth_m:
        reason = "initial_depth_limit_reached"
    else:
        for index, block in enumerate(x.blocks):
            stress_range = block.maximum_stress_Pa - block.minimum_stress_Pa
            initial_k = intensity(depth, block.maximum_stress_Pa)
            if initial_k >= x.fracture_toughness_Pa_sqrt_m:
                reason = "toughness_limit_reached"
                break
            if stress_range == 0:
                total += block.cycles
                rows.append(
                    dict(
                        block_index=index,
                        cycles_used=block.cycles,
                        initial_depth_m=depth,
                        final_depth_m=depth,
                        mode="zero_range",
                    )
                )
                continue
            ratio = block.minimum_stress_Pa / block.maximum_stress_Pa
            delta_k = intensity(depth, stress_range)
            if not x.minimum_calibrated_stress_ratio <= ratio <= x.maximum_calibrated_stress_ratio:
                status = "out_of_scope"
                reason = "stress_ratio_outside_calibration"
                break
            if delta_k <= x.threshold_delta_K_Pa_sqrt_m:
                total += block.cycles
                rows.append(
                    dict(
                        block_index=index,
                        cycles_used=block.cycles,
                        initial_depth_m=depth,
                        final_depth_m=depth,
                        mode="below_declared_threshold",
                    )
                )
                continue
            if (
                not x.minimum_calibrated_delta_K_Pa_sqrt_m
                <= delta_k
                <= x.maximum_calibrated_delta_K_Pa_sqrt_m
            ):
                status = "out_of_scope"
                reason = "delta_K_outside_calibration"
                break
            candidates = [(x.terminal_depth_m, "declared_depth_limit", "computed")]
            for stress, limit, label, ending_status in (
                (
                    block.maximum_stress_Pa,
                    x.fracture_toughness_Pa_sqrt_m,
                    "toughness_limit_reached",
                    "computed",
                ),
                (
                    stress_range,
                    x.maximum_calibrated_delta_K_Pa_sqrt_m,
                    "growth_calibration_limit_reached",
                    "out_of_scope",
                ),
            ):
                if intensity(x.terminal_depth_m, stress) >= limit:
                    terminal = brentq(
                        lambda a, stress_ref=stress, limit_ref=limit: intensity(a, stress_ref) - limit_ref,
                        depth,
                        x.terminal_depth_m,
                        xtol=x.absolute_depth_tolerance_m,
                    )
                    candidates.append((terminal, label, ending_status))
            stop, stop_reason, stop_status = min(candidates, key=lambda item: item[0])

            def cycles_to(a, origin=depth, range_ref=stress_range):
                knots = [origin, *[v for v in x.geometry_depth_m if origin < v < a], a]
                cycles = 0.0
                error = 0.0
                for first, last in zip(knots, knots[1:], strict=False):
                    integral, estimate = quad(
                        lambda size: (
                            1
                            / (
                                x.coefficient_m_cycle_per_Pa_sqrt_m_power
                                * intensity(size, range_ref) ** x.exponent
                            )
                        ),
                        first,
                        last,
                        epsrel=x.relative_integration_tolerance,
                        epsabs=x.absolute_cycle_tolerance,
                        limit=200,
                    )
                    cycles += integral
                    error += estimate
                if error > max(x.absolute_cycle_tolerance, x.relative_integration_tolerance * cycles) * 2:
                    raise RuntimeError("Paris integration did not meet the declared numerical tolerance")
                return cycles, error

            to_stop, error = cycles_to(stop)
            old = depth
            if block.cycles >= to_stop:
                depth = stop
                used = to_stop
                reason = stop_reason
                status = stop_status
            else:
                depth = brentq(
                    lambda a, target=block.cycles: cycles_to(a)[0] - target,
                    depth,
                    stop,
                    xtol=x.absolute_depth_tolerance_m,
                )
                used = block.cycles
            total += used
            checked_cycles, actual_error = cycles_to(depth)
            if abs(checked_cycles - used) > 2 * max(
                x.absolute_cycle_tolerance, x.relative_integration_tolerance * used
            ):
                raise RuntimeError(
                    "Depth root resolution does not satisfy the cycle tolerance; tighten absolute_depth_tolerance_m"
                )
            rows.append(
                dict(
                    block_index=index,
                    cycles_used=used,
                    initial_depth_m=old,
                    final_depth_m=depth,
                    terminal_delta_K_Pa_sqrt_m=intensity(depth, stress_range),
                    terminal_maximum_K_Pa_sqrt_m=intensity(depth, block.maximum_stress_Pa),
                    integration_error_estimate_cycles=actual_error,
                    cycle_inversion_residual=checked_cycles - used,
                    mode="Paris_growth",
                )
            )
            if reason != "requested_blocks_completed":
                break
    return Calculation(
        status=status,
        values=dict(
            final_depth_m=depth,
            cycles_evaluated=total,
            requested_cycles=sum(block.cycles for block in x.blocks),
            termination_reason=reason,
            block_results=rows,
        ),
        notes=(
            "Piecewise-linear nondecreasing supplied geometry, tensile load blocks and a thresholded Paris-region law; no geometry extrapolation.",
            "Maximum K and declared depth limit terminate assessment separately from growth-calibration limits. No initiation, closure, retardation, plastic collapse, residual stress or environmental coefficient is inferred.",
            "Threshold inactivity suppresses only this Paris contribution, not all possible crack or material damage. Fractional cycles represent continuous-law interpolation, not measured cycle resolution.",
        ),
    )


class TabulatedCrackGrowthCurve(Contract):
    """Caller-controlled crack-growth curve with explicit provenance and support."""

    schema_version: Literal["matintegrity.tabulated_crack_growth_curve.v1"] = (
        "matintegrity.tabulated_crack_growth_curve.v1"
    )
    curve_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    stress_ratio: float = Field(ge=0, lt=1)
    frequency_Hz: Positive | None
    delta_k_Pa_sqrt_m: list[Positive] = Field(min_length=2)
    crack_growth_m_cycle: list[Positive] = Field(min_length=2)
    interpolation: Literal["log_delta_k_log_growth_linear"] = "log_delta_k_log_growth_linear"
    below_minimum_policy: Literal["out_of_scope", "zero_below_declared_threshold"]
    declared_threshold_delta_k_Pa_sqrt_m: Nonnegative | None = None
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_citation: str | None = None
    license_id: str | None = None
    rights_review_id: str | None = None
    applicability_review_id: str | None = None
    pointwise_computational_use_authorized: Literal[True]
    curve_applicability_reviewed: Literal[True]
    physical_specimen_identity_status: Literal["identified", "not_required_for_user_model", "not_established"]

    @model_validator(mode="after")
    def curve_support(self):
        if len(self.delta_k_Pa_sqrt_m) != len(self.crack_growth_m_cycle):
            raise ValueError("one crack-growth rate per delta-K point is required")
        if any(
            right <= left
            for left, right in zip(self.delta_k_Pa_sqrt_m, self.delta_k_Pa_sqrt_m[1:], strict=False)
        ):
            raise ValueError("tabulated delta-K points must strictly increase")
        if self.below_minimum_policy == "zero_below_declared_threshold":
            if self.declared_threshold_delta_k_Pa_sqrt_m is None:
                raise ValueError("zero-growth policy requires a caller-declared threshold")
            if self.declared_threshold_delta_k_Pa_sqrt_m > self.delta_k_Pa_sqrt_m[0]:
                raise ValueError("declared threshold must not exceed the first tabulated delta-K")
        elif self.declared_threshold_delta_k_Pa_sqrt_m is not None:
            raise ValueError("a threshold is only valid with the declared zero-growth policy")
        return self


def _tabulated_growth_rate(curve: TabulatedCrackGrowthCurve, delta_k: float) -> tuple[float, int]:
    lower = curve.delta_k_Pa_sqrt_m[0]
    upper = curve.delta_k_Pa_sqrt_m[-1]
    if delta_k < lower or delta_k > upper:
        raise ValueError("delta K lies outside the tabulated crack-growth support")
    index = int(np.searchsorted(curve.delta_k_Pa_sqrt_m, delta_k, side="right") - 1)
    index = min(max(index, 0), len(curve.delta_k_Pa_sqrt_m) - 2)
    x0, x1 = curve.delta_k_Pa_sqrt_m[index : index + 2]
    y0, y1 = curve.crack_growth_m_cycle[index : index + 2]
    fraction = math.log(delta_k / x0) / math.log(x1 / x0)
    return math.exp(math.log(y0) + fraction * math.log(y1 / y0)), index


class TabulatedGrowthRateQuery(Contract):
    curve: TabulatedCrackGrowthCurve
    query_delta_k_Pa_sqrt_m: list[Positive] = Field(min_length=1)


def tabulated_growth_rate(x: TabulatedGrowthRateQuery) -> Calculation:
    rows = []
    outside = False
    lower, upper = x.curve.delta_k_Pa_sqrt_m[0], x.curve.delta_k_Pa_sqrt_m[-1]
    for delta_k in x.query_delta_k_Pa_sqrt_m:
        if not lower <= delta_k <= upper:
            outside = True
            rows.append(
                {
                    "delta_k_Pa_sqrt_m": delta_k,
                    "crack_growth_m_cycle": None,
                    "interpolation_segment_index": None,
                    "within_curve_support": False,
                }
            )
            continue
        rate, segment = _tabulated_growth_rate(x.curve, delta_k)
        rows.append(
            {
                "delta_k_Pa_sqrt_m": delta_k,
                "crack_growth_m_cycle": rate,
                "interpolation_segment_index": segment,
                "within_curve_support": True,
            }
        )
    return Calculation(
        status="out_of_scope" if outside else "computed",
        values={"curve_id": x.curve.curve_id, "query_results": rows},
        notes=(
            "Interpolation is linear in log(delta K)-log(da/dN) coordinates and never extrapolates.",
            "A caller-authorized curve remains a user model; interpolation does not qualify its material, environment, specimen independence or service applicability.",
        ),
    )


class TabulatedGrowthLoadBlock(Contract):
    minimum_stress_Pa: Nonnegative
    maximum_stress_Pa: Positive
    cycles: Positive
    frequency_Hz: Positive

    @model_validator(mode="after")
    def ordered(self):
        if self.maximum_stress_Pa < self.minimum_stress_Pa:
            raise ValueError("load-block extrema are reversed")
        return self


class TabulatedCrackGrowth(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth.v1"] = (
        "matintegrity.tabulated_crack_growth.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    initial_depth_m: Positive
    terminal_depth_m: Positive
    geometry_depth_m: list[Positive] = Field(min_length=2)
    geometry_factor: list[Positive] = Field(min_length=2)
    blocks: list[TabulatedGrowthLoadBlock] = Field(min_length=1)
    curve: TabulatedCrackGrowthCurve
    material_condition_id: str | None = None
    environment_id: str | None = None
    curve_material_environment_mapping_reviewed: bool = False
    maximum_absolute_stress_ratio_difference: Nonnegative
    maximum_relative_frequency_difference: Nonnegative
    fracture_toughness_Pa_sqrt_m: Positive
    relative_integration_tolerance: float = Field(gt=0, le=0.01)
    absolute_cycle_tolerance: Positive
    absolute_depth_tolerance_m: Positive
    geometry_solution_reviewed: Literal[True]
    load_to_curve_mapping_reviewed: Literal[True]
    toughness_application_reviewed: Literal[True]

    @model_validator(mode="after")
    def applicability(self):
        if len(self.geometry_depth_m) != len(self.geometry_factor):
            raise ValueError("one geometry factor per depth is required")
        if any(
            right <= left
            for left, right in zip(self.geometry_depth_m, self.geometry_depth_m[1:], strict=False)
        ):
            raise ValueError("geometry depths must strictly increase")
        if any(
            right < left for left, right in zip(self.geometry_factor, self.geometry_factor[1:], strict=False)
        ):
            raise ValueError("tabulated growth integration requires nondecreasing geometry factors")
        if not (
            self.geometry_depth_m[0]
            <= self.initial_depth_m
            <= self.terminal_depth_m
            <= self.geometry_depth_m[-1]
        ):
            raise ValueError("the assessed depth interval must lie inside the geometry table")
        return self


def tabulated_crack_growth(x: TabulatedCrackGrowth) -> Calculation:
    """Integrate a caller-supplied da/dN curve over ordered tensile load blocks."""
    base_values = {
        "assessment_id": x.assessment_id,
        "curve_id": x.curve.curve_id,
        "final_depth_m": x.initial_depth_m,
        "cycles_evaluated": 0.0,
        "requested_cycles": sum(block.cycles for block in x.blocks),
        "termination_reason": "material_environment_mapping_not_reviewed",
        "block_results": [],
    }
    if not (
        x.curve_material_environment_mapping_reviewed
        and x.material_condition_id
        and x.environment_id
    ):
        return Calculation(
            status="needs_data",
            values=base_values,
            notes=("Explicit target material condition and environment must be mapped to the curve before life integration.",),
        )
    if (
        x.material_condition_id != x.curve.material_condition_id
        or x.environment_id != x.curve.environment_id
    ):
        return Calculation(
            status="out_of_scope",
            values=base_values | {"termination_reason": "curve_material_environment_mismatch"},
            notes=("The tabulated curve material condition and environment do not match the declared assessment target.",),
        )
    from scipy.integrate import quad
    from scipy.optimize import brentq

    depth = x.initial_depth_m
    cycles_evaluated = 0.0
    block_results = []
    reason = "requested_blocks_completed"
    status = "computed"

    def geometry(a: float) -> float:
        return float(np.interp(a, x.geometry_depth_m, x.geometry_factor))

    def intensity(a: float, stress: float) -> float:
        return geometry(a) * stress * math.sqrt(math.pi * a)

    def first_depth_for_delta_k(origin: float, limit: float, stress_range: float) -> float | None:
        if intensity(origin, stress_range) >= limit:
            return origin
        if intensity(x.terminal_depth_m, stress_range) < limit:
            return None
        return float(
            brentq(
                lambda a: intensity(a, stress_range) - limit,
                origin,
                x.terminal_depth_m,
                xtol=x.absolute_depth_tolerance_m,
            )
        )

    if depth == x.terminal_depth_m:
        reason = "initial_depth_limit_reached"
    else:
        for index, block in enumerate(x.blocks):
            initial_depth = depth
            stress_range = block.maximum_stress_Pa - block.minimum_stress_Pa
            maximum_k = intensity(depth, block.maximum_stress_Pa)
            if maximum_k >= x.fracture_toughness_Pa_sqrt_m:
                reason = "toughness_limit_reached"
                break
            if stress_range == 0:
                cycles_evaluated += block.cycles
                block_results.append(
                    {
                        "block_index": index,
                        "cycles_used": block.cycles,
                        "initial_depth_m": depth,
                        "final_depth_m": depth,
                        "mode": "zero_range",
                    }
                )
                continue
            ratio = block.minimum_stress_Pa / block.maximum_stress_Pa
            if abs(ratio - x.curve.stress_ratio) > x.maximum_absolute_stress_ratio_difference:
                status, reason = "out_of_scope", "stress_ratio_outside_curve_mapping"
                break
            if x.curve.frequency_Hz is None:
                status, reason = "out_of_scope", "curve_frequency_unreported_cannot_map_load_block"
                break
            relative_frequency_difference = abs(block.frequency_Hz / x.curve.frequency_Hz - 1.0)
            if relative_frequency_difference > x.maximum_relative_frequency_difference:
                status, reason = "out_of_scope", "frequency_outside_curve_mapping"
                break

            initial_delta_k = intensity(depth, stress_range)
            curve_minimum = x.curve.delta_k_Pa_sqrt_m[0]
            curve_maximum = x.curve.delta_k_Pa_sqrt_m[-1]
            if initial_delta_k < curve_minimum:
                threshold = x.curve.declared_threshold_delta_k_Pa_sqrt_m
                if (
                    x.curve.below_minimum_policy == "zero_below_declared_threshold"
                    and threshold is not None
                    and initial_delta_k <= threshold
                ):
                    cycles_evaluated += block.cycles
                    block_results.append(
                        {
                            "block_index": index,
                            "cycles_used": block.cycles,
                            "initial_depth_m": depth,
                            "final_depth_m": depth,
                            "initial_delta_K_Pa_sqrt_m": initial_delta_k,
                            "mode": "below_declared_threshold",
                        }
                    )
                    continue
                status, reason = "out_of_scope", "delta_K_below_curve_support"
                break
            if initial_delta_k > curve_maximum:
                status, reason = "out_of_scope", "delta_K_above_curve_support"
                break

            candidates = [(x.terminal_depth_m, "declared_depth_limit", "computed")]
            toughness_depth = first_depth_for_delta_k(
                depth, x.fracture_toughness_Pa_sqrt_m, block.maximum_stress_Pa
            )
            if toughness_depth is not None:
                candidates.append((toughness_depth, "toughness_limit_reached", "computed"))
            curve_limit_depth = first_depth_for_delta_k(depth, curve_maximum, stress_range)
            if curve_limit_depth is not None:
                candidates.append((curve_limit_depth, "growth_curve_upper_bound_reached", "out_of_scope"))
            stop, stop_reason, stop_status = min(candidates, key=lambda item: item[0])
            integration_origin = depth
            integration_stress_range = stress_range
            requested_block_cycles = block.cycles

            def cycles_to(
                target_depth: float,
                origin: float = integration_origin,
                range_ref: float = integration_stress_range,
            ) -> tuple[float, float]:
                knots = {origin, target_depth}
                knots.update(value for value in x.geometry_depth_m if origin < value < target_depth)
                for delta_k_knot in x.curve.delta_k_Pa_sqrt_m[1:-1]:
                    crossing = first_depth_for_delta_k(origin, delta_k_knot, range_ref)
                    if crossing is not None and origin < crossing < target_depth:
                        knots.add(crossing)
                ordered_knots = sorted(knots)
                total_cycles = 0.0
                total_error = 0.0
                for first, last in zip(ordered_knots, ordered_knots[1:], strict=False):
                    integral, error = quad(
                        lambda size: 1.0 / _tabulated_growth_rate(x.curve, intensity(size, range_ref))[0],
                        first,
                        last,
                        epsrel=x.relative_integration_tolerance,
                        epsabs=x.absolute_cycle_tolerance,
                        limit=200,
                    )
                    total_cycles += integral
                    total_error += error
                if total_error > 2 * max(
                    x.absolute_cycle_tolerance,
                    x.relative_integration_tolerance * total_cycles,
                ):
                    raise RuntimeError("tabulated growth integration missed the declared tolerance")
                return total_cycles, total_error

            cycles_to_stop, _ = cycles_to(stop)
            if block.cycles >= cycles_to_stop:
                depth = stop
                cycles_used = cycles_to_stop
                reason, status = stop_reason, stop_status
            else:
                depth = float(
                    brentq(
                        lambda a, target=requested_block_cycles: cycles_to(a)[0] - target,
                        depth,
                        stop,
                        xtol=x.absolute_depth_tolerance_m,
                    )
                )
                cycles_used = block.cycles
            cycles_evaluated += cycles_used
            checked_cycles, integration_error = cycles_to(depth)
            if abs(checked_cycles - cycles_used) > 2 * max(
                x.absolute_cycle_tolerance,
                x.relative_integration_tolerance * cycles_used,
            ):
                raise RuntimeError(
                    "depth root resolution does not satisfy the cycle tolerance; tighten absolute_depth_tolerance_m"
                )
            terminal_delta_k = intensity(depth, stress_range)
            terminal_growth_rate, _ = _tabulated_growth_rate(x.curve, terminal_delta_k)
            block_results.append(
                {
                    "block_index": index,
                    "cycles_used": cycles_used,
                    "initial_depth_m": initial_depth,
                    "final_depth_m": depth,
                    "initial_delta_K_Pa_sqrt_m": initial_delta_k,
                    "terminal_delta_K_Pa_sqrt_m": terminal_delta_k,
                    "terminal_maximum_K_Pa_sqrt_m": intensity(depth, block.maximum_stress_Pa),
                    "terminal_growth_m_cycle": terminal_growth_rate,
                    "integration_error_estimate_cycles": integration_error,
                    "cycle_inversion_residual": checked_cycles - cycles_used,
                    "mode": "tabulated_curve_growth",
                }
            )
            if reason != "requested_blocks_completed":
                break

    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "curve_id": x.curve.curve_id,
            "final_depth_m": depth,
            "cycles_evaluated": cycles_evaluated,
            "requested_cycles": sum(block.cycles for block in x.blocks),
            "termination_reason": reason,
            "block_results": block_results,
        },
        notes=(
            "The supplied curve is interpolated only inside its delta-K support in log-log coordinates; no environmental, threshold or upper-range extrapolation is inferred.",
            "Ordered tensile blocks must match the curve stress ratio and frequency within caller-declared tolerances. Geometry factors are linearly interpolated without extrapolation.",
            "Maximum K, curve support and declared depth terminate separately. No initiation, closure, retardation, overload interaction, plasticity, residual stress, probability or code acceptance is modelled.",
        ),
    )


class TabulatedCrackGrowthCurveFamily(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth_curve_family.v1"] = (
        "matintegrity.tabulated_crack_growth_curve_family.v1"
    )
    family_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    curves: list[TabulatedCrackGrowthCurve] = Field(min_length=2)
    maximum_absolute_stress_ratio_difference: Nonnegative
    maximum_relative_frequency_difference: Nonnegative
    selection_policy: Literal["nearest_within_declared_tolerances"] = "nearest_within_declared_tolerances"
    family_applicability_reviewed: Literal[True]

    @model_validator(mode="after")
    def aligned_family(self):
        curve_ids = [curve.curve_id for curve in self.curves]
        if len(set(curve_ids)) != len(curve_ids):
            raise ValueError("curve IDs must be unique inside one family")
        conditions = [(curve.stress_ratio, curve.frequency_Hz) for curve in self.curves]
        if len(set(conditions)) != len(conditions):
            raise ValueError("stress-ratio/frequency conditions must be unique inside one family")
        if any(curve.material_condition_id != self.material_condition_id for curve in self.curves):
            raise ValueError("every family curve must use the declared material condition")
        if any(curve.environment_id != self.environment_id for curve in self.curves):
            raise ValueError("every family curve must use the declared environment")
        return self


def _select_family_curve(
    family: TabulatedCrackGrowthCurveFamily,
    block: TabulatedGrowthLoadBlock,
) -> tuple[TabulatedCrackGrowthCurve | None, dict, str | None]:
    stress_ratio = block.minimum_stress_Pa / block.maximum_stress_Pa
    candidates = []
    diagnostics = []
    for curve in family.curves:
        ratio_difference = abs(stress_ratio - curve.stress_ratio)
        frequency_difference = (
            None if curve.frequency_Hz is None else abs(block.frequency_Hz / curve.frequency_Hz - 1.0)
        )
        within = (
            ratio_difference <= family.maximum_absolute_stress_ratio_difference
            and frequency_difference is not None
            and frequency_difference <= family.maximum_relative_frequency_difference
        )
        ratio_scale = family.maximum_absolute_stress_ratio_difference
        frequency_scale = family.maximum_relative_frequency_difference
        ratio_component = (
            0.0
            if ratio_scale == 0 and ratio_difference == 0
            else ratio_difference / ratio_scale
            if ratio_scale > 0
            else math.inf
        )
        frequency_component = (
            0.0
            if frequency_difference is not None and frequency_scale == 0 and frequency_difference == 0
            else frequency_difference / frequency_scale
            if frequency_difference is not None and frequency_scale > 0
            else math.inf
        )
        score = math.hypot(ratio_component, frequency_component)
        diagnostics.append(
            {
                "curve_id": curve.curve_id,
                "absolute_stress_ratio_difference": ratio_difference,
                "relative_frequency_difference": frequency_difference,
                "within_declared_tolerances": within,
                "normalized_selection_distance": score if math.isfinite(score) else None,
            }
        )
        if within:
            candidates.append((score, curve))
    summary = {
        "block_stress_ratio": stress_ratio,
        "block_frequency_Hz": block.frequency_Hz,
        "candidate_diagnostics": diagnostics,
    }
    if not candidates:
        return None, summary, "no_curve_within_mapping_tolerances"
    candidates.sort(key=lambda item: (item[0], item[1].curve_id))
    if len(candidates) > 1 and math.isclose(candidates[0][0], candidates[1][0], rel_tol=1e-12, abs_tol=1e-15):
        summary["tied_curve_ids"] = [
            curve.curve_id
            for score, curve in candidates
            if math.isclose(score, candidates[0][0], rel_tol=1e-12, abs_tol=1e-15)
        ]
        return None, summary, "ambiguous_curve_mapping"
    selected = candidates[0][1]
    summary["selected_curve_id"] = selected.curve_id
    summary["selected_normalized_distance"] = candidates[0][0]
    return selected, summary, None


class TabulatedCurveFamilyGrowth(Contract):
    schema_version: Literal["matintegrity.tabulated_curve_family_growth.v1"] = (
        "matintegrity.tabulated_curve_family_growth.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    initial_depth_m: Positive
    terminal_depth_m: Positive
    geometry_depth_m: list[Positive] = Field(min_length=2)
    geometry_factor: list[Positive] = Field(min_length=2)
    blocks: list[TabulatedGrowthLoadBlock] = Field(min_length=1)
    curve_family: TabulatedCrackGrowthCurveFamily
    material_condition_id: str | None = None
    environment_id: str | None = None
    curve_family_material_environment_mapping_reviewed: bool = False
    fracture_toughness_Pa_sqrt_m: Positive
    relative_integration_tolerance: float = Field(gt=0, le=0.01)
    absolute_cycle_tolerance: Positive
    absolute_depth_tolerance_m: Positive
    geometry_solution_reviewed: Literal[True]
    load_to_curve_mapping_reviewed: Literal[True]
    toughness_application_reviewed: Literal[True]

    @model_validator(mode="after")
    def geometry_support(self):
        if len(self.geometry_depth_m) != len(self.geometry_factor):
            raise ValueError("one geometry factor per depth is required")
        if any(
            right <= left
            for left, right in zip(self.geometry_depth_m, self.geometry_depth_m[1:], strict=False)
        ):
            raise ValueError("geometry depths must strictly increase")
        if any(
            right < left for left, right in zip(self.geometry_factor, self.geometry_factor[1:], strict=False)
        ):
            raise ValueError("tabulated growth integration requires nondecreasing geometry factors")
        if not (
            self.geometry_depth_m[0]
            <= self.initial_depth_m
            <= self.terminal_depth_m
            <= self.geometry_depth_m[-1]
        ):
            raise ValueError("the assessed depth interval must lie inside the geometry table")
        return self


def tabulated_curve_family_growth(x: TabulatedCurveFamilyGrowth) -> Calculation:
    """Select one reviewed curve per block without interpolating between test conditions."""
    depth = x.initial_depth_m
    cycles_evaluated = 0.0
    block_results = []
    selection_results = []
    selected_curve_ids = []
    status = "computed"
    reason = "initial_depth_limit_reached" if depth == x.terminal_depth_m else ("requested_blocks_completed")
    if not (
        x.curve_family_material_environment_mapping_reviewed
        and x.material_condition_id
        and x.environment_id
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "curve_family_id": x.curve_family.family_id,
                "final_depth_m": depth,
                "cycles_evaluated": 0.0,
                "requested_cycles": sum(block.cycles for block in x.blocks),
                "termination_reason": "material_environment_mapping_not_reviewed",
                "selected_curve_ids": [],
                "curve_selection_results": [],
                "block_results": [],
            },
            notes=("Explicit target material condition and environment must be mapped to the curve family before life integration.",),
        )
    if (
        x.material_condition_id != x.curve_family.material_condition_id
        or x.environment_id != x.curve_family.environment_id
    ):
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "curve_family_id": x.curve_family.family_id,
                "final_depth_m": depth,
                "cycles_evaluated": 0.0,
                "requested_cycles": sum(block.cycles for block in x.blocks),
                "termination_reason": "curve_family_material_environment_mismatch",
                "selected_curve_ids": [],
                "curve_selection_results": [],
                "block_results": [],
            },
            notes=("The curve-family material condition and environment do not match the declared assessment target.",),
        )
    if depth < x.terminal_depth_m:
        for block_index, block in enumerate(x.blocks):
            selected, selection, selection_failure = _select_family_curve(x.curve_family, block)
            selection["block_index"] = block_index
            selection_results.append(selection)
            if selection_failure is not None:
                status = "out_of_scope"
                reason = selection_failure
                break
            selected_curve_ids.append(selected.curve_id)
            single = TabulatedCrackGrowth(
                assessment_id=x.assessment_id,
                physical_scope_id=x.physical_scope_id,
                initial_depth_m=depth,
                terminal_depth_m=x.terminal_depth_m,
                geometry_depth_m=x.geometry_depth_m,
                geometry_factor=x.geometry_factor,
                blocks=[block],
                curve=selected,
                material_condition_id=x.material_condition_id,
                environment_id=x.environment_id,
                curve_material_environment_mapping_reviewed=True,
                maximum_absolute_stress_ratio_difference=(
                    x.curve_family.maximum_absolute_stress_ratio_difference
                ),
                maximum_relative_frequency_difference=(x.curve_family.maximum_relative_frequency_difference),
                fracture_toughness_Pa_sqrt_m=x.fracture_toughness_Pa_sqrt_m,
                relative_integration_tolerance=x.relative_integration_tolerance,
                absolute_cycle_tolerance=x.absolute_cycle_tolerance,
                absolute_depth_tolerance_m=x.absolute_depth_tolerance_m,
                geometry_solution_reviewed=True,
                load_to_curve_mapping_reviewed=True,
                toughness_application_reviewed=True,
            )
            result = tabulated_crack_growth(single)
            depth = result.values["final_depth_m"]
            cycles_evaluated += result.values["cycles_evaluated"]
            for row in result.values["block_results"]:
                block_results.append(
                    {
                        **row,
                        "block_index": block_index,
                        "selected_curve_id": selected.curve_id,
                    }
                )
            if result.values["termination_reason"] != "requested_blocks_completed":
                status = result.status
                reason = result.values["termination_reason"]
                break
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "curve_family_id": x.curve_family.family_id,
            "final_depth_m": depth,
            "cycles_evaluated": cycles_evaluated,
            "requested_cycles": sum(block.cycles for block in x.blocks),
            "termination_reason": reason,
            "selected_curve_ids": selected_curve_ids,
            "curve_selection_results": selection_results,
            "block_results": block_results,
        },
        notes=(
            "Each tensile block selects one nearest curve inside explicit stress-ratio and relative-frequency tolerances; equal-distance candidates stop as ambiguous.",
            "No interpolation, averaging or fitting across stress ratio, frequency, environment, material condition or source group is performed.",
            "Each selected curve retains the single-curve integration limits; family selection does not qualify closure, retardation, overload interaction, plasticity, residual stress, acceptance, probability or service life.",
        ),
    )


class CrackGrowthUncertaintySample(Contract):
    sample_id: str = Field(min_length=1)
    normalized_weight: float = Field(gt=0, le=1)
    crack_growth_rate_multiplier: Positive
    geometry_factor_multiplier: Positive
    stress_multiplier: Positive
    fracture_toughness_multiplier: Positive


class TabulatedCrackGrowthUncertainty(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth_uncertainty.v1"] = (
        "matintegrity.tabulated_crack_growth_uncertainty.v1"
    )
    uncertainty_run_id: str = Field(min_length=1)
    distribution_definition_id: str = Field(min_length=1)
    sample_design_id: str = Field(min_length=1)
    joint_sample_source_id: str = Field(min_length=1)
    joint_sample_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    base_growth: TabulatedCrackGrowth | TabulatedCurveFamilyGrowth = Field(discriminator="schema_version")
    samples: list[CrackGrowthUncertaintySample] = Field(min_length=2)
    requested_quantiles: list[float] = Field(min_length=1)
    depth_exceedance_threshold_m: Positive
    maximum_weight_sum_error: float = Field(gt=0, le=1e-6)
    joint_sample_values_reviewed: Literal[True]
    dependence_preserved_in_joint_rows: Literal[True]
    normalized_weight_meaning_reviewed: Literal[True]
    base_model_and_multiplier_scope_reviewed: Literal[True]

    @model_validator(mode="after")
    def uncertainty_design(self):
        sample_ids = [sample.sample_id for sample in self.samples]
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError("uncertainty sample IDs must be unique")
        weight_sum = sum(sample.normalized_weight for sample in self.samples)
        if abs(weight_sum - 1.0) > self.maximum_weight_sum_error:
            raise ValueError("uncertainty sample weights must sum to one within the declared tolerance")
        if any(not 0 < quantile < 1 for quantile in self.requested_quantiles):
            raise ValueError("requested uncertainty quantiles must lie strictly between zero and one")
        if any(
            right <= left
            for left, right in zip(self.requested_quantiles, self.requested_quantiles[1:], strict=False)
        ):
            raise ValueError("requested uncertainty quantiles must strictly increase")
        return self


def _scaled_single_growth(
    base: TabulatedCrackGrowth,
    sample: CrackGrowthUncertaintySample,
) -> TabulatedCrackGrowth:
    payload = base.model_dump(mode="json")
    payload["curve"]["crack_growth_m_cycle"] = [
        value * sample.crack_growth_rate_multiplier for value in payload["curve"]["crack_growth_m_cycle"]
    ]
    payload["geometry_factor"] = [
        value * sample.geometry_factor_multiplier for value in payload["geometry_factor"]
    ]
    for block in payload["blocks"]:
        block["minimum_stress_Pa"] *= sample.stress_multiplier
        block["maximum_stress_Pa"] *= sample.stress_multiplier
    payload["fracture_toughness_Pa_sqrt_m"] *= sample.fracture_toughness_multiplier
    return TabulatedCrackGrowth.model_validate(payload)


def _scaled_family_growth(
    base: TabulatedCurveFamilyGrowth,
    sample: CrackGrowthUncertaintySample,
) -> TabulatedCurveFamilyGrowth:
    payload = base.model_dump(mode="json")
    for curve in payload["curve_family"]["curves"]:
        curve["crack_growth_m_cycle"] = [
            value * sample.crack_growth_rate_multiplier for value in curve["crack_growth_m_cycle"]
        ]
    payload["geometry_factor"] = [
        value * sample.geometry_factor_multiplier for value in payload["geometry_factor"]
    ]
    for block in payload["blocks"]:
        block["minimum_stress_Pa"] *= sample.stress_multiplier
        block["maximum_stress_Pa"] *= sample.stress_multiplier
    payload["fracture_toughness_Pa_sqrt_m"] *= sample.fracture_toughness_multiplier
    return TabulatedCurveFamilyGrowth.model_validate(payload)


def _weighted_inverse_cdf(rows: list[tuple[float, float]], quantile: float) -> float:
    cumulative = 0.0
    for value, weight in sorted(rows, key=lambda item: item[0]):
        cumulative += weight
        if cumulative >= quantile:
            return value
    return max(value for value, _ in rows)


def tabulated_crack_growth_uncertainty(x: TabulatedCrackGrowthUncertainty) -> Calculation:
    """Propagate caller-supplied joint weighted multipliers without generating samples."""
    sample_results = []
    complete_rows = []
    status_counts = {"computed": 0, "out_of_scope": 0, "needs_data": 0}
    for sample in x.samples:
        if isinstance(x.base_growth, TabulatedCrackGrowth):
            result = tabulated_crack_growth(_scaled_single_growth(x.base_growth, sample))
        else:
            result = tabulated_curve_family_growth(_scaled_family_growth(x.base_growth, sample))
        status_counts[result.status] += 1
        row = {
            "sample_id": sample.sample_id,
            "normalized_weight": sample.normalized_weight,
            "crack_growth_rate_multiplier": sample.crack_growth_rate_multiplier,
            "geometry_factor_multiplier": sample.geometry_factor_multiplier,
            "stress_multiplier": sample.stress_multiplier,
            "fracture_toughness_multiplier": sample.fracture_toughness_multiplier,
            "status": result.status,
            "final_depth_m": result.values["final_depth_m"],
            "cycles_evaluated": result.values["cycles_evaluated"],
            "termination_reason": result.values["termination_reason"],
        }
        sample_results.append(row)
        if result.status == "computed":
            complete_rows.append((result.values["final_depth_m"], sample.normalized_weight))

    all_computed = status_counts["computed"] == len(x.samples)
    values = {
        "uncertainty_run_id": x.uncertainty_run_id,
        "distribution_definition_id": x.distribution_definition_id,
        "sample_design_id": x.sample_design_id,
        "sample_count": len(x.samples),
        "weight_sum": sum(sample.normalized_weight for sample in x.samples),
        "status_counts": status_counts,
        "all_samples_computed": all_computed,
        "sample_results": sample_results,
        "weighted_mean_final_depth_m": None,
        "weighted_standard_deviation_final_depth_m": None,
        "weighted_quantiles": None,
        "depth_exceedance_threshold_m": x.depth_exceedance_threshold_m,
        "model_implied_depth_exceedance_probability": None,
    }
    if all_computed:
        mean = sum(value * weight for value, weight in complete_rows)
        variance = sum(weight * (value - mean) ** 2 for value, weight in complete_rows)
        values.update(
            {
                "weighted_mean_final_depth_m": mean,
                "weighted_standard_deviation_final_depth_m": math.sqrt(max(variance, 0.0)),
                "weighted_quantiles": [
                    {
                        "cumulative_probability": quantile,
                        "final_depth_m": _weighted_inverse_cdf(complete_rows, quantile),
                    }
                    for quantile in x.requested_quantiles
                ],
                "model_implied_depth_exceedance_probability": sum(
                    weight for value, weight in complete_rows if value >= x.depth_exceedance_threshold_m
                ),
            }
        )
    return Calculation(
        status="computed" if all_computed else "out_of_scope",
        values=values,
        notes=(
            "Joint caller-supplied rows preserve dependence among global crack-growth-rate, geometry-factor, stress and toughness multipliers; this calculator does not generate, fit, normalize or resample them.",
            "If any sample is outside the deterministic model scope, every row is retained and aggregate moments, quantiles and exceedance probability are withheld rather than conditioning on successful samples.",
            "The reported exceedance is the discrete push-forward of the declared input-uncertainty mass. It is not a period first-failure probability, observed frequency, FTA basic-event probability, model-form uncertainty, confidence bound or code acceptance result.",
        ),
    )


class CrackGrowthScenario(Contract):
    schema_version: Literal["matintegrity.crack_growth_scenario.v1"] = "matintegrity.crack_growth_scenario.v1"
    scenario_id: str = Field(min_length=1)
    normalized_weight: Positive
    joint_scenario_source_id: str = Field(min_length=1)
    joint_scenario_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    growth: TabulatedCrackGrowth | TabulatedCurveFamilyGrowth = Field(discriminator="schema_version")


class TabulatedCrackGrowthScenarioEnsemble(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth_scenario_ensemble.v1"] = (
        "matintegrity.tabulated_crack_growth_scenario_ensemble.v1"
    )
    ensemble_run_id: str = Field(min_length=1)
    distribution_definition_id: str = Field(min_length=1)
    sample_design_id: str = Field(min_length=1)
    scenarios: list[CrackGrowthScenario] = Field(min_length=2)
    requested_quantiles: list[float] = Field(min_length=1)
    depth_exceedance_threshold_m: Positive
    maximum_weight_sum_error: float = Field(gt=0, le=1e-6)
    full_scenario_inputs_reviewed: Literal[True]
    dependence_preserved_inside_scenarios: Literal[True]
    normalized_weight_meaning_reviewed: Literal[True]
    common_physical_scope_reviewed: Literal[True]

    @model_validator(mode="after")
    def scenario_design(self):
        scenario_ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("crack-growth scenario IDs must be unique")
        weight_sum = sum(scenario.normalized_weight for scenario in self.scenarios)
        if abs(weight_sum - 1.0) > self.maximum_weight_sum_error:
            raise ValueError("crack-growth scenario weights must sum to one")
        if any(not 0 < quantile < 1 for quantile in self.requested_quantiles):
            raise ValueError("requested scenario quantiles must lie strictly between zero and one")
        if any(
            right <= left
            for left, right in zip(self.requested_quantiles, self.requested_quantiles[1:], strict=False)
        ):
            raise ValueError("requested scenario quantiles must strictly increase")
        scopes = {scenario.growth.physical_scope_id for scenario in self.scenarios}
        if len(scopes) != 1:
            raise ValueError("all crack-growth scenarios must share one physical scope")
        return self


def tabulated_crack_growth_scenario_ensemble(
    x: TabulatedCrackGrowthScenarioEnsemble,
) -> Calculation:
    """Push complete caller-supplied crack-growth scenarios through deterministic models."""
    scenario_results = []
    complete_rows = []
    status_counts = {"computed": 0, "out_of_scope": 0, "needs_data": 0}
    for scenario in x.scenarios:
        if isinstance(scenario.growth, TabulatedCrackGrowth):
            result = tabulated_crack_growth(scenario.growth)
            model_kind = "single_curve"
        else:
            result = tabulated_curve_family_growth(scenario.growth)
            model_kind = "curve_family"
        status_counts[result.status] += 1
        scenario_results.append(
            {
                "scenario_id": scenario.scenario_id,
                "normalized_weight": scenario.normalized_weight,
                "joint_scenario_source_id": scenario.joint_scenario_source_id,
                "joint_scenario_source_sha256": scenario.joint_scenario_source_sha256,
                "deterministic_model_kind": model_kind,
                "assessment_id": scenario.growth.assessment_id,
                "physical_scope_id": scenario.growth.physical_scope_id,
                "input_sha256": canonical_digest(scenario.growth.model_dump(mode="json")),
                "status": result.status,
                "final_depth_m": result.values["final_depth_m"],
                "cycles_evaluated": result.values["cycles_evaluated"],
                "termination_reason": result.values["termination_reason"],
            }
        )
        if result.status == "computed":
            complete_rows.append((result.values["final_depth_m"], scenario.normalized_weight))

    all_computed = status_counts["computed"] == len(x.scenarios)
    values = {
        "ensemble_run_id": x.ensemble_run_id,
        "distribution_definition_id": x.distribution_definition_id,
        "sample_design_id": x.sample_design_id,
        "physical_scope_id": x.scenarios[0].growth.physical_scope_id,
        "scenario_count": len(x.scenarios),
        "weight_sum": sum(scenario.normalized_weight for scenario in x.scenarios),
        "status_counts": status_counts,
        "all_scenarios_computed": all_computed,
        "scenario_results": scenario_results,
        "weighted_mean_final_depth_m": None,
        "weighted_standard_deviation_final_depth_m": None,
        "weighted_quantiles": None,
        "depth_exceedance_threshold_m": x.depth_exceedance_threshold_m,
        "model_implied_depth_exceedance_probability": None,
    }
    if all_computed:
        mean = sum(value * weight for value, weight in complete_rows)
        variance = sum(weight * (value - mean) ** 2 for value, weight in complete_rows)
        values.update(
            {
                "weighted_mean_final_depth_m": mean,
                "weighted_standard_deviation_final_depth_m": math.sqrt(max(variance, 0.0)),
                "weighted_quantiles": [
                    {
                        "cumulative_probability": quantile,
                        "final_depth_m": _weighted_inverse_cdf(complete_rows, quantile),
                    }
                    for quantile in x.requested_quantiles
                ],
                "model_implied_depth_exceedance_probability": sum(
                    weight for value, weight in complete_rows if value >= x.depth_exceedance_threshold_m
                ),
            }
        )
    return Calculation(
        status="computed" if all_computed else "out_of_scope",
        values=values,
        notes=(
            "Each row is a complete caller-supplied deterministic crack-growth scenario, allowing joint variation of curve points, curve families, geometry tables, ordered load blocks, toughness and numerical controls without reducing them to global multipliers.",
            "The calculator preserves scenario identity, source digest and deterministic input digest; it does not generate, fit, normalize, interpolate between or establish probabilities for scenarios.",
            "If any scenario is outside scope, all rows remain visible and aggregate statistics are withheld. The declared-depth exceedance mass is an input-uncertainty push-forward, not a period first-failure probability, FTA basic-event probability, model-form validation, confidence bound or code acceptance result.",
        ),
    )


ScenarioEvaluationState = Literal[
    "computed", "needs_data", "out_of_scope", "invalid_input", "execution_failed"
]


class CrackGrowthScenarioManifestRow(Contract):
    schema_version: Literal["matintegrity.crack_growth_scenario_manifest_row.v1"] = (
        "matintegrity.crack_growth_scenario_manifest_row.v1"
    )
    scenario_id: str = Field(min_length=1)
    normalized_weight: Positive
    joint_scenario_source_id: str = Field(min_length=1)
    joint_scenario_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)


class CrackGrowthScenarioEvaluation(Contract):
    schema_version: Literal["matintegrity.crack_growth_scenario_evaluation.v1"] = (
        "matintegrity.crack_growth_scenario_evaluation.v1"
    )
    scenario_id: str = Field(min_length=1)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: ScenarioEvaluationState
    final_depth_m: Positive | None = None
    cycles_evaluated: Nonnegative | None = None
    termination_reason: str | None = None
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def computed_values_present(self):
        values = (self.final_depth_m, self.cycles_evaluated, self.termination_reason)
        if self.status == "computed" and any(value is None for value in values):
            raise ValueError("a computed crack-growth scenario evaluation needs all result values")
        if self.status in {"invalid_input", "execution_failed"} and any(
            value is not None for value in values
        ):
            raise ValueError("invalid or failed external evaluations cannot claim result values")
        return self


class TabulatedCrackGrowthScenarioReduction(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth_scenario_reduction.v1"] = (
        "matintegrity.tabulated_crack_growth_scenario_reduction.v1"
    )
    ensemble_run_id: str = Field(min_length=1)
    distribution_definition_id: str = Field(min_length=1)
    sample_design_id: str = Field(min_length=1)
    manifest: list[CrackGrowthScenarioManifestRow] = Field(min_length=2)
    evaluations: list[CrackGrowthScenarioEvaluation] = Field(min_length=2)
    requested_quantiles: list[float] = Field(min_length=1)
    depth_exceedance_threshold_m: Positive
    maximum_weight_sum_error: float = Field(gt=0, le=1e-6)
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    external_evaluations_reviewed: Literal[True]
    normalized_weight_meaning_reviewed: Literal[True]
    common_physical_scope_reviewed: Literal[True]

    @model_validator(mode="after")
    def aligned_external_results(self):
        manifest_ids = [row.scenario_id for row in self.manifest]
        evaluation_ids = [row.scenario_id for row in self.evaluations]
        if len(set(manifest_ids)) != len(manifest_ids):
            raise ValueError("scenario-reduction manifest IDs must be unique")
        if len(set(evaluation_ids)) != len(evaluation_ids):
            raise ValueError("scenario-reduction evaluation IDs must be unique")
        if set(manifest_ids) != set(evaluation_ids):
            raise ValueError("scenario-reduction evaluations must exactly cover the manifest")
        if abs(sum(row.normalized_weight for row in self.manifest) - 1.0) > (self.maximum_weight_sum_error):
            raise ValueError("scenario-reduction manifest weights must sum to one")
        if len({row.physical_scope_id for row in self.manifest}) != 1:
            raise ValueError("scenario-reduction manifest must share one physical scope")
        if any(not 0 < quantile < 1 for quantile in self.requested_quantiles):
            raise ValueError("requested scenario-reduction quantiles must lie inside zero and one")
        if any(
            right <= left
            for left, right in zip(self.requested_quantiles, self.requested_quantiles[1:], strict=False)
        ):
            raise ValueError("requested scenario-reduction quantiles must strictly increase")
        manifest_by_id = {row.scenario_id: row for row in self.manifest}
        for evaluation in self.evaluations:
            expected = manifest_by_id[evaluation.scenario_id]
            if evaluation.input_sha256 != expected.input_sha256:
                raise ValueError("scenario-reduction evaluation input digest does not match manifest")
            if (
                evaluation.evaluator_id != self.evaluator_id
                or evaluation.evaluator_revision != self.evaluator_revision
                or evaluation.evaluator_configuration_sha256 != self.evaluator_configuration_sha256
            ):
                raise ValueError("scenario-reduction evaluator identity is inconsistent")
        return self


def crack_growth_scenario_manifest(
    x: TabulatedCrackGrowthScenarioEnsemble,
) -> list[CrackGrowthScenarioManifestRow]:
    """Create a portable identity/weight manifest without evaluating any scenario."""
    return [
        CrackGrowthScenarioManifestRow(
            scenario_id=scenario.scenario_id,
            normalized_weight=scenario.normalized_weight,
            joint_scenario_source_id=scenario.joint_scenario_source_id,
            joint_scenario_source_sha256=scenario.joint_scenario_source_sha256,
            input_sha256=canonical_digest(scenario.growth.model_dump(mode="json")),
            physical_scope_id=scenario.growth.physical_scope_id,
        )
        for scenario in x.scenarios
    ]


def evaluate_crack_growth_scenario_job(
    scenario: CrackGrowthScenario,
    *,
    evaluator_id: str,
    evaluator_revision: str,
    evaluator_configuration_sha256: str,
) -> CrackGrowthScenarioEvaluation:
    """Evaluate one independently schedulable scenario and bind it to its input digest."""
    input_sha256 = canonical_digest(scenario.growth.model_dump(mode="json"))
    if isinstance(scenario.growth, TabulatedCrackGrowth):
        result = tabulated_crack_growth(scenario.growth)
    else:
        result = tabulated_curve_family_growth(scenario.growth)
    values = {
        "final_depth_m": result.values["final_depth_m"],
        "cycles_evaluated": result.values["cycles_evaluated"],
        "termination_reason": result.values["termination_reason"],
    }
    return CrackGrowthScenarioEvaluation(
        scenario_id=scenario.scenario_id,
        input_sha256=input_sha256,
        evaluator_id=evaluator_id,
        evaluator_revision=evaluator_revision,
        evaluator_configuration_sha256=evaluator_configuration_sha256,
        status=result.status,
        **values,
        result_sha256=canonical_digest(
            {
                "status": result.status,
                **values,
            }
        ),
    )


def tabulated_crack_growth_scenario_reduction(
    x: TabulatedCrackGrowthScenarioReduction,
) -> Calculation:
    """Reduce complete, externally evaluated scenario rows without silently filtering failures."""
    evaluation_by_id = {row.scenario_id: row for row in x.evaluations}
    ordered_rows = []
    complete_rows = []
    status_counts = {state: 0 for state in ScenarioEvaluationState.__args__}
    for manifest in x.manifest:
        evaluation = evaluation_by_id[manifest.scenario_id]
        status_counts[evaluation.status] += 1
        ordered_rows.append(
            {
                **manifest.model_dump(mode="json"),
                "evaluator_id": evaluation.evaluator_id,
                "evaluator_revision": evaluation.evaluator_revision,
                "evaluator_configuration_sha256": evaluation.evaluator_configuration_sha256,
                "status": evaluation.status,
                "final_depth_m": evaluation.final_depth_m,
                "cycles_evaluated": evaluation.cycles_evaluated,
                "termination_reason": evaluation.termination_reason,
                "result_sha256": evaluation.result_sha256,
            }
        )
        if evaluation.status == "computed":
            complete_rows.append((evaluation.final_depth_m, manifest.normalized_weight))

    all_computed = status_counts["computed"] == len(x.manifest)
    values = {
        "ensemble_run_id": x.ensemble_run_id,
        "distribution_definition_id": x.distribution_definition_id,
        "sample_design_id": x.sample_design_id,
        "physical_scope_id": x.manifest[0].physical_scope_id,
        "scenario_count": len(x.manifest),
        "weight_sum": sum(row.normalized_weight for row in x.manifest),
        "status_counts": status_counts,
        "all_scenarios_computed": all_computed,
        "scenario_results": ordered_rows,
        "weighted_mean_final_depth_m": None,
        "weighted_standard_deviation_final_depth_m": None,
        "weighted_quantiles": None,
        "depth_exceedance_threshold_m": x.depth_exceedance_threshold_m,
        "model_implied_depth_exceedance_probability": None,
    }
    if all_computed:
        mean = sum(value * weight for value, weight in complete_rows)
        variance = sum(weight * (value - mean) ** 2 for value, weight in complete_rows)
        values.update(
            {
                "weighted_mean_final_depth_m": mean,
                "weighted_standard_deviation_final_depth_m": math.sqrt(max(variance, 0.0)),
                "weighted_quantiles": [
                    {
                        "cumulative_probability": quantile,
                        "final_depth_m": _weighted_inverse_cdf(complete_rows, quantile),
                    }
                    for quantile in x.requested_quantiles
                ],
                "model_implied_depth_exceedance_probability": sum(
                    weight for value, weight in complete_rows if value >= x.depth_exceedance_threshold_m
                ),
            }
        )
    return Calculation(
        status="computed" if all_computed else "out_of_scope",
        values=values,
        notes=(
            "The manifest and externally evaluated rows form a portable map/reduce boundary: scenario identity, weight, physical scope, input digest, evaluator identity, configuration digest and result digest are checked before aggregation.",
            "Missing, duplicate, extra, digest-mismatched or mixed-evaluator rows are rejected. Noncomputed rows are retained and suppress every aggregate rather than being filtered or renormalized.",
            "The reducer does not establish scenario probabilities, scheduler correctness, model-form validity, period failure probability, FTA basic-event probability, confidence bounds or code acceptance.",
        ),
    )


class CrackGrowthUncertaintyDesignLevel(Contract):
    schema_version: Literal["matintegrity.crack_growth_uncertainty_design_level.v1"] = (
        "matintegrity.crack_growth_uncertainty_design_level.v1"
    )
    level_id: str = Field(min_length=1)
    sample_design_id: str = Field(min_length=1)
    joint_sample_source_id: str = Field(min_length=1)
    joint_sample_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    relationship_to_previous: Literal[
        "initial", "nested_refinement", "refined_design", "independent_replicate"
    ]
    samples: list[CrackGrowthUncertaintySample] = Field(min_length=2)


class TabulatedCrackGrowthUncertaintyConvergence(Contract):
    schema_version: Literal["matintegrity.tabulated_crack_growth_uncertainty_convergence.v1"] = (
        "matintegrity.tabulated_crack_growth_uncertainty_convergence.v1"
    )
    convergence_run_id: str = Field(min_length=1)
    distribution_definition_id: str = Field(min_length=1)
    base_growth: TabulatedCrackGrowth | TabulatedCurveFamilyGrowth = Field(discriminator="schema_version")
    levels: list[CrackGrowthUncertaintyDesignLevel] = Field(min_length=2)
    requested_quantiles: list[float] = Field(min_length=1)
    depth_exceedance_threshold_m: Positive
    maximum_weight_sum_error: float = Field(gt=0, le=1e-6)
    depth_change_scale_m: Positive
    maximum_normalized_mean_depth_change: Nonnegative
    maximum_normalized_standard_deviation_change: Nonnegative
    maximum_normalized_quantile_depth_change: Nonnegative
    maximum_absolute_exceedance_probability_change: float = Field(ge=0, le=1)
    joint_sample_values_reviewed: Literal[True]
    dependence_preserved_in_joint_rows: Literal[True]
    normalized_weight_meaning_reviewed: Literal[True]
    base_model_and_multiplier_scope_reviewed: Literal[True]
    level_relationships_reviewed: Literal[True]
    diagnostic_tolerances_reviewed: Literal[True]

    @model_validator(mode="after")
    def convergence_design(self):
        level_ids = [level.level_id for level in self.levels]
        design_ids = [level.sample_design_id for level in self.levels]
        if len(set(level_ids)) != len(level_ids) or len(set(design_ids)) != len(design_ids):
            raise ValueError("uncertainty level and sample-design IDs must be unique")
        if self.levels[0].relationship_to_previous != "initial":
            raise ValueError("the first uncertainty level must declare the initial relationship")
        if any(level.relationship_to_previous == "initial" for level in self.levels[1:]):
            raise ValueError("only the first uncertainty level may be initial")
        if any(not 0 < quantile < 1 for quantile in self.requested_quantiles):
            raise ValueError("requested uncertainty quantiles must lie strictly between zero and one")
        if any(
            right <= left
            for left, right in zip(self.requested_quantiles, self.requested_quantiles[1:], strict=False)
        ):
            raise ValueError("requested uncertainty quantiles must strictly increase")
        for level in self.levels:
            sample_ids = [sample.sample_id for sample in level.samples]
            if len(set(sample_ids)) != len(sample_ids):
                raise ValueError("uncertainty sample IDs must be unique inside each level")
            weight_sum = sum(sample.normalized_weight for sample in level.samples)
            if abs(weight_sum - 1.0) > self.maximum_weight_sum_error:
                raise ValueError("each uncertainty level's weights must sum to one")
        for previous, current in zip(self.levels, self.levels[1:], strict=False):
            if current.relationship_to_previous in {"nested_refinement", "refined_design"}:
                if len(current.samples) <= len(previous.samples):
                    raise ValueError("refined uncertainty levels must contain more samples")
            if current.relationship_to_previous == "nested_refinement":
                current_by_id = {sample.sample_id: sample for sample in current.samples}
                for old in previous.samples:
                    if old.sample_id not in current_by_id:
                        raise ValueError("nested refinement must retain every prior sample ID")
                    new = current_by_id[old.sample_id]
                    old_values = old.model_dump(exclude={"normalized_weight"})
                    new_values = new.model_dump(exclude={"normalized_weight"})
                    if old_values != new_values:
                        raise ValueError("nested refinement changed a prior joint sample row")
        return self


def tabulated_crack_growth_uncertainty_convergence(
    x: TabulatedCrackGrowthUncertaintyConvergence,
) -> Calculation:
    """Compare ordered uncertainty designs without claiming mathematical convergence."""
    level_rows = []
    calculations = []
    for level in x.levels:
        request = TabulatedCrackGrowthUncertainty(
            uncertainty_run_id=f"{x.convergence_run_id}:{level.level_id}",
            distribution_definition_id=x.distribution_definition_id,
            sample_design_id=level.sample_design_id,
            joint_sample_source_id=level.joint_sample_source_id,
            joint_sample_source_sha256=level.joint_sample_source_sha256,
            base_growth=x.base_growth,
            samples=level.samples,
            requested_quantiles=x.requested_quantiles,
            depth_exceedance_threshold_m=x.depth_exceedance_threshold_m,
            maximum_weight_sum_error=x.maximum_weight_sum_error,
            joint_sample_values_reviewed=True,
            dependence_preserved_in_joint_rows=True,
            normalized_weight_meaning_reviewed=True,
            base_model_and_multiplier_scope_reviewed=True,
        )
        calculation = tabulated_crack_growth_uncertainty(request)
        calculations.append(calculation)
        level_rows.append(
            {
                "level_id": level.level_id,
                "sample_design_id": level.sample_design_id,
                "relationship_to_previous": level.relationship_to_previous,
                "sample_count": len(level.samples),
                "status": calculation.status,
                "weighted_mean_final_depth_m": calculation.values["weighted_mean_final_depth_m"],
                "weighted_standard_deviation_final_depth_m": calculation.values[
                    "weighted_standard_deviation_final_depth_m"
                ],
                "weighted_quantiles": calculation.values["weighted_quantiles"],
                "model_implied_depth_exceedance_probability": calculation.values[
                    "model_implied_depth_exceedance_probability"
                ],
                "status_counts": calculation.values["status_counts"],
            }
        )

    transition_rows = []
    for previous, current in zip(level_rows, level_rows[1:], strict=False):
        both_computed = previous["status"] == current["status"] == "computed"
        transition = {
            "from_level_id": previous["level_id"],
            "to_level_id": current["level_id"],
            "relationship_to_previous": current["relationship_to_previous"],
            "both_levels_computed": both_computed,
            "normalized_mean_depth_change": None,
            "normalized_standard_deviation_change": None,
            "maximum_normalized_quantile_depth_change": None,
            "absolute_exceedance_probability_change": None,
            "diagnostic_criteria_met": None,
        }
        if both_computed:
            mean_change = (
                abs(current["weighted_mean_final_depth_m"] - previous["weighted_mean_final_depth_m"])
                / x.depth_change_scale_m
            )
            standard_deviation_change = (
                abs(
                    current["weighted_standard_deviation_final_depth_m"]
                    - previous["weighted_standard_deviation_final_depth_m"]
                )
                / x.depth_change_scale_m
            )
            quantile_change = max(
                abs(new["final_depth_m"] - old["final_depth_m"]) / x.depth_change_scale_m
                for old, new in zip(
                    previous["weighted_quantiles"], current["weighted_quantiles"], strict=True
                )
            )
            probability_change = abs(
                current["model_implied_depth_exceedance_probability"]
                - previous["model_implied_depth_exceedance_probability"]
            )
            criteria_met = (
                mean_change <= x.maximum_normalized_mean_depth_change
                and standard_deviation_change <= x.maximum_normalized_standard_deviation_change
                and quantile_change <= x.maximum_normalized_quantile_depth_change
                and probability_change <= x.maximum_absolute_exceedance_probability_change
            )
            transition.update(
                {
                    "normalized_mean_depth_change": mean_change,
                    "normalized_standard_deviation_change": standard_deviation_change,
                    "maximum_normalized_quantile_depth_change": quantile_change,
                    "absolute_exceedance_probability_change": probability_change,
                    "diagnostic_criteria_met": criteria_met,
                }
            )
        transition_rows.append(transition)

    all_levels_computed = all(row["status"] == "computed" for row in level_rows)
    all_transitions_met = all_levels_computed and all(
        row["diagnostic_criteria_met"] is True for row in transition_rows
    )
    final = level_rows[-1]
    return Calculation(
        status="computed" if all_levels_computed else "out_of_scope",
        values={
            "convergence_run_id": x.convergence_run_id,
            "distribution_definition_id": x.distribution_definition_id,
            "level_count": len(level_rows),
            "all_levels_computed": all_levels_computed,
            "all_transition_diagnostic_criteria_met": (all_transitions_met if all_levels_computed else None),
            "final_level_id": final["level_id"],
            "final_weighted_mean_depth_m": final["weighted_mean_final_depth_m"],
            "final_weighted_standard_deviation_depth_m": final["weighted_standard_deviation_final_depth_m"],
            "model_implied_depth_exceedance_probability": final["model_implied_depth_exceedance_probability"],
            "level_results": level_rows,
            "transition_diagnostics": transition_rows,
        },
        notes=(
            "Ordered design comparisons retain every level and declare whether rows are nested refinements, nonnested refinements or independent replicates; nested lineage fixes prior multiplier rows but allows normalized weights to change.",
            "Changes are normalized by a caller-declared physical depth scale, not by a potentially zero statistic. Meeting diagnostic tolerances is not a convergence proof, error bound, distribution validation or sample-size guarantee.",
            "Any out-of-scope sample makes its level and the overall diagnostic out of scope; failed rows and levels are never discarded or renormalized.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fracture.variable_paris",
            VariableParis,
            variable_paris,
            {"final_depth_m": "m", "cycles_evaluated": "cycle", "requested_cycles": "cycle"},
            (
                "Ordered tensile blocks with explicit Paris calibration, threshold, toughness and bounded geometry provider.",
            ),
            ("nasa_paris", "nasa_fracture_control"),
        ),
        ModelSpec(
            "fracture.tabulated_growth_rate",
            TabulatedGrowthRateQuery,
            tabulated_growth_rate,
            {"query_results": "mixed"},
            (
                "Caller-authorized positive crack-growth points with strictly increasing delta K; log-log interpolation is confined to the supplied support.",
                "Material condition, environment, stress ratio, frequency and applicability remain caller-reviewed and no design curve is inferred.",
            ),
            ("astm_e647_scope", "tabulated_growth_interpolation_derivation"),
            qualification="user_model",
        ),
        ModelSpec(
            "fracture.tabulated_crack_growth",
            TabulatedCrackGrowth,
            tabulated_crack_growth,
            {
                "final_depth_m": "m",
                "cycles_evaluated": "cycle",
                "requested_cycles": "cycle",
            },
            (
                "Caller-authorized tabulated da/dN curve, explicitly matched and reviewed target material/environment, reviewed nondecreasing geometry provider and ordered tensile load blocks.",
                "Stress ratio and frequency are matched within explicit tolerances; curve and geometry extrapolation are prohibited. Missing frequency or target-condition mismatch prevents life integration.",
            ),
            ("astm_e647_scope", "tabulated_growth_interpolation_derivation"),
            qualification="user_model",
        ),
        ModelSpec(
            "fracture.tabulated_curve_family_growth",
            TabulatedCurveFamilyGrowth,
            tabulated_curve_family_growth,
            {
                "final_depth_m": "m",
                "cycles_evaluated": "cycle",
                "requested_cycles": "cycle",
            },
            (
                "Caller-reviewed curve family explicitly matched to the assessment target material/environment; each block selects one curve by explicit stress-ratio and relative-frequency tolerances.",
                "Curve conditions are not interpolated. Missing or tied candidates remain out of scope and every selected curve retains its own delta-K support.",
            ),
            (
                "astm_e647_scope",
                "tabulated_growth_interpolation_derivation",
                "tabulated_curve_family_selection_derivation",
            ),
            qualification="user_model",
        ),
        ModelSpec(
            "fracture.tabulated_crack_growth_uncertainty",
            TabulatedCrackGrowthUncertainty,
            tabulated_crack_growth_uncertainty,
            {
                "sample_count": "1",
                "weight_sum": "1",
                "weighted_mean_final_depth_m": "m",
                "weighted_standard_deviation_final_depth_m": "m",
                "depth_exceedance_threshold_m": "m",
                "model_implied_depth_exceedance_probability": "1",
            },
            (
                "Caller-supplied normalized joint uncertainty rows multiply curve rates, geometry factors, tensile stresses and toughness while preserving row dependence.",
                "All samples must compute before aggregate moments, inverse-CDF quantiles or depth-exceedance probability are reported; unsuccessful samples are never dropped or renormalized.",
            ),
            (
                "tabulated_growth_interpolation_derivation",
                "joint_crack_growth_uncertainty_propagation",
            ),
            qualification="user_model",
            probability_semantics={
                "model_implied_depth_exceedance_probability": ("model_implied_input_uncertainty_probability")
            },
        ),
        ModelSpec(
            "fracture.tabulated_crack_growth_uncertainty_convergence",
            TabulatedCrackGrowthUncertaintyConvergence,
            tabulated_crack_growth_uncertainty_convergence,
            {
                "level_count": "1",
                "final_weighted_mean_depth_m": "m",
                "final_weighted_standard_deviation_depth_m": "m",
                "model_implied_depth_exceedance_probability": "1",
            },
            (
                "Two or more caller-reviewed uncertainty designs for one distribution and deterministic crack-growth input, with explicit nested, refined or replicate relationships.",
                "Successive weighted-statistic changes use a declared depth scale and diagnostic tolerances; satisfaction is not a convergence proof or distribution qualification.",
            ),
            (
                "joint_crack_growth_uncertainty_propagation",
                "crack_growth_uncertainty_convergence_diagnostic",
            ),
            qualification="user_model",
            probability_semantics={
                "model_implied_depth_exceedance_probability": ("model_implied_input_uncertainty_probability")
            },
        ),
        ModelSpec(
            "fracture.tabulated_crack_growth_scenario_ensemble",
            TabulatedCrackGrowthScenarioEnsemble,
            tabulated_crack_growth_scenario_ensemble,
            {
                "scenario_count": "1",
                "weight_sum": "1",
                "weighted_mean_final_depth_m": "m",
                "weighted_standard_deviation_final_depth_m": "m",
                "depth_exceedance_threshold_m": "m",
                "model_implied_depth_exceedance_probability": "1",
            },
            (
                "Caller-reviewed weighted complete inputs for the single-curve or curve-family deterministic model preserve joint variation in curve points, geometry, ordered loads, toughness and controls.",
                "All scenarios must compute before aggregate moments, quantiles or exceedance mass are reported; scenario probabilities and model-form validity are never inferred.",
            ),
            (
                "tabulated_growth_interpolation_derivation",
                "complete_crack_growth_scenario_ensemble",
            ),
            qualification="user_model",
            probability_semantics={
                "model_implied_depth_exceedance_probability": ("model_implied_input_uncertainty_probability")
            },
        ),
        ModelSpec(
            "fracture.tabulated_crack_growth_scenario_reduction",
            TabulatedCrackGrowthScenarioReduction,
            tabulated_crack_growth_scenario_reduction,
            {
                "scenario_count": "1",
                "weight_sum": "1",
                "weighted_mean_final_depth_m": "m",
                "weighted_standard_deviation_final_depth_m": "m",
                "depth_exceedance_threshold_m": "m",
                "model_implied_depth_exceedance_probability": "1",
            },
            (
                "Portable reduction of externally evaluated complete crack-growth scenarios with exact manifest coverage, input digests and one evaluator identity/configuration.",
                "Every noncomputed row is retained and suppresses aggregate statistics; the reducer does not validate scheduler execution, scenario probabilities or physical model form.",
            ),
            (
                "complete_crack_growth_scenario_ensemble",
                "portable_crack_growth_scenario_reduction",
            ),
            qualification="user_model",
            probability_semantics={
                "model_implied_depth_exceedance_probability": ("model_implied_input_uncertainty_probability")
            },
        ),
    ]
