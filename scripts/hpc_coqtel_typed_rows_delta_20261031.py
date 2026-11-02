"""Synthetic pinned-parser outputs for local typed-row contracts, no raw HDF5."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import numpy as np
from pydantic import ValidationError
from matintegrity import coqtel_typed_rows as module,signals
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def parser_fixture(path,*,duplicate_policy,require_pinned_hash):
    assert duplicate_policy=='preserve_identical' and require_pinned_hash is True
    pin=signals.COQTEL_FILES[Path(path).name]
    return {'dataset_id':'coqtel','source_sha256':pin['sha256'],'state_index':np.array([1,2,3]),'time_s':np.array([0.0,1.0,1.0]),'current_A':np.array([-0.1,0.2,0.2]),'potential_V':np.array([-0.5,-0.4,-0.4]),'experimental_anomaly':['none_reported']*3,'repeated_time_state_pairs':[(2,3)],'identical_duplicate_intervals':1,'experiment_id':'synthetic-experiment','specimen_id':'synthetic-specimen'}

def auth(): return module.CoqtelReadAuthorization(attribution='Fabricated COQTEL parser-output adapter test only.',computational_use_authorized=True,local_only_authorized=True)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unauthorized contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/coqtel_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['source_pins']=={k:dict(v,reported_anomaly_state_range=list(v['reported_anomaly_state_range']) if v['reported_anomaly_state_range'] is not None else None) for k,v in signals.COQTEL_FILES.items()}
    for cls in (module.CoqtelReadAuthorization,module.CoqtelArchiveAuditRequest,module.CoqtelElectrochemistryRow):
        assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
        exported=artifact['standalone_schema_exports'][cls.__name__]
        if exported is not None: assert json.loads((ROOT/exported).read_text())==cls.model_json_schema()
    rights=artifact['source_rows']['datasets']['coqtel'];assert rights['license']=='CC-BY-4.0' and rights['rights_status']=='reviewed_license'
    module.coqtel_electrochemistry=parser_fixture
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/next(iter(signals.COQTEL_FILES));path.write_bytes(b'Synthetic opaque fixture only; not HDF5.')
        authorization=auth();digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='schema-rights':
            registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.CoqtelArchiveAuditRequest(local_hdf5_path=str(path),authorization=authorization)
            result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds'))
            assert result.status=='computed' and result.values['row_count']==3 and result.values['authorization_sha256']==digest
            assert result.values['identical_repeated_time_interval_count']==1 and not result.values['point_values_returned'] and not result.values['local_path_returned'] and str(path) not in json.dumps(result.values)
            assert artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
        else:
            rows=list(module.iter_coqtel_electrochemistry_rows(path,authorization=authorization))
            assert [r.provider_source_row for r in rows]==[1,2,3] and [r.source_order for r in rows]==[0,1,2] and [r.time_s for r in rows]==[0.0,1.0,1.0]
            assert [r.duplicate_timestamp_from_previous_row for r in rows]==[False,False,True]
            for row in rows:
                identity={'dataset_id':'coqtel','source_filename':path.name,'source_file_sha256':row.source_file_sha256,'source_order':row.source_order,'provider_source_row':row.provider_source_row,'time_s':row.time_s,'current_A':row.current_A,'potential_V':row.potential_V,'anomaly':row.anomaly}
                assert row.source_row_sha256==canonical_digest(identity) and row.authorization_sha256==digest and row.local_only and row.pit_dimension_per_state is None and row.evidence.sha256==row.source_file_sha256 and row.evidence.license_id=='CC-BY-4.0'
                assert not row.corrosion_rate_inferred and not row.wall_loss_inferred and not row.failure_probability_inferred
            assert rows[0].current_A==-0.1 and rows[1].current_A==0.2
            for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
                changed=authorization.model_dump(mode='json');changed.update(change);rejects(lambda:module.CoqtelReadAuthorization.model_validate_json(json.dumps(changed)))
            changed=authorization.model_dump(mode='json');changed['attribution']=' ';blank=module.CoqtelReadAuthorization.model_validate_json(json.dumps(changed));rejects(lambda:next(module.iter_coqtel_electrochemistry_rows(path,authorization=blank)))
    for record in json.loads(Path(os.environ['MATINTEGRITY_DELTA_FILE_MANIFEST']).read_text())['files']:
        assert Path(record['path']).suffix.lower() not in ('.h5','.hdf5','.xlsx','.zip','.csv') and not record['path'].startswith(('data/raw/','data/evidence/','data/derived/'))
    return {'partition':task,'parser_output_fabricated_pinned_policy_asserted':True,'source_order_repeated_time_signed_channels_authorization_digest':True,'actual_HDF5_or_pit_measurement_validated':False,'central_counts':artifact['central_counts']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-rights','lineage-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
