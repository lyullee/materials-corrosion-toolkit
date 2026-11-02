"""Synthetic training/testing rows retain compilation-only rights and unit ambiguity."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from pydantic import ValidationError
from matintegrity import fracture_toughness_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry
ROOT=Path(__file__).resolve().parents[1]

class Frame:
    attrs={'source_archive_sha256':module.ARCHIVE_SHA256,'source_member_sha256':module.WORKBOOK_MEMBER_SHA256}
    source_partition=np.array(['training','test'])
    def __len__(self): return 2
    def itertuples(self,index=False):
        rows=[]
        for i,partition in enumerate(('training','test')):
            values={'source_partition':partition,'source_sheet':partition,'source_row':i+5,'reported_record_id':i+1,'observation_id':'synthetic-'+str(i),'material_label':'synthetic','carbon_wt_percent':0.1,'carbon_mass_fraction':0.001,'reported_temperature':293.15,'reported_temperature_unit_label':'K','temperature_K':None,'temperature_unit_override':None,'temperature_unit_basis':'unresolved','yield_strength_MPa':500.0,'yield_strength_Pa':500e6,'specimen_type':'CT','reported_CT_flag':1,'reported_SEB_flag':0,'reported_PCCv_flag':0,'reported_W':1.0,'reported_B':1.0,'reported_a':0.5,'W_m':None,'B_m':None,'a_m':None,'dimension_unit_override':None,'dimension_unit_basis':'unresolved','reported_KJc_MPa_sqrt_m':50.0,'reported_KJc_Pa_sqrt_m':50e6,'article_source_group_status':'unresolved','article_reference_identity_status':'unresolved','article_reference_observation_rights_status':'unresolved','condition_group_status':'unresolved'}
            values.update({key:None for key in ('article_source_group_id','article_source_material_label','article_reference_bibliographic_id','article_reference_publication_license_id','condition_group_id','condition_group_W_center_m','condition_group_B_center_m')});rows.append(SimpleNamespace(**values))
        return iter(rows)

def check(task):
    artifact=json.loads((ROOT/'metadata/fracture_compilation_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.FractureToughnessArchiveAuditRequest.model_json_schema();assert artifact['row_schema']==module.FractureToughnessObservationRow.model_json_schema()
    module._verify_archive=lambda source:(module.ARCHIVE_SHA256,module.ARCHIVE_BYTES);module.read_fracture_toughness_temperature=lambda *args,**kwargs:Frame()
    source=Path('synthetic-never-opened')/module.ARCHIVE_FILENAME;auth=module.FractureToughnessReadAuthorization(attribution='Fabricated compilation split-row contract only.',computational_use_authorized=True,local_only_authorized=True,parser_unit_interpretations_reviewed=True);digest=canonical_digest(auth.model_dump(mode='json'))
    if task=='compilation-rights-local-only':
        registry=ModelRegistry();registry.register(module.specifications()[0]);result=registry.run(module.MODEL_ID,module.FractureToughnessArchiveAuditRequest(local_archive_path=str(source),authorization=auth),RunContext(asset_id='synthetic',location_id='synthetic',time_basis='compilation_source_order'))
        assert result.status=='computed' and result.values['training_partition_rows']==1 and result.values['test_partition_rows']==1 and 'testing_partition_rows' not in result.values and result.values['compilation_license_scope']==module.LICENSE_SCOPE and result.values['underlying_observation_rights_status']=='unresolved' and result.values['local_only'] and not result.values['point_values_returned']
    else:
        rows=list(module.iter_fracture_toughness_observation_rows(source,authorization=auth));assert [r.source_partition for r in rows]==['training','test'] and [r.provider_source_row for r in rows]==[5,6] and [r.source_order for r in rows]==[0,1]
        assert rows[0].source_row_sha256!=rows[1].source_row_sha256 and all(r.authorization_sha256==digest and r.source_workbook_sha256==module.WORKBOOK_MEMBER_SHA256 and r.underlying_observation_rights_status=='unresolved' and r.physical_specimen_id is None and r.temperature_K is None and r.W_m is None and r.local_only and not r.toughness_validity_inferred and not r.acceptance_inferred for r in rows)
        for change in ({'license_scope':'all_observations_cleared'},{'local_only_authorized':False},{'parser_unit_interpretations_reviewed':False}):
            values=auth.model_dump(mode='json');values.update(change)
            try: module.FractureToughnessReadAuthorization.model_validate_json(json.dumps(values))
            except ValidationError: pass
            else: raise AssertionError('compilation rights/unit boundary widened')
    return {'partition':task,'mock_parser_no_raw_archive_access':True,'compilation_only_underlying_rights_and_units_unresolved':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['compilation-rights-local-only','exact-source-label-row-lineage'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(a.task)
    except Exception as e: a.output.write_text(json.dumps({'status':'failed','error':str(e)},indent=2));raise
    a.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
