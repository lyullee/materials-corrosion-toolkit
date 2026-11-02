"""Guided-wave typed adapter on fabricated pinned-parser output, never raw archive."""
import argparse
import json
from pathlib import Path
import tempfile
from pydantic import ValidationError
from matintegrity import guided_wave_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def parser(path,acquisition_id,*,specimen_id,require_pinned_hash,expected_archive_sha256,article_state_review):
    assert acquisition_id==7 and specimen_id=='synthetic' and require_pinned_hash and article_state_review and expected_archive_sha256==module.GUIDED_WAVE_ARCHIVE_SHA256
    signal={'frequency_Hz':14000.0,'source_sheet_name':'synthetic-sheet','source_sheet_index':0,'excitation_cycles':5.0,'raw_window_label':'synthetic-window','distance_m':[0.0,0.1,0.1],'torsional_V':[-1.0,0.0,1.0],'flexural_V':[1.0,0.0,-1.0],'provider_pure_dac_V':[0.2,0.2,0.2],'numeric_sample_rows':3,'distance_axis_order':'source_order_with_repeated_distance','repeated_distance_intervals':1}
    return {'outer_archive_sha256':module.GUIDED_WAVE_ARCHIVE_SHA256,'nested_archive_sha256':'b'*64,'workbook_sha256':'c'*64,'member_path':'synthetic/workbook.xls','acquisition_id':7,'specimen_id':'synthetic','signals':[signal]}

def auth(): return module.GuidedWaveReadAuthorization(attribution='Fabricated guided-wave parser-output verification only.',computational_use_authorized=True,local_only_authorized=True)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported source/rights contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/guided_wave_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert module.GUIDED_WAVE_ARCHIVE_SHA256==artifact['archive_pin'] and module.ARCHIVE_BYTES==artifact['archive_bytes']
    for cls in (module.GuidedWaveReadAuthorization,module.GuidedWaveArchiveAuditRequest,module.GuidedWaveSampleRow): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    rights=artifact['source_rows']['datasets'][module.DATASET_ID];assert rights['license']=='CC-BY-4.0' and rights['rights_status']=='reviewed_license'
    module.read_guided_wave_acquisition=parser
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/module.ARCHIVE_FILENAME;path.write_bytes(b'Fabricated opaque bytes; not provider archive.');authorization=auth();digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='schema-rights':
            registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.GuidedWaveArchiveAuditRequest(local_archive_path=str(path),acquisition_id=7,specimen_id='synthetic',excitation_frequency_Hz=14000.0,authorization=authorization)
            result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='source_distance_axis'))
            assert result.status=='computed' and result.values['sample_count']==3 and result.values['authorization_sha256']==digest and result.values['repeated_distance_intervals']==1
            assert not result.values['point_values_returned'] and not result.values['local_path_returned'] and result.values['machining_step_id'] is None and result.values['temperature_K'] is None and str(path) not in json.dumps(result.values)
            assert artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
        else:
            kwargs={'acquisition_id':7,'specimen_id':'synthetic','excitation_frequency_Hz':14000.0,'authorization':authorization};rows=list(module.iter_guided_wave_sample_rows(path,**kwargs))
            assert [r.sample_row_order for r in rows]==[0,1,2] and [r.provider_source_row for r in rows]==[3,4,5] and [r.distance_m for r in rows]==[0.0,0.1,0.1]
            assert [r.torsional_voltage_V for r in rows]==[-1.0,0.0,1.0] and [r.flexural_voltage_V for r in rows]==[1.0,0.0,-1.0]
            assert len({r.sample_row_sha256 for r in rows})==3 and all(r.authorization_sha256==digest and r.outer_archive_sha256==module.GUIDED_WAVE_ARCHIVE_SHA256 and r.nested_archive_sha256=='b'*64 and r.workbook_sha256=='c'*64 and r.local_only and r.evidence.license_id=='CC-BY-4.0' and r.timestamp is None and r.machining_step_id is None and not r.wall_loss_inferred and not r.probability_of_detection_inferred for r in rows)
            rejects(lambda:next(module.iter_guided_wave_sample_rows(path,**dict(kwargs,excitation_frequency_Hz=999.0))))
            for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
                values=authorization.model_dump(mode='json');values.update(change);rejects(lambda:module.GuidedWaveReadAuthorization.model_validate_json(json.dumps(values)))
            def duplicate(*args,**kwargs):
                record=parser(*args,**kwargs);record['signals']*=2;return record
            module.read_guided_wave_acquisition=duplicate;rejects(lambda:next(module.iter_guided_wave_sample_rows(path,**kwargs)))
    return {'partition':task,'mock_pinned_parser_contract_only':True,'source_order_duplicates_signed_voltage_row_auth_nested_lineage':True,'actual_archive_or_wall_loss_or_POD_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-rights','lineage-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
