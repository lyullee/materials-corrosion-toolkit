"""Current-conserving mixed potentials on declared signed polarization interpolants."""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PolarizationCurve(Contract):
    schema_version: Literal["matintegrity.polarization_curve.v1"] = "matintegrity.polarization_curve.v1"
    curve_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    protocol_id: str = Field(min_length=1)
    electrolyte_id: str | None = Field(default=None, min_length=1)
    reference_electrode_id: str | None = Field(default=None, min_length=1)
    temperature_K: Positive | None = None
    point_ids: list[str] = Field(min_length=2, max_length=20000)
    potential_V: list[float] = Field(min_length=2, max_length=20000)
    signed_net_current_density_A_m2: list[float] = Field(min_length=2, max_length=20000)
    current_convention: Literal["anodic_positive_net", "unreviewed_signed_net"] = "anodic_positive_net"
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_branch(self):
        if len({len(self.point_ids), len(self.potential_V), len(self.signed_net_current_density_A_m2)}) != 1:
            raise ValueError("polarization point IDs, potentials and currents must align")
        if len(set(self.point_ids)) != len(self.point_ids) or any(
            not point.strip() for point in self.point_ids
        ):
            raise ValueError("polarization points require unique nonempty identities")
        if any(right <= left for left, right in pairwise(self.potential_V)):
            raise ValueError(
                "one strictly increasing potential branch is required; do not sort a cyclic scan"
            )
        return self


class PolarizedElectrode(Contract):
    electrode_id: str = Field(min_length=1)
    exposed_area_m2: Positive
    curve: PolarizationCurve


class MixedPotential(Contract):
    electrodes: list[PolarizedElectrode] = Field(min_length=2, max_length=32)
    quasi_steady_reviewed: bool
    negligible_ohmic_drop_reviewed: bool
    condition_compatibility_reviewed: bool
    anodic_positive_reviewed: bool
    absolute_balance_tolerance_A: Nonnegative = 1e-12
    relative_balance_tolerance: float = Field(default=1e-10, ge=0, lt=0.01)

    @model_validator(mode="after")
    def distinct_electrodes(self):
        if len({electrode.electrode_id for electrode in self.electrodes}) != len(self.electrodes):
            raise ValueError("electrode identities must be unique")
        if sum(len(electrode.curve.potential_V) for electrode in self.electrodes) > 100000:
            raise ValueError("combined polarization point budget exceeds 100000")
        return self


class MixedPotentialEquilibrium(Contract):
    potential_V: float
    containing_interval_V: list[float] = Field(min_length=2, max_length=2)
    electrode_ids: list[str]
    signed_net_current_density_A_m2: list[float]
    electrode_net_current_A: list[float]
    total_positive_net_current_A: Nonnegative
    current_balance_residual_A: float
    balance_tolerance_A: Nonnegative
    residual_within_tolerance: bool
    balance_slope_left_A_V: float | None
    balance_slope_right_A_V: float | None
    slope_diagnostic: Literal["positive", "negative", "mixed_or_tangent", "support_boundary"]
    numerical_quality: Literal["resolved", "cancellation_limited", "unrepresentable_slope"]

    @model_validator(mode="after")
    def aligned_electrodes_and_support(self):
        if (
            len(
                {
                    len(self.electrode_ids),
                    len(self.signed_net_current_density_A_m2),
                    len(self.electrode_net_current_A),
                }
            )
            != 1
            or len(self.electrode_ids) < 2
        ):
            raise ValueError("equilibrium electrode identities and current arrays must align")
        if len(set(self.electrode_ids)) != len(self.electrode_ids) or any(
            not value.strip() for value in self.electrode_ids
        ):
            raise ValueError("equilibrium electrode identities must be unique and nonempty")
        if not self.containing_interval_V[0] <= self.potential_V <= self.containing_interval_V[1]:
            raise ValueError("equilibrium potential must lie in its declared supporting interval")
        return self


