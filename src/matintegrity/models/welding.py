"""Welding-process screening models with user-supplied procedure and material data."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class HydrogenBakeoutSlab(Contract):
    """Diffusion-limited release from a finite planar weld region exposed on both faces."""

    procedure_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    diffusivity_source_id: str = Field(min_length=1)
    thickness_source_id: str = Field(min_length=1)
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=4096)
    temperature_K: list[Positive] = Field(min_length=2, max_length=4096)
    effective_diffusivity_m2_s: list[Positive] = Field(min_length=2, max_length=4096)
    slab_thickness_m: Positive
    initial_diffusible_hydrogen_atoms_mol_m3: Nonnegative
    both_faces_exposed_reviewed: bool = False
    uniform_initial_concentration_reviewed: bool = False
    diffusion_limited_surface_reviewed: bool = False
    diffusivity_history_reviewed: bool = False
    temperature_history_reviewed: bool = False
    series_absolute_tolerance: float = Field(default=1e-10, ge=1e-14, le=1e-4)
    maximum_series_terms: int = Field(default=200000, ge=10, le=1000000)

    @model_validator(mode="after")
    def aligned_history(self):
        count = len(self.elapsed_time_s)
        if self.elapsed_time_s[0] != 0 or any(
            later <= earlier
            for earlier, later in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)
        ):
            raise ValueError("bakeout elapsed time must start at zero and strictly increase")
        if len(self.temperature_K) != count or len(self.effective_diffusivity_m2_s) != count:
            raise ValueError("temperature and diffusivity must align with every bakeout time knot")
        return self


def _remaining_fraction(fourier_number: float, tolerance: float, maximum_terms: int):
    if fourier_number == 0:
        return 1.0, 0.0, 0
    total = 0.0
    pi2 = math.pi**2
    coefficient = 8.0 / pi2
    for index in range(maximum_terms):
        odd = 2 * index + 1
        total += coefficient * math.exp(-(odd * odd) * pi2 * fourier_number) / (odd * odd)
        next_index = index + 1
        next_odd = 2 * next_index + 1
        next_term = (
            coefficient * math.exp(-(next_odd * next_odd) * pi2 * fourier_number) / (next_odd * next_odd)
        )
        ratio_bound = math.exp(-8.0 * (next_index + 1) * pi2 * fourier_number)
        tail_bound = next_term / (1.0 - ratio_bound) if ratio_bound < 1.0 else math.inf
        if tail_bound <= tolerance:
            return min(1.0, max(0.0, total)), tail_bound, index + 1
    raise ArithmeticError("finite-slab series did not meet the requested absolute tail bound")


def hydrogen_bakeout_slab(x: HydrogenBakeoutSlab) -> Calculation:
    reviews = {
        "both_faces_exposed_reviewed": x.both_faces_exposed_reviewed,
        "uniform_initial_concentration_reviewed": x.uniform_initial_concentration_reviewed,
        "diffusion_limited_surface_reviewed": x.diffusion_limited_surface_reviewed,
        "diffusivity_history_reviewed": x.diffusivity_history_reviewed,
        "temperature_history_reviewed": x.temperature_history_reviewed,
    }
    missing = tuple(name for name, reviewed in reviews.items() if not reviewed)
    if missing:
        return Calculation(
            status="needs_data",
            values={"missing_reviews": list(missing)},
            notes=(
                "Bakeout screening is withheld until every geometry, boundary and history review is true.",
            ),
        )

    diffusion_time = [0.0]
    for index in range(1, len(x.elapsed_time_s)):
        duration = x.elapsed_time_s[index] - x.elapsed_time_s[index - 1]
        average_diffusivity = (
            x.effective_diffusivity_m2_s[index - 1] + x.effective_diffusivity_m2_s[index]
        ) / 2.0
        diffusion_time.append(diffusion_time[-1] + duration * average_diffusivity)

    remaining, tail_bounds, terms = [], [], []
    try:
        for value in diffusion_time:
            result, tail, count = _remaining_fraction(
                value / x.slab_thickness_m**2,
                x.series_absolute_tolerance,
                x.maximum_series_terms,
            )
            remaining.append(result)
            tail_bounds.append(tail)
            terms.append(count)
    except ArithmeticError as error:
        return Calculation(
            status="out_of_scope",
            values={"completed_time_knots": len(remaining)},
            notes=(str(error), "Increase the series budget or relax the declared numerical tolerance."),
        )

    released = [1.0 - value for value in remaining]
    initial_inventory = x.initial_diffusible_hydrogen_atoms_mol_m3 * x.slab_thickness_m
    return Calculation(
        values={
            "procedure_id": x.procedure_id,
            "material_condition_id": x.material_condition_id,
            "elapsed_time_s": x.elapsed_time_s,
            "temperature_K": x.temperature_K,
            "diffusion_time_m2": diffusion_time,
            "fourier_number": [value / x.slab_thickness_m**2 for value in diffusion_time],
            "remaining_diffusible_fraction": remaining,
            "released_diffusible_fraction": released,
            "mean_diffusible_hydrogen_atoms_mol_m3": [
                x.initial_diffusible_hydrogen_atoms_mol_m3 * value for value in remaining
            ],
            "cumulative_released_hydrogen_atoms_mol_m2": [initial_inventory * value for value in released],
            "series_tail_bound": tail_bounds,
            "series_terms_used": terms,
        },
        notes=(
            "Effective diffusivity is integrated as piecewise linear in elapsed time; temperature is retained as procedure evidence and does not generate hidden material properties.",
            "The exact finite-slab eigenfunction solution assumes an initially uniform diffusible concentration and zero surface concentration on both faces. Traps, phase changes, stress coupling, finite surface kinetics, weld heterogeneity and hydrogen cracking are outside this screening model.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "welding.hydrogen_bakeout_slab",
            HydrogenBakeoutSlab,
            hydrogen_bakeout_slab,
            {
                "elapsed_time_s": "s",
                "temperature_K": "K",
                "diffusion_time_m2": "m^2",
                "fourier_number": "1",
                "remaining_diffusible_fraction": "1",
                "released_diffusible_fraction": "1",
                "mean_diffusible_hydrogen_atoms_mol_m3": "mol/m^3",
                "cumulative_released_hydrogen_atoms_mol_m2": "mol/m^2",
                "series_tail_bound": "1",
                "series_terms_used": "count",
            },
            (
                "One-dimensional finite planar diffusion screening with an initially uniform diffusible-hydrogen field, zero concentration on both reviewed exposed faces and caller-supplied effective diffusivity history.",
            ),
            (
                "nist_hydrogen_outgassing",
                "hydrogen_bakeout_slab_derivation",
            ),
        )
    ]
