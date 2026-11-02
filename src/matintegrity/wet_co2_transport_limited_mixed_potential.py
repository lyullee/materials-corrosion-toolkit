"""Caller-parameterized film-transport-limited wet-CO2 mixed potential."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .carbonate_transport_adapter import CarbonateTransportBoundary
from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .electrode_kinetics import ButlerVolmerReaction, electrode_reaction_flux
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_film_transport_limited_mixed_potential"
SOURCE_ID = "caller_wet_co2_species_film_transport_parameters"
BV_SOURCE_ID = "caller_calibrated_butler_volmer_reaction_set"
FARADAY_C_MOL = 96485.33212
GAS_CONSTANT_J_MOL_K = 8.31446261815324


class WetCo2ReactantFilmRecord(Contract):
    """Caller-supplied linear liquid-film conductance for one consumed species."""

    species_id: str = Field(min_length=1)
    diffusivity_m2_s: Positive
    film_thickness_m: Positive
    minimum_surface_concentration_mol_m3: Nonnegative = 0.0
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence: Evidence
    transfer_parameter_reviewed: bool

    @model_validator(mode="after")
    def source_matches(self):
        if self.provider_id != self.evidence.source_id:
            raise ValueError("film-parameter provider must match Evidence source_id")
        return self

    @property
    def flux_capacity_mol_m2_s(self) -> float:
        return self.diffusivity_m2_s / self.film_thickness_m


class WetCo2TransportLimitedMixedPotentialRequest(Contract):
    boundary: CarbonateTransportBoundary
    boundary_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reactions: tuple[ButlerVolmerReaction, ...] = Field(min_length=2, max_length=64)
    reactant_films: tuple[WetCo2ReactantFilmRecord, ...] = Field(min_length=1, max_length=16)
    potential_absolute_tolerance_V: Positive = 1e-10
    maximum_bisection_iterations: int = Field(default=200, ge=1, le=500)
    boundary_scope_match_reviewed: bool
    species_direction_and_reaction_mapping_reviewed: bool
    planar_steady_film_approximation_reviewed: bool
    common_temperature_and_solution_reference_reviewed: bool

    @model_validator(mode="after")
    def validate_bindings(self):
        boundary = self.boundary
        if canonical_digest(boundary.model_dump(mode="json")) != self.boundary_sha256:
            raise ValueError("boundary digest differs from pinned boundary")
        if len(boundary.species_ids) != len(boundary.concentration_mol_m3) or len(set(boundary.species_ids)) != len(boundary.species_ids):
            raise ValueError("boundary species and concentration vectors must have equal length and unique species IDs")
        if len({reaction.reaction_id for reaction in self.reactions}) != len(self.reactions):
            raise ValueError("reaction IDs must be unique")
        if len({film.species_id for film in self.reactant_films}) != len(self.reactant_films):
            raise ValueError("one film record per species is required")
        concentrations = dict(zip(boundary.species_ids, boundary.concentration_mol_m3, strict=True))
        if any(film.species_id not in concentrations for film in self.reactant_films):
            raise ValueError("film-limited species must appear in the pinned carbonate boundary")
        if any(film.minimum_surface_concentration_mol_m3 > concentrations[film.species_id] for film in self.reactant_films):
            raise ValueError("minimum surface concentration cannot exceed the boundary concentration")
        for reaction in self.reactions:
            if reaction.temperature_K != boundary.temperature_K:
                raise ValueError("every reaction temperature must exactly equal the boundary temperature")
            if any(species not in boundary.species_ids for species in reaction.stoichiometric_species_coefficients):
                raise ValueError("reaction species must be present in the explicit carbonate boundary")
            if not reaction.calibration_and_reaction_direction_reviewed:
                raise ValueError("all selected Butler-Volmer reactions require reviewed calibration and direction")
        for film in self.reactant_films:
            if not any(reaction.stoichiometric_species_coefficients.get(film.species_id, 0.0) != 0.0 for reaction in self.reactions):
                raise ValueError("each film-limited species must occur in the selected reaction stoichiometry")
        if any(not row.transfer_parameter_reviewed for row in self.reactant_films):
            raise ValueError("all film coefficients require explicit caller review")
        return self


def evaluate_wet_co2_transport_limited_mixed_potential(
    request: WetCo2TransportLimitedMixedPotentialRequest,
) -> Calculation:
    """Solve a branch-scaled zero-current potential with Fick-film reactant caps.

    Each film cap is D/delta*(C_bulk-C_surface,min). At a trial potential,
    consumption on each forward/reverse partial-current branch is calculated
    from signed reaction stoichiometry. A species with multiple consumers
    shares a single cap proportionally by uniformly scaling all consuming
    branches; if a reaction consumes multiple bounded species it receives the
    smallest applicable branch factor. The resulting net current is root-solved.
    """
    boundary = request.boundary
    concentrations = dict(zip(boundary.species_ids, boundary.concentration_mol_m3, strict=True))
    films = {item.species_id: item for item in request.reactant_films}
    capacities = {
        species: record.diffusivity_m2_s / record.film_thickness_m
        * (concentrations[species] - record.minimum_surface_concentration_mol_m3)
        for species, record in films.items()
    }
    if any(not math.isfinite(value) or value < 0.0 for value in capacities.values()):
        return Calculation(status="out_of_scope", values={"model_id": MODEL_ID, "reason": "film_capacity_outside_finite_support"})

    low = max(row.equilibrium_potential_V + row.minimum_overpotential_V for row in request.reactions)
    high = min(row.equilibrium_potential_V + row.maximum_overpotential_V for row in request.reactions)
    base = {
        "model_id": MODEL_ID,
        "boundary_id": boundary.boundary_id,
        "boundary_sha256": request.boundary_sha256,
        "boundary_selection_sha256": boundary.selection_sha256,
        "carbonate_history_result_sha256": boundary.equilibrium_result_sha256,
        "temperature_K": boundary.temperature_K,
        "solvent_composition_sha256": boundary.solvent_composition_sha256,
        "species_ids": list(boundary.species_ids),
        "reactant_film_capacity_mol_m2_s": capacities,
        "interpolation_performed": False,
        "full_aqueous_composition_inferred": False,
    }
    if not request.boundary_scope_match_reviewed or not request.species_direction_and_reaction_mapping_reviewed or not request.planar_steady_film_approximation_reviewed or not request.common_temperature_and_solution_reference_reviewed:
        return Calculation(status="needs_data", values=base | {"reason": "required_scope_or_model_assumptions_not_reviewed"})
    if low >= high:
        return Calculation(status="out_of_scope", values=base | {"reason": "no_common_calibrated_potential_interval"})

    def at_potential(potential: float):
        raw = {row.reaction_id: electrode_reaction_flux(row, potential) for row in request.reactions}
        if any(row["status"] != "computed" for row in raw.values()):
            raise ArithmeticError("reaction left its calibration interval or numeric support")
        factors = {row.reaction_id: {"anodic": 1.0, "cathodic": 1.0} for row in request.reactions}
        species_ledger = {}
        for species, capacity in capacities.items():
            demand_by_branch: dict[tuple[str, str], float] = {}
            for reaction in request.reactions:
                coefficient = reaction.stoichiometric_species_coefficients.get(species, 0.0)
                if coefficient < 0.0:
                    branch, current_key = "anodic", "gross_anodic_current_density_A_m2"
                elif coefficient > 0.0:
                    branch, current_key = "cathodic", "gross_cathodic_current_density_A_m2"
                else:
                    continue
                demand_by_branch[(reaction.reaction_id, branch)] = abs(coefficient) * raw[reaction.reaction_id][current_key] / (reaction.electron_count * FARADAY_C_MOL)
            demand = math.fsum(demand_by_branch.values())
            shared_factor = 1.0 if demand <= capacity or demand == 0.0 else capacity / demand
            for reaction_id, branch in demand_by_branch:
                factors[reaction_id][branch] = min(factors[reaction_id][branch], shared_factor)
            species_ledger[species] = {"gross_consumption_mol_m2_s": demand, "film_capacity_mol_m2_s": capacity, "branch_factor": shared_factor}
        adjusted = {}
        for reaction in request.reactions:
            row = raw[reaction.reaction_id]
            anodic = row["gross_anodic_current_density_A_m2"] * factors[reaction.reaction_id]["anodic"]
            cathodic = row["gross_cathodic_current_density_A_m2"] * factors[reaction.reaction_id]["cathodic"]
            net = anodic - cathodic
            extent = net / (reaction.electron_count * FARADAY_C_MOL)
            adjusted[reaction.reaction_id] = {
                "anodic_current_density_A_m2": anodic,
                "cathodic_current_density_A_m2": cathodic,
                "signed_current_density_A_m2": net,
                "signed_extent_mol_m2_s": extent,
                "branch_factors": factors[reaction.reaction_id],
                "species_flux_mol_m2_s": {key: coeff * extent for key, coeff in reaction.stoichiometric_species_coefficients.items()},
            }
        return math.fsum(item["signed_current_density_A_m2"] for item in adjusted.values()), adjusted, species_ledger

    try:
        left = at_potential(low)
        right = at_potential(high)
        if left[0] > 0.0 or right[0] < 0.0:
            return Calculation(status="out_of_scope", values=base | {"reason": "transport_limited_zero_current_not_bracketed", "endpoint_net_current_A_m2": [left[0], right[0]]})
        if left[0] == 0.0:
            potential, solved = low, left
        elif right[0] == 0.0:
            potential, solved = high, right
        else:
            lo, hi = low, high
            solved = left
            potential = lo
            for iteration in range(request.maximum_bisection_iterations):
                potential = lo + (hi - lo) / 2.0
                solved = at_potential(potential)
                if abs(solved[0]) <= 1e-12 or hi - lo <= request.potential_absolute_tolerance_V:
                    break
                if solved[0] < 0.0:
                    lo = potential
                else:
                    hi = potential
            else:
                return Calculation(status="out_of_scope", values=base | {"reason": "potential_bisection_iteration_limit", "iterations": request.maximum_bisection_iterations})
    except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
        return Calculation(status="out_of_scope", values=base | {"reason": "reaction_or_film_evaluation_failed", "detail": str(exc)})
    net_current, reaction_rows, species_rows = solved
    return Calculation(values=base | {
        "status": "computed",
        "mixed_potential_V": potential,
        "net_current_residual_A_m2": net_current,
        "reaction_results": reaction_rows,
        "consumed_species_transport": species_rows,
        "film_parameter_digests": {item.species_id: canonical_digest(item.model_dump(mode="json")) for item in request.reactant_films},
        "kinetics_provider_digests": {item.reaction_id: item.calibration_sha256 for item in request.reactions},
    }, notes=(
        "Linear steady planar film law uses caller-supplied diffusivity, thickness and minimum surface concentration.",
        "Partial-current branch scaling is a limiting-rate closure, not a simultaneous diffusion-reaction PDE solution.",
        "Only explicitly bounded carbonate-boundary species are represented; counterions, full speciation, pH feedback, precipitation and moving scale are not inferred.",
        "No kinetic parameters, diffusivities, film thicknesses or experimental records are embedded.",
    ))


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            WetCo2TransportLimitedMixedPotentialRequest,
            evaluate_wet_co2_transport_limited_mixed_potential,
            {
                "mixed_potential_V": "V",
                "net_current_residual_A_m2": "A/m^2",
                "reaction_results[].signed_extent_mol_m2_s": "mol/m^2/s",
                "consumed_species_transport[].film_capacity_mol_m2_s": "mol/m^2/s",
            },
            (
                "A digest-pinned caller carbonate boundary and caller-reviewed reactant film records define the finite dissolved-species support.",
                "Caller-calibrated Butler-Volmer reactions must match the exact boundary temperature and use only explicitly listed carbonate species.",
                "Transport limitation scales consuming partial-current branches against a steady planar Fick-film cap and solves the bounded zero-current potential by bisection.",
                "No full speciation, pH feedback, precipitation, moving scale, simultaneous diffusion-reaction PDE, or corrosion qualification is inferred.",
            ),
            (SOURCE_ID, BV_SOURCE_ID),
            qualification="user_model",
        )
    ]
