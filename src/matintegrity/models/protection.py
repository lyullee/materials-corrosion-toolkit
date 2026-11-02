"""Cathodic-protection charge and current budgets using declared design inputs."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class CathodicBudget(Contract):
    time_s: list[Nonnegative] = Field(min_length=2)
    protected_area_m2: Positive
    bare_surface_fraction: list[Fraction] = Field(min_length=2)
    bare_surface_current_density_A_m2: list[Nonnegative] = Field(min_length=2)
    additional_current_drain_A: list[Nonnegative] = Field(min_length=2)
    anode_electrochemical_capacity_C_kg: Positive
    anode_utilization_fraction: float = Field(gt=0, le=1)
    single_anode_mass_kg: Positive
    single_anode_minimum_available_current_A: Positive
    installed_anodes: int = Field(ge=0)

    @model_validator(mode="after")
    def align(self):
        if (
            len(
                {
                    len(self.time_s),
                    len(self.bare_surface_fraction),
                    len(self.bare_surface_current_density_A_m2),
                    len(self.additional_current_drain_A),
                }
            )
            != 1
        ):
            raise ValueError("cathodic-demand vectors require one common clock")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("cathodic-demand clock must strictly increase")
        return self


def cathodic_budget(x: CathodicBudget) -> Calculation:
    charge = 0.0
    peak = 0.0
    peak_time = x.time_s[0]
    for k, (first, last) in enumerate(zip(x.time_s, x.time_s[1:], strict=False)):
        dt = last - first
        f = x.bare_surface_fraction[k]
        i = x.bare_surface_current_density_A_m2[k]
        d = x.additional_current_drain_A[k]
        df = x.bare_surface_fraction[k + 1] - f
        di = x.bare_surface_current_density_A_m2[k + 1] - i
        dd = x.additional_current_drain_A[k + 1] - d
        a = x.protected_area_m2 * df * di
        b = x.protected_area_m2 * (f * di + i * df) + dd
        c = x.protected_area_m2 * f * i + d
        charge += dt * (c + b / 2 + a / 3)
        candidates = [0.0, 1.0]
        if a != 0:
            stationary = -b / (2 * a)
            if 0 < stationary < 1:
                candidates.append(stationary)
        for u in candidates:
            value = a * u * u + b * u + c
            if value > peak:
                peak = value
                peak_time = first + dt * u
    usable_per_kg = x.anode_electrochemical_capacity_C_kg * x.anode_utilization_fraction
    required_mass = charge / usable_per_kg
    by_charge = math.ceil(required_mass / x.single_anode_mass_kg)
    by_current = math.ceil(peak / x.single_anode_minimum_available_current_A)
    charge_margin = x.installed_anodes * x.single_anode_mass_kg * usable_per_kg - charge
    current_margin = x.installed_anodes * x.single_anode_minimum_available_current_A - peak
    return Calculation(
        values=dict(
            required_charge_C=charge,
            mean_current_A=charge / (x.time_s[-1] - x.time_s[0]),
            peak_current_A=peak,
            peak_time_s=peak_time,
            required_continuous_anode_mass_kg=required_mass,
            minimum_anodes_by_charge=by_charge,
            minimum_anodes_by_peak_current=by_current,
            minimum_anodes_for_declared_budget=max(by_charge, by_current),
            installed_charge_margin_C=charge_margin,
            installed_peak_current_margin_A=current_margin,
            declared_budget_outcome="satisfied"
            if charge_margin >= 0 and current_margin >= 0
            else "not_satisfied",
        ),
        notes=(
            "Bare fraction, bare-surface current density and additional drain vary linearly between knots. Their product is integrated exactly and interior peak current is checked.",
            "Anode capacity, utilization and minimum available current are qualified caller inputs. Additive current output assumes the declared installation and interference basis.",
            "Charge/current sufficiency alone does not establish protective potential, polarization, shielding, overprotection limits or compliance with a cathodic-protection standard.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "protection.cathodic_budget",
            CathodicBudget,
            cathodic_budget,
            {
                "required_charge_C": "C",
                "mean_current_A": "A",
                "peak_current_A": "A",
                "peak_time_s": "s",
                "required_continuous_anode_mass_kg": "kg",
                "installed_charge_margin_C": "C",
                "installed_peak_current_margin_A": "A",
            },
            (
                "Declared piecewise-linear coating/current histories, charge capacity and an independent current-output bound.",
            ),
            ("charge_budget", "dod_cathodic_current"),
        )
    ]
