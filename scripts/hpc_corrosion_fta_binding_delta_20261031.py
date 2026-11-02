"""Explicit caller probability exchange; deterministic history never supplies p."""
import argparse
import json
from pathlib import Path
from pydantic import ValidationError
import hpc_corrosion_rate_history_delta_20261031 as history_fixture
from matintegrity import corrosion_fta_binding as adapter,corrosion_rate_history as rate
from matintegrity.contracts import Calculation,RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def probability():
    return {'event_id':'synthetic-event','failure_mode':'caller-thickness-condition','condition_id':'synthetic-condition','condition_statement':'Fabricated finite-support thickness condition.','condition_basis':'required_thickness_crossing_within_history_support','probability':0.2,'probability_meaning':'conditional_first_failure_in_period','conditioning':'Caller synthetic assumptions only.','probability_scope_id':'synthetic-scope','probability_evidence':[{'source_id':'caller','origin':'user_declared','citation':'Fabricated probability for adapter verification.'}],'rights_boundary':'local_only'}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('invalid rights contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/corrosion_fta_snapshot.json').read_text())
    for cls in (adapter.CorrosionFaultTreeProbabilityInput,adapter.CorrosionFaultTreeEventBinding,adapter.CorrosionFaultTreeBindingRequest): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    assert artifact['source_rows']==artifact['package_rows']
    request=rate.CorrosionRateThicknessHistoryRequest.model_validate_json(json.dumps(history_fixture.payload()));result=rate.evaluate_corrosion_rate_thickness_history(request);assert result.status=='computed'
    probability_input=adapter.CorrosionFaultTreeProbabilityInput.model_validate_json(json.dumps(probability()));binding=adapter.bind_corrosion_history_probability_to_fta(request,result,probability_input)
    assert isinstance(binding,adapter.CorrosionFaultTreeEventBinding) and binding.basic_event.probability==0.2 and binding.integrity_event_basis.event_probability==0.2
    assert binding.basic_event.evidence_digest==binding.integrity_event_basis.integrity_result_digest
    assert not binding.calculation.values['probability_inferred'] and binding.calculation.values['corrosion_request_sha256']==canonical_digest(request.model_dump(mode='json'))
    wrapper=adapter.CorrosionFaultTreeBindingRequest(corrosion_request=request,corrosion_result=result,probability_input=probability_input)
    registry=ModelRegistry();registry.register(adapter.specifications()[0]);registered=registry.run(adapter.MODEL_ID,wrapper,RunContext(asset_id=request.asset_id,location_id=request.location_id,time_basis=request.time_basis))
    assert registered.status=='computed' and registered.values==binding.calculation.values
    assert artifact['source_rows']['capabilities'][adapter.MODEL_ID]['input_schema']==registry.describe(adapter.MODEL_ID)['input_schema']
    if task=='explicit-binding':
        changed=probability();changed['probability']=0.3;other=adapter.bind_corrosion_history_probability_to_fta(request,result,adapter.CorrosionFaultTreeProbabilityInput.model_validate_json(json.dumps(changed)))
        assert other.basic_event.probability==0.3 and other.basic_event.evidence_digest!=binding.basic_event.evidence_digest
        assert binding.integrity_event_basis.horizon_start_s==0.0 and binding.integrity_event_basis.horizon_end_s==20.0
        changed=probability();changed.update(rights_boundary='caller_authorized_open_distribution',rights_authorization_digest='a'*64)
        opened=adapter.bind_corrosion_history_probability_to_fta(request,result,adapter.CorrosionFaultTreeProbabilityInput.model_validate_json(json.dumps(changed)));assert opened.rights_boundary=='caller_authorized_open_distribution'
    else:
        for field in ('asset_id','location_id','time_basis'):
            context={'asset_id':request.asset_id,'location_id':request.location_id,'time_basis':request.time_basis};context[field]='mismatched'
            rejects(lambda:registry.run(adapter.MODEL_ID,wrapper,RunContext(**context)))
        missing=adapter.bind_corrosion_history_probability_to_fta(request,result,None);assert missing.status=='needs_data' and not missing.values['probability_inferred']
        for change in ({'rights_boundary':'caller_authorized_open_distribution'},{'rights_authorization_digest':'a'*64},{'probability':1.1},{'probability_evidence':[]}):
            changed=dict(probability(),**change);rejects(lambda:adapter.CorrosionFaultTreeProbabilityInput.model_validate_json(json.dumps(changed)))
        for key,bad in (('request_sha256','f'*64),('physical_scope_id','other')):
            changed=result.model_dump(mode='json');changed['values'][key]=bad;tampered=Calculation.model_validate_json(json.dumps(changed));assert adapter.bind_corrosion_history_probability_to_fta(request,tampered,probability_input).status=='out_of_scope'
    return {'partition':task,'caller_probability_preserved_never_inferred':True,'scope_horizon_evidence_rights_digest_binding':True,'actual_failure_probability_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['explicit-binding','fail-closed-rights'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
