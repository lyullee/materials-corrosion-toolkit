"""Synthetic programme/independent records with compilation-only local rights."""
import argparse,json
from pathlib import Path
from pydantic import ValidationError
from matintegrity import atmospheric_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry
ROOT=Path(__file__).resolve().parents[1]

def records():
    rows=[]
    for i,partition in enumerate(('programme','independent')):
        values={'observation_id':'synthetic-'+partition,'provider_partition':partition,'provider_source_row':7 if i==0 else 3,'source_group_id':'synthetic-group','provider_source_id':'synthetic-source','country':'synthetic','site':'synthetic','latitude_deg':0.0,'longitude_deg':0.0,'reported_first_year_rate_um_year':10.0,'first_year_loss_m':1e-5,'equivalent_first_year_rate_m_s':1e-5/31557600.0,'era5_cell_id':'synthetic-cell','era5_corrected_temperature_K':293.15,'era5_relative_humidity_fraction':0.5,'era5_wet_hours_rh80_per_year':100.0,'era5_wet_hour_mean_temperature_K':293.15,'era5_annual_precipitation_m':0.1,'source_archive_sha256':module.PINNED_ARCHIVE_SHA256}
        values.update({'programme_id':'synthetic-programme','provider_site_id':'synthetic-site'} if partition=='programme' else {'provider_tier':'A','provider_rate_source':'table'})
        rows.append(module.AtmosphericCorrosionObservation.model_validate_json(json.dumps(values)))
    return rows

def check(task):
    artifact=json.loads((ROOT/'metadata/atmospheric_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.AtmosphericArchiveAuditRequest.model_json_schema()
    module._validate_local_archive=lambda path:module.ARCHIVE_BYTES
    def parser(path,*,partition,require_pinned_hash):
        assert require_pinned_hash
        return [r for r in records() if partition=='both' or r.provider_partition==partition]
    module.read_atmospheric_corrosion_observations=parser;source=Path('synthetic-never-opened')/module.ARCHIVE_FILENAME
    auth=module.AtmosphericReadAuthorization(attribution='Fabricated atmospheric compilation records only.',computational_use_authorized=True,underlying_observation_use_authorized=True,local_only_authorized=True);digest=canonical_digest(auth.model_dump(mode='json'))
    if task=='compilation-rights-local-only':
        registry=ModelRegistry();registry.register(module.specifications()[0]);result=registry.run(module.MODEL_ID,module.AtmosphericArchiveAuditRequest(local_archive_path=str(source),authorization=auth),RunContext(asset_id='synthetic',location_id='synthetic',time_basis='first_year_observation'))
        assert result.status=='computed' and result.values['programme_row_count']==1 and result.values['independent_row_count']==1 and result.values['license_scope']==module.LICENSE_SCOPE and result.values['underlying_observation_rights_status']=='unresolved' and result.values['local_only'] and not result.values['point_values_returned']
    else:
        rows=list(module.iter_atmospheric_corrosion_typed_rows(source,authorization=auth));assert [r.source_order for r in rows]==[0,1] and [r.provider_source_row for r in rows]==[7,3] and [r.provider_partition for r in rows]==['programme','independent']
        assert rows[0].source_row_sha256!=rows[1].source_row_sha256 and all(r.authorization_sha256==digest and r.license_scope==module.LICENSE_SCOPE and r.underlying_observation_rights_status=='unresolved' and r.parsed_record.first_year_loss_m==1e-5 and r.local_only and not r.long_term_rate_inferred and not r.localized_corrosion_inferred for r in rows)
        for change in ({'license_scope':'all_observations_cleared'},{'underlying_observation_use_authorized':False},{'local_only_authorized':False}):
            values=auth.model_dump(mode='json');values.update(change)
            try: module.AtmosphericReadAuthorization.model_validate_json(json.dumps(values))
            except ValidationError: pass
            else: raise AssertionError('underlying-use/rights boundary widened')
        bad=records()[0].model_copy(update={'source_archive_sha256':'f'*64});module.read_atmospheric_corrosion_observations=lambda *args,**kwargs:[bad]
        try: next(module.iter_atmospheric_corrosion_typed_rows(source,authorization=auth))
        except ValueError: pass
        else: raise AssertionError('parser/archive digest mismatch accepted')
    return {'partition':task,'mock_parser_no_raw_archive_access':True,'compilation_only_underlying_rights_unresolved':True,'actual_long_term_corrosion_or_remaining_life_validated':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['compilation-rights-local-only','source-order-lineage-fail-closed'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(a.task)
    except Exception as e: a.output.write_text(json.dumps({'status':'failed','error':str(e)},indent=2));raise
    a.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
