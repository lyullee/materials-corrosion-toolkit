"""Incremental Ksp per-record review gate; no screening/kinetics may be invoked."""
import argparse,json
from pathlib import Path
import hpc_carbonate_scale_handoff_delta_20261031 as fixture
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def check(task):
    module=fixture.module;artifact=json.loads((ROOT/'metadata/carbonate_scale_handoff_snapshot.json').read_text());assert artifact['schema']==module.FixedFugacityCarbonateScaleKinetics.model_json_schema();assert artifact['source_rows']==artifact['package_rows']
    calls=[]
    def forbidden(*args,**kwargs): calls.append('called');raise AssertionError('downstream invoked before per-record review gate')
    module.aqueous_saturation_screen=forbidden;module.caller_surface_scale_kinetics=forbidden
    selected=(0,) if task=='record-temperature-review-gate' else (1,)
    for index in selected:
        values=fixture.payload();values['knots'][index]['solubility_product']['temperature_applicability_reviewed']=False
        if task=='fail-closed-before-kinetics': values['fixed_fugacity_carbonate_history']['values']['co3_mol_L_history'][0]=0.0;values['fixed_fugacity_carbonate_history_sha256']=fixture.canonical_digest(values['fixed_fugacity_carbonate_history'])
        request=module.FixedFugacityCarbonateScaleKinetics.model_validate_json(json.dumps(values));registry=ModelRegistry();registry.register(module.specifications()[0]);result=registry.run(module.specifications()[0].model_id,request,request.fixed_fugacity_carbonate_history.context)
        assert result.status=='needs_data' and result.values['completed_saturation_knot_count']==0 and result.values['saturation_knot_results']==[] and calls==[]
        missing=result.values['missing_ksp_temperature_applicability_reviews'];assert len(missing)==1 and missing[0]['knot_index']==index and missing[0]['solubility_record_id']=='ksp'
    return {'partition':task,'per_record_review_false_blocks_before_all_downstream_calls':True,'synthetic_only':True,'actual_saturation_kinetics_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['record-temperature-review-gate','fail-closed-before-kinetics'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error: args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
