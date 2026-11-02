"""One-dimensional finite-volume diffusion of a caller-defined crevice component.

The transported scalar is defined by the caller.  The model does not infer ionic
electromigration, aqueous reactions, activities, pH, electrochemical kinetics or
corrosion damage.  Provider-bounded diffusivity and source histories remain
explicit evidence inputs.
"""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import (
    Calculation,
    Contract,
    Evidence,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec


class CreviceComponentDiffusionSupport(Contract):
    support_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    bulk_solution_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_gap_m: Positive
    maximum_gap_m: Positive
    minimum_diffusivity_m2_s: Positive
    maximum_diffusivity_m2_s: Positive
    maximum_supported_component_concentration_mol_m3: Positive
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_model_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        for lower, upper, label in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_gap_m, self.maximum_gap_m, "gap"),
            (self.minimum_diffusivity_m2_s, self.maximum_diffusivity_m2_s, "diffusivity"),
        ):
            if upper < lower:
                raise ValueError(f"crevice component {label} support must be ordered")
        return self


class CreviceComponentDiffusionInterval(Contract):
    interval_id: str = Field(min_length=1)
    support_id: str = Field(min_length=1)
    temperature_K: Positive
    gap_m: Positive
    diffusivity_m2_s: Positive
    mouth_component_concentration_mol_m3: Nonnegative
    volumetric_component_source_mol_m3_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    provider_state_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_provider_record(self):
        if any(not math.isfinite(value) for value in self.volumetric_component_source_mol_m3_s):
            raise ValueError("crevice component source values must be finite")
        if self.record_valid and self.provider_state_digest is None:
            raise ValueError("a valid crevice component interval requires a provider-state digest")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid crevice component interval requires a basis")
        return self


