"""Exact-knot handoff contracts with fabricated assessment and mock downstream laws."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import fixed_fugacity_carbonate_scale_kinetics as module
from matintegrity.contracts import AssessmentResult,Calculation,RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    inputs={'synthetic':True};raw={'model_id':'chemistry.fixed_fugacity_carbonate_history','model_version':'synthetic','status':'computed','inputs':inputs,'values':{'input_sha256':canonical_digest(inputs),'physical_scope_id':'scope','history_id':'synthetic','time_s':[0.0,10.0],'temperature_K_history':[300.0,300.0],'co3_mol_L_history':[0.001,0.002],'all_points_computed':True,'chemistry_interpolation_performed':False},'units':{'time_s':'s','co3_mol_L_history':'mol/L'},'assumptions':[],'notes':['Fabricated carbonate history, not actual equilibrium.'],'context':{'asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds'},'input_digest':'pending','source_ids':[],'qualification':'user_model','runtime':{}}
    normalized=AssessmentResult.model_validate_json(json.dumps(raw));raw['context']=normalized.context.model_dump(mode='json')
    raw['input_digest']=canonical_digest({k:raw[k] for k in ('model_id','model_version','inputs','context')});result=AssessmentResult.model_validate_json(json.dumps(raw)).model_dump(mode='json')
    def record(name,value_key,value): return {'provider_id':'synthetic-'+name,'provider_revision':'1','record_id':name,'sha256':'a'*64,value_key:value,'evidence':[{'source_id':name,'origin':'synthetic','citation':'Fabricated '+name+' record.','sha256':'a'*64}]}
    knots=[]
    for time in (0.0,10.0):
        ksp=record('ksp','log10_solubility_product',-3.0);ksp.update(temperature_support_min_K=290.0,temperature_support_max_K=310.0,temperature_applicability_reviewed=True)
        calcium=record('calcium','dimensionless_activity',1.0);calcium['species_id']='Ca'
        knots.append({'time_s':time,'carbonate_activity_coefficient':record('gamma','value',1.0),'other_species_activities':[calcium],'solubility_product':ksp})
    kinetics={'assessment_id':'synthetic-law','physical_scope_id':'scope','substrate_condition_id':'synthetic','solution_condition_id':'synthetic','scale_phase_id':'solid','physical_specimen_id':'synthetic','source_group_id':'synthetic','provider_id':'synthetic','provider_revision':'1','source_sha256':'b'*64,'condition_sha256':'c'*64,'kinetic_configuration_sha256':'d'*64,'temperature_K':300.0,'initial_scale_thickness_m':0.0,'precipitation_rate_constant_mol_m2_s':1e-9,'precipitation_order':1.0,'dissolution_rate_constant_mol_m2_s':1e-9,'dissolution_order':1.0,'scale_molar_volume_m3_mol':1e-5,'intervals':[{'interval_id':'a','start_time_s':0.0,'end_time_s':10.0,'saturation_ratio':1.0,'saturation_ratio_end':2.0,'temperature_K':300.0}],'linearly_varying_saturation_reviewed':True,'interval_temperature_profile_reviewed':True,'supersaturation_kinetics_and_standard_state_reviewed':True,'precipitation_and_dissolution_coefficients_reviewed':True,'scale_phase_identity_and_molar_volume_reviewed':True,'single_uniform_scale_layer_scope_reviewed':True,'computational_use_authorized':True,'evidence':[{'source_id':'synthetic-law','origin':'synthetic','citation':'Fabricated law fixture; downstream calculation mocked.'}]}
    return {'assessment_id':'synthetic','fixed_fugacity_carbonate_history':result,'fixed_fugacity_carbonate_history_sha256':canonical_digest(result),'carbonate_species_id':'CO3','selected_solid_id':'solid','scale_phase_mapping_reviewed':True,'solid_terms':[{'species_id':'CO3','stoichiometric_exponent':1.0},{'species_id':'Ca','stoichiometric_exponent':1.0}],'knots':knots,'carbonate_activity_and_standard_state_reviewed':True,'complete_knot_species_inventory_reviewed':True,'solubility_temperature_support_reviewed':True,'saturation_path_interpolation_reviewed':True,'caller_kinetic_law_scope_and_coefficients_reviewed':True,'computational_use_authorized':True,'kinetics_template':kinetics}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('misaligned carbonate-scale handoff accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/carbonate_scale_handoff_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.FixedFugacityCarbonateScaleKinetics.model_json_schema()
    calls=[]
    def screen(request):
        activities={row.species_id:row.dimensionless_activity for row in request.species};assert request.temperature_K==300.0
        ratio=activities['CO3']*activities['Ca']/1e-3
        return Calculation(values={'candidate_results':[{'solid_id':'solid','log10_saturation_ratio':math.log10(ratio)}]})
    def law(request):
        calls.append(request.model_dump(mode='json'));return Calculation(values={'final_scale_thickness_m':1.23e-6,'scale_history':[]})
    module.aqueous_saturation_screen=screen;module.caller_surface_scale_kinetics=law
    cls=module.FixedFugacityCarbonateScaleKinetics;request=cls.model_validate_json(json.dumps(payload()));registry=ModelRegistry();registry.register(module.specifications()[0]);result=registry.run(module.specifications()[0].model_id,request,request.fixed_fugacity_carbonate_history.context)
    assert result.status=='computed' and len(calls)==1 and result.values['completed_saturation_knot_count']==2
    assert calls[0]['intervals'][0]['saturation_ratio']==1.0 and math.isclose(calls[0]['intervals'][0]['saturation_ratio_end'],2.0,rel_tol=1e-14)
    assert [r['time_s'] for r in result.values['saturation_knot_results']]==[0.0,10.0] and not result.values['temperature_interpolation_performed'] and not result.values['phase_selection_performed']
    if task=='exact-knot-context':
        assert result.values['carbonate_history_result_sha256']==canonical_digest(request.fixed_fugacity_carbonate_history.model_dump(mode='json'))
        for field in ('asset_id','location_id','time_basis'):
            context={'asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds'};context[field]='other';rejects(lambda:registry.run(module.specifications()[0].model_id,request,RunContext(**context)))
    else:
        for change in ('digest','time','temperature-support','phase','record-evidence'):
            values=payload()
            if change=='digest': values['fixed_fugacity_carbonate_history_sha256']='f'*64
            elif change=='time': values['knots'][1]['time_s']=10.001
            elif change=='temperature-support': values['knots'][0]['solubility_product']['temperature_support_max_K']=299.0
            elif change=='phase': values['selected_solid_id']='other'
            else: values['knots'][0]['carbonate_activity_coefficient']['sha256']='f'*64
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        values=payload();values['carbonate_activity_and_standard_state_reviewed']=False;before=len(calls);assert module.evaluate_fixed_fugacity_carbonate_scale_kinetics(cls.model_validate_json(json.dumps(values))).status=='needs_data' and len(calls)==before
        values=payload();values['fixed_fugacity_carbonate_history']['values']['co3_mol_L_history'][1]=0.0;values['fixed_fugacity_carbonate_history_sha256']=canonical_digest(values['fixed_fugacity_carbonate_history']);before=len(calls);partial=module.evaluate_fixed_fugacity_carbonate_scale_kinetics(cls.model_validate_json(json.dumps(values)));assert partial.status=='out_of_scope' and partial.values['completed_saturation_knot_count']==1 and len(calls)==before
    return {'partition':task,'fabricated_assessment_activity_Ksp_and_mock_kinetics_only':True,'exact_source_knot_context_and_downstream_withholding':True,'actual_equilibrium_or_scale_growth_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['exact-knot-context','fail-closed-scale-handoff'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
