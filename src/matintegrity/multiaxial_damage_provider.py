"""Integrate caller-owned path-sensitive multiaxial fatigue damage-rate providers."""

from __future__ import annotations

import math
from numbers import Real
from collections.abc import Callable, Mapping
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest
from .models.multiaxial_work_life import (
    ClosedTensorCycle,
    _cycle_pchip_coefficients,
    _cycle_periodic_spline_coefficients,
    _pchip_slopes,
)


class MultiaxialFatigueLawProfile(Contract):
    """Evidence-linked material-law support envelope for one provider revision."""

    law_id: str = Field(min_length=1)
    law_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_condition_id: str = Field(min_length=1)
    stress_measure_id: str = Field(min_length=1)
    stress_unit: Literal["Pa"]
    stress_component_order: tuple[str, ...] = Field(min_length=6, max_length=6)
    strain_measure_id: str = Field(min_length=1)
    strain_unit: Literal["dimensionless"]
    strain_shear_convention: Literal["tensor", "engineering"]
    stress_component_minimum_Pa: tuple[float, ...] = Field(min_length=6, max_length=6)
    stress_component_maximum_Pa: tuple[float, ...] = Field(min_length=6, max_length=6)
    strain_component_minimum: tuple[float, ...] = Field(min_length=6, max_length=6)
    strain_component_maximum: tuple[float, ...] = Field(min_length=6, max_length=6)
    minimum_cycle_duration_s: Positive
    maximum_cycle_duration_s: Positive
    minimum_cycle_count: int = Field(ge=1)
    maximum_cycle_count: int = Field(ge=1)
    minimum_allocated_repetitions: Positive
    maximum_allocated_repetitions: Positive
    supported_time_reconstructions: tuple[
        Literal["piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"], ...
    ] = Field(min_length=1, max_length=4)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    tensor_order_and_measurement_definition_reviewed: bool
    calibration_support_and_transfer_reviewed: bool
    material_condition_match_reviewed: bool
    cycle_population_scope_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def valid_support(self):
        if self.stress_component_order != ("xx", "yy", "zz", "xy", "yz", "zx"):
            raise ValueError("tensor component order must be [xx, yy, zz, xy, yz, zx]")
        if len(set(self.supported_time_reconstructions)) != len(self.supported_time_reconstructions):
            raise ValueError("supported time reconstructions must be unique")
        if self.maximum_cycle_duration_s < self.minimum_cycle_duration_s:
            raise ValueError("cycle-duration support is reversed")
        if self.maximum_cycle_count < self.minimum_cycle_count:
            raise ValueError("cycle-count support is reversed")
        if self.maximum_allocated_repetitions < self.minimum_allocated_repetitions:
            raise ValueError("allocated repetition support is reversed")
        bounds = (
            self.stress_component_minimum_Pa, self.stress_component_maximum_Pa,
            self.strain_component_minimum, self.strain_component_maximum,
        )
        if any(not math.isfinite(value) for values in bounds for value in values):
            raise ValueError("provider stress/strain support bounds must be finite")
        if any(lo > hi for lo, hi in zip(self.stress_component_minimum_Pa, self.stress_component_maximum_Pa, strict=True)):
            raise ValueError("each stress component requires ordered calibration bounds")
        if any(lo > hi for lo, hi in zip(self.strain_component_minimum, self.strain_component_maximum, strict=True)):
            raise ValueError("each strain component requires ordered calibration bounds")
        if not any(row.source_id == self.provider_id and row.sha256 == self.calibration_sha256 for row in self.evidence):
            raise ValueError("calibration digest must match Evidence attributed to the declared provider")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must carry the declared license or rights identifier")
        if not all((self.tensor_order_and_measurement_definition_reviewed,
                    self.calibration_support_and_transfer_reviewed,
                    self.material_condition_match_reviewed, self.cycle_population_scope_reviewed,
                    self.usage_rights_reviewed, self.computational_use_authorized)):
            raise ValueError("all law support, material, population, rights and use reviews are required")
        return self


class QualifiedMultiaxialFatigueProvider:
    """Fail-closed runtime wrapper applying a reviewed law profile to callback samples."""

    def __init__(self, request, provider, profile: MultiaxialFatigueLawProfile):
        if not callable(provider):
            raise TypeError("underlying fatigue law provider must be callable")
        expected = (profile.provider_id, profile.provider_revision, profile.provider_configuration_sha256)
        actual = (getattr(provider, "provider_id", None), getattr(provider, "revision", None),
                  getattr(provider, "configuration_sha256", None))
        if actual != expected:
            raise ValueError("fatigue provider identity/revision/configuration differs from the reviewed profile")
        if (request.material_condition_id != profile.material_condition_id
                or request.calibration_id != profile.calibration_id
                or request.calibration_sha256 != profile.calibration_sha256
                or request.damage_provider_id != profile.provider_id
                or request.damage_provider_revision != profile.provider_revision
                or request.damage_provider_configuration_sha256 != profile.provider_configuration_sha256
                or request.strain_shear_convention != profile.strain_shear_convention
                or request.time_reconstruction not in profile.supported_time_reconstructions):
            raise ValueError("fatigue analysis metadata is outside the reviewed law profile")
        if not profile.minimum_cycle_count <= len(request.cycles) <= profile.maximum_cycle_count:
            raise ValueError("cycle count is outside the reviewed material-law population support")
        repetitions = math.fsum(cycle.allocated_cycle_count for cycle in request.cycles)
        if not profile.minimum_allocated_repetitions <= repetitions <= profile.maximum_allocated_repetitions:
            raise ValueError("allocated repetitions are outside the reviewed law support")
        for cycle in request.cycles:
            if cycle.sample_time_s is None:
                raise ValueError("profile binding requires time-resolved cycle histories")
            duration = cycle.sample_time_s[-1] - cycle.sample_time_s[0]
            if not profile.minimum_cycle_duration_s <= duration <= profile.maximum_cycle_duration_s:
                raise ValueError(f"cycle {cycle.cycle_id} duration is outside provider support")
        self._provider = provider
        self._profile = profile
        self.provider_id = profile.provider_id
        self.revision = profile.provider_revision
        self.configuration_sha256 = profile.provider_configuration_sha256
        self.law_profile_sha256 = canonical_digest({
            "law_id": profile.law_id,
            "law_revision": profile.law_revision,
            "profile": profile.model_dump(mode="json"),
        })
        self.source_configuration_sha256 = profile.provider_configuration_sha256
        self.calibration_sha256 = profile.calibration_sha256
        self.law_profile = profile.model_dump(mode="json")

    def __call__(self, *args):
        if len(args) not in (6, 7):
            raise TypeError("expected memoryless or stateful multiaxial callback arguments")
        stress, strain, context = args[1], args[2], args[-1]
        profile = self._profile
        if context.get("material_condition_id") != profile.material_condition_id:
            raise ValueError("provider callback material condition differs from the reviewed profile")
        if context.get("strain_shear_convention") != profile.strain_shear_convention:
            raise ValueError("provider callback strain convention differs from the reviewed profile")
        for label, values, lower, upper in (
            ("stress", stress, profile.stress_component_minimum_Pa, profile.stress_component_maximum_Pa),
            ("strain", strain, profile.strain_component_minimum, profile.strain_component_maximum),
        ):
            if len(values) != 6 or any(not math.isfinite(value) or value < lo or value > hi
                                       for value, lo, hi in zip(values, lower, upper, strict=True)):
                raise ValueError(f"reconstructed {label} state is outside the reviewed material-law envelope")
        identity = (getattr(self._provider, "provider_id", None), getattr(self._provider, "revision", None),
                    getattr(self._provider, "configuration_sha256", None))
        expected = (profile.provider_id, profile.provider_revision, profile.provider_configuration_sha256)
        if identity != expected:
            raise ValueError("underlying provider identity changed after profile binding")
        return self._provider(*args)


def bind_qualified_multiaxial_fatigue_provider(request, provider, profile):
    """Bind a calibrated callback to explicit material and path applicability support."""
    if not isinstance(profile, MultiaxialFatigueLawProfile):
        profile = MultiaxialFatigueLawProfile.model_validate(profile)
    return QualifiedMultiaxialFatigueProvider(request, provider, profile)


def bind_caller_multiaxial_material_law(request, provider, profile):
    """Public adapter alias for binding either damage integrator to a law profile."""
    return bind_qualified_multiaxial_fatigue_provider(request, provider, profile)


