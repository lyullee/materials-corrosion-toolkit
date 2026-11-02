"""Digest-bound inertance flow schedule and upwind component advection primitives."""
from __future__ import annotations
import math
from typing import Sequence, TYPE_CHECKING
import numpy as np
from pydantic import Field, model_validator
from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .models.planar_slit_transient_hydraulic import PlanarSlitTransientHydraulicHistory
if TYPE_CHECKING:
    from .crevice_component_state_bdf import CreviceComponentStateBDFRequest, ConservedAqueousComponent

class CreviceHydraulicComponentAdvection(Contract):
    """Validated exact hydraulic interval solution plus caller inlet compositions."""
    schema_version: str = "matintegrity.crevice_hydraulic_component_advection.v1"
    assessment_id: str = Field(min_length=1)
    time_s: tuple[float,...] = Field(min_length=2,max_length=500)
    cell_ids: tuple[str,...] = Field(min_length=2,max_length=300)
    cell_solution_volume_L: tuple[Positive,...] = Field(min_length=2,max_length=300)
    species_order: tuple[str,...] = Field(min_length=2,max_length=100)
    species_charge_numbers: tuple[int,...] = Field(min_length=2,max_length=100)
    hydraulic_request: PlanarSlitTransientHydraulicHistory
    hydraulic_result: Calculation
    hydraulic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    left_boundary_species_concentration_mol_m3_by_knot: tuple[tuple[float,...],...] = Field(min_length=2,max_length=500)
    right_boundary_species_concentration_mol_m3_by_knot: tuple[tuple[float,...],...] = Field(min_length=2,max_length=500)
    boundary_species_order: tuple[str,...] = Field(min_length=2,max_length=100)
    boundary_schedule_evidence: tuple[Evidence,...] = Field(min_length=1)
    boundary_schedule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_concentration_electroneutrality_reviewed: bool
    fixed_geometry_flow_transport_reviewed: bool
    computational_use_authorized: bool
    maximum_abs_flow_m3_s: Positive

    @model_validator(mode="after")
    def validate_bindings(self):
        hreq,hresult=self.hydraulic_request,self.hydraulic_result
        if hresult.status!="computed" or hresult.model_id!="corrosion.planar_slit_transient_hydraulic_history": raise ValueError("committed transient planar-slit hydraulic result required")
        if canonical_digest(hresult.model_dump(mode="json"))!=self.hydraulic_result_sha256: raise ValueError("hydraulic result digest mismatch")
        if hresult.values.get("input_sha256")!=canonical_digest(hreq.model_dump(mode="json")): raise ValueError("hydraulic result/request digest mismatch")
        if tuple(hreq.time_s)!=self.time_s or tuple(hresult.values.get("time_s",()))!=self.time_s: raise ValueError("hydraulic and BDF clocks must match exactly")
        if tuple(hreq.cell_ids)!=self.cell_ids: raise ValueError("ordered hydraulic cell IDs must match BDF cells")
        if len(self.cell_solution_volume_L)!=len(self.cell_ids) or len(self.species_order)!=len(self.species_charge_numbers): raise ValueError("BDF geometry/species metadata shape mismatch")
        if self.boundary_species_order!=self.species_order or len(set(self.species_order))!=len(self.species_order): raise ValueError("boundary species ordering must exactly match BDF chemistry")
        for side in (self.left_boundary_species_concentration_mol_m3_by_knot,self.right_boundary_species_concentration_mol_m3_by_knot):
            if len(side)!=len(self.time_s) or any(len(row)!=len(self.species_order) for row in side): raise ValueError("boundary concentrations must cover every time and species")
            for row in side:
                if any(not math.isfinite(x) or x<0 for x in row): raise ValueError("boundary concentrations must be finite and nonnegative")
                charge=math.fsum(z*c for z,c in zip(self.species_charge_numbers,row,strict=True)); scale=max(1.,math.fsum(abs(z*c) for z,c in zip(self.species_charge_numbers,row,strict=True)))
                if abs(charge)>1e-10*scale: raise ValueError("each boundary composition must be electroneutral")
        digest=canonical_digest({"time_s":self.time_s,"species_order":self.species_order,"left":self.left_boundary_species_concentration_mol_m3_by_knot,"right":self.right_boundary_species_concentration_mol_m3_by_knot})
        if digest!=self.boundary_schedule_sha256 or not any(row.sha256==digest for row in self.boundary_schedule_evidence): raise ValueError("boundary schedule digest must be pinned by matching Evidence")
        if not (self.boundary_concentration_electroneutrality_reviewed and self.fixed_geometry_flow_transport_reviewed and self.computational_use_authorized): raise ValueError("boundary, fixed-geometry and computational reviews required")
        if any(tuple(row)!=tuple(hreq.aperture_by_interval_m[0]) for row in hreq.aperture_by_interval_m[1:]): raise ValueError("moving aperture is outside this fixed-volume BDF coupling")
        for i,(vol,gap,length) in enumerate(zip(self.cell_solution_volume_L,hreq.aperture_by_interval_m[0],hreq.cell_widths_m,strict=True)):
            geom=length*hreq.transverse_width_m*gap*1000.
            if not math.isclose(geom,vol,rel_tol=1e-8,abs_tol=1e-12): raise ValueError(f"BDF/hydraulic cell volume mismatch at cell {i}")
        q=hresult.values.get("volumetric_flow_history_m3_s",())
        if len(q)!=len(self.time_s) or any(not math.isfinite(x) or abs(x)>self.maximum_abs_flow_m3_s for x in q): raise ValueError("hydraulic flow is missing or exceeds the caller bound")
        return self

