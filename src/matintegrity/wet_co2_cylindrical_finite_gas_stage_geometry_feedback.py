"""Same-stage finite-gas wet-CO2 transport with algebraic moving-cylinder geometry."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_finite_gas_stage_speciation_feedback import (
    GAS_CAP_SOURCE_ID,
    GAS_COUPLING_SOURCE_ID,
    GAS_INITIAL_SOURCE_ID,
    GAS_TRANSFER_SOURCE_ID,
    KINETICS_SOURCE_ID,
    SPECIATION_SOURCE_ID,
    SUPPLY_SOURCE_ID,
    WetCo2CylindricalFiniteGasStageSpeciationFeedback,
    _solve_stage_mass_action,
    _stage_fluxes,
)
from .wet_co2_cylindrical_scale_geometry import evaluate_wet_co2_cylindrical_scale_geometry_history
from .wet_co2_cylindrical_stage_speciation_scale_feedback import WetCo2StageShearRemoval
from .wet_co2_cylindrical_spatial_mixed_potential import _transport_fluxes
from .wet_co2_cylindrical_transient_transport import (
    FARADAY_C_MOL,
    _cell_volumes_per_axial_metre,
    _edges,
    _remap_species,
)
from .wet_co2_finite_gas_liquid_exchange_history import _overall_liquid_coefficient

MODEL_ID = "integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback"
MOVING_GEOMETRY_SOURCE_ID = "same_stage_cylindrical_radius_from_wall_and_scale_inventories"
ALE_MESH_SOURCE_ID = "lagrangian_radial_mesh_conserved_cell_inventory_transport"
SHEAR_HISTORY_SOURCE_ID = "caller_wall_shear_history"
SHEAR_LAW_SOURCE_ID = "caller_calibrated_shear_scale_detachment_law"


class WetCo2CylindricalFiniteGasStageGeometryFeedback(Contract):
    """Finite gas + BDF-stage speciation/scale with bore radius updated in the same RHS."""

    schema_version: Literal[
        "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v1",
        "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v2",
    ] = (
        "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    finite_gas_stage_request: WetCo2CylindricalFiniteGasStageSpeciationFeedback
    shear_removal: WetCo2StageShearRemoval | None = None
    same_stage_geometry_recomputation_reviewed: bool
    lagrangian_mesh_and_boundary_motion_assumption_reviewed: bool
    no_qualification_claim_reviewed: bool

    @model_validator(mode="after")
    def validate_dynamic_geometry_scope(self):
        req = self.finite_gas_stage_request
        if self.assessment_id != req.assessment_id:
            raise ValueError("assessment IDs must match the nested finite-gas stage request")
        if self.shear_removal is not None and self.schema_version != "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v2":
            raise ValueError("finite-gas stage shear removal requires schema version v2")
        if self.schema_version == "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v2" and self.shear_removal is None:
            raise ValueError("schema version v2 requires caller-bound stage shear-removal configuration")
        if self.shear_removal is not None:
            shear = self.shear_removal
            times = tuple(row.time_s for row in req.spatial_request.knots)
            if tuple(row.time_s for row in shear.shear_history) != times:
                raise ValueError("finite-gas shear knots must exactly match all BDF transport knots")
            phase_ids = {row.phase_id for row in req.phases}
            law_ids = [row.phase_id for row in shear.phase_laws]
            if len(law_ids) != len(set(law_ids)) or set(law_ids) != phase_ids:
                raise ValueError("finite-gas shear laws must cover each scale phase exactly once")
            if not all((shear.exact_knot_left_hold_reviewed,
                        shear.detached_solid_export_and_inner_area_reviewed,
                        shear.phase_law_applicability_reviewed)):
                raise ValueError("finite-gas shear mode requires left-hold, export-basis and law-applicability review")
        if not self.same_stage_geometry_recomputation_reviewed:
            raise ValueError("same-stage radius/transport feedback requires explicit caller review")
        if not self.lagrangian_mesh_and_boundary_motion_assumption_reviewed:
            raise ValueError("the Lagrangian radial-mesh motion and fixed outer-boundary assumption require caller review")
        if not self.no_qualification_claim_reviewed:
            raise ValueError("caller must acknowledge that this model is not a corrosion qualification")
        return self


def _radius_from_inventory(request, geometry, phase_volumes, cumulative_wall_release, phase_inventory):
    if any(not math.isfinite(value) or value < -request.absolute_inventory_tolerance_mol_m
            for value in phase_inventory.values()):
        raise ArithmeticError("live phase inventory is negative or nonfinite")
    if any(not math.isfinite(value) or value < -request.absolute_inventory_tolerance_mol_m
            for value in cumulative_wall_release.values()):
        raise ArithmeticError("cumulative wall release is negative or nonfinite")
    wall_mass = math.fsum(cumulative_wall_release[e.element_id] * e.atomic_molar_mass_kg_mol
        for e in request.spatial_request.wall_elements)
    steel_r2 = geometry.initial_inner_radius_m ** 2 + wall_mass / (request.spatial_request.wall_density_kg_m3 * math.pi)
    phase_annulus = math.fsum(phase_inventory[p] * phase_volumes[p] for p in phase_volumes) / math.pi
    bore_r2 = steel_r2 - phase_annulus
    if not all(math.isfinite(v) for v in (steel_r2, bore_r2)) or steel_r2 <= 0.0 or bore_r2 <= 0.0:
        raise ArithmeticError("same-stage cylindrical radius is nonpositive or nonfinite")
    steel_radius, bore_radius = math.sqrt(steel_r2), math.sqrt(bore_r2)
    if steel_radius >= geometry.outer_radius_m or bore_radius >= steel_radius:
        raise ArithmeticError("same-stage wall or bore geometry exceeds its declared envelope")
    return bore_radius, steel_radius


def _run_dynamic_intervals(request, geometry, initial_bore_radius, rhs_budget, shear_removal=None):
    from scipy.integrate import solve_ivp

    stage = request.finite_gas_stage_request
    spatial = stage.spatial_request
    species = list(spatial.species)
    sids = [row.species_id for row in species]
    sidx = {sid: i for i, sid in enumerate(sids)}
    nr, nsp = len(spatial.initial_species[0].cell_concentrations_mol_m3), len(sids)
    ne, phases = len(spatial.wall_elements), stage.phases
    phase_volumes = {p.phase_id: p.molar_volume_m3_mol for p in spatial.geometry.phases}
    initial_phase = {row.phase_id: row.moles_per_axial_metre_mol_m for row in spatial.geometry.history[0].phase_inventories}
    phase_inventory = dict(initial_phase)
    cumulative_detached = {p.phase_id: 0.0 for p in phases}
    cumulative_wall = {row.element_id: 0.0 for row in spatial.wall_elements}
    gas_species = stage.gas_transfer_species_id
    gas_capacity = stage.gas_inventory_capacity_mol_per_axial_metre_Pa
    gas_area = stage.gas_liquid_interfacial_area_m_per_axial_metre
    henry = stage.henry_concentration_over_fugacity_mol_m3_Pa
    transfer_k = _overall_liquid_coefficient(stage.gas_film_coefficient_mol_m2_s_Pa, henry,
        stage.liquid_film_coefficient_m_s)
    if transfer_k is None:
        return {"failure": {"failed_interval_index": 0, "reason": "gas_liquid_transfer_conductance_outside_numeric_support",
            "completed_intervals": []}, "history": [], "intervals": []}
    gas_fugacity = float(stage.initial_gas_co2_fugacity_Pa)
    cumulative_gas_transfer = 0.0
    profiles = {row.species_id: list(row.cell_concentrations_mol_m3) for row in spatial.initial_species}
    ma = stage.mass_action_system_template
    ma_sha = canonical_digest(ma.model_dump(mode="json"))
    intervals, history = [], []
    previous_edges = None
    seed_radius, _ = _radius_from_inventory(stage, spatial.geometry, phase_volumes, cumulative_wall, phase_inventory)
    geometry_seed_tolerance = stage.absolute_radius_tolerance_m + stage.relative_radius_tolerance * max(initial_bore_radius, 1e-30)
    if abs(seed_radius - initial_bore_radius) > geometry_seed_tolerance:
        return {"failure": {"failed_interval_index": 0, "reason": "initial_geometry_inventory_seed_mismatch",
            "geometry_seed_radius_m": initial_bore_radius, "inventory_derived_radius_m": seed_radius,
            "allowed_residual_m": geometry_seed_tolerance}, "history": [], "intervals": []}
    for k, (knot, nxt) in enumerate(zip(spatial.knots, spatial.knots[1:], strict=False)):
        dt = nxt.time_s - knot.time_s
        current_radius, current_steel_radius = _radius_from_inventory(stage, spatial.geometry,
            phase_volumes, cumulative_wall, phase_inventory)
        fixed_outer_radius = current_radius + knot.solution_film_thickness_m
        if previous_edges is not None:
            next_edges = _edges(current_radius, knot.solution_film_thickness_m, nr)
            previous_profiles = profiles
            sweep = {}
            boundary_rows = {row.species_id: row for row in knot.species_boundaries}
            for sid in sids:
                profiles[sid], sweep[sid] = _remap_species(previous_edges, next_edges, previous_profiles[sid],
                    previous_profiles[sid][0], boundary_rows[sid].bulk_concentration_mol_m3)
            edges = next_edges
        else:
            edges = _edges(current_radius, knot.solution_film_thickness_m, nr)
            sweep = {sid: {"added_inner_mol_m": 0.0, "added_outer_mol_m": 0.0,
                "removed_inner_mol_m": 0.0, "removed_outer_mol_m": 0.0} for sid in sids}
        volumes = _cell_volumes_per_axial_metre(edges)
        centers = [math.sqrt(edges[j] * edges[j + 1]) for j in range(nr)]
        boundaries = {row.species_id: row for row in knot.species_boundaries}
        reactions = knot.reactions
        nre = len(reactions)
        csize = nr * nsp
        off_outer = csize
        off_bv = off_outer + nsp
        off_scale = off_bv + nsp
        off_wall = off_scale + nsp
        off_extent = off_wall + ne
        off_charge = off_extent + nre
        off_phase = off_charge + 1
        phase_offsets = [off_phase + p for p in range(len(phases))]
        detachment_offsets = ([off_phase + len(phases) + p for p in range(len(phases))]
            if shear_removal is not None else [])
        off_gas = off_phase + len(phases) + (len(phases) if shear_removal is not None else 0)
        off_gas_transfer = off_gas + 1
        amount_start = {sid: [c * v for c, v in zip(profiles[sid], volumes, strict=True)] for sid in sids}
        start_moles = {sid: math.fsum(amount_start[sid]) for sid in sids}
        y0 = [amount_start[sid][j] for sid in sids for j in range(nr)]
        y0 += [0.0] * (3 * nsp + ne + nre + 1)
        y0 += [phase_inventory[p.phase_id] for p in phases]
        if shear_removal is not None:
            y0 += [0.0] * len(phases)
        y0 += [gas_fugacity, 0.0]
        atol = [spatial.inventory_absolute_tolerance_mol_m] * csize
        atol += [spatial.inventory_absolute_tolerance_mol_m] * (3 * nsp + ne + nre + 1 + len(phases) +
            (len(phases) if shear_removal is not None else 0)) + [1e-12, 1e-12]
        evals, solves, max_ma_residual = [0], [0], [0.0]
        activity_guess = {row.species_id: row.initial_activity for row in ma.species}
        stage_geometry_first, stage_geometry_last = [None], [None]
        stage_mass_action_first, stage_mass_action_last = [None], [None]
        stage_radius_min, stage_radius_max = [math.inf], [0.0]
        stage_radius_samples = []

        def rhs(time_s, y):
            evals[0] += 1
            if evals[0] > rhs_budget:
                raise ArithmeticError("bounded dynamic-geometry BDF stage budget exceeded")
            local_phase = {p.phase_id: float(y[phase_offsets[j]]) for j, p in enumerate(phases)}
            local_wall = {e.element_id: cumulative_wall[e.element_id] + float(y[off_wall + j])
                for j, e in enumerate(spatial.wall_elements)}
            radius, steel_radius = _radius_from_inventory(stage, spatial.geometry, phase_volumes, local_wall, local_phase)
            outer_radius = fixed_outer_radius
            if outer_radius <= radius:
                raise ArithmeticError("moving bore reached the fixed outer boundary of the liquid film")
            film = outer_radius - radius
            local_edges = _edges(radius, film, nr)
            local_volumes = _cell_volumes_per_axial_metre(local_edges)
            local_centers = [math.sqrt(local_edges[j] * local_edges[j + 1]) for j in range(nr)]
            amounts = [list(y[p * nr:(p + 1) * nr]) for p in range(nsp)]
            if any(not math.isfinite(v) or v < -spatial.inventory_absolute_tolerance_mol_m for row in amounts for v in row):
                raise ArithmeticError("moving-grid cell inventory became negative or nonfinite")
            cs = [[max(0.0, amounts[p][j]) / local_volumes[j] for j in range(nr)] for p in range(nsp)]
            if not math.isfinite(y[off_gas]) or y[off_gas] < -1e-12:
                raise ArithmeticError("finite-gas fugacity became negative or nonfinite")
            potential, bv_rows, _ = _transport_fluxes(cs, boundaries, local_edges, radius, reactions,
                spatial.potential_absolute_tolerance_V, spatial.maximum_bisection_iterations)
            wall_comp = {sid: cs[sidx[sid]][0] for sid in sids}
            solves[0] += 1
            activities, ma_diag = _solve_stage_mass_action(ma, wall_comp, activity_guess, ma_sha)
            activity_guess.update(activities)
            ma_residual = ma_diag.get("normalized_residual_norm")
            if not isinstance(ma_residual, (int, float)) or not math.isfinite(float(ma_residual)):
                raise ArithmeticError("dynamic-geometry stage mass-action residual is invalid")
            max_ma_residual[0] = max(max_ma_residual[0], float(ma_residual))
            if stage_mass_action_first[0] is None:
                stage_mass_action_first[0] = {"input_sha256": ma_diag.get("input_digest"),
                    "wall_composition_sha256": ma_diag.get("stage_wall_composition_sha256")}
            stage_mass_action_last[0] = {"input_sha256": ma_diag.get("input_digest"),
                "wall_composition_sha256": ma_diag.get("stage_wall_composition_sha256")}
            if stage_geometry_first[0] is None:
                stage_geometry_first[0] = {"time_s": time_s, "bore_radius_m": radius, "steel_inner_radius_m": steel_radius,
                    "radius_stage_sha256": canonical_digest({"time_s": time_s, "bore_radius_m": radius,
                        "steel_inner_radius_m": steel_radius, "phase_inventory_mol_m_by_phase": local_phase,
                        "cumulative_wall_release_mol_m_by_element": local_wall})}
            stage_geometry_last[0] = {"time_s": time_s, "bore_radius_m": radius, "steel_inner_radius_m": steel_radius,
                "radius_stage_sha256": canonical_digest({"time_s": time_s, "bore_radius_m": radius,
                    "steel_inner_radius_m": steel_radius, "phase_inventory_mol_m_by_phase": local_phase,
                    "cumulative_wall_release_mol_m_by_element": local_wall})}
            stage_radius_min[0] = min(stage_radius_min[0], radius)
            stage_radius_max[0] = max(stage_radius_max[0], radius)
            if len(stage_radius_samples) < 128:
                stage_radius_samples.append(stage_geometry_last[0])
            phase_offsets_local = phase_offsets
            phase_rates, _ = _stage_fluxes(stage, phases, k, time_s, y, nr, sids, boundaries, local_edges,
                radius, nxt.time_s, dt, phase_offsets_local, activities)
            chemical_phase_rates = list(phase_rates)
            net_phase_rates = list(phase_rates)
            actual_detachment_fluxes = [0.0] * len(phases)
            if shear_removal is not None:
                shear_stress = shear_removal.shear_history[k].wall_shear_stress_Pa
                laws = {law.phase_id: law for law in shear_removal.phase_laws}
                remaining = max(nxt.time_s - time_s, dt * 1e-12)
                for j, phase in enumerate(phases):
                    law = laws[phase.phase_id]
                    excess = max(0.0, shear_stress / law.critical_shear_stress_Pa - 1.0)
                    try:
                        velocity = law.detachment_velocity_scale_m_s * excess ** law.stress_exponent
                    except OverflowError as exc:
                        raise ArithmeticError("finite-gas stage shear-detachment velocity overflowed") from exc
                    if not math.isfinite(velocity):
                        raise ArithmeticError("finite-gas stage shear-detachment velocity is nonfinite")
                    requested = velocity / phase_volumes[phase.phase_id]
                    if not math.isfinite(requested):
                        raise ArithmeticError("finite-gas stage shear-detachment flux is nonfinite")
                    available = max(0.0, float(y[phase_offsets[j]]))
                    maximum_inventory_rate = available / (2.0 * math.pi * radius * remaining)
                    if chemical_phase_rates[j] < 0.0:
                        maximum_inventory_rate = max(0.0, maximum_inventory_rate + chemical_phase_rates[j])
                    actual = min(requested, maximum_inventory_rate)
                    actual_detachment_fluxes[j] = actual
                    net_phase_rates[j] -= actual
            bv_species = {sid: 0.0 for sid in sids}
            extent_rate = {row.reaction_id: 0.0 for row in reactions}
            wall_rate = {e.element_id: 0.0 for e in spatial.wall_elements}
            area = 2.0 * math.pi * radius
            for reaction in reactions:
                extent = bv_rows[reaction.reaction_id]["extent_mol_m2_s"]
                extent_rate[reaction.reaction_id] = extent * area
                for sid, coefficient in reaction.stoichiometric_species_coefficients.items():
                    bv_species[sid] += coefficient * extent * area
                for element in wall_rate:
                    gain = math.fsum(coefficient * species[sidx[sid]].elemental_composition.get(element, 0.0)
                        for sid, coefficient in reaction.stoichiometric_species_coefficients.items())
                    if gain > 0.0:
                        wall_rate[element] += gain * extent * area
            scale_species = {sid: 0.0 for sid in sids}
            for j, phase in enumerate(phases):
                for sid, coefficient in phase.species_moles_per_mole_solid.items():
                    scale_species[sid] -= coefficient * chemical_phase_rates[j] * area
            gas_i = sidx[stage.gas_transfer_species_id]
            gas_raw = gas_area * transfer_k * (henry * max(0.0, float(y[off_gas])) - cs[gas_i][-1])
            remainder = max(nxt.time_s - time_s, dt * 1e-12)
            gas_supply = gas_capacity * max(0.0, float(y[off_gas])) / remainder
            liquid_supply = max(0.0, cs[gas_i][-1]) * local_volumes[-1] / remainder
            gas_flow = min(gas_supply, max(-liquid_supply, gas_raw))
            dy = [0.0] * len(y)
            outer = {sid: 0.0 for sid in sids}
            for pos, sid in enumerate(sids):
                c, d, balance = cs[pos], boundaries[sid].radial_cell_diffusivity_m2_s, [0.0] * nr
                for f in range(1, nr):
                    resistance = math.log(local_edges[f] / local_centers[f - 1]) / d[f - 1] + math.log(local_centers[f] / local_edges[f]) / d[f]
                    flow = 2.0 * math.pi / resistance * (c[f - 1] - c[f])
                    balance[f - 1] -= flow
                    balance[f] += flow
                resistance = math.log(local_edges[-1] / local_centers[-1]) / d[-1]
                boundary_flow = 0.0 if sid == stage.gas_transfer_species_id else 2.0 * math.pi / resistance * (
                    boundaries[sid].bulk_concentration_mol_m3 - c[-1])
                outer[sid] = boundary_flow
                if sid == stage.gas_transfer_species_id:
                    balance[-1] += gas_flow
                else:
                    balance[-1] += boundary_flow
                balance[0] += bv_species[sid] + scale_species[sid]
                for j in range(nr):
                    dy[pos * nr + j] = balance[j]
                dy[off_outer + pos] = boundary_flow
                dy[off_bv + pos] = bv_species[sid]
                dy[off_scale + pos] = scale_species[sid]
            for j, element in enumerate(wall_rate):
                dy[off_wall + j] = wall_rate[element]
            for j, reaction in enumerate(reactions):
                dy[off_extent + j] = extent_rate[reaction.reaction_id]
            dy[off_charge] = -FARADAY_C_MOL * math.fsum(reaction.electron_count *
                bv_rows[reaction.reaction_id]["extent_mol_m2_s"] * area for reaction in reactions)
            for j in range(len(phases)):
                dy[phase_offsets[j]] = net_phase_rates[j] * area
                if shear_removal is not None:
                    dy[detachment_offsets[j]] = actual_detachment_fluxes[j] * area
            dy[off_gas] = -gas_flow / gas_capacity
            dy[off_gas_transfer] = gas_flow
            return dy

        try:
            sol = solve_ivp(rhs, (knot.time_s, nxt.time_s), y0, method="BDF", t_eval=[nxt.time_s],
                rtol=spatial.relative_tolerance, atol=atol, max_step=min(spatial.maximum_step_s, dt))
        except (ArithmeticError, ValueError, RuntimeError, OverflowError) as exc:
            return {"failure": {"failed_interval_index": k, "detail": str(exc), "rhs_evaluations": evals[0],
                "rhs_evaluation_budget": rhs_budget, "completed_intervals": intervals}, "history": history, "intervals": intervals}
        if not sol.success or sol.y.shape[1] != 1 or sol.t[-1] != nxt.time_s:
            return {"failure": {"failed_interval_index": k, "detail": str(sol.message),
                "completed_intervals": intervals}, "history": history, "intervals": intervals}
        y = [float(v) for v in sol.y[:, -1]]
        phase_start = dict(phase_inventory)
        phase_end = {p.phase_id: y[phase_offsets[j]] for j, p in enumerate(phases)}
        detached_interval = ({p.phase_id: float(y[detachment_offsets[j]]) for j, p in enumerate(phases)}
            if shear_removal is not None else {p.phase_id: 0.0 for p in phases})
        if any(not math.isfinite(value) or value < -spatial.inventory_absolute_tolerance_mol_m
               for value in detached_interval.values()):
            return {"failure": {"failed_interval_index": k, "reason": "invalid_detached_solid_export_inventory",
                "detached_mol_m_by_phase": detached_interval, "completed_intervals": intervals},
                "history": history, "intervals": intervals}
        detached_interval = {phase_id: max(0.0, value) for phase_id, value in detached_interval.items()}
        interval_wall = {e.element_id: y[off_wall + j] for j, e in enumerate(spatial.wall_elements)}
        local_wall = {e.element_id: cumulative_wall[e.element_id] + interval_wall[e.element_id]
            for e in spatial.wall_elements}
        try:
            radius_end, steel_end = _radius_from_inventory(stage, spatial.geometry, phase_volumes, local_wall, phase_end)
        except ArithmeticError as exc:
            return {"failure": {"failed_interval_index": k, "reason": "same_stage_geometry_failed_at_endpoint",
                "detail": str(exc), "completed_intervals": intervals}, "history": history, "intervals": intervals}
        film_end = fixed_outer_radius - radius_end
        if film_end <= 0.0:
            return {"failure": {"failed_interval_index": k, "reason": "bore_reached_liquid_outer_boundary",
                "completed_intervals": intervals}, "history": history, "intervals": intervals}
        end_edges = _edges(radius_end, film_end, nr)
        end_volumes = _cell_volumes_per_axial_metre(end_edges)
        end_amounts = {sid: list(y[pos * nr:(pos + 1) * nr]) for pos, sid in enumerate(sids)}
        if any(v < -spatial.inventory_absolute_tolerance_mol_m or not math.isfinite(v)
                for row in end_amounts.values() for v in row):
            return {"failure": {"failed_interval_index": k, "reason": "negative_or_nonfinite_dynamic_cell_inventory",
                "completed_intervals": intervals}, "history": history, "intervals": intervals}
        end_profiles = {sid: [max(0.0, amount) / volume for amount, volume in zip(end_amounts[sid], end_volumes, strict=True)]
            for sid in sids}
        outer = {sid: y[off_outer + j] for j, sid in enumerate(sids)}
        bv = {sid: y[off_bv + j] for j, sid in enumerate(sids)}
        scale = {sid: y[off_scale + j] for j, sid in enumerate(sids)}
        gas_transfer = y[off_gas_transfer]
        gas_end = y[off_gas]
        gas_change = gas_capacity * (gas_end - gas_fugacity)
        gas_closure = gas_change + gas_transfer
        end_moles = {sid: math.fsum(end_amounts[sid]) for sid in sids}
        species_residual = {sid: end_moles[sid] - start_moles[sid] - outer[sid] - bv[sid] - scale[sid]
            - (gas_transfer if sid == stage.gas_transfer_species_id else 0.0) for sid in sids}
        if any(abs(v) > spatial.inventory_absolute_tolerance_mol_m + spatial.inventory_relative_tolerance *
                max(abs(end_moles[sid]), 1e-30) for sid, v in species_residual.items()):
            return {"failure": {"failed_interval_index": k, "reason": "dynamic_species_inventory_closure_failed",
                "residual_mol_m_by_species": species_residual, "completed_intervals": intervals},
                "history": history, "intervals": intervals}
        charge_residual = math.fsum(species[sidx[sid]].charge_number * value for sid, value in species_residual.items())
        electronic = FARADAY_C_MOL * math.fsum(species[sidx[sid]].charge_number * bv[sid] for sid in sids) + y[off_charge]
        elements = sorted({element for row in species for element in row.elemental_composition})
        element_residual = {e: math.fsum(species[sidx[sid]].elemental_composition.get(e, 0.0) * species_residual[sid]
            for sid in sids) for e in elements}
        if abs(electronic) > spatial.charge_absolute_tolerance_C_m + spatial.inventory_relative_tolerance * max(abs(y[off_charge]), 1e-30):
            return {"failure": {"failed_interval_index": k, "reason": "bv_electronic_charge_closure_failed",
                "residual_C_m": electronic, "completed_intervals": intervals}, "history": history, "intervals": intervals}
        if abs(charge_residual) > spatial.charge_absolute_tolerance_C_m / FARADAY_C_MOL + spatial.inventory_relative_tolerance * max(
                math.fsum(abs(species[sidx[sid]].charge_number * end_moles[sid]) for sid in sids), 1e-30):
            return {"failure": {"failed_interval_index": k, "reason": "aqueous_charge_inventory_closure_failed",
                "residual_mol_charge_m": charge_residual, "completed_intervals": intervals}, "history": history, "intervals": intervals}
        solid_delta = {e: math.fsum((phase_end[p.phase_id] - phase_start[p.phase_id]) * p.phase_element_composition.get(e, 0.0)
            for p in phases) for e in sorted(set(elements) | set().union(*(set(p.phase_element_composition) for p in phases)))}
        scale_element = {e: math.fsum(species[sidx[sid]].elemental_composition.get(e, 0.0) * scale[sid] for sid in sids)
            for e in sorted(set(elements) | set(solid_delta))}
        detached_element_export = {e: math.fsum(detached_interval[p.phase_id] * p.phase_element_composition.get(e, 0.0)
            for p in phases) for e in sorted(set(elements) | set(solid_delta))}
        scale_residual = {e: scale_element.get(e, 0.0) + solid_delta.get(e, 0.0) + detached_element_export.get(e, 0.0)
            for e in sorted(set(scale_element) | set(solid_delta) | set(detached_element_export))}
        if any(abs(v) > spatial.inventory_absolute_tolerance_mol_m + spatial.inventory_relative_tolerance *
                max(abs(scale_element.get(e, 0.0)), abs(solid_delta.get(e, 0.0)),
                    abs(detached_element_export.get(e, 0.0)), 1e-30) for e, v in scale_residual.items()):
            return {"failure": {"failed_interval_index": k, "reason": "scale_aqueous_solid_element_closure_failed",
                "residual_mol_m_by_element": scale_residual, "completed_intervals": intervals}, "history": history, "intervals": intervals}
        transfer_species = species[sidx[stage.gas_transfer_species_id]]
        global_elements = sorted(set(elements) | set(solid_delta) | set(detached_element_export) |
            set(transfer_species.elemental_composition) | set(local_wall))
        gas_delta_elements = {e: transfer_species.elemental_composition.get(e, 0) * gas_change for e in global_elements}
        external_elements = {e: math.fsum(species[sidx[sid]].elemental_composition.get(e, 0.0) * outer[sid] for sid in sids)
            for e in global_elements}
        wall_elements = {e: interval_wall.get(e, 0.0) for e in global_elements}
        global_delta = {e: (math.fsum(species[sidx[sid]].elemental_composition.get(e, 0.0) * (end_moles[sid] - start_moles[sid])
                for sid in sids) + solid_delta.get(e, 0.0) + detached_element_export.get(e, 0.0) +
                gas_delta_elements.get(e, 0.0)) for e in global_elements}
        global_residual = {e: global_delta[e] - external_elements[e] - wall_elements[e] for e in global_elements}
        if abs(gas_closure) > spatial.inventory_absolute_tolerance_mol_m + spatial.inventory_relative_tolerance * max(abs(gas_transfer), abs(gas_change), 1e-30):
            return {"failure": {"failed_interval_index": k, "reason": "finite_gas_inventory_closure_failed",
                "residual_mol_m": gas_closure, "completed_intervals": intervals}, "history": history, "intervals": intervals}
        if any(abs(v) > spatial.inventory_absolute_tolerance_mol_m + spatial.inventory_relative_tolerance *
                max(abs(global_delta[e]), abs(external_elements[e]), abs(wall_elements[e]), 1e-30)
                for e, v in global_residual.items()):
            return {"failure": {"failed_interval_index": k, "reason": "same_stage_global_element_closure_failed",
                "residual_mol_m_by_element": global_residual, "completed_intervals": intervals},
                "history": history, "intervals": intervals}
        if any(phase_end[p.phase_id] < -spatial.inventory_absolute_tolerance_mol_m for p in phases):
            return {"failure": {"failed_interval_index": k, "reason": "scale_inventory_depleted",
                "completed_intervals": intervals}, "history": history, "intervals": intervals}
        geometry_row = {"time_s": nxt.time_s, "bore_radius_m": radius_end, "steel_inner_radius_m": steel_end,
            "wall_recession_m": steel_end - spatial.geometry.initial_inner_radius_m,
            "phase_inventory_mol_m_by_phase": phase_end,
            "cumulative_wall_release_mol_m_by_element": local_wall,
            "stage_radius_range_m": [stage_radius_min[0], stage_radius_max[0]],
            "stage_geometry_samples": stage_radius_samples,
            "stage_geometry_sample_sha256": canonical_digest(stage_radius_samples)}
        interval = {"interval_index": k, "start_time_s": knot.time_s, "end_time_s": nxt.time_s,
            "rhs_evaluations": evals[0], "rhs_evaluation_budget": rhs_budget,
            "mass_action_stage_solves": solves[0], "maximum_mass_action_residual": max_ma_residual[0],
            "first_stage_mass_action_digest": stage_mass_action_first[0],
            "last_stage_mass_action_digest": stage_mass_action_last[0],
            "geometry_recomputed_from_live_wall_and_scale_states_at_every_rhs": True,
            "first_stage_geometry": stage_geometry_first[0], "last_stage_geometry": stage_geometry_last[0],
            "endpoint_geometry": geometry_row,
            "gas_fugacity_start_Pa": gas_fugacity, "gas_fugacity_end_Pa": gas_end,
            "gas_transfer_mol_m": gas_transfer, "gas_inventory_closure_residual_mol_m": gas_closure,
            "species_inventory_residual_mol_m_by_species": species_residual,
            "charge_residual_mol_charge_m": charge_residual, "element_residual_mol_m_by_element": element_residual,
            "scale_element_closure_residual_mol_m_by_element": scale_residual,
            **({"detached_solid_inventory_export_mol_m_by_phase": detached_interval,
                "detached_solid_element_export_mol_m_by_element": detached_element_export,
                "wall_shear_stress_Pa": shear_removal.shear_history[k].wall_shear_stress_Pa}
                if shear_removal is not None else {}),
            "global_element_residual_mol_m_by_element": global_residual,
            "aqueous_outer_exchange_mol_m_by_species": outer, "aqueous_bv_transfer_mol_m_by_species": bv,
            "aqueous_scale_transfer_mol_m_by_species": scale,
            "solid_inventory_start_mol_m_by_phase": phase_start, "solid_inventory_end_mol_m_by_phase": phase_end,
            "wall_release_mol_m_by_element": interval_wall,
            "moving_mesh_remap_exchange_mol_m_by_species": sweep,
            "bv_electronic_charge_residual_C_m": electronic}
        intervals.append(interval)
        for phase_id, value in detached_interval.items():
            cumulative_detached[phase_id] += value
        phase_inventory = {p.phase_id: max(0.0, phase_end[p.phase_id]) for p in phases}
        cumulative_wall = local_wall
        gas_fugacity = gas_end
        cumulative_gas_transfer += gas_transfer
        profiles = end_profiles
        previous_edges = end_edges
        history.append({"time_s": nxt.time_s, "geometry": geometry_row,
            "species_profile_mol_m3_by_species": profiles,
            "aqueous_inventory_mol_m_by_species": end_moles,
            "phase_inventory_mol_m_by_phase": phase_inventory,
            "gas_co2_fugacity_Pa": gas_fugacity,
            "gas_inventory_mol_m": gas_capacity * gas_fugacity,
            "cumulative_gas_to_liquid_transfer_mol_m": cumulative_gas_transfer,
            "cumulative_wall_release_mol_m_by_element": cumulative_wall})
        if shear_removal is not None:
            history[-1]["cumulative_detached_solid_inventory_export_mol_m_by_phase"] = dict(cumulative_detached)
    return {"failure": None, "intervals": intervals, "history": history,
        "final_phase_inventory_mol_m_by_phase": phase_inventory,
        "cumulative_wall_release_mol_m_by_element": cumulative_wall,
        "final_gas_fugacity_Pa": gas_fugacity, "cumulative_gas_transfer_mol_m": cumulative_gas_transfer,
        "cumulative_detached_solid_inventory_export_mol_m_by_phase": cumulative_detached}


def evaluate_wet_co2_cylindrical_finite_gas_stage_geometry_feedback(
    request: WetCo2CylindricalFiniteGasStageGeometryFeedback,
) -> Calculation:
    stage = request.finite_gas_stage_request
    spatial = stage.spatial_request
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {"assessment_id": request.assessment_id, "model_id": MODEL_ID, "input_sha256": input_digest,
        "finite_gas_stage_input_sha256": canonical_digest(stage.model_dump(mode="json")),
        "spatial_input_sha256": canonical_digest(spatial.model_dump(mode="json")),
        "source_ids": [KINETICS_SOURCE_ID, SUPPLY_SOURCE_ID, SPECIATION_SOURCE_ID, GAS_TRANSFER_SOURCE_ID,
            GAS_COUPLING_SOURCE_ID, GAS_INITIAL_SOURCE_ID, GAS_CAP_SOURCE_ID, MOVING_GEOMETRY_SOURCE_ID, ALE_MESH_SOURCE_ID]
            + ([SHEAR_HISTORY_SOURCE_ID, SHEAR_LAW_SOURCE_ID] if request.shear_removal is not None else [])}
    missing = [name for name in ("mass_action_network_and_standard_state_reviewed",
        "phase_identity_and_balanced_reaction_reviewed", "cylindrical_supply_map_reviewed",
        "exact_knot_left_hold_and_geometry_reviewed", "no_qualification_claim_reviewed",
        "computational_use_authorized", "finite_gas_and_fixed_transfer_scope_reviewed") if not getattr(stage, name)]
    missing.extend(f"phase:{phase.phase_id}:chemistry_and_rate_law_reviewed" for phase in stage.phases
        if not phase.chemistry_and_rate_law_reviewed)
    if missing:
        return Calculation(status="needs_data", values=base | {"reason": "review_gates_incomplete", "missing_reviews": missing})
    geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(spatial.geometry)
    if geometry.status != "computed":
        return Calculation(status=geometry.status, values=base | {"reason": "initial_geometry_not_computed"})
    initial_bore = float(geometry.values["history"][0]["bore_radius_m"])
    nint = len(spatial.knots) - 1
    nr = len(spatial.initial_species[0].cell_concentrations_mol_m3)
    nsp = len(spatial.species)
    nre = max(len(k.reactions) for k in spatial.knots)
    state_count = (nr * nsp + 3 * nsp + len(spatial.wall_elements) + nre + len(stage.phases) +
        (len(stage.phases) if request.shear_removal is not None else 0) + 3)
    ma = stage.mass_action_system_template
    ma_weight = len(ma.species) * (ma.maximum_iterations + 1) * 33 + 3 * len(ma.species) ** 3
    rhs_budget = stage.maximum_work_units // (max(1, nint) * (state_count + ma_weight))
    if rhs_budget < 20:
        return Calculation(status="out_of_scope", values=base | {"reason": "dynamic_geometry_work_budget_below_minimum",
            "required_minimum_rhs_evaluations_per_interval": 20, "computed_rhs_budget": rhs_budget})
    result = _run_dynamic_intervals(request, geometry, initial_bore, rhs_budget, request.shear_removal)
    if result["failure"]:
        return Calculation(status="out_of_scope", values=base | {"reason": "dynamic_geometry_interval_failed",
            "failure_prefix": result["failure"], "completed_interval_count": len(result["intervals"])})
    values = base | {"status": "computed", "geometry_history": [geometry.values["history"][0]] +
        [row["geometry"] for row in result["history"]],
        "geometry_history_sha256": canonical_digest([geometry.values["history"][0]] + [row["geometry"] for row in result["history"]]),
        "history": result["history"], "interval_ledger": result["intervals"],
        "final_phase_inventory_mol_m_by_phase": result["final_phase_inventory_mol_m_by_phase"],
        "final_wall_release_mol_m_by_element": result["cumulative_wall_release_mol_m_by_element"],
        "final_gas_co2_fugacity_Pa": result["final_gas_fugacity_Pa"],
        "cumulative_gas_to_liquid_transfer_mol_m": result["cumulative_gas_transfer_mol_m"],
        "initial_geometry_result_sha256": canonical_digest(geometry.model_dump(mode="json")),
        "geometry_mode": "radius and steel inner surface are recomputed algebraically from the live BDF wall-release and scale-phase inventories at each RHS; species state uses conservative cell molar inventories on a moving Lagrangian radial mesh",
        "model_scope": "caller-owned gas transfer, aqueous mass-action, BV and scale laws; no hydraulic radial velocity or moving bulk control-volume law is inferred"}
    if request.shear_removal is not None:
        values["cumulative_detached_solid_inventory_export_mol_m_by_phase"] = result[
            "cumulative_detached_solid_inventory_export_mol_m_by_phase"]
        values["shear_removal_lineage"] = {
            "shear_record_sha256_by_knot": [row.record_sha256 for row in request.shear_removal.shear_history],
            "shear_evidence_source_ids": sorted({row.source_id for knot in request.shear_removal.shear_history
                for row in knot.evidence}),
            "phase_laws": [{"phase_id": law.phase_id, "record_sha256": law.record_sha256,
                "evidence_source_ids": [row.source_id for row in law.evidence]}
                for law in request.shear_removal.phase_laws],
        }
    return Calculation(values=values)


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalFiniteGasStageGeometryFeedback,
        evaluator=evaluate_wet_co2_cylindrical_finite_gas_stage_geometry_feedback,
        units={"geometry_history[].bore_radius_m": "m", "geometry_history[].steel_inner_radius_m": "m",
            "history[].gas_inventory_mol_m": "mol/m", "interval_ledger[].gas_transfer_mol_m": "mol/m",
            "interval_ledger[].species_inventory_residual_mol_m_by_species.*": "mol/m",
            "interval_ledger[].detached_solid_inventory_export_mol_m_by_phase.*": "mol/m",
            "interval_ledger[].detached_solid_element_export_mol_m_by_element.*": "mol/m",
            "interval_ledger[].wall_shear_stress_Pa": "Pa",
            "shear_removal.shear_history[].time_s": "s",
            "shear_removal.shear_history[].wall_shear_stress_Pa": "Pa",
            "shear_removal.phase_laws[].critical_shear_stress_Pa": "Pa",
            "shear_removal.phase_laws[].detachment_velocity_scale_m_s": "m/s"},
        assumptions=("Caller transfer, mass-action, BV and scale laws remain fixed/evidence-bound.",
            "The cylindrical radius is recalculated from live wall release and phase inventory at each BDF evaluation.",
            "A Lagrangian radial mesh conserves cell molar inventories as bore geometry changes; caller must review this mesh-motion assumption.",
            "Schema v2 is opt-in and requires an exact-knot caller shear law; detached solids are exported, excluded from aqueous source terms, and included in scale/global element closure.",
            "The gas, aqueous, scale and wall source ledgers close by element; this does not establish empirical validity."),
        source_ids=(KINETICS_SOURCE_ID, SUPPLY_SOURCE_ID, SPECIATION_SOURCE_ID, GAS_TRANSFER_SOURCE_ID,
            GAS_COUPLING_SOURCE_ID, GAS_INITIAL_SOURCE_ID, GAS_CAP_SOURCE_ID, MOVING_GEOMETRY_SOURCE_ID, ALE_MESH_SOURCE_ID,
            SHEAR_HISTORY_SOURCE_ID, SHEAR_LAW_SOURCE_ID),
        qualification="user_model",
    ),)
