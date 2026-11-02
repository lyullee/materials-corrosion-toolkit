"""Incremental caller-attribution lineage only, using two fabricated CSV rows."""
import argparse
import json
from pathlib import Path
import tempfile
import hpc_metropt3_delta_20261031 as fixture

ROOT=Path(__file__).resolve().parents[1]

def check():
    metro=fixture.metro
    artifact=json.loads((ROOT/'metadata/metropt3_snapshot.json').read_text())
    for cls in (metro.MetroPT3ArchiveAuthorization,metro.MetroPT3ArchiveAuditRequest,metro.MetroPT3Row): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    assert artifact['source_rows']==artifact['package_rows']
    with tempfile.TemporaryDirectory() as folder:
        path=fixture.fixture(Path(folder));authorization=fixture.authorization()
        rows=list(metro.iter_metropt3_rows(path,authorization=authorization))
        assert len(rows)==2 and all(row.attribution==authorization.attribution for row in rows)
        request=metro.MetroPT3ArchiveAuditRequest(local_archive_path=str(path),authorization=authorization)
        result=metro.audit_metropt3_archive(request)
        assert result.values['attribution']==authorization.attribution
        assert not result.values['local_path_returned'] and str(path) not in json.dumps(result.values)
        return {'caller_CC_BY_attribution_preserved_in_each_row_and_audit':True,'selected_schema_catalog_parity':True,'actual_archive_scanned':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['attribution'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check()
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
