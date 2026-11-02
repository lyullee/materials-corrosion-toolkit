"""Synthetic finite elastic-joint snapshot arithmetic and lineage boundaries."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import gasket_joint_load_history as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    return {'history_id':'synthetic','asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds','knots':[{'knot_index':index,'time_s':float(index*10),'load_state':{'initial_bolt_force_N':100.0,'bolt_stiffness_N_m':100.0,'clamped_stiffness_N_m':300.0,'external_separating_force_N':float(index*40),'free_clamped_minus_bolt_expansion_m':0.0,'linear_contact_applicability_reviewed':True}} for index in range(3)],'minimum_clamp_force_N':70.0,'ordered_time_basis_reviewed':True,'elastic_closed_contact_model_reviewed':True,'per_knot_preload_applicability_reviewed':True,'finite_snapshot_only_interpretation_reviewed':True}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('invalid contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/gasket_load_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.ElasticJointLoadHistoryRequest.model_json_schema()
    cls=module.ElasticJointLoadHistoryRequest;request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_elastic_joint_load_history(request);assert result.status=='computed'
    rows=result.values['joint_load_history'];assert [row['clamp_force_N'] for row in rows]==[100.0,70.0,40.0]
    assert [row['bolt_force_N'] for row in rows]==[100.0,110.0,120.0]
    assert result.values['first_supplied_snapshot_below_minimum_clamp_force']['knot_index']==2
    assert not result.values['crossing_time_interpolated'] and not result.values['threshold_is_seal_acceptance']
    for knot,row in zip(request.knots,rows,strict=True): assert row['knot_input_sha256']==canonical_digest(knot.model_dump(mode='json'))
    if task=='contracts':
        for change in ('bool-index','float-index','duplicate-time','order'):
            values=payload()
            if change=='bool-index': values['knots'][0]['knot_index']=False
            elif change=='float-index': values['knots'][0]['knot_index']=0.0
            elif change=='duplicate-time': values['knots'][1]['time_s']=0.0
            else: values['knots'].reverse()
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        thermal=payload();thermal['knots'][0]['load_state']['free_clamped_minus_bolt_expansion_m']=0.1
        shifted=module.evaluate_elastic_joint_load_history(cls.model_validate_json(json.dumps(thermal)))
        assert math.isclose(shifted.values['joint_load_history'][0]['thermal_preload_change_N'],7.5)
    else:
        values=payload();values['finite_snapshot_only_interpretation_reviewed']=False;assert module.evaluate_elastic_joint_load_history(cls.model_validate_json(json.dumps(values))).status=='needs_data'
        values=payload();values['knots'][2]['load_state']['external_separating_force_N']=200.0
        partial=module.evaluate_elastic_joint_load_history(cls.model_validate_json(json.dumps(values)))
        assert partial.status=='out_of_scope' and partial.values['failed_knot_index']==2 and len(partial.values['completed_knot_results'])==2
        registry=ModelRegistry();registry.register(module.specifications()[0]);context=RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds');assert registry.run(module.MODEL_ID,request,context).status=='computed'
        rejects(lambda:registry.run(module.MODEL_ID,request,RunContext(asset_id='wrong',location_id='synthetic',time_basis='elapsed_seconds')))
    return {'partition':task,'synthetic_two_spring_snapshot_reference':True,'strict_threshold_equality_not_event':True,'no_seal_probability_or_interpolated_crossing':True,'physical_gasket_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['contracts','scope-lineage'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
