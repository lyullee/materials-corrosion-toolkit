"""Static release boundary and incremental scope-linkage partitions only."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def check(task):
    artifact=load('metadata/release_scope_snapshot.json')
    capabilities={row['id']:row for row in load('data/catalogs/capabilities.json')['capabilities']}
    if task=='allowlist':
        spec=importlib.util.spec_from_file_location('boundary',ROOT/'scripts/build_release.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.validate_catalog_sync(ROOT)
        ignored=(ROOT/'.gitignore').read_text()
        manifest=(ROOT/'MANIFEST.in').read_text()
        for directory in ('data/raw','data/derived','data/evidence','tmp'):
            assert directory+'/' in ignored and 'prune '+directory in manifest
        selected=module.public_files()
        assert all(not p.relative_to(ROOT).as_posix().startswith(('data/raw/','data/evidence/','data/derived/','tmp/','hpc-results/')) for p in selected)
        with tempfile.TemporaryDirectory() as folder:
            fixture=Path(folder);(fixture/'src').mkdir();(fixture/'src/allowed.py').write_text('value = 1\n')
            for name in ('data/raw','data/evidence','tmp','hpc-results'):
                (fixture/name).mkdir(parents=True);(fixture/name/'private.txt').write_text('local excluded fixture')
            module.ROOT=fixture;module.validate_catalog_sync=lambda:None
            assert [p.relative_to(fixture).as_posix() for p in module.public_files()]==['src/allowed.py']
            for marker in module.FORBIDDEN_MARKERS:
                (fixture/'src/allowed.py').write_text(marker+'synthetic')
                try: module.public_files()
                except ValueError: pass
                else: raise AssertionError('local marker accepted')
            (fixture/'src/allowed.py').write_text('value = 1\n');(fixture/'src/asset.pdf').write_bytes(b'synthetic forbidden suffix')
            try: module.public_files()
            except ValueError: pass
            else: raise AssertionError('binary suffix accepted')
        return {'snapshot_public_files':len(selected),'local_asset_and_marker_probes':True,'legal_clearance':False,'scope':'source/catalog/schema closure, not complete release artifact'}
    if task=='scope-trace':
        rows=[r for r in load('data/catalogs/implementation_scope_audit.json')['items'] if r['classification']=='code_incomplete']
        assert len(rows)==4
        count=0
        for row in rows:
            parent=capabilities[row['capability_id']]
            assert set(row['implemented_components'])<=set(capabilities)
            assert set(parent.get('implemented_components',[]))<=set(row['implemented_components'])
            for path in row['source_paths']:
                content=(ROOT/path).read_bytes();ast.parse(content.decode('utf-8'));count+=1
            for record in row.get('source_path_audit',[]):
                if record['path'] in row['source_paths']:
                    actual=hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()
                    assert record['sha256']==actual,'stale source-path evidence: '+record['path']
            for record in row.get('code_symbol_evidence_audit',[]):
                tree=ast.parse((ROOT/record['path']).read_text(encoding='utf-8'))
                assert record['symbol'] in {node.name for node in ast.walk(tree) if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
            assert row['implementation_complete'] is False
        return {'rows':4,'ast_path_occurrences':count,'incremental_parent_child_paths':True,'full_scope_completion_claimed':False}
    sources={row['id'] for row in load('data/catalogs/sources.json')['sources']}
    for name in ('capabilities','sources','datasets'):
        assert (ROOT/f'data/catalogs/{name}.json').read_bytes()==(ROOT/f'src/matintegrity/catalog_data/{name}.json').read_bytes()
    for row in capabilities.values():
        assert all(identifier in capabilities for identifier in row.get('implemented_components',[]))
        for identifier in row.get('source_ids',[]): assert identifier in sources
    schema_paths=sorted((ROOT/'docs/schemas').glob('*.json'))
    for path in schema_paths:
        value=json.loads(path.read_text(encoding='utf-8'));assert isinstance(value,dict)
    for entry in artifact['files']:
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    return {'capabilities':len(capabilities),'sources':len(sources),'schemas':len(schema_paths),'package_parity_and_snapshot_hashes':True,'numerical_tests_executed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['allowlist','scope-trace','closure'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
