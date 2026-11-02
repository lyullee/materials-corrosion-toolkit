"""Bind a layered-scale diffusion flux limit to a complete electrode reaction set."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Contract, canonical_digest


class ScaleLimitedSurfaceFlux(Contract):
    """Reviewed binding between one scale transport assessment and an electrode boundary."""

    scale_transport_result: AssessmentResult
    scale_transport_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    solution_condition_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    scale_state_id: str = Field(min_length=1)
    transported_species_id: str = Field(min_length=1)
    surface_area_basis_id: str | None = Field(default=None, min_length=1)
    limited_reaction_ids: tuple[str, ...] = Field(min_length=1)
    application_location: Literal["tip", "wall"]
    complete_species_production_branch_set_reviewed: bool
    diffusion_bound_and_surface_area_basis_reviewed: bool
    scale_state_constant_over_transport_horizon_reviewed: bool
    metal_potential_and_solution_reference_compatible_reviewed: bool
    electrochemical_and_scale_physical_scope_match_reviewed: bool

    @model_validator(mode="after")
    def result_lineage_and_support(self):
        result = self.scale_transport_result
        if canonical_digest(result.model_dump(mode="json")) != self.scale_transport_result_sha256:
            raise ValueError("scale transport result digest does not match the pinned result")
        if result.status != "computed" or result.model_id != "chemistry.layered_scale_diffusion_limit":
            raise ValueError("a computed layered-scale transport assessment is required")
        if result.units.get("area_average_flux_limit_mol_m2_s") != "mol/m2/s":
            raise ValueError("scale transport assessment does not declare the expected molar-flux unit")
        values = result.values
        expected = {
            "physical_scope_id": self.physical_scope_id,
            "substrate_condition_id": self.substrate_condition_id,
            "solution_condition_id": self.solution_condition_id,
            "scale_phase_id": self.scale_phase_id,
            "scale_state_id": self.scale_state_id,
            "transported_species_id": self.transported_species_id,
        }
        if any(values.get(key) != value for key, value in expected.items()):
            raise ValueError("scale result scope, state or transported species differs from the boundary mapping")
        if values.get("surface_area_basis_id") != self.surface_area_basis_id:
            raise ValueError("scale result surface-area basis differs from the boundary mapping")
        if values.get("scale_history_result_digest") is not None and values.get("scale_history_mapping_reviewed") is not True:
            raise ValueError("linked scale state must include its reviewed history mapping")
        cap = values.get("area_average_flux_limit_mol_m2_s")
        if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap < 0:
            raise ValueError("scale assessment must provide a finite nonnegative area-average species-flux limit")
        if not self.limited_reaction_ids or len(set(self.limited_reaction_ids)) != len(self.limited_reaction_ids):
            raise ValueError("limited reaction IDs must be nonempty and unique")
        return self

    @property
    def flux_limit_mol_m2_s(self) -> float:
        return float(self.scale_transport_result.values["area_average_flux_limit_mol_m2_s"])


def limit_species_production_branches(
    binding: ScaleLimitedSurfaceFlux,
    reactions,
    reaction_results: dict[str, dict],
) -> tuple[dict[str, dict], dict]:
    """Apply one species-production cap and return its diagnostic record."""
    adjusted, diagnostics = limit_species_production_branch_sets((binding,), reactions, reaction_results)
    return adjusted, diagnostics[0]


def limit_species_production_branch_sets(
    bindings: tuple[ScaleLimitedSurfaceFlux, ...],
    reactions,
    reaction_results: dict[str, dict],
) -> tuple[dict[str, dict], list[dict]]:
    """Apply species caps simultaneously, independent of binding order.

    Each species bound first yields a common factor from the original partial
    currents. If one electrochemical branch produces multiple bounded species,
    that branch receives the minimum applicable factor once. This satisfies
    every upper bound without repeatedly scaling already-adjusted currents.
    """
    faraday = 96485.33212
    by_id = {row.reaction_id: row for row in reactions}
    factors = []
    gross_fluxes = []
    selected_sets = []
    anodic_factors: dict[str, list[float]] = {}
    cathodic_factors: dict[str, list[float]] = {}
    for binding in bindings:
        selected = set(binding.limited_reaction_ids)
        if not selected <= set(by_id) or not selected <= set(reaction_results):
            raise ValueError("scale-limited reaction set does not match the selected electrode boundary")
        if any(
            by_id[reaction_id].stoichiometric_species_coefficients.get(binding.transported_species_id, 0.0) == 0
            for reaction_id in selected
        ):
            raise ValueError("every limited reaction must produce the selected species in one reaction direction")
        gross_flux = math.fsum(
            abs(by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id])
            * reaction_results[reaction_id][
                "gross_anodic_current_density_A_m2"
                if by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id] > 0
                else "gross_cathodic_current_density_A_m2"
            ]
            / (by_id[reaction_id].electron_count * faraday)
            for reaction_id in selected
        )
        cap = binding.flux_limit_mol_m2_s
        if not math.isfinite(gross_flux) or gross_flux < 0:
            raise ArithmeticError("gross transported-species production exceeds finite support")
        factor = 1.0 if gross_flux <= cap or gross_flux == 0 else cap / gross_flux
        factors.append(factor)
        gross_fluxes.append(gross_flux)
        selected_sets.append(selected)
        for reaction_id in selected:
            coefficient = by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id]
            branch_factors = anodic_factors if coefficient > 0 else cathodic_factors
            branch_factors.setdefault(reaction_id, []).append(factor)

    adjusted = dict(reaction_results)
    for reaction_id in set(anodic_factors) | set(cathodic_factors):
        reaction = by_id[reaction_id]
        original = reaction_results[reaction_id]
        anodic_factor = min(anodic_factors.get(reaction_id, (1.0,)))
        cathodic_factor = min(cathodic_factors.get(reaction_id, (1.0,)))
        anodic = original["gross_anodic_current_density_A_m2"] * anodic_factor
        cathodic = original["gross_cathodic_current_density_A_m2"] * cathodic_factor
        current = anodic - cathodic
        extent_rate = current / (reaction.electron_count * faraday)
        species_flux = {
            species: coefficient * extent_rate
            for species, coefficient in reaction.stoichiometric_species_coefficients.items()
        }
        if not all(math.isfinite(value) for value in (anodic, cathodic, current, extent_rate, *species_flux.values())):
            raise ArithmeticError("limited electrochemical current or species flux exceeds finite support")
        adjusted[reaction_id] = original | {
            "gross_anodic_current_density_A_m2": anodic,
            "gross_cathodic_current_density_A_m2": cathodic,
            "signed_current_density_A_m2": current,
            "signed_reaction_extent_mol_m2_s": extent_rate,
            "inward_species_flux_mol_m2_s": species_flux,
            "scale_limiter_productive_branch_factor": min(anodic_factor, cathodic_factor),
        }
    diagnostics = []
    for binding, selected, factor, gross_flux in zip(bindings, selected_sets, factors, gross_fluxes, strict=True):
        limited_flux = math.fsum(
            abs(by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id])
            * adjusted[reaction_id][
                "gross_anodic_current_density_A_m2"
                if by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id] > 0
                else "gross_cathodic_current_density_A_m2"
            ] / (by_id[reaction_id].electron_count * faraday)
            for reaction_id in selected
        )
        branch_scale_factors = [
            factor_value
            for reaction_id in selected
            for factor_value in (
                anodic_factors
                if by_id[reaction_id].stoichiometric_species_coefficients[binding.transported_species_id] > 0
                else cathodic_factors
            )[reaction_id]
        ]
        diagnostics.append({
            "scale_transport_result_sha256": binding.scale_transport_result_sha256,
            "scale_phase_id": binding.scale_phase_id,
            "scale_state_id": binding.scale_state_id,
            "transported_species_id": binding.transported_species_id,
            "surface_area_basis_id": binding.surface_area_basis_id,
            "application_location": binding.application_location,
            "caller_area_average_flux_limit_mol_m2_s": binding.flux_limit_mol_m2_s,
            "unlimited_gross_species_production_mol_m2_s": gross_flux,
            "limited_gross_species_production_mol_m2_s": limited_flux,
            "productive_partial_current_scaling_factor": min(branch_scale_factors, default=factor),
            "limiter_factor_before_shared_branch_constraints": factor,
            "limited_reaction_ids": list(binding.limited_reaction_ids),
            "limiter_basis": "simultaneous_species_caps_with_minimum_factor_on_shared_productive_branches",
        })
        if not math.isfinite(limited_flux) or limited_flux > binding.flux_limit_mol_m2_s * (1.0 + 1e-10) + 1e-15:
            raise ArithmeticError("limited species production does not satisfy the caller flux bound")
    return adjusted, diagnostics
