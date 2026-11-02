"""Synthetic asset-identity and typed adapter boundaries; actual XLSX parser is mocked."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from matintegrity import galvanized_polarization_rows as module
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

class Column:
    def __init__(self,values): self.values=values
    def unique(self): return sorted(set(self.values))

class Frame:
    electrolyte_id=Column(['synthetic'])
    specimen_id=Column(['synthetic'])
    def __len__(self): return 3
    def itertuples(self,index=False):
        return iter([SimpleNamespace(source_row=i+3,specimen_id='synthetic',electrolyte_id='synthetic',potential_V=-0.5+i*0.1,signed_current_density_A_m2=current) for i,current in enumerate((-2.0,0.0,3.0))])

def rejects(factory):
    try: factory()
    except ValueError: return
    raise AssertionError('unsupported identity accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/galvanized_rows_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.GalvanizedPolarizationArchiveAuditRequest.model_json_schema();assert artifact['row_schema']==module.GalvanizedPolarizationSample.model_json_schema()
    assert {k:list(v) for k,v in module.ASSETS.items()}==artifact['asset_pins']
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);name=next(iter(module.ASSETS));path=folder/name;content=b'Synthetic opaque payload; never parsed as real workbook.';path.write_bytes(content);md5=hashlib.md5(content).hexdigest();sha=hashlib.sha256(content).hexdigest();module.ASSETS=dict(module.ASSETS);module.ASSETS[name]=(md5,len(content))
        if task=='asset-contract':
            assert module._asset_identity(path)==(md5,len(content),sha)
            unknown=folder/'unlisted.xlsx';unknown.write_bytes(content);rejects(lambda:module._asset_identity(unknown))
            module.ASSETS[name]=('f'*32,len(content));rejects(lambda:module._asset_identity(path));module.ASSETS[name]=(md5,len(content)+1);rejects(lambda:module._asset_identity(path))
        else:
            module.read_galvanized_polarization=lambda source:Frame()
            auth=module.GalvanizedPolarizationReadAuthorization(attribution='Fabricated adapter verification only.',computational_use_authorized=True,local_only_authorized=True);digest=canonical_digest(auth.model_dump(mode='json'));rows=list(module.iter_galvanized_polarization_samples(path,authorization=auth))
            assert [r.signed_current_density_A_m2 for r in rows]==[-2.0,0.0,3.0] and [r.provider_source_row for r in rows]==[3,4,5]
            assert all(r.authorization_sha256==digest and r.source_file_sha256==sha and r.source_file_md5==md5 and r.local_only and not r.corrosion_rate_inferred and not r.tafel_extrapolation_performed for r in rows)
            assert rows[0].current_density_provider_A_cm2==-0.0002 and rows[2].current_density_provider_A_cm2==0.0003
            result=module.audit_galvanized_polarization_workbook(module.GalvanizedPolarizationArchiveAuditRequest(local_workbook_path=str(path),authorization=auth))
            assert result.values['sample_count']==3 and result.values['authorization_sha256']==digest and not result.values['sample_values_returned'] and str(path) not in json.dumps(result.values)
    return {'partition':task,'exact_current_central_counts':artifact['central_counts'],'synthetic_asset_and_parser_frame_only':True,'actual_workbook_or_electrochemical_fit_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['asset-contract','typed-lineage'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
