"""Thermal typed adapter contracts on tiny opaque bytes and fabricated parser rows."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from pydantic import ValidationError
from matintegrity import thermal_typed_rows as module
from matintegrity.contracts import RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

class Frame:
    def __init__(self,digest): self.attrs={'source_archive_sha256':digest,'source_member':'synthetic/run.csv','source_member_sha256':'b'*64}
    def __len__(self): return 2
    def itertuples(self,index=False): return iter([SimpleNamespace(time_s=float(i*5),controller_setting_counts=float(100*(i+1)),**{f'tc{j}_excess_temperature_K':float(i+j-2) for j in range(1,7)}) for i in range(2)])

def auth(): return module.ThermalRodReadAuthorization(attribution='Fabricated thermal row adapter test only.',computational_use_authorized=True,local_only_authorized=True)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported reader/rights boundary accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/thermal_typed_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert module.ARCHIVE_SHA256==artifact['archive_pin'] and module.ARCHIVE_BYTES==artifact['archive_bytes']
    for cls in (module.ThermalRodReadAuthorization,module.ThermalRodArchiveAuditRequest,module.ThermalRodObservationRow): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    rights=artifact['source_rows']['datasets'][module.DATASET_ID];assert rights['license']=='CC-BY-4.0' and rights['rights_status']=='reviewed_license'
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/module.ARCHIVE_FILENAME;data=b'Fabricated opaque bytes; not an actual ZIP archive.';path.write_bytes(data);digest=hashlib.sha256(data).hexdigest();module.ARCHIVE_SHA256=digest;module.ARCHIVE_BYTES=len(data)
        def parser(source,run_id):
            if run_id!='synthetic': raise ValueError('synthetic parser fixture run unsupported')
            return Frame(digest)
        module.read_thermal_rod_series=parser;authorization=auth();authorization_digest=canonical_digest(authorization.model_dump(mode='json'))
        if task=='schema-rights':
            registry=ModelRegistry();registry.register(module.specifications()[0]);request=module.ThermalRodArchiveAuditRequest(local_archive_path=str(path),run_id='synthetic',authorization=authorization)
            result=registry.run(module.MODEL_ID,request,RunContext(asset_id='synthetic',location_id='synthetic',time_basis='elapsed_seconds'))
            assert result.status=='computed' and result.values['source_row_count']==2 and result.values['authorization_sha256']==authorization_digest
            assert not result.values['point_values_returned'] and not result.values['controller_setting_converted_to_power'] and not result.values['thermal_properties_inferred'] and str(path) not in json.dumps(result.values)
            assert artifact['source_rows']['capabilities'][module.MODEL_ID]['input_schema']==registry.describe(module.MODEL_ID)['input_schema']
        else:
            rows=list(module.iter_thermal_rod_observation_rows(path,'synthetic',authorization=authorization))
            assert [r.source_row_order for r in rows]==[0,1] and [r.provider_source_row for r in rows]==[2,3] and [r.time_s for r in rows]==[0.0,5.0]
            assert [r.tc1_excess_temperature_K for r in rows]==[-1.0,0.0] and [r.controller_setting_counts for r in rows]==[100.0,200.0]
            assert rows[0].source_row_sha256!=rows[1].source_row_sha256 and all(r.authorization_sha256==authorization_digest and r.source_archive_sha256==digest and r.source_member_sha256=='b'*64 and r.local_only and r.evidence.license_id=='CC-BY-4.0' and not r.heat_flux_inferred and not r.corrosion_metric_inferred for r in rows)
            assert all('kelvin_difference' in r.temperature_basis and 'not_power' in r.controller_setting_basis for r in rows)
            rejects(lambda:next(module.iter_thermal_rod_observation_rows(path,'unavailable',authorization=authorization)))
            for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
                values=authorization.model_dump(mode='json');values.update(change);rejects(lambda:module.ThermalRodReadAuthorization.model_validate_json(json.dumps(values)))
            module.read_thermal_rod_series=lambda source,run_id:Frame('f'*64);rejects(lambda:next(module.iter_thermal_rod_observation_rows(path,'synthetic',authorization=authorization)))
            path.write_bytes(b'changed');rejects(lambda:module._verify_archive(path))
    return {'partition':task,'synthetic_pin_and_parser_fixture_only':True,'source_header_row_units_archive_member_authorization_lineage':True,'actual_provider_archive_or_thermal_properties_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-rights','lineage-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
