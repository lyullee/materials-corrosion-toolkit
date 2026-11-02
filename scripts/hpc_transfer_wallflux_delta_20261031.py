"""Synthetic declared-composition and fixed-area flux adapter partitions."""
import argparse
import json
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from matintegrity.models import wco2_species_transfer as transfer
from matintegrity import electrochemical_wall_flux_schedule as wall
from matintegrity.contracts import canonical_digest,RunContext
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported input accepted')

def wall_payload():
    result={"model_id":"integration.electrochemical_partial_current_metal_loss","model_version":"synthetic","status":"computed","inputs":{},"values":{"reaction_to_metal_mapping":[{"reaction_id":"dissolve","metal_species_id":"M"}],"interval_metal_loss":[{"start_time_s":100.0,"end_time_s":110.0,"reaction_metal_loss":[{"reaction_id":"dissolve","anodic_metal_removal_mol":20.0,"exposed_area_m2":2.0}]},{"start_time_s":110.0,"end_time_s":130.0,"reaction_metal_loss":[{"reaction_id":"dissolve","anodic_metal_removal_mol":80.0,"exposed_area_m2":2.0}]}]},"units":{},"assumptions":[],"notes":["Synthetic ledger only; upstream electrochemical model not exercised."],"context":{"asset_id":"synthetic","location_id":"synthetic","time_basis":"elapsed_seconds"},"input_digest":"synthetic","source_ids":[],"qualification":"user_model","runtime":{}}
    from matintegrity.contracts import AssessmentResult
    model=AssessmentResult.model_validate_json(json.dumps(result))
    return {"metal_loss_result":model.model_dump(mode="json"),"metal_loss_result_sha256":canonical_digest(model.model_dump(mode="json")),"species_ids":["M","inert"],"cell_count":3,"local_average_flux_mapping_reviewed":True,"reaction_surface_area_is_comparable_across_selected_branches_reviewed":True,"source_clock_origin_rebasing_reviewed":True,"computational_use_authorized":True,"local_only_authorized":True}

def check(task):
    if task=="closure":
        evidence=[{"source_id":"synthetic","origin":"synthetic","citation":"Fabricated species handoff."}]
        payload={"upstream_species":[{"species_id":"A","charge_number":2,"element_counts":{"M":1}}],"downstream_species":[{"species_id":"B","charge_number":2,"element_counts":{"M":1}}],"transfers":[{"transfer_id":"rename","transfer_kind":"renamed","source_terms":[{"species_id":"A","coefficient":1}],"target_terms":[{"species_id":"B","coefficient":1}],"reviewed":True,"evidence":evidence}]}
        model=transfer.Wco2SpeciesTransferAuditRequest.model_validate_json(json.dumps(payload))
        assert transfer.audit_wco2_species_transfer(model).values["transfer_rules"][0]["element_charge_balanced"]
        for field,value in (("charge_number",1),("element_counts",{"M":2})):
            changed=json.loads(json.dumps(payload));changed["downstream_species"][0][field]=value
            rejects(lambda:transfer.Wco2SpeciesTransferAuditRequest.model_validate_json(json.dumps(changed)))
        for bad in (True,1.0,"1"):
            changed=json.loads(json.dumps(payload));changed["transfers"][0]["source_terms"][0]["coefficient"]=bad
            rejects(lambda:transfer.Wco2SpeciesTransferAuditRequest.model_validate_json(json.dumps(changed)))
        return {"declared_element_charge_closure":True,"strict_stoichiometry":True,"mechanism_inferred":False}
    values=wall_payload()
    request=wall.ElectrochemicalWallFluxScheduleRequest.model_validate_json(json.dumps(values))
    if task=="time-prefix":
        callback=wall.build_electrochemical_wall_flux_schedule(request)
        state=np.zeros((2,3))
        for time,rate in ((0.0,1.0),(9.999,1.0),(10.0,2.0),(30.0,2.0)):
            np.testing.assert_array_equal(callback(time,state,None),np.array([[rate]*3,[0.0]*3]))
        assert callback.source_clock_origin_s==100.0 and callback.interval_support_s==(0.0,30.0)
        for time in (-1e-8,30.0000001): rejects(lambda:callback(time,state,None))
        for status in ('out_of_scope','needs_data'):
            changed=wall_payload();changed['metal_loss_result']['status']=status
            rejects(lambda:wall.ElectrochemicalWallFluxScheduleRequest.model_validate_json(json.dumps(changed)))
        changed=wall_payload();changed['source_clock_origin_rebasing_reviewed']=False
        rejects(lambda:wall.ElectrochemicalWallFluxScheduleRequest.model_validate_json(json.dumps(changed)))
        return {"source_origin_rebased":True,"partition_boundary_and_final_endpoint":True,"incomplete_result_no_extrapolation":True,"upstream_solver_exercised":False}
    artifact=json.loads((ROOT/'metadata/transfer_wallflux_snapshot.json').read_text())
    assert artifact['source_rows']==artifact['package_rows']
    for module in (wall,transfer):
        spec=module.specifications()[0]
        assert artifact['schemas'][spec.model_id]==spec.input_type.model_json_schema()
    registry=ModelRegistry();registry.register(wall.specifications()[0])
    result=registry.run(wall.INTERFACE_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds'))
    assert result.status=='computed' and result.values['callback_builder_available']
    assert 'moving-boundary' in result.values['interpretation_limit']
    assert result.values['source_result_sha256']==request.metal_loss_result_sha256
    for flag in ('local_average_flux_mapping_reviewed','reaction_surface_area_is_comparable_across_selected_branches_reviewed'):
        changed=wall_payload();changed[flag]=False
        rejects(lambda:wall.ElectrochemicalWallFluxScheduleRequest.model_validate_json(json.dumps(changed)))
    return {'metadata_parity':True,'geometry_total_not_claimed':True,'area_mapping_reviews':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['closure','time-prefix','mapping-metadata'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details,'physical_validation':False},indent=2))
