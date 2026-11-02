"""Reduced scale diffusion supply versus caller electrochemical demand balance."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

FARADAY_C_MOL = 96485.33212331001


class ScaleReactionDemandInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive
    effective_diffusivity_m2_s: Positive
    interface_transfer_coefficient_m_s: Positive
    reservoir_driving_concentration_mol_m3: Nonnegative
    scale_consumption_flux_mol_m2_s: Nonnegative | None = None
    signed_partial_current_density_A_m2: float | None = None

    @model_validator(mode="after")
    def one_demand_and_duration(self):
        if (self.scale_consumption_flux_mol_m2_s is None) == (self.signed_partial_current_density_A_m2 is None):
            raise ValueError("declare exactly one solid-consumption flux or signed partial current")
        if self.end_time_s <= self.start_time_s or not math.isfinite(self.end_time_s - self.start_time_s):
            raise ValueError("interval duration must be finite and positive")
        return self


class PlanarScaleReactionDemandBalance(Contract):
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    transported_reactant_id: str = Field(min_length=1)
    demand_reaction_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_scale_thickness_m: Nonnegative
    scale_molar_volume_m3_mol: Positive
    transported_reactant_moles_per_scale_mole: Positive
    electrons_per_reaction_extent: Positive | None = None
    consumed_scale_moles_per_reaction_extent: Positive | None = None
    consuming_partial_current_sign: Literal["positive", "negative"] | None = None
    temperature_support_min_K: Positive
    temperature_support_max_K: Positive
    intervals: tuple[ScaleReactionDemandInterval, ...] = Field(min_length=1, max_length=10000)
    maximum_scalar_iterations: int = Field(default=160, ge=8, le=1000)
    thickness_tolerance_m: Positive = Field(default=1e-12)
    time_tolerance_s: Positive = Field(default=1e-9)
    fixed_planar_dense_single_phase_and_area_reviewed: bool
    quasi_steady_series_resistance_and_reservoir_reviewed: bool
    stoichiometry_and_surface_consumption_balance_reviewed: bool
    signed_partial_current_mapping_reviewed: bool = False
    interval_parameter_temperature_support_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent(self):
        if self.temperature_support_max_K < self.temperature_support_min_K:
            raise ValueError("temperature support is reversed")
        if any(not self.temperature_support_min_K <= i.temperature_K <= self.temperature_support_max_K for i in self.intervals):
            raise ValueError("interval temperature lies outside parameter support")
        if len({i.interval_id for i in self.intervals}) != len(self.intervals):
            raise ValueError("interval IDs must be unique")
        if any(a.end_time_s != b.start_time_s for a, b in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous and ordered")
        mappings = (self.electrons_per_reaction_extent, self.consumed_scale_moles_per_reaction_extent, self.consuming_partial_current_sign)
        if any(value is not None for value in mappings) and not all(value is not None for value in mappings):
            raise ValueError("Faraday mapping requires electrons, solid stoichiometry and consuming sign together")
        for interval in self.intervals:
            current = interval.signed_partial_current_density_A_m2
            if current is not None:
                if not all(value is not None for value in mappings) or not self.signed_partial_current_mapping_reviewed:
                    raise ValueError("partial current requires reviewed explicit Faraday mapping")
                if (self.consuming_partial_current_sign == "positive" and current < 0.0) or (self.consuming_partial_current_sign == "negative" and current > 0.0):
                    raise ValueError("partial current sign is opposite the declared consuming direction")
        if not any(e.source_id == self.provider_id and e.sha256 == self.parameter_record_sha256 and e.license_id for e in self.evidence):
            raise ValueError("provider record requires digest-matched Evidence with declared usage-license identity")
        return self


def _log_remainder(u: float) -> float:
    if u >= 1.0:
        return math.inf
    if u < 1e-4:
        return sum(u ** order / order for order in range(2, 9))
    return -math.log1p(-u) - u


def _advance(length, a, supply, demand, duration, iterations, length_tol, time_tol):
    """Solve L'=supply/(L+a)-demand with monotone scalar inversion."""
    if duration == 0.0:
        return length, duration, False, 0
    if supply == 0.0 and demand == 0.0:
        return length, duration, False, 0
    if demand == 0.0:
        state = length * (length + 2.0 * a) + 2.0 * supply * duration
        radicand = a * a + state
        if not all(math.isfinite(value) for value in (state, radicand)):
            raise ArithmeticError("zero-demand root exceeds finite numerical support")
        root = math.sqrt(radicand)
        if not math.isfinite(root + a):
            raise ArithmeticError("zero-demand root denominator exceeds finite support")
        final = state / (root + a)
        if final < length or (supply > 0.0 and duration > 0.0 and final == length):
            raise ArithmeticError("zero-demand growth lost through floating-point range limits")
        return final, duration, False, 0
    if supply == 0.0:
        depletion = length / demand
        if length > 0.0 and depletion == 0.0:
            raise ArithmeticError("positive depletion time underflowed to zero")
        used = min(duration, depletion)
        depleted = depletion <= duration
        final = 0.0 if depleted else length - demand * duration
        if not depleted and duration > 0.0 and final == length:
            raise ArithmeticError("positive demand-only shrinkage lost below thickness spacing")
        return final, used, depleted, 0
    equilibrium_y = supply / demand
    y0 = length + a
    distance = equilibrium_y - y0
    if equilibrium_y <= 0.0 or not all(math.isfinite(value) for value in (equilibrium_y, y0, distance)):
        raise ArithmeticError("equilibrium coordinate exceeds finite support")
    if distance == 0.0:
        return length, duration, False, 0
    def elapsed(u):
        return (y0 * u + equilibrium_y * _log_remainder(u)) / demand
    upper = 1.0
    if equilibrium_y < a:
        event_u = length / (-distance)
        event_time = elapsed(event_u)
        if length > 0.0 and event_time == 0.0:
            raise ArithmeticError("positive depletion time underflowed to zero")
        if event_time <= duration:
            return 0.0, event_time, True, 0
        upper = event_u
    low = 0.0
    for count in range(1, iterations + 1):
        middle = low + (upper - low) * 0.5
        if not low < middle < upper:
            raise ArithmeticError("scalar inversion exhausted floating-point resolution")
        t = elapsed(middle)
        if t < duration:
            low = middle
        else:
            upper = middle
        if abs(distance) * (upper - low) <= length_tol or abs(t - duration) <= time_tol:
            final = length + distance * middle
            if duration > 0.0 and final == length:
                raise ArithmeticError("non-equilibrium thickness change lost below floating-point spacing")
            if length > 0.0 and final == 0.0:
                raise ArithmeticError("positive thickness underflowed to zero before the depletion event")
            return final, duration, False, count
    raise ArithmeticError("scalar inversion budget exhausted")


