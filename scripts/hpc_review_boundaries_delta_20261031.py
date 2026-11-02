"""Post-review remap, evidence and explicit unit contracts only."""
import argparse
import json
from pathlib import Path
from pydantic import ValidationError
import hpc_fatigue_crevice_bridge_delta_20261031 as bridges
import hpc_wetco2_wallloss_delta_20261031 as wet_fixture
from matintegrity import crevice_transport_composition_bridge as crevice,fatigue_miner_block_history as fatigue,wet_co2_simulation_wall_loss_envelope as wet
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def rejects(factory):
    try: factory()
    except ValidationError: return
    raise AssertionError('invalid evidence contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/review_boundaries_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows']
    for module in (crevice,fatigue,wet):
        spec=module.specifications()[0];assert artifact['schemas'][spec.model_id]==spec.input_type.model_json_schema() and artifact['units'][spec.model_id]==spec.units
    if task=='geometry-remap':
        values=bridges.crevice_payload();states=values['campaign']['geometry_history']['geometry_states'];remap=values['campaign_result']['geometry_boundary_inventory_remaps'][0]
        remap.update(elapsed_time_s=10.0,from_geometry_state_sha256=canonical_digest(states[0]),to_geometry_state_sha256=canonical_digest(states[1]));values['campaign_result_sha256']=canonical_digest(values['campaign_result'])
        request=crevice.CreviceTransportCompositionBridge.model_validate_json(json.dumps(values));assert crevice.summarize_crevice_transport_composition(request).status=='computed'
        for key,bad in (('elapsed_time_s',10.0001),('from_geometry_state_sha256','f'*64),('to_geometry_state_sha256','f'*64)):
            changed=json.loads(json.dumps(values));changed['campaign_result']['geometry_boundary_inventory_remaps'][0][key]=bad;changed['campaign_result_sha256']=canonical_digest(changed['campaign_result'])
            assert crevice.summarize_crevice_transport_composition(crevice.CreviceTransportCompositionBridge.model_validate_json(json.dumps(changed))).status=='out_of_scope'
        return {'exact_remap_clock_from_to_state_digest':True,'whole_result_digest_recomputed_for_each_adversarial_case':True,'upstream_transport_solved':False}
    values=bridges.fatigue_payload()
    for block in values['blocks']: block['life_result']['units']={'cycles_to_failure':'cycle'}
    cls=fatigue.FindleyMinerHistoryRequest;assert fatigue.evaluate_findley_miner_block_history(cls.model_validate_json(json.dumps(values))).status=='computed'
    for index in (0,1):
        changed=json.loads(json.dumps(values));changed['blocks'][index]['life_result']['units']={'cycles_to_failure':'s'}
        assert fatigue.evaluate_findley_miner_block_history(cls.model_validate_json(json.dumps(changed))).status=='out_of_scope'
    values=wet_fixture.payload();values['baseline_evidence']={'source_id':'synthetic-measured-shape','origin':'measured','citation':'Fabricated measurement-shaped descriptor for contract testing only.'};values['required_thickness_evidence']={'source_id':'synthetic-limit','origin':'user_declared','citation':'Fabricated caller limit.'}
    cls=wet.WetCo2SimulationWallLossEnvelopeRequest
    assert wet.evaluate_wet_co2_simulation_wall_loss_envelope(cls.model_validate_json(json.dumps(values))).status=='computed'
    for key,bad in (('baseline_evidence','synthetic'),('required_thickness_evidence','measured')):
        changed=json.loads(json.dumps(values));changed[key]['origin']=bad;rejects(lambda:cls.model_validate_json(json.dumps(changed)))
    changed=json.loads(json.dumps(values));changed['required_thickness_evidence']['origin']='open_dataset';cls.model_validate_json(json.dumps(changed))
    units=wet.specifications()[0].units
    for key,unit in (('corrosion_rate_m_s','m/s'),('uniform_wall_loss_m','m'),('remaining_thickness_m','m'),('required_thickness_margin_m','m'),('threshold_crossing_time_within_exposure_s','s')): assert units['finite_provider_simulation_scenarios[].'+key]==unit
    return {'Findley_first_and_later_life_cycle_units_required':True,'wallloss_baseline_and_limit_evidence_origin_gates':True,'scenario_output_units_explicit':True,'actual_measurement_or_limit_supplied':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['geometry-remap','units-evidence'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
