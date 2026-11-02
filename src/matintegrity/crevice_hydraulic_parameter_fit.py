"""Group-separated fit of caller hydraulic resistance/inertance correction factors."""
from __future__ import annotations
import math
from typing import Literal
import numpy as np
from pydantic import Field, model_validator
from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .models.planar_slit_transient_hydraulic import PlanarSlitTransientHydraulicHistory
from .registry import ModelSpec

MODEL_ID="calibration.crevice_slit_hydraulic_law_parameters"
SOURCE_ID="caller_group_separated_transient_slit_flow_parameter_fit"

class HydraulicFlowObservationRun(Contract):
    run_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_state_id: str = Field(min_length=1)
    role: Literal["calibration","holdout"]
    hydraulic_request: PlanarSlitTransientHydraulicHistory
    observed_volumetric_flow_m3_s: tuple[float,...] = Field(min_length=2,max_length=100001)
    standard_uncertainty_m3_s: tuple[Positive,...] = Field(min_length=2,max_length=100001)
    observation_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence,...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_observation(self):
        if self.hydraulic_request.material_state_id != self.material_state_id:
            raise ValueError("observation material identity must match its hydraulic request")
        if len(self.observed_volumetric_flow_m3_s)!=len(self.hydraulic_request.time_s) or len(self.standard_uncertainty_m3_s)!=len(self.hydraulic_request.time_s):
            raise ValueError("observed flow and uncertainty must align with exact hydraulic time knots")
        if any(not math.isfinite(x) for x in self.observed_volumetric_flow_m3_s): raise ValueError("observed flow must be finite and signed")
        payload={"run_id":self.run_id,"independence_group_id":self.independence_group_id,"material_state_id":self.material_state_id,"time_s":self.hydraulic_request.time_s,"flow_m3_s":self.observed_volumetric_flow_m3_s,"uncertainty_m3_s":self.standard_uncertainty_m3_s}
        if canonical_digest(payload)!=self.observation_record_sha256 or not any(e.sha256==self.observation_record_sha256 for e in self.evidence): raise ValueError("flow observations require matching record digest Evidence")
        return self

class CreviceHydraulicParameterFitRequest(Contract):
    schema_version: Literal["matintegrity.crevice_hydraulic_parameter_fit.v1"]="matintegrity.crevice_hydraulic_parameter_fit.v1"
    assessment_id: str = Field(min_length=1)
    calibration_runs: tuple[HydraulicFlowObservationRun,...] = Field(min_length=2,max_length=100)
    holdout_runs: tuple[HydraulicFlowObservationRun,...] = Field(min_length=1,max_length=100)
    resistance_multiplier_bounds: tuple[Positive,Positive]=(0.1,10.0)
    inertance_multiplier_bounds: tuple[Positive,Positive]=(0.1,10.0)
    maximum_nfev: int=Field(default=2000,ge=10,le=100000)
    same_reduced_law_family_reviewed: bool
    calibration_holdout_independence_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_groups(self):
        if self.resistance_multiplier_bounds[1]<=self.resistance_multiplier_bounds[0] or self.inertance_multiplier_bounds[1]<=self.inertance_multiplier_bounds[0]: raise ValueError("parameter bounds must be strictly increasing")
        runs=(*self.calibration_runs,*self.holdout_runs)
        if len({r.run_id for r in runs})!=len(runs): raise ValueError("run IDs must be unique")
        if any(r.role!="calibration" for r in self.calibration_runs) or any(r.role!="holdout" for r in self.holdout_runs): raise ValueError("run role must match its declared partition")
        if {r.independence_group_id for r in self.calibration_runs}&{r.independence_group_id for r in self.holdout_runs}: raise ValueError("calibration and holdout independence groups must be disjoint")
        if len({r.independence_group_id for r in self.calibration_runs})<2: raise ValueError("at least two independent calibration groups are required")
        reference=runs[0].hydraulic_request
        for run in runs[1:]:
            candidate=run.hydraulic_request
            exact_fields=("physical_scope_id","time_basis","material_state_id","geometry_provider_id","geometry_provider_revision","pressure_provider_id","pressure_provider_revision","fluid_property_provider_id","fluid_property_provider_revision","cell_ids","cell_widths_m","transverse_width_m")
            if any(getattr(candidate,name)!=getattr(reference,name) for name in exact_fields): raise ValueError("all runs must share the same reviewed material/scope, clock basis, provider revisions and fixed axial grid")
        if any(r.hydraulic_request.hydraulic_parameter_fit_result_sha256 is not None or r.hydraulic_request.resistance_correction_multiplier!=1.0 or r.hydraulic_request.inertance_correction_multiplier!=1.0 for r in runs): raise ValueError("fit observations must be generated from the uncorrected baseline law")
        if not (self.same_reduced_law_family_reviewed and self.calibration_holdout_independence_reviewed and self.computational_use_authorized): raise ValueError("law applicability, partition independence and computational-use reviews are required")
        return self