def planar_scale_reaction_demand_balance(x: PlanarScaleReactionDemandBalance) -> Calculation:
    base = {"assessment_id": x.assessment_id, "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id, "input_sha256": canonical_digest(x.model_dump(mode="json")),
            "scale_phase_id": x.scale_phase_id, "transported_reactant_id": x.transported_reactant_id,
            "demand_reaction_id": x.demand_reaction_id, "parameter_record_sha256": x.parameter_record_sha256}
    if not all((x.fixed_planar_dense_single_phase_and_area_reviewed,
                x.quasi_steady_series_resistance_and_reservoir_reviewed,
                x.stoichiometry_and_surface_consumption_balance_reviewed,
                x.interval_parameter_temperature_support_reviewed, x.computational_use_authorized)):
        return Calculation(status="needs_data", values=base)
    length = x.initial_scale_thickness_m
    rows = []
    for interval in x.intervals:
        try:
            flux = interval.scale_consumption_flux_mol_m2_s
            if flux is None:
                charge_per_extent = x.electrons_per_reaction_extent * FARADAY_C_MOL
                if not math.isfinite(charge_per_extent) or charge_per_extent <= 0.0:
                    raise ArithmeticError("Faraday charge mapping exceeds numerical support")
                flux = (abs(interval.signed_partial_current_density_A_m2) / charge_per_extent) * x.consumed_scale_moles_per_reaction_extent
                if interval.signed_partial_current_density_A_m2 != 0.0 and flux == 0.0:
                    raise ArithmeticError("nonzero partial current mapped to zero by numerical underflow")
            a = interval.effective_diffusivity_m2_s / interval.interface_transfer_coefficient_m_s
            supply = x.scale_molar_volume_m3_mol * interval.effective_diffusivity_m2_s * interval.reservoir_driving_concentration_mol_m3 / x.transported_reactant_moles_per_scale_mole
            demand = x.scale_molar_volume_m3_mol * flux
            if not all(math.isfinite(v) for v in (a, supply, demand)) or a <= 0.0:
                raise ArithmeticError("coefficient numerical support exceeded")
            if (flux > 0.0 and demand == 0.0) or (interval.reservoir_driving_concentration_mol_m3 > 0.0 and supply == 0.0):
                raise ArithmeticError("nonzero physical coefficient underflowed to zero")
            if length == 0.0 and supply / a <= demand:
                return Calculation(values=base | {"history": rows, "termination": "scale_absent", "full_requested_history_completed": False, "termination_time_s": interval.start_time_s, "final_thickness_m": 0.0})
            final, used, depleted, count = _advance(length, a, supply, demand, interval.end_time_s - interval.start_time_s, x.maximum_scalar_iterations, x.thickness_tolerance_m, x.time_tolerance_s)
            consumed = flux * used
            net = (final - length) / x.scale_molar_volume_m3_mol
            supplied = net + consumed
            transported = supplied * x.transported_reactant_moles_per_scale_mole
            if not all(math.isfinite(v) for v in (final, used, consumed, net, supplied, transported)) or final < 0.0 or supplied < 0.0:
                raise ArithmeticError("state or balance numerical support exceeded")
        except (ArithmeticError, ValueError, OverflowError) as error:
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": rows, "failed_interval_id": interval.interval_id, "reason": str(error)})
        rows.append({"interval_id": interval.interval_id, "start_time_s": interval.start_time_s,
                     "end_time_s": interval.start_time_s + used if depleted else interval.end_time_s,
                     "temperature_K": interval.temperature_K, "initial_thickness_m": length,
                     "final_thickness_m": final, "consumed_scale_mol_m2": consumed,
                     "supplied_scale_equivalent_mol_m2": supplied,
                     "transported_reactant_mol_m2": transported,
                     "net_scale_change_mol_m2": net, "scalar_iterations": count,
                     "scale_depleted": depleted})
        length = final
        if depleted:
            return Calculation(values=base | {"history": rows, "termination": "scale_depleted", "full_requested_history_completed": False, "termination_time_s": rows[-1]["end_time_s"], "final_thickness_m": length})
    return Calculation(values=base | {"history": rows, "termination": "requested_end", "full_requested_history_completed": True, "final_thickness_m": length}, notes=("Reduced single-species surface balance only; electrode potential, mixed potential and current feedback are not solved.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec("chemistry.planar_scale_reaction_demand_balance", PlanarScaleReactionDemandBalance,
        planar_scale_reaction_demand_balance,
        {"final_thickness_m": "m", "history[].consumed_scale_mol_m2": "mol/m2", "history[].transported_reactant_mol_m2": "mol/m2"},
        ("Single dense planar scale with quasi-steady diffusion/interface resistance and caller constant consuming reaction demand per interval.",
         "Explicit reactant/solid stoichiometry; optional reviewed sign-specific partial-current Faraday mapping; no net-current inference.",
         "Stop at scale depletion; no absent-scale substrate, finite reservoir, potential solve, kinetic-current feedback, porosity or adhesion model."),
        ("caller_planar_scale_reaction_demand_balance",), qualification="user_model")]
