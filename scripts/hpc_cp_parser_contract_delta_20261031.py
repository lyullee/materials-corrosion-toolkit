"""Real DPlot parser on fabricated CSVs; distinct from mocked iterator tests."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import numpy as np
from matintegrity import cathodic_protection_data as cp

ROOT=Path(__file__).resolve().parents[1]

def rows(): return [['DPLOT v1.6'],['data'],['2'],['3'],['0','-0.6'],['1','-0.5'],['2','-0.4'],['trailer'],['synthetic-A'],['separator'],['3'],['-1','-0.7'],['0','-0.6'],['1','-0.5'],['trailer'],['synthetic-B'],['separator']]

def write(folder,name,data):
    path=folder/name
    with path.open('w',encoding='utf-8',newline='') as stream: csv.writer(stream).writerows(data)
    return path,hashlib.sha256(path.read_bytes()).hexdigest()

def rejects(factory):
    try: factory()
    except ValueError: return
    raise AssertionError('invalid DPlot input accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/cp_iterator_snapshot.json').read_text());assert artifact['source_pins']==cp.SOURCE_FILES;assert artifact['source_rows']==artifact['package_rows']
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder)
        if task=='digest-axis':
            for name,kind,unit in [('OCP Synthetic.csv','open_circuit_potential','s'),('Synthetic Polarization.csv','potentiodynamic_scan','provider_current_axis_unresolved')]:
                path,digest=write(folder,name,rows());curves,records=cp.read_dplot_curves(path,expected_sha256=digest)
                assert len(curves)==len(records)==2 and all(r.sample_count==3 and r.source_file_sha256==digest and r.measurement_kind==kind and r.x_unit==unit and r.y_unit=='V_vs_calomel' for r in records)
                np.testing.assert_array_equal(next(iter(curves.values()))[1],[-0.6,-0.5,-0.4])
                assert [r.provider_curve_label for r in records]==['synthetic-A','synthetic-B']
                rejects(lambda:cp.read_dplot_curves(path,expected_sha256='f'*64));rejects(lambda:cp.read_dplot_curves(path))
        else:
            for case in ('header','width','numeric','nonfinite','label','truncate'):
                data=rows()
                if case=='header': data[0]=['unreviewed-format']
                elif case=='width': data[4]=['0','1','2']
                elif case=='numeric': data[4]=['not-numeric','-0.6']
                elif case=='nonfinite': data[4]=['nan','-0.6']
                elif case=='label': data[8]=[' ']
                else: data=data[:12]
                path,digest=write(folder,'OCP Synthetic.csv',data);rejects(lambda:cp.read_dplot_curves(path,expected_sha256=digest))
    return {'partition':task,'actual_parser_on_fabricated_CSVs':True,'provider_current_units_remain_unresolved':True,'raw_provider_assets_accessed':False,'corrosion_or_protection_qualification':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['digest-axis','malformed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