def _predict(request: PlanarSlitTransientHydraulicHistory, resistance_multiplier: float, inertance_multiplier: float)->np.ndarray:
    q=float(request.initial_volumetric_flow_m3_s); output=[q]
    for k,(t0,t1,gaps,dp) in enumerate(zip(request.time_s[:-1],request.time_s[1:],request.aperture_by_interval_m,request.pressure_drop_by_interval_Pa,strict=True)):
        resistance=math.fsum(12.*request.dynamic_viscosity_Pa_s*length/(width*gap**3) for length,width,gap in zip(request.cell_widths_m,[request.transverse_width_m]*len(gaps),gaps,strict=True))*resistance_multiplier
        inertance=math.fsum(request.density_kg_m3*length/(width*gap) for length,width,gap in zip(request.cell_widths_m,[request.transverse_width_m]*len(gaps),gaps,strict=True))*inertance_multiplier
        if not (math.isfinite(resistance) and resistance>0 and math.isfinite(inertance) and inertance>0): raise ArithmeticError("nonfinite or nonpositive fitted hydraulic coefficients")
        rate=resistance/inertance; equilibrium=dp/resistance; q=equilibrium+(q-equilibrium)*math.exp(-rate*(t1-t0))
        if not math.isfinite(q): raise ArithmeticError("predicted flow left finite support")
        output.append(q)
    return np.asarray(output,dtype=float)