class ChronoamperometryWindowSummary(Contract):
    """One provenance-bound current trace and caller-declared summary windows."""

    schema_version: Literal["matintegrity.chronoamperometry_window_summary.v1"] = (
        "matintegrity.chronoamperometry_window_summary.v1"
    )
    trace_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_archive_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_member_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    time_s: list[float] = Field(min_length=2, max_length=200000)
    current_A: list[float] = Field(min_length=2, max_length=200000)
    analysis_window_s: list[float] = Field(min_length=2, max_length=2)
    baseline_window_s: list[float] | None = Field(default=None, min_length=2, max_length=2)
    boundary_policy: Literal["exact_samples", "piecewise_linear"] = "piecewise_linear"
    sample_order_reviewed: bool
    time_unit_reviewed_as_seconds: bool
    current_unit_reviewed_as_amperes: bool
    current_sign_basis: str = Field(min_length=1)
    current_sign_reviewed: bool

    @model_validator(mode="after")
    def aligned_finite_trace(self):
        if len(self.time_s) != len(self.current_A):
            raise ValueError("chronoamperometry time and current arrays must align")
        if not all(math.isfinite(value) for value in (*self.time_s, *self.current_A)):
            raise ValueError("chronoamperometry arrays must contain only finite values")
        if any(right <= left for left, right in pairwise(self.time_s)):
            raise ValueError("chronoamperometry time must be strictly increasing without sorting")
        for name, window in (
            ("analysis_window_s", self.analysis_window_s),
            ("baseline_window_s", self.baseline_window_s),
        ):
            if window is not None and (
                not all(math.isfinite(value) for value in window) or window[1] <= window[0]
            ):
                raise ValueError(f"{name} must be a finite increasing interval")
        return self


def _window_samples(
    time_s: np.ndarray,
    current_A: np.ndarray,
    window_s: list[float],
    policy: str,
) -> tuple[np.ndarray, np.ndarray] | None:
    start, end = window_s
    if start < time_s[0] or end > time_s[-1]:
        return None
    left = int(np.searchsorted(time_s, start, side="left"))
    right = int(np.searchsorted(time_s, end, side="left"))
    if policy == "exact_samples":
        if left == len(time_s) or right == len(time_s) or time_s[left] != start or time_s[right] != end:
            return None
        return time_s[left : right + 1].copy(), current_A[left : right + 1].copy()
    internal = (time_s > start) & (time_s < end)
    window_time = np.concatenate(([start], time_s[internal], [end]))
    window_current = np.concatenate(
        ([np.interp(start, time_s, current_A)], current_A[internal], [np.interp(end, time_s, current_A)])
    )
    return window_time, window_current


def _absolute_piecewise_linear_integral(time_s: np.ndarray, current_A: np.ndarray) -> float:
    times = [float(time_s[0])]
    currents = [float(current_A[0])]
    for index in range(len(time_s) - 1):
        left, right = float(current_A[index]), float(current_A[index + 1])
        if left * right < 0:
            fraction = abs(left) / (abs(left) + abs(right))
            times.append(float(time_s[index] + fraction * (time_s[index + 1] - time_s[index])))
            currents.append(0.0)
        times.append(float(time_s[index + 1]))
        currents.append(right)
    return float(np.trapezoid(np.abs(currents), times))


def _piecewise_linear_polarity_integrals(time_s: np.ndarray, current_A: np.ndarray) -> tuple[float, float]:
    """Return positive and negative-magnitude charge, splitting every sign-changing segment at zero."""
    positive_charge = 0.0
    negative_charge = 0.0
    for index, duration in enumerate(np.diff(time_s)):
        left = float(current_A[index])
        right = float(current_A[index + 1])
        interval = float(duration)
        if left >= 0 and right >= 0:
            positive_charge += 0.5 * (left + right) * interval
        elif left <= 0 and right <= 0:
            negative_charge += -0.5 * (left + right) * interval
        else:
            fraction = abs(left) / (abs(left) + abs(right))
            if left > 0:
                positive_charge += 0.5 * left * fraction * interval
                negative_charge += 0.5 * abs(right) * (1 - fraction) * interval
            else:
                negative_charge += 0.5 * abs(left) * fraction * interval
                positive_charge += 0.5 * right * (1 - fraction) * interval
    return positive_charge, negative_charge


