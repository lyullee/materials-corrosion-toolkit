"""Transient cylindrical finite-volume species transport coupled to one BV potential."""

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
from .wet_co2_cylindrical_transient_transport import (
    FARADAY_C_MOL,
    WetCo2TransientInitialSpecies,
    WetCo2TransientSpecies,
    WetCo2TransientSpeciesBoundary,
    WetCo2WallElement,
    _allowed,
    _cell_volumes_per_axial_metre,
    _edges,
    _remap_species,
    _wall_element_inventory_per_axial_metre,
)

MODEL_ID = "integration.wet_co2_cylindrical_spatial_mixed_potential"
SOURCE_ID = "independent_transient_cylindrical_finite_volume_electrochemical_inventory"
KINETICS_SOURCE_ID = "caller_calibrated_butler_volmer_reaction_set"
GEOMETRY_SOURCE_ID = "degradation.wet_co2_cylindrical_scale_geometry_history"


class WetCo2SpatialElectrochemicalKnot(Contract):
    time_s: Nonnegative
    solution_film_thickness_m: Positive
    species_boundaries: tuple[WetCo2TransientSpeciesBoundary, ...] = Field(min_length=1, max_length=32)
    reactions: tuple[ButlerVolmerReaction, ...] = Field(min_length=2, max_length=64)
    boundary_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def records_are_bound(self):
        payload = {
            "time_s": self.time_s,
            "solution_film_thickness_m": self.solution_film_thickness_m,
            "species_boundaries": [row.model_dump(mode="json") for row in self.species_boundaries],
            "reactions": [row.model_dump(mode="json") for row in self.reactions],
        }
        if canonical_digest(payload) != self.boundary_record_sha256:
            raise ValueError("knot digest must bind time, bulk concentrations, diffusivities, film and BV branches")
        if not any(row.sha256 == self.boundary_record_sha256 and row.license_id for row in self.boundary_evidence):
            raise ValueError("licensed Evidence must pin each boundary and BV knot digest")
        if len({row.species_id for row in self.species_boundaries}) != len(self.species_boundaries):
            raise ValueError("one radial profile is required per species")
        if len({row.reaction_id for row in self.reactions}) != len(self.reactions):
            raise ValueError("BV reaction IDs must be unique per knot")
        if len({row.temperature_K for row in self.reactions}) != 1:
            raise ValueError("all BV branches at a knot must use one temperature")
        for reaction in self.reactions:
            if not reaction.calibration_and_reaction_direction_reviewed:
                raise ValueError("every BV branch must be reviewed")
            if not any(ev.sha256 == reaction.calibration_sha256 and ev.license_id for ev in self.boundary_evidence):
                raise ValueError("each BV calibration digest must have licensed knot Evidence")
        return self