def bind_crevice_hydraulic_component_advection(bdf_request, hydraulic_request, hydraulic_result, hydraulic_result_sha256: str, left_boundary, right_boundary, boundary_evidence, *, reviewed: bool, authorized: bool, maximum_abs_flow_m3_s: float):
    """Create the digest-pinned schedule after matching it to an existing BDF request."""
    from .crevice_component_state_bdf import CreviceComponentStateBDFRequest
    bdf=bdf_request if isinstance(bdf_request,CreviceComponentStateBDFRequest) else CreviceComponentStateBDFRequest.model_validate(bdf_request)
    species=bdf.cells[0].aqueous_activity_request.system.species
    payload={"time_s":bdf.time_s,"species_order":tuple(x.species_id for x in species),"left":left_boundary,"right":right_boundary}
    digest=canonical_digest(payload)
    return CreviceHydraulicComponentAdvection(assessment_id=bdf.assessment_id,time_s=bdf.time_s,cell_ids=tuple(x.cell_id for x in bdf.cells),cell_solution_volume_L=tuple(x.solution_volume_L for x in bdf.cells),species_order=tuple(x.species_id for x in species),species_charge_numbers=tuple(x.charge_number for x in species),hydraulic_request=hydraulic_request,hydraulic_result=hydraulic_result,hydraulic_result_sha256=hydraulic_result_sha256,left_boundary_species_concentration_mol_m3_by_knot=left_boundary,right_boundary_species_concentration_mol_m3_by_knot=right_boundary,boundary_species_order=tuple(x.species_id for x in species),boundary_schedule_evidence=boundary_evidence,boundary_schedule_sha256=digest,boundary_concentration_electroneutrality_reviewed=reviewed,fixed_geometry_flow_transport_reviewed=reviewed,computational_use_authorized=authorized,maximum_abs_flow_m3_s=maximum_abs_flow_m3_s)

def hydraulic_flow_at_time(binding: CreviceHydraulicComponentAdvection,time_s: float)->float:
    if not math.isfinite(time_s) or time_s<binding.time_s[0] or time_s>binding.time_s[-1]: raise ValueError("time outside hydraulic support")
    i=min(len(binding.time_s)-2,max(0,int(np.searchsorted(binding.time_s,time_s,side="right")-1)))
    if time_s==binding.time_s[-1]: return float(binding.hydraulic_result.values["volumetric_flow_history_m3_s"][-1])
    row=binding.hydraulic_result.values["interval_results"][i]; dt=time_s-float(row["start_time_s"])
    q=float(row["equilibrium_volumetric_flow_m3_s"])+(float(row["start_volumetric_flow_m3_s"])-float(row["equilibrium_volumetric_flow_m3_s"]))*math.exp(-float(row["momentum_relaxation_rate_s_inv"])*dt)
    if not math.isfinite(q) or abs(q)>binding.maximum_abs_flow_m3_s: raise ArithmeticError("hydraulic flow exceeded declared bound")
    return q

