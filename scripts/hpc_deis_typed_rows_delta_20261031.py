"""DEIS typed adapter over fabricated matrix rows and an explicitly mocked archive manifest."""
import argparse,hashlib,json
from pathlib import Path
import tempfile
from pydantic import ValidationError
from matintegrity import zenodo_deis_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def auth(): return module.ZenodoDeisReadAuthorization(attribution='Fabricated DEIS matrix adapter contract only.',computational_use_authorized=True,local_only_authorized=True)

def manifest():
    members=tuple(module.DeisMatrixMember(member_path=name,declared_material_label=label,member_sha256=('a' if label=='AZ31' else 'b')*64,member_bytes=20,row_count=2,column_count=3,blank_cell_count=0,nonfinite_cell_count=0) for name,label in module.MEMBER_MATERIAL.items())
    return module.ZenodoDeisArchiveManifest(archive_sha256=module.ARCHIVE_SHA256,archive_bytes=module.ARCHIVE_BYTES,matrices=members)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported DEIS local-only contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/deis_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert module.ARCHIVE_SHA256==artifact['archive_pin']
    for cls in (module.ZenodoDeisReadAuthorization,module.ZenodoDeisMatrixAuditRequest,module.ZenodoDeisMatrixRow): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    assert artifact['source_rows']['datasets'][module.DATASET_ID]['license']=='CC0-1.0'
    declared=manifest();member=declared.matrices[0].member_path
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/module.ARCHIVE_FILENAME;content=b'Synthetic opaque payload, not provider archive.';path.write_bytes(content);module.ARCHIVE_BYTES=len(content);module.ARCHIVE_MD5=hashlib.md5(content).hexdigest()
        module._pinned_manifest=lambda source:declared
        module.iter_zenodo_deis_rows=lambda source,manifest,member:iter(((0.0,2.0,-1.0),(3.0,0.0,4.0)))
        authorization=auth();digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='schema-rights':
            request=module.ZenodoDeisMatrixAuditRequest(local_archive_path=str(path),source_member_path=member,authorization=authorization);registry=ModelRegistry();registry.register(module.specifications()[0]);result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='unresolved_matrix_axes'))
            assert result.status=='computed' and result.values['source_row_count']==2 and result.values['source_column_count']==3 and result.values['authorization_sha256']==digest and not result.values['numeric_values_returned'] and result.values['local_only']
            assert result.values['axis_mapping']=='unresolved' and artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
        else:
            rows=list(module.iter_zenodo_deis_typed_rows(path,declared,member,authorization=authorization))
            assert [r.source_row_order for r in rows]==[0,1] and [r.provider_row_number for r in rows]==[1,2] and rows[0].matrix_values_as_provided==(0.0,2.0,-1.0)
            assert rows[0].source_row_sha256!=rows[1].source_row_sha256 and all(r.authorization_sha256==digest and r.local_only and r.evidence.license_id=='CC0-1.0' and r.source_member_sha256==declared.matrices[0].member_sha256 and r.units_mapping=='unresolved' and r.row_axis_mapping=='unresolved' and not r.frequency_axis_inferred and not r.material_performance_inferred for r in rows)
            for change in ({'license_id':'CC-BY-4.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
                values=authorization.model_dump(mode='json');values.update(change);rejects(lambda:module.ZenodoDeisReadAuthorization.model_validate_json(json.dumps(values)))
            values=authorization.model_dump(mode='json');values['attribution']=' ';blank=module.ZenodoDeisReadAuthorization.model_validate_json(json.dumps(values));rejects(lambda:next(module.iter_zenodo_deis_typed_rows(path,declared,member,authorization=blank)))
            module.ARCHIVE_MD5='f'*32;rejects(lambda:next(module.iter_zenodo_deis_typed_rows(path,declared,member,authorization=authorization)))
    return {'partition':task,'synthetic_matrix_rows_and_mock_archive_manifest_only':True,'actual_archive_or_EIS_axis_interpretation_validated':False,'local_only_and_source_row_order_preserved':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-rights','row-order-local-only'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error: args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