class WetCo2CylindricalSpatialMixedPotential(Contract):
    """Finite transient radial inventory and common mixed-potential DAE on exact knots."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_spatial_mixed_potential.v1"] = (
        "matintegrity.wet_co2_cylindrical_spatial_mixed_potential.v1"
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
    knots: tuple[WetCo2SpatialElectrochemicalKnot, ...] = Field(min_length=2, max_length=2000)
    relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    concentration_absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    inventory_absolute_tolerance_mol_m: Positive = Field(default=1e-12)
    charge_absolute_tolerance_C_m: Positive = Field(default=1e-7)
    inventory_relative_tolerance: Positive = Field(default=1e-8, le=1e-2)
    potential_absolute_tolerance_V: Positive = Field(default=1e-10)
    maximum_bisection_iterations: int = Field(default=200, ge=1, le=500)
    maximum_step_s: Positive
    axisymmetric_reaction_area_and_material_mapping_reviewed: bool
    boundary_transport_and_chemistry_reviewed: bool
    element_charge_and_reaction_direction_reviewed: bool
    geometry_trial_mode: bool = False
    fixed_point_input_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    trial_geometry_closure_exemption_reviewed: bool = False

    @model_validator(mode="after")
    def verify_inputs(self):
        if self.geometry_trial_mode and not self.fixed_point_input_sha256:
            raise ValueError("geometry trial mode requires the controller fixed-point input digest")
        if self.geometry_trial_mode and not self.trial_geometry_closure_exemption_reviewed:
            raise ValueError("geometry trial mode requires explicit review of the deferred wall-geometry closure gate")
        if canonical_digest(self.geometry.model_dump(mode="json")) != self.geometry_sha256:
            raise ValueError("geometry digest differs from nested geometry request")
        if self.initial_state_evidence.sha256 != self.initial_state_sha256 or not self.initial_state_evidence.license_id:
            raise ValueError("licensed initial-state Evidence must pin the initial concentration arrays")
        if self.wall_material_evidence.sha256 != self.wall_material_record_sha256 or not self.wall_material_evidence.license_id:
            raise ValueError("licensed wall-material Evidence must pin alloy inputs")
        if not math.isclose(math.fsum(x.alloy_mass_fraction for x in self.wall_elements), 1.0,
                            rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("alloy element mass fractions must sum to one")
        material = {"density_kg_m3": self.wall_density_kg_m3,
                    "elements": [x.model_dump(mode="json") for x in self.wall_elements]}
        if canonical_digest(material) != self.wall_material_record_sha256:
            raise ValueError("wall material digest does not bind density and elemental fractions")
        species = {x.species_id: x for x in self.species}
        if len(species) != len(self.species):
            raise ValueError("species identities must be unique")
        initial = {x.species_id: x for x in self.initial_species}
        if set(initial) != set(species) or len(initial) != len(self.initial_species):
            raise ValueError("initial state must contain exactly one profile per species")
        if canonical_digest([x.model_dump(mode="json") for x in self.initial_species]) != self.initial_state_sha256:
            raise ValueError("initial state digest differs from ordered concentration profiles")
        counts = {len(x.cell_concentrations_mol_m3) for x in self.initial_species}
        if len(counts) != 1:
            raise ValueError("initial species arrays must have one common radial cell count")
        radial_count = next(iter(counts))
        if any(len(p.radial_cell_diffusivity_m2_s) != radial_count
               for knot in self.knots for p in knot.species_boundaries):
            raise ValueError("knot diffusivity arrays must match the radial mesh size")
        if sum(len(p.radial_cell_diffusivity_m2_s) for knot in self.knots
               for p in knot.species_boundaries) > 2_000_000:
            raise ValueError("total species-cell-knot work exceeds request budget")
        times = tuple(x.time_s for x in self.knots)
        if times[0] != 0 or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("knots must start at zero and strictly increase")
        if times != tuple(x.time_s for x in self.geometry.history):
            raise ValueError("geometry and electrochemical knots must align exactly and in order")
        reaction_ids = {row.reaction_id for row in self.knots[0].reactions}
        if any({row.reaction_id for row in knot.reactions} != reaction_ids for knot in self.knots):
            raise ValueError("all exact knots must provide the same reaction identities")
        formulas = {key: row.elemental_composition for key, row in species.items()}
        charges = {key: row.charge_number for key, row in species.items()}
        element_ids = {row.element_id for row in self.wall_elements}
        for knot in self.knots:
            if {row.species_id for row in knot.species_boundaries} != set(species):
                raise ValueError("each knot must have exactly one boundary/diffusivity record per species")
            if len(knot.species_boundaries[0].radial_cell_diffusivity_m2_s) * len(species) > 2_000_000:
                raise ValueError("single-knot species-cell work exceeds request budget")
            for reaction in knot.reactions:
                coeffs = reaction.stoichiometric_species_coefficients
                if not coeffs or not set(coeffs) <= set(species):
                    raise ValueError("each BV reaction must reference declared aqueous species")
                qdelta = math.fsum(charges[key] * value for key, value in coeffs.items())
                if not math.isclose(qdelta, float(reaction.electron_count), rel_tol=1e-10, abs_tol=1e-10):
                    raise ValueError("anodic aqueous charge change must equal the declared electron count")
                all_elements = element_ids | {e for sid in coeffs for e in formulas[sid]}
                for element in all_elements:
                    delta = math.fsum(coeffs[sid] * formulas[sid].get(element, 0.0) for sid in coeffs)
                    if (element in element_ids and delta < -1e-10) or (element not in element_ids and abs(delta) > 1e-10):
                        raise ValueError("reaction element change must be zero for nonalloy elements and nonnegative for wall elements")
        return self


def _transport_fluxes(concentrations: list[list[float]] | dict[str, list[float]], boundary: dict, edges: list[float],
                      inner_radius: float, reactions: tuple[ButlerVolmerReaction, ...],
                      tolerance: float, max_iterations: int) -> tuple[float, dict, dict]:
    """Solve one current-neutral potential with branchwise finite wall supply limits."""
    species_ids = list(boundary)
    centers = [math.sqrt(edges[j] * edges[j + 1]) for j in range(len(edges) - 1)]
    transport_cap = {}
    for pos, sid in enumerate(species_ids):
        # Cylindrical wall-to-first-cell-center conductance per inner wall area.
        d = boundary[sid].radial_cell_diffusivity_m2_s[0]
        k = d / (inner_radius * math.log(centers[0] / inner_radius))
        profile = concentrations[sid] if isinstance(concentrations, dict) else concentrations[pos]
        transport_cap[sid] = k * max(0.0, profile[0])
    low = max(r.equilibrium_potential_V + r.minimum_overpotential_V for r in reactions)
    high = min(r.equilibrium_potential_V + r.maximum_overpotential_V for r in reactions)
    if low >= high:
        raise ValueError("BV branches have no common calibrated potential range")

    def evaluate(potential: float):
        raw = {r.reaction_id: electrode_reaction_flux(r, potential) for r in reactions}
        if any(row.get("status") != "computed" for row in raw.values()):
            raise ValueError("potential or BV current left caller calibration support")
        factors = {r.reaction_id: {"anodic": 1.0, "cathodic": 1.0} for r in reactions}
        demand_rows = {}
        for sid, cap in transport_cap.items():
            demands = {}
            for r in reactions:
                coeff = r.stoichiometric_species_coefficients.get(sid, 0.0)
                if not coeff:
                    continue
                branch = "anodic" if coeff < 0 else "cathodic"
                current_key = "gross_anodic_current_density_A_m2" if coeff < 0 else "gross_cathodic_current_density_A_m2"
                demands[(r.reaction_id, branch)] = abs(coeff) * raw[r.reaction_id][current_key] / (r.electron_count * FARADAY_C_MOL)
            total = math.fsum(demands.values())
            factor = 1.0 if total <= cap or total == 0 else cap / total
            for reaction_id, branch in demands:
                factors[reaction_id][branch] = min(factors[reaction_id][branch], factor)
            demand_rows[sid] = {"unlimited_consumption_mol_m2_s": total,
                                "radial_wall_supply_mol_m2_s": cap, "branch_factor": factor}
        result = {}
        currents = []
        for r in reactions:
            row = raw[r.reaction_id]
            anodic = row["gross_anodic_current_density_A_m2"] * factors[r.reaction_id]["anodic"]
            cathodic = row["gross_cathodic_current_density_A_m2"] * factors[r.reaction_id]["cathodic"]
            current = anodic - cathodic
            extent = current / (r.electron_count * FARADAY_C_MOL)
            currents.append(current)
            result[r.reaction_id] = {"anodic_current_density_A_m2": anodic,
                "cathodic_current_density_A_m2": cathodic, "current_density_A_m2": current,
                "extent_mol_m2_s": extent, "branch_factors": factors[r.reaction_id]}
        return math.fsum(currents), result, demand_rows

    left, right = evaluate(low), evaluate(high)
    if left[0] > 0 or right[0] < 0:
        raise ValueError("current-neutral potential is not bracketed in calibrated range")
    if left[0] == 0:
        potential, solution = low, left
    elif right[0] == 0:
        potential, solution = high, right
    else:
        lo, hi = low, high
        solution = left
        for _ in range(max_iterations):
            potential = lo + 0.5 * (hi - lo)
            solution = evaluate(potential)
            if abs(solution[0]) <= 1e-12 or hi - lo <= tolerance:
                break
            if solution[0] < 0:
                lo = potential
            else:
                hi = potential
        else:
            raise ArithmeticError("mixed-potential bisection exceeded its iteration budget")
    return potential, solution[1], solution[2]


def evaluate_wet_co2_cylindrical_spatial_mixed_potential(request: WetCo2CylindricalSpatialMixedPotential) -> Calculation:
    """Integrate the spatial semi-discrete inventory while solving common BV potential at every RHS state."""
    from scipy.integrate import solve_ivp

    digest = canonical_digest(request.model_dump(mode="json"))
    base = {"assessment_id": request.assessment_id, "model_id": MODEL_ID, "input_sha256": digest,
            "geometry_request_sha256": request.geometry_sha256, "time_interpolation": "left_hold_exact_knots",
            "wall_reaction_coupling": "common_zero_net_current_potential_with_cell_supply_limited_BV_branches",
            "geometry_trial_mode": request.geometry_trial_mode,
            "fixed_point_input_sha256": request.fixed_point_input_sha256}
    missing = [name for name, value in {
        "axisymmetric_reaction_area_and_material_mapping_reviewed": request.axisymmetric_reaction_area_and_material_mapping_reviewed,
        "boundary_transport_and_chemistry_reviewed": request.boundary_transport_and_chemistry_reviewed,
        "element_charge_and_reaction_direction_reviewed": request.element_charge_and_reaction_direction_reviewed,
    }.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"reason": "caller_review_gates_incomplete", "missing_reviews": missing})
    geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(request.geometry)
    if geometry.status != "computed":
        return Calculation(status=geometry.status, values=base | {"reason": "geometry_not_computed", "geometry_status": geometry.status})
    states = geometry.values["history"]
    base["geometry_result_sha256"] = canonical_digest(geometry.model_dump(mode="json"))
    species = list(request.species); sids = [x.species_id for x in species]; sidx = {x: i for i, x in enumerate(sids)}
    elements = [x.element_id for x in request.wall_elements]
    reactions0 = request.knots[0].reactions; rids = [x.reaction_id for x in reactions0]
    nsp = len(sids); nr = len(request.initial_species[0].cell_concentrations_mol_m3)
    profiles = {x.species_id: list(x.cell_concentrations_mol_m3) for x in request.initial_species}
    edges = _edges(float(states[0]["bore_radius_m"]), request.knots[0].solution_film_thickness_m, nr)
    initial_moles = {sid: math.fsum(c*v for c, v in zip(profiles[sid], _cell_volumes_per_axial_metre(edges), strict=True)) for sid in sids}
    wall_initial = _wall_element_inventory_per_axial_metre(states[0], request.wall_elements, request.wall_density_kg_m3)
    outer_total = {sid: 0.0 for sid in sids}; reaction_total = {sid: 0.0 for sid in sids}
    extents = {rid: 0.0 for rid in rids}; wall_release = {e: 0.0 for e in elements}; circuit_charge = 0.0
    history = []; intervals = []
    target_radii = [float(states[0]["bore_radius_m"])]
    wall_balance_history = {e: [0.0] for e in elements}
    if not all(math.isfinite(v) and v >= 0 for v in initial_moles.values()):
        return Calculation(status="out_of_scope", values=base | {"reason": "invalid_initial_finite_inventory"})

    for k in range(len(request.knots) - 1):
        knot, next_knot = request.knots[k], request.knots[k + 1]
        dt = next_knot.time_s - knot.time_s
        geom = states[k]; radius = float(geom["bore_radius_m"]); area = 2 * math.pi * radius
        boundary_rows = {x.species_id: x for x in knot.species_boundaries}
        boundary = {sid: boundary_rows[sid] for sid in sids}
        reactions = knot.reactions
        current_edges = edges
        vols = _cell_volumes_per_axial_metre(edges)
        centers = [math.sqrt(edges[j] * edges[j + 1]) for j in range(nr)]
        # State: concentrations (species-major), outer exchange, species wall transfer,
        # metal-element release, reaction extents, electronic charge, and current integral.
        csize = nsp * nr; off_outer = csize; off_rxn_species = off_outer + nsp
        off_elements = off_rxn_species + nsp; off_extents = off_elements + len(elements)
        off_charge = off_extents + len(rids); off_current = off_charge + 1
        y0 = [profiles[sid][j] for sid in sids for j in range(nr)] + [0.0] * (2*nsp + len(elements) + len(rids) + 2)
        atol = [request.concentration_absolute_tolerance_mol_m3] * csize + [request.inventory_absolute_tolerance_mol_m] * (2*nsp+len(elements)+len(rids)) + [request.charge_absolute_tolerance_C_m, request.charge_absolute_tolerance_C_m]
        last_potential = [None]

        def rhs(_t, y):
            cs = [list(y[p*nr:(p+1)*nr]) for p in range(nsp)]
            if any(not math.isfinite(c) or c < -request.concentration_absolute_tolerance_mol_m3 for row in cs for c in row):
                raise ArithmeticError("cell concentration became negative or nonfinite")
            potential, reaction_rows, _supply = _transport_fluxes(dict(zip(sids, cs, strict=True)), boundary, edges, radius, reactions,
                request.potential_absolute_tolerance_V, request.maximum_bisection_iterations)
            last_potential[0] = potential
            reaction_species_rate = {sid: 0.0 for sid in sids}; element_rate = {e: 0.0 for e in elements}
            extent_rate = {rid: 0.0 for rid in rids}; current_sum = 0.0
            for r in reactions:
                row = reaction_rows[r.reaction_id]; extent = row["extent_mol_m2_s"]
                extent_rate[r.reaction_id] = extent * area
                current_sum += row["current_density_A_m2"] * area
                for sid, coeff in r.stoichiometric_species_coefficients.items():
                    reaction_species_rate[sid] += coeff * extent * area
                # Element release is inferred only from caller stoichiometry/formula.
                # Add metal source where the dissolved aqueous balance contains positive element gain.
                for e in elements:
                    gained = math.fsum(coeff * species[sidx[sid]].elemental_composition.get(e, 0.0)
                                       for sid, coeff in r.stoichiometric_species_coefficients.items())
                    if gained > 0:
                        element_rate[e] += gained * extent * area
            dy = [0.0] * len(y)
            for pos, sid in enumerate(sids):
                cc = cs[pos]; d = boundary[sid].radial_cell_diffusivity_m2_s
                balance = [0.0] * nr
                for f in range(1, nr):
                    rface = edges[f]
                    resistance = math.log(rface/centers[f-1])/d[f-1] + math.log(centers[f]/rface)/d[f]
                    flux = 2*math.pi/resistance * (cc[f-1]-cc[f])
                    balance[f-1] -= flux; balance[f] += flux
                out_res = math.log(edges[-1]/centers[-1])/d[-1]
                out_flux = 2*math.pi/out_res * (boundary[sid].bulk_concentration_mol_m3-cc[-1])
                balance[-1] += out_flux; balance[0] += reaction_species_rate[sid]
                for j in range(nr): dy[pos*nr+j] = balance[j]/vols[j]
                dy[off_outer+pos] = out_flux
                dy[off_rxn_species+pos] = reaction_species_rate[sid]
            for p, e in enumerate(elements): dy[off_elements+p] = element_rate[e]
            for p, rid in enumerate(rids): dy[off_extents+p] = extent_rate[rid]
            dy[off_charge] = -FARADAY_C_MOL * math.fsum(r.electron_count * reaction_rows[r.reaction_id]["extent_mol_m2_s"] * area for r in reactions)
            dy[off_current] = current_sum
            return dy

        try:
            sol = solve_ivp(rhs, (knot.time_s, next_knot.time_s), y0, method="BDF", t_eval=[next_knot.time_s],
                            rtol=request.relative_tolerance, atol=atol, max_step=min(request.maximum_step_s, dt))
        except (ArithmeticError, ValueError, OverflowError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {"reason": "coupled_radial_interval_failed",
                "failed_interval_index": k, "detail": str(exc), "history_prefix": history, "interval_ledger": intervals})
        if not sol.success or sol.y.shape[1] != 1 or sol.t[-1] != next_knot.time_s:
            return Calculation(status="out_of_scope", values=base | {"reason": "coupled_radial_solver_did_not_reach_knot",
                "failed_interval_index": k, "solver_message": sol.message, "history_prefix": history, "interval_ledger": intervals})
        y = [float(x) for x in sol.y[:, -1]]
        if any(not math.isfinite(x) for x in y):
            return Calculation(status="out_of_scope", values=base | {"reason": "nonfinite_coupled_state", "failed_interval_index": k})
        for p, sid in enumerate(sids):
            vals = y[p*nr:(p+1)*nr]
            if min(vals) < -request.concentration_absolute_tolerance_mol_m3:
                return Calculation(status="out_of_scope", values=base | {"reason": "negative_cell_concentration",
                    "failed_interval_index": k, "species_id": sid, "minimum_mol_m3": min(vals), "history_prefix": history})
            profiles[sid] = [max(0.0, x) for x in vals]
            outer_total[sid] += y[off_outer+p]; reaction_total[sid] += y[off_rxn_species+p]
        for p,e in enumerate(elements): wall_release[e] += y[off_elements+p]
        for p,rid in enumerate(rids): extents[rid] += y[off_extents+p]
        circuit_charge += y[off_charge]
        current_integral = y[off_current]
        try:
            end_potential, _end_reactions, _ = _transport_fluxes(profiles, boundary, edges, radius, reactions,
                request.potential_absolute_tolerance_V, request.maximum_bisection_iterations)
        except (ArithmeticError, ValueError, OverflowError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {"reason": "end_knot_mixed_potential_failed",
                "failed_interval_index": k, "detail": str(exc), "history_prefix": history})
        # Account for species inventory swept by geometry/mesh changes using conservative overlap.
        next_geom = states[k+1]; new_edges = _edges(float(next_geom["bore_radius_m"]), next_knot.solution_film_thickness_m, nr)
        next_bound = {x.species_id: x for x in next_knot.species_boundaries}
        sweep = {}
        for sid in sids:
            remapped, ledger = _remap_species(edges, new_edges, profiles[sid], next_bound[sid].bulk_concentration_mol_m3,
                                               next_bound[sid].bulk_concentration_mol_m3)
            profiles[sid] = remapped; sweep[sid] = ledger
        edges = new_edges
        # Exact species inventory closure includes explicit rezone fill/discard terms.
        volumes = _cell_volumes_per_axial_metre(edges)
        inventories = {sid: math.fsum(c*v for c,v in zip(profiles[sid],volumes,strict=True)) for sid in sids}
        sweep_net = {sid: sweep[sid]["swept_in_inner_mol_m"] + sweep[sid]["swept_in_outer_mol_m"] - sweep[sid]["swept_out_inner_mol_m"] - sweep[sid]["swept_out_outer_mol_m"] for sid in sids}
        residuals = {sid: inventories[sid] - initial_moles[sid] - outer_total[sid] - reaction_total[sid] for sid in sids}
        # Successful prior remaps are carried in the interval ledger for cumulative closure.
        for sid in sids:
            prior = math.fsum(row["sweep_net_mol_m"][sid] for row in intervals)
            residuals[sid] -= prior + sweep_net[sid]
        bad = next((sid for sid in sids if not _allowed(residuals[sid], max(abs(inventories[sid]),abs(initial_moles[sid]),abs(outer_total[sid]),abs(reaction_total[sid]),abs(sweep_net[sid])), request.inventory_absolute_tolerance_mol_m, request.inventory_relative_tolerance)), None)
        if bad:
            return Calculation(status="out_of_scope", values=base | {"reason": "species_inventory_closure_failed", "failed_interval_index": k,
                "species_id": bad, "residual_mol_m": residuals[bad], "history_prefix": history})
        total_sweep_net = {sid: math.fsum(row["moving_geometry_sweep_net_mol_m"][sid] for row in intervals) + sweep_net[sid]
                           for sid in sids}
        charge_residual = math.fsum(request.species[sidx[sid]].charge_number *
            (inventories[sid]-initial_moles[sid]-outer_total[sid]-reaction_total[sid]-total_sweep_net[sid]) for sid in sids)
        if not _allowed(charge_residual, max(1e-30, math.fsum(abs(v) for v in inventories.values())),
                        request.charge_absolute_tolerance_C_m/FARADAY_C_MOL, request.inventory_relative_tolerance):
            return Calculation(status="out_of_scope", values=base | {"reason": "aqueous_charge_inventory_closure_failed", "failed_interval_index": k,
                "residual_mol_charge_m": charge_residual})
        electronic_residual = FARADAY_C_MOL * math.fsum(
            request.species[sidx[sid]].charge_number * reaction_total[sid] for sid in sids
        ) + circuit_charge
        if not _allowed(electronic_residual, max(abs(circuit_charge), 1e-30),
                        request.charge_absolute_tolerance_C_m, request.inventory_relative_tolerance):
            return Calculation(status="out_of_scope", values=base | {"reason": "reaction_electronic_charge_closure_failed",
                "electronic_residual_C_m": electronic_residual, "history_prefix": history})
        aqueous_element_residuals = {}
        tracked_elements = sorted({e for row in request.species for e in row.elemental_composition})
        for element in tracked_elements:
            liquid_delta = math.fsum(request.species[sidx[sid]].elemental_composition.get(element, 0.0)
                                     * (inventories[sid] - initial_moles[sid]) for sid in sids)
            boundary_delta = math.fsum(request.species[sidx[sid]].elemental_composition.get(element, 0.0)
                                       * outer_total[sid] for sid in sids)
            reaction_delta = math.fsum(request.species[sidx[sid]].elemental_composition.get(element, 0.0)
                                       * reaction_total[sid] for sid in sids)
            sweep_delta = math.fsum(request.species[sidx[sid]].elemental_composition.get(element, 0.0)
                                    * total_sweep_net[sid] for sid in sids)
            residual = liquid_delta - boundary_delta - reaction_delta - sweep_delta
            aqueous_element_residuals[element] = residual
            if not _allowed(residual, max(abs(liquid_delta), abs(boundary_delta), abs(reaction_delta), abs(sweep_delta)),
                            request.inventory_absolute_tolerance_mol_m, request.inventory_relative_tolerance):
                return Calculation(status="out_of_scope", values=base | {"reason": "aqueous_element_inventory_closure_failed",
                    "element_id": element, "residual_mol_m": residual, "history_prefix": history})
        wall_now = _wall_element_inventory_per_axial_metre(next_geom, request.wall_elements, request.wall_density_kg_m3)
        elem_resid = {e: wall_initial[e]-wall_now[e]-wall_release[e] for e in elements}
        if any(wall_release[e] < -request.inventory_absolute_tolerance_mol_m for e in elements):
            return Calculation(status="out_of_scope", values=base | {"reason": "net_wall_element_deposition_outside_recession_model",
                "wall_element_release_mol_m": wall_release, "history_prefix": history})
        if (not request.geometry_trial_mode and any(
                abs(v) > request.inventory_absolute_tolerance_mol_m
                + request.inventory_relative_tolerance*max(abs(wall_initial[e]),1e-30)
                for e,v in elem_resid.items())):
            return Calculation(status="out_of_scope", values=base | {"reason": "wall_element_geometry_closure_failed", "element_residual_mol_m": elem_resid,
                "history_prefix": history})
        element_mass_kg_m = math.fsum(
            wall_release[element.element_id] * element.atomic_molar_mass_kg_mol
            for element in request.wall_elements
        )
        scale_inventory = {row.phase_id: row.moles_per_axial_metre_mol_m
                           for row in request.geometry.history[k + 1].phase_inventories}
        scale_volume_per_length_m2 = math.fsum(
            scale_inventory[phase.phase_id] * phase.molar_volume_m3_mol
            for phase in request.geometry.phases
        )
        steel_inner_radius_target_sq = request.geometry.initial_inner_radius_m**2 + element_mass_kg_m / (
            request.wall_density_kg_m3 * math.pi
        )
        target_radius_sq = steel_inner_radius_target_sq - scale_volume_per_length_m2 / math.pi
        if not math.isfinite(target_radius_sq) or target_radius_sq <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
            "reason": "element_release_and_scale_inventory_imply_invalid_target_radius",
                "failed_interval_index": k,
                "history_prefix": history,
            })
        target_radius = math.sqrt(target_radius_sq)
        if target_radius >= request.geometry.outer_radius_m:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "element_release_exhausts_cylindrical_wall",
                "failed_interval_index": k,
                "target_bore_radius_m": target_radius,
                "history_prefix": history,
            })
        target_radii.append(target_radius)
        for element_id in elements:
            wall_balance_history[element_id].append(elem_resid[element_id])
        history.append({"time_s": next_knot.time_s, "geometry_state": next_geom, "radial_edges_m": edges,
            "cell_concentration_mol_m3_by_species": profiles, "mixed_potential_at_interval_end_V": end_potential,
            "species_inventory_mol_m": inventories, "species_balance_residual_mol_m": residuals,
            "aqueous_charge_residual_mol_charge_m": charge_residual,
            "aqueous_element_balance_residual_mol_m": aqueous_element_residuals,
            "wall_element_balance_residual_mol_m": elem_resid,
            "reaction_extent_inventory_mol_m": extents, "circuit_charge_transfer_C_m": circuit_charge})
        intervals.append({"interval_index": k, "start_time_s": knot.time_s, "end_time_s": next_knot.time_s,
            "geometry_held_at_left_knot": True, "mixed_potential_at_interval_end_V": end_potential,
            "integrated_net_current_C_m": current_integral, "outer_boundary_exchange_mol_m": {sid:y[off_outer+p] for p,sid in enumerate(sids)},
            "wall_reaction_species_transfer_mol_m": {sid:y[off_rxn_species+p] for p,sid in enumerate(sids)},
            "moving_geometry_sweep_net_mol_m": sweep_net, "mixed_potential_zero_current_residual_A_m": current_integral/max(dt,1e-30),
            "reaction_extent_mol_m": {rid:y[off_extents+p] for p,rid in enumerate(rids)},
            "wall_element_release_increment_mol_m": {
                element_id: y[off_elements+p] for p, element_id in enumerate(elements)},
            "wall_element_balance_residual_mol_m_by_element": elem_resid,
            "trial_target_bore_radius_m": target_radius})
    return Calculation(status="computed", values=base | {"history": history, "interval_ledger": intervals,
        "final_species_inventory_mol_m": history[-1]["species_inventory_mol_m"], "final_wall_element_balance_mol_m": history[-1]["wall_element_balance_residual_mol_m"],
        "time_s": [float(row.time_s) for row in request.knots],
        "input_bore_radius_m_by_knot": [float(row["bore_radius_m"]) for row in states],
        "target_bore_radius_m_by_knot": target_radii,
        "wall_element_balance_residual_mol_m_by_element": wall_balance_history,
        "wall_element_inventory_scale_mol_m": {
            element_id: [abs(wall_initial[element_id])] * len(target_radii)
            for element_id in elements
        },
        "trial_result_only": request.geometry_trial_mode,
        "qualification": "caller_bound transient spatial screening; not validated for design or life prediction"})


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(model_id=MODEL_ID, input_type=WetCo2CylindricalSpatialMixedPotential,
        evaluator=evaluate_wet_co2_cylindrical_spatial_mixed_potential,
        units={"time": "s", "concentration": "mol/m3", "potential": "V", "inventory": "mol/m", "current": "A/m"},
        assumptions=("Exact geometry knots with left-held interval inputs.",
                     "Axisymmetric radial finite-volume aqueous domain per unit axial length.",
                     "Caller BV branches share one zero-net-current mixed potential at each integrated state.",
                     "Species consumption is limited by first-cell cylindrical wall supply; nonnegative inventories are fail-closed."),
        source_ids=(SOURCE_ID, KINETICS_SOURCE_ID, GEOMETRY_SOURCE_ID), version="1.0.0"),)