def component_advection_face_rates_mol_s(binding: CreviceHydraulicComponentAdvection,time_s: float,concentration_mol_m3_by_cell_and_species: Sequence[Sequence[float]],components)->np.ndarray:
    nc=len(binding.cell_ids); ns=len(binding.species_order); c=np.asarray(concentration_mol_m3_by_cell_and_species,dtype=float)
    if c.shape!=(nc,ns) or not np.isfinite(c).all() or np.any(c<0): raise ValueError("invalid BDF stage species concentration matrix")
    q=hydraulic_flow_at_time(binding,time_s); rates=np.zeros((len(components),nc+1),dtype=float)
    if q==0.: return rates
    i=min(len(binding.time_s)-2,max(0,int(np.searchsorted(binding.time_s,time_s,side="right")-1))); f=(time_s-binding.time_s[i])/(binding.time_s[i+1]-binding.time_s[i])
    left=np.asarray(binding.left_boundary_species_concentration_mol_m3_by_knot[i])*(1-f)+np.asarray(binding.left_boundary_species_concentration_mol_m3_by_knot[i+1])*f
    right=np.asarray(binding.right_boundary_species_concentration_mol_m3_by_knot[i])*(1-f)+np.asarray(binding.right_boundary_species_concentration_mol_m3_by_knot[i+1])*f
    for face in range(nc+1):
        up=left if face==0 and q>0 else right if face==nc and q<0 else c[face] if face<nc and q<0 else c[face-1] if face>0 else left
        flux=q*up
        for k,comp in enumerate(components):
            coeff={x.species_id:x.coefficient for x in comp.species_coefficients}
            rates[k,face]=math.fsum(coeff.get(sid,0.)*flux[j] for j,sid in enumerate(binding.species_order))
    if not np.isfinite(rates).all(): raise ArithmeticError("nonfinite component advection rates")
    return rates

def boundary_advection_reservoir_rates(binding: CreviceHydraulicComponentAdvection,time_s: float,concentration_mol_m3_by_cell_and_species: Sequence[Sequence[float]],species_elemental_composition: dict[str,dict[str,float]],components):
    """Return left/right external reservoir component, element, charge rates."""
    c=np.asarray(concentration_mol_m3_by_cell_and_species,dtype=float)
    q=hydraulic_flow_at_time(binding,time_s); nc=len(binding.cell_ids)
    if c.shape!=(nc,len(binding.species_order)) or not np.isfinite(c).all(): raise ValueError("invalid concentration for boundary ledger")
    i=min(len(binding.time_s)-2,max(0,int(np.searchsorted(binding.time_s,time_s,side="right")-1))); f=(time_s-binding.time_s[i])/(binding.time_s[i+1]-binding.time_s[i])
    left=np.asarray(binding.left_boundary_species_concentration_mol_m3_by_knot[i])*(1-f)+np.asarray(binding.left_boundary_species_concentration_mol_m3_by_knot[i+1])*f
    right=np.asarray(binding.right_boundary_species_concentration_mol_m3_by_knot[i])*(1-f)+np.asarray(binding.right_boundary_species_concentration_mol_m3_by_knot[i+1])*f
    inlet_left=left if q>=0 else c[0]; inlet_right=c[-1] if q>=0 else right
    sys_left=q*inlet_left; sys_right=q*inlet_right
    result=[]
    for sign,flux in ((-1.,sys_left),(1.,sys_right)):
        comp_rates={comp.component_id:sign*math.fsum(({x.species_id:x.coefficient for x in comp.species_coefficients}).get(sid,0.)*flux[j] for j,sid in enumerate(binding.species_order)) for comp in components}
        elems={e:0. for formula in species_elemental_composition.values() for e in formula}
        charge=0.
        for j,sid in enumerate(binding.species_order):
            charge+=sign*flux[j]*binding.species_charge_numbers[j]
            for e,n in species_elemental_composition[sid].items(): elems[e]+=sign*flux[j]*n
        result.append((comp_rates,elems,charge))
    return result[0],result[1]
