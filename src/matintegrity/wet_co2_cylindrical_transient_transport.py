"""Finite-inventory transient radial species transport on moving cylindrical film geometry."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalScaleGeometryHistory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)

MODEL_ID = "integration.wet_co2_cylindrical_transient_transport"
SOURCE_ID = "independent_moving_cylinder_finite_volume_inventory_balance"
KINETICS_SOURCE_ID = "caller_signed_cylindrical_wall_reaction_extent_schedule"
FARADAY_C_MOL = 96485.33212


class WetCo2TransientSpecies(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    charge_number: int = Field(ge=-8, le=8)
    elemental_composition: dict[str, Positive]

    @model_validator(mode="after")
    def formula_is_explicit(self):
        if not self.elemental_composition:
            raise ValueError("each transported species needs an explicit elemental formula")
        return self


class WetCo2WallElement(Contract):
    element_id: str = Field(min_length=1, max_length=32)
    atomic_molar_mass_kg_mol: Positive
    alloy_mass_fraction: Positive = Field(le=1.0)


class WetCo2TransientWallReaction(Contract):
    reaction_id: str = Field(min_length=1, max_length=160)
    electron_count: int = Field(gt=0, le=32)
    aqueous_species_stoichiometry: dict[str, float]
    metal_element_release_mol_per_extent: dict[str, Nonnegative] = Field(default_factory=dict)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence


class WetCo2TransientInitialSpecies(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    cell_concentrations_mol_m3: tuple[Nonnegative, ...] = Field(min_length=1, max_length=200)


class WetCo2TransientSpeciesBoundary(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    bulk_concentration_mol_m3: Nonnegative
    radial_cell_diffusivity_m2_s: tuple[Positive, ...] = Field(min_length=1, max_length=200)


class WetCo2ReactionExtentRate(Contract):
    reaction_id: str = Field(min_length=1, max_length=160)
    signed_extent_mol_m2_s: float

    @model_validator(mode="after")
    def finite_rate(self):
        if not math.isfinite(self.signed_extent_mol_m2_s):
            raise ValueError("reaction extent rate must be finite")
        return self


class WetCo2TransientTransportKnot(Contract):
    time_s: Nonnegative
    solution_film_thickness_m: Positive
    species_boundaries: tuple[WetCo2TransientSpeciesBoundary, ...] = Field(min_length=1, max_length=32)
    reaction_extent_rates: tuple[WetCo2ReactionExtentRate, ...] = Field(min_length=1, max_length=64)
    boundary_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def verify_boundary_record(self):
        payload = {
            "time_s": self.time_s,
            "solution_film_thickness_m": self.solution_film_thickness_m,
            "species_boundaries": [row.model_dump(mode="json") for row in self.species_boundaries],
            "reaction_extent_rates": [row.model_dump(mode="json") for row in self.reaction_extent_rates],
        }
        if canonical_digest(payload) != self.boundary_record_sha256:
            raise ValueError("boundary digest must bind the exact knot concentrations, transport and reaction rates")
        if not any(row.sha256 == self.boundary_record_sha256 and row.license_id for row in self.boundary_evidence):
            raise ValueError("boundary Evidence must pin the digest and include a usage license")
        ids = [row.species_id for row in self.species_boundaries]
        reaction_ids = [row.reaction_id for row in self.reaction_extent_rates]
        if len(ids) != len(set(ids)) or len(reaction_ids) != len(set(reaction_ids)):
            raise ValueError("species and reaction rate IDs must be unique at a knot")
        return self


class WetCo2CylindricalTransientTransport(Contract):
    """Transient multicomponent radial FV inventory model using exact geometry knots."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_transient_transport.v1"] = (
        "matintegrity.wet_co2_cylindrical_transient_transport.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species: tuple[WetCo2TransientSpecies, ...] = Field(min_length=1, max_length=32)
    initial_species: tuple[WetCo2TransientInitialSpecies, ...] = Field(min_length=1, max_length=32)
    initial_state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_evidence: Evidence
    wall_elements: tuple[WetCo2WallElement, ...] = Field(min_length=1, max_length=16)
    wall_density_kg_m3: Positive
    wall_material_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_material_evidence: Evidence
    reactions: tuple[WetCo2TransientWallReaction, ...] = Field(min_length=1, max_length=64)
    knots: tuple[WetCo2TransientTransportKnot, ...] = Field(min_length=2, max_length=2000)
    relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    concentration_absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    inventory_absolute_tolerance_mol_m: Positive = Field(default=1e-12)
    charge_absolute_tolerance_C_m: Positive = Field(default=1e-7)
    inventory_relative_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_step_s: Positive
    axisymmetric_reaction_area_and_material_mapping_reviewed: bool
    boundary_and_transport_history_reviewed: bool
    element_charge_and_reaction_direction_reviewed: bool

    @model_validator(mode="after")
    def verify_static_contract(self):
        if canonical_digest(self.geometry.model_dump(mode="json")) != self.geometry_sha256:
            raise ValueError("geometry digest differs from nested moving-cylinder geometry")
        if self.initial_state_evidence.sha256 != self.initial_state_sha256 or not self.initial_state_evidence.license_id:
            raise ValueError("initial-state Evidence must pin the declared concentration digest and usage license")
        if self.wall_material_evidence.sha256 != self.wall_material_record_sha256 or not self.wall_material_evidence.license_id:
            raise ValueError("wall-material Evidence must pin alloy density/composition and usage license")
        species_by_id = {row.species_id: row for row in self.species}
        element_ids = {row.element_id for row in self.wall_elements}
        if len(species_by_id) != len(self.species) or len(element_ids) != len(self.wall_elements):
            raise ValueError("species and wall-element identities must be unique")
        if not math.isclose(math.fsum(row.alloy_mass_fraction for row in self.wall_elements), 1.0,
                            rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("caller alloy element mass fractions must sum to one")
        wall_material_payload = {
            "density_kg_m3": self.wall_density_kg_m3,
            "elements": [row.model_dump(mode="json") for row in self.wall_elements],
        }
        if canonical_digest(wall_material_payload) != self.wall_material_record_sha256:
            raise ValueError("wall material digest must bind alloy density, mass fractions and atomic masses")
        if set(species_by_id) != {row.species_id for row in self.initial_species}:
            raise ValueError("initial state must contain exactly one record for every species")
        initial_payload = [row.model_dump(mode="json") for row in self.initial_species]
        if canonical_digest(initial_payload) != self.initial_state_sha256:
            raise ValueError("initial state digest differs from ordered species concentration arrays")
        cell_counts = {len(row.cell_concentrations_mol_m3) for row in self.initial_species}
        if len(cell_counts) != 1:
            raise ValueError("all initial species profiles must share one radial cell count")
        cell_count = next(iter(cell_counts))
        if any(len(row.radial_cell_diffusivity_m2_s) != cell_count
               for knot in self.knots for row in knot.species_boundaries):
            raise ValueError("every knot species diffusivity vector must align with initial radial cell count")
        if sum(len(row.radial_cell_diffusivity_m2_s)
               for knot in self.knots for row in knot.species_boundaries) > 2_000_000:
            raise ValueError("transient species-cell-knot work exceeds the finite request budget")
        if set(self.geometry.history[i].time_s for i in range(len(self.geometry.history))) != set(k.time_s for k in self.knots):
            raise ValueError("transport and geometry histories must use exactly matching time knots")
        if tuple(row.time_s for row in self.geometry.history) != tuple(row.time_s for row in self.knots):
            raise ValueError("transport knots must preserve geometry knot order")
        species_ids = set(species_by_id)
        reaction_by_id = {row.reaction_id: row for row in self.reactions}
        if len(reaction_by_id) != len(self.reactions):
            raise ValueError("reaction IDs must be unique")
        charges = {key: value.charge_number for key, value in species_by_id.items()}
        formulas = {key: value.elemental_composition for key, value in species_by_id.items()}
        for reaction in self.reactions:
            if not reaction.evidence.license_id or reaction.evidence.sha256 != reaction.calibration_sha256:
                raise ValueError("reaction Evidence must pin its caller calibration digest and usage license")
            if not set(reaction.aqueous_species_stoichiometry) <= species_ids:
                raise ValueError("reaction stoichiometry references an undeclared transported species")
            if not set(reaction.metal_element_release_mol_per_extent) <= element_ids:
                raise ValueError("reaction metal release refers to an element absent from the wall alloy")
            charge_delta = math.fsum(charges[key] * coeff
                                     for key, coeff in reaction.aqueous_species_stoichiometry.items())
            if not math.isclose(charge_delta, float(reaction.electron_count), rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("aqueous reaction charge delta must equal caller electron count in anodic direction")
            elements = set(element_ids) | {
                element for key in reaction.aqueous_species_stoichiometry for element in formulas[key]
            }
            for element in elements:
                aqueous_delta = math.fsum(
                    coefficient * formulas[species_id].get(element, 0.0)
                    for species_id, coefficient in reaction.aqueous_species_stoichiometry.items()
                )
                solid_release = reaction.metal_element_release_mol_per_extent.get(element, 0.0)
                if not math.isclose(aqueous_delta, solid_release, rel_tol=1e-10, abs_tol=1e-10):
                    raise ValueError(f"reaction elemental balance does not match wall transfer for {element}")
        expected_species = set(species_by_id)
        expected_reactions = set(reaction_by_id)
        if self.knots[0].time_s != 0.0:
            raise ValueError("transient wet-CO2 history must begin at time zero")
        for index, knot in enumerate(self.knots):
            if set(row.species_id for row in knot.species_boundaries) != expected_species:
                raise ValueError("every knot must provide exactly one boundary profile for each species")
            if set(row.reaction_id for row in knot.reaction_extent_rates) != expected_reactions:
                raise ValueError("every knot must provide exactly one extent rate for each wall reaction")
            if index and knot.time_s <= self.knots[index - 1].time_s:
                raise ValueError("transient transport knot times must strictly increase")
            rates = {row.reaction_id: row.signed_extent_mol_m2_s for row in knot.reaction_extent_rates}
            for reaction in self.reactions:
                if reaction.metal_element_release_mol_per_extent and rates[reaction.reaction_id] < 0.0:
                    raise ValueError("reverse deposition of wall metal is outside this monotone-recession model")
            if index == len(self.knots) - 1 and any(value != 0.0 for value in rates.values()):
                raise ValueError("terminal knot has no following interval; its reaction rates must be zero")
        return self


def _edges(inner: float, film: float, count: int) -> list[float]:
    outer = inner + film
    log_width = math.log(outer / inner) / count
    return [inner * math.exp(index * log_width) for index in range(count + 1)]


def _cell_volumes_per_axial_metre(edges: list[float]) -> list[float]:
    return [math.pi * (edges[index + 1] ** 2 - edges[index] ** 2) for index in range(len(edges) - 1)]


def _remap_species(old_edges: list[float], new_edges: list[float], old_concentration: list[float],
                   new_inner_concentration: float, new_bulk_concentration: float) -> tuple[list[float], dict[str, float]]:
    """Conservatively remap piecewise-constant concentration through radial overlap."""
    old_inner, old_outer = old_edges[0], old_edges[-1]
    new_inner, new_outer = new_edges[0], new_edges[-1]
    new_values = []
    added_inner = added_outer = 0.0
    removed_inner = removed_outer = 0.0
    for index, (low, high) in enumerate(zip(new_edges[:-1], new_edges[1:], strict=True)):
        amount = 0.0
        for old_index, (old_low, old_high) in enumerate(zip(old_edges[:-1], old_edges[1:], strict=True)):
            overlap_low, overlap_high = max(low, old_low), min(high, old_high)
            if overlap_high > overlap_low:
                amount += old_concentration[old_index] * math.pi * (overlap_high**2 - overlap_low**2)
        inner_low, inner_high = low, min(high, old_inner)
        if inner_high > inner_low:
            volume = math.pi * (inner_high**2 - inner_low**2)
            amount += new_inner_concentration * volume
            added_inner += new_inner_concentration * volume
        outer_low, outer_high = max(low, old_outer), high
        if outer_high > outer_low:
            volume = math.pi * (outer_high**2 - outer_low**2)
            amount += new_bulk_concentration * volume
            added_outer += new_bulk_concentration * volume
        volume_new = math.pi * (high**2 - low**2)
        if not math.isfinite(amount) or amount < 0.0 or volume_new <= 0.0:
            raise ArithmeticError("moving-grid remap produced invalid finite species inventory")
        new_values.append(amount / volume_new)
    for index, (low, high) in enumerate(zip(old_edges[:-1], old_edges[1:], strict=True)):
        inner_low, inner_high = low, min(high, new_inner)
        if inner_high > inner_low:
            removed_inner += old_concentration[index] * math.pi * (inner_high**2 - inner_low**2)
        outer_low, outer_high = max(low, new_outer), high
        if outer_high > outer_low:
            removed_outer += old_concentration[index] * math.pi * (outer_high**2 - outer_low**2)
    return new_values, {
        "swept_in_inner_mol_m": added_inner,
        "swept_in_outer_mol_m": added_outer,
        "swept_out_inner_mol_m": removed_inner,
        "swept_out_outer_mol_m": removed_outer,
    }


def _wall_element_inventory_per_axial_metre(geometry_state: dict,
                                             wall_elements: tuple[WetCo2WallElement, ...], density: float) -> dict[str, float]:
    steel_area = float(geometry_state["steel_cross_section_area_m2"])
    return {
        row.element_id: steel_area * density * row.alloy_mass_fraction / row.atomic_molar_mass_kg_mol
        for row in wall_elements
    }


def _allowed(residual: float, scale: float, absolute: float, relative: float) -> bool:
    return math.isfinite(residual) and abs(residual) <= absolute + relative * max(1e-30, abs(scale))


def evaluate_wet_co2_cylindrical_transient_transport(
    request: WetCo2CylindricalTransientTransport, *, scipy=None
) -> Calculation:
    """Integrate finite species inventories over left-held knot intervals and rezone conservatively."""
    if scipy is None:
        from scipy.integrate import solve_ivp
    else:
        solve_ivp = scipy.integrate.solve_ivp

    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "geometry_request_sha256": request.geometry_sha256,
        "geometry_result_sha256": None,
        "time_interpolation": "left_hold_between_exact_knots",
        "moving_grid_remap": "piecewise_constant_conservative_annular_overlap_with_explicit_boundary_fill",
    }
    reviews = {
        "axisymmetric_reaction_area_and_material_mapping_reviewed": request.axisymmetric_reaction_area_and_material_mapping_reviewed,
        "boundary_and_transport_history_reviewed": request.boundary_and_transport_history_reviewed,
        "element_charge_and_reaction_direction_reviewed": request.element_charge_and_reaction_direction_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"reason": "caller_review_gates_incomplete", "missing_reviews": missing})
    geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(request.geometry)
    if geometry.status != "computed":
        return Calculation(status=geometry.status, values=base | {
            "reason": "nested_cylindrical_geometry_not_computed",
            "geometry_status": geometry.status,
            "geometry_values": geometry.values,
        })
    geometry_states = geometry.values["history"]
    geometry_result_digest = canonical_digest(geometry.model_dump(mode="json"))
    base["geometry_result_sha256"] = geometry_result_digest
    species = tuple(request.species)
    species_ids = [row.species_id for row in species]
    species_index = {key: index for index, key in enumerate(species_ids)}
    elements = tuple(row.element_id for row in request.wall_elements)
    element_index = {key: index for index, key in enumerate(elements)}
    reactions = tuple(request.reactions)
    reaction_index = {row.reaction_id: index for index, row in enumerate(reactions)}
    knot_count = len(request.knots)
    radial_count = len(request.initial_species[0].cell_concentrations_mol_m3)
    species_count, element_count, reaction_count = len(species), len(elements), len(reactions)
    initial_geometry = geometry_states[0]
    current_geometry = initial_geometry
    initial_edges = _edges(float(initial_geometry["bore_radius_m"]),
                           float(request.knots[0].solution_film_thickness_m), radial_count)
    concentrations = {
        row.species_id: list(row.cell_concentrations_mol_m3) for row in request.initial_species
    }
    initial_moles = {
        key: math.fsum(value * volume for value, volume in zip(concentrations[key],
                    _cell_volumes_per_axial_metre(initial_edges), strict=True))
        for key in species_ids
    }
    if not all(math.isfinite(value) and value >= 0.0 for value in initial_moles.values()):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "initial_finite_species_inventory_outside_numeric_support",
        })
    outer_ledger = {key: 0.0 for key in species_ids}
    reaction_ledger = {key: 0.0 for key in species_ids}
    sweep_in = {key: 0.0 for key in species_ids}
    sweep_out = {key: 0.0 for key in species_ids}
    element_release = {key: 0.0 for key in elements}
    reaction_extents = {row.reaction_id: 0.0 for row in reactions}
    circuit_charge_C_m = 0.0
    history = []
    interval_ledger = []
    wall_initial = _wall_element_inventory_per_axial_metre(initial_geometry,
                                                            request.wall_elements, request.wall_density_kg_m3)
    if not all(math.isfinite(value) and value >= 0.0 for value in wall_initial.values()):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "initial_finite_wall_element_inventory_outside_numeric_support",
        })
    current_edges = initial_edges

    def inventory_snapshot() -> dict[str, float]:
        volumes = _cell_volumes_per_axial_metre(current_edges)
        return {key: math.fsum(value * volume for value, volume in
                               zip(concentrations[key], volumes, strict=True)) for key in species_ids}

    def audit_state(knot_index: int, geometry_state: dict, sweep_detail: dict[str, dict[str, float]]) -> dict | None:
        inventories = inventory_snapshot()
        species_rows = {row.species_id: row for row in species}
        liquid_balance = {}
        for species_id in species_ids:
            sweep_net = sweep_in[species_id] - sweep_out[species_id]
            residual = inventories[species_id] - initial_moles[species_id] - outer_ledger[species_id] - reaction_ledger[species_id] - sweep_net
            scale = max(abs(inventories[species_id]), abs(initial_moles[species_id]), abs(outer_ledger[species_id]),
                        abs(reaction_ledger[species_id]), abs(sweep_net))
            liquid_balance[species_id] = {"inventory_mol_m": inventories[species_id],
                "outer_boundary_exchange_mol_m": outer_ledger[species_id],
                "wall_reaction_transfer_mol_m": reaction_ledger[species_id],
                "swept_in_mol_m": sweep_in[species_id], "swept_out_mol_m": sweep_out[species_id],
                "residual_mol_m": residual, "scale_mol_m": scale}
            if not _allowed(residual, scale, request.inventory_absolute_tolerance_mol_m,
                            request.inventory_relative_tolerance):
                return {"reason": "species_inventory_balance_exceeded_tolerance", "species_id": species_id,
                        "residual_mol_m": residual, "scale_mol_m": scale, "inventories": liquid_balance}
        charge_inventory = math.fsum(species_rows[key].charge_number * inventories[key] for key in species_ids)
        initial_charge = math.fsum(species_rows[key].charge_number * initial_moles[key] for key in species_ids)
        boundary_charge = math.fsum(species_rows[key].charge_number * outer_ledger[key] for key in species_ids)
        reaction_charge = math.fsum(species_rows[key].charge_number * reaction_ledger[key] for key in species_ids)
        sweep_charge = math.fsum(species_rows[key].charge_number * (sweep_in[key] - sweep_out[key]) for key in species_ids)
        charge_residual = charge_inventory - initial_charge - boundary_charge - reaction_charge - sweep_charge
        if not _allowed(charge_residual, max(abs(charge_inventory), abs(initial_charge), abs(boundary_charge),
                                             abs(reaction_charge), abs(sweep_charge)),
                        request.charge_absolute_tolerance_C_m / FARADAY_C_MOL,
                        request.inventory_relative_tolerance):
            return {"reason": "liquid_charge_inventory_balance_exceeded_tolerance",
                    "charge_residual_mol_charge_m": charge_residual, "species_balance": liquid_balance}
        electronic_reaction_residual = FARADAY_C_MOL * reaction_charge + circuit_charge_C_m
        if not _allowed(electronic_reaction_residual, max(abs(FARADAY_C_MOL * reaction_charge),
                abs(circuit_charge_C_m)), request.charge_absolute_tolerance_C_m,
                request.inventory_relative_tolerance):
            return {"reason": "reaction_electron_transfer_charge_balance_exceeded_tolerance",
                    "reaction_electronic_charge_residual_C_m": electronic_reaction_residual}
        wall_now = _wall_element_inventory_per_axial_metre(geometry_state,
                                                            request.wall_elements, request.wall_density_kg_m3)
        wall_balances = {}
        for element in elements:
            geometric_release = wall_initial[element] - wall_now[element]
            residual = geometric_release - element_release[element]
            scale = max(abs(wall_initial[element]), abs(wall_now[element]), abs(geometric_release), abs(element_release[element]))
            wall_balances[element] = {"initial_wall_inventory_mol_m": wall_initial[element],
                "remaining_wall_inventory_mol_m": wall_now[element], "geometry_release_mol_m": geometric_release,
                "reaction_release_mol_m": element_release[element], "residual_mol_m": residual}
            if wall_now[element] < -request.inventory_absolute_tolerance_mol_m or element_release[element] < -request.inventory_absolute_tolerance_mol_m:
                return {"reason": "finite_wall_inventory_became_negative", "element_id": element, "wall_balances": wall_balances}
            if not _allowed(residual, scale, request.inventory_absolute_tolerance_mol_m,
                            request.inventory_relative_tolerance):
                return {"reason": "geometry_and_wall_reaction_element_inventory_mismatch", "element_id": element,
                        "residual_mol_m": residual, "wall_balances": wall_balances}
        aqueous_element_balance = {}
        for element in elements:
            liquid_delta = math.fsum(species_rows[key].elemental_composition.get(element, 0.0)
                                     * (inventories[key] - initial_moles[key]) for key in species_ids)
            boundary_delta = math.fsum(species_rows[key].elemental_composition.get(element, 0.0)
                                       * outer_ledger[key] for key in species_ids)
            reaction_delta = math.fsum(species_rows[key].elemental_composition.get(element, 0.0)
                                       * reaction_ledger[key] for key in species_ids)
            sweep_delta = math.fsum(species_rows[key].elemental_composition.get(element, 0.0)
                                    * (sweep_in[key] - sweep_out[key]) for key in species_ids)
            residual = liquid_delta - boundary_delta - reaction_delta - sweep_delta
            aqueous_element_balance[element] = residual
            if not _allowed(residual, max(abs(liquid_delta), abs(boundary_delta), abs(reaction_delta), abs(sweep_delta)),
                            request.inventory_absolute_tolerance_mol_m, request.inventory_relative_tolerance):
                return {"reason": "aqueous_element_inventory_balance_exceeded_tolerance", "element_id": element,
                        "residual_mol_m": residual, "aqueous_element_residuals_mol_m": aqueous_element_balance}
        snapshot = {
            "time_s": request.knots[knot_index].time_s,
            "geometry_state": geometry_state,
            "radial_edges_m": current_edges,
            "cell_concentration_mol_m3_by_species": concentrations,
            "species_inventory_balance_mol_m": liquid_balance,
            "wall_element_inventory_balance_mol_m": wall_balances,
            "aqueous_element_balance_residual_mol_m": aqueous_element_balance,
            "liquid_charge_residual_mol_charge_m": charge_residual,
            "reaction_extent_inventory_mol_m": reaction_extents,
            "electronic_circuit_charge_transfer_C_m": circuit_charge_C_m,
            "moving_boundary_sweep_ledger_mol_m": sweep_detail,
        }
        return snapshot

    first = audit_state(0, current_geometry, {})
    if first and "reason" in first:
        return Calculation(status="out_of_scope", values=base | {"reason": first["reason"],
            "failed_knot_index": 0, "balance_details": first})
    history.append(first)
    for index in range(knot_count - 1):
        start_knot, end_knot = request.knots[index], request.knots[index + 1]
        dt = end_knot.time_s - start_knot.time_s
        left_geometry = geometry_states[index]
        inner_radius = float(left_geometry["bore_radius_m"])
        outer_radius = inner_radius + start_knot.solution_film_thickness_m
        edges = current_edges
        volumes = _cell_volumes_per_axial_metre(edges)
        centers = [math.sqrt(edges[cell] * edges[cell + 1]) for cell in range(radial_count)]
        boundaries = {row.species_id: row for row in start_knot.species_boundaries}
        rates = {row.reaction_id: row.signed_extent_mol_m2_s for row in start_knot.reaction_extent_rates}
        reaction_species_rate = {key: 0.0 for key in species_ids}
        wall_element_rate = {key: 0.0 for key in elements}
        electron_charge_rate = 0.0
        wall_area_per_axial_m = 2.0 * math.pi * inner_radius
        for reaction in reactions:
            extent = rates[reaction.reaction_id]
            for species_id, coefficient in reaction.aqueous_species_stoichiometry.items():
                reaction_species_rate[species_id] += coefficient * extent * wall_area_per_axial_m
            for element, release in reaction.metal_element_release_mol_per_extent.items():
                wall_element_rate[element] += release * extent * wall_area_per_axial_m
            electron_charge_rate -= FARADAY_C_MOL * reaction.electron_count * extent * wall_area_per_axial_m
        state = [concentrations[key][cell] for key in species_ids for cell in range(radial_count)]
        boundary_offset = len(state)
        reaction_offset = boundary_offset + species_count
        element_offset = reaction_offset + species_count
        extent_offset = element_offset + element_count
        charge_offset = extent_offset + reaction_count
        state.extend([0.0] * (species_count * 2 + element_count + reaction_count + 1))
        absolute_tolerances = ([request.concentration_absolute_tolerance_mol_m3] * (species_count * radial_count)
            + [request.inventory_absolute_tolerance_mol_m] * (species_count * 2 + element_count + reaction_count)
            + [request.charge_absolute_tolerance_C_m])
        def rhs(_time, y):
            deriv = [0.0] * len(y)
            for species_pos, species_id in enumerate(species_ids):
                concentrations_now = y[species_pos * radial_count:(species_pos + 1) * radial_count]
                if any(not math.isfinite(value) or value < -10.0 * request.concentration_absolute_tolerance_mol_m3
                       for value in concentrations_now):
                    raise ArithmeticError("transient species concentration left nonnegative finite support")
                profile = boundaries[species_id]
                diffusivity = profile.radial_cell_diffusivity_m2_s
                cell_balance = [0.0] * radial_count
                for face in range(1, radial_count):
                    shared = edges[face]
                    resistance = (math.log(shared / centers[face - 1]) / diffusivity[face - 1]
                                  + math.log(centers[face] / shared) / diffusivity[face])
                    conductance = 2.0 * math.pi / resistance
                    flux = conductance * (concentrations_now[face - 1] - concentrations_now[face])
                    cell_balance[face - 1] -= flux
                    cell_balance[face] += flux
                outer_resistance = math.log(outer_radius / centers[-1]) / diffusivity[-1]
                outer_flux = (2.0 * math.pi / outer_resistance
                              * (profile.bulk_concentration_mol_m3 - concentrations_now[-1]))
                cell_balance[-1] += outer_flux
                cell_balance[0] += reaction_species_rate[species_id]
                for cell in range(radial_count):
                    deriv[species_pos * radial_count + cell] = cell_balance[cell] / volumes[cell]
                deriv[boundary_offset + species_pos] = outer_flux
                deriv[reaction_offset + species_pos] = reaction_species_rate[species_id]
            for element_pos, element in enumerate(elements):
                deriv[element_offset + element_pos] = wall_element_rate[element]
            for reaction_pos, reaction in enumerate(reactions):
                deriv[extent_offset + reaction_pos] = rates[reaction.reaction_id] * wall_area_per_axial_m
            deriv[charge_offset] = electron_charge_rate
            return deriv

        try:
            solved = solve_ivp(rhs, (start_knot.time_s, end_knot.time_s), state,
                method="BDF", t_eval=[end_knot.time_s], rtol=request.relative_tolerance,
                atol=absolute_tolerances, max_step=min(request.maximum_step_s, dt))
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transient_cylindrical_fv_interval_failed",
                "completed_knot_count": len(history) - 1,
                "failed_interval_index": index,
                "failure_detail": str(exc),
                "history_prefix": history,
                "interval_ledger": interval_ledger,
            })
        if not solved.success or solved.y.shape[1] != 1 or solved.t[-1] != end_knot.time_s:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transient_cylindrical_fv_solver_did_not_reach_interval_end",
                "completed_knot_count": len(history) - 1,
                "failed_interval_index": index,
                "solver_message": solved.message,
                "history_prefix": history,
                "interval_ledger": interval_ledger,
            })
        y = [float(value) for value in solved.y[:, -1]]
        if not all(math.isfinite(value) for value in y):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "transient_fv_state_or_ledger_nonfinite", "failed_interval_index": index,
                "history_prefix": history, "interval_ledger": interval_ledger,
            })
        for species_pos, species_id in enumerate(species_ids):
            values = y[species_pos * radial_count:(species_pos + 1) * radial_count]
            if any(value < -request.concentration_absolute_tolerance_mol_m3 for value in values):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "transient_species_inventory_became_negative", "failed_interval_index": index,
                    "species_id": species_id, "minimum_cell_concentration_mol_m3": min(values),
                    "history_prefix": history, "interval_ledger": interval_ledger,
                })
            concentrations[species_id] = [max(0.0, value) for value in values]
            outer_ledger[species_id] += y[boundary_offset + species_pos]
            reaction_ledger[species_id] += y[reaction_offset + species_pos]
        for element_pos, element in enumerate(elements):
            element_release[element] += y[element_offset + element_pos]
        for reaction_pos, reaction in enumerate(reactions):
            reaction_extents[reaction.reaction_id] += y[extent_offset + reaction_pos]
        circuit_charge_C_m += y[charge_offset]
        remap_detail = {key: {} for key in species_ids}
        old_edges = current_edges
        new_geometry = geometry_states[index + 1]
        next_knot = request.knots[index + 1]
        new_edges = _edges(float(new_geometry["bore_radius_m"]), next_knot.solution_film_thickness_m, radial_count)
        next_boundary = {row.species_id: row for row in next_knot.species_boundaries}
        for species_id in species_ids:
            sweep_concentration = next_boundary[species_id].bulk_concentration_mol_m3
            remapped, ledger = _remap_species(old_edges, new_edges, concentrations[species_id],
                sweep_concentration, next_boundary[species_id].bulk_concentration_mol_m3)
            concentrations[species_id] = remapped
            sweep_in[species_id] += ledger["swept_in_inner_mol_m"] + ledger["swept_in_outer_mol_m"]
            sweep_out[species_id] += ledger["swept_out_inner_mol_m"] + ledger["swept_out_outer_mol_m"]
            remap_detail[species_id] = ledger
        current_edges = new_edges
        current_geometry = new_geometry
        interval_ledger.append({
            "interval_index": index,
            "start_time_s": start_knot.time_s,
            "end_time_s": end_knot.time_s,
            "geometry_held_at_left_knot": True,
            "outer_boundary_species_exchange_mol_m": {
                key: y[boundary_offset + pos] for pos, key in enumerate(species_ids)
            },
            "wall_reaction_species_transfer_mol_m": {
                key: y[reaction_offset + pos] for pos, key in enumerate(species_ids)
            },
            "wall_element_release_mol_m": {
                key: y[element_offset + pos] for pos, key in enumerate(elements)
            },
            "reaction_extent_integral_mol_m": {
                row.reaction_id: y[extent_offset + reaction_index[row.reaction_id]] for row in reactions
            },
            "electronic_circuit_charge_transfer_C_m": y[charge_offset],
            "moving_geometry_rezone": remap_detail,
        })
        failure = audit_state(index + 1, current_geometry, remap_detail)
        if failure and "reason" in failure:
            return Calculation(status="out_of_scope", values=base | {
                "reason": failure["reason"], "completed_knot_count": len(history),
                "failed_knot_index": index + 1, "balance_details": failure,
                "history_prefix": history, "interval_ledger": interval_ledger,
            })
        history.append(failure)
    return Calculation(values=base | {
        "status": "computed",
        "species_ids": species_ids,
        "wall_element_ids": list(elements),
        "radial_cell_count": radial_count,
        "history": history,
        "interval_ledger": interval_ledger,
        "final_species_inventory_mol_m": history[-1]["species_inventory_balance_mol_m"],
        "final_wall_element_inventory_mol_m": history[-1]["wall_element_inventory_balance_mol_m"],
        "limitations": [
            "Geometry, boundary concentration, transport coefficient and reaction extent are held at each left knot over the following interval; geometry is conservatively rezoned only at the next exact knot.",
            "Radial transport is one-dimensional, axisymmetric, liquid-film-only, and uses caller piecewise-constant cell diffusivity without advection or homogeneous reaction.",
            "Signed wall reaction extents are imposed by the caller rather than solved from Butler-Volmer or concentration-dependent kinetics.",
            "Finite alloy inventory is estimated from caller density/composition and the cylindrical steel geometry; agreement with reaction metal release is a strict balance gate, not evidence of model validity.",
            "Scale transport, porosity, morphology, phase-specific solid inventories, pH evolution, corrosion qualification and life are not modeled.",
        ],
    }, notes=(
        "Species inventories include explicit outer-boundary exchange, reaction transfer and geometry-sweep inflow/outflow ledgers.",
        "Elemental and charge closure are checked separately; any failed balance, material depletion or negative concentration stops the run with its completed prefix.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalTransientTransport,
        evaluator=evaluate_wet_co2_cylindrical_transient_transport,
        units={
            "history[].time_s": "s",
            "history[].radial_edges_m[]": "m",
            "history[].cell_concentration_mol_m3_by_species.*[]": "mol/m^3",
            "history[].species_inventory_balance_mol_m.*.inventory_mol_m": "mol/m",
            "history[].wall_element_inventory_balance_mol_m.*.remaining_wall_inventory_mol_m": "mol/m",
            "history[].liquid_charge_residual_mol_charge_m": "mol_charge/m",
            "interval_ledger[].electronic_circuit_charge_transfer_C_m": "C/m",
        },
        assumptions=(
            "Each time interval uses its left-knot boundary, transport and reaction records; geometric remapping uses annular overlap and explicit caller concentrations for added material.",
            "The finite-volume balance is conservative in cylindrical volume per unit axial length and includes species, charge and alloy inventories.",
            "Every wall reaction is caller supplied and must satisfy declared element and charge stoichiometry.",
            "The calculation is a reduced transient transport model, not an aqueous chemistry solver or corrosion qualification.",
        ),
        source_ids=(SOURCE_ID, KINETICS_SOURCE_ID, "caller_wet_co2_initial_cylindrical_pipe_geometry"),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    )]