def fit_crevice_hydraulic_parameters(request: CreviceHydraulicParameterFitRequest)->Calculation:
    try:
        from scipy.optimize import least_squares
    except ImportError:
        return Calculation(status="needs_data", values={"reason":"optional_scipy_required_for_hydraulic_parameter_fit"})
    digest=canonical_digest(request.model_dump(mode="json")); runs=request.calibration_runs
    lo=np.log([request.resistance_multiplier_bounds[0],request.inertance_multiplier_bounds[0]])
    hi=np.log([request.resistance_multiplier_bounds[1],request.inertance_multiplier_bounds[1]])
    def residual(theta):
        r,i=np.exp(theta); return np.concatenate([(_predict(run.hydraulic_request,r,i)-np.asarray(run.observed_volumetric_flow_m3_s))/np.asarray(run.standard_uncertainty_m3_s) for run in runs])
    try:
        fit=least_squares(residual,np.clip(np.zeros(2),lo,hi),bounds=(lo,hi),max_nfev=request.maximum_nfev,method="trf",x_scale="jac")
        if not fit.success or not np.isfinite(fit.x).all() or np.linalg.matrix_rank(fit.jac)<2: raise ValueError("hydraulic correction factors are not identifiable or optimizer did not converge")
        multipliers=np.exp(fit.x); dof=max(1,len(fit.fun)-2); covariance=np.linalg.inv(fit.jac.T@fit.jac)*(float(fit.fun@fit.fun)/dof)
        calibration=[]
        for run in runs:
            predicted=_predict(run.hydraulic_request,*multipliers); residuals=predicted-np.asarray(run.observed_volumetric_flow_m3_s)
            calibration.append({"run_id":run.run_id,"independence_group_id":run.independence_group_id,"observed_flow_m3_s":list(run.observed_volumetric_flow_m3_s),"predicted_flow_m3_s":predicted.tolist(),"standardized_residual":(residuals/np.asarray(run.standard_uncertainty_m3_s)).tolist(),"observation_sha256":run.observation_record_sha256})
        holdout=[]
        for run in request.holdout_runs:
            predicted=_predict(run.hydraulic_request,*multipliers); residuals=predicted-np.asarray(run.observed_volumetric_flow_m3_s)
            holdout.append({"run_id":run.run_id,"independence_group_id":run.independence_group_id,"observed_flow_m3_s":list(run.observed_volumetric_flow_m3_s),"predicted_flow_m3_s":predicted.tolist(),"standardized_residual":(residuals/np.asarray(run.standard_uncertainty_m3_s)).tolist(),"observation_sha256":run.observation_record_sha256})
        all_requests=[r.hydraulic_request for r in request.calibration_runs]
        apertures=[x for req in all_requests for row in req.aperture_by_interval_m for x in row]
        pressures=[x for req in all_requests for x in req.pressure_drop_by_interval_Pa]
        durations=[b-a for req in all_requests for a,b in zip(req.time_s[:-1],req.time_s[1:],strict=True)]
        span=[req.time_s[-1]-req.time_s[0] for req in all_requests]
        observed_flows=[x for run in request.calibration_runs for x in run.observed_volumetric_flow_m3_s]
        support={"physical_scope_id":all_requests[0].physical_scope_id,"material_state_id":request.calibration_runs[0].material_state_id,"time_basis":all_requests[0].time_basis,"geometry_provider_id":all_requests[0].geometry_provider_id,"geometry_provider_revision":all_requests[0].geometry_provider_revision,"pressure_provider_id":all_requests[0].pressure_provider_id,"pressure_provider_revision":all_requests[0].pressure_provider_revision,"fluid_property_provider_id":all_requests[0].fluid_property_provider_id,"fluid_property_provider_revision":all_requests[0].fluid_property_provider_revision,"cell_ids":list(all_requests[0].cell_ids),"cell_widths_m":list(all_requests[0].cell_widths_m),"transverse_width_m":all_requests[0].transverse_width_m,"aperture_m_min":min(apertures),"aperture_m_max":max(apertures),"pressure_drop_Pa_min":min(pressures),"pressure_drop_Pa_max":max(pressures),"density_kg_m3_min":min(x.density_kg_m3 for x in all_requests),"density_kg_m3_max":max(x.density_kg_m3 for x in all_requests),"viscosity_Pa_s_min":min(x.dynamic_viscosity_Pa_s for x in all_requests),"viscosity_Pa_s_max":max(x.dynamic_viscosity_Pa_s for x in all_requests),"interval_duration_s_min":min(durations),"interval_duration_s_max":max(durations),"time_span_s_min":min(span),"time_span_s_max":max(span),"observed_flow_m3_s_min":min(observed_flows),"observed_flow_m3_s_max":max(observed_flows)}
        return Calculation(values={"model_id":MODEL_ID,"assessment_id":request.assessment_id,"input_sha256":digest,"calibration_group_ids":sorted({r.independence_group_id for r in runs}),"holdout_group_ids":sorted({r.independence_group_id for r in request.holdout_runs}),"resistance_multiplier":float(multipliers[0]),"inertance_multiplier":float(multipliers[1]),"log_parameter_covariance":covariance.tolist(),"weighted_calibration_rms":float(np.sqrt(np.mean(np.square(fit.fun)))),"calibration_predictions":calibration,"holdout_predictions":holdout,"calibration_support":support,"optimizer_nfev":int(fit.nfev),"optimizer_cost":float(fit.cost),"parameter_fit_state":"computed","qualification_claimed":False},notes=("Only the declared lumped resistance and inertance multipliers were fitted; pressure, aperture, density and viscosity remain caller inputs.","Independent holdout records are evaluated after fitting and do not participate in parameter estimation.","The result does not establish universal transferability, Navier-Stokes validity, moving-aperture feedback, corrosion kinetics or component qualification."))
    except (ArithmeticError,ValueError,np.linalg.LinAlgError,FloatingPointError) as exc:
        return Calculation(status="needs_data",values={"model_id":MODEL_ID,"assessment_id":request.assessment_id,"input_sha256":digest,"parameter_fit_state":"not_computed","reason":str(exc),"qualification_claimed":False})

