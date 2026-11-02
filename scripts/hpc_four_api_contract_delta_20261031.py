"""Four independent focused API contracts, with fabricated inputs only."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity.contracts import AssessmentResult,canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('invalid contract accepted')

def receipt(model_id,inputs,values):
    raw={'model_id':model_id,'model_version':'synthetic','status':'computed','inputs':inputs,'values':values,'units':{},'assumptions':[],'notes':['Fabricated API-contract receipt only.'],'context':{'asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds'},'input_digest':'pending','source_ids':[],'qualification':'user_model','runtime':{}}
    raw['input_digest']=canonical_digest({k:raw[k] for k in ('model_id','model_version','inputs','context')})
    return AssessmentResult.model_validate_json(json.dumps(raw)).model_dump(mode='json')

def scale_fixture():
    transport={'assessment_id':'synthetic','physical_scope_id':'scope','substrate_condition_id':'substrate','solution_condition_id':'solution','scale_phase_id':'stack','scale_state_id':'synthetic','transported_species_id':'M','provider_id':'synthetic','provider_revision':'1','source_sha256':'a'*64,'condition_sha256':'b'*64,'transport_configuration_sha256':'c'*64,'bulk_concentration_mol_m3':2.0,'interface_concentration_mol_m3':0.0,'bare_film_thickness_m':1.0,'bare_diffusivity_m2_s':1.0,'covered_area_fraction':1.0,'layers':[{'layer_id':'layer','thickness_m':1.0,'effective_diffusivity_m2_s':1.0,'solution_to_layer_partition_coefficient':1.0}],'electron_equivalents_per_mole':1.0,'concentration_basis_and_partition_reviewed':True,'effective_diffusivity_support_reviewed':True,'area_coverage_and_uniform_parallel_path_reviewed':True,'electron_equivalent_mapping_reviewed':True,'computational_use_authorized':True,'evidence':[{'source_id':'synthetic','origin':'synthetic','citation':'Fabricated unit resistance path.'}]}
    inputs={'assessment_id':'source','physical_scope_id':'scope','substrate_condition_id':'substrate','solution_condition_id':'solution','scale_phase_id':'phase'}
    values=dict(inputs,input_digest=canonical_digest(inputs),scale_history=[{'time_s':0.0,'scale_thickness_m':1.0},{'time_s':10.0,'scale_thickness_m':2.0}])
    history=receipt('chemistry.caller_surface_scale_kinetics',inputs,values)
    return {'transport_request':transport,'layer_bindings':[{'layer_id':'layer','scale_history_result':history}],'layer_history_order_and_phase_mapping_reviewed':True,'common_scope_time_and_knot_alignment_reviewed':True,'independent_quasi_steady_knot_interpretation_reviewed':True,'computational_use_authorized':True}

def check(task):
    if task=='gsa':
        from matintegrity import ince_glinka_gsa_curve_life as module
    elif task=='crevice':
        from matintegrity import crevice_local_speciation_ledger as module
    elif task=='gasket':
        from matintegrity.models import gasket_leakage_rate_threshold_events as module
    else:
        from matintegrity import scale_layer_stack_series_transport as module
    spec=module.specifications()[0]
    artifact=json.loads((ROOT/'metadata/four_api_contract_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schemas'][spec.model_id]==spec.input_type.model_json_schema();rejects(lambda:spec.input_type.model_validate_json('{}'))
    if task=='gsa':
        loader=importlib.util.spec_from_file_location('synthetic_gsa_example',ROOT/'examples/ince_glinka_gsa.py');example=importlib.util.module_from_spec(loader);loader.loader.exec_module(example)
        target=example.result.values['maximum_gsa_parameter'];points=[{'point_id':str(i),'gsa_parameter':target*factor,'cycles_to_failure':life,'source_record_id':'curve','evidence':[{'source_id':'curve','origin':'synthetic','citation':'Fabricated monotone life curve.'}]} for i,(factor,life) in enumerate(((0.5,1000.0),(2.0,100.0)))]
        values={'calculation':example.request.model_dump(mode='json'),'calibration_id':'synthetic','calibration_material_condition_id':example.request.material_condition_id,'cycles_definition':'caller synthetic full cycles','curve_points':points,'interpolation_reviewed':True,'repeated_cycle_assumption_reviewed':True,'material_condition_and_curve_applicability_reviewed':True}
        request=spec.input_type.model_validate_json(json.dumps(values));result=module.evaluate_ince_glinka_gsa_curve_life(request);assert result.status=='computed' and math.isclose(result.values['cycles_to_failure'],math.sqrt(1000*100),rel_tol=1e-12)
        values['interpolation_reviewed']=False;assert module.evaluate_ince_glinka_gsa_curve_life(spec.input_type.model_validate_json(json.dumps(values))).status=='needs_data'
        values['curve_points'][1]['cycles_to_failure']=2000.0;rejects(lambda:spec.input_type.model_validate_json(json.dumps(values)))
    elif task=='crevice':
        knot={'time_s':10.0,'geometry_side':'left_pre_remap','cell_volume_m3':[1.0,3.0],'cell_concentration_mol_m3':[[2.0,4.0],[1.0,5.0]]}
        first=module.transport_cell_context_digest(knot,0);second=module.transport_cell_context_digest(knot,1);assert first!=second
        expected=canonical_digest({'knot_summary':knot,'cell_index':0,'cell_volume_m3':1.0,'cell_concentration_mol_m3':[2.0,1.0]});assert first==expected
        changed=dict(knot,geometry_side='right_post_remap');assert module.transport_cell_context_digest(changed,0)!=first
        rejects(lambda:module.transport_cell_context_digest(knot,2));rejects(lambda:module.CreviceSpeciationKnot.model_validate_json(json.dumps({'knot_summary_index':0,'time_s':10.0,'geometry_side':'left_pre_remap','cells':[]})))
    elif task=='gasket':
        above=module._outside_intervals([0.0,10.0,20.0],[0.0,2.0,0.0],1.0,below=False)
        assert len(above)==1 and above[0]['start_time_s']==5.0 and above[0]['end_time_s']==15.0 and above[0]['duration_s']==10.0
        assert not above[0]['left_censored'] and not above[0]['right_censored']
        left=module._outside_intervals([0.0,10.0],[2.0,0.0],1.0,below=False);right=module._outside_intervals([0.0,10.0],[0.0,2.0],1.0,below=False)
        assert left[0]['left_censored'] and right[0]['right_censored']
        assert module._outside_intervals([0.0,10.0],[1.0,1.0],1.0,below=False)==[]
    else:
        values=scale_fixture();request=spec.input_type.model_validate_json(json.dumps(values));result=module.evaluate_layered_scale_history_series_transport(request);assert result.status=='computed'
        flux=[row['transport_result']['values']['area_average_flux_limit_mol_m2_s'] for row in result.values['knots']]
        assert len(flux)==2 and math.isclose(flux[0],1.0,rel_tol=1e-12) and math.isclose(flux[1],2.0/3.0,rel_tol=1e-12)
        values['common_scope_time_and_knot_alignment_reviewed']=False;assert module.evaluate_layered_scale_history_series_transport(spec.input_type.model_validate_json(json.dumps(values))).status=='needs_data'
        values=scale_fixture();values['layer_bindings'][0]['scale_history_result']['values']['input_digest']='f'*64;rejects(lambda:spec.input_type.model_validate_json(json.dumps(values)))
    return {'partition':task,'independent_focused_contract_reference':True,'central_counts':artifact['central_counts'],'real_dataset_used':False,'complete_model_or_physical_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['gsa','crevice','gasket','scale'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
