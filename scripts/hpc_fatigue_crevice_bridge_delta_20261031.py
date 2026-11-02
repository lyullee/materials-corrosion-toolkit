"""Separate bounded synthetic fatigue and volume-bookkeeping partitions."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from matintegrity.contracts import AssessmentResult,canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('invalid contract accepted')

def fatigue_payload():
    from matintegrity import fatigue_miner_block_history as module
    def result(life):
        raw={'model_id':module.FINDLEY_MODEL_ID,'model_version':'synthetic','status':'computed','inputs':{},'values':{'material_condition_id':'synthetic','cycles_to_failure':life},'units':{},'assumptions':[],'notes':['Synthetic life receipt; Findley law not exercised.'],'context':{'asset_id':'synthetic','location_id':'synthetic','time_basis':'cycle'},'input_digest':'pending','source_ids':[],'qualification':'user_model','runtime':{}}
        model=AssessmentResult.model_validate_json(json.dumps(raw));raw['input_digest']=canonical_digest({k:(model.context.model_dump(mode='json') if k=='context' else raw[k]) for k in ('model_id','model_version','inputs','context')});return raw
    return {'blocks':[{'block_id':'a','cycle_count':30,'life_result':result(100.0)},{'block_id':'b','cycle_count':40,'life_result':result(200.0)}],'damage_threshold':0.5,'ordered_blocks_reviewed':True,'shared_asset_location_material_condition_reviewed':True,'linear_damage_rule_reviewed':True,'no_sequence_interaction_assumed':True}

def crevice_payload():
    from matintegrity.crevice_campaign import CreviceGeometryTransportCampaign
    states=[]
    for time,scale in ((0.0,1.0),(10.0,2.0),(20.0,2.0)):
        states.append({'elapsed_time_s':time,'restricted_transport_geometry':{'cell_cross_section_m2':[scale,3*scale],'face_cross_section_m2':[scale,2*scale,3*scale],'wall_area_per_volume_m2_m3':[1.0,1.0],'reference_cross_section_m2':1.0,'cell_widths_m':[1.0,1.0]}})
    history={'geometry_id':'synthetic','status':'computed','geometry_states':states,'reference_cross_section_m2':1.0,'cell_count':2,'cell_widths_m':[1.0,1.0]}
    base={'simulation_id':'synthetic','species_ids':['M'],'length_m':2.0,'cell_count':2,'cell_widths_m':[1.0,1.0],'cell_cross_section_m2':[1.0,3.0],'face_cross_section_m2':[1.0,2.0,3.0],'reference_cross_section_m2':1.0,'variable_area_one_dimensional_reduction_reviewed':True,'diffusivity_m2_s':[1e-9],'initial_concentration_mol_m3':[[1.0,3.0]],'mouth_concentration_mol_m3':[1.0],'output_times_s':[0.0,10.0,20.0],'reaction_provider_id':'synthetic','reaction_configuration_sha256':'b'*64,'geometry_diffusion_reaction_basis_reviewed':True}
    campaign={'campaign_id':'synthetic','geometry_id':'synthetic','geometry_history':history,'geometry_history_sha256':canonical_digest(history),'base_transport_request':base,'exact_geometry_transport_clock_reviewed':True,'operator_split_and_fixed_within_interval_reviewed':True,'cell_inventory_remap_on_aperture_change_reviewed':True,'callback_global_time_mapping_reviewed':True}
    model=CreviceGeometryTransportCampaign.model_validate_json(json.dumps(campaign))
    result={'status':'computed','campaign_id':'synthetic','geometry_id':'synthetic','geometry_history_sha256':model.geometry_history_sha256,'campaign_input_sha256':canonical_digest(model.model_dump(mode='json')),'segment_results':[{'segment_index':i,'global_start_time_s':float(10*i),'global_end_time_s':float(10*(i+1)),'result':{'status':'computed','output_times_s':[0.0,10.0],'concentration_mol_m3':[[[1.0,3.0]],[[1.0,3.0]]] if i==0 else [[[0.5,1.5]],[[0.5,1.5]]]}} for i in range(2)],'geometry_boundary_inventory_remaps':[{'post_remap_cell_concentration_mol_m3':[[0.5,1.5]]}]}
    return {'assessment_id':'synthetic','campaign':model.model_dump(mode='json'),'campaign_result':result,'campaign_result_sha256':canonical_digest(result),'cell_volume_weighted_bulk_summary_reviewed':True,'local_cell_heterogeneity_must_be_preserved_reviewed':True,'no_automatic_equilibrium_or_kinetic_interpretation_reviewed':True}

def check(task):
    kind,partition=task.split('-')
    if kind=='fatigue':
        from matintegrity import fatigue_miner_block_history as module
        payload=fatigue_payload();cls=module.FindleyMinerHistoryRequest;evaluator=module.evaluate_findley_miner_block_history
    else:
        from matintegrity import crevice_transport_composition_bridge as module
        payload=crevice_payload();cls=module.CreviceTransportCompositionBridge;evaluator=module.summarize_crevice_transport_composition
    artifact=json.loads((ROOT/f'metadata/{kind}_bridge_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==cls.model_json_schema()
    request=cls.model_validate_json(json.dumps(payload));result=evaluator(request);assert result.status=='computed'
    if kind=='fatigue':
        assert math.isclose(result.values['cumulative_damage'],0.5)
        assert result.values['first_threshold_crossing_in_supplied_sequence']['cycle_count_at_crossing_in_supplied_sequence']==70
        assert not result.values['probability_inferred'] and not result.values['remaining_life_extrapolated']
        if partition=='contracts':
            for bad in (True,1.0,0,-1):
                changed=fatigue_payload();changed['blocks'][0]['cycle_count']=bad;rejects(lambda:cls.model_validate_json(json.dumps(changed)))
        else:
            changed=fatigue_payload();changed['linear_damage_rule_reviewed']=False;assert evaluator(cls.model_validate_json(json.dumps(changed))).status=='needs_data'
            changed=fatigue_payload();changed['blocks'][1]['life_result']['input_digest']='f'*64;assert evaluator(cls.model_validate_json(json.dumps(changed))).status=='out_of_scope'
            changed=fatigue_payload();changed['damage_threshold']=0.6;assert evaluator(cls.model_validate_json(json.dumps(changed))).values['first_threshold_crossing_in_supplied_sequence'] is None
    else:
        rows=result.values['knot_summaries'];assert [row['geometry_side'] for row in rows]==['initial_or_interior','left_pre_remap','right_post_remap','final_state']
        np.testing.assert_allclose([row['total_inventory_mol'][0] for row in rows],[10.0]*4)
        np.testing.assert_allclose([row['volume_weighted_bulk_concentration_mol_m3'][0] for row in rows],[2.5,2.5,1.25,1.25])
        assert not result.values['automatic_mass_action_input']
        if partition=='contracts':
            changed=crevice_payload();changed['campaign_result_sha256']='f'*64;rejects(lambda:cls.model_validate_json(json.dumps(changed)))
            changed=crevice_payload();changed['campaign_result']['geometry_id']='wrong';changed['campaign_result_sha256']=canonical_digest(changed['campaign_result']);rejects(lambda:cls.model_validate_json(json.dumps(changed)))
        else:
            changed=crevice_payload();changed['local_cell_heterogeneity_must_be_preserved_reviewed']=False;assert evaluator(cls.model_validate_json(json.dumps(changed))).status=='needs_data'
            changed=crevice_payload();changed['campaign_result']['geometry_boundary_inventory_remaps']=[];changed['campaign_result_sha256']=canonical_digest(changed['campaign_result']);assert evaluator(cls.model_validate_json(json.dumps(changed))).status=='out_of_scope'
    return {'module':kind,'partition':partition,'schema_and_synthetic_bookkeeping':True,'upstream_solver_or_material_law_exercised':False,'actual_dataset_used':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['fatigue-contracts','fatigue-scope','crevice-contracts','crevice-scope'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
