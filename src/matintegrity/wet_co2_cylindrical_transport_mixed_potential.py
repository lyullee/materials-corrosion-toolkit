"""Radial cylindrical finite-volume diffusion coupled to caller Butler-Volmer kinetics."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .electrode_kinetics import ButlerVolmerReaction, electrode_reaction_flux
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalScaleGeometryHistory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)

MODEL_ID = "integration.wet_co2_cylindrical_transport_mixed_potential"
SOURCE_ID = "independent_cylindrical_radial_finite_volume_species_balance"
KINETICS_SOURCE_ID = "caller_calibrated_butler_volmer_reaction_set"
GEOMETRY_SOURCE_ID = "degradation.wet_co2_cylindrical_scale_geometry_history"
FARADAY_C_MOL = 96485.33212


class WetCo2CylindricalSpeciesBoundary(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    bulk_concentration_mol_m3: Nonnegative
    radial_cell_diffusivity_m2_s: tuple[Positive, ...] = Field(min_length=1, max_length=200)


class WetCo2CylindricalElectrodeKnot(Contract):
    time_s: Nonnegative
    solution_film_thickness_m: Positive
    species: tuple[WetCo2CylindricalSpeciesBoundary, ...] = Field(min_length=1, max_length=32)
    reactions: tuple[ButlerVolmerReaction, ...] = Field(min_length=2, max_length=64)
    kinetics_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def knot_records_are_aligned(self):
        species_ids = [row.species_id for row in self.species]
        reactions = {row.reaction_id: row for row in self.reactions}
        if len(species_ids) != len(set(species_ids)):
            raise ValueError("one radial transport profile is required per unique species")
        if len(reactions) != len(self.reactions):
            raise ValueError("Butler-Volmer reaction IDs must be unique at each knot")
        if len({row.temperature_K for row in self.reactions}) != 1:
            raise ValueError("all reactions at a geometry knot must share one exact temperature")
        evidence_bindings = {(row.sha256, row.source_id) for row in self.kinetics_evidence if row.license_id}
        for reaction in self.reactions:
            if (reaction.calibration_sha256 not in {digest for digest, _source in evidence_bindings}
                    or not reaction.calibration_and_reaction_direction_reviewed):
                raise ValueError("each reviewed reaction calibration must be digest-pinned by licensed Evidence")
            if not set(reaction.stoichiometric_species_coefficients) <= set(species_ids):
                raise ValueError("all electrode reaction species must have a radial transport profile")
        if not any(coefficient != 0.0 for reaction in self.reactions
                   for coefficient in reaction.stoichiometric_species_coefficients.values()):
            raise ValueError("at least one reaction must exchange a transported species")
        return self


class WetCo2CylindricalTransportMixedPotential(Contract):
    """Independent steady radial species balances at exact annular-geometry knots."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_transport_mixed_potential.v1"] = (
        "matintegrity.wet_co2_cylindrical_transport_mixed_potential.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: tuple[WetCo2CylindricalElectrodeKnot, ...] = Field(min_length=1, max_length=5000)
    potential_absolute_tolerance_V: Positive = 1e-10
    maximum_bisection_iterations: int = Field(default=200, ge=1, le=500)
    boundary_chemistry_and_reference_reviewed: bool
    radial_domain_mesh_and_film_reviewed: bool
    current_reaction_and_surface_area_basis_reviewed: bool

    @model_validator(mode="after")
    def geometry_and_clock_are_pinned(self):
        if canonical_digest(self.geometry.model_dump(mode="json")) != self.geometry_sha256:
            raise ValueError("cylindrical geometry digest differs from the nested geometry contract")
        expected_times = tuple(row.time_s for row in self.geometry.history)
        actual_times = tuple(row.time_s for row in self.knots)
        if actual_times != expected_times:
            raise ValueError("electrochemical boundary knots must exactly match geometry history times")
        total_work = sum(len(profile.radial_cell_diffusivity_m2_s)
                         for knot in self.knots for profile in knot.species)
        if total_work > 2_000_000:
            raise ValueError("radial species-cell work exceeds the finite request budget")
        return self


def _radial_transport_factor(inner_radius_m: float, film_thickness_m: float,
                              diffusivity: tuple[float, ...]) -> tuple[float, list[float], list[float]]:
    """Return inner-area conductance and radial face positions/resistance fractions."""
    outer_radius = inner_radius_m + film_thickness_m
    if not math.isfinite(outer_radius) or outer_radius <= inner_radius_m:
        raise ArithmeticError("cylindrical solution film is outside finite radial support")
    count = len(diffusivity)
    log_width = math.log(outer_radius / inner_radius_m) / count
    faces = [inner_radius_m * math.exp(index * log_width) for index in range(count + 1)]
    increments = [math.log(faces[index + 1] / faces[index]) / diffusivity[index]
                  for index in range(count)]
    resistance = math.fsum(increments)
    factor = 1.0 / (inner_radius_m * resistance)
    if not math.isfinite(factor) or factor <= 0.0:
        raise ArithmeticError("cylindrical radial conductance is outside finite support")
    return factor, faces, increments


def _solve_knot(knot: WetCo2CylindricalElectrodeKnot, geometry_state: dict,
                tolerance: float, max_iterations: int) -> dict:
    """Solve one steady radial species balance and zero-current electrode closure."""
    inner_radius = float(geometry_state["bore_radius_m"])
    species = {row.species_id: row for row in knot.species}
    transport = {
        key: _radial_transport_factor(inner_radius, knot.solution_film_thickness_m,
                                      row.radial_cell_diffusivity_m2_s)
        for key, row in species.items()
    }
    capacities = {
        key: transport[key][0] * row.bulk_concentration_mol_m3
        for key, row in species.items()
    }
    if any(not math.isfinite(value) or value < 0.0 for value in capacities.values()):
        raise ArithmeticError("radial species transport capacity is outside finite nonnegative support")
    reactions = knot.reactions
    low = max(row.equilibrium_potential_V + row.minimum_overpotential_V for row in reactions)
    high = min(row.equilibrium_potential_V + row.maximum_overpotential_V for row in reactions)
    if low >= high:
        raise ValueError("no common calibrated mixed-potential interval at geometry knot")

    def at_potential(potential: float):
        raw = {reaction.reaction_id: electrode_reaction_flux(reaction, potential) for reaction in reactions}
        if any(row.get("status") != "computed" for row in raw.values()):
            raise ValueError("Butler-Volmer reaction left its reviewed calibration support")
        factors = {reaction.reaction_id: {"anodic": 1.0, "cathodic": 1.0} for reaction in reactions}
        species_demand = {}
        for species_id, capacity in capacities.items():
            demand_by_branch = {}
            for reaction in reactions:
                coefficient = reaction.stoichiometric_species_coefficients.get(species_id, 0.0)
                if coefficient == 0.0:
                    continue
                branch = "anodic" if coefficient < 0.0 else "cathodic"
                current_key = "gross_anodic_current_density_A_m2" if coefficient < 0.0 else "gross_cathodic_current_density_A_m2"
                demand_by_branch[(reaction.reaction_id, branch)] = (
                    abs(coefficient) * raw[reaction.reaction_id][current_key]
                    / (reaction.electron_count * FARADAY_C_MOL)
                )
            demand = math.fsum(demand_by_branch.values())
            factor = 1.0 if demand == 0.0 or demand <= capacity else capacity / demand
            for reaction_id, branch in demand_by_branch:
                factors[reaction_id][branch] = min(factors[reaction_id][branch], factor)
            species_demand[species_id] = {
                "gross_consumption_mol_m2_s": demand,
                "radial_capacity_mol_m2_s": capacity,
                "branch_factor": factor,
            }
        adjusted = {}
        for reaction in reactions:
            row = raw[reaction.reaction_id]
            anodic = row["gross_anodic_current_density_A_m2"] * factors[reaction.reaction_id]["anodic"]
            cathodic = row["gross_cathodic_current_density_A_m2"] * factors[reaction.reaction_id]["cathodic"]
            current = anodic - cathodic
            extent = current / (reaction.electron_count * FARADAY_C_MOL)
            adjusted[reaction.reaction_id] = {
                "anodic_current_density_A_m2": anodic,
                "cathodic_current_density_A_m2": cathodic,
                "signed_current_density_A_m2": current,
                "signed_extent_mol_m2_s": extent,
                "branch_factors": factors[reaction.reaction_id],
                "species_flux_mol_m2_s": {
                    name: coefficient * extent
                    for name, coefficient in reaction.stoichiometric_species_coefficients.items()
                },
            }
        return (math.fsum(row["signed_current_density_A_m2"] for row in adjusted.values()),
                adjusted, species_demand)

    low_result = at_potential(low)
    high_result = at_potential(high)
    if low_result[0] > 0.0 or high_result[0] < 0.0:
        raise ValueError("zero-current potential is not bracketed by caller kinetic support")
    if low_result[0] == 0.0:
        potential, solved = low, low_result
    elif high_result[0] == 0.0:
        potential, solved = high, high_result
    else:
        left, right = low, high
        solved = low_result
        for _iteration in range(max_iterations):
            potential = left + (right - left) / 2.0
            solved = at_potential(potential)
            if abs(solved[0]) <= 1e-12 or right - left <= tolerance:
                break
            if solved[0] < 0.0:
                left = potential
            else:
                right = potential
        else:
            raise ArithmeticError("mixed-potential bisection reached its iteration limit")
    net_current, reaction_results, demand_rows = solved
    aggregate_consumption = {key: 0.0 for key in species}
    for reaction in reactions:
        extent = reaction_results[reaction.reaction_id]["signed_extent_mol_m2_s"]
        for species_id, coefficient in reaction.stoichiometric_species_coefficients.items():
            aggregate_consumption[species_id] -= coefficient * extent
    species_output = {}
    for species_id, profile in species.items():
        factor, faces, increments = transport[species_id]
        consumption = aggregate_consumption[species_id]
        cumulative = math.fsum(increments)
        face_concentrations = []
        for index in range(len(faces)):
            concentration = profile.bulk_concentration_mol_m3 - consumption * inner_radius * cumulative
            if not math.isfinite(concentration) or concentration < -1e-10:
                raise ArithmeticError("radial finite-volume concentration left nonnegative support")
            face_concentrations.append(max(0.0, concentration))
            if index < len(increments):
                cumulative -= increments[index]
        species_output[species_id] = {
            "bulk_concentration_mol_m3": profile.bulk_concentration_mol_m3,
            "diffusivity_m2_s_by_radial_cell": list(profile.radial_cell_diffusivity_m2_s),
            "radial_face_radius_m_inner_to_outer": faces,
            "radial_face_concentration_mol_m3_inner_to_outer": face_concentrations,
            "net_wall_consumption_mol_m2_s": consumption,
            "transport_capacity_mol_m2_s": capacities[species_id],
            "bulk_side_flux_mol_m2_s": consumption * inner_radius / faces[-1],
            "finite_volume_wall_flux_residual_mol_m2_s": (
                factor * (profile.bulk_concentration_mol_m3 - face_concentrations[0]) - consumption
            ),
            "gross_consumption_limiter": demand_rows.get(species_id),
            "radial_cell_resistance_ln_radius_over_diffusivity_s_m2": increments,
        }
    return {
        "time_s": knot.time_s,
        "bore_radius_m": inner_radius,
        "scale_thickness_equivalent_m": geometry_state["scale_thickness_equivalent_m"],
        "wall_remaining_m": geometry_state["wall_remaining_m"],
        "solution_film_thickness_m": knot.solution_film_thickness_m,
        "temperature_K": reactions[0].temperature_K,
        "mixed_potential_V": potential,
        "net_current_residual_A_m2": net_current,
        "reaction_results": reaction_results,
        "species_transport": species_output,
        "kinetics_calibration_sha256_by_reaction": {
            row.reaction_id: row.calibration_sha256 for row in reactions
        },
    }


def evaluate_wet_co2_cylindrical_transport_mixed_potential(
    request: WetCo2CylindricalTransportMixedPotential,
) -> Calculation:
    """Solve exact-knot radial balances and a branch-limited zero-current potential."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "geometry_request_sha256": request.geometry_sha256,
        "geometry_result_sha256": None,
        "interpolation_performed": False,
        "time_integration_performed": False,
        "chemistry_inferred": False,
    }
    missing = [key for key in (
        "boundary_chemistry_and_reference_reviewed",
        "radial_domain_mesh_and_film_reviewed",
        "current_reaction_and_surface_area_basis_reviewed",
    ) if not getattr(request, key)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "reviewed_boundary_radial_mesh_and_current_basis_required",
            "missing_reviews": missing,
        })
    geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(request.geometry)
    if geometry.status != "computed":
        return Calculation(status=geometry.status, values=base | {
            "reason": "nested_cylindrical_geometry_not_computed",
            "geometry_status": geometry.status,
            "geometry_values": geometry.values,
        })
    geometry_states = geometry.values["history"]
    geometry_result_digest = canonical_digest(geometry.model_dump(mode="json"))
    knots = []
    for index, (knot, state) in enumerate(zip(request.knots, geometry_states, strict=True)):
        try:
            knots.append(_solve_knot(knot, state, request.potential_absolute_tolerance_V,
                                     request.maximum_bisection_iterations))
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "geometry_result_sha256": geometry_result_digest,
                "reason": "cylindrical_transport_or_electrode_solve_outside_reviewed_support",
                "completed_knot_count": len(knots),
                "failed_knot_index": index,
                "failed_time_s": knot.time_s,
                "failure_detail": str(exc),
                "history_prefix": knots,
            })
    return Calculation(values=base | {
        "status": "computed",
        "geometry_history": geometry_states,
        "geometry_result_sha256": geometry_result_digest,
        "knot_count": len(knots),
        "history": knots,
        "limitations": [
            "Each exact geometry knot is solved as an independent steady radial species balance; temporal species storage and homogeneous chemistry are not integrated.",
            "The radial finite-volume resistance uses caller diffusivity in each logarithmic annular cell and caller bulk concentration at the film outer radius.",
            "Gross consuming Butler-Volmer branches are uniformly scaled within each species transport limit before solving zero net current.",
            "No aqueous speciation, precipitation, scale-growth feedback, hydrodynamics, or experimental qualification is included.",
        ],
    }, notes=(
        "The bore radius at each knot comes from the exact cylindrical geometry adapter and controls the radial finite-volume mesh.",
        "The branch limiter is a bounded steady closure, not a simultaneous transient diffusion-reaction PDE or a calibrated surface-chemistry mechanism.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalTransportMixedPotential,
        evaluator=evaluate_wet_co2_cylindrical_transport_mixed_potential,
        units={
            "history[].time_s": "s",
            "history[].bore_radius_m": "m",
            "history[].scale_thickness_equivalent_m": "m",
            "history[].wall_remaining_m": "m",
            "history[].solution_film_thickness_m": "m",
            "history[].mixed_potential_V": "V",
            "history[].net_current_residual_A_m2": "A/m^2",
            "history[].species_transport.*.net_wall_consumption_mol_m2_s": "mol/m^2/s",
            "history[].species_transport.*.transport_capacity_mol_m2_s": "mol/m^2/s",
            "history[].species_transport.*.radial_face_radius_m_inner_to_outer[]": "m",
            "history[].species_transport.*.radial_face_concentration_mol_m3_inner_to_outer[]": "mol/m^3",
        },
        assumptions=(
            "Geometry and electrochemical boundary are paired at exactly equal caller time knots; no interpolation is performed.",
            "Steady radial cylindrical Fick transport uses the declared annular cell resistances.",
            "Caller-calibrated Butler-Volmer branches share a species-specific transport-capacity limiter before zero-current solution.",
            "This bounded layer does not perform transient species storage, automatic aqueous chemistry, or scale-growth feedback.",
        ),
        source_ids=(SOURCE_ID, KINETICS_SOURCE_ID, GEOMETRY_SOURCE_ID),
        qualification="user_model",
    )]
