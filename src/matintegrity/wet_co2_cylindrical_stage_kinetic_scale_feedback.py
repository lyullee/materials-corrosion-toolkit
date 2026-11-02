"""Stage-coupled activity-driven scale kinetics in cylindrical BV transport."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import evaluate_wet_co2_cylindrical_scale_geometry_history
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

MODEL_ID = "integration.wet_co2_cylindrical_stage_kinetic_scale_feedback"
KINETICS_SOURCE_ID = "caller_activity_driven_stage_scale_kinetics"
SUPPLY_SOURCE_ID = "multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages"


class WetCo2StageActivityProductTerm(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    exponent: Positive
    reference_concentration_mol_m3: Positive


class WetCo2StageActivityKnot(Contract):
    time_s: Nonnegative
    log_solubility_activity_product: float
    activity_coefficients_by_species: dict[str, Positive]
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_activity_state(self):
        if not math.isfinite(self.log_solubility_activity_product):
            raise ValueError("log solubility activity product must be finite")
        payload = {"time_s": self.time_s,
                   "log_solubility_activity_product": self.log_solubility_activity_product,
                   "activity_coefficients_by_species": self.activity_coefficients_by_species}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("activity-knot digest must bind time, log K and all activity coefficients")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin every activity/solubility knot")
        return self


class WetCo2StageKineticPhase(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    species_moles_per_mole_solid: dict[str, float]
    phase_element_composition: dict[str, Positive]
    activity_product_terms: tuple[WetCo2StageActivityProductTerm, ...] = Field(min_length=1, max_length=64)
    activity_history: tuple[WetCo2StageActivityKnot, ...] = Field(min_length=2, max_length=2000)
    precipitation_rate_constant_mol_m2_s: Nonnegative
    precipitation_log_supersaturation_exponent: Positive
    dissolution_rate_constant_mol_m2_s: Nonnegative
    dissolution_log_undersaturation_exponent: Positive
    maximum_absolute_flux_mol_m2_s: Positive
    kinetic_law_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_law_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    chemistry_and_rate_law_reviewed: bool

    @model_validator(mode="after")
    def bind_law(self):
        if not self.species_moles_per_mole_solid or any(not math.isfinite(v) or v == 0.0
                for v in self.species_moles_per_mole_solid.values()):
            raise ValueError("phase reaction requires finite nonzero signed aqueous stoichiometry")
        if len({row.species_id for row in self.activity_product_terms}) != len(self.activity_product_terms):
            raise ValueError("activity-product species terms must be unique")
        payload = {"phase_id": self.phase_id,
            "species_moles_per_mole_solid": self.species_moles_per_mole_solid,
            "phase_element_composition": self.phase_element_composition,
            "activity_product_terms": [row.model_dump(mode="json") for row in self.activity_product_terms],
            "precipitation_rate_constant_mol_m2_s": self.precipitation_rate_constant_mol_m2_s,
            "precipitation_log_supersaturation_exponent": self.precipitation_log_supersaturation_exponent,
            "dissolution_rate_constant_mol_m2_s": self.dissolution_rate_constant_mol_m2_s,
            "dissolution_log_undersaturation_exponent": self.dissolution_log_undersaturation_exponent,
            "maximum_absolute_flux_mol_m2_s": self.maximum_absolute_flux_mol_m2_s}
        if canonical_digest(payload) != self.kinetic_law_sha256:
            raise ValueError("kinetic-law digest must bind phase, formula, activity terms and all rate parameters")
        if not any(row.sha256 == self.kinetic_law_sha256 and row.license_id for row in self.kinetic_law_evidence):
            raise ValueError("licensed Evidence must pin the complete caller kinetic law")
        return self


class WetCo2CylindricalStageKineticScaleFeedback(Contract):
    schema_version: Literal["matintegrity.wet_co2_cylindrical_stage_kinetic_scale_feedback.v1"] = (
        "matintegrity.wet_co2_cylindrical_stage_kinetic_scale_feedback.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_request: WetCo2CylindricalSpatialMixedPotential
    phases: tuple[WetCo2StageKineticPhase, ...] = Field(min_length=1, max_length=32)
    maximum_feedback_iterations: int = Field(default=20, ge=1, le=60)
    relaxation_factor: float = Field(default=0.5, gt=0, le=1)
    absolute_radius_tolerance_m: Positive = Field(default=1e-9)
    relative_radius_tolerance: Positive = Field(default=1e-7, le=1e-2)
    absolute_inventory_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_inventory_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_work_units: int = Field(default=30_000_000, ge=10_000, le=300_000_000)
    activity_model_and_reference_state_reviewed: bool
    phase_identity_and_balanced_reaction_reviewed: bool
    cylindrical_supply_map_reviewed: bool
    exact_knot_left_hold_and_geometry_reviewed: bool
    no_qualification_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_composition_and_budget(self):
        req = self.spatial_request
        if req.geometry_trial_mode:
            raise ValueError("stage kinetics requires an ordinary spatial request")
        times = tuple(row.time_s for row in req.knots)
        if times != tuple(row.time_s for row in req.geometry.history):
            raise ValueError("BV and geometry knots must exactly align")
        species = {row.species_id: row for row in req.species}
        geometry_phases = {row.phase_id: row for row in req.geometry.phases}
        if len(geometry_phases) != len(req.geometry.phases) or len({p.phase_id for p in self.phases}) != len(self.phases):
            raise ValueError("phase identifiers must be unique")
        if set(geometry_phases) != {p.phase_id for p in self.phases}:
            raise ValueError("kinetic phase set must equal the geometry phase set")
        for phase in self.phases:
            if tuple(row.time_s for row in phase.activity_history) != times:
                raise ValueError("each phase activity and solubility schedule must match exact geometry knots")
            if set(phase.species_moles_per_mole_solid) - set(species):
                raise ValueError("phase reaction species must be present in the spatial aqueous species list")
            term_ids = {row.species_id for row in phase.activity_product_terms}
            if not term_ids <= set(species):
                raise ValueError("activity product terms must refer to declared aqueous species")
            expected_q_terms={sid:coef for sid,coef in phase.species_moles_per_mole_solid.items() if coef>0.0}
            actual_q_terms={row.species_id:row.exponent for row in phase.activity_product_terms}
            if set(actual_q_terms)!=set(expected_q_terms) or any(not math.isclose(actual_q_terms[sid],expected_q_terms[sid],
                    rel_tol=1e-10,abs_tol=1e-10) for sid in expected_q_terms):
                raise ValueError("Q activity terms/exponents must equal positive aqueous reactant stoichiometry")
            if any(term_ids != set(knot.activity_coefficients_by_species) for knot in phase.activity_history):
                raise ValueError("each activity knot must supply exactly one coefficient for every Q term")
            reaction_charge = math.fsum(coef*species[sid].charge_number
                for sid,coef in phase.species_moles_per_mole_solid.items())
            if not math.isclose(reaction_charge,0.0,rel_tol=1e-10,abs_tol=1e-10):
                raise ValueError("scale formation/dissolution stoichiometry must be electrically neutral")
            reaction_elements: dict[str,float] = {}
            for sid,coef in phase.species_moles_per_mole_solid.items():
                for element,count in species[sid].elemental_composition.items():
                    reaction_elements[element]=reaction_elements.get(element,0.0)+coef*count
            all_elements=set(reaction_elements)|set(phase.phase_element_composition)
            if any(not math.isclose(reaction_elements.get(e,0.0),phase.phase_element_composition.get(e,0.0),
                    rel_tol=1e-10,abs_tol=1e-10) for e in all_elements):
                raise ValueError("aqueous stoichiometry and solid element formula do not balance")
        nr=len(req.initial_species[0].cell_concentrations_mol_m3)
        reaction_count=max(len(k.reactions) for k in req.knots)
        state_count=nr*len(species)+3*len(species)+len(req.wall_elements)+reaction_count+len(self.phases)+1
        rhs_budget=self.maximum_work_units//(self.maximum_feedback_iterations*(len(times)-1)*state_count)
        if rhs_budget<20:
            raise ValueError("work budget leaves fewer than 20 stage evaluations per interval")
        if not req.axisymmetric_reaction_area_and_material_mapping_reviewed or not req.boundary_transport_and_chemistry_reviewed or not req.element_charge_and_reaction_direction_reviewed:
            raise ValueError("underlying BV/spatial review gates must be complete")
        return self


def _activity_log_ratio(phase, knot, wall_concentrations):
    log_q=0.0
    for term in phase.activity_product_terms:
        concentration=wall_concentrations[term.species_id]
        if concentration<=0.0:
            return -math.inf
        gamma=knot.activity_coefficients_by_species[term.species_id]
        activity=gamma*concentration/term.reference_concentration_mol_m3
        if not math.isfinite(activity) or activity<=0.0:
            raise ArithmeticError("caller activity left positive finite support")
        log_q+=term.exponent*math.log(activity)
    return log_q-knot.log_solubility_activity_product


def _bounded_power_rate(constant, driving, exponent, cap):
    if constant<=0.0 or driving<=0.0:
        return 0.0
    log_rate=math.log(constant)+exponent*math.log(driving)
    if log_rate>=math.log(cap):
        return cap
    return math.exp(log_rate)


def _radial_supply(request, knot_index, sid, concentration, radius, edges, boundary):
    nr=len(edges)-1; centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]
    d=boundary.radial_cell_diffusivity_m2_s
    resistance=math.log(centers[0]/radius)/d[0]
    for j in range(1,nr):
        resistance+=math.log(edges[j]/centers[j-1])/d[j-1]+math.log(centers[j]/edges[j])/d[j]
    resistance+=math.log((radius+request.knots[knot_index].solution_film_thickness_m)/centers[-1])/d[-1]
    return max(0.0,boundary.bulk_concentration_mol_m3-concentration)/(radius*resistance)


def _stage_fluxes(request, phases, knot_index, time_s, y, nr, sids, boundaries, edges, radius,
                  interval_end_s, dt, phase_offsets):
    sidx={sid:index for index,sid in enumerate(sids)}
    stage_profiles={sid:y[sidx[sid]*nr:(sidx[sid]+1)*nr] for sid in sids}
    wall_concentrations={sid:max(0.0,float(stage_profiles[sid][0])) for sid in sids}
    raw=[]; saturation=[]
    for p,phase in enumerate(phases):
        knot=phase.activity_history[knot_index]
        log_si=_activity_log_ratio(phase,knot,wall_concentrations)
        saturation.append(log_si)
        if log_si>0.0:
            rate=_bounded_power_rate(phase.precipitation_rate_constant_mol_m2_s,log_si,
                phase.precipitation_log_supersaturation_exponent,phase.maximum_absolute_flux_mol_m2_s)
        elif log_si<0.0:
            rate=-_bounded_power_rate(phase.dissolution_rate_constant_mol_m2_s,-log_si,
                phase.dissolution_log_undersaturation_exponent,phase.maximum_absolute_flux_mol_m2_s)
        else:
            rate=0.0
        raw.append(max(-phase.maximum_absolute_flux_mol_m2_s,
                       min(phase.maximum_absolute_flux_mol_m2_s,rate)))
    # Cap each phase's dissolution by its live inventory and remaining interval time.
    remaining=max(interval_end_s-time_s,dt*1e-12)
    for p,phase in enumerate(phases):
        inv=max(0.0,float(y[phase_offsets[p]]))
        if raw[p]<0.0:
            raw[p]=max(raw[p],-inv/(2*math.pi*radius*remaining))
    # Apply a joint cylindrical diffusion supply cap for every aqueous reactant consumed
    # by simultaneous precipitation phases.
    for sid in sids:
        demand=math.fsum(max(phase.species_moles_per_mole_solid.get(sid,0.0),0.0)*max(raw[p],0.0)
            for p,phase in enumerate(phases))
        if demand<=0.0: continue
        supply=_radial_supply(request,knot_index,sid,wall_concentrations[sid],radius,edges,boundaries[sid])
        factor=min(1.0,supply/demand)
        for p,phase in enumerate(phases):
            if raw[p]>0 and phase.species_moles_per_mole_solid.get(sid,0.0)>0:
                raw[p]*=factor
    return raw,saturation


def _run_stage_coupled_intervals(request, phases, geometry_states, rhs_budget):
    from scipy.integrate import solve_ivp
    species=list(request.species); sids=[s.species_id for s in species]; sidx={sid:i for i,sid in enumerate(sids)}
    nr=len(request.initial_species[0].cell_concentrations_mol_m3); nsp=len(sids); ne=len(request.wall_elements)
    profiles={row.species_id:list(row.cell_concentrations_mol_m3) for row in request.initial_species}
    scale0={row.phase_id:row.moles_per_axial_metre_mol_m for row in request.geometry.history[0].phase_inventories}
    phase_inventory={p.phase_id:scale0[p.phase_id] for p in phases}
    metal_release={row.element_id:0.0 for row in request.wall_elements}; intervals=[]; history=[]
    for k,(knot,nxt) in enumerate(zip(request.knots,request.knots[1:],strict=False)):
        dt=nxt.time_s-knot.time_s; radius=float(geometry_states[k]["bore_radius_m"]); area=2*math.pi*radius
        edges=_edges(radius,knot.solution_film_thickness_m,nr); volumes=_cell_volumes_per_axial_metre(edges)
        centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]
        bound_rows={row.species_id:row for row in knot.species_boundaries}; boundaries={sid:bound_rows[sid] for sid in sids}
        reactions=knot.reactions; nre=len(reactions); np=len(phases); csize=nsp*nr
        off_outer=csize; off_bv=off_outer+nsp; off_scale=off_bv+nsp; off_wall=off_scale+nsp
        off_extent=off_wall+ne; off_charge=off_extent+nre; off_inventory=off_charge+1
        phase_offsets=[off_inventory+p for p in range(np)]
        start_moles={sid:math.fsum(c*v for c,v in zip(profiles[sid],volumes,strict=True)) for sid in sids}
        y0=[profiles[sid][j] for sid in sids for j in range(nr)]+[0.0]*(3*nsp+ne+nre+1)+[phase_inventory[p.phase_id] for p in phases]
        atol=[request.concentration_absolute_tolerance_mol_m3]*csize+[request.inventory_absolute_tolerance_mol_m]*(3*nsp+ne+nre+1+np)
        evals=[0]
        def rhs(time_s,y):
            evals[0]+=1
            if evals[0]>rhs_budget: raise ArithmeticError("bounded BDF stage-evaluation budget exceeded")
            cs=[list(y[p*nr:(p+1)*nr]) for p in range(nsp)]
            if any(not math.isfinite(c) or c < -request.concentration_absolute_tolerance_mol_m3 for row in cs for c in row):
                raise ArithmeticError("aqueous stage concentration became negative or nonfinite")
            potential,bv_rows,_=_transport_fluxes(cs,boundaries,edges,radius,reactions,
                request.potential_absolute_tolerance_V,request.maximum_bisection_iterations)
            fluxes,log_si=_stage_fluxes(request,phases,k,time_s,y,nr,sids,boundaries,edges,radius,
                nxt.time_s,dt,phase_offsets)
            bv_species={sid:0.0 for sid in sids}; wall={e.element_id:0.0 for e in request.wall_elements}
            extent_rate={r.reaction_id:0.0 for r in reactions}
            for reaction in reactions:
                row=bv_rows[reaction.reaction_id];extent=row["extent_mol_m2_s"]
                extent_rate[reaction.reaction_id]=extent*area
                for sid,coefficient in reaction.stoichiometric_species_coefficients.items():bv_species[sid]+=coefficient*extent*area
                for element in wall:
                    gain=math.fsum(coefficient*species[sidx[sid]].elemental_composition.get(element,0.0)
                        for sid,coefficient in reaction.stoichiometric_species_coefficients.items())
                    if gain>0:wall[element]+=gain*extent*area
            scale_species={sid:0.0 for sid in sids}
            for p,phase in enumerate(phases):
                for sid,coefficient in phase.species_moles_per_mole_solid.items():
                    scale_species[sid]-=coefficient*fluxes[p]*area
            dy=[0.0]*len(y)
            for pos,sid in enumerate(sids):
                c=cs[pos];d=boundaries[sid].radial_cell_diffusivity_m2_s;balance=[0.0]*nr
                for f in range(1,nr):
                    resistance=math.log(edges[f]/centers[f-1])/d[f-1]+math.log(centers[f]/edges[f])/d[f]
                    flow=2*math.pi/resistance*(c[f-1]-c[f]);balance[f-1]-=flow;balance[f]+=flow
                resistance=math.log(edges[-1]/centers[-1])/d[-1]
                outer_flow=2*math.pi/resistance*(boundaries[sid].bulk_concentration_mol_m3-c[-1])
                balance[-1]+=outer_flow;balance[0]+=bv_species[sid]+scale_species[sid]
                for j in range(nr):dy[pos*nr+j]=balance[j]/volumes[j]
                dy[off_outer+pos]=outer_flow;dy[off_bv+pos]=bv_species[sid];dy[off_scale+pos]=scale_species[sid]
            for p,element in enumerate(wall):dy[off_wall+p]=wall[element]
            for p,reaction in enumerate(reactions):dy[off_extent+p]=extent_rate[reaction.reaction_id]
            dy[off_charge]=-FARADAY_C_MOL*math.fsum(reaction.electron_count*bv_rows[reaction.reaction_id]["extent_mol_m2_s"]*area for reaction in reactions)
            for p in range(np):dy[phase_offsets[p]]=fluxes[p]*area
            return dy
        try:
            sol=solve_ivp(rhs,(knot.time_s,nxt.time_s),y0,method="BDF",t_eval=[nxt.time_s],
                rtol=request.relative_tolerance,atol=atol,max_step=min(request.maximum_step_s,dt))
        except (ArithmeticError,ValueError,RuntimeError) as exc:
            return {"failure":{"failed_interval_index":k,"detail":str(exc),"partial_interval_rhs_evaluations":evals[0],
                "rhs_evaluation_budget":rhs_budget,"completed_intervals":intervals},"history":history}
        if not sol.success or sol.y.shape[1]!=1 or sol.t[-1]!=nxt.time_s:
            return {"failure":{"failed_interval_index":k,"detail":str(sol.message),"completed_intervals":intervals},"history":history}
        y=[float(v) for v in sol.y[:,-1]]
        for pos,sid in enumerate(sids):
            values=y[pos*nr:(pos+1)*nr]
            if min(values)<-request.concentration_absolute_tolerance_mol_m3:
                return {"failure":{"failed_interval_index":k,"reason":"negative_aqueous_inventory","species_id":sid,"completed_intervals":intervals},"history":history}
            profiles[sid]=[max(0.0,v) for v in values]
        outer={sid:y[off_outer+p] for p,sid in enumerate(sids)};bv={sid:y[off_bv+p] for p,sid in enumerate(sids)}
        scale={sid:y[off_scale+p] for p,sid in enumerate(sids)}
        inventory={sid:math.fsum(c*v for c,v in zip(profiles[sid],volumes,strict=True)) for sid in sids}
        species_residual={sid:inventory[sid]-start_moles[sid]-outer[sid]-bv[sid]-scale[sid] for sid in sids}
        charge_residual=math.fsum(species[sidx[sid]].charge_number*r for sid,r in species_residual.items())
        elements=sorted({e for sp in species for e in sp.elemental_composition})
        element_residual={e:math.fsum(species[sidx[sid]].elemental_composition.get(e,0.0)*r for sid,r in species_residual.items()) for e in elements}
        electronic=FARADAY_C_MOL*math.fsum(species[sidx[sid]].charge_number*bv[sid] for sid in sids)+y[off_charge]
        phase_inventory_start=dict(phase_inventory)
        if any(abs(r)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*max(abs(inventory[sid]),1e-30)
                for sid,r in species_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_species_closure_failed","residual_mol_m_by_species":species_residual,"completed_intervals":intervals},"history":history}
        if abs(electronic)>request.spatial_request.charge_absolute_tolerance_C_m+request.relative_inventory_tolerance*max(abs(y[off_charge]),1e-30):
            return {"failure":{"failed_interval_index":k,"reason":"bv_electronic_charge_closure_failed","residual_C_m":electronic,"completed_intervals":intervals},"history":history}
        if abs(charge_residual)>(request.spatial_request.charge_absolute_tolerance_C_m/FARADAY_C_MOL+
                request.relative_inventory_tolerance*max(1e-30,math.fsum(abs(species[sidx[sid]].charge_number*inventory[sid]) for sid in sids))):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_charge_closure_failed","residual_mol_charge_m":charge_residual,"completed_intervals":intervals},"history":history}
        if any(abs(value)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*
                max(1e-30,math.fsum(abs(species[sidx[sid]].elemental_composition.get(e,0.0)*inventory[sid]) for sid in sids))
                for e,value in element_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_element_closure_failed","residual_mol_m_by_element":element_residual,"completed_intervals":intervals},"history":history}
        scale_transfer_element={e:math.fsum(species[sidx[sid]].elemental_composition.get(e,0.0)*scale[sid] for sid in sids)
            for e in elements}
        phase_inventory_end={phase.phase_id:y[phase_offsets[p]] for p,phase in enumerate(phases)}
        solid_element_delta={e:math.fsum((phase_inventory_end[p.phase_id]-phase_inventory_start[p.phase_id])*
            p.phase_element_composition.get(e,0.0) for p in phases) for e in sorted(set(elements)|
            set().union(*(set(p.phase_element_composition) for p in phases)))}
        solid_aqueous_element_residual={e:scale_transfer_element.get(e,0.0)+solid_element_delta.get(e,0.0)
            for e in sorted(set(scale_transfer_element)|set(solid_element_delta))}
        if any(abs(v)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*
                max(abs(scale_transfer_element.get(e,0.0)),abs(solid_element_delta.get(e,0.0)),1e-30)
                for e,v in solid_aqueous_element_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_solid_element_closure_failed",
                "residual_mol_m_by_element":solid_aqueous_element_residual,"completed_intervals":intervals},"history":history}
        endpoint_flux,endpoint_log_si=_stage_fluxes(request,phases,k,nxt.time_s,y,nr,sids,boundaries,edges,radius,
            nxt.time_s,dt,phase_offsets)
        endpoint_log_si={phase.phase_id:(value if math.isfinite(value) else None)
            for phase,value in zip(phases,endpoint_log_si,strict=True)}
        endpoint_flux={phase.phase_id:value for phase,value in zip(phases,endpoint_flux,strict=True)}
        intervals.append({"interval_index":k,"start_time_s":knot.time_s,"end_time_s":nxt.time_s,"geometry_radius_left_m":radius,
            "activity_and_logK_held_from_left_knot":True,"bv_and_stage_scale_sources_share_bdf_rhs":True,
            "rhs_evaluations":evals[0],"rhs_evaluation_budget":rhs_budget,
            "time_averaged_scale_flux_mol_m2_s_by_phase":{p.phase_id:(y[phase_offsets[j]]-phase_inventory[p.phase_id])/(area*dt) for j,p in enumerate(phases)},
            "solid_inventory_end_mol_m_by_phase":dict(phase_inventory_end),
            "solid_element_increment_mol_m_by_element":solid_element_delta,
            "endpoint_log_saturation_ratio_by_phase":endpoint_log_si,
            "endpoint_supply_limited_flux_mol_m2_s_by_phase":endpoint_flux,
            "aqueous_outer_exchange_mol_m_by_species":outer,"aqueous_bv_transfer_mol_m_by_species":bv,
            "aqueous_scale_transfer_mol_m_by_species":scale,"aqueous_inventory_residual_mol_m_by_species":species_residual,
            "aqueous_charge_residual_mol_charge_m":charge_residual,"aqueous_element_residual_mol_m_by_element":element_residual,
            "bv_electronic_charge_residual_C_m":electronic,"solid_inventory_start_mol_m_by_phase":phase_inventory_start,
            "aqueous_scale_transfer_element_mol_m_by_element":scale_transfer_element,
            "solid_phase_element_increment_mol_m_by_element":solid_element_delta,
            "scale_aqueous_solid_element_residual_mol_m_by_element":solid_aqueous_element_residual})
        for p,phase in enumerate(phases):
            phase_inventory[phase.phase_id]=y[phase_offsets[p]]
            if phase_inventory[phase.phase_id]<-request.absolute_inventory_tolerance_mol_m:
                return {"failure":{"failed_interval_index":k,"reason":"solid_inventory_depleted","phase_id":phase.phase_id,"completed_intervals":intervals},"history":history}
            phase_inventory[phase.phase_id]=max(0.0,phase_inventory[phase.phase_id])
        for p,element in enumerate(metal_release):metal_release[element]+=y[off_wall+p]
        next_edges=_edges(float(geometry_states[k+1]["bore_radius_m"]),nxt.solution_film_thickness_m,nr)
        next_boundaries={row.species_id:row for row in nxt.species_boundaries};sweep={}
        for sid in sids:
            profiles[sid],sweep[sid]=_remap_species(edges,next_edges,profiles[sid],next_boundaries[sid].bulk_concentration_mol_m3,next_boundaries[sid].bulk_concentration_mol_m3)
        intervals[-1]["moving_mesh_sweep_by_species"]=sweep
        post_volume=_cell_volumes_per_axial_metre(next_edges)
        post_inventory={sid:math.fsum(c*v for c,v in zip(profiles[sid],post_volume,strict=True)) for sid in sids}
        solid_elements={}
        for phase in phases:
            for element,count in phase.phase_element_composition.items():solid_elements[element]=solid_elements.get(element,0.0)+phase_inventory[phase.phase_id]*count
        history.append({"time_s":nxt.time_s,"species_profile_mol_m3_by_species":{sid:list(v) for sid,v in profiles.items()},
            "aqueous_inventory_after_mesh_remap_mol_m_by_species":post_inventory,
            "phase_inventory_mol_m_by_phase":dict(phase_inventory),"solid_element_inventory_mol_m_by_element":solid_elements,
            "cumulative_wall_release_mol_m_by_element":dict(metal_release)})
    return {"failure":None,"intervals":intervals,"history":history,
        "final_phase_inventory_mol_m_by_phase":phase_inventory,"cumulative_wall_release_mol_m_by_element":metal_release}


def evaluate_wet_co2_cylindrical_stage_kinetic_scale_feedback(request: WetCo2CylindricalStageKineticScaleFeedback) -> Calculation:
    req=request.spatial_request;input_digest=canonical_digest(request.model_dump(mode="json"))
    base={"assessment_id":request.assessment_id,"model_id":MODEL_ID,"input_sha256":input_digest,
          "spatial_input_sha256":canonical_digest(req.model_dump(mode="json")),"source_ids":[KINETICS_SOURCE_ID,SUPPLY_SOURCE_ID]}
    missing=[name for name in ("activity_model_and_reference_state_reviewed","phase_identity_and_balanced_reaction_reviewed",
        "cylindrical_supply_map_reviewed","exact_knot_left_hold_and_geometry_reviewed","no_qualification_claim_reviewed",
        "computational_use_authorized") if not getattr(request,name)]
    missing.extend(f"phase:{p.phase_id}:chemistry_and_rate_law_reviewed" for p in request.phases if not p.chemistry_and_rate_law_reviewed)
    if missing:return Calculation(status="needs_data",values=base|{"reason":"review_gates_incomplete","missing_reviews":missing})
    geometry=evaluate_wet_co2_cylindrical_scale_geometry_history(req.geometry)
    if geometry.status!="computed":return Calculation(status=geometry.status,values=base|{"reason":"geometry_not_computed"})
    geom_states=[dict(row) for row in geometry.values["history"]];initial_radii=[float(row["bore_radius_m"]) for row in geom_states]
    nr=len(req.initial_species[0].cell_concentrations_mol_m3);nsp=len(req.species);nint=len(req.knots)-1
    state_count=nr*nsp+3*nsp+len(req.wall_elements)+max(len(k.reactions) for k in req.knots)+len(request.phases)+1
    rhs_budget=request.maximum_work_units//(request.maximum_feedback_iterations*nint*state_count)
    iterations=[];final=None;geometry_path=[]
    phase_volumes={p.phase_id:p.molar_volume_m3_mol for p in req.geometry.phases}
    for iteration in range(1,request.maximum_feedback_iterations+1):
        trial=_run_stage_coupled_intervals(req,request.phases,geom_states,rhs_budget)
        if trial["failure"]:
            return Calculation(status="out_of_scope",values=base|{"reason":"stage_kinetic_interval_failed","failure_prefix":trial["failure"],
                "completed_iterations":iterations,"failed_iteration":iteration})
        target_radii=[initial_radii[0]]
        geometry_path=[{"time_s":req.knots[0].time_s,"bore_radius_m":initial_radii[0],"steel_inner_radius_m":req.geometry.initial_inner_radius_m,
            "wall_recession_m":0.0,"phase_inventory_mol_m_by_phase":{r.phase_id:r.moles_per_axial_metre_mol_m for r in req.geometry.history[0].phase_inventories},
            "cumulative_wall_release_mol_m_by_element":{e.element_id:0.0 for e in req.wall_elements}}]
        for h in trial["history"]:
            release=h["cumulative_wall_release_mol_m_by_element"]
            mass=math.fsum(release[e.element_id]*e.atomic_molar_mass_kg_mol for e in req.wall_elements)
            steel_r2=req.geometry.initial_inner_radius_m**2+mass/(req.wall_density_kg_m3*math.pi)
            inventory=h["phase_inventory_mol_m_by_phase"]
            annulus=math.fsum(inventory[p]*phase_volumes[p] for p in phase_volumes)/math.pi
            bore_r2=steel_r2-annulus
            if not math.isfinite(bore_r2) or bore_r2<=0:
                return Calculation(status="out_of_scope",values=base|{"reason":"nonpositive_bore_from_stage_kinetics",
                    "completed_iterations":iterations,"failure_prefix":trial["intervals"]})
            steel_radius=math.sqrt(steel_r2);bore_radius=math.sqrt(bore_r2)
            if steel_radius>=req.geometry.outer_radius_m or bore_radius>=steel_radius:
                return Calculation(status="out_of_scope",values=base|{"reason":"stage_kinetics_exceeds_wall_geometry",
                    "failed_time_s":h["time_s"],"completed_iterations":iterations,"failure_prefix":trial["intervals"]})
            expected={e.element_id:math.pi*(steel_r2-req.geometry.initial_inner_radius_m**2)*req.wall_density_kg_m3*
                e.alloy_mass_fraction/e.atomic_molar_mass_kg_mol for e in req.wall_elements}
            wall_res={e.element_id:expected[e.element_id]-release[e.element_id] for e in req.wall_elements}
            if any(abs(v)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*max(abs(expected[e]),1e-30)
                   for e,v in wall_res.items()):
                return Calculation(status="out_of_scope",values=base|{"reason":"wall_element_geometry_closure_failed",
                    "failed_time_s":h["time_s"],"residual_mol_m_by_element":wall_res,"completed_iterations":iterations,
                    "failure_prefix":trial["intervals"]})
            target_radii.append(bore_radius)
            geometry_path.append({"time_s":h["time_s"],"bore_radius_m":bore_radius,"steel_inner_radius_m":steel_radius,
                "wall_recession_m":steel_radius-req.geometry.initial_inner_radius_m,
                "phase_inventory_mol_m_by_phase":inventory,"solid_element_inventory_mol_m_by_element":h["solid_element_inventory_mol_m_by_element"],
                "cumulative_wall_release_mol_m_by_element":release,"wall_element_geometry_residual_mol_m_by_element":wall_res})
        residual=max(abs(a-b) for a,b in zip(initial_radii,target_radii,strict=True))
        iterations.append({"iteration":iteration,"geometry_radius_residual_m":residual,"geometry_path_m":target_radii,
            "geometry_history_sha256":canonical_digest(geometry_path),"interval_count":nint})
        final=trial
        if residual<=request.absolute_radius_tolerance_m+request.relative_radius_tolerance*max(req.geometry.outer_radius_m,1e-30):break
        relax=request.relaxation_factor
        initial_radii=[(1-relax)*a+relax*b for a,b in zip(initial_radii,target_radii,strict=True)]
        geom_states=[dict(row)|{"bore_radius_m":initial_radii[i]} for i,row in enumerate(geom_states)]
    else:
        return Calculation(status="out_of_scope",values=base|{"reason":"geometry_feedback_not_converged","completed_iterations":iterations,
            "failure_prefix":final["intervals"] if final else []})
    return Calculation(status="computed",values=base|{"iteration_count":len(iterations),"iteration_history":iterations,
        "geometry_history":geometry_path,"geometry_history_sha256":canonical_digest(geometry_path),
        "history":final["history"],"interval_ledger":final["intervals"],
        "final_phase_inventory_mol_m_by_phase":final["final_phase_inventory_mol_m_by_phase"],
        "final_wall_release_mol_m_by_element":final["cumulative_wall_release_mol_m_by_element"],
        "seed_geometry_result_sha256":canonical_digest(geometry.model_dump(mode="json")),
        "phase_lineage":[{"phase_id":p.phase_id,"kinetic_law_sha256":p.kinetic_law_sha256,
            "kinetic_law_evidence_source_ids":[e.source_id for e in p.kinetic_law_evidence],
            "activity_records":[{"time_s":k.time_s,"record_sha256":k.record_sha256,"evidence_source_ids":[e.source_id for e in k.evidence]}
                for k in p.activity_history]} for p in request.phases],
        "model_scope":"caller activity and log-K records are left-held per exact interval; kinetic flux is recomputed at every BDF stage from wall-cell concentrations and inserted alongside BV terms; phase supply and inventory caps are stage-local"})


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalStageKineticScaleFeedback,
        evaluator=evaluate_wet_co2_cylindrical_stage_kinetic_scale_feedback,
        units={
            "time_s[]": "s",
            "geometry_history[].bore_radius_m": "m",
            "geometry_history[].steel_inner_radius_m": "m",
            "history[].phase_inventory_mol_m_by_phase.*": "mol/m",
            "interval_ledger[].time_averaged_scale_flux_mol_m2_s_by_phase.*": "mol/m^2/s",
            "interval_ledger[].aqueous_inventory_residual_mol_m_by_species.*": "mol/m",
        },
        assumptions=(
            "Caller supplies activity coefficients, dimensionless activity reference concentrations, natural-log solubility products, reaction formulae, and kinetic parameters with bound Evidence.",
            "The chosen power law acts on positive/negative log saturation driving force and is reevaluated from wall-cell concentrations during every BDF stage.",
            "Activity and solubility inputs are left-held by exact interval; radial diffusion supply, solid inventory and common geometry are updated within the bounded calculation.",
        ),
        source_ids=(KINETICS_SOURCE_ID, SUPPLY_SOURCE_ID),
        qualification="user_model",
    ),)