class CreviceComponentDiffusionHistory(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    component_definition: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    bulk_solution_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    crevice_length_m: Positive
    constant_cross_section_area_m2: Positive
    cell_count: int = Field(ge=2, le=500)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=5000)
    initial_component_concentration_mol_m3: tuple[Nonnegative, ...] = Field(min_length=2, max_length=500)
    intervals: tuple[CreviceComponentDiffusionInterval, ...] = Field(min_length=1, max_length=4999)
    supports: tuple[CreviceComponentDiffusionSupport, ...] = Field(min_length=1)
    maximum_internal_step_s: Positive
    maximum_relative_mass_balance_error: Nonnegative
    geometry_and_constant_cross_section_reviewed: bool
    component_definition_and_initial_state_reviewed: bool
    mouth_boundary_and_closed_tip_reviewed: bool
    independent_fickian_component_transport_reviewed: bool
    diffusivity_and_source_provider_reviewed: bool
    clock_and_interval_alignment_reviewed: bool
    numerical_step_and_balance_tolerance_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_history(self):
        if len(self.initial_component_concentration_mol_m3) != self.cell_count:
            raise ValueError("one initial crevice component concentration is required per cell")
        if len(self.intervals) != len(self.elapsed_time_s) - 1:
            raise ValueError("one crevice component interval is required per clock interval")
        if any(
            right <= left for left, right in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)
        ):
            raise ValueError("crevice component clock must strictly increase")
        if any(len(row.volumetric_component_source_mol_m3_s) != self.cell_count for row in self.intervals):
            raise ValueError("one volumetric component source is required per cell and interval")
        for values, label in (
            ([row.interval_id for row in self.intervals], "interval"),
            ([row.support_id for row in self.supports], "support"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"crevice component {label} IDs must be unique")
        return self


def _solve_tridiagonal(lower: list[float], diagonal: list[float], upper: list[float], rhs: list[float]):
    """Thomas solution for a strictly diagonally dominant tridiagonal system."""
    count = len(diagonal)
    c_prime = [0.0] * (count - 1)
    d_prime = [0.0] * count
    pivot = diagonal[0]
    if pivot <= 0.0 or not math.isfinite(pivot):
        raise ArithmeticError("crevice diffusion matrix has an invalid first pivot")
    c_prime[0] = upper[0] / pivot
    d_prime[0] = rhs[0] / pivot
    for index in range(1, count):
        pivot = diagonal[index] - lower[index - 1] * c_prime[index - 1]
        if pivot <= 0.0 or not math.isfinite(pivot):
            raise ArithmeticError("crevice diffusion matrix has an invalid pivot")
        if index < count - 1:
            c_prime[index] = upper[index] / pivot
        d_prime[index] = (rhs[index] - lower[index - 1] * d_prime[index - 1]) / pivot
    solution = [0.0] * count
    solution[-1] = d_prime[-1]
    for index in range(count - 2, -1, -1):
        solution[index] = d_prime[index] - c_prime[index] * solution[index + 1]
    return solution


def _implicit_diffusion_step(
    concentration: list[float],
    diffusivity: float,
    cell_width: float,
    step_s: float,
    mouth_concentration: float,
    source: tuple[float, ...],
) -> list[float]:
    count = len(concentration)
    ratio = diffusivity * step_s / cell_width**2
    lower = [-ratio] * (count - 1)
    upper = [-ratio] * (count - 1)
    diagonal = [1.0 + 2.0 * ratio] * count
    diagonal[0] = 1.0 + 3.0 * ratio
    diagonal[-1] = 1.0 + ratio
    rhs = [value + step_s * rate for value, rate in zip(concentration, source, strict=True)]
    rhs[0] += 2.0 * ratio * mouth_concentration
    return _solve_tridiagonal(lower, diagonal, upper, rhs)


def crevice_component_diffusion_history(x: CreviceComponentDiffusionHistory) -> Calculation:
    supports = {row.support_id: row for row in x.supports}
    missing_reviews = [
        name
        for name, reviewed in (
            ("geometry_and_constant_cross_section", x.geometry_and_constant_cross_section_reviewed),
            ("component_definition_and_initial_state", x.component_definition_and_initial_state_reviewed),
            ("mouth_boundary_and_closed_tip", x.mouth_boundary_and_closed_tip_reviewed),
            (
                "independent_fickian_component_transport",
                x.independent_fickian_component_transport_reviewed,
            ),
            ("diffusivity_and_source_provider", x.diffusivity_and_source_provider_reviewed),
            ("clock_and_interval_alignment", x.clock_and_interval_alignment_reviewed),
            (
                "numerical_step_and_balance_tolerance",
                x.numerical_step_and_balance_tolerance_reviewed,
            ),
        )
        if not reviewed
    ]
    invalid_intervals = [row.interval_id for row in x.intervals if not row.record_valid]
    unmatched_intervals = [row.interval_id for row in x.intervals if row.support_id not in supports]
    support_identity_mismatches = []
    for support in x.supports:
        fields = [
            field
            for field in (
                "component_id",
                "material_condition_id",
                "bulk_solution_id",
                "geometry_id",
            )
            if getattr(support, field) != getattr(x, field)
        ]
        if fields:
            support_identity_mismatches.append({"support_id": support.support_id, "fields": fields})
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "clock_id": x.clock_id,
        "component_id": x.component_id,
        "geometry_id": x.geometry_id,
        "cell_center_position_m": [
            (index + 0.5) * x.crevice_length_m / x.cell_count for index in range(x.cell_count)
        ],
    }
    if missing_reviews or invalid_intervals or unmatched_intervals or support_identity_mismatches:
        return Calculation(
            status="needs_data",
            values=base
            | {
                "missing_reviews": missing_reviews,
                "invalid_interval_ids": invalid_intervals,
                "unmatched_interval_ids": unmatched_intervals,
                "support_identity_mismatches": support_identity_mismatches,
            },
        )

    outside_support = []
    for interval in x.intervals:
        support = supports[interval.support_id]
        fields = []
        if not support.minimum_temperature_K <= interval.temperature_K <= support.maximum_temperature_K:
            fields.append("temperature")
        if not support.minimum_gap_m <= interval.gap_m <= support.maximum_gap_m:
            fields.append("gap")
        if (
            not support.minimum_diffusivity_m2_s
            <= interval.diffusivity_m2_s
            <= support.maximum_diffusivity_m2_s
        ):
            fields.append("diffusivity")
        if (
            interval.mouth_component_concentration_mol_m3
            > support.maximum_supported_component_concentration_mol_m3
        ):
            fields.append("mouth_component_concentration")
        if fields:
            outside_support.append({"interval_id": interval.interval_id, "fields": fields})
    initial_limit = supports[x.intervals[0].support_id].maximum_supported_component_concentration_mol_m3
    if max(x.initial_component_concentration_mol_m3) > initial_limit:
        outside_support.append({"interval_id": None, "fields": ["initial_component_concentration"]})
    if outside_support:
        return Calculation(
            status="out_of_scope",
            values=base | {"outside_support": outside_support},
            notes=("Reviewed transport conditions lie outside caller-declared provider support.",),
        )

    cell_width = x.crevice_length_m / x.cell_count
    cell_volume = x.constant_cross_section_area_m2 * cell_width
    concentration = list(x.initial_component_concentration_mol_m3)
    history = [
        {
            "time_s": x.elapsed_time_s[0],
            "component_concentration_mol_m3": list(concentration),
            "total_component_amount_mol": math.fsum(concentration) * cell_volume,
        }
    ]
    interval_balances = []
    maximum_balance_error = 0.0
    for interval_index, interval in enumerate(x.intervals):
        start_time = x.elapsed_time_s[interval_index]
        end_time = x.elapsed_time_s[interval_index + 1]
        duration = end_time - start_time
        substep_count = max(1, math.ceil(duration / x.maximum_internal_step_s))
        step_s = duration / substep_count
        initial_amount = math.fsum(concentration) * cell_volume
        boundary_transfer = 0.0
        source_transfer = 0.0
        support = supports[interval.support_id]
        for _ in range(substep_count):
            updated = _implicit_diffusion_step(
                concentration,
                interval.diffusivity_m2_s,
                cell_width,
                step_s,
                interval.mouth_component_concentration_mol_m3,
                interval.volumetric_component_source_mol_m3_s,
            )
            minimum = min(updated)
            maximum = max(updated)
            if minimum < -1e-12 or not all(math.isfinite(value) for value in updated):
                return Calculation(
                    status="out_of_scope",
                    values=base
                    | {
                        "failed_interval_index": interval_index,
                        "failure_reason": "computed concentration became negative or non-finite",
                        "computed_history": history,
                    },
                )
            if maximum > support.maximum_supported_component_concentration_mol_m3:
                return Calculation(
                    status="out_of_scope",
                    values=base
                    | {
                        "failed_interval_index": interval_index,
                        "failure_reason": "computed concentration exceeded provider support",
                        "computed_history": history,
                    },
                )
            updated = [max(0.0, value) for value in updated]
            boundary_transfer += (
                2.0
                * interval.diffusivity_m2_s
                * x.constant_cross_section_area_m2
                / cell_width
                * (interval.mouth_component_concentration_mol_m3 - updated[0])
                * step_s
            )
            source_transfer += math.fsum(interval.volumetric_component_source_mol_m3_s) * cell_volume * step_s
            concentration = updated
        final_amount = math.fsum(concentration) * cell_volume
        residual = final_amount - initial_amount - boundary_transfer - source_transfer
        scale = max(
            abs(initial_amount),
            abs(final_amount),
            abs(boundary_transfer),
            abs(source_transfer),
            1e-30,
        )
        relative_error = abs(residual) / scale
        maximum_balance_error = max(maximum_balance_error, relative_error)
        interval_balances.append(
            {
                "interval_id": interval.interval_id,
                "start_time_s": start_time,
                "end_time_s": end_time,
                "internal_step_count": substep_count,
                "mouth_boundary_transfer_mol": boundary_transfer,
                "volumetric_source_transfer_mol": source_transfer,
                "inventory_change_mol": final_amount - initial_amount,
                "mass_balance_residual_mol": residual,
                "relative_mass_balance_error": relative_error,
            }
        )
        history.append(
            {
                "time_s": end_time,
                "component_concentration_mol_m3": list(concentration),
                "total_component_amount_mol": final_amount,
            }
        )
        if relative_error > x.maximum_relative_mass_balance_error:
            return Calculation(
                status="out_of_scope",
                values=base
                | {
                    "failed_interval_index": interval_index,
                    "failure_reason": "relative mass-balance error exceeded the reviewed tolerance",
                    "computed_history": history,
                    "interval_mass_balance": interval_balances,
                },
            )

    return Calculation(
        values=base
        | {
            "concentration_history": history,
            "concentration_history_sha256": canonical_digest(history),
            "interval_mass_balance": interval_balances,
            "maximum_relative_mass_balance_error": maximum_balance_error,
            "boundary_condition": "fixed mouth concentration and closed no-flux tip",
            "spatial_discretization": "cell-centered finite volume",
            "time_discretization": "backward Euler with piecewise-constant interval inputs",
        },
        notes=(
            "The transported component is caller-defined; the calculation does not establish individual ionic species concentrations.",
            "Electromigration, electroneutral coupling, activity corrections, homogeneous reactions, precipitation, pH, electrochemical kinetics and geometry change are excluded.",
        ),
    )


