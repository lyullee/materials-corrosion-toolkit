"""Incremental authorization digest lineage on fabricated two-row Metro data."""
import argparse
import json
from pathlib import Path
import tempfile
from pydantic import ValidationError
import hpc_metropt3_delta_20261031 as fixture
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def check():
    metro=fixture.metro
    artifact=json.loads((ROOT/'metadata/metropt3_snapshot.json').read_text())
    assert artifact['schemas']['MetroPT3Row']==metro.MetroPT3Row.model_json_schema()
    assert artifact['source_rows']==artifact['package_rows']
    with tempfile.TemporaryDirectory() as folder:
        path=fixture.fixture(Path(folder));authorization=fixture.authorization();digest=canonical_digest(authorization.model_dump(mode='json'))
        rows=list(metro.iter_metropt3_rows(path,authorization=authorization))
        assert len(rows)==2 and all(row.authorization_sha256==digest and row.attribution==authorization.attribution and row.local_only for row in rows)
        changed=rows[0].model_dump(mode='json');changed.pop('authorization_sha256')
        try: metro.MetroPT3Row.model_validate_json(json.dumps(changed))
        except ValidationError: pass
        else: raise AssertionError('row without authorization lineage accepted')
    return {'authorization_digest_attribution_local_only_preserved':True,'missing_authorization_digest_rejected':True,'actual_provider_archive_read':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['authorization'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check()
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
