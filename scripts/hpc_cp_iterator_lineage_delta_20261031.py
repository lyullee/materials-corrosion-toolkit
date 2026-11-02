"""Typed iterator lineage over fabricated parser output, not raw-file validation."""
import argparse
import json
from pathlib import Path
import numpy as np
from matintegrity import cathodic_protection_data as cp
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def authorization(): return cp.CathodicProtectionReadAuthorization(attribution='Fabricated curve-array adapter verification only.',computational_use_authorized=True,local_only_authorized=True)

def parser_fixture(path,*,expected_sha256):
    filename=Path(path).name;assert expected_sha256==cp.SOURCE_FILES[filename]
    file_index=list(cp.SOURCE_FILES).index(filename);count=2 if file_index<3 else 1
    arrays={};records=[]
    for index in range(1,count+1):
        samples=1492 if file_index==4 else 1490;kind='open_circuit_potential' if filename.startswith('OCP') else 'potentiodynamic_scan';label='synthetic-'+str(index)
        x=np.arange(samples,dtype=float);y=-0.5+np.arange(samples,dtype=float)*1e-5
        record=cp.CathodicProtectionCurveRecord(source_filename=filename,source_file_sha256=expected_sha256,curve_index=index,provider_curve_label=label,measurement_kind=kind,sample_count=samples,x_quantity='time' if kind=='open_circuit_potential' else 'current',x_unit='s' if kind=='open_circuit_potential' else 'provider_current_axis_unresolved',minimum_x=float(x[0]),maximum_x=float(x[-1]),minimum_potential_V=float(y[0]),maximum_potential_V=float(y[-1]))
        arrays[f'{Path(filename).stem}:{index}:{label}']=(x,y);records.append(record)
    return arrays,tuple(records)

def rejects(factory):
    try: factory()
    except ValueError: return
    raise AssertionError('invalid parser receipt accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/cp_iterator_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['row_schema']==cp.CathodicProtectionSample.model_json_schema()
    assert artifact['source_pins']==cp.SOURCE_FILES
    cp.read_dplot_curves=parser_fixture
    if task=='lineage':
        auth=authorization();digest=canonical_digest(auth.model_dump(mode='json'));rows=list(cp.iter_cathodic_protection_samples('synthetic-directory',authorization=auth))
        assert len(rows)==11922 and len({(r.source_filename,r.curve_index) for r in rows})==8
        records_by_curve={}
        for filename,pin in cp.SOURCE_FILES.items():
            _,records=parser_fixture(Path(filename),expected_sha256=pin)
            records_by_curve.update({(filename,record.curve_index):canonical_digest(record.model_dump(mode='json')) for record in records})
        for row in rows:
            assert row.authorization_sha256==digest and row.attribution==auth.attribution and row.local_only and row.source_file_sha256==cp.SOURCE_FILES[row.source_filename]
            assert row.curve_record_sha256==records_by_curve[(row.source_filename,row.curve_index)]
        changed=auth.model_dump(mode='json');changed['attribution']='Second synthetic caller attribution.';other=cp.CathodicProtectionReadAuthorization.model_validate_json(json.dumps(changed))
        first=next(cp.iter_cathodic_protection_samples('synthetic-directory',authorization=other));assert first.authorization_sha256!=rows[0].authorization_sha256 and first.source_file_sha256==rows[0].source_file_sha256
    else:
        def broken_prefix(path,*,expected_sha256):
            arrays,records=parser_fixture(path,expected_sha256=expected_sha256);return {'wrong:1:synthetic-1':next(iter(arrays.values()))},records
        cp.read_dplot_curves=broken_prefix;rejects(lambda:next(cp.iter_cathodic_protection_samples('synthetic-directory',authorization=authorization())))
        def broken_length(path,*,expected_sha256):
            arrays,records=parser_fixture(path,expected_sha256=expected_sha256);key=next(iter(arrays));x,y=arrays[key];arrays[key]=(x[:-1],y);return arrays,records
        cp.read_dplot_curves=broken_length;rejects(lambda:next(cp.iter_cathodic_protection_samples('synthetic-directory',authorization=authorization())))
        cp.read_dplot_curves=parser_fixture;values=authorization().model_dump(mode='json');values['attribution']=' '
        rejects(lambda:next(cp.iter_cathodic_protection_samples('synthetic-directory',authorization=cp.CathodicProtectionReadAuthorization.model_validate_json(json.dumps(values)))))
    return {'partition':task,'typed_iterator_adapter_exercised':True,'parser_outputs_fabricated':True,'raw_files_or_actual_DPlot_parser_validated':False,'corrosion_protection_acceptance_inferred':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['lineage','fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
