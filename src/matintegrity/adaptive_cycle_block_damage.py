"""Caller state/damage ODE integration in an ordered integer-cycle domain."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from numbers import Real

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

INTERFACE_ID = "integration.adaptive_cycle_block_damage"
SOURCE_ID = "caller_adaptive_cycle_block_state_damage_ode"


class CycleBlockLawParameter(Contract):
    parameter_id: str = Field(min_length=1)
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1)

    @model_validator(mode="after")
    def meaningful_parameter(self):
        if not self.parameter_id.strip() or not self.unit.strip():
            raise ValueError("parameter ID and unit must contain non-whitespace characters")
        return self


class IntegerCycleDamageBlock(Contract):
    block_id: str = Field(min_length=1)
    cycle_population_id: str = Field(min_length=1)
    loading_state_id: str = Field(min_length=1)
    cycle_count: int = Field(ge=1, le=2**53, strict=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameters: tuple[CycleBlockLawParameter, ...] = Field(default=(), max_length=1000)

    @model_validator(mode="after")
    def unique_parameters(self):
        if any(not name.strip() for name in (self.block_id, self.cycle_population_id, self.loading_state_id)):
            raise ValueError("block, population and loading-state IDs must contain non-whitespace characters")
        if len({p.parameter_id for p in self.parameters}) != len(self.parameters):
            raise ValueError("block parameter IDs must be unique")
        return self


class AdaptiveCycleBlockDamageRequest(Contract):
    analysis_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    cycle_count_basis_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_variable_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    state_units: tuple[str, ...] = Field(min_length=1, max_length=128)
    initial_state: tuple[float, ...] = Field(min_length=1, max_length=128)
    minimum_state: tuple[float, ...] = Field(min_length=1, max_length=128)
    maximum_state: tuple[float, ...] = Field(min_length=1, max_length=128)
    initial_damage: Nonnegative = 0.0
    damage_event_threshold: Positive | None = None
    blocks: tuple[IntegerCycleDamageBlock, ...] = Field(min_length=1, max_length=10000)
    initial_step_cycles: Positive
    minimum_step_cycles: Positive
    maximum_step_cycles: Positive
    state_absolute_tolerance: tuple[Positive, ...] = Field(min_length=1, max_length=128)
    state_relative_tolerance: Positive
    damage_absolute_tolerance: Positive
    damage_relative_tolerance: Positive
    maximum_function_evaluations: int = Field(default=100000, ge=12, le=10000000)
    maximum_rejected_steps: int = Field(default=10000, ge=1, le=1000000)
    ordered_integer_blocks_and_cycle_count_basis_reviewed: bool
    state_law_and_nonnegative_damage_rate_reviewed: bool
    initialization_bounds_and_event_meaning_reviewed: bool
    deterministic_repeat_evaluation_reviewed: bool
    adaptive_controls_and_local_error_meaning_reviewed: bool
    material_calibration_and_usage_rights_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def dimensions_and_support(self):
        n = len(self.state_variable_ids)
        if len(set(self.state_variable_ids)) != n or any(not name.strip() for name in self.state_variable_ids):
            raise ValueError("state IDs must be nonempty and unique")
        if any(len(values) != n for values in (self.state_units, self.initial_state, self.minimum_state, self.maximum_state, self.state_absolute_tolerance)):
            raise ValueError("state arrays must align with ordered state IDs")
        if any(not unit.strip() for unit in self.state_units):
            raise ValueError("each state variable requires an explicit nonempty unit")
        if any(not lo <= value <= hi for lo, value, hi in zip(self.minimum_state, self.initial_state, self.maximum_state, strict=True)):
            raise ValueError("initial state must lie inside ordered bounds")
        if not self.minimum_step_cycles <= self.initial_step_cycles <= self.maximum_step_cycles:
            raise ValueError("cycle-step bounds must enclose the initial step")
        if len({b.block_id for b in self.blocks}) != len(self.blocks):
            raise ValueError("block IDs must be unique")
        if sum(b.cycle_count for b in self.blocks) > 2**53:
            raise ValueError("total cycle count exceeds exact integer representation")
        if self.damage_event_threshold is not None and self.initial_damage >= self.damage_event_threshold:
            raise ValueError("initial damage must lie strictly below the declared event threshold")
        if not any(e.source_id == self.provider_id and e.sha256 == self.calibration_sha256 and e.license_id for e in self.evidence):
            raise ValueError("calibration requires provider/digest-matched Evidence with a usage-rights identifier")
        return self


class _StateBound(Exception):
    pass


def evaluate_adaptive_cycle_block_damage(request: AdaptiveCycleBlockDamageRequest, provider: Callable) -> dict:
    """Integrate a caller cycle-count ODE, without assigning a fatigue material law.

    provider(local_cycle_coordinate, state_tuple, block) returns
    {state_derivative_per_cycle: tuple, damage_rate_per_cycle: nonnegative scalar}.
    """
    x = request
    expected_identity = (x.provider_id, x.provider_revision, x.provider_configuration_sha256,
                         x.calibration_sha256, x.state_variable_ids, x.state_units, x.cycle_count_basis_id, "1")
    def identity():
        return (getattr(provider, "provider_id", None), getattr(provider, "revision", None),
                getattr(provider, "configuration_sha256", None), getattr(provider, "calibration_sha256", None),
                getattr(provider, "state_variable_ids", None), getattr(provider, "state_units", None),
                getattr(provider, "cycle_count_basis_id", None), getattr(provider, "damage_unit", None))
    if not callable(provider) or identity() != expected_identity:
        raise ValueError("runtime provider identity/revision/configuration must match request")
    input_digest = canonical_digest(x.model_dump(mode="json"))
    base = {"interface_id": INTERFACE_ID, "analysis_id": x.analysis_id, "physical_scope_id": x.physical_scope_id,
            "input_sha256": input_digest, "provider_id": x.provider_id, "provider_revision": x.provider_revision,
            "provider_configuration_sha256": x.provider_configuration_sha256, "calibration_sha256": x.calibration_sha256,
            "cycle_count_basis_id": x.cycle_count_basis_id, "state_variable_ids": list(x.state_variable_ids),
            "state_units": list(x.state_units), "damage_unit": "1"}
    reviews = (x.ordered_integer_blocks_and_cycle_count_basis_reviewed, x.state_law_and_nonnegative_damage_rate_reviewed,
               x.initialization_bounds_and_event_meaning_reviewed, x.deterministic_repeat_evaluation_reviewed,
               x.adaptive_controls_and_local_error_meaning_reviewed, x.material_calibration_and_usage_rights_reviewed,
               x.computational_use_authorized)
    if not all(reviews):
        return base | {"status": "needs_data", "reason": "required_reviews_incomplete"}
    state = tuple(x.initial_state) + (float(x.initial_damage),)
    rows = []
    evaluations = accepted = rejected = 0
    maximum_accepted_error = 0.0
    completed_cycles = 0
    block = x.blocks[0]
    coordinate = 0.0
    h = x.initial_step_cycles

    def stop(reason, **extra):
        return base | {"status": "out_of_scope", "reason": reason, "completed_blocks": rows,
                       "completed_integer_cycle_count": completed_cycles, "current_block_id": block.block_id,
                       "accepted_local_cycle_coordinate": coordinate, "accepted_state": list(state[:-1]),
                       "accepted_damage": state[-1], "function_evaluations": evaluations,
                       "accepted_steps": accepted, "rejected_steps": rejected,
                       "maximum_accepted_scaled_local_error": maximum_accepted_error,
                       "full_requested_history_completed": False} | extra

    def evaluate(t, y):
        nonlocal evaluations
        if evaluations >= x.maximum_function_evaluations:
            raise RuntimeError("function_evaluation_budget_exhausted")
        if not all(math.isfinite(v) for v in y):
            raise ArithmeticError("nonfinite_stage_state")
        if any(not lo <= value <= hi for lo, value, hi in zip(x.minimum_state, y[:-1], x.maximum_state, strict=True)):
            raise _StateBound("state_bound_reached_in_trial_stage")
        if y[-1] < state[-1]:
            raise ArithmeticError("damage_decreased_in_trial_stage")
        if identity() != expected_identity:
            raise ValueError("provider_identity_changed")
        evaluations += 1
        result = provider(float(t), tuple(y[:-1]), block)
        if identity() != expected_identity:
            raise ValueError("provider_identity_changed")
        if not isinstance(result, Mapping):
            raise ValueError("provider_result_must_be_mapping")
        if set(result) != {"state_derivative_per_cycle", "damage_rate_per_cycle"}:
            raise ValueError("provider_result_requires_exact_derivative_and_damage_keys")
        derivatives = result.get("state_derivative_per_cycle")
        rate = result.get("damage_rate_per_cycle")
        if not isinstance(derivatives, (tuple, list)) or len(derivatives) != len(x.initial_state):
            raise ValueError("provider_state_derivative_dimension_mismatch")
        values = tuple(derivatives) + (rate,)
        if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v) for v in values) or rate < 0.0:
            raise ValueError("provider_derivatives_must_be_finite_and_damage_rate_nonnegative")
        return tuple(float(v) for v in values)

    def rk4(t, y, step):
        k1 = evaluate(t, y)
        k2 = evaluate(t + step / 2.0, tuple(v + step * k / 2.0 for v, k in zip(y, k1, strict=True)))
        k3 = evaluate(t + step / 2.0, tuple(v + step * k / 2.0 for v, k in zip(y, k2, strict=True)))
        k4 = evaluate(t + step, tuple(v + step * k for v, k in zip(y, k3, strict=True)))
        result = tuple(v + step * (a / 6.0 + b / 3.0 + c / 3.0 + d / 6.0) for v, a, b, c, d in zip(y, k1, k2, k3, k4, strict=True))
        if not all(math.isfinite(v) for v in result):
            raise ArithmeticError("nonfinite_trial_solution")
        if any(not lo <= value <= hi for lo, value, hi in zip(x.minimum_state, result[:-1], x.maximum_state, strict=True)):
            raise _StateBound("state_bound_reached_in_trial_solution")
        return result

    for block in x.blocks:
        coordinate = 0.0
        start_state = state
        block_digest = canonical_digest(block.model_dump(mode="json"))
        while coordinate < block.cycle_count:
            remaining = block.cycle_count - coordinate
            h = min(h, remaining, x.maximum_step_cycles)
            if coordinate + h <= coordinate or coordinate + h / 2.0 <= coordinate:
                return stop("cycle_coordinate_resolution_exhausted")
            if evaluations + 12 > x.maximum_function_evaluations:
                return stop("function_evaluation_budget_exhausted")
            try:
                whole = rk4(coordinate, state, h)
                half = rk4(coordinate, state, h / 2.0)
                fine = rk4(coordinate + h / 2.0, half, h / 2.0)
                scaled_errors = []
                for old, a, b, atol, rtol in zip(state, whole, fine,
                    x.state_absolute_tolerance + (x.damage_absolute_tolerance,),
                    (x.state_relative_tolerance,) * len(x.initial_state) + (x.damage_relative_tolerance,), strict=True):
                    scale = atol + rtol * max(abs(old), abs(b))
                    difference = abs(a - b)
                    if not math.isfinite(scale) or not math.isfinite(difference):
                        raise ArithmeticError("error_scale_or_difference_exceeds_numeric_support")
                    scaled_errors.append((difference / scale) / 15.0)
                error = max(scaled_errors)
            except _StateBound as event:
                rejected += 1
                if h <= x.minimum_step_cycles or rejected >= x.maximum_rejected_steps:
                    return stop(str(event), event_cycle_bracket=[coordinate, coordinate + h], event_is_exact=False)
                h = max(x.minimum_step_cycles, h * 0.5)
                continue
            except Exception as failure:
                return stop("provider_or_numerical_failure", failure_type=type(failure).__name__, failure_message=str(failure))
            if not math.isfinite(error):
                return stop("error_estimator_numerical_support_exceeded")
            if error > 1.0:
                rejected += 1
                if h <= x.minimum_step_cycles or rejected >= x.maximum_rejected_steps:
                    return stop("local_error_tolerance_unresolved_at_step_or_rejection_limit", last_scaled_local_error=error)
                h = max(x.minimum_step_cycles, h * max(0.1, 0.9 * error ** -0.2))
                continue
            if fine[-1] < state[-1]:
                return stop("accepted_trial_damage_not_monotone")
            if x.damage_event_threshold is not None and fine[-1] >= x.damage_event_threshold:
                return stop("damage_threshold_bracketed", event_cycle_bracket=[coordinate, coordinate + h],
                            trial_event_state=list(fine[:-1]), trial_event_damage=fine[-1], event_is_exact=False)
            coordinate = float(block.cycle_count) if h == remaining else coordinate + h
            state = fine
            accepted += 1
            maximum_accepted_error = max(maximum_accepted_error, error)
            h = min(x.maximum_step_cycles, h * (2.0 if error == 0.0 else min(2.0, max(0.5, 0.9 * error ** -0.2))))
        rows.append({"block_id": block.block_id, "block_input_sha256": block_digest,
                     "cycle_count": block.cycle_count, "initial_state": list(start_state[:-1]),
                     "final_state": list(state[:-1]), "initial_damage": start_state[-1],
                     "final_damage": state[-1], "damage_increment": state[-1] - start_state[-1]})
        completed_cycles += block.cycle_count
    return base | {"status": "computed", "completed_blocks": rows, "completed_integer_cycle_count": completed_cycles,
                   "final_state": list(state[:-1]), "final_damage": state[-1], "function_evaluations": evaluations,
                   "accepted_steps": accepted, "rejected_steps": rejected, "full_requested_history_completed": True,
                   "maximum_accepted_scaled_local_error": maximum_accepted_error,
                   "method": "RK4_step_doubling_fine_solution_no_Richardson_extrapolation",
                   "meaning": "caller cycle-count ODE numerical integration; no fatigue-law inference, material qualification, life or failure probability"}


def _registered_evaluator(request: AdaptiveCycleBlockDamageRequest, provider: Callable) -> Calculation:
    result = evaluate_adaptive_cycle_block_damage(request, provider)
    status = result.pop("status")
    return Calculation(
        status=status,
        values=result,
        notes=(
            "Caller-defined cycle-domain state and damage ODE only; no fatigue law, material qualification, life or failure probability is inferred.",
            "State output units follow the ordered state_units in the request; cycle count is an integer count, not elapsed time.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id=INTERFACE_ID,
            input_type=AdaptiveCycleBlockDamageRequest,
            evaluator=_registered_evaluator,
            units={
                "completed_integer_cycle_count": "1",
                "final_damage": "1",
                "accepted_damage": "1",
                "maximum_accepted_scaled_local_error": "1",
            },
            assumptions=(
                "The caller supplies a deterministic provider whose identity, revision and configuration digest match the request.",
                "State derivatives and nonnegative damage rate are defined per cycle in the ordered caller state basis.",
                "Adaptive RK4 step-doubling controls only local numerical error for the declared ODE and does not establish physical validity or global error bounds.",
                "Integer cycle blocks are caller-provided accounting partitions; the solver does not count cycles or infer a material failure law.",
            ),
            source_ids=(SOURCE_ID,),
            qualification="user_model",
            runtime_dependency_names=("provider",),
        )
    ]
