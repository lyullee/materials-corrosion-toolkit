"""Crack-arrest typed adapter on fabricated signed/zero observations only."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from pydantic import ValidationError
from matintegrity import crack_arrest_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

class Frame:
    def __init__(self,digest): self.attrs={'source_archive_sha256':digest,'source_member':'synthetic/C1_20.csv','source_member_sha256':'b'*64,'specimen_id':'synthetic','test_family':'C1','reported_temperature_K':293.15,'temperature_origin':'filename_token_only; specimen_log_not_checked'}
    def __len__(self): return 3
    def itertuples(self,index=False): return iter([SimpleNamespace(time_s=float(i),machine_displacement_m=value*0.001,force_N=value,extensometer_displacement_m=value*0.0001,reported_cycle_index=0 if i<2 else 1) for i,value in enumerate((-1.0,0.0,2.0))])

def auth(): return module.CrackArrestReadAuthorization(attribution='Fabricated force/displacement adapter contract only.',computational_use_authorized=True,local_only_authorized=True)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported rights/parser boundary accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/crack_arrest_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert module.ARCHIVE_SHA256==artifact['archive_pin'] and module.ARCHIVE_BYTES==artifact['archive_bytes']
    for cls in (module.CrackArrestReadAuthorization,module.CrackArrestArchiveAuditRequest,module.CrackArrestObservationRow): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    rights=artifact['source_rows']['datasets'][module.DATASET_ID];assert rights['license']=='CC-BY-4.0' and rights['rights_status']=='reviewed_license'
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/module.ARCHIVE_FILENAME;content=b'Synthetic opaque payload; no provider archive accessed.';path.write_bytes(content);digest=hashlib.sha256(content).hexdigest();module.ARCHIVE_SHA256=digest;module.ARCHIVE_BYTES=len(content)
        def parser(source,specimen_id):
            if specimen_id!='synthetic': raise ValueError('synthetic specimen unsupported')
            return Frame(digest)
        module.read_crack_arrest_series=parser;authorization=auth();auth_digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='schema-rights':
            registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.CrackArrestArchiveAuditRequest(local_archive_path=str(path),specimen_id='synthetic',authorization=authorization)
            result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds'))
            assert result.status=='computed' and result.values['source_row_count']==3 and result.values['authorization_sha256']==auth_digest
            assert not result.values['point_values_returned'] and not result.values['local_path_returned'] and not result.values['toughness_inferred'] and not result.values['acceptance_inferred'] and str(path) not in json.dumps(result.values)
            assert artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
        else:
            rows=list(module.iter_crack_arrest_observation_rows(path,'synthetic',authorization=authorization))
            assert [r.source_row_order for r in rows]==[0,1,2] and [r.provider_source_row for r in rows]==[2,3,4] and [r.force_N for r in rows]==[-1.0,0.0,2.0]
            assert [r.machine_displacement_m for r in rows]==[-0.001,0.0,0.002] and [r.reported_cycle_index for r in rows]==[0,0,1]
            assert len({r.source_row_sha256 for r in rows})==3 and all(r.authorization_sha256==auth_digest and r.source_archive_sha256==digest and r.source_member_sha256=='b'*64 and r.local_only and r.evidence.license_id=='CC-BY-4.0' and r.force_unit=='N' and r.displacement_unit=='m' and not r.toughness_inferred and not r.acceptance_inferred for r in rows)
            assert all('specimen_log_not_checked' in r.temperature_provenance for r in rows)
            rejects(lambda:next(module.iter_crack_arrest_observation_rows(path,'missing',authorization=authorization)))
            for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
                values=authorization.model_dump(mode='json');values.update(change);rejects(lambda:module.CrackArrestReadAuthorization.model_validate_json(json.dumps(values)))
            module.read_crack_arrest_series=lambda source,specimen_id:Frame('f'*64);rejects(lambda:next(module.iter_crack_arrest_observation_rows(path,'synthetic',authorization=authorization)))
            path.write_bytes(b'changed');rejects(lambda:module._verify_archive(path))
    return {'partition':task,'fabricated_signed_zero_preserving_adapter_rows':True,'archive_member_authorization_evidence_row_lineage':True,'actual_fracture_toughness_or_acceptance_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-rights','lineage-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
