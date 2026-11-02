"""Caller cycle-group workflow with mocked life evaluation and Miner execution."""
import argparse,json
from pathlib import Path
from pydantic import ValidationError
from matintegrity import ince_glinka_gsa_miner_campaign as module
from matintegrity.contracts import Calculation,canonical_digest
ROOT=Path(__file__).resolve().parents[1]

def payload():
    source=(ROOT/'examples/ince_glinka_gsa.py').read_text();namespace={};exec(source.split('result = ince_glinka_gsa_parameter(request)')[0],namespace)
    calculation=namespace['request'].model_dump(mode='json')
    points=[{'point_id':str(i),'gsa_parameter':value,'cycles_to_failure':life,'source_record_id':'curve','evidence':[{'source_id':'curve','origin':'synthetic','citation':'Fabricated shared monotone curve.'}]} for i,(value,life) in enumerate(((1e-4,1000.0),(1e-2,100.0)))]
    groups=[]
    for i,count in enumerate((10.0,20.0)):
        calc=dict(calculation,assessment_id='gsa-'+str(i));groups.append({'cycle_group_id':'group-'+str(i),'allocated_cycle_count':count,'life_request':{'calculation':calc,'calibration_id':'synthetic','calibration_material_condition_id':calc['material_condition_id'],'cycles_definition':'caller full cycles','curve_points':points,'interpolation_reviewed':True,'repeated_cycle_assumption_reviewed':True,'material_condition_and_curve_applicability_reviewed':True}})
    return {'campaign_id':'synthetic','cycle_groups':groups,'declared_damage_limit':1.0,'cycle_group_count_and_identity_reviewed':True,'curve_and_material_consistency_reviewed':True,'linear_miner_rule_reviewed':True,'sequence_effects_excluded_reviewed':True,'computational_use_authorized':True}

def check(task):
    artifact=json.loads((ROOT/'metadata/gsa_miner_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.InceGlinkaGSAMinerCampaign.model_json_schema()
    calls=[];miner_calls=[]
    def life(request):
        index=int(request.calculation.assessment_id[-1]);calls.append(index)
        return Calculation(status='needs_data',values={'synthetic_failure':True}) if task=='all-groups-before-damage' and index==1 else Calculation(values={'cycles_to_failure':100.0*(index+1)})
    def miner(request):
        assert calls==[0,1] and list(request.cycle_counts)==[10.0,20.0] and list(request.cycles_to_failure)==[100.0,200.0]
        miner_calls.append(True);return Calculation(values={'damage':0.2,'damage_margin':0.8})
    module.evaluate_ince_glinka_gsa_curve_life=life;module.miner_damage=miner
    cls=module.InceGlinkaGSAMinerCampaign;request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_ince_glinka_gsa_miner_campaign(request)
    if task=='all-groups-before-damage': assert result.status=='needs_data' and result.values['completed_cycle_group_count']==1 and result.values['total_miner_damage'] is None and miner_calls==[]
    else:
        assert result.status=='computed' and result.values['total_miner_damage']==0.2 and miner_calls==[True]
        assert result.values['input_sha256']==canonical_digest(request.model_dump(mode='json'))
        values=payload();values['cycle_groups'][1]['life_request']['calibration_id']='other'
        try: cls.model_validate_json(json.dumps(values))
        except ValidationError: pass
        else: raise AssertionError('incomparable life curve accepted')
    return {'partition':task,'mock_life_and_Miner_workflow_only':True,'no_GSA_solver_or_fatigue_life_validation':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['all-groups-before-damage','curve-scope-lineage'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(a.task)
    except Exception as e: a.output.write_text(json.dumps({'status':'failed','error':str(e)},indent=2));raise
    a.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
