"""Mock compilation rows retain unresolved observation rights and censored values."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from pydantic import ValidationError
from matintegrity import corrosion_metrics_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry
ROOT=Path(__file__).resolve().parents[1]

class Frame:
    attrs={'source_workbook_sha256':module.SOURCE_SHA256}
    source_observation_id=SimpleNamespace(nunique=lambda:1)
    def __len__(self): return 2
    def itertuples(self,index=False):
        return iter([SimpleNamespace(source_sheet='synthetic',source_row=i+3,source_number=0,observation_id='metric-'+str(i),source_observation_id='source-1',metric='potential',statistic='reported',raw_value=raw,value_status=status,qualifier=qualifier,reported_value=number,source_unit='mV',normalized_value=number/1000,normalized_unit='V',potential_reference=None,composition_wt_percent={'Fe':90.0,'Cr':10.0},composition_raw={'Fe':'90','Cr':'10'},material_class='synthetic',conditions={'temperature':None},reference_number=None,underlying_reference_doi=None,underlying_reference_citation=None,source_group_id=None) for i,(raw,status,qualifier,number) in enumerate(((0.0,'exact',None,0.0),('<1','upper_bound','<',1.0)))])

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('compilation rights boundary widened')

def check(task):
    artifact=json.loads((ROOT/'metadata/alloy_metrics_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.CorrosionMetricsArchiveAuditRequest.model_json_schema()
    module._verify_workbook=lambda path:(module.SOURCE_MD5,module.SOURCE_SHA256,module.SOURCE_BYTES)
    def parser(path,*,require_pinned_hash): assert require_pinned_hash;return Frame()
    module.read_corrosion_alloy_metrics=parser;path=Path('synthetic-never-opened')/module.SOURCE_FILENAME
    auth=module.CorrosionMetricsReadAuthorization(attribution='Fabricated compilation adapter test only.',computational_use_authorized=True,local_only_authorized=True);digest=canonical_digest(auth.model_dump(mode='json'))
    if task=='rights-scope-local-only':
        registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.CorrosionMetricsArchiveAuditRequest(local_workbook_path=str(path),authorization=auth);result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='literature_record_order'))
        assert result.status=='computed' and result.values['compilation_license_id']=='CC-BY-4.0' and result.values['compilation_license_scope']==module.LICENSE_SCOPE and result.values['underlying_observation_rights_status']=='unresolved' and result.values['local_only'] and not result.values['point_values_returned'] and result.values['source_observation_count']==1
        assert result.values['authorization_sha256']==digest and str(path) not in json.dumps(result.values)
    else:
        rows=list(module.iter_corrosion_metric_observation_rows(path,authorization=auth));assert [r.source_order for r in rows]==[0,1] and [r.provider_source_row for r in rows]==[3,4]
        assert rows[0].normalized_value==0.0 and rows[1].raw_value=='<1' and rows[1].value_status=='upper_bound' and rows[1].qualifier=='<' and rows[1].normalized_value==0.001
        assert rows[0].source_row_sha256!=rows[1].source_row_sha256 and all(r.authorization_sha256==digest and r.compilation_license_scope==module.LICENSE_SCOPE and r.underlying_observation_rights_status=='unresolved' and r.physical_specimen_id is None and r.local_only and not r.ranking_inferred and 'compilation license only' in r.evidence.citation for r in rows)
        for change in ({'license_scope':'underlying_observations_cleared'},{'local_only_authorized':False},{'computational_use_authorized':False}):
            values=auth.model_dump(mode='json');values.update(change);rejects(lambda:module.CorrosionMetricsReadAuthorization.model_validate_json(json.dumps(values)))
        bad=Frame();bad.attrs={'source_workbook_sha256':'f'*64};module.read_corrosion_alloy_metrics=lambda *args,**kwargs:bad;rejects(lambda:next(module.iter_corrosion_metric_observation_rows(path,authorization=auth)))
    return {'partition':task,'mock_parser_no_workbook_opened':True,'compilation_only_CC_BY_underlying_rights_unresolved':True,'no_ranking_or_clearance_claim':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['rights-scope-local-only','row-order-lineage-fail-closed'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(a.task)
    except Exception as e: a.output.write_text(json.dumps({'status':'failed','error':str(e)},indent=2));raise
    a.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
