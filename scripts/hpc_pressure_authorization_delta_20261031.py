"""New authorization digest propagation paths; no actual workbook is read."""
import argparse
import json
from pathlib import Path
import tempfile
import hpc_pressure_decay_delta_20261031 as fixture
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def check(task):
    module=fixture.decay
    artifact=json.loads((ROOT/'metadata/pressure_decay_snapshot.json').read_text())
    assert artifact['schemas']['PressureDecayLeakSample']==module.PressureDecayLeakSample.model_json_schema()
    with tempfile.TemporaryDirectory() as folder:
        path,_=fixture.fixture(Path(folder));authorization=fixture.authorization();digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='stream-authorization':
            rows=list(module.iter_pressure_decay_leak_samples(path,authorization=authorization))
            assert len(rows)==310 and all(row.authorization_sha256==digest and row.local_only and row.attribution==authorization.attribution for row in rows)
            changed=authorization.model_dump(mode='json');changed['attribution']='Distinct caller attribution for identical synthetic observations.'
            changed=module.PressureDecayLeakReadAuthorization.model_validate_json(json.dumps(changed))
            replay=next(module.iter_pressure_decay_leak_samples(path,authorization=changed))
            assert replay.authorization_sha256==canonical_digest(changed.model_dump(mode='json')) and replay.authorization_sha256!=rows[0].authorization_sha256
            assert replay.source_file_sha256==rows[0].source_file_sha256 and replay.pressure_Pa==rows[0].pressure_Pa
        else:
            request=module.PressureDecayLeakArchiveAuditRequest(local_archive_path=str(path),authorization=authorization)
            result=module.audit_pressure_decay_leak_archive(request)
            assert result.values['request_authorization_sha256']==digest and result.values['attribution']==authorization.attribution
            assert str(path) not in json.dumps(result.values) and not result.values['leak_rate_inferred']
    return {'partition':task,'new_authorization_digest_runtime_propagation':True,'fabricated_workbook_only':True,'previous_full_reader_suite_replayed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['stream-authorization','audit-authorization'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