class CallerMultiaxialDamageRequest(Contract):
    """Lineage, cycle histories and numerical controls for a caller damage provider."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    cycles: tuple[ClosedTensorCycle, ...] = Field(min_length=1, max_length=10000)
    strain_shear_convention: Literal["tensor", "engineering"]
    time_reconstruction: Literal["piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"]
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    damage_provider_id: str = Field(min_length=1)
    damage_provider_revision: str = Field(min_length=1)
    damage_provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_closure_stress_error_Pa: Nonnegative
    maximum_closure_strain_error: Nonnegative
    maximum_closure_stress_rate_error_Pa_s: Nonnegative | None = None
    maximum_closure_strain_rate_error_s_inv: Nonnegative | None = None
    quadrature_absolute_tolerance_damage: Positive = 1e-10
    quadrature_relative_tolerance: Positive = 1e-6
    initial_subinterval_count: int = Field(default=1, ge=1, le=128)
    maximum_subinterval_count: int = Field(default=1024, ge=2, le=8192)
    maximum_provider_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    quadrature_order: Literal[4, 8, 16] = 8
    tensor_basis_and_order_reviewed: bool
    stress_strain_conjugacy_reviewed: bool
    cycle_extraction_and_closure_reviewed: bool
    time_reconstruction_reviewed: bool
    periodic_spline_reviewed: bool = False
    provider_material_applicability_reviewed: bool
    provider_usage_rights_reviewed: bool
    memoryless_deterministic_rate_reviewed: bool

    @model_validator(mode="after")
    def coherent_path_contract(self):
        if self.maximum_subinterval_count <= self.initial_subinterval_count:
            raise ValueError("maximum quadrature subdivision count must exceed its initial count")
        declared_numeric = (
            self.maximum_closure_stress_error_Pa,
            self.maximum_closure_strain_error,
            self.quadrature_absolute_tolerance_damage,
            self.quadrature_relative_tolerance,
            *(
                value
                for value in (
                    self.maximum_closure_stress_rate_error_Pa_s,
                    self.maximum_closure_strain_rate_error_s_inv,
                )
                if value is not None
            ),
        )
        if any(not math.isfinite(value) for value in declared_numeric):
            raise ValueError("closure limits and quadrature tolerances must be finite")
        if len({cycle.cycle_id for cycle in self.cycles}) != len(self.cycles):
            raise ValueError("cycle IDs must be unique")
        for cycle in self.cycles:
            if cycle.sample_time_s is None:
                raise ValueError("time-resolved cycles are required by the damage-rate integral")
            data = [
                *cycle.sample_time_s,
                cycle.allocated_cycle_count,
                *(value for row in cycle.stress_tensor_components_Pa for value in row),
                *(value for row in cycle.strain_tensor_components for value in row),
            ]
            for history in (cycle.stress_time_derivative_components_Pa_s, cycle.strain_time_derivative_components_s_inv):
                if history is not None:
                    data.extend(value for row in history for value in row)
            if any(isinstance(value, bool) or not math.isfinite(value) for value in data):
                raise ValueError("cycle samples, times, derivatives and allocated counts must be finite numeric values")
            if self.time_reconstruction == "piecewise_cubic_hermite":
                if cycle.stress_time_derivative_components_Pa_s is None or cycle.strain_time_derivative_components_s_inv is None:
                    raise ValueError("cubic Hermite reconstruction requires both derivative histories")
                if (
                    self.maximum_closure_stress_rate_error_Pa_s is None
                    or self.maximum_closure_strain_rate_error_s_inv is None
                ):
                    raise ValueError("cubic Hermite reconstruction requires caller-reviewed stress and strain rate closure limits")
            elif self.time_reconstruction == "piecewise_pchip":
                if cycle.stress_time_derivative_components_Pa_s is not None:
                    raise ValueError("PCHIP derives its own slopes and cannot accept supplied derivatives")
                if self.maximum_closure_stress_rate_error_Pa_s is None or self.maximum_closure_strain_rate_error_s_inv is None:
                    raise ValueError("PCHIP reconstruction requires caller-reviewed stress and strain rate closure limits")
            elif self.time_reconstruction == "piecewise_periodic_cubic_spline":
                if cycle.stress_time_derivative_components_Pa_s is not None:
                    raise ValueError("periodic cubic spline derives its own slopes and cannot accept supplied derivatives")
                if cycle.stress_tensor_components_Pa[0] != cycle.stress_tensor_components_Pa[-1] or cycle.strain_tensor_components[0] != cycle.strain_tensor_components[-1]:
                    raise ValueError("periodic cubic spline requires exactly matching first and last stress/strain samples")
                if self.maximum_closure_stress_rate_error_Pa_s is None or self.maximum_closure_strain_rate_error_s_inv is None:
                    raise ValueError("periodic cubic spline requires caller-reviewed stress and strain rate closure limits")
            elif self.time_reconstruction == "piecewise_linear" and (cycle.stress_time_derivative_components_Pa_s is not None or cycle.strain_time_derivative_components_s_inv is not None):
                raise ValueError("derivative histories require cubic Hermite reconstruction")
        if self.time_reconstruction not in {"piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"} and (
            self.maximum_closure_stress_rate_error_Pa_s is not None
            or self.maximum_closure_strain_rate_error_s_inv is not None
        ):
            raise ValueError("rate-closure limits apply only to cubic-Hermite, PCHIP or periodic cubic-spline reconstruction")
        if self.time_reconstruction == "piecewise_periodic_cubic_spline" and not self.periodic_spline_reviewed:
            raise ValueError("periodic cubic spline requires explicit caller review")
        return self


class CallerStatefulMultiaxialDamageRequest(Contract):
    """Ordered tensor cycles and bounded state for an externally calibrated rate law."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    cycles: tuple[ClosedTensorCycle, ...] = Field(min_length=1, max_length=10000)
    state_variable_ids: tuple[str, ...] = Field(min_length=1, max_length=64)
    initial_state: tuple[float, ...] = Field(min_length=1, max_length=64)
    minimum_state: tuple[float, ...] = Field(min_length=1, max_length=64)
    maximum_state: tuple[float, ...] = Field(min_length=1, max_length=64)
    strain_shear_convention: Literal["tensor", "engineering"]
    time_reconstruction: Literal["piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"]
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    damage_provider_id: str = Field(min_length=1)
    damage_provider_revision: str = Field(min_length=1)
    damage_provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    integration_method: Literal["fixed_step_rk4", "adaptive_step_doubling_rk4"] = "fixed_step_rk4"
    maximum_time_step_s: Positive
    minimum_time_step_s: Positive | None = None
    state_absolute_tolerance: Positive | None = None
    state_relative_tolerance: Positive | None = None
    damage_absolute_tolerance: Positive | None = None
    damage_relative_tolerance: Positive | None = None
    maximum_rejected_steps_per_interval: int = Field(default=1000, ge=0, le=100000)
    maximum_rejection_history_records: int = Field(default=10000, ge=0, le=100000)
    maximum_provider_evaluations: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_closure_stress_error_Pa: Nonnegative
    maximum_closure_strain_error: Nonnegative
    maximum_closure_stress_rate_error_Pa_s: Nonnegative | None = None
    maximum_closure_strain_rate_error_s_inv: Nonnegative | None = None
    tensor_basis_and_order_reviewed: bool
    stress_strain_conjugacy_reviewed: bool
    cycle_extraction_and_sequence_order_reviewed: bool
    time_reconstruction_reviewed: bool
    periodic_spline_reviewed: bool = False
    state_initialization_and_bounds_reviewed: bool
    provider_material_applicability_reviewed: bool
    provider_usage_rights_reviewed: bool
    stateful_rate_and_evolution_law_reviewed: bool
    adaptive_integration_controls_reviewed: bool = False
    provider_repeat_evaluation_is_deterministic_reviewed: bool = False
    periodic_state_absolute_tolerance: Positive | None = None
    periodic_state_relative_tolerance: float | None = Field(default=None, ge=0.0, le=1.0)
    periodic_state_convergence_reviewed: bool = False
    cycle_exchange_receipt_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    cycle_block_order_ids: tuple[str, ...] | None = Field(default=None, min_length=1, max_length=10000)
    cycle_exchange_clock_id: str | None = Field(default=None, min_length=1)
    cycle_exchange_provider_id: str | None = Field(default=None, min_length=1)
    cycle_exchange_provider_revision: str | None = Field(default=None, min_length=1)
    cycle_exchange_provider_run_id: str | None = Field(default=None, min_length=1)
    cycle_exchange_provider_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    cycle_source_initial_state_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    cycle_source_terminal_state_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_state_path(self):
        exchange_fields = (
            self.cycle_exchange_receipt_sha256,
            self.cycle_block_order_ids,
            self.cycle_exchange_clock_id,
            self.cycle_exchange_provider_id,
            self.cycle_exchange_provider_revision,
            self.cycle_exchange_provider_run_id,
            self.cycle_exchange_provider_result_sha256,
            self.cycle_source_initial_state_sha256,
            self.cycle_source_terminal_state_sha256,
        )
        if any(value is not None for value in exchange_fields):
            if any(value is None for value in exchange_fields):
                raise ValueError("cycle exchange receipt requires block order and both material-state identity endpoints")
            if len(set(self.cycle_block_order_ids or ())) != len(self.cycle_block_order_ids or ()):
                raise ValueError("cycle exchange block IDs must be unique")
        finite_controls = (
            self.maximum_time_step_s,
            self.maximum_closure_stress_error_Pa,
            self.maximum_closure_strain_error,
            *(
                value for value in (
                    self.minimum_time_step_s, self.state_absolute_tolerance,
                    self.state_relative_tolerance, self.damage_absolute_tolerance,
                    self.damage_relative_tolerance, self.maximum_closure_stress_rate_error_Pa_s,
                    self.maximum_closure_strain_rate_error_s_inv,
                    self.periodic_state_absolute_tolerance, self.periodic_state_relative_tolerance,
                ) if value is not None
            ),
        )
        if any(not math.isfinite(value) for value in finite_controls):
            raise ValueError("stateful damage integration controls and closure limits must be finite")
        adaptive_controls = (
            self.minimum_time_step_s,
            self.state_absolute_tolerance,
            self.state_relative_tolerance,
            self.damage_absolute_tolerance,
            self.damage_relative_tolerance,
        )
        if self.integration_method == "adaptive_step_doubling_rk4":
            if any(value is None for value in adaptive_controls):
                raise ValueError("adaptive RK4 requires minimum step and all state/damage absolute-relative tolerances")
            if self.minimum_time_step_s > self.maximum_time_step_s:
                raise ValueError("minimum adaptive step cannot exceed the maximum time step")
            if not self.adaptive_integration_controls_reviewed or not self.provider_repeat_evaluation_is_deterministic_reviewed:
                raise ValueError("adaptive step doubling requires reviewed controls and deterministic repeatable provider evaluation")
        elif any(value is not None for value in adaptive_controls):
            raise ValueError("adaptive tolerances and minimum step apply only to adaptive RK4")
        count = len(self.state_variable_ids)
        if len(set(self.state_variable_ids)) != count:
            raise ValueError("state variable IDs must be unique")
        if any(len(values) != count for values in (self.initial_state, self.minimum_state, self.maximum_state)):
            raise ValueError("initial state and bounds must align with state variable IDs")
        if any(not math.isfinite(value) for values in (self.initial_state, self.minimum_state, self.maximum_state) for value in values):
            raise ValueError("state values and bounds must be finite")
        if any(lo >= hi or initial < lo or initial > hi for initial, lo, hi in zip(self.initial_state, self.minimum_state, self.maximum_state, strict=True)):
            raise ValueError("initial state must lie inside strictly ordered caller bounds")
        if len({cycle.cycle_id for cycle in self.cycles}) != len(self.cycles):
            raise ValueError("cycle IDs must be unique and their tuple order is the declared sequence")
        has_repeated_path = False
        minimum_evaluations = 0
        for cycle in self.cycles:
            if cycle.sample_time_s is None:
                raise ValueError("time-resolved cycles are required for stateful damage integration")
            count_value = cycle.allocated_cycle_count
            if not math.isfinite(count_value) or count_value < 1 or count_value != math.floor(count_value):
                raise ValueError("stateful sequence cycles require finite positive integer repetitions")
            has_repeated_path = has_repeated_path or count_value >= 2
            time_values = tuple(cycle.sample_time_s)
            path_values = (
                *time_values,
                *(value for row in cycle.stress_tensor_components_Pa for value in row),
                *(value for row in cycle.strain_tensor_components for value in row),
                *(
                    value for history in (
                        cycle.stress_time_derivative_components_Pa_s,
                        cycle.strain_time_derivative_components_s_inv,
                    ) if history is not None for row in history for value in row
                ),
            )
            if any(not math.isfinite(value) for value in path_values):
                raise ValueError("stateful damage cycle paths and derivative histories must be finite")
            evaluations_per_step = 4 if self.integration_method == "fixed_step_rk4" else 12
            minimum_steps = 0
            for left, right in zip(time_values[:-1], time_values[1:], strict=True):
                ratio = (right - left) / self.maximum_time_step_s
                if not math.isfinite(ratio):
                    raise ValueError("cycle-path resolution exceeds finite numeric support")
                minimum_steps += max(1, math.ceil(ratio)) if self.integration_method == "fixed_step_rk4" else 1
            minimum_evaluations += int(count_value) * minimum_steps * evaluations_per_step
            if self.time_reconstruction == "piecewise_cubic_hermite":
                if cycle.stress_time_derivative_components_Pa_s is None or cycle.strain_time_derivative_components_s_inv is None:
                    raise ValueError("cubic-Hermite reconstruction requires times and both derivative histories")
            elif self.time_reconstruction == "piecewise_linear" and cycle.stress_time_derivative_components_Pa_s is not None:
                raise ValueError("piecewise-linear reconstruction cannot include cubic derivative histories")
            elif self.time_reconstruction == "piecewise_pchip" and cycle.stress_time_derivative_components_Pa_s is not None:
                raise ValueError("PCHIP derives its own slopes and cannot accept supplied derivatives")
            elif self.time_reconstruction == "piecewise_periodic_cubic_spline":
                if cycle.stress_time_derivative_components_Pa_s is not None:
                    raise ValueError("periodic cubic spline derives its own slopes and cannot accept supplied derivatives")
                if cycle.stress_tensor_components_Pa[0] != cycle.stress_tensor_components_Pa[-1] or cycle.strain_tensor_components[0] != cycle.strain_tensor_components[-1]:
                    raise ValueError("periodic cubic spline requires exactly matching first and last stress/strain samples")
        if self.time_reconstruction in {"piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"}:
            if self.maximum_closure_stress_rate_error_Pa_s is None or self.maximum_closure_strain_rate_error_s_inv is None:
                raise ValueError("cubic time reconstruction requires explicit derivative closure tolerances")
        if self.time_reconstruction == "piecewise_periodic_cubic_spline":
            if not self.periodic_spline_reviewed:
                raise ValueError("periodic cubic spline requires explicit caller review")
        elif self.maximum_closure_stress_rate_error_Pa_s is not None or self.maximum_closure_strain_rate_error_s_inv is not None:
            raise ValueError("derivative closure tolerances apply only to cubic-Hermite or PCHIP reconstruction")
        periodic_tolerances = (
            self.periodic_state_absolute_tolerance,
            self.periodic_state_relative_tolerance,
        )
        if any(value is not None for value in periodic_tolerances):
            if any(value is None for value in periodic_tolerances):
                raise ValueError("periodic-state diagnostics require both absolute and relative tolerances")
            if not self.periodic_state_convergence_reviewed or not has_repeated_path:
                raise ValueError("periodic-state tolerance reporting requires review and at least one repeated cycle")
        elif self.periodic_state_convergence_reviewed:
            raise ValueError("periodic-state review requires declared tolerances")
        if minimum_evaluations > self.maximum_provider_evaluations:
            raise ValueError("minimum cycle-path evaluation count exceeds the provider evaluation budget")
        return self


