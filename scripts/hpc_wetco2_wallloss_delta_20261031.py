"""Conditional finite-scenario arithmetic with fabricated provider-shaped rows."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import wet_co2_simulation_wall_loss_envelope as module
from matintegrity.wet_co2_data import WetCo2SimulationGridRow
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def payload():
    rows=[]
    for index,rate in enumerate((1e-4,2e-4),start=2):
        raw={'provider_row':index,'source_archive_sha256':'a'*64,'temperature_K':300.0,'flow_velocity_m_s':1.0,'co2_pressure_Pa':1e5,'internal_pressure_Pa':2e5,'corrosion_inhibitor_efficiency_fraction':0.0,'shear_stress_Pa':1.0,'ph':5.0,'corrosion_rate_m_s':rate,'evidence':[{'source_id':'norsok-m506-simulation-grid','origin':'open_dataset','citation':'Synthetic descriptor, not an actual provider measurement.','license_id':'CC-BY-4.0','sha256':'a'*64}]}
        rows.append(WetCo2SimulationGridRow.model_validate_json(json.dumps(raw)).model_dump(mode='json'))
    evidence={'source_id':'synthetic','origin':'synthetic','citation':'Fabricated thickness bounds.'}
    return {'rows':rows,'scenarios':[{'provider_row':row['provider_row'],'row_sha256':canonical_digest(row),'corrosion_rate_m_s':row['corrosion_rate_m_s']} for row in rows],'exposure_duration_s':10.0,'baseline_wall_thickness_m':0.01,'required_wall_thickness_m':0.0085,'baseline_evidence':evidence,'required_thickness_evidence':evidence,'scenario_mapping_reviewed':True,'constant_rate_over_exposure_reviewed':True,'baseline_location_material_time_scope_reviewed':True,'finite_scenario_set_interpretation_reviewed':True}

def check(task):
    cls=module.WetCo2SimulationWallLossEnvelopeRequest
    artifact=json.loads((ROOT/'metadata/wetco2_wallloss_snapshot.json').read_text());assert artifact['schema']==cls.model_json_schema();assert artifact['source_rows']==artifact['package_rows']
    request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_wet_co2_simulation_wall_loss_envelope(request);assert result.status=='computed'
    rows=result.values['finite_provider_simulation_scenarios'];assert math.isclose(rows[0]['remaining_thickness_m'],0.009) and math.isclose(rows[1]['remaining_thickness_m'],0.008)
    assert rows[0]['threshold_crossing_time_within_exposure_s'] is None
    assert math.isclose(rows[1]['threshold_crossing_time_within_exposure_s'],7.5,abs_tol=1e-12)
    assert result.values['minimum_remaining_provider_row']==3 and not result.values['probability_inferred'] and not result.values['field_corrosion_prediction']
    if task=='analytic':
        changed=payload();changed['exposure_duration_s']=100.0
        assert module.evaluate_wet_co2_simulation_wall_loss_envelope(cls.model_validate_json(json.dumps(changed))).status=='out_of_scope'
        changed=payload();changed['rows'][0]['corrosion_rate_m_s']=0.0;changed['scenarios'][0].update(corrosion_rate_m_s=0.0,row_sha256=canonical_digest(changed['rows'][0]));zero=module.evaluate_wet_co2_simulation_wall_loss_envelope(cls.model_validate_json(json.dumps(changed)))
        assert zero.values['finite_provider_simulation_scenarios'][0]['threshold_crossing_time_within_exposure_s'] is None
    else:
        changed=payload();changed['constant_rate_over_exposure_reviewed']=False;assert module.evaluate_wet_co2_simulation_wall_loss_envelope(cls.model_validate_json(json.dumps(changed))).status=='needs_data'
        for mutation in ('digest','order','bounds'):
            changed=payload()
            if mutation=='digest': changed['scenarios'][0]['row_sha256']='f'*64
            elif mutation=='order': changed['rows'].reverse()
            else: changed['required_wall_thickness_m']=0.01
            try: cls.model_validate_json(json.dumps(changed))
            except ValidationError: pass
            else: raise AssertionError('invalid row/bounds binding accepted')
    return {'synthetic_conditional_wall_loss_threshold_arithmetic':True,'partition':task,'actual_provider_rows_used':False,'probability_or_field_calibration_claimed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['analytic','lineage-schema'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
