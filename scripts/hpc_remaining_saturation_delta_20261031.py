"""Synthetic lineage/boundary tests for two new adapters and strict JSON fixes."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity.contracts import AssessmentResult, Evidence, RunContext, canonical_digest
from matintegrity.ti12mo5zr_mass_balance import Ti12Mo5ZrMassBalanceRequest, Ti12Mo5ZrMassBalanceResult, Ti12Mo5ZrPenetrationPoint
from matintegrity import ti12mo5zr_remaining_thickness as thickness
from matintegrity import saturation_history_events as events

ROOT=Path(__file__).resolve().parents[1]


def assessment(model,inputs,values,source_ids=("synthetic",)):
    context=RunContext(asset_id="synthetic",location_id="synthetic",time_basis="elapsed_seconds")
    digest=canonical_digest({"model_id":model,"model_version":"1.0.0","inputs":inputs,"context":context.model_dump(mode="json")})
    return AssessmentResult(model_id=model,model_version="1.0.0",status="computed",inputs=inputs,values=values,units={},assumptions=("Synthetic receipt only; no archive or physical validation.",),notes=(),context=context,input_digest=digest,source_ids=source_ids,qualification="user_model",runtime={})


def remaining_fixture():
    evidence=Evidence(source_id="synthetic-density",origin="synthetic",citation="Fabricated density fixture only.",sha256="a"*64,license_id="CC0-1.0")
    inputs={"local_archive_path":"not-opened/zenodo_APSUC_2024.zip","density_kg_m3":4000.0,"density_evidence":evidence.model_dump(mode="json"),"alloy_label":"Ti-12Mo-5Zr","analyzed_elements":["Ti","Mo","Zr"]}
    for key in ("computational_use_authorized","local_only_authorized","source_time_axis_is_valid_for_interval_integration","provider_positive_rate_means_outward_loss_reviewed","analyzed_element_coverage_is_complete_for_this_conversion","uniform_area_and_density_equivalent_penetration_reviewed","linear_interpolation_between_time_rows_reviewed"): inputs[key]=True
    inputs=Ti12Mo5ZrMassBalanceRequest.model_validate_json(json.dumps(inputs)).model_dump(mode="json")
    points=[]
    for index,(positive,negative,net,velocity) in enumerate(((0.0,0.0,0.0,1e-6),(0.25e-6,-0.25e-6,0.0,-1e-6),(0.25e-6,-1.25e-6,-1e-6,-1e-6))):
        points.append(Ti12Mo5ZrPenetrationPoint(source_row_number=index+2,source_row_sha256=str(index)*64,source_member_sha256=thickness.PROVIDER_MEMBER_SHA256,provider_time_s=float(index),elemental_mass_flux_kg_m2_s={"Ti":velocity*4000.0,"Mo":0.0,"Zr":0.0},signed_net_mass_flux_kg_m2_s=velocity*4000.0,signed_equivalent_penetration_velocity_m_s=velocity,cumulative_positive_penetration_m=positive,cumulative_negative_penetration_m=negative,cumulative_signed_net_penetration_m=net))
    mass=Ti12Mo5ZrMassBalanceResult(source_member_sha256=thickness.PROVIDER_MEMBER_SHA256,exact_request_sha256=canonical_digest(inputs),exact_input_rows_sha256="b"*64,density_kg_m3=4000.0,density_evidence=evidence,density_evidence_sha256=canonical_digest(evidence.model_dump(mode="json")),analyzed_elements=("Ti","Mo","Zr"),input_row_count=3,first_provider_time_s=0.0,last_provider_time_s=2.0,positive_cumulative_penetration_m=0.25e-6,negative_cumulative_penetration_m=-1.25e-6,signed_net_integrated_penetration_m=-1e-6,points=tuple(points))
    source=assessment(thickness.SOURCE_MODEL_ID,inputs,{"mass_balance":mass.model_dump(mode="json")},(thickness.DATASET_ID,"caller-density-evidence"))
    return thickness.RemainingThicknessRequest(assessment=source,expected_assessment_input_digest=source.input_digest,expected_assessment_result_digest=thickness.assessment_result_digest(source),expected_mass_balance_result_digest=thickness.mass_balance_result_digest(mass),expected_run_context=source.context,baseline_thickness_m=1e-3,baseline_thickness_evidence=Evidence(source_id="synthetic-baseline",origin="synthetic",citation="Fabricated baseline only.",sha256="c"*64),uniform_area_basis_authorized=True,density_material_applicability_authorized=True,computational_use_authorized=True,local_only_authorized=True)


def positive_and_json():
    request=remaining_fixture()
    result=thickness.build_remaining_thickness_history(request)
    assert [row.provider_time_s for row in result.knots]==[0.0,1.0,2.0]
    assert result.knots[1].remaining_thickness_m==result.knots[2].remaining_thickness_m
    assert math.isclose(result.knots[-1].remaining_thickness_m,1e-3-0.25e-6,abs_tol=1e-15)
    assert result.negative_penetration_restores_thickness is False
    from hpc_cycle_feature_handoff_delta_20261031 import fixture
    from matintegrity.multiaxial_cycle_block_feature_handoff import bind_cycle_features_to_adaptive_request
    _,receipt,target=fixture()
    bound=bind_cycle_features_to_adaptive_request(target,receipt)
    assert isinstance(bound.blocks,tuple) and isinstance(bound.blocks[0].parameters,tuple)
    assert len(bound.blocks)==2
    return {"exact_knots_and_positive_only_loss":True,"negative_ledger_does_not_restore_thickness":True,"strict_JSON_mass_balance_and_integer_block_reconstruction":True,"synthetic_receipts_not_archive_validation":True}


def remaining_failures():
    request=remaining_fixture()
    # Establish the valid path so a generic parse error cannot mask boundary checks.
    thickness.build_remaining_thickness_history(request)
    rejected=[]
    for name,change in (("result-digest",{"expected_assessment_result_digest":"f"*64}),("baseline-boundary",{"baseline_thickness_m":1e-7}),("context",{"expected_run_context":{"asset_id":"wrong","location_id":"synthetic","time_basis":"elapsed_seconds"}})):
        values=request.model_dump(mode="json")|change
        try: thickness.build_remaining_thickness_history(thickness.RemainingThicknessRequest.model_validate_json(json.dumps(values)))
        except ValueError: rejected.append(name)
        else: raise AssertionError("invalid lineage/boundary accepted: "+name)
    values=request.model_dump(mode="json")
    values["assessment"]["values"]["mass_balance"]["source_member_sha256"]="e"*64
    modified=AssessmentResult.model_validate_json(json.dumps(values["assessment"]))
    values["expected_assessment_result_digest"]=canonical_digest(modified.model_dump(mode="json"))
    values["expected_mass_balance_result_digest"]=canonical_digest(modified.values["mass_balance"])
    try: thickness.build_remaining_thickness_history(thickness.RemainingThicknessRequest.model_validate_json(json.dumps(values)))
    except ValueError as failure:
        assert "pinned files" in str(failure)
        rejected.append("self-consistent-wrong-member-material-boundary")
    else: raise AssertionError("wrong material/member accepted after digest repinning")
    values=request.model_dump(mode="json")
    values["density_material_applicability_authorized"]=False
    try: thickness.RemainingThicknessRequest.model_validate_json(json.dumps(values))
    except ValidationError: rejected.append("material-applicability-authorization")
    else: raise AssertionError("missing material applicability authorization accepted")
    return {"rejected":rejected}


def saturation_fixture(values=None):
    times=[0.0,2.0,4.0]
    if values is None:
        values={"history_id":"synthetic-history","times_s":times,"saturation_history":[{"time_s":time,"status":"computed","screen":{"values":{"candidate_results":[{"solid_id":"A","log10_saturation_ratio":level},{"solid_id":"B","log10_saturation_ratio":10.0}]}}} for time,level in zip(times,(-1.0,1.0,-1.0),strict=True)]}
    source=assessment("integration.aqueous_vant_hoff_saturation_history",{"history_id":"synthetic-history"},values)
    return events.SaturationHistoryAssessmentBinding(saturation_assessment=source,expected_assessment_result_sha256=canonical_digest(source.model_dump(mode="json")),solid_id="A",consistent_solid_and_standard_state_reviewed=True,time_basis_and_order_reviewed=True,piecewise_linear_interpolation_reviewed=True,computational_use_authorized=True)


def saturation_binding():
    request=saturation_fixture()
    result=events.bind_vant_hoff_saturation_events(request)
    assert result.status=="computed"
    audit=result.values["event_audit"]["values"]
    assert audit["crossing_times_s"]==[1.0,3.0] and audit["above_threshold_duration_s"]==2.0
    alternative=request.model_dump(mode="json")
    alternative["solid_id"]="B"
    selected_b=events.bind_vant_hoff_saturation_events(events.SaturationHistoryAssessmentBinding.model_validate_json(json.dumps(alternative)))
    assert selected_b.status=="computed" and selected_b.values["event_audit"]["values"]["above_threshold_duration_s"]==4.0
    assert selected_b.values["event_request_sha256"]!=result.values["event_request_sha256"]
    assert result.values["upstream_saturation_knots_used"]==[{"time_s":0.0,"log10_saturation_ratio":-1.0},{"time_s":2.0,"log10_saturation_ratio":1.0},{"time_s":4.0,"log10_saturation_ratio":-1.0}]
    rejected=[]
    for name in ("missing-candidate","duplicate-candidate","time-mismatch"):
        values=json.loads(json.dumps(request.saturation_assessment.values))
        row=values["saturation_history"][1]
        candidates=row["screen"]["values"]["candidate_results"]
        if name=="missing-candidate": candidates.pop(0)
        elif name=="duplicate-candidate": candidates.append(dict(candidates[0]))
        else: row["time_s"]=2.0001
        checked=events.bind_vant_hoff_saturation_events(saturation_fixture(values))
        assert checked.status!="computed",name
        rejected.append(name)
    values=request.model_dump(mode="json")
    values["expected_assessment_result_sha256"]="f"*64
    assert events.bind_vant_hoff_saturation_events(events.SaturationHistoryAssessmentBinding.model_validate_json(json.dumps(values))).status=="needs_data"
    return {"exact_candidate_times_and_threshold":True,"rejected_binding_paths":rejected+["result-digest"],"chemistry_or_phase_calculation_performed":False}


def metadata():
    artifact=json.loads((ROOT/"metadata/remaining_saturation_snapshot.json").read_text(encoding="utf-8"))
    contracts=(thickness.RemainingThicknessRequest,thickness.RemainingThicknessKnot,thickness.RemainingThicknessHistory,events.SaturationHistoryAssessmentBinding)
    for contract in contracts: assert artifact["schemas"][contract.__name__]==contract.model_json_schema()
    assert artifact["source_catalogs"]==artifact["package_catalogs"]
    assert not (ROOT/"data/raw").exists()
    return {"targeted_schema_and_source_package_parity":True,"raw_source_opened":False}


def main():
    tasks={"positive-json":positive_and_json,"remaining-failures":remaining_failures,"saturation-binding":saturation_binding,"metadata":metadata}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"synthetic lineage/strict-contract checks only; no raw archive or physical validation"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
