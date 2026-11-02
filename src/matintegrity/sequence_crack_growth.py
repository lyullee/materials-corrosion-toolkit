"""Ordered cycle stepping with explicit opening ratio and calibrated plastic-zone retardation."""

import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Positive, canonical_digest
from .models.crack import VariableParis


class SequenceGrowthState(Contract):
    depth_m: Positive
    plastic_zone_tip_m: Positive
    accumulated_cycles: int = Field(ge=0)
    law_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def digest(self):
        payload = self.model_dump(mode="json", exclude={"state_sha256"})
        if canonical_digest(payload) != self.state_sha256:
            raise ValueError("sequence state digest differs from its contents")
        return self


class SequenceCrackGrowth(Contract):
    growth: VariableParis
    yield_strength_Pa: Positive
    plastic_zone_coefficient: Positive
    retardation_exponent: Positive
    opening_K_fraction_of_maximum: float = Field(ge=0, lt=1)
    maximum_depth_increment_m: Positive
    maximum_cycle_steps: int = Field(ge=1, le=2_000_000)
    calibrated_sequence_law_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sequence_and_closure_law_reviewed: bool
    initial_state: SequenceGrowthState | None = None


def evaluate_sequence_crack_growth(request: SequenceCrackGrowth) -> dict:
    base = dict(input_sha256=canonical_digest(request.model_dump(mode="json")), status="needs_data")
    if not request.sequence_and_closure_law_reviewed:
        return base
    x = request.growth
    configuration = request.model_dump(mode="json", exclude={"initial_state", "maximum_cycle_steps"})
    configuration["growth"].pop("blocks")
    configuration["growth"].pop("initial_depth_m")
    law_digest = canonical_digest(configuration)
    if request.initial_state is not None:
        if (
            request.initial_state.depth_m != x.initial_depth_m
            or request.initial_state.law_configuration_sha256 != law_digest
        ):
            raise ValueError("resume state depth or law/geometry configuration differs from the request")
    if any(not float(block.cycles).is_integer() for block in x.blocks):
        raise ValueError("sequence stepping requires whole cycles in each ordered block")
    if sum(int(block.cycles) for block in x.blocks) > request.maximum_cycle_steps:
        return base | dict(reason="Declared cycle-step budget is insufficient")
    depth = x.initial_depth_m
    zone_tip = request.initial_state.plastic_zone_tip_m if request.initial_state is not None else depth
    prior_cycles = request.initial_state.accumulated_cycles if request.initial_state is not None else 0
    total = prior_cycles
    rows = []
    crossing_cycle_interval = None
    crossing_depth_m = None
    predicted_cycle_end_depth_m = None
    reason = "requested_blocks_completed"
    status = "computed"
    for block_index, block in enumerate(x.blocks):
        completed = 0
        minimum_factor = 1.0
        for _ in range(int(block.cycles)):
            if depth >= x.terminal_depth_m:
                reason = "depth_limit_reached"
                break
            if not x.geometry_depth_m[0] <= depth <= x.geometry_depth_m[-1]:
                status = "out_of_scope"
                reason = "geometry_support_exceeded"
                break
            factor = float(np.interp(depth, x.geometry_depth_m, x.geometry_factor))
            kmax = factor * block.maximum_stress_Pa * math.sqrt(math.pi * depth)
            kmin = factor * block.minimum_stress_Pa * math.sqrt(math.pi * depth)
            if kmax >= x.fracture_toughness_Pa_sqrt_m:
                reason = "fracture_toughness_reached"
                break
            if kmax == 0:
                completed += 1
                total += 1
                continue
            ratio = kmin / kmax
            if not x.minimum_calibrated_stress_ratio <= ratio <= x.maximum_calibrated_stress_ratio:
                status = "out_of_scope"
                reason = "stress_ratio_support_exceeded"
                break
            effective = kmax - max(kmin, request.opening_K_fraction_of_maximum * kmax)
            zone = request.plastic_zone_coefficient * (kmax / request.yield_strength_Pa) ** 2
            remaining = zone_tip - depth
            retardation = (
                min(1.0, (zone / remaining) ** request.retardation_exponent) if remaining > zone else 1.0
            )
            increment = 0.0
            if effective > x.threshold_delta_K_Pa_sqrt_m:
                if (
                    not x.minimum_calibrated_delta_K_Pa_sqrt_m
                    <= effective
                    <= x.maximum_calibrated_delta_K_Pa_sqrt_m
                ):
                    status = "out_of_scope"
                    reason = "effective_delta_K_support_exceeded"
                    break
                increment = retardation * x.coefficient_m_cycle_per_Pa_sqrt_m_power * effective**x.exponent
            if not math.isfinite(increment) or increment > request.maximum_depth_increment_m:
                status = "out_of_scope"
                reason = "cycle_increment_resolution_exceeded"
                break
            predicted = depth + increment
            assessed = min(predicted, x.terminal_depth_m)
            limit = x.terminal_depth_m
            limit_kind = "terminal_depth_crossed_within_cycle"
            if block.maximum_stress_Pa > 0:
                end_factor = float(np.interp(assessed, x.geometry_depth_m, x.geometry_factor))
                end_k = end_factor * block.maximum_stress_Pa * math.sqrt(math.pi * assessed)
                if end_k >= x.fracture_toughness_Pa_sqrt_m:
                    from scipy.optimize import brentq

                    limit = brentq(
                        lambda a: (
                            float(np.interp(a, x.geometry_depth_m, x.geometry_factor))
                            * block.maximum_stress_Pa
                            * math.sqrt(math.pi * a)
                            - x.fracture_toughness_Pa_sqrt_m
                        ),
                        depth,
                        assessed,
                        xtol=x.absolute_depth_tolerance_m,
                    )
                    limit_kind = "fracture_toughness_crossed_within_cycle"
            if predicted >= limit:
                reason = limit_kind
                crossing_cycle_interval = [total, total + 1]
                crossing_depth_m = limit
                predicted_cycle_end_depth_m = predicted
                break
            zone_tip = max(zone_tip, depth + zone)
            depth += increment
            minimum_factor = min(minimum_factor, retardation)
            completed += 1
            total += 1
        rows.append(
            dict(
                block_index=block_index,
                completed_cycles=completed,
                depth_m=depth,
                plastic_zone_tip_m=zone_tip,
                minimum_retardation_factor=minimum_factor,
            )
        )
        if reason != "requested_blocks_completed":
            break
    state_payload = dict(
        depth_m=depth,
        plastic_zone_tip_m=zone_tip,
        accumulated_cycles=total,
        law_configuration_sha256=law_digest,
    )
    state = SequenceGrowthState(**state_payload, state_sha256=canonical_digest(state_payload))
    return base | dict(
        status=status,
        termination_reason=reason,
        completed_cycles=total,
        completed_cycles_this_run=total - prior_cycles,
        final_state=state.model_dump(mode="json"),
        final_depth_m=depth,
        plastic_zone_tip_m=zone_tip,
        block_results=rows,
        unresolved_crossing_cycle_interval=crossing_cycle_interval,
        limiting_depth_m=crossing_depth_m,
        predicted_cycle_end_depth_m=predicted_cycle_end_depth_m,
        basis="Caller-calibrated opening ratio and plastic-zone memory law; whole-cycle explicit stepping with a declared increment bound. No overload-law calibration or engineering acceptance is inferred.",
    )
