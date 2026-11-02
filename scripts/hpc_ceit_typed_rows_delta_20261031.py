"""CEIT typed rows over mock parser objects only; no CEIT file is opened."""
import argparse,json
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from matintegrity import ceit_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def parser(source,*,series_id,reported_tof_unit,reported_temperature_unit,sample_interval_s):
    if series_id!='synthetic': raise ValueError('mock series unsupported')
    return {'timestamp_basis':'provider_naive_calendar_time_timezone_unresolved','observations':[{'timestamp':datetime(2020,1,1)+timedelta(seconds=i),'node_id':'synthetic-node','sample_id':str(i),'piezo_id':'synthetic-piezo','reported_frequency_code':3,'reported_pwm':0,'reported_echo_index':1,'reported_tof_reference':0,'tof_reported':float(i),'reported_temperature':20.0,'reported_battery':3.7,'reported_amplitude':0,'tof_s':None,'ambient_temperature_K':None,'sample_time_s':None,'raw_signal':np.array([-1.0,0.0,1.0]),'filtered_signal':np.array([0.0,1.0,0.0]),'correlation_signal':np.array([0.0,0.0,1.0]),'envelope_signal':np.array([1.0,0.0,1.0]),'raw_adc_rail_count':0} for i in range(2)]}

def auth(): return module.CeitFieldReadAuthorization(attribution='Fabricated CEIT parser output, no source JSON accessed.',computational_use_authorized=True,local_only_authorized=True)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported CEIT rights contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/ceit_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert module.SOURCE_SHA256==artifact['source_pin']
    for cls in (module.CeitFieldReadAuthorization,module.CeitFieldArchiveAuditRequest,module.CeitFieldObservationRow): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    assert artifact['source_rows']['datasets'][module.DATASET_ID]['license']=='CC-BY-4.0'
    module._verify_source=lambda source:(module.SOURCE_MD5,module.SOURCE_SHA256,module.SOURCE_BYTES)
    module.read_ceit_uniform_corrosion_field=parser
    source=Path('synthetic-never-opened')/module.SOURCE_FILENAME;authorization=auth();digest=canonical_digest(authorization.model_dump(mode='json'))
    if task=='schema-rights':
        registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.CeitFieldArchiveAuditRequest(local_json_path=str(source),series_id='synthetic',authorization=authorization)
        result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='provider_naive_calendar'))
        assert result.status=='computed' and result.values['observation_count']==2 and result.values['authorization_sha256']==digest and result.values['reported_tof_unit'] is None
        assert not result.values['sample_values_returned'] and not result.values['thickness_computed'] and str(source) not in json.dumps(result.values)
        assert artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
    else:
        rows=list(module.iter_ceit_field_observation_rows(source,series_id='synthetic',authorization=authorization))
        assert [r.source_order for r in rows]==[0,1] and [r.provider_array_index for r in rows]==[0,1] and rows[0].raw_signal==(-1.0,0.0,1.0)
        assert rows[0].observation_row_sha256!=rows[1].observation_row_sha256 and all(r.authorization_sha256==digest and r.source_file_sha256==module.SOURCE_SHA256 and r.evidence.license_id=='CC-BY-4.0' and r.local_only and r.tof_s is None and r.ambient_temperature_K is None and r.sample_time_s is None and not r.wall_thickness_inferred and not r.corrosion_rate_inferred for r in rows)
        rejects(lambda:next(module.iter_ceit_field_observation_rows(source,series_id='missing',authorization=authorization)))
        for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
            values=authorization.model_dump(mode='json');values.update(change);rejects(lambda:module.CeitFieldReadAuthorization.model_validate_json(json.dumps(values)))
        values=authorization.model_dump(mode='json');values['attribution']=' ';blank=module.CeitFieldReadAuthorization.model_validate_json(json.dumps(values));rejects(lambda:next(module.iter_ceit_field_observation_rows(source,series_id='synthetic',authorization=blank)))
    return {'partition':task,'mock_source_verification_and_parser_outputs_only':True,'source_file_opened':False,'actual_tof_thickness_or_corrosion_validated':False}

if __name__=='__main__':
    parser_args=argparse.ArgumentParser();parser_args.add_argument('--task',choices=['schema-rights','lineage-fail-closed'],required=True);parser_args.add_argument('--output',type=Path,required=True);args=parser_args.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error: args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