DamageRateProvider = Callable[[float, tuple[float, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...], Mapping[str, str]], float]


def _hermite_state(y0: float, y1: float, dy0: float, dy1: float, dt: float, u: float) -> tuple[float, float]:
    a = y0
    b = dt * dy0
    c = -3.0 * y0 - 2.0 * dt * dy0 + 3.0 * y1 - dt * dy1
    d = 2.0 * y0 + dt * dy0 - 2.0 * y1 + dt * dy1
    value = ((d * u + c) * u + b) * u + a
    derivative_per_time = (b + 2.0 * c * u + 3.0 * d * u * u) / dt
    return value, derivative_per_time


def _periodic_spline_endpoint_rates(cycle: ClosedTensorCycle, coefficients=None):
    """Get stress/strain time derivatives at the closed-path endpoints."""
    assert cycle.sample_time_s is not None
    if coefficients is None:
        coefficients = _cycle_periodic_spline_coefficients(cycle)
    times = cycle.sample_time_s
    first_dt = times[1] - times[0]
    last_dt = times[-1] - times[-2]

    def endpoint_rates(history):
        start_segment, end_segment = history[0], history[-1]
        start = [start_segment[k][1] / first_dt for k in range(6)]
        end = [
            (segment[1] + 2.0 * segment[2] + 3.0 * segment[3]) / last_dt
            for segment in end_segment
        ]
        return start, end

    stress_start, stress_end = endpoint_rates(coefficients[0])
    strain_start, strain_end = endpoint_rates(coefficients[1])
    return stress_start, stress_end, strain_start, strain_end


