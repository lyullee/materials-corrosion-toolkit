"""Finite linear-rate integral/reference and scope contracts on fabricated inputs."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import corrosion_rate_history as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    rate_evidence=[{'source_id':'synthetic-rate','origin':'synthetic','citation':'Fabricated rate knots only.'}]
    return {'history_id':'synthetic','asset_id':'synthetic','location_id':'synthetic','material_id':'synthetic','material_condition_id':'synthetic','physical_scope_id':'synthetic','time_basis':'elapsed_seconds','knots':[{'knot_index':i,'time_s':float(i*10),'corrosion_rate_m_s':rate,'evidence':rate_evidence} for i,rate in enumerate((1e-4,3e-4,1e-4))],'baseline_thickness_m':0.01,'baseline_evidence':{'source_id':'synthetic-measurement-shape','origin':'measured','citation':'Fabricated measured-shaped descriptor for contract testing.'},'required_thickness_m':0.009,'required_thickness_evidence':{'source_id':'synthetic-limit','origin':'user_declared','citation':'Fabricated threshold.'},'ordered_history_reviewed':True,'rate_source_mapping_reviewed':True,'piecewise_linear_rate_reconstruction_reviewed':True,'uniform_area_average_loss_reviewed':True,'material_condition_and_location_reviewed':True,'finite_support_no_extrapolation_reviewed':True}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('invalid history contract accepted')

def check(task):
    cls=module.CorrosionRateThicknessHistoryRequest
    artifact=json.loads((ROOT/'metadata/rate_history_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'] and artifact['schema']==cls.model_json_schema()
    request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_corrosion_rate_thickness_history(request);assert result.status=='computed'
    assert math.isclose(result.values['cumulative_wall_loss_m'],0.004,abs_tol=1e-15) and math.isclose(result.values['remaining_thickness_m'],0.006,abs_tol=1e-15)
    crossing=result.values['first_required_thickness_crossing'];needed=request.baseline_thickness_m-request.required_thickness_m
    reference=2*needed/(1e-4+math.sqrt(1e-8+4e-5*needed))
    assert math.isclose(crossing['time_estimate_s'],reference,abs_tol=2e-12)
    assert crossing['time_lower_s']<=crossing['time_upper_s'] and crossing['time_upper_s']-crossing['time_lower_s']<1e-12
    assert result.values['support_end_s']==20.0 and not result.values['extrapolation_performed'] and not result.values['probability_inferred']
    assert result.values['ordered_knot_digests']==[canonical_digest(k.model_dump(mode='json')) for k in request.knots]
    if task=='integral-contract':
        for change in ('index','zero-start','duplicate-time','baseline-origin'):
            values=payload()
            if change=='index': values['knots'][0]['knot_index']=False
            elif change=='zero-start': values['knots'][0]['time_s']=1.0
            elif change=='duplicate-time': values['knots'][1]['time_s']=0.0
            else: values['baseline_evidence']['origin']='synthetic'
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        values=payload()
        for knot in values['knots']: knot['corrosion_rate_m_s']=0.0
        zero=module.evaluate_corrosion_rate_thickness_history(cls.model_validate_json(json.dumps(values)));assert zero.values['cumulative_wall_loss_m']==0.0 and zero.values['first_required_thickness_crossing'] is None
    else:
        values=payload();values['piecewise_linear_rate_reconstruction_reviewed']=False;assert module.evaluate_corrosion_rate_thickness_history(cls.model_validate_json(json.dumps(values))).status=='needs_data'
        values=payload();values['knots'][2]['corrosion_rate_m_s']=1.0;partial=module.evaluate_corrosion_rate_thickness_history(cls.model_validate_json(json.dumps(values)))
        assert partial.status=='out_of_scope' and len(partial.values['completed_intervals'])==1 and partial.values['failed_interval_index']==1
        registry=ModelRegistry();registry.register(module.specifications()[0]);assert registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds')).status=='computed'
        rejects(lambda:registry.run(module.MODEL_ID,request,RunContext(asset_id='other',location_id='synthetic',time_basis='elapsed_seconds')))
    return {'partition':task,'independent_linear_rate_quadratic_crossing_reference':True,'finite_support_and_source_lineage':True,'actual_rate_measurement_or_field_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['integral-contract','scope-lineage'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
