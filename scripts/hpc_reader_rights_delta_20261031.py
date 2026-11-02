"""Metadata-only latest reader contracts; no provider files are read or staged."""
import argparse
import hashlib
import json
from pathlib import Path
from pydantic import ValidationError
from matintegrity import cathodic_protection_data as cp
from matintegrity import pressure_decay_leak_data as pressure
from matintegrity import metropt3_data as metro
from matintegrity.contracts import canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]
CONTRACTS=(cp.CathodicProtectionReadAuthorization,cp.CathodicProtectionArchiveAuditRequest,cp.CathodicProtectionSample,pressure.PressureDecayLeakReadAuthorization,pressure.PressureDecayLeakArchiveAuditRequest,pressure.PressureDecayLeakSample,metro.MetroPT3ArchiveAuthorization,metro.MetroPT3ArchiveAuditRequest,metro.MetroPT3Row)

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported contract accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/reader_rights_snapshot.json').read_text())
    assert artifact['source_rows']==artifact['package_rows']
    for cls in CONTRACTS: assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    if task=='schema-catalog':
        registry=ModelRegistry()
        for module in (cp,pressure,metro):
            spec=module.specifications()[0];registry.register(spec)
            assert registry.describe(spec.model_id)['input_schema']==artifact['source_rows']['capabilities'][spec.model_id]['input_schema']
            rejects(lambda:spec.input_type.model_validate_json('{}'))
        assert cp.SOURCE_FILES==artifact['cp_source_pins']
        assert pressure.SOURCE_SHA256==artifact['pressure_source_pin']
        assert metro.ARCHIVE_SHA256==artifact['metro_archive_pin']
        return {'latest_reader_schemas_ModelSpecs_catalog_source_package_parity':True,'real_reader_files_opened':False}
    authorizations=[]
    for cls in (cp.CathodicProtectionReadAuthorization,pressure.PressureDecayLeakReadAuthorization,metro.MetroPT3ArchiveAuthorization):
        values={'attribution':'Caller-owned synthetic CC BY attribution.','computational_use_authorized':True,'local_only_authorized':True}
        authorization=cls.model_validate_json(json.dumps(values));authorizations.append(authorization)
        for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False},{'attribution':''}):
            changed=dict(values,**change);rejects(lambda:cls.model_validate_json(json.dumps(changed)))
    cp_row={'attribution':authorizations[0].attribution,'authorization_sha256':canonical_digest(authorizations[0].model_dump(mode='json')),'source_filename':next(iter(cp.SOURCE_FILES)),'source_file_sha256':next(iter(cp.SOURCE_FILES.values())),'curve_record_sha256':'b'*64,'curve_index':1,'provider_curve_label':'synthetic','curve_sample_index':0,'measurement_kind':'open_circuit_potential','x_quantity':'time','x_unit':'s','x_value_provider_native':0.0,'potential_V_vs_calomel':-0.5}
    row=cp.CathodicProtectionSample.model_validate_json(json.dumps(cp_row))
    assert row.local_only and row.reference_electrode_subtype=='unresolved_calomel_subtype' and 'no_protection_or_corrosion_rate' in row.interpretation_status
    pressure_row={'attribution':authorizations[1].attribution,'authorization_sha256':canonical_digest(authorizations[1].model_dump(mode='json')),'source_file_sha256':pressure.SOURCE_SHA256,'source_sheet_name':'synthetic','series_id':'nitrogen-100mm','provider_gas_label':'synthetic','normalized_gas_label':'nitrogen','provider_capillary_length_m':0.1,'sample_index':0,'time_s':0.0,'temperature_K':293.15,'pressure_Pa':100000.0}
    row=pressure.PressureDecayLeakSample.model_validate_json(json.dumps(pressure_row))
    assert row.local_only and row.authorization_sha256==pressure_row['authorization_sha256'] and row.interpretation_status=='raw_pressure_temperature_not_leak_rate'
    for key in ('authorization_sha256','attribution'):
        changed=dict(pressure_row);changed.pop(key);rejects(lambda:pressure.PressureDecayLeakSample.model_validate_json(json.dumps(changed)))
    manifest=json.loads(Path(__import__('os').environ['MATINTEGRITY_DELTA_FILE_MANIFEST']).read_text())
    for record in manifest['files']:
        assert not record['path'].startswith(('data/raw/','data/evidence/','data/derived/'))
        assert Path(record['path']).suffix.lower() not in ('.zip','.xlsx','.csv','.pdf','.opju')
        assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
    return {'caller_attribution_authorization_digest_local_only_lineage':True,'no_corrosion_protection_or_leak_inference':True,'source_asset_exclusion_manifest':True,'actual_dataset_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['schema-catalog','rights-lineage'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