def _path_state(cycle: ClosedTensorCycle, interval: int, u: float, reconstruction: str, pchip_coefficients=None):
    assert cycle.sample_time_s is not None
    t0, t1 = cycle.sample_time_s[interval : interval + 2]
    dt = t1 - t0
    time_s = t0 + u * dt
    stress = []
    strain = []
    dstress = []
    dstrain = []
    for component in range(6):
        s0 = cycle.stress_tensor_components_Pa[interval][component]
        s1 = cycle.stress_tensor_components_Pa[interval + 1][component]
        e0 = cycle.strain_tensor_components[interval][component]
        e1 = cycle.strain_tensor_components[interval + 1][component]
        if reconstruction == "piecewise_linear":
            stress.append(s0 + u * (s1 - s0))
            strain.append(e0 + u * (e1 - e0))
            dstress.append((s1 - s0) / dt)
            dstrain.append((e1 - e0) / dt)
        elif reconstruction == "piecewise_cubic_hermite":
            assert cycle.stress_time_derivative_components_Pa_s is not None
            assert cycle.strain_time_derivative_components_s_inv is not None
            ds0, ds1 = cycle.stress_time_derivative_components_Pa_s[interval][component], cycle.stress_time_derivative_components_Pa_s[interval + 1][component]
            de0, de1 = cycle.strain_time_derivative_components_s_inv[interval][component], cycle.strain_time_derivative_components_s_inv[interval + 1][component]
            sv, sd = _hermite_state(s0, s1, ds0, ds1, dt, u)
            ev, ed = _hermite_state(e0, e1, de0, de1, dt, u)
            stress.append(sv)
            strain.append(ev)
            dstress.append(sd)
            dstrain.append(ed)
        else:
            assert pchip_coefficients is not None
            for coefficients, output, derivative in (
                (pchip_coefficients[0][interval], stress, dstress),
                (pchip_coefficients[1][interval], strain, dstrain),
            ):
                a, b, c, d = coefficients[component]
                output.append(((d * u + c) * u + b) * u + a)
                derivative.append((b + 2.0 * c * u + 3.0 * d * u * u) / dt)
    return time_s, tuple(stress), tuple(strain), tuple(dstress), tuple(dstrain)


def _integrate_interval(
    cycle: ClosedTensorCycle,
    interval: int,
    reconstruction: str,
    provider: DamageRateProvider,
    order: int,
    panel_count: int,
    provider_context: Mapping[str, str],
    pchip_coefficients=None,
) -> float:
    assert cycle.sample_time_s is not None
    nodes, weights = _gauss_rule(order)
    left_time, right_time = cycle.sample_time_s[interval : interval + 2]
    panel_width = 1.0 / panel_count
    terms = []
    for panel in range(panel_count):
        left = panel * panel_width
        right = (panel + 1) * panel_width
        midpoint = 0.5 * (left + right)
        half_width = 0.5 * (right - left)
        for node, weight in zip(nodes, weights, strict=True):
            u = midpoint + half_width * node
            time_s, stress, strain, dstress, dstrain = _path_state(
                cycle, interval, u, reconstruction, pchip_coefficients
            )
            rate = provider(time_s, stress, strain, dstress, dstrain, provider_context)
            if isinstance(rate, bool) or not isinstance(rate, Real) or not math.isfinite(float(rate)) or rate < 0:
                raise ValueError("provider must return a finite nonnegative damage rate in 1/s")
            terms.append(float(rate) * (right_time - left_time) * half_width * weight)
    value = math.fsum(terms)
    if not math.isfinite(value) or value < 0:
        raise OverflowError("integrated damage is outside finite nonnegative support")
    return value


