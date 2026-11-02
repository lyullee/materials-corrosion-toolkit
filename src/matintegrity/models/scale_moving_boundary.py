"""Exact planar scale growth under caller-reviewed series transport resistance."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class ScaleDiffusionReactionInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    effective_diffusivity_m2_s: Positive
    interface_transfer_coefficient_m_s: Positive
    signed_reservoir_driving_concentration_mol_m3: float
    temperature_K: Positive

    @model_validator(mode="after")
    def duration(self):
        if self.end_time_s <= self.start_time_s or not math.isfinite(self.end_time_s - self.start_time_s):
            raise ValueError("interval requires a positive finite duration")
        return self


class PlanarScaleDiffusionReactionHistory(Contract):
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    transported_species_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_thickness_m: Nonnegative
    scale_molar_volume_m3_mol: Positive
    temperature_support_min_K: Positive
    temperature_support_max_K: Positive
    intervals: tuple[ScaleDiffusionReactionInterval, ...] = Field(min_length=1, max_length=100000)
    fixed_planar_area_dense_single_phase_reviewed: bool
    quasi_steady_series_resistance_and_reservoir_reviewed: bool
    signed_driving_force_and_one_to_one_molar_balance_reviewed: bool
    interval_properties_and_temperature_support_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def contiguous(self):
        if self.temperature_support_max_K < self.temperature_support_min_K:
            raise ValueError("temperature support maximum must not be below its minimum")
        if any(
            row.temperature_K < self.temperature_support_min_K
            or row.temperature_K > self.temperature_support_max_K
            for row in self.intervals
        ):
            raise ValueError("every interval temperature must lie inside the declared support")
        if len({row.interval_id for row in self.intervals}) != len(self.intervals):
            raise ValueError("interval IDs must be unique")
        if any(a.end_time_s != b.start_time_s for a, b in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous and ordered")
        if self.provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("parameter provider requires declared Evidence")
        return self


def planar_scale_diffusion_reaction_history(x: PlanarScaleDiffusionReactionHistory) -> Calculation:
    """Integrate dL/dt=Vm*D*delta_c/(L+D/k), stopping at scale depletion."""
    base = {
        "assessment_id": x.assessment_id,
        "physical_scope_id": x.physical_scope_id,
        "clock_id": x.clock_id,
        "scale_phase_id": x.scale_phase_id,
        "transported_species_id": x.transported_species_id,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "configuration_sha256": x.configuration_sha256,
    }
    if not all((x.fixed_planar_area_dense_single_phase_reviewed,
                x.quasi_steady_series_resistance_and_reservoir_reviewed,
                x.signed_driving_force_and_one_to_one_molar_balance_reviewed,
                x.interval_properties_and_temperature_support_reviewed,
                x.computational_use_authorized)):
        return Calculation(status="needs_data", values=base, notes=("Required physical and use reviews are incomplete.",))
    thickness = float(x.initial_thickness_m)
    rows = []
    for interval in x.intervals:
        resistance_length = interval.effective_diffusivity_m2_s / interval.interface_transfer_coefficient_m_s
        coefficient = x.scale_molar_volume_m3_mol * interval.effective_diffusivity_m2_s * interval.signed_reservoir_driving_concentration_mol_m3
        duration = interval.end_time_s - interval.start_time_s
        # L^2 + 2*a*L is the integrated state; stop before the absent-scale regime.
        inventory_state = thickness * (thickness + 2.0 * resistance_length)
        depletion_time = inventory_state / (-2.0 * coefficient) if coefficient < 0.0 else None
        depleted = depletion_time is not None and depletion_time <= duration
        used_duration = depletion_time if depleted else duration
        target = inventory_state + 2.0 * coefficient * used_duration
        radicand = resistance_length * resistance_length + target
        if resistance_length <= 0.0 or not all(math.isfinite(value) for value in (resistance_length, coefficient, inventory_state, target, radicand)) or (not depleted and (target < 0.0 or radicand < 0.0)):
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": rows, "failed_interval_id": interval.interval_id}, notes=("Finite numerical support was exceeded; no further interval was evaluated.",))
        # Rationalized positive root avoids subtracting two close positive values.
        final = 0.0 if depleted else target / (math.sqrt(radicand) + resistance_length)
        if not math.isfinite(final) or final < 0.0:
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": rows, "failed_interval_id": interval.interval_id})
        transfer = (final - thickness) / x.scale_molar_volume_m3_mol
        if not math.isfinite(transfer):
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": rows, "failed_interval_id": interval.interval_id}, notes=("Molar transfer exceeds finite numerical support.",))
        rows.append({
            "interval_id": interval.interval_id,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.start_time_s + used_duration if depleted else interval.end_time_s,
            "temperature_K": interval.temperature_K,
            "initial_thickness_m": thickness,
            "final_thickness_m": final,
            "signed_scale_molar_transfer_mol_m2": transfer,
            "scale_depleted": depleted,
        })
        thickness = final
        if depleted:
            return Calculation(values=base | {"history": rows, "termination": "scale_depleted", "full_requested_history_completed": False, "final_thickness_m": thickness}, notes=("The absent-scale regime and subsequent substrate exposure are not modeled; the history terminates at the depletion event.",))
    return Calculation(values=base | {"history": rows, "termination": "requested_end", "full_requested_history_completed": True, "final_thickness_m": thickness}, notes=("An exact integration of a restricted caller-reviewed planar resistance law is not corrosion-rate or protective-scale qualification.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.planar_scale_diffusion_reaction_history",
        PlanarScaleDiffusionReactionHistory,
        planar_scale_diffusion_reaction_history,
        {"final_thickness_m": "m", "history[].signed_scale_molar_transfer_mol_m2": "mol/m2"},
        ("Fixed-area dense single-phase planar scale; one-to-one transported-species/solid molar balance.",
         "Piecewise-constant caller diffusivity, interfacial coefficient and signed reservoir concentration difference; quasi-steady series resistance.",
         "No nucleation, porosity, adhesion, finite reservoir, electrode feedback or substrate corrosion prediction; stop at scale depletion."),
        ("caller_planar_scale_diffusion_reaction_balance",),
        qualification="user_model",
    )]
