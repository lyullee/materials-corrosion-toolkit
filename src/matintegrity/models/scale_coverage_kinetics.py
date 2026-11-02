"""Caller-calibrated evolution of covered surface fraction for one scale phase."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

_GAS_CONSTANT_J_MOL_K = 8.31446261815324


class ScaleCoverageKineticInterval(Contract):
    """One exposure interval with an optional linearly varying saturation path."""

    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    saturation_ratio: Nonnegative
    saturation_ratio_end: Nonnegative | None = None
    temperature_K: Positive | None = None

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("scale-coverage interval must have positive duration")
        return self


class CallerScaleCoverageKinetics(Contract):
    schema_version: Literal["matintegrity.caller_scale_coverage_kinetics.v1"] = (
        "matintegrity.caller_scale_coverage_kinetics.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    solution_condition_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    initial_covered_area_fraction: float = Field(ge=0.0, le=1.0)
    attachment_rate_constant_s: Nonnegative
    rate_reference_temperature_K: Positive | None = None
    minimum_rate_valid_temperature_K: Positive | None = None
    maximum_rate_valid_temperature_K: Positive | None = None
    attachment_activation_energy_J_mol: Nonnegative | None = None
    attachment_supersaturation_order: Positive = Field(le=8.0)
    detachment_rate_constant_s: Nonnegative
    detachment_activation_energy_J_mol: Nonnegative | None = None
    arrhenius_temperature_scaling_reviewed: bool = False
    detachment_undersaturation_order: Positive = Field(le=8.0)
    intervals: tuple[ScaleCoverageKineticInterval, ...] = Field(min_length=1, max_length=100000)
    interval_constant_saturation_reviewed: bool
    linearly_varying_saturation_reviewed: bool = False
    interval_temperature_profile_reviewed: bool = False
    maximum_time_step_s: Positive | None = None
    minimum_time_step_s: Positive | None = None
    coverage_absolute_tolerance: Positive | None = None
    coverage_relative_tolerance: Positive | None = None
    inventory_absolute_tolerance: Positive | None = None
    inventory_relative_tolerance: Positive | None = None
    maximum_rate_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_rejected_steps_per_interval: int = Field(default=1000, ge=0, le=100000)
    coverage_kinetic_law_and_standard_state_reviewed: bool
    rate_coefficients_and_temperature_reviewed: bool
    scale_phase_identity_and_specimen_match_reviewed: bool
    area_average_coverage_representation_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_intervals(self):
        arrhenius_values = (
            self.rate_reference_temperature_K,
            self.minimum_rate_valid_temperature_K,
            self.maximum_rate_valid_temperature_K,
            self.attachment_activation_energy_J_mol,
            self.detachment_activation_energy_J_mol,
        )
        if any(value is not None for value in arrhenius_values):
            if any(value is None for value in arrhenius_values):
                raise ValueError("Arrhenius scaling requires reference temperature and both activation energies")
            if not self.arrhenius_temperature_scaling_reviewed:
                raise ValueError("Arrhenius scaling requires explicit parameter applicability review")
            if self.maximum_rate_valid_temperature_K <= self.minimum_rate_valid_temperature_K:
                raise ValueError("Arrhenius temperature support must be a nonempty interval")
            if not self.minimum_rate_valid_temperature_K <= self.rate_reference_temperature_K <= self.maximum_rate_valid_temperature_K:
                raise ValueError("Arrhenius reference temperature must lie within declared support")
            if not self.minimum_rate_valid_temperature_K <= self.temperature_K <= self.maximum_rate_valid_temperature_K:
                raise ValueError("target temperature lies outside caller-declared rate support")
        elif self.arrhenius_temperature_scaling_reviewed:
            raise ValueError("Arrhenius scaling review requires its parameters")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("scale-coverage history must start at zero elapsed time")
        ids = [row.interval_id for row in self.intervals]
        if len(ids) != len(set(ids)):
            raise ValueError("scale-coverage interval IDs must be unique")
        if any(right.start_time_s != left.end_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True)):
            raise ValueError("scale-coverage intervals must be contiguous and ordered")
        varying = any(
            row.saturation_ratio_end is not None
            and row.saturation_ratio_end != row.saturation_ratio
            for row in self.intervals
        )
        adaptive = (
            self.maximum_time_step_s, self.minimum_time_step_s,
            self.coverage_absolute_tolerance, self.coverage_relative_tolerance,
            self.inventory_absolute_tolerance, self.inventory_relative_tolerance,
        )
        if varying:
            if not self.linearly_varying_saturation_reviewed:
                raise ValueError("varying saturation requires explicit linear-path review")
            if any(value is None for value in adaptive):
                raise ValueError("varying saturation requires bounded adaptive integration controls")
            if self.minimum_time_step_s > self.maximum_time_step_s:
                raise ValueError("minimum integration step cannot exceed maximum step")
        elif any(value is not None for value in adaptive):
            raise ValueError("adaptive integration controls apply only to varying saturation paths")
        if self.linearly_varying_saturation_reviewed and not varying:
            raise ValueError("linear saturation review is declared without a varying saturation path")
        interval_temperatures = [row.temperature_K for row in self.intervals]
        has_interval_temperatures = any(value is not None for value in interval_temperatures)
        if has_interval_temperatures and any(value is None for value in interval_temperatures):
            raise ValueError("interval temperature must be supplied for every interval or none")
        if has_interval_temperatures and not self.interval_temperature_profile_reviewed:
            raise ValueError("piecewise-constant interval temperatures require explicit profile review")
        if self.interval_temperature_profile_reviewed and not has_interval_temperatures:
            raise ValueError("interval temperature profile review is declared without interval temperatures")
        if has_interval_temperatures:
            declared_temperatures = [float(value) for value in interval_temperatures if value is not None]
            if any(value != self.temperature_K for value in declared_temperatures) and self.rate_reference_temperature_K is None:
                raise ValueError("interval temperatures differing from the target require Arrhenius rate parameters")
            if self.rate_reference_temperature_K is not None and any(
                not self.minimum_rate_valid_temperature_K <= value <= self.maximum_rate_valid_temperature_K
                for value in declared_temperatures
            ):
                raise ValueError("an interval temperature lies outside the caller-declared Arrhenius support")
        return self


def _arrhenius_rate_at_temperature(
    reference_rate_s: float,
    activation_energy_J_mol: float,
    reference_temperature_K: float,
    temperature_K: float,
) -> float:
    if reference_rate_s == 0.0:
        return 0.0
    exponent = -activation_energy_J_mol / _GAS_CONSTANT_J_MOL_K * (
        1.0 / temperature_K - 1.0 / reference_temperature_K
    )
    log_rate = math.log(reference_rate_s) + exponent
    if not math.isfinite(log_rate) or log_rate > math.log(float.fromhex("0x1.fffffffffffffp+1023")):
        raise ArithmeticError("scale coverage rate exceeds finite Arrhenius support")
    if log_rate < math.log(math.ulp(0.0)):
        raise ArithmeticError("scale coverage rate underflows declared Arrhenius support")
    rate = math.exp(log_rate)
    if not math.isfinite(rate) or rate <= 0.0:
        raise ArithmeticError("scale coverage rate exceeds finite Arrhenius support")
    return rate


def caller_scale_coverage_kinetics(x: CallerScaleCoverageKinetics) -> Calculation:
    """Integrate a caller-defined attachment/detachment law exactly per interval.

    Constant interval saturation uses a closed-form update. A caller-reviewed
    linearly varying saturation path uses adaptive RK4 step doubling on coverage
    and cumulative attachment/detachment inventories. This tracks an
    area-average state only; it does not resolve morphology or protection.
    """
    input_digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "physical_scope_id": x.physical_scope_id,
        "substrate_condition_id": x.substrate_condition_id,
        "solution_condition_id": x.solution_condition_id,
        "scale_phase_id": x.scale_phase_id,
        "physical_specimen_id": x.physical_specimen_id,
        "source_group_id": x.source_group_id,
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "source_sha256": x.source_sha256,
        "condition_sha256": x.condition_sha256,
        "kinetic_configuration_sha256": x.kinetic_configuration_sha256,
        "temperature_K": x.temperature_K,
        "input_digest": input_digest,
        "coverage_law": "dθ/dt = attachment_rate*(1-θ) - detachment_rate*θ",
        "attachment_rate_constant_s": x.attachment_rate_constant_s,
        "rate_reference_temperature_K": x.rate_reference_temperature_K,
        "minimum_rate_valid_temperature_K": x.minimum_rate_valid_temperature_K,
        "maximum_rate_valid_temperature_K": x.maximum_rate_valid_temperature_K,
        "attachment_activation_energy_J_mol": x.attachment_activation_energy_J_mol,
        "attachment_supersaturation_order": x.attachment_supersaturation_order,
        "detachment_rate_constant_s": x.detachment_rate_constant_s,
        "detachment_activation_energy_J_mol": x.detachment_activation_energy_J_mol,
        "arrhenius_temperature_scaling_reviewed": x.arrhenius_temperature_scaling_reviewed,
        "interval_temperature_profile_reviewed": x.interval_temperature_profile_reviewed,
        "detachment_undersaturation_order": x.detachment_undersaturation_order,
        "saturation_path_interpolation": (
            "piecewise_linear" if x.linearly_varying_saturation_reviewed else "piecewise_constant"
        ),
        "maximum_time_step_s": x.maximum_time_step_s,
        "minimum_time_step_s": x.minimum_time_step_s,
        "coverage_absolute_tolerance": x.coverage_absolute_tolerance,
        "coverage_relative_tolerance": x.coverage_relative_tolerance,
        "inventory_absolute_tolerance": x.inventory_absolute_tolerance,
        "inventory_relative_tolerance": x.inventory_relative_tolerance,
    }
    varying = any(
        row.saturation_ratio_end is not None and row.saturation_ratio_end != row.saturation_ratio
        for row in x.intervals
    )
    has_constant_interval = any(
        row.saturation_ratio_end is None or row.saturation_ratio_end == row.saturation_ratio
        for row in x.intervals
    )
    reviews = {
        "coverage_kinetic_law_and_standard_state_reviewed": x.coverage_kinetic_law_and_standard_state_reviewed,
        "rate_coefficients_and_temperature_reviewed": x.rate_coefficients_and_temperature_reviewed,
        "scale_phase_identity_and_specimen_match_reviewed": x.scale_phase_identity_and_specimen_match_reviewed,
        "area_average_coverage_representation_reviewed": x.area_average_coverage_representation_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    if has_constant_interval:
        reviews["interval_constant_saturation_reviewed"] = x.interval_constant_saturation_reviewed
    if varying:
        reviews["linearly_varying_saturation_reviewed"] = x.linearly_varying_saturation_reviewed
    if x.interval_temperature_profile_reviewed:
        reviews["interval_temperature_profile_reviewed"] = x.interval_temperature_profile_reviewed
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    try:
        if x.rate_reference_temperature_K is None:
            attachment_rate_constant_s = x.attachment_rate_constant_s
            detachment_rate_constant_s = x.detachment_rate_constant_s
            rate_scaling = "caller_constants_at_declared_temperature"
        else:
            attachment_rate_constant_s = _arrhenius_rate_at_temperature(
                x.attachment_rate_constant_s,
                x.attachment_activation_energy_J_mol,
                x.rate_reference_temperature_K,
                x.temperature_K,
            )
            detachment_rate_constant_s = _arrhenius_rate_at_temperature(
                x.detachment_rate_constant_s,
                x.detachment_activation_energy_J_mol,
                x.rate_reference_temperature_K,
                x.temperature_K,
            )
            rate_scaling = "caller_arrhenius_scaled_from_reference_temperature"
    except ArithmeticError as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error)})
    base |= {
        "effective_attachment_rate_constant_at_temperature_s": attachment_rate_constant_s,
        "effective_detachment_rate_constant_at_temperature_s": detachment_rate_constant_s,
        "rate_temperature_scaling": rate_scaling,
    }

    coverage = x.initial_covered_area_fraction
    history = [{
        "time_s": x.intervals[0].start_time_s,
        "covered_area_fraction": coverage,
        "saturation_ratio_for_next_interval": x.intervals[0].saturation_ratio,
        "saturation_ratio_end_for_next_interval": x.intervals[0].saturation_ratio_end,
        "cumulative_attachment_exposure": 0.0,
        "cumulative_detachment_exposure": 0.0,
    }]
    cumulative_attachment = cumulative_detachment = 0.0
    maximum_balance_residual = 0.0
    rate_evaluations = adaptive_accepted_steps = adaptive_rejected_steps = 0
    adaptive_maximum_error_ratio = 0.0

    def rhs(saturation_ratio: float, state: tuple[float, float, float]) -> tuple[float, float, float]:
        theta, attached, detached = state
        attachment_rate = attachment_rate_constant_s * max(saturation_ratio - 1.0, 0.0) ** x.attachment_supersaturation_order
        detachment_rate = detachment_rate_constant_s * max(1.0 - saturation_ratio, 0.0) ** x.detachment_undersaturation_order
        attachment_flux = attachment_rate * (1.0 - theta)
        detachment_flux = detachment_rate * theta
        return attachment_flux - detachment_flux, attachment_flux, detachment_flux

    def rk4_path_step(start_state: tuple[float, float, float], position: float, step: float,
                      duration: float, saturation_start: float, saturation_end: float):
        nonlocal rate_evaluations
        def evaluate(offset: float, state: tuple[float, float, float]):
            nonlocal rate_evaluations
            if not -1e-12 <= state[0] <= 1.0 + 1e-12:
                raise ArithmeticError("coverage_kinetics_intermediate_state_left_bounds")
            u = min(1.0, max(0.0, (position + offset) / duration))
            saturation = saturation_start + u * (saturation_end - saturation_start)
            rate_evaluations += 1
            return rhs(saturation, state)
        k1 = evaluate(0.0, start_state)
        k2 = evaluate(0.5 * step, tuple(y + 0.5 * step * k for y, k in zip(start_state, k1, strict=True)))
        k3 = evaluate(0.5 * step, tuple(y + 0.5 * step * k for y, k in zip(start_state, k2, strict=True)))
        k4 = evaluate(step, tuple(y + step * k for y, k in zip(start_state, k3, strict=True)))
        return tuple(
            y + step * (a + 2.0 * b + 2.0 * c + d) / 6.0
            for y, a, b, c, d in zip(start_state, k1, k2, k3, k4, strict=True)
        )

    try:
        for interval in x.intervals:
            saturation = interval.saturation_ratio
            saturation_end = saturation if interval.saturation_ratio_end is None else interval.saturation_ratio_end
            dt = interval.end_time_s - interval.start_time_s
            interval_temperature = x.temperature_K if interval.temperature_K is None else interval.temperature_K
            if x.rate_reference_temperature_K is None:
                interval_attachment_rate_constant_s = x.attachment_rate_constant_s
                interval_detachment_rate_constant_s = x.detachment_rate_constant_s
            else:
                interval_attachment_rate_constant_s = _arrhenius_rate_at_temperature(
                    x.attachment_rate_constant_s,
                    x.attachment_activation_energy_J_mol,
                    x.rate_reference_temperature_K,
                    interval_temperature,
                )
                interval_detachment_rate_constant_s = _arrhenius_rate_at_temperature(
                    x.detachment_rate_constant_s,
                    x.detachment_activation_energy_J_mol,
                    x.rate_reference_temperature_K,
                    interval_temperature,
                )
            attachment_rate_constant_s = interval_attachment_rate_constant_s
            detachment_rate_constant_s = interval_detachment_rate_constant_s
            varying = saturation_end != saturation
            if varying:
                initial_state = (coverage, 0.0, 0.0)
                state = initial_state
                position = 0.0
                step_size = min(x.maximum_time_step_s, dt)
                rejected_this_interval = 0
                accepted_before, rejected_before = adaptive_accepted_steps, adaptive_rejected_steps
                while position < dt:
                    remaining = dt - position
                    step = min(step_size, remaining)
                    if rate_evaluations + 12 > x.maximum_rate_evaluations:
                        raise ArithmeticError("coverage_kinetics_rate_evaluation_budget_exceeded")
                    try:
                        full = rk4_path_step(state, position, step, dt, saturation, saturation_end)
                        half = rk4_path_step(state, position, 0.5 * step, dt, saturation, saturation_end)
                        doubled = rk4_path_step(half, position + 0.5 * step, 0.5 * step, dt, saturation, saturation_end)
                    except ArithmeticError as error:
                        if str(error) != "coverage_kinetics_intermediate_state_left_bounds":
                            raise
                        adaptive_rejected_steps += 1
                        rejected_this_interval += 1
                        if rejected_this_interval > x.maximum_rejected_steps_per_interval or step <= x.minimum_time_step_s:
                            raise ArithmeticError("coverage_kinetics_bounds_unresolved_at_minimum_step") from error
                        step_size = max(x.minimum_time_step_s, 0.5 * step)
                        continue
                    errors = tuple(abs(b - a) / 15.0 for a, b in zip(full, doubled, strict=True))
                    scales = (
                        x.coverage_absolute_tolerance + x.coverage_relative_tolerance * max(abs(state[0]), abs(doubled[0])),
                        x.inventory_absolute_tolerance + x.inventory_relative_tolerance * max(abs(state[1]), abs(doubled[1])),
                        x.inventory_absolute_tolerance + x.inventory_relative_tolerance * max(abs(state[2]), abs(doubled[2])),
                    )
                    error_ratio = max(error / scale for error, scale in zip(errors, scales, strict=True))
                    if not math.isfinite(error_ratio) or not all(math.isfinite(value) for value in doubled):
                        raise ArithmeticError("coverage_kinetics_adaptive_state_exceeded_finite_support")
                    if doubled[0] < 0.0 or doubled[0] > 1.0:
                        error_ratio = max(error_ratio, 2.0)
                    adaptive_maximum_error_ratio = max(adaptive_maximum_error_ratio, error_ratio)
                    if error_ratio <= 1.0:
                        state = doubled
                        position = dt if step == remaining else position + step
                        adaptive_accepted_steps += 1
                        factor = 5.0 if error_ratio == 0.0 else min(5.0, max(0.2, 0.9 * error_ratio ** -0.2))
                        step_size = min(x.maximum_time_step_s, max(x.minimum_time_step_s, step * factor))
                    else:
                        adaptive_rejected_steps += 1
                        rejected_this_interval += 1
                        if rejected_this_interval > x.maximum_rejected_steps_per_interval or step <= x.minimum_time_step_s:
                            raise ArithmeticError("coverage_kinetics_adaptive_tolerance_unresolved_at_minimum_step")
                        step_size = max(x.minimum_time_step_s, step * max(0.1, min(0.8, 0.9 * error_ratio ** -0.2)))
                coverage = state[0]
                attachment_increment = state[1]
                detachment_increment = state[2]
                cumulative_attachment += attachment_increment
                cumulative_detachment += detachment_increment
                interval_balance_residual = (coverage - initial_state[0]) - (attachment_increment - detachment_increment)
                attachment = attachment_increment / dt
                detachment = detachment_increment / dt
                accepted_this_interval = adaptive_accepted_steps - accepted_before
                rejected_this_interval = adaptive_rejected_steps - rejected_before
            else:
                attachment = attachment_rate_constant_s * max(saturation - 1.0, 0.0) ** x.attachment_supersaturation_order
                detachment = detachment_rate_constant_s * max(1.0 - saturation, 0.0) ** x.detachment_undersaturation_order
                accepted_this_interval = rejected_this_interval = 0
                total_rate = attachment + detachment
                if total_rate == 0.0:
                    next_coverage = coverage
                    integrated_coverage = coverage * dt
                else:
                    equilibrium_coverage = attachment / total_rate
                    exponential_integral = -math.expm1(-total_rate * dt) / total_rate
                    next_coverage = equilibrium_coverage + (coverage - equilibrium_coverage) * math.exp(-total_rate * dt)
                    integrated_coverage = equilibrium_coverage * dt + (coverage - equilibrium_coverage) * exponential_integral
                attachment_increment = attachment * (dt - integrated_coverage)
                detachment_increment = detachment * integrated_coverage
                interval_balance_residual = (next_coverage - coverage) - (attachment_increment - detachment_increment)
                cumulative_attachment += attachment_increment
                cumulative_detachment += detachment_increment
                values = (attachment, detachment, next_coverage, cumulative_attachment, cumulative_detachment, interval_balance_residual)
                if not all(math.isfinite(value) for value in values):
                    raise ArithmeticError("coverage kinetic state exceeded finite numeric support")
                if not -1e-14 <= next_coverage <= 1.0 + 1e-14:
                    raise ArithmeticError("coverage kinetic state left [0, 1] bounds")
                coverage = min(max(next_coverage, 0.0), 1.0)
                interval_balance_residual = (coverage - history[-1]["covered_area_fraction"]) - (attachment_increment - detachment_increment)
            if not 0.0 <= coverage <= 1.0 or not all(math.isfinite(value) for value in (
                coverage, cumulative_attachment, cumulative_detachment, interval_balance_residual
            )):
                raise ArithmeticError("coverage kinetic state left [0, 1] bounds")
            balance_scale = max(
                1.0, abs(coverage), abs(attachment_increment), abs(detachment_increment)
            )
            closure_operations = max(1, accepted_this_interval)
            if abs(interval_balance_residual) > 64.0 * closure_operations * math.ulp(balance_scale):
                raise ArithmeticError("coverage inventory balance exceeds floating-point closure tolerance")
            maximum_balance_residual = max(maximum_balance_residual, abs(interval_balance_residual))
            history.append({
                "time_s": interval.end_time_s,
                "interval_id": interval.interval_id,
                "temperature_K": interval_temperature,
                "attachment_rate_constant_s": interval_attachment_rate_constant_s,
                "detachment_rate_constant_s": interval_detachment_rate_constant_s,
                "saturation_ratio": saturation,
                "saturation_ratio_end": saturation_end,
                "attachment_rate_s": attachment,
                "detachment_rate_s": detachment,
                "covered_area_fraction": coverage,
                "cumulative_attachment_exposure": cumulative_attachment,
                "cumulative_detachment_exposure": cumulative_detachment,
                "interval_coverage_balance_residual": interval_balance_residual,
                "adaptive_accepted_steps": accepted_this_interval,
                "adaptive_rejected_steps": rejected_this_interval,
            })
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error),
            "computed_prefix": history,
        })

    cumulative_balance_residual = coverage - x.initial_covered_area_fraction - (
        cumulative_attachment - cumulative_detachment
    )
    cumulative_balance_scale = max(
        1.0, abs(coverage), abs(cumulative_attachment), abs(cumulative_detachment)
    )
    closure_operations = max(1, adaptive_accepted_steps + len(x.intervals))
    if not math.isfinite(cumulative_balance_residual) or abs(cumulative_balance_residual) > (
        64.0 * closure_operations * math.ulp(cumulative_balance_scale)
    ):
        return Calculation(status="out_of_scope", values=base | {
            "computed_prefix": history,
            "out_of_scope_reason": "cumulative coverage inventory balance exceeds floating-point closure tolerance",
            "cumulative_coverage_balance_residual": cumulative_balance_residual,
            "adaptive_rate_evaluation_count": rate_evaluations,
        })
    return Calculation(values=base | {
        "initial_covered_area_fraction": x.initial_covered_area_fraction,
        "final_covered_area_fraction": coverage,
        "maximum_absolute_coverage_balance_residual": maximum_balance_residual,
        "adaptive_rate_evaluation_count": rate_evaluations,
        "maximum_rate_evaluations": x.maximum_rate_evaluations,
        "adaptive_accepted_steps": adaptive_accepted_steps,
        "adaptive_rejected_steps": adaptive_rejected_steps,
        "adaptive_maximum_error_ratio": adaptive_maximum_error_ratio,
        "cumulative_coverage_balance_residual": cumulative_balance_residual,
        "scale_history": history,
        "interval_rate_temperature_interpretation": (
            "caller_reviewed_piecewise_constant_per_interval"
            if x.interval_temperature_profile_reviewed else "single_declared_temperature"
        ),
        "interval_saturation_interpretation": (
            "caller_supplied_piecewise_linear_path" if x.linearly_varying_saturation_reviewed
            else "caller_supplied_constant_per_interval"
        ),
        "coverage_integrator": (
            "closed_form_constant_saturation_with_adaptive_RK4_for_varying_saturation"
        ),
    }, notes=(
        "The result is an area-average coverage state from the explicitly caller-defined attachment/detachment law; reviewed interval temperatures select a constant Arrhenius rate within each interval.",
        "No scale thickness, phase discovery, nucleation model, morphology, porosity, adhesion, effective diffusivity, corrosion protection or scale-to-substrate transfer is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.caller_scale_coverage_kinetics",
        CallerScaleCoverageKinetics,
        caller_scale_coverage_kinetics,
        {
            "temperature_K": "K",
            "scale_history[].temperature_K": "K",
            "scale_history[].attachment_rate_constant_s": "1/s",
            "scale_history[].detachment_rate_constant_s": "1/s",
            "attachment_rate_constant_s": "1/s",
            "effective_attachment_rate_constant_at_temperature_s": "1/s",
            "rate_reference_temperature_K": "K",
            "minimum_rate_valid_temperature_K": "K",
            "maximum_rate_valid_temperature_K": "K",
            "attachment_activation_energy_J_mol": "J/mol",
            "detachment_rate_constant_s": "1/s",
            "effective_detachment_rate_constant_at_temperature_s": "1/s",
            "detachment_activation_energy_J_mol": "J/mol",
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].saturation_ratio": "1",
            "intervals[].saturation_ratio_end": "1",
            "maximum_time_step_s": "s",
            "minimum_time_step_s": "s",
            "coverage_absolute_tolerance": "1",
            "coverage_relative_tolerance": "1",
            "inventory_absolute_tolerance": "1",
            "inventory_relative_tolerance": "1",
            "initial_covered_area_fraction": "1",
            "final_covered_area_fraction": "1",
            "maximum_absolute_coverage_balance_residual": "1",
            "cumulative_coverage_balance_residual": "1",
            "scale_history[].time_s": "s",
            "scale_history[].saturation_ratio_for_next_interval": "1",
            "scale_history[].saturation_ratio_end_for_next_interval": "1",
            "scale_history[].saturation_ratio": "1",
            "scale_history[].saturation_ratio_end": "1",
            "scale_history[].attachment_rate_s": "1/s",
            "scale_history[].detachment_rate_s": "1/s",
            "scale_history[].covered_area_fraction": "1",
            "scale_history[].cumulative_attachment_exposure": "1",
            "scale_history[].cumulative_detachment_exposure": "1",
            "scale_history[].interval_coverage_balance_residual": "1",
            "scale_history[].adaptive_accepted_steps": "1",
            "scale_history[].adaptive_rejected_steps": "1",
            "adaptive_maximum_error_ratio": "1",
            "adaptive_rate_evaluation_count": "1",
            "maximum_rate_evaluations": "1",
            "adaptive_accepted_steps": "1",
            "adaptive_rejected_steps": "1",
        },
        (
            "A caller-supplied first-order surface-coverage attachment/detachment law uses a closed-form solution for constant saturation and adaptive RK4 step doubling for reviewed piecewise-linear saturation paths.",
            "Optional caller-supplied Arrhenius activation energies scale both reference rate constants only inside the declared absolute-temperature support. The output is an area-average coverage variable; rate-law calibration, morphology and any protective effect remain caller-owned.",
        ),
        ("caller_scale_coverage_attachment_detachment_law", "arrhenius_kinetics"),
        qualification="user_model",
    )]