@lru_cache(maxsize=3)
def _gauss_rule(order: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    nodes, weights = np.polynomial.legendre.leggauss(order)
    return tuple(float(value) for value in nodes), tuple(float(value) for value in weights)


def evaluate_caller_multiaxial_damage(
    request: CallerMultiaxialDamageRequest,
    provider: DamageRateProvider,
) -> dict[str, Any]:
    """Adaptively integrate a deterministic memoryless caller damage rate over each tensor cycle.

    The callback receives absolute time, tensor component order [xx, yy, zz, xy,
    yz, zx], time derivatives and immutable material/calibration/cycle context. It must return instantaneous dimensionless
    damage rate in 1/s. Constitutive state evolution must be handled by a
    separate provider; this adapter only integrates a memoryless rate law.
    """
    if not callable(provider):
        return {"status": "needs_data", "analysis_id": request.analysis_id, "reason": "damage provider callback is unavailable"}
    expected_identity = {
        "provider_id": request.damage_provider_id,
        "revision": request.damage_provider_revision,
        "configuration_sha256": request.damage_provider_configuration_sha256,
    }
    actual_identity = {
        "provider_id": getattr(provider, "provider_id", None),
        "revision": getattr(provider, "revision", None),
        "configuration_sha256": getattr(provider, "configuration_sha256", None),
    }
    common = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "damage_provider": expected_identity,
        "calibration_id": request.calibration_id,
        "calibration_sha256": request.calibration_sha256,
        "law_profile_sha256": getattr(provider, "law_profile_sha256", None),
        "law_profile": getattr(provider, "law_profile", None),
        "provider_source_configuration_sha256": getattr(provider, "source_configuration_sha256", None),
        "stress_history_source_id": request.stress_history_source_id,
        "strain_history_source_id": request.strain_history_source_id,
        "stress_history_sha256": request.stress_history_sha256,
        "strain_history_sha256": request.strain_history_sha256,
        "strain_shear_convention": request.strain_shear_convention,
        "time_reconstruction": request.time_reconstruction,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
    }
    if actual_identity != expected_identity:
        return common | {"status": "out_of_scope", "reason": "provider identity or configuration digest differs from caller-pinned values"}
    reviews = (
        request.tensor_basis_and_order_reviewed,
        request.stress_strain_conjugacy_reviewed,
        request.cycle_extraction_and_closure_reviewed,
        request.time_reconstruction_reviewed,
        (request.time_reconstruction != "piecewise_periodic_cubic_spline" or request.periodic_spline_reviewed),
        request.provider_material_applicability_reviewed,
        request.provider_usage_rights_reviewed,
        request.memoryless_deterministic_rate_reviewed,
    )
    if not all(reviews):
        return common | {"status": "needs_data", "missing_review_count": sum(not item for item in reviews)}

    cycle_results = []
    total_damage_terms = []
    total_count_terms = []
    provider_evaluation_count = 0
    for cycle in request.cycles:
        assert cycle.sample_time_s is not None
        stress_closure = max(abs(a - b) for a, b in zip(cycle.stress_tensor_components_Pa[0], cycle.stress_tensor_components_Pa[-1], strict=True))
        strain_closure = max(abs(a - b) for a, b in zip(cycle.strain_tensor_components[0], cycle.strain_tensor_components[-1], strict=True))
        if stress_closure > request.maximum_closure_stress_error_Pa or strain_closure > request.maximum_closure_strain_error:
            return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                             "unresolved_cycle_id": cycle.cycle_id, "reason": "cycle closure exceeds declared tolerance"}
        try:
            periodic_spline_coefficients = (
                _cycle_periodic_spline_coefficients(cycle)
                if request.time_reconstruction == "piecewise_periodic_cubic_spline"
                else None
            )
        except RuntimeError as error:
            return common | {"status": "needs_data", "unresolved_cycle_id": cycle.cycle_id, "reason": str(error)}
        stress_rate_closure = None
        strain_rate_closure = None
        if request.time_reconstruction in {"piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"}:
            if request.time_reconstruction == "piecewise_cubic_hermite":
                assert cycle.stress_time_derivative_components_Pa_s is not None
                assert cycle.strain_time_derivative_components_s_inv is not None
                stress_start, stress_end = cycle.stress_time_derivative_components_Pa_s[0], cycle.stress_time_derivative_components_Pa_s[-1]
                strain_start, strain_end = cycle.strain_time_derivative_components_s_inv[0], cycle.strain_time_derivative_components_s_inv[-1]
            elif request.time_reconstruction == "piecewise_pchip":
                assert cycle.sample_time_s is not None
                stress_start = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.stress_tensor_components_Pa])[0] for k in range(6)]
                stress_end = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.stress_tensor_components_Pa])[-1] for k in range(6)]
                strain_start = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.strain_tensor_components])[0] for k in range(6)]
                strain_end = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.strain_tensor_components])[-1] for k in range(6)]
            else:
                stress_start, stress_end, strain_start, strain_end = _periodic_spline_endpoint_rates(
                    cycle, periodic_spline_coefficients
                )
            stress_rate_closure = max(abs(a - b) for a, b in zip(stress_start, stress_end, strict=True))
            strain_rate_closure = max(abs(a - b) for a, b in zip(strain_start, strain_end, strict=True))
            if (
                stress_rate_closure > request.maximum_closure_stress_rate_error_Pa_s
                or strain_rate_closure > request.maximum_closure_strain_rate_error_s_inv
            ):
                return common | {
                    "status": "out_of_scope",
                    "cycle_results": cycle_results,
                    "unresolved_cycle_id": cycle.cycle_id,
                    "maximum_stress_rate_closure_error_Pa_s": stress_rate_closure,
                    "maximum_strain_rate_closure_error_s_inv": strain_rate_closure,
                    "reason": "reconstructed cycle derivative closure exceeds the caller tolerance",
                }
        previous = None
        panel_count = request.initial_subinterval_count
        converged = False
        cycle_evaluation_count = 0
        provider_context = MappingProxyType({
            "analysis_id": request.analysis_id,
            "cycle_id": cycle.cycle_id,
            "material_condition_id": request.material_condition_id,
            "location_id": request.location_id,
            "calibration_id": request.calibration_id,
            "calibration_sha256": request.calibration_sha256,
            "strain_shear_convention": request.strain_shear_convention,
            "time_reconstruction": request.time_reconstruction,
        })
        pchip_coefficients = (
            _cycle_pchip_coefficients(cycle)
            if request.time_reconstruction == "piecewise_pchip"
            else periodic_spline_coefficients
            if request.time_reconstruction == "piecewise_periodic_cubic_spline"
            else None
        )
        while panel_count <= request.maximum_subinterval_count:
            requested_evaluations = (len(cycle.sample_time_s) - 1) * panel_count * request.quadrature_order
            if provider_evaluation_count + requested_evaluations > request.maximum_provider_evaluations:
                return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                                 "unresolved_cycle_id": cycle.cycle_id,
                                 "provider_evaluation_count": provider_evaluation_count,
                                 "maximum_provider_evaluations": request.maximum_provider_evaluations,
                                 "reason": "provider evaluation budget exceeded"}
            provider_evaluation_count += requested_evaluations
            cycle_evaluation_count += requested_evaluations
            try:
                value = math.fsum(
                    _integrate_interval(cycle, interval, request.time_reconstruction, provider,
                                        request.quadrature_order, panel_count, provider_context, pchip_coefficients)
                    for interval in range(len(cycle.sample_time_s) - 1)
                )
            except Exception as error:
                return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                                 "unresolved_cycle_id": cycle.cycle_id,
                                 "reason": "provider evaluation failed or returned an invalid damage rate",
                                 "provider_error_type": type(error).__name__}
            if previous is not None:
                error_estimate = abs(value - previous)
                tolerance = request.quadrature_absolute_tolerance_damage + request.quadrature_relative_tolerance * abs(value)
                if error_estimate <= tolerance:
                    converged = True
                    break
            previous = value
            if panel_count == request.maximum_subinterval_count:
                break
            panel_count = min(panel_count * 2, request.maximum_subinterval_count)
        if not converged:
            return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                             "unresolved_cycle_id": cycle.cycle_id,
                             "provider_evaluation_count": provider_evaluation_count,
                             "reason": "adaptive quadrature did not meet the caller tolerance",
                             "maximum_subinterval_count": request.maximum_subinterval_count}
        allocated_damage = value * cycle.allocated_cycle_count
        if not math.isfinite(allocated_damage):
            return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                             "unresolved_cycle_id": cycle.cycle_id, "reason": "allocated damage overflow"}
        cycle_results.append({
            "cycle_id": cycle.cycle_id,
            "allocated_cycle_count": cycle.allocated_cycle_count,
            "cycle_damage": value,
            "allocated_miner_damage": allocated_damage,
            "quadrature_error_estimate": error_estimate,
            "quadrature_tolerance": tolerance,
            "quadrature_subintervals_per_sample_interval": panel_count,
            "provider_evaluation_count": cycle_evaluation_count,
            "maximum_stress_closure_error_Pa": stress_closure,
            "maximum_strain_closure_error": strain_closure,
            "maximum_stress_rate_closure_error_Pa_s": stress_rate_closure,
            "maximum_strain_rate_closure_error_s_inv": strain_rate_closure,
        })
        total_damage_terms.append(allocated_damage)
        total_count_terms.append(cycle.allocated_cycle_count)
    final_identity = {
        "provider_id": getattr(provider, "provider_id", None),
        "revision": getattr(provider, "revision", None),
        "configuration_sha256": getattr(provider, "configuration_sha256", None),
    }
    if final_identity != expected_identity:
        return common | {"status": "out_of_scope", "cycle_results": cycle_results,
                         "provider_evaluation_count": provider_evaluation_count,
                         "reason": "provider identity or configuration changed during evaluation"}
    try:
        total_damage = math.fsum(total_damage_terms)
        total_cycle_count = math.fsum(total_count_terms)
    except (ValueError, OverflowError):
        return common | {"status": "out_of_scope", "cycle_results": cycle_results, "reason": "aggregate damage overflow"}
    if not math.isfinite(total_damage) or not math.isfinite(total_cycle_count):
        return common | {"status": "out_of_scope", "cycle_results": cycle_results, "reason": "aggregate damage or count is nonfinite"}
    return common | {
        "status": "computed",
        "cycle_results": cycle_results,
        "total_miner_damage": total_damage,
        "total_allocated_cycle_count": total_cycle_count,
        "total_provider_evaluation_count": provider_evaluation_count,
        "quadrature_method": f"adaptive_composite_Gauss_Legendre_order_{request.quadrature_order}",
        "damage_basis": "caller_supplied_memoryless_nonnegative_instantaneous_damage_rate_integrated_along_declared_tensor_path",
        "qualification": "user_model_unverified",
        "notes": [
            "The provider defines all material-specific multiaxial damage physics, state-independent rate, calibration and applicability. This adapter does not supply a universal nonproportional fatigue law.",
            "Each cycle is integrated independently. Stateful constitutive evolution, sequence effects, interaction between cycles and code acceptance require separate qualified providers.",
        ],
    }


StatefulDamageProvider = Callable[
    [float, tuple[float, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...], Mapping[str, Any]],
    Mapping[str, Any],
]