def apply_hydraulic_parameter_fit(base_request: PlanarSlitTransientHydraulicHistory, fit_result: Calculation, fit_result_sha256: str, fit_evidence: Evidence, *, applicability_reviewed: bool)->PlanarSlitTransientHydraulicHistory:
    """Return a new hydraulic request with pinned fitted multipliers inside fit support."""
    if fit_result.model_id!=MODEL_ID or fit_result.status!="computed" or fit_result.values.get("parameter_fit_state")!="computed": raise ValueError("computed hydraulic law fit result is required")
    if canonical_digest(fit_result.model_dump(mode="json"))!=fit_result_sha256: raise ValueError("hydraulic fit result digest mismatch")
    if fit_evidence.source_id!=MODEL_ID or fit_evidence.sha256!=fit_result_sha256: raise ValueError("fit Evidence must pin the exact fit result")
    if not applicability_reviewed: raise ValueError("caller must review hydraulic fit applicability")
    support=fit_result.values["calibration_support"]
    for name in ("physical_scope_id","material_state_id","time_basis","geometry_provider_id","geometry_provider_revision","pressure_provider_id","pressure_provider_revision","fluid_property_provider_id","fluid_property_provider_revision"):
        if getattr(base_request,name)!=support[name]: raise ValueError(f"target hydraulic request {name} is outside fit applicability")
    if base_request.material_state_id!=support["material_state_id"]: raise ValueError("target hydraulic material identity differs from fit support")
    if list(base_request.cell_ids)!=support["cell_ids"] or list(base_request.cell_widths_m)!=support["cell_widths_m"] or base_request.transverse_width_m!=support["transverse_width_m"]: raise ValueError("target hydraulic geometry grid differs from fit support")
    checks=((base_request.initial_volumetric_flow_m3_s,support["observed_flow_m3_s_min"],support["observed_flow_m3_s_max"],"initial flow"),(min(x for row in base_request.aperture_by_interval_m for x in row),support["aperture_m_min"],support["aperture_m_max"],"aperture"),(max(x for row in base_request.aperture_by_interval_m for x in row),support["aperture_m_min"],support["aperture_m_max"],"aperture"),(base_request.density_kg_m3,support["density_kg_m3_min"],support["density_kg_m3_max"],"density"),(base_request.dynamic_viscosity_Pa_s,support["viscosity_Pa_s_min"],support["viscosity_Pa_s_max"],"viscosity"),(min(base_request.pressure_drop_by_interval_Pa),support["pressure_drop_Pa_min"],support["pressure_drop_Pa_max"],"pressure"),(max(base_request.pressure_drop_by_interval_Pa),support["pressure_drop_Pa_min"],support["pressure_drop_Pa_max"],"pressure"))
    if any(value<low or value>high for value,low,high,_ in checks): raise ValueError("target hydraulic request extrapolates beyond calibrated pressure/aperture/fluid support")
    durations=[b-a for a,b in zip(base_request.time_s[:-1],base_request.time_s[1:],strict=True)]
    target_span=base_request.time_s[-1]-base_request.time_s[0]
    if min(durations)<support["interval_duration_s_min"] or max(durations)>support["interval_duration_s_max"] or target_span<support["time_span_s_min"] or target_span>support["time_span_s_max"]: raise ValueError("target hydraulic clock extrapolates beyond fit support")
    payload=base_request.model_dump(mode="python")
    payload.update(resistance_correction_multiplier=fit_result.values["resistance_multiplier"],inertance_correction_multiplier=fit_result.values["inertance_multiplier"],hydraulic_parameter_fit_result_sha256=fit_result_sha256,hydraulic_parameter_fit_evidence=fit_evidence,hydraulic_parameter_fit_applicability_reviewed=True)
    return PlanarSlitTransientHydraulicHistory.model_validate(payload)

def specifications()->tuple[ModelSpec,...]:
    return (ModelSpec(model_id=MODEL_ID,input_type=CreviceHydraulicParameterFitRequest,evaluator=fit_crevice_hydraulic_parameters,units={"observed_volumetric_flow_m3_s[]":"m^3/s","standard_uncertainty_m3_s[]":"m^3/s","resistance_multiplier":"1","inertance_multiplier":"1","optimizer_nfev":"1"},assumptions=("Fit only two positive global correction multipliers on the caller-declared reduced lumped slit law; each observation record is digest-pinned.","Split complete independent groups before fit; holdout groups are predicted after fitting and are never included in the objective.","Weighted least squares uses caller measurement standard uncertainties; covariance is local linearized covariance and is conditional on the chosen model and declared data."),source_ids=(SOURCE_ID,"caller_lumped_slit_inertance_resistance"),version="0.1.0",qualification="user_model"),)