def chronoamperometry_window_summary(x: ChronoamperometryWindowSummary) -> Calculation:
    """Summarize declared windows without filtering, event classification, or probability conversion."""
    base = dict(
        trace_id=x.trace_id,
        physical_specimen_id=x.physical_specimen_id,
        source_group_id=x.source_group_id,
        source_trace_sha256=x.source_trace_sha256,
        source_archive_sha256=x.source_archive_sha256,
        source_member_sha256=x.source_member_sha256,
        boundary_policy=x.boundary_policy,
    )
    notes = (
        "Integration is over a caller-declared window of the supplied ordered samples; piecewise-linear boundaries add no filtered or synthetic interior samples.",
        "Signed charge follows the reviewed instrument-current sign basis; absolute charge is a signal-magnitude descriptor, not metal loss.",
        "A trace summary does not establish an electrochemical event class, independent specimen, pit dimension, POD, acceptance, life or failure probability.",
    )

    def result(status, reason, **updates):
        return Calculation(status=status, values=base | updates | {"reason": reason}, notes=notes)

    review_flags = {
        "sample_order_reviewed": x.sample_order_reviewed,
        "time_unit_reviewed_as_seconds": x.time_unit_reviewed_as_seconds,
        "current_unit_reviewed_as_amperes": x.current_unit_reviewed_as_amperes,
        "current_sign_reviewed": x.current_sign_reviewed,
    }
    unreviewed = [name for name, reviewed in review_flags.items() if not reviewed]
    if unreviewed:
        return result("needs_data", "unreviewed_trace_basis", unreviewed=unreviewed)

    time_s = np.asarray(x.time_s, dtype=float)
    current_A = np.asarray(x.current_A, dtype=float)
    selected = _window_samples(time_s, current_A, x.analysis_window_s, x.boundary_policy)
    if selected is None:
        reason = (
            "analysis_window_outside_trace_support"
            if x.analysis_window_s[0] < time_s[0] or x.analysis_window_s[1] > time_s[-1]
            else "analysis_window_endpoints_not_sampled"
        )
        return result("out_of_scope", reason)
    analysis_time, analysis_current = selected
    duration = float(analysis_time[-1] - analysis_time[0])
    signed_charge = float(np.trapezoid(analysis_current, analysis_time))
    absolute_charge = _absolute_piecewise_linear_integral(analysis_time, analysis_current)
    positive_polarity_charge, negative_polarity_charge = _piecewise_linear_polarity_integrals(
        analysis_time, analysis_current
    )
    minimum = float(np.min(analysis_current))
    maximum = float(np.max(analysis_current))
    minimum_times = analysis_time[analysis_current == minimum]
    maximum_times = analysis_time[analysis_current == maximum]

    baseline_mean = None
    baseline_charge = None
    baseline_count = 0
    if x.baseline_window_s is not None:
        baseline = _window_samples(time_s, current_A, x.baseline_window_s, x.boundary_policy)
        if baseline is None:
            reason = (
                "baseline_window_outside_trace_support"
                if x.baseline_window_s[0] < time_s[0] or x.baseline_window_s[1] > time_s[-1]
                else "baseline_window_endpoints_not_sampled"
            )
            return result("out_of_scope", reason)
        baseline_time, baseline_current = baseline
        baseline_charge = float(np.trapezoid(baseline_current, baseline_time))
        baseline_mean = baseline_charge / float(baseline_time[-1] - baseline_time[0])
        baseline_count = len(baseline_time)

    values = dict(
        analysis_window_s=list(x.analysis_window_s),
        analysis_sample_count=len(analysis_time),
        analysis_duration_s=duration,
        signed_charge_C=signed_charge,
        absolute_charge_C=absolute_charge,
        positive_polarity_charge_C=positive_polarity_charge,
        negative_polarity_charge_C=negative_polarity_charge,
        time_mean_current_A=signed_charge / duration,
        minimum_current_A=minimum,
        minimum_time_first_s=float(minimum_times[0]),
        minimum_time_last_s=float(minimum_times[-1]),
        maximum_current_A=maximum,
        maximum_time_first_s=float(maximum_times[0]),
        maximum_time_last_s=float(maximum_times[-1]),
        baseline_window_s=list(x.baseline_window_s) if x.baseline_window_s is not None else None,
        baseline_sample_count=baseline_count,
        baseline_signed_charge_C=baseline_charge,
        baseline_time_mean_current_A=baseline_mean,
        minimum_minus_baseline_A=minimum - baseline_mean if baseline_mean is not None else None,
        maximum_minus_baseline_A=maximum - baseline_mean if baseline_mean is not None else None,
        current_sign_basis=x.current_sign_basis,
        interpretation="descriptive_trace_summary_only",
    )
    if not all(
        math.isfinite(value)
        for value in values.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ):
        return result("out_of_scope", "summary_not_numerically_representable")
    return result("computed", "declared_window_summary", **values)