def evaluate_caller_stateful_multiaxial_damage(
    request: CallerStatefulMultiaxialDamageRequest,
    provider: StatefulDamageProvider,
) -> dict[str, Any]:
    """Integrate a caller state-evolution law and damage rate in declared cycle order.

    Classical RK4 advances dimensionless caller state variables and cumulative
    dimensionless damage together. Each closed tensor path is repeated the
    declared integer count, and the terminal state carries into the next path.
    This adapter supplies integration mechanics, not a material fatigue law.
    """
    expected = {
        "provider_id": request.damage_provider_id,
        "revision": request.damage_provider_revision,
        "configuration_sha256": request.damage_provider_configuration_sha256,
    }
    actual = {
        "provider_id": getattr(provider, "provider_id", None),
        "revision": getattr(provider, "revision", None),
        "configuration_sha256": getattr(provider, "configuration_sha256", None),
    }
    common = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "damage_provider": expected,
        "calibration_id": request.calibration_id,
        "calibration_sha256": request.calibration_sha256,
        "law_profile_sha256": getattr(provider, "law_profile_sha256", None),
        "law_profile": getattr(provider, "law_profile", None),
        "provider_source_configuration_sha256": getattr(provider, "source_configuration_sha256", None),
        "stress_history_source_id": request.stress_history_source_id,
        "stress_history_sha256": request.stress_history_sha256,
        "strain_history_source_id": request.strain_history_source_id,
        "strain_history_sha256": request.strain_history_sha256,
        "state_variable_ids": list(request.state_variable_ids),
        "cycle_exchange_receipt_sha256": request.cycle_exchange_receipt_sha256,
        "cycle_block_order_ids": list(request.cycle_block_order_ids) if request.cycle_block_order_ids else None,
        "cycle_exchange_clock_id": request.cycle_exchange_clock_id,
        "cycle_exchange_provider_id": request.cycle_exchange_provider_id,
        "cycle_exchange_provider_revision": request.cycle_exchange_provider_revision,
        "cycle_exchange_provider_run_id": request.cycle_exchange_provider_run_id,
        "cycle_exchange_provider_result_sha256": request.cycle_exchange_provider_result_sha256,
        "cycle_source_initial_state_sha256": request.cycle_source_initial_state_sha256,
        "cycle_source_terminal_state_sha256": request.cycle_source_terminal_state_sha256,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
    }
    if not callable(provider):
        return common | {"status": "needs_data", "reason": "stateful damage provider callback is unavailable"}
    if actual != expected:
        return common | {"status": "out_of_scope", "reason": "provider identity or configuration digest differs from caller-pinned values"}
    reviews = (
        request.tensor_basis_and_order_reviewed,
        request.stress_strain_conjugacy_reviewed,
        request.cycle_extraction_and_sequence_order_reviewed,
        request.time_reconstruction_reviewed,
        (request.time_reconstruction != "piecewise_periodic_cubic_spline" or request.periodic_spline_reviewed),
        request.state_initialization_and_bounds_reviewed,
        request.provider_material_applicability_reviewed,
        request.provider_usage_rights_reviewed,
        request.stateful_rate_and_evolution_law_reviewed,
    )
    if not all(reviews):
        return common | {"status": "needs_data", "missing_review_count": sum(not value for value in reviews)}

    state = np.asarray(request.initial_state, dtype=float)
    lower = np.asarray(request.minimum_state, dtype=float)
    upper = np.asarray(request.maximum_state, dtype=float)
    context = MappingProxyType({
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "calibration_id": request.calibration_id,
        "calibration_sha256": request.calibration_sha256,
        "state_variable_ids": tuple(request.state_variable_ids),
        "strain_shear_convention": request.strain_shear_convention,
    })
    evaluations = 0
    elapsed = 0.0
    total_damage_terms = []
    cycle_results = []
    adaptive_accepted_steps = 0
    adaptive_rejected_steps = 0
    adaptive_maximum_error_ratio = 0.0
    adaptive_rejection_history = []
    active_pchip_coefficients = None

    def integration_diagnostics():
        return {
            "integration_method": "fixed_step_classical_RK4" if request.integration_method == "fixed_step_rk4" else "adaptive_step_doubling_classical_RK4",
            "integration_method_id": request.integration_method,
            "maximum_time_step_s": request.maximum_time_step_s,
            "minimum_time_step_s": request.minimum_time_step_s,
            "state_absolute_tolerance": request.state_absolute_tolerance,
            "state_relative_tolerance": request.state_relative_tolerance,
            "damage_absolute_tolerance": request.damage_absolute_tolerance,
            "damage_relative_tolerance": request.damage_relative_tolerance,
            "maximum_rejected_steps_per_interval": request.maximum_rejected_steps_per_interval,
            "maximum_rejection_history_records": request.maximum_rejection_history_records,
            "periodic_state_absolute_tolerance": request.periodic_state_absolute_tolerance,
            "periodic_state_relative_tolerance": request.periodic_state_relative_tolerance,
            "periodic_state_convergence_reviewed": request.periodic_state_convergence_reviewed,
            "total_provider_evaluation_count": evaluations,
            "adaptive_accepted_steps": adaptive_accepted_steps,
            "adaptive_rejected_steps": adaptive_rejected_steps,
            "adaptive_maximum_error_ratio": adaptive_maximum_error_ratio,
            "adaptive_rejection_history": adaptive_rejection_history,
            "adaptive_rejection_history_sha256": canonical_digest(adaptive_rejection_history),
        }

    def record_adaptive_rejection(record):
        if len(adaptive_rejection_history) >= request.maximum_rejection_history_records:
            raise ArithmeticError("adaptive_RK4_rejection_history_budget_exceeded")
        adaptive_rejection_history.append({
            "rejection_index": len(adaptive_rejection_history),
            **record,
        })

    def evaluate(cycle, interval, u, global_start, cycle_index, repetition_index, state_value):
        nonlocal evaluations
        if evaluations >= request.maximum_provider_evaluations:
            raise ArithmeticError("stateful_damage_provider_evaluation_budget_exceeded")
        if not np.isfinite(state_value).all() or np.any(state_value < lower) or np.any(state_value > upper):
            raise ArithmeticError("stateful_damage_state_left_declared_bounds")
        local_time, stress, strain, dstress, dstrain = _path_state(
            cycle, interval, u, request.time_reconstruction, active_pchip_coefficients
        )
        assert cycle.sample_time_s is not None
        global_time = global_start + local_time - cycle.sample_time_s[0]
        if not all(math.isfinite(value) for value in (*stress, *strain, *dstress, *dstrain, global_time)):
            raise ArithmeticError("reconstructed_tensor_path_exceeded_finite_support")
        provider_context = MappingProxyType({
            **context,
            "cycle_id": cycle.cycle_id,
            "cycle_index": str(cycle_index),
            "repetition_index": str(repetition_index),
            "elapsed_cycle_sequence_time_s": str(global_time),
        })
        current_identity = {
            "provider_id": getattr(provider, "provider_id", None),
            "revision": getattr(provider, "revision", None),
            "configuration_sha256": getattr(provider, "configuration_sha256", None),
        }
        if current_identity != expected:
            raise ArithmeticError("stateful_damage_provider_identity_changed_during_evaluation")
        evaluations += 1
        raw = provider(
            global_time,
            tuple(stress),
            tuple(strain),
            tuple(dstress),
            tuple(dstrain),
            tuple(float(value) for value in state_value),
            provider_context,
        )
        if not isinstance(raw, Mapping):
            raise ValueError("stateful provider must return a mapping")
        derivative = raw.get("state_derivative_per_s")
        rate = raw.get("damage_rate_per_s")
        if not isinstance(derivative, (tuple, list, np.ndarray)) or len(derivative) != len(state_value):
            raise ValueError("provider state derivative must align with the declared state variables")
        derivative_values = []
        for value in derivative:
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
                raise ValueError("provider state derivative must contain finite real values")
            derivative_values.append(float(value))
        if isinstance(rate, bool) or not isinstance(rate, Real) or not math.isfinite(float(rate)) or rate < 0:
            raise ValueError("provider damage rate must be finite, real, and nonnegative")
        return np.asarray(derivative_values, dtype=float), float(rate)

    def rk4_step(cycle, interval, global_start, cycle_index, repetition_index,
                 interval_duration, position, step_size, state_value):
        u0 = position / interval_duration
        umid = (position + 0.5 * step_size) / interval_duration
        remaining = interval_duration - position
        u1 = 1.0 if step_size >= remaining else (position + step_size) / interval_duration
        k1, d1 = evaluate(cycle, interval, u0, global_start, cycle_index, repetition_index, state_value)
        k2, d2 = evaluate(cycle, interval, umid, global_start, cycle_index, repetition_index, state_value + 0.5 * step_size * k1)
        k3, d3 = evaluate(cycle, interval, umid, global_start, cycle_index, repetition_index, state_value + 0.5 * step_size * k2)
        k4, d4 = evaluate(cycle, interval, u1, global_start, cycle_index, repetition_index, state_value + step_size * k3)
        next_state = state_value + (step_size / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        increment = (step_size / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)
        if (not np.isfinite(next_state).all() or np.any(next_state < lower)
            or np.any(next_state > upper) or not math.isfinite(increment) or increment < 0):
            raise ArithmeticError("stateful_damage_update_left_finite_or_declared_support")
        return next_state, increment

    for cycle_index, cycle in enumerate(request.cycles):
        assert cycle.sample_time_s is not None
        try:
            active_pchip_coefficients = (
                _cycle_pchip_coefficients(cycle)
                if request.time_reconstruction == "piecewise_pchip"
                else _cycle_periodic_spline_coefficients(cycle)
                if request.time_reconstruction == "piecewise_periodic_cubic_spline"
                else None
            )
        except RuntimeError as error:
            return common | integration_diagnostics() | {
                "status": "needs_data",
                "unresolved_cycle_id": cycle.cycle_id,
                "reason": str(error),
            }
        cycle_evaluations_start = evaluations
        cycle_adaptive_accepted_start = adaptive_accepted_steps
        cycle_adaptive_rejected_start = adaptive_rejected_steps
        cycle_rejection_history_start = len(adaptive_rejection_history)
        cycle_maximum_error_ratio = 0.0
        stress_closure = max(
            abs(a - b)
            for a, b in zip(cycle.stress_tensor_components_Pa[0], cycle.stress_tensor_components_Pa[-1], strict=True)
        )
        strain_closure = max(
            abs(a - b)
            for a, b in zip(cycle.strain_tensor_components[0], cycle.strain_tensor_components[-1], strict=True)
        )
        if stress_closure > request.maximum_closure_stress_error_Pa or strain_closure > request.maximum_closure_strain_error:
            return common | integration_diagnostics() | {
                "status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                "unresolved_cycle_id": cycle.cycle_id, "reason": "cycle closure exceeds declared tolerance",
            }
        if request.time_reconstruction in {"piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"}:
            if request.time_reconstruction == "piecewise_cubic_hermite":
                assert cycle.stress_time_derivative_components_Pa_s is not None
                assert cycle.strain_time_derivative_components_s_inv is not None
                stress_start, stress_end = cycle.stress_time_derivative_components_Pa_s[0], cycle.stress_time_derivative_components_Pa_s[-1]
                strain_start, strain_end = cycle.strain_time_derivative_components_s_inv[0], cycle.strain_time_derivative_components_s_inv[-1]
            elif request.time_reconstruction == "piecewise_pchip":
                assert cycle.sample_time_s is not None
                stress_start = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.stress_tensor_components_Pa])[0] for k in range(6)]
                stress_end = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.stress_tensor_components_Pa])[-1] for k in range(6)]
                strain_start = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.strain_tensor_components])[0] for k in range(6)]
                strain_end = [_pchip_slopes(cycle.sample_time_s, [row[k] for row in cycle.strain_tensor_components])[-1] for k in range(6)]
            else:
                stress_start, stress_end, strain_start, strain_end = _periodic_spline_endpoint_rates(
                    cycle, active_pchip_coefficients
                )
            stress_rate_closure = max(abs(a - b) for a, b in zip(stress_start, stress_end, strict=True))
            strain_rate_closure = max(abs(a - b) for a, b in zip(strain_start, strain_end, strict=True))
            if (stress_rate_closure > request.maximum_closure_stress_rate_error_Pa_s
                or strain_rate_closure > request.maximum_closure_strain_rate_error_s_inv):
                return common | integration_diagnostics() | {
                    "status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                    "unresolved_cycle_id": cycle.cycle_id,
                    "maximum_stress_rate_closure_error_Pa_s": stress_rate_closure,
                    "maximum_strain_rate_closure_error_s_inv": strain_rate_closure,
                    "reason": "cycle derivative closure exceeds declared tolerance",
                }
        repeat_count = int(cycle.allocated_cycle_count)
        cycle_initial_state = state.copy()
        cycle_start_elapsed = elapsed
        cycle_damage = 0.0
        first_repeat_damage = None
        first_repeat_final_state = None
        previous_repeat_final_state = None
        penultimate_repeat_final_state = None
        last_repeat_damage = 0.0
        for repetition_index in range(repeat_count):
            repeat_damage = 0.0
            for interval, (left_time, right_time) in enumerate(zip(cycle.sample_time_s[:-1], cycle.sample_time_s[1:], strict=True)):
                interval_duration = right_time - left_time
                ratio = interval_duration / request.maximum_time_step_s
                if not math.isfinite(ratio):
                    return common | integration_diagnostics() | {"status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                                     "unresolved_cycle_id": cycle.cycle_id, "reason": "requested RK4 resolution exceeds finite support"}
                try:
                    if request.integration_method == "fixed_step_rk4":
                        steps = max(1, math.ceil(ratio))
                        nominal_step_size = interval_duration / steps
                        for step_index in range(steps):
                            position = interval_duration * step_index / steps
                            step_size = interval_duration - position if step_index == steps - 1 else nominal_step_size
                            state, increment = rk4_step(cycle, interval, elapsed, cycle_index, repetition_index,
                                                        interval_duration, position, step_size, state)
                            repeat_damage += increment
                    else:
                        position = 0.0
                        step_size = min(request.maximum_time_step_s, interval_duration)
                        rejected_this_interval = 0
                        while position < interval_duration:
                            remaining = interval_duration - position
                            trial_step = min(step_size, remaining)
                            if evaluations + 12 > request.maximum_provider_evaluations:
                                raise ArithmeticError("stateful_damage_provider_evaluation_budget_exceeded")
                            try:
                                full_state, full_damage = rk4_step(cycle, interval, elapsed, cycle_index, repetition_index,
                                                                  interval_duration, position, trial_step, state)
                                half_state, half_damage_a = rk4_step(cycle, interval, elapsed, cycle_index, repetition_index,
                                                                     interval_duration, position, 0.5 * trial_step, state)
                                doubled_state, half_damage_b = rk4_step(cycle, interval, elapsed, cycle_index, repetition_index,
                                                                        interval_duration, position + 0.5 * trial_step,
                                                                        0.5 * trial_step, half_state)
                            except ArithmeticError as error:
                                if str(error) not in {
                                    "stateful_damage_state_left_declared_bounds",
                                    "stateful_damage_update_left_finite_or_declared_support",
                                }:
                                    raise
                                rejected_this_interval += 1
                                adaptive_rejected_steps += 1
                                cycle_global_start = elapsed + left_time - cycle.sample_time_s[0]
                                record_adaptive_rejection({
                                    "cycle_id": cycle.cycle_id,
                                    "repetition_index": repetition_index,
                                    "interval_index": interval,
                                    "global_start_time_s": cycle_global_start + position,
                                    "attempted_step_s": trial_step,
                                    "reason": "intermediate_or_endpoint_state_outside_declared_support",
                                    "next_step_s": max(request.minimum_time_step_s, 0.5 * trial_step),
                                })
                                if (rejected_this_interval > request.maximum_rejected_steps_per_interval
                                    or trial_step <= request.minimum_time_step_s):
                                    raise ArithmeticError("adaptive_RK4_cannot_resolve_state_bounds_at_minimum_step") from error
                                step_size = max(request.minimum_time_step_s, 0.5 * trial_step)
                                continue
                            error_state = np.abs(doubled_state - full_state) / 15.0
                            state_scale = request.state_absolute_tolerance + request.state_relative_tolerance * np.maximum(np.abs(state), np.abs(doubled_state))
                            state_error_ratio = float(np.max(error_state / state_scale))
                            doubled_damage = half_damage_a + half_damage_b
                            damage_error = abs(doubled_damage - full_damage) / 15.0
                            damage_scale = request.damage_absolute_tolerance + request.damage_relative_tolerance * max(
                                abs(repeat_damage), abs(repeat_damage + doubled_damage)
                            )
                            error_ratio = max(state_error_ratio, damage_error / damage_scale)
                            if not math.isfinite(error_ratio):
                                raise ArithmeticError("adaptive_RK4_error_estimate_exceeded_finite_support")
                            adaptive_maximum_error_ratio = max(adaptive_maximum_error_ratio, error_ratio)
                            cycle_maximum_error_ratio = max(cycle_maximum_error_ratio, error_ratio)
                            if error_ratio <= 1.0:
                                state = doubled_state
                                repeat_damage += doubled_damage
                                position = interval_duration if trial_step == remaining else position + trial_step
                                adaptive_accepted_steps += 1
                                factor = 5.0 if error_ratio == 0 else min(5.0, max(0.2, 0.9 * error_ratio ** -0.2))
                                step_size = min(request.maximum_time_step_s, max(request.minimum_time_step_s, trial_step * factor))
                            else:
                                rejected_this_interval += 1
                                adaptive_rejected_steps += 1
                                smaller_step = trial_step * max(0.1, min(0.8, 0.9 * error_ratio ** -0.2))
                                record_adaptive_rejection({
                                    "cycle_id": cycle.cycle_id,
                                    "repetition_index": repetition_index,
                                    "interval_index": interval,
                                    "global_start_time_s": elapsed + left_time - cycle.sample_time_s[0] + position,
                                    "attempted_step_s": trial_step,
                                    "error_ratio": error_ratio,
                                    "state_error_ratio": state_error_ratio,
                                    "damage_error_ratio": damage_error / damage_scale,
                                    "reason": "estimated_local_error_above_tolerance",
                                    "next_step_s": max(request.minimum_time_step_s, min(remaining, smaller_step)),
                                })
                                if rejected_this_interval > request.maximum_rejected_steps_per_interval:
                                    raise ArithmeticError("adaptive_RK4_rejection_budget_exceeded")
                                if trial_step <= request.minimum_time_step_s:
                                    raise ArithmeticError("adaptive_RK4_minimum_step_reached_before_tolerance")
                                step_size = max(request.minimum_time_step_s, min(remaining, smaller_step))
                except Exception as error:
                    return common | integration_diagnostics() | {
                        "status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                        "unresolved_cycle_id": cycle.cycle_id,
                        "repetition_index": repetition_index,
                        "state_at_failure": state.tolist(),
                        "reason": "stateful provider or RK4 integration failed",
                        "provider_error_type": type(error).__name__,
                        "provider_error": str(error),
                    }
            elapsed += cycle.sample_time_s[-1] - cycle.sample_time_s[0]
            if not math.isfinite(elapsed):
                return common | integration_diagnostics() | {
                    "status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                    "unresolved_cycle_id": cycle.cycle_id,
                    "reason": "sequence elapsed time exceeded finite support",
                }
            if not math.isfinite(repeat_damage):
                return common | integration_diagnostics() | {"status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                                 "unresolved_cycle_id": cycle.cycle_id, "reason": "cycle damage overflow"}
            cycle_damage += repeat_damage
            if not math.isfinite(cycle_damage):
                return common | integration_diagnostics() | {
                    "status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                    "unresolved_cycle_id": cycle.cycle_id,
                    "reason": "cycle sequence damage overflow",
                }
            if repetition_index == 0:
                first_repeat_damage = repeat_damage
                first_repeat_final_state = state.copy()
            if previous_repeat_final_state is not None:
                penultimate_repeat_final_state = previous_repeat_final_state
            previous_repeat_final_state = state.copy()
            last_repeat_damage = repeat_damage
        cycle_rejections = adaptive_rejection_history[cycle_rejection_history_start:]
        repeated_path_diagnostic = None
        if repeat_count >= 2:
            assert penultimate_repeat_final_state is not None
            assert previous_repeat_final_state is not None
            state_change = np.abs(previous_repeat_final_state - penultimate_repeat_final_state)
            repeated_path_diagnostic = {
                "basis": "successive_terminal_states_after_repeating_the_same_declared_cycle_path",
                "state_after_penultimate_repetition": penultimate_repeat_final_state.tolist(),
                "state_after_last_repetition": previous_repeat_final_state.tolist(),
                "absolute_state_change_by_variable": state_change.tolist(),
                "maximum_absolute_state_change": float(np.max(state_change)),
                "caller_tolerance_evaluated": request.periodic_state_absolute_tolerance is not None,
                "within_caller_tolerance": None,
                "normalized_error_by_variable": None,
            }
            if request.periodic_state_absolute_tolerance is not None:
                tolerance = request.periodic_state_absolute_tolerance + request.periodic_state_relative_tolerance * np.maximum(
                    np.abs(penultimate_repeat_final_state), np.abs(previous_repeat_final_state)
                )
                if not np.isfinite(tolerance).all() or np.any(tolerance <= 0.0):
                    return common | integration_diagnostics() | {
                        "status": "out_of_scope",
                        "computed_cycle_prefix": cycle_results,
                        "unresolved_cycle_id": cycle.cycle_id,
                        "reason": "periodic-state tolerance scale exceeded finite numeric support",
                    }
                normalized_error = state_change / tolerance
                if not np.isfinite(normalized_error).all():
                    return common | integration_diagnostics() | {
                        "status": "out_of_scope",
                        "computed_cycle_prefix": cycle_results,
                        "unresolved_cycle_id": cycle.cycle_id,
                        "reason": "periodic-state normalized error exceeded finite numeric support",
                    }
                repeated_path_diagnostic.update({
                    "absolute_tolerance": request.periodic_state_absolute_tolerance,
                    "relative_tolerance": request.periodic_state_relative_tolerance,
                    "normalized_error_by_variable": normalized_error.tolist(),
                    "within_caller_tolerance": bool(np.all(normalized_error <= 1.0)),
                })
        cycle_results.append({
            "cycle_id": cycle.cycle_id,
            "repetition_count": repeat_count,
            "sequence_start_time_s": cycle_start_elapsed,
            "sequence_end_time_s": elapsed,
            "cycle_sequence_damage": cycle_damage,
            "damage_first_repetition": first_repeat_damage,
            "damage_last_repetition": last_repeat_damage,
            "initial_state": cycle_initial_state.tolist(),
            "state_after_first_repetition": first_repeat_final_state.tolist(),
            "final_state": state.tolist(),
            "repeated_path_state_diagnostic": repeated_path_diagnostic,
            "maximum_stress_closure_error_Pa": stress_closure,
            "maximum_strain_closure_error": strain_closure,
            "provider_evaluation_count": evaluations - cycle_evaluations_start,
            "adaptive_accepted_steps": adaptive_accepted_steps - cycle_adaptive_accepted_start,
            "adaptive_rejected_steps": adaptive_rejected_steps - cycle_adaptive_rejected_start,
            "adaptive_maximum_error_ratio": cycle_maximum_error_ratio,
            "adaptive_rejection_history_start_index": cycle_rejection_history_start,
            "adaptive_rejection_history_end_index_exclusive": len(adaptive_rejection_history),
            "adaptive_rejection_history": cycle_rejections,
            "adaptive_rejection_history_sha256": canonical_digest(cycle_rejections),
        })
        total_damage_terms.append(cycle_damage)
    final_identity = {
        "provider_id": getattr(provider, "provider_id", None),
        "revision": getattr(provider, "revision", None),
        "configuration_sha256": getattr(provider, "configuration_sha256", None),
    }
    if final_identity != expected:
        return common | integration_diagnostics() | {"status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                         "reason": "provider identity or configuration changed during evaluation"}
    try:
        total_damage = math.fsum(total_damage_terms)
    except (OverflowError, ValueError):
        return common | integration_diagnostics() | {"status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                         "reason": "sequence damage aggregate overflow"}
    if not math.isfinite(total_damage):
        return common | integration_diagnostics() | {"status": "out_of_scope", "computed_cycle_prefix": cycle_results,
                         "reason": "sequence damage aggregate is nonfinite"}
    return common | integration_diagnostics() | {
        "status": "computed",
        "cycle_results": cycle_results,
        "initial_state": list(request.initial_state),
        "final_state": state.tolist(),
        "elapsed_sequence_time_s": elapsed,
        "total_damage": total_damage,
        "damage_basis": "caller_supplied_stateful_multiaxial_rate_and_state_evolution_integrated_over_ordered_tensor_cycles",
        "qualification": "user_model_unverified",
        "notes": [
            "The provider defines all material-specific state evolution, damage physics, calibration and applicability; the adapter contributes only the declared RK4 integration mechanics.",
            "Cycle order is exactly the request tuple order; integer repetitions carry the terminal state into the next repetition and cycle.",
            "Adaptive step doubling estimates local integration error from one full and two half classical-RK4 advances; it is a numerical error indicator, not a material-law uncertainty or physical validity measure.",
            "When a cycle path repeats, the optional periodic-state diagnostic compares only the terminal state after the last two repetitions of that path. Meeting caller tolerances is not proof of an asymptotic fixed point or fatigue stabilization.",
            "The caller must independently assess step convergence, state-law stability, provider determinism, model validity and code acceptance.",
        ],
    }
