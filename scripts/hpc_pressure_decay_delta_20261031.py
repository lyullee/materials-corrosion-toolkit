"""Synthetic workbook layout, typed-row and attribution checks only."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from openpyxl import Workbook
from pydantic import ValidationError
from matintegrity import pressure_decay_leak_data as decay

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_READER=decay.read_pressure_decay_leak_workbook

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported input accepted')

def fixture(folder,mutate=None):
    book=Workbook();sheet=book.active;sheet.title='synthetic'
    sheet.cell(1,1,'Testing gas');sheet.cell(2,1,'Lenght of capilar [mm]');sheet.cell(3,1,'Time t [s]')
    for raw,gas,length,tcol,pcol in decay.SERIES_COLUMNS:
        if length==100.0: sheet.cell(1,tcol,raw)
        sheet.cell(2,tcol,f'{int(length)} mm');sheet.cell(3,tcol,'Temperatures T [°C]');sheet.cell(3,pcol,'Pressure [Pa]')
        for index,row in enumerate(range(4,35)):
            sheet.cell(row,1,index*30.0);sheet.cell(row,tcol,20.0);sheet.cell(row,pcol,100000.0-index*10.0)
    if mutate: mutate(sheet)
    path=folder/'synthetic.xlsx';book.save(path);book.close();digest=hashlib.sha256(path.read_bytes()).hexdigest()
    decay.read_pressure_decay_leak_workbook=lambda path:ORIGINAL_READER(path,expected_sha256=digest)
    return path,digest

def authorization(): return decay.PressureDecayLeakReadAuthorization(attribution='Synthetic fixture only; caller CC BY attribution semantics.',computational_use_authorized=True,local_only_authorized=True)

def check(task):
    artifact=json.loads((ROOT/'metadata/pressure_decay_snapshot.json').read_text())
    assert artifact['source_rows']==artifact['package_rows']
    for cls in (decay.PressureDecayLeakReadAuthorization,decay.PressureDecayLeakArchiveAuditRequest,decay.PressureDecayLeakSample): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    assert artifact['source_sha256']==decay.SOURCE_SHA256
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);path,digest=fixture(folder)
        if task=='layout':
            times,arrays,audit=decay.read_pressure_decay_leak_workbook(path)
            assert len(times)==31 and times.tolist()==list(range(0,901,30)) and len(arrays)==10 and audit.total_samples==310
            assert all(temperature[0]==293.15 for temperature,pressure in arrays.values())
            rejects(lambda:ORIGINAL_READER(path,expected_sha256='f'*64))
            for mutate in (lambda s:s.cell(4,1,-1.0),lambda s:s.cell(5,1,0.0),lambda s:s.cell(3,2,'wrong-unit'),lambda s:s.delete_rows(34)):
                changed,_=fixture(folder,mutate);rejects(lambda:decay.read_pressure_decay_leak_workbook(changed))
            return {'synthetic_31_knots_ten_series_310_samples':True,'SI_temperature_conversion':True,'digest_layout_time_unit_gates':True,'real_workbook_read':False}
        if task=='typed-rows':
            rows=list(decay.iter_pressure_decay_leak_samples(path,authorization=authorization()))
            assert len(rows)==310 and len({r.series_id for r in rows})==10
            for index,row in enumerate(rows):
                assert row.sample_index==index%31 and row.time_s==(index%31)*30.0 and row.source_file_sha256==digest and row.attribution==authorization().attribution
            values=rows[0].model_dump(mode='json')
            for bad in (-1,31,True,1.0):
                changed=dict(values,sample_index=bad);rejects(lambda:decay.PressureDecayLeakSample.model_validate_json(json.dumps(changed)))
            return {'typed_row_series_index_time_digest_attribution':True,'index_strictness':True,'raw_workbook_transmitted':False}
        result=decay.audit_pressure_decay_leak_archive(decay.PressureDecayLeakArchiveAuditRequest(local_archive_path=str(path),authorization=authorization()))
        assert result.values['attribution']==authorization().attribution and result.values['sample_count']==310
        assert not result.values['leak_rate_inferred'] and not result.values['local_path_returned'] and str(path) not in json.dumps(result.values)
        assert 'not a leak rate or acceptance' in result.values['interpretation_limit']
        for change in ({'license_id':'CC0-1.0'},{'computational_use_authorized':False},{'local_only_authorized':False}):
            changed=authorization().model_dump(mode='json');changed.update(change);rejects(lambda:decay.PressureDecayLeakReadAuthorization.model_validate_json(json.dumps(changed)))
        return {'CC_BY_attribution_and_authorizations':True,'no_leak_rate_acceptance_or_local_path':True,'actual_data_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['layout','typed-rows','semantics'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