def _interpolate(points, curve):
    positions = np.asarray(curve.potential_V)
    currents = np.asarray(curve.signed_net_current_density_A_m2)
    points = np.asarray(points)
    # The caller restricts points to common support; the final endpoint uses its left segment.
    index = np.clip(np.searchsorted(positions, points, side="right") - 1, 0, len(positions) - 2)
    fraction = (points - positions[index]) / (positions[index + 1] - positions[index])
    return (1 - fraction) * currents[index] + fraction * currents[index + 1]


def mixed_potential(x: MixedPotential) -> Calculation:
    """Find every equilibrium of the signed, piecewise-linear current balance, without extrapolation."""
    curves = [electrode.curve for electrode in x.electrodes]
    base = dict(
        mixed_potential_V=None,
        electrode_ids=[electrode.electrode_id for electrode in x.electrodes],
        electrode_net_current_A=None,
        total_positive_net_current_A=None,
        equilibria=[],
        zero_balance_intervals_V=[],
        common_potential_interval_V=None,
        interpolation="signed_current_linear_in_potential",
        current_meaning="net_external_electrode_current_not_total_metal_dissolution",
    )
    notes = (
        "Common electronic and solution potentials, reviewed quasi-steady compatible curves, and negligible ohmic drop are required.",
        "Net electrode current does not identify partial metal-dissolution current or total corrosion loss.",
        "Roots and slope diagnostics concern the supplied interpolants; measurement, interpolation and dynamic stability are not validated here.",
    )

    def result(status, reason, **updates):
        return Calculation(status=status, values=base | updates | dict(reason=reason), notes=notes)

    flags = (
        "quasi_steady_reviewed",
        "negligible_ohmic_drop_reviewed",
        "condition_compatibility_reviewed",
        "anodic_positive_reviewed",
    )
    unreviewed = [name for name in flags if not getattr(x, name)]
    if unreviewed:
        return result("needs_data", "unreviewed_applicability", unreviewed=unreviewed)
    if any(curve.current_convention != "anodic_positive_net" for curve in curves):
        return result("needs_data", "unreviewed_current_convention")
    for name in ("reference_electrode_id", "electrolyte_id", "temperature_K"):
        values = [getattr(curve, name) for curve in curves]
        if any(value is None for value in values):
            return result("needs_data", "missing_curve_condition", condition=name)
        if len(set(values)) != 1:
            return result("out_of_scope", "incompatible_curve_conditions", condition=name)

    lower = max(curve.potential_V[0] for curve in curves)
    upper = min(curve.potential_V[-1] for curve in curves)
    if upper <= lower:
        return result("out_of_scope", "no_common_potential_span")
    base["common_potential_interval_V"] = [lower, upper]
    with np.errstate(over="ignore", invalid="ignore"):
        if any(not np.isfinite(np.diff(curve.potential_V)).all() for curve in curves):
            return result("out_of_scope", "potential_interval_not_representable")
    knots = np.unique(
        np.concatenate(
            [np.array([lower, upper])]
            + [
                np.asarray(curve.potential_V)[
                    (np.asarray(curve.potential_V) > lower) & (np.asarray(curve.potential_V) < upper)
                ]
                for curve in curves
            ]
        )
    )
    densities = np.asarray([_interpolate(knots, curve) for curve in curves])
    areas = np.asarray([electrode.exposed_area_m2 for electrode in x.electrodes])
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        currents = areas[:, None] * densities
    if not np.isfinite(currents).all() or np.any((currents == 0) & (densities != 0)):
        return result("out_of_scope", "electrode_current_not_representable")
    scale = float(np.max(np.abs(currents)))
    if scale == 0:
        return result("needs_data", "nonunique_zero_balance", zero_balance_intervals_V=[[lower, upper]])
    normalized = currents / scale
    if np.any((normalized == 0) & (currents != 0)):
        return result("out_of_scope", "relative_current_scale_not_representable")
    balance = np.asarray([math.fsum(column) for column in normalized.T])
    magnitude = np.sum(np.abs(normalized), axis=0)
    zero_intervals = []
    zero_edges = set()
    for index in range(len(knots) - 1):
        if balance[index] == balance[index + 1] == 0:
            left, right = float(knots[index]), float(knots[index + 1])
            if zero_intervals and zero_intervals[-1][1] == left:
                zero_intervals[-1][1] = right
            else:
                zero_intervals.append([left, right])
            zero_edges.update((index, index + 1))
    candidates = [
        (float(knots[index]), index, True)
        for index in np.flatnonzero(balance == 0)
        if index not in zero_edges
    ]
    for index, (left, right) in enumerate(pairwise(balance)):
        if (left < 0 < right) or (right < 0 < left):
            # A convex combination avoids subtracting two large absolute potentials.
            fraction = abs(left) / (abs(left) + abs(right))
            potential = (1 - fraction) * knots[index] + fraction * knots[index + 1]
            candidates.append((float(potential), index, False))
    candidates.sort()
    equilibria = []
    epsilon = np.finfo(float).eps

    def slope(index):
        if index < 0 or index >= len(knots) - 1:
            return None
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            value = scale * ((balance[index + 1] - balance[index]) / (knots[index + 1] - knots[index]))
        return float(value) if math.isfinite(value) else None

    for potential, index, at_knot in candidates:
        left_index, right_index = (index - 1, index) if at_knot else (index, index)
        left_slope, right_slope = slope(left_index), slope(right_index)
        indices = [i for i in (left_index, right_index) if 0 <= i < len(knots) - 1]
        cancellation_limited = any(
            abs(balance[i + 1] - balance[i]) <= 32 * epsilon * max(magnitude[i], magnitude[i + 1])
            for i in indices
        )
        boundary = at_knot and index in (0, len(knots) - 1)
        unrepresentable = (left_slope is None and left_index >= 0) or (
            right_slope is None and right_index < len(knots) - 1
        )
        quality = (
            "unrepresentable_slope"
            if unrepresentable
            else "cancellation_limited"
            if cancellation_limited
            else "resolved"
        )
        if boundary:
            diagnostic = "support_boundary"
        elif left_slope is not None and right_slope is not None and left_slope > 0 and right_slope > 0:
            diagnostic = "positive"
        elif left_slope is not None and right_slope is not None and left_slope < 0 and right_slope < 0:
            diagnostic = "negative"
        else:
            diagnostic = "mixed_or_tangent"
        current_density = [float(_interpolate(potential, curve)) for curve in curves]
        electrode_current = [float(area * value) for area, value in zip(areas, current_density, strict=True)]
        residual_normalized = math.fsum(value / scale for value in electrode_current)
        absolute_sum_normalized = math.fsum(abs(value / scale) for value in electrode_current)
        tolerance_normalized = (
            x.absolute_balance_tolerance_A / scale + x.relative_balance_tolerance * absolute_sum_normalized
        )
        residual = scale * residual_normalized
        tolerance = scale * tolerance_normalized
        positive_current = scale * math.fsum(max(value / scale, 0) for value in electrode_current)
        if not all(math.isfinite(value) for value in (residual, tolerance, positive_current)):
            return result("out_of_scope", "balance_output_not_representable")
        first, last = max(0, left_index), min(len(knots) - 1, right_index + 1)
        equilibria.append(
            MixedPotentialEquilibrium(
                potential_V=potential,
                containing_interval_V=[float(knots[first]), float(knots[last])],
                electrode_ids=base["electrode_ids"],
                signed_net_current_density_A_m2=current_density,
                electrode_net_current_A=electrode_current,
                total_positive_net_current_A=positive_current,
                current_balance_residual_A=residual,
                balance_tolerance_A=tolerance,
                residual_within_tolerance=abs(residual_normalized) <= tolerance_normalized,
                balance_slope_left_A_V=left_slope,
                balance_slope_right_A_V=right_slope,
                slope_diagnostic=diagnostic,
                numerical_quality=quality,
            ).model_dump(mode="json")
        )
    details = dict(equilibria=equilibria, zero_balance_intervals_V=zero_intervals)
    if zero_intervals:
        return result("needs_data", "nonunique_zero_balance", **details)
    if not equilibria:
        return result("out_of_scope", "no_equilibrium_in_common_support", **details)
    if len(equilibria) > 1:
        return result("needs_data", "multiple_equilibria", **details)
    equilibrium = equilibria[0]
    if not equilibrium["residual_within_tolerance"] or equilibrium["numerical_quality"] != "resolved":
        return result("needs_data", "numerically_unresolved_equilibrium", **details)
    return result(
        "computed",
        "unique_interpolant_equilibrium",
        **details,
        mixed_potential_V=equilibrium["potential_V"],
        electrode_net_current_A=equilibrium["electrode_net_current_A"],
        total_positive_net_current_A=equilibrium["total_positive_net_current_A"],
    )


