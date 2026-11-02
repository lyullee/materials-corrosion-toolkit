"""Small synthetic ZIP integrity/streaming checks; never scan the real archive."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile
from pydantic import ValidationError
from matintegrity import metropt3_data as metro

ROOT=Path(__file__).resolve().parents[1]

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported input accepted')

def authorization(): return metro.MetroPT3ArchiveAuthorization(attribution='Synthetic test input; UCI attribution semantics only.',computational_use_authorized=True,local_only_authorized=True)

def fixture(folder,mutate=None):
    rows=[list(metro.HEADERS),['0','2020-01-01 00:00:00',*['1.25']*15],['1','2020-01-01 00:00:01',*['-0.25']*15]]
    if mutate: mutate(rows)
    stream=io.StringIO(newline='');csv.writer(stream).writerows(rows);content=stream.getvalue().encode()
    path=folder/metro.ARCHIVE_NAME
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(metro.MEMBER_NAME,content)
        archive.writestr(getattr(metro,'README_MEMBER_NAME','readme.txt'),'Synthetic fixture, no actual provider observations.')
    metro.ARCHIVE_BYTES=path.stat().st_size;metro.ARCHIVE_SHA256=hashlib.sha256(path.read_bytes()).hexdigest();metro.MEMBER_BYTES=len(content);metro.MEMBER_SHA256=hashlib.sha256(content).hexdigest();metro.EXPECTED_DATA_ROWS=2
    return path

def check(task):
    artifact=json.loads((ROOT/'metadata/metropt3_snapshot.json').read_text())
    assert artifact['source_rows']==artifact['package_rows']
    for cls in (metro.MetroPT3ArchiveAuthorization,metro.MetroPT3ArchiveAuditRequest,metro.MetroPT3Row): assert artifact['schemas'][cls.__name__]==cls.model_json_schema()
    for key,value in artifact['pins'].items(): assert getattr(metro,key)==value
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder);path=fixture(folder)
        if task=='archive':
            metro._verify_archive(path)
            original=metro.ARCHIVE_SHA256;metro.ARCHIVE_SHA256='f'*64;rejects(lambda:metro._verify_archive(path));metro.ARCHIVE_SHA256=original
            original=metro.MEMBER_SHA256;metro.MEMBER_SHA256='f'*64;rejects(lambda:metro._verify_archive(path));metro.MEMBER_SHA256=original
            original=metro.MEMBER_BYTES;metro.MEMBER_BYTES+=1;rejects(lambda:metro._verify_archive(path));metro.MEMBER_BYTES=original
            wrong=folder/'unreviewed.zip';wrong.write_bytes(path.read_bytes());rejects(lambda:metro._verify_archive(wrong))
            return {'synthetic_zip_digest_member_size_name_gates':True,'actual_218MB_archive_scanned':False,'real_pins_preserved_in_snapshot':True}
        if task=='stream':
            iterator=metro.iter_metropt3_rows(path,authorization=authorization());first=next(iterator)
            assert first.provider_row_number==2 and first.provider_index==0 and first.raw_signal_cells['TP2']=='1.25' and first.signal_values_provider_native['TP2']==1.25
            second=next(iterator);assert second.provider_row_number==3 and second.provider_index==1 and second.signal_values_provider_native['TP2']==-0.25
            assert list(iterator)==[] and first.units_status=='provider_native_unresolved'
            for mutate in (lambda r:r[0].__setitem__(2,'changed-header'),lambda r:r[2].__setitem__(0,'0'),lambda r:r[1].__setitem__(2,'nan'),lambda r:r[1].__setitem__(1,'')):
                changed=fixture(folder,mutate);rejects(lambda:list(metro.iter_metropt3_rows(changed,authorization=authorization())))
            return {'synthetic_stream_header_index_raw_numeric_lineage':True,'bad_header_order_nonfinite_timestamp_gates':True,'whole_provider_archive_parsed':False}
        request=metro.MetroPT3ArchiveAuditRequest(local_archive_path=str(path),authorization=authorization())
        result=metro.audit_metropt3_archive(request)
        assert result.values['license_id']=='CC-BY-4.0' and not result.values['raw_data_returned'] and not result.values['local_path_returned'] and not result.values['archive_extracted']
        assert 'not corrosion' in result.values['interpretation_limit'] and str(path) not in json.dumps(result.values)
        for change in ({'computational_use_authorized':False},{'local_only_authorized':False},{'license_id':'CC0-1.0'}):
            values=authorization().model_dump(mode='json');values.update(change);rejects(lambda:metro.MetroPT3ArchiveAuthorization.model_validate_json(json.dumps(values)))
        blank=authorization().model_dump(mode='json');blank['attribution']=' '
        bad=metro.MetroPT3ArchiveAuditRequest(local_archive_path=str(path),authorization=metro.MetroPT3ArchiveAuthorization.model_validate_json(json.dumps(blank)))
        rejects(lambda:metro.audit_metropt3_archive(bad))
        return {'metadata_only_no_path_no_corrosion_inference':True,'CC_BY_attribution_computational_local_gates':True,'actual_dataset_numerical_validation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['archive','stream','semantics'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