def _validate_context(x: CreviceComponentDiffusionHistory, context: RunContext) -> None:
    if context.asset_id != x.asset_id:
        raise ValueError("run context asset must match the crevice component history")
    if context.location_id != x.location_id:
        raise ValueError("run context location must match the crevice component history")
    if context.time_basis != x.clock_id:
        raise ValueError("run context time basis must match the crevice component clock ID")


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "transport.crevice_component_diffusion_1d",
            CreviceComponentDiffusionHistory,
            crevice_component_diffusion_history,
            {
                "cell_center_position_m": "m",
                "concentration_history[].time_s": "s",
                "concentration_history[].component_concentration_mol_m3": "mol/m^3",
                "concentration_history[].total_component_amount_mol": "mol",
                "interval_mass_balance[].mouth_boundary_transfer_mol": "mol",
                "interval_mass_balance[].volumetric_source_transfer_mol": "mol",
                "interval_mass_balance[].inventory_change_mol": "mol",
                "interval_mass_balance[].mass_balance_residual_mol": "mol",
                "interval_mass_balance[].relative_mass_balance_error": "1",
                "maximum_relative_mass_balance_error": "1",
            },
            (
                "A caller-defined scalar component diffuses along a constant-cross-section one-dimensional crevice with fixed mouth concentration and a closed tip.",
                "Diffusivity, mouth concentration and cellwise volumetric source are piecewise constant over each caller clock interval.",
                "Backward-Euler cell-centered finite volumes preserve an explicit component balance; provider support prevents hidden property or concentration extrapolation.",
            ),
            ("finite_volume_fick_component_diffusion", "declared_crevice_transport_provider"),
            qualification="user_model",
            context_validator=_validate_context,
        )
    ]