def specifications():
    return [
        ModelSpec(
            "corrosion.chronoamperometry_window_summary",
            ChronoamperometryWindowSummary,
            chronoamperometry_window_summary,
            {
                "analysis_window_s": "s",
                "analysis_duration_s": "s",
                "signed_charge_C": "C",
                "absolute_charge_C": "C",
                "positive_polarity_charge_C": "C",
                "negative_polarity_charge_C": "C",
                "time_mean_current_A": "A",
                "minimum_current_A": "A",
                "minimum_time_first_s": "s",
                "minimum_time_last_s": "s",
                "maximum_current_A": "A",
                "maximum_time_first_s": "s",
                "maximum_time_last_s": "s",
                "baseline_window_s": "s",
                "baseline_signed_charge_C": "C",
                "baseline_time_mean_current_A": "A",
                "minimum_minus_baseline_A": "A",
                "maximum_minus_baseline_A": "A",
            },
            (
                "Time and current units, strict sample order, current sign and source trace digest are explicitly reviewed.",
                "Trapezoidal integration represents the supplied trace as piecewise linear; requested boundaries are exact samples or explicit linear interpolants.",
                "Raw signal summaries do not classify corrosion events, infer metal loss or pit dimensions, or establish probability, POD, life or acceptance.",
            ),
            ("authored_chronoamperometry_window_contract",),
        ),
        ModelSpec(
            "corrosion.mixed_potential",
            MixedPotential,
            mixed_potential,
            {
                "mixed_potential_V": "V",
                "electrode_net_current_A": "A",
                "total_positive_net_current_A": "A",
                "common_potential_interval_V": "V",
                "zero_balance_intervals_V": "V",
            },
            (
                "Reviewed compatible signed net polarization curves share one reference, electrolyte and temperature; negligible ohmic drop and quasi-steady response are required.",
                "Area-scaled electrode currents sum to zero on the common measured support; all piecewise-linear roots and zero intervals are preserved.",
                "A unique algebraic equilibrium does not establish dynamic stability, total metal loss, structural acceptance or failure probability.",
            ),
            ("iupac_mixed_potential", "gamry_net_polarization", "signed_interpolant_balance"),
        ),
    ]
