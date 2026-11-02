"""Pinned public metadata parity only; no legal clearance or raw-data test."""
import argparse
import json
from pathlib import Path
from matintegrity import cathodic_protection_data as cp

ROOT=Path(__file__).resolve().parents[1]

def check():
    artifact=json.loads((ROOT/'metadata/cp_iterator_snapshot.json').read_text())
    assert artifact['source_rows']==artifact['package_rows']
    dataset=artifact['source_rows']['datasets'][cp.DATASET_ID]
    assert dataset['checked_on']=='2026-10-31' and dataset['license']==cp.LICENSE_ID=='CC-BY-4.0'
    assert dataset['rights_evidence_url']=='https://zenodo.org/api/records/18735817'
    assert dataset['rights_status']=='reviewed_license' and dataset['acquisition_policy']=='allowed_selected_assets'
    assets={item['filename']:item for item in dataset['assets']}
    assert set(cp.SOURCE_FILES)<=set(assets) and artifact['source_pins']==cp.SOURCE_FILES
    for name in cp.SOURCE_FILES:
        assert assets[name]['url'].startswith('https://zenodo.org/api/records/18735817/files/')
        assert assets[name]['checksum'].startswith('md5:') and len(assets[name]['checksum'])==36
    assert cp.specifications()[0].source_ids[0] in artifact['source_rows']['sources']
    return {'review_date_license_evidence_asset_allowlist_and_package_parity':True,'provider_MD5_not_confused_with_reader_SHA256':True,'raw_assets_read':False,'independent_legal_clearance':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['rights'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check()
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
