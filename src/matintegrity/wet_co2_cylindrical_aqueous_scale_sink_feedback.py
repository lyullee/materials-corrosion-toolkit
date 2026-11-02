"""Bounded exact-knot BV transport with caller-owned scale reaction sinks."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)
from .wet_co2_cylindrical_spatial_mixed_potential import (
    WetCo2CylindricalSpatialMixedPotential,
    _transport_fluxes,
)
from .wet_co2_cylindrical_transient_transport import (
    FARADAY_C_MOL,
    _cell_volumes_per_axial_metre,
    _edges,
    _remap_species,
)

MODEL_ID = "integration.wet_co2_cylindrical_aqueous_scale_sink_feedback"
SOURCE_ID = "bounded_bv_transport_with_caller_scale_reaction_interval_sources"
DIFFUSION_SOURCE_ID = "cylindrical_radial_supply_cap_for_scale_reactants"


class WetCo2ScaleReactionKnot(Contract):
    """Caller-specified intrinsic precipitation rate at an exact time knot."""

    time_s: Nonnegative
    intrinsic_precipitation_flux_mol_m2_s: float
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_rate(self):
        if not math.isfinite(self.intrinsic_precipitation_flux_mol_m2_s):
            raise ValueError("caller precipitation flux must be finite")
        payload = {"time_s": self.time_s,
                   "intrinsic_precipitation_flux_mol_m2_s": self.intrinsic_precipitation_flux_mol_m2_s}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("flux digest must bind exact knot time and intrinsic signed flux")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each caller flux record")
        return self


class WetCo2AqueousScalePhase(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    species_moles_per_mole_solid: dict[str, float]
    phase_element_composition: dict[str, Positive]
    flux_history: tuple[WetCo2ScaleReactionKnot, ...] = Field(min_length=2, max_length=2000)
    stoichiometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stoichiometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    identity_and_direction_reviewed: bool

    @model_validator(mode="after")
    def verify_stoichiometry(self):
        if not self.species_moles_per_mole_solid or any(not math.isfinite(v) or v == 0.0
                for v in self.species_moles_per_mole_solid.values()):
            raise ValueError("phase reaction must declare finite nonzero signed aqueous stoichiometric coefficients")
        payload = {"phase_id": self.phase_id,
                   "species_moles_per_mole_solid": self.species_moles_per_mole_solid,
                   "phase_element_composition": self.phase_element_composition}
        if canonical_digest(payload) != self.stoichiometry_sha256:
            raise ValueError("stoichiometry digest must bind phase, aqueous coefficients and solid formula")
        if not any(row.sha256 == self.stoichiometry_sha256 and row.license_id
                   for row in self.stoichiometry_evidence):
            raise ValueError("licensed Evidence must pin the caller phase stoichiometry")
        if any(not math.isfinite(row.intrinsic_precipitation_flux_mol_m2_s)
               for row in self.flux_history):
            raise ValueError("all phase fluxes must be finite")
        return self


class WetCo2CylindricalAqueousScaleSinkFeedback(Contract):
    """Iterate moving geometry and exact-knot BV transport with scale sinks in its RHS."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_aqueous_scale_sink_feedback.v1"] = (
        "matintegrity.wet_co2_cylindrical_aqueous_scale_sink_feedback.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_request: WetCo2CylindricalSpatialMixedPotential
    phases: tuple[WetCo2AqueousScalePhase, ...] = Field(min_length=1, max_length=32)
    maximum_feedback_iterations: int = Field(default=20, ge=1, le=60)
    relaxation_factor: float = Field(default=0.5, gt=0, le=1)
    absolute_radius_tolerance_m: Positive = Field(default=1e-9)
    relative_radius_tolerance: Positive = Field(default=1e-7, le=1e-2)
    absolute_inventory_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_inventory_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_work_units: int = Field(default=30_000_000, ge=10_000, le=300_000_000)
    caller_flux_law_reviewed: bool
    phase_formula_and_reaction_direction_reviewed: bool
    diffusion_supply_mapping_reviewed: bool
    uniform_axisymmetric_scale_and_recession_reviewed: bool
    no_inter_knot_or_qualification_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_campaign(self):
        req = self.spatial_request
        if req.geometry_trial_mode:
            raise ValueError("provide an ordinary spatial request, not a trial-mode request")
        times = tuple(row.time_s for row in req.knots)
        if times != tuple(row.time_s for row in req.geometry.history):
            raise ValueError("BV and geometry knots must match exactly")
        species = {row.species_id: row for row in req.species}
        phase_by_id = {row.phase_id: row for row in req.geometry.phases}
        if len(phase_by_id)!=len(req.geometry.phases) or len({row.phase_id for row in self.phases})!=len(self.phases) or \
                set(phase_by_id) != {row.phase_id for row in self.phases}:
            raise ValueError("phase kinetic records must cover exactly the geometry phases")
        nr = len(req.initial_species[0].cell_concentrations_mol_m3)
        reaction_count=max(len(knot.reactions) for knot in req.knots)
        estimated = self.maximum_feedback_iterations * (len(times) - 1) * nr * (
            len(species) + reaction_count + len(self.phases))
        if estimated > self.maximum_work_units:
            raise ValueError("declared feedback budget is insufficient for knot, cell and species work")
        rhs_state_count=nr*len(species)+3*len(species)+len(req.wall_elements)+reaction_count+1
        rhs_budget=self.maximum_work_units//(self.maximum_feedback_iterations*(len(times)-1)*rhs_state_count)
        if rhs_budget<20:
            raise ValueError("declared work budget leaves fewer than 20 RHS evaluations per interval")
        for phase in self.phases:
            if tuple(row.time_s for row in phase.flux_history) != times:
                raise ValueError("phase flux records must cover every exact geometry knot")
            if set(phase.species_moles_per_mole_solid) - set(species):
                raise ValueError("phase reactants/products must be spatial aqueous species")
            element_delta: dict[str, float] = {}
            charge_delta = 0.0
            for sid, coefficient in phase.species_moles_per_mole_solid.items():
                sp = species[sid]
                charge_delta += coefficient * sp.charge_number
                for element, amount in sp.elemental_composition.items():
                    element_delta[element] = element_delta.get(element, 0.0) + coefficient * amount
            if not math.isclose(charge_delta, 0.0, rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("neutral scale phase reaction must conserve aqueous charge")
            elements = set(element_delta) | set(phase.phase_element_composition)
            if any(not math.isclose(element_delta.get(e, 0.0), phase.phase_element_composition.get(e, 0.0),
                                    rel_tol=1e-10, abs_tol=1e-10) for e in elements):
                raise ValueError("aqueous reaction formula must exactly match the caller solid formula")
        return self


def _run_bv_with_sinks(request, phase_rows, rates_by_interval, geometry_states, rhs_budget_per_interval):
    """Integrate interval RHS; caller scale terms are explicit cell-wall source/sink terms."""
    from scipy.integrate import solve_ivp
    species = list(request.species); sids = [x.species_id for x in species]
    sidx = {sid: i for i, sid in enumerate(sids)}; nr = len(request.initial_species[0].cell_concentrations_mol_m3)
    profiles = {x.species_id: list(x.cell_concentrations_mol_m3) for x in request.initial_species}
    intervals = []; history = []; failed = None
    cumulative_metal = {row.element_id: 0.0 for row in request.wall_elements}
    initial_phase_inventory={row.phase_id:row.moles_per_axial_metre_mol_m for row in request.geometry.history[0].phase_inventories}
    scale_inventory = {row.phase_id: initial_phase_inventory[row.phase_id] for row in phase_rows}
    for k, (knot, nxt) in enumerate(zip(request.knots, request.knots[1:], strict=False)):
        dt = nxt.time_s - knot.time_s; radius = float(geometry_states[k]["bore_radius_m"]); area = 2 * math.pi * radius
        edges = _edges(radius, knot.solution_film_thickness_m, nr); vols = _cell_volumes_per_axial_metre(edges)
        centers = [math.sqrt(edges[j] * edges[j + 1]) for j in range(nr)]
        boundary_rows = {row.species_id: row for row in knot.species_boundaries}
        boundaries = {sid: boundary_rows[sid] for sid in sids}
        reactions = knot.reactions; nsp = len(sids); ne = len(cumulative_metal); np = len(phase_rows)
        # concentrations, boundary exchange, BV transfer, scale transfer, wall release, BV extent, electronic charge
        csize = nsp * nr; off_outer = csize; off_bv = off_outer+nsp; off_scale = off_bv+nsp
        off_wall = off_scale+nsp; off_extent = off_wall+ne; off_charge = off_extent+len(reactions)
        start_profile={sid:list(profiles[sid]) for sid in sids}
        start_moles={sid:math.fsum(c*v for c,v in zip(start_profile[sid],vols,strict=True)) for sid in sids}
        y0 = [profiles[sid][j] for sid in sids for j in range(nr)] + [0.0]*(3*nsp+ne+len(reactions)+1)
        atol = [request.concentration_absolute_tolerance_mol_m3]*csize + [request.inventory_absolute_tolerance_mol_m]*(3*nsp+ne+len(reactions)+1)
        ext_rate_by_phase = rates_by_interval[k]
        rhs_evaluations=[0]
        def rhs(_t, y):
            rhs_evaluations[0]+=1
            if rhs_evaluations[0]>rhs_budget_per_interval:
                raise ArithmeticError("bounded RHS evaluation budget exceeded")
            cs = [list(y[p*nr:(p+1)*nr]) for p in range(nsp)]
            if any(not math.isfinite(c) or c < -request.concentration_absolute_tolerance_mol_m3 for row in cs for c in row):
                raise ArithmeticError("aqueous cell inventory became negative or nonfinite")
            potential, bv_rows, _ = _transport_fluxes(cs, boundaries, edges, radius, reactions,
                request.potential_absolute_tolerance_V, request.maximum_bisection_iterations)
            bv_species = {sid: 0.0 for sid in sids}; wall = {e: 0.0 for e in cumulative_metal}
            bv_extent = {r.reaction_id: 0.0 for r in reactions}; current = 0.0
            for r in reactions:
                row = bv_rows[r.reaction_id]; extent = row["extent_mol_m2_s"]
                bv_extent[r.reaction_id] = extent*area; current += row["current_density_A_m2"]*area
                for sid, coeff in r.stoichiometric_species_coefficients.items(): bv_species[sid] += coeff*extent*area
                for e in wall:
                    gain = math.fsum(coeff*species[sidx[sid]].elemental_composition.get(e, 0.0)
                                     for sid, coeff in r.stoichiometric_species_coefficients.items())
                    if gain > 0: wall[e] += gain*extent*area
            scale_species = {sid: 0.0 for sid in sids}
            for p, phase in enumerate(phase_rows):
                rate = ext_rate_by_phase[p]
                for sid, coeff in phase.species_moles_per_mole_solid.items():
                    # Positive rate precipitates and consumes caller stoichiometric reactants.
                    scale_species[sid] -= coeff*rate*area
            dy = [0.0]*len(y)
            for pos, sid in enumerate(sids):
                c = cs[pos]; d = boundaries[sid].radial_cell_diffusivity_m2_s; bal = [0.0]*nr
                for f in range(1, nr):
                    resistance = math.log(edges[f]/centers[f-1])/d[f-1] + math.log(centers[f]/edges[f])/d[f]
                    flux = 2*math.pi/resistance*(c[f-1]-c[f]); bal[f-1] -= flux; bal[f] += flux
                resistance = math.log(edges[-1]/centers[-1])/d[-1]
                outer_flux = 2*math.pi/resistance*(boundaries[sid].bulk_concentration_mol_m3-c[-1])
                bal[-1] += outer_flux; bal[0] += bv_species[sid]+scale_species[sid]
                for j in range(nr): dy[pos*nr+j] = bal[j]/vols[j]
                dy[off_outer+pos] = outer_flux; dy[off_bv+pos] = bv_species[sid]; dy[off_scale+pos] = scale_species[sid]
            for j,e in enumerate(cumulative_metal): dy[off_wall+j] = wall[e]
            for j,r in enumerate(reactions): dy[off_extent+j] = bv_extent[r.reaction_id]
            dy[off_charge] = -FARADAY_C_MOL*math.fsum(r.electron_count*bv_rows[r.reaction_id]["extent_mol_m2_s"]*area for r in reactions)
            return dy
        try:
            sol = solve_ivp(rhs, (knot.time_s, nxt.time_s), y0, method="BDF", t_eval=[nxt.time_s],
                rtol=request.relative_tolerance, atol=atol, max_step=min(request.maximum_step_s, dt))
        except (ArithmeticError, ValueError, OverflowError, ZeroDivisionError) as exc:
            failed = {"failed_interval_index": k, "detail": str(exc), "completed_intervals": intervals}; break
        if not sol.success or sol.y.shape[1] != 1 or sol.t[-1] != nxt.time_s:
            failed = {"failed_interval_index": k, "detail": str(sol.message), "completed_intervals": intervals}; break
        y = [float(v) for v in sol.y[:, -1]]
        for p,sid in enumerate(sids):
            vals=y[p*nr:(p+1)*nr]
            if min(vals)<-request.concentration_absolute_tolerance_mol_m3:
                failed={"failed_interval_index":k,"species_id":sid,"reason":"negative_aqueous_concentration","completed_intervals":intervals}; break
            profiles[sid]=[max(0.0,v) for v in vals]
        if failed: break
        bv = {sid:y[off_bv+p] for p,sid in enumerate(sids)}; scale = {sid:y[off_scale+p] for p,sid in enumerate(sids)}
        outer = {sid:y[off_outer+p] for p,sid in enumerate(sids)}
        inventories = {sid:math.fsum(c*v for c,v in zip(profiles[sid],vols,strict=True)) for sid in sids}
        aqueous_residual = {sid: inventories[sid]-start_moles[sid]-outer[sid]-bv[sid]-scale[sid] for sid in sids}
        charge_residual=math.fsum(species[sidx[sid]].charge_number*value for sid,value in aqueous_residual.items())
        element_residual={element:math.fsum(species[sidx[sid]].elemental_composition.get(element,0.0)*value
            for sid,value in aqueous_residual.items()) for element in sorted({e for sp in species for e in sp.elemental_composition})}
        electronic_residual=FARADAY_C_MOL*math.fsum(species[sidx[sid]].charge_number*bv[sid] for sid in sids)+y[off_charge]
        intervals.append({"interval_index":k,"start_time_s":knot.time_s,"end_time_s":nxt.time_s,
            "radius_left_m":radius,"scale_precipitation_flux_mol_m2_s_by_phase":{
                phase_rows[p].phase_id:ext_rate_by_phase[p] for p in range(np)},
            "aqueous_boundary_exchange_mol_m_by_species":outer,"bv_species_transfer_mol_m_by_species":bv,
            "scale_species_transfer_mol_m_by_species":scale,"aqueous_inventory_mol_m_by_species":inventories,
            "aqueous_species_closure_residual_mol_m_by_species":aqueous_residual,
            "aqueous_charge_closure_residual_mol_charge_m":charge_residual,
            "aqueous_element_closure_residual_mol_m_by_element":element_residual,
            "bv_electronic_charge_closure_residual_C_m":electronic_residual,
            "bv_and_scale_terms_in_same_interval_rhs":True,
            "rhs_evaluations":rhs_evaluations[0],"rhs_evaluation_budget":rhs_budget_per_interval})
        if any(abs(v)>request.inventory_absolute_tolerance_mol_m+request.inventory_relative_tolerance*max(abs(inventories[s]),1e-30)
               for s,v in aqueous_residual.items()):
            failed={"failed_interval_index":k,"reason":"aqueous_inventory_closure_failed","residual_mol_m_by_species":aqueous_residual,"completed_intervals":intervals};break
        if abs(charge_residual)>request.charge_absolute_tolerance_C_m/FARADAY_C_MOL+request.inventory_relative_tolerance*max(
                1e-30,math.fsum(abs(species[sidx[sid]].charge_number*inventories[sid]) for sid in sids)):
            failed={"failed_interval_index":k,"reason":"aqueous_charge_closure_failed","residual_mol_charge_m":charge_residual,"completed_intervals":intervals};break
        if any(abs(value)>request.inventory_absolute_tolerance_mol_m+request.inventory_relative_tolerance*max(
                1e-30,math.fsum(abs(species[sidx[sid]].elemental_composition.get(element,0.0)*inventories[sid]) for sid in sids))
                for element,value in element_residual.items()):
            failed={"failed_interval_index":k,"reason":"aqueous_element_closure_failed","residual_mol_m_by_element":element_residual,"completed_intervals":intervals};break
        if abs(electronic_residual)>request.charge_absolute_tolerance_C_m+request.inventory_relative_tolerance*max(abs(y[off_charge]),1e-30):
            failed={"failed_interval_index":k,"reason":"bv_electronic_charge_closure_failed","residual_C_m":electronic_residual,"completed_intervals":intervals};break
        for j,e in enumerate(cumulative_metal): cumulative_metal[e]+=y[off_wall+j]
        phase_inventory_before=dict(scale_inventory)
        for p,phase in enumerate(phase_rows):
            scale_inventory[phase.phase_id]+=ext_rate_by_phase[p]*area*dt
            if scale_inventory[phase.phase_id] < -request.inventory_absolute_tolerance_mol_m:
                failed={"failed_interval_index":k,"reason":"scale_inventory_depleted","phase_id":phase.phase_id,"completed_intervals":intervals};break
            scale_inventory[phase.phase_id]=max(0.0,scale_inventory[phase.phase_id])
        if failed: break
        # Geometry rezone uses conservative overlap and caller bulk fill for the next left knot.
        next_geometry=geometry_states[k+1]; next_edges=_edges(float(next_geometry["bore_radius_m"]),nxt.solution_film_thickness_m,nr)
        next_bound={row.species_id:row for row in nxt.species_boundaries}; sweep={}
        for sid in sids:
            remapped, led=_remap_species(edges,next_edges,profiles[sid],next_bound[sid].bulk_concentration_mol_m3,next_bound[sid].bulk_concentration_mol_m3)
            profiles[sid]=remapped; sweep[sid]=led
        next_volumes=_cell_volumes_per_axial_metre(next_edges)
        post_rezone_inventory={sid:math.fsum(c*v for c,v in zip(profiles[sid],next_volumes,strict=True)) for sid in sids}
        intervals[-1]["geometry_sweep_ledger_by_species"]=sweep
        intervals[-1]["geometry_sweep_net_mol_m_by_species"]={sid:(sweep[sid]["swept_in_inner_mol_m"]+sweep[sid]["swept_in_outer_mol_m"]-
            sweep[sid]["swept_out_inner_mol_m"]-sweep[sid]["swept_out_outer_mol_m"]) for sid in sids}
        intervals[-1]["post_rezone_aqueous_inventory_mol_m_by_species"]=post_rezone_inventory
        solid_element_increment={}
        for p,phase in enumerate(phase_rows):
            delta=scale_inventory[phase.phase_id]-phase_inventory_before[phase.phase_id]
            for element,coefficient in phase.phase_element_composition.items():
                solid_element_increment[element]=solid_element_increment.get(element,0.0)+delta*coefficient
        aqueous_scale_element={element:math.fsum(species[sidx[sid]].elemental_composition.get(element,0.0)*scale[sid]
            for sid in sids) for element in sorted({e for row in species for e in row.elemental_composition})}
        intervals[-1]["solid_phase_element_inventory_increment_mol_m_by_element"]=solid_element_increment
        intervals[-1]["aqueous_scale_reaction_element_transfer_mol_m_by_element"]=aqueous_scale_element
        intervals[-1]["scale_aqueous_solid_element_closure_residual_mol_m_by_element"]={element:
            aqueous_scale_element.get(element,0.0)+solid_element_increment.get(element,0.0) for element in
            sorted(set(aqueous_scale_element)|set(solid_element_increment))}
        scale_element_residual=intervals[-1]["scale_aqueous_solid_element_closure_residual_mol_m_by_element"]
        if any(abs(value)>request.inventory_absolute_tolerance_mol_m+request.relative_inventory_tolerance*
               max(abs(aqueous_scale_element.get(element,0.0)),abs(solid_element_increment.get(element,0.0)),1e-30)
               for element,value in scale_element_residual.items()):
            failed={"failed_interval_index":k,"reason":"aqueous_scale_solid_element_closure_failed",
                "residual_mol_m_by_element":scale_element_residual,"completed_intervals":intervals};break
        solid_element_inventory={}
        for phase in phase_rows:
            for element,coefficient in phase.phase_element_composition.items():
                solid_element_inventory[element]=solid_element_inventory.get(element,0.0)+scale_inventory[phase.phase_id]*coefficient
        history.append({"time_s":nxt.time_s,"species_profile_mol_m3_by_species":profiles.copy(),
                        "aqueous_inventory_mol_m_by_species":post_rezone_inventory,"scale_inventory_mol_m_by_phase":dict(scale_inventory),
                        "solid_element_inventory_mol_m_by_element":solid_element_inventory,
                        "cumulative_wall_release_mol_m_by_element":dict(cumulative_metal)})
    return {"intervals":intervals,"history":history,"failure":failed,"final_profiles":profiles,
            "scale_inventory_mol_m_by_phase":scale_inventory,"cumulative_wall_release_mol_m_by_element":cumulative_metal}


def evaluate_wet_co2_cylindrical_aqueous_scale_sink_feedback(request: WetCo2CylindricalAqueousScaleSinkFeedback) -> Calculation:
    """Run bounded geometry Picard updates; sinks/sources enter every BV interval ODE RHS."""
    req=request.spatial_request; digest=canonical_digest(request.model_dump(mode="json"))
    base={"assessment_id":request.assessment_id,"model_id":MODEL_ID,"input_sha256":digest,
          "spatial_request_sha256":canonical_digest(req.model_dump(mode="json")),"source_ids":[SOURCE_ID,DIFFUSION_SOURCE_ID]}
    missing=[name for name in ("caller_flux_law_reviewed","phase_formula_and_reaction_direction_reviewed",
        "diffusion_supply_mapping_reviewed","uniform_axisymmetric_scale_and_recession_reviewed",
        "no_inter_knot_or_qualification_claim_reviewed","computational_use_authorized") if not getattr(request,name)]
    missing.extend(f"phase:{row.phase_id}:identity_and_direction_reviewed" for row in request.phases
                   if not row.identity_and_direction_reviewed)
    missing.extend(name for name in ("axisymmetric_reaction_area_and_material_mapping_reviewed",
        "boundary_transport_and_chemistry_reviewed","element_charge_and_reaction_direction_reviewed")
        if not getattr(req,name))
    if missing:return Calculation(status="needs_data",values=base|{"reason":"review_gates_incomplete","missing_reviews":missing})
    geometry=evaluate_wet_co2_cylindrical_scale_geometry_history(req.geometry)
    if geometry.status!="computed":return Calculation(status=geometry.status,values=base|{"reason":"geometry_not_computed"})
    geom_states=geometry.values["history"]
    phases=tuple(request.phases); times=tuple(k.time_s for k in req.knots)
    # Start from a no-scale-sink predictor; subsequent passes feed the bounded sink into the BV RHS.
    rate_guess=[[0.0 for _phase in phases] for _k in range(len(times)-1)]
    nr=len(req.initial_species[0].cell_concentrations_mol_m3)
    state_count=nr*len(req.species)+3*len(req.species)+len(req.wall_elements)+max(len(k.reactions) for k in req.knots)+1
    rhs_budget=request.maximum_work_units//(request.maximum_feedback_iterations*(len(times)-1)*state_count)
    prior_radii=[float(row["bore_radius_m"]) for row in geom_states]
    iteration_rows=[]; final=None
    for iteration in range(1,request.maximum_feedback_iterations+1):
        trial=_run_bv_with_sinks(req,phases,rate_guess,geom_states,rhs_budget)
        if trial["failure"]:
            return Calculation(status="out_of_scope",values=base|{"reason":"sink_coupled_interval_failed","failure_prefix":trial["failure"],
                "completed_iterations":iteration_rows,"failed_iteration":iteration})
        # Recompute cylindrical diffusion limits from each interval's integrated endpoint state.
        targets=[]
        start_profiles={row.species_id:list(row.cell_concentrations_mol_m3) for row in req.initial_species}
        phase_inventory0={row.phase_id:row.moles_per_axial_metre_mol_m
                          for row in req.geometry.history[0].phase_inventories}
        target_inventory_current=dict(phase_inventory0)
        radius_target=[prior_radii[0]]
        for k,row in enumerate(trial["intervals"]):
            # Conservative left-held supply estimate is recomputed on the pass state at interval start.
            left_radius=float(geom_states[k]["bore_radius_m"]); edges=_edges(left_radius,req.knots[k].solution_film_thickness_m,len(next(iter(start_profiles.values()))))
            boundary={b.species_id:b for b in req.knots[k].species_boundaries}; row_rates=[]
            for p,phase in enumerate(phases):
                previous=target_inventory_current[phase.phase_id]
                intrinsic=phase.flux_history[k].intrinsic_precipitation_flux_mol_m2_s
                if intrinsic<0:limited=max(intrinsic,-previous/(2*math.pi*left_radius*(times[k+1]-times[k])))
                else:
                    nr=len(edges)-1; centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]; caps=[]
                    for sid,coeff in phase.species_moles_per_mole_solid.items():
                        b=boundary[sid]; d=b.radial_cell_diffusivity_m2_s
                        res=math.log(centers[0]/left_radius)/d[0]
                        for j in range(1,nr):res+=math.log(edges[j]/centers[j-1])/d[j-1]+math.log(centers[j]/edges[j])/d[j]
                        res+=math.log((left_radius+req.knots[k].solution_film_thickness_m)/centers[-1])/d[-1]
                        supply=max(0.0,b.bulk_concentration_mol_m3-start_profiles[sid][0])/(left_radius*res)
                        if coeff>0: caps.append(supply/coeff)
                    limited=min(intrinsic,min(caps,default=intrinsic))
                row_rates.append(limited)
            # Several phases may consume the same dissolved species. Share its one radial
            # supply cap proportionally so their combined demand cannot exceed transport.
            for sid in sorted(set().union(*(set(ph.species_moles_per_mole_solid) for ph in phases))):
                demand=math.fsum(max(ph.species_moles_per_mole_solid.get(sid,0.0),0.0)*max(row_rates[p],0.0)
                    for p,ph in enumerate(phases))
                if demand<=0: continue
                b=boundary[sid]; d=b.radial_cell_diffusivity_m2_s; nr=len(edges)-1
                centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]
                resistance=math.log(centers[0]/left_radius)/d[0]
                for j in range(1,nr): resistance+=math.log(edges[j]/centers[j-1])/d[j-1]+math.log(centers[j]/edges[j])/d[j]
                resistance+=math.log((left_radius+req.knots[k].solution_film_thickness_m)/centers[-1])/d[-1]
                supply=max(0.0,b.bulk_concentration_mol_m3-start_profiles[sid][0])/(left_radius*resistance)
                factor=min(1.0,supply/demand)
                for p,ph in enumerate(phases):
                    if row_rates[p]>0 and ph.species_moles_per_mole_solid.get(sid,0.0)>0: row_rates[p]*=factor
            targets.append(row_rates)
            for p,phase in enumerate(phases):
                target_inventory_current[phase.phase_id]+=row_rates[p]*(2*math.pi*left_radius)*(times[k+1]-times[k])
                if target_inventory_current[phase.phase_id] < -request.absolute_inventory_tolerance_mol_m:
                    return Calculation(status="out_of_scope",values=base|{"reason":"caller_dissolution_flux_exceeds_solid_inventory",
                        "failed_interval_index":k,"phase_id":phase.phase_id,"completed_iterations":iteration_rows,
                        "failure_prefix":trial["intervals"]})
            # Advance left state from the just integrated interval for next-knot limiter.
            history_index=k
            if history_index<len(trial["history"]):start_profiles=trial["history"][history_index]["species_profile_mol_m3_by_species"]
        phase_volumes={row.phase_id:row.molar_volume_m3_mol for row in req.geometry.phases}
        geometry_path=[{"time_s":times[0],"bore_radius_m":prior_radii[0],
                        "steel_inner_radius_m":req.geometry.initial_inner_radius_m,
                        "wall_recession_m":0.0,
                        "scale_inventory_mol_m_by_phase":{row.phase_id:row.moles_per_axial_metre_mol_m for row in req.geometry.history[0].phase_inventories},
                        "wall_element_release_mol_m_by_element":{e.element_id:0.0 for e in req.wall_elements},
                        "wall_element_geometry_residual_mol_m_by_element":{e.element_id:0.0 for e in req.wall_elements}}]
        for knot_history in trial["history"]:
            release=knot_history["cumulative_wall_release_mol_m_by_element"]
            metal_mass=math.fsum(release[e.element_id]*e.atomic_molar_mass_kg_mol for e in req.wall_elements)
            steel_r2=req.geometry.initial_inner_radius_m**2+metal_mass/(req.wall_density_kg_m3*math.pi)
            inv=knot_history["scale_inventory_mol_m_by_phase"]
            annulus=math.fsum(inv[pid]*phase_volumes[pid] for pid in phase_volumes)/math.pi
            radius2=steel_r2-annulus
            if not math.isfinite(radius2) or radius2<=0:
                return Calculation(status="out_of_scope",values=base|{"reason":"scale_and_recession_imply_nonpositive_radius",
                    "completed_iterations":iteration_rows,"failure_prefix":trial["intervals"]})
            radius_target.append(math.sqrt(radius2))
            steel_radius=math.sqrt(steel_r2)
            if steel_radius>=req.geometry.outer_radius_m or math.sqrt(radius2)>=steel_radius:
                return Calculation(status="out_of_scope",values=base|{"reason":"recession_or_scale_exceeds_cylindrical_wall",
                    "failed_time_s":knot_history["time_s"],"completed_iterations":iteration_rows,
                    "failure_prefix":trial["intervals"]})
            recession=steel_radius-req.geometry.initial_inner_radius_m
            expected_release={e.element_id:math.pi*(steel_radius**2-req.geometry.initial_inner_radius_m**2)*
                req.wall_density_kg_m3*e.alloy_mass_fraction/e.atomic_molar_mass_kg_mol for e in req.wall_elements}
            release_residual={e.element_id:expected_release[e.element_id]-release[e.element_id] for e in req.wall_elements}
            if any(abs(v)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*
                   max(abs(expected_release[e]),1e-30) for e,v in release_residual.items()):
                return Calculation(status="out_of_scope",values=base|{"reason":"wall_element_release_does_not_match_cylindrical_recession",
                    "failed_time_s":knot_history["time_s"],"wall_element_geometry_residual_mol_m":release_residual,
                    "completed_iterations":iteration_rows,"failure_prefix":trial["intervals"]})
            geometry_path.append({"time_s":knot_history["time_s"],"bore_radius_m":math.sqrt(radius2),
                "steel_inner_radius_m":steel_radius,"wall_recession_m":recession,
                "scale_inventory_mol_m_by_phase":inv,"wall_element_release_mol_m_by_element":release,
                "wall_element_geometry_residual_mol_m":release_residual})
        radius_res=max(abs(a-b) for a,b in zip(prior_radii,radius_target,strict=True))
        flux_res=max((abs(a-b) for old,new in zip(rate_guess,targets,strict=True) for a,b in zip(old,new,strict=True)),default=0.0)
        iteration_rows.append({"iteration":iteration,"radius_residual_m":radius_res,"flux_residual_mol_m2_s":flux_res,
            "radius_path_m":radius_target,"scale_flux_by_interval_mol_m2_s":targets,
            "geometry_digest":canonical_digest(geometry_path),"interval_count":len(trial["intervals"])})
        final=trial
        if radius_res<=request.absolute_radius_tolerance_m+request.relative_radius_tolerance*max(req.geometry.outer_radius_m,1e-30) and flux_res<=1e-12+1e-7*max((abs(x) for row in targets for x in row),default=0):
            break
        relax=request.relaxation_factor
        rate_guess=[[(1-relax)*a+relax*b for a,b in zip(old,new,strict=True)] for old,new in zip(rate_guess,targets,strict=True)]
        prior_radii=[(1-relax)*a+relax*b for a,b in zip(prior_radii,radius_target,strict=True)]
        geom_states=[dict(row)|{"bore_radius_m":prior_radii[i]} for i,row in enumerate(geom_states)]
    else:
        return Calculation(status="out_of_scope",values=base|{"reason":"feedback_not_converged","completed_iterations":iteration_rows,
            "failure_prefix":final["intervals"] if final else []})
    if final is None:return Calculation(status="out_of_scope",values=base|{"reason":"no_feedback_iteration_completed"})
    return Calculation(status="computed",values=base|{"iteration_count":len(iteration_rows),"iteration_history":iteration_rows,
        "history":final["history"],"interval_ledger":final["intervals"],
        "geometry_history":geometry_path,"geometry_history_sha256":canonical_digest(geometry_path),
        "final_scale_inventory_mol_m_by_phase":final["scale_inventory_mol_m_by_phase"],
        "final_cumulative_wall_release_mol_m_by_element":final["cumulative_wall_release_mol_m_by_element"],
        "geometry_result_sha256":canonical_digest(geometry.model_dump(mode="json")),
        "phase_lineage":[{"phase_id":phase.phase_id,"stoichiometry_sha256":phase.stoichiometry_sha256,
            "stoichiometry_evidence_source_ids":[e.source_id for e in phase.stoichiometry_evidence],
            "flux_records":[{"time_s":flux.time_s,"record_sha256":flux.record_sha256,
                "evidence_source_ids":[e.source_id for e in flux.evidence]} for flux in phase.flux_history]}
            for phase in phases],
        "conservation_scope":"aqueous inventory closure includes simultaneous BV and caller scale terms in each interval RHS; solid formula is caller-bound; global geometry and moving-mesh closure remain explicit ledgers"})


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalAqueousScaleSinkFeedback,
        evaluator=evaluate_wet_co2_cylindrical_aqueous_scale_sink_feedback,
        units={
            "time_s[]": "s",
            "history[].concentration_mol_m3[]": "mol/m^3",
            "final_scale_inventory_mol_m_by_phase.*[]": "mol/m",
            "geometry_history[].bore_radius_m": "m",
        },
        assumptions=(
            "Caller owns phase identity, stoichiometry, intrinsic phase flux law, and geometry inputs.",
            "Caller phase flux and geometry data are left-held on exact knots; no intra-knot chemistry or phase-selection law is inferred.",
            "Scale reaction source/sink terms are inserted in the same interval BDF RHS as the BV transport terms and are limited by shared cylindrical reactant supply.",
            "The bounded outer iteration is not a thermodynamic phase-selection, validated corrosion-life, or qualification model.",
            "Independent carrier ions, pH/speciation and gas equilibria are not solved unless supplied as transported species and caller flux histories.",
        ),
        source_ids=(SOURCE_ID, DIFFUSION_SOURCE_ID),
        qualification="user_model",
    ),)
