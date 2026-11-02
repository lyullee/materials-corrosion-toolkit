"""Six focused reader-parity/roundoff checks; no research-model extension."""
from __future__ import annotations
import argparse
from datetime import date, datetime, time
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import urllib.request
from zipfile import ZipFile
from pydantic import ValidationError
from matintegrity import ti12mo5hf_aesec_rows as reader
from matintegrity.models.scale_reaction_demand_balance import PlanarScaleReactionDemandBalance, _advance, planar_scale_reaction_demand_balance

ROOT=Path(__file__).resolve().parents[1]


def metadata():
    artifact=json.loads((ROOT/"metadata/aesec_contract_snapshot.json").read_text(encoding="utf-8"))
    for contract in (reader.Ti12Mo5HfAESECRequest,reader.Ti12Mo5HfAESECProvenance,reader.Ti12Mo5HfAESECRow):
        assert contract.model_json_schema()==artifact["schemas"][contract.__name__]
    assert artifact["source_dataset"]==artifact["package_dataset"]
    assert artifact["source_dataset"]["license"]=="CC0-1.0"
    assert reader.ARCHIVE_SHA256=="0d50714744e0c6b1b2359beedde96f6b8842ad45ba19c6fcc224b90fd95d6915"
    for member,pin in reader._AESEC.items():
        provenance=reader.Ti12Mo5HfAESECProvenance(member_path=member,member_bytes=pin["bytes"],member_sha256=pin["sha256"],provider_row_count_including_header=pin["rows"])
        cells=(None,True,1,1.5,"=SUM(A1:A2)","literal",0.0)
        row=reader.Ti12Mo5HfAESECRow(provenance=provenance,source_row_number=2,raw_cells=cells)
        assert row.raw_cells==cells and tuple(type(v) for v in row.raw_cells)==tuple(type(v) for v in cells)
    assert not (ROOT/"data/raw").exists()
    return {"schema_count":3,"synthetic_cell_type_preservation":True,"CC0_catalog_parity":True,"source_archive_opened":False,"schema_snapshot_scope":"captured reader-runtime schema exports; not central registry execution"}


def stream():
    from openpyxl import load_workbook
    private=Path(os.environ["MATINTEGRITY_PRIVATE_DATA"])
    private.mkdir(parents=True,exist_ok=True)
    path=private/reader.ARCHIVE_FILENAME
    if not path.exists():
        temporary=private/"bounded-download.part"
        url="https://zenodo.org/api/records/19462164/files/Data_Zenodo_EA2026.zip/content"
        count=0
        with urllib.request.urlopen(url,timeout=60) as response,temporary.open("wb") as output:
            while chunk:=response.read(1024*1024):
                count+=len(chunk)
                if count>reader.ARCHIVE_BYTES: raise ValueError("archive byte budget exceeded")
                output.write(chunk)
        assert count==reader.ARCHIVE_BYTES
        temporary.replace(path)
    raw=path.read_bytes()
    assert len(raw)==reader.ARCHIVE_BYTES and hashlib.sha256(raw).hexdigest()==reader.ARCHIVE_SHA256
    records=[]
    with ZipFile(path) as archive:
        for member,pin in reader._AESEC.items():
            payload=archive.read(member)
            assert len(payload)==pin["bytes"] and hashlib.sha256(payload).hexdigest()==pin["sha256"]
            workbook=load_workbook(BytesIO(payload),read_only=False,data_only=False)
            try:
                sheet=workbook["Sheet1"]
                request=reader.Ti12Mo5HfAESECRequest(local_archive_path=str(path),member_path=member,computational_use_authorized=True,local_only_authorized=True)
                digest=hashlib.sha256()
                count=0
                source=sheet.iter_rows(min_row=2,max_row=sheet.max_row,values_only=True)
                for number,(row,values) in enumerate(zip(reader.iter_local_aesec_rows(request),source,strict=True),start=2):
                    expected=tuple(value.isoformat() if isinstance(value,(datetime,date,time)) else value for value in values)
                    assert row.source_row_number==number and row.raw_cells==expected
                    assert tuple(type(value) for value in row.raw_cells)==tuple(type(value) for value in expected)
                    assert row.provenance.member_sha256==pin["sha256"]
                    digest.update(json.dumps(expected,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode())
                    count+=1
                assert count==pin["rows"]-1
                records.append({"member":member,"rows":count,"ordered_cell_stream_sha256":digest.hexdigest()})
            finally: workbook.close()
    return {"archive_sha256":reader.ARCHIVE_SHA256,"streams":records,"raw_values_exported":False,"reference":"direct normal-mode openpyxl cells compared to reader read-only stream; no corrosion calculation"}


def expect_roundoff(label,length,a,supply,demand,duration,message):
    try: _advance(length,a,supply,demand,duration,160,1e-40,1e-40)
    except ArithmeticError as error: assert message in str(error),str(error)
    else: raise AssertionError("roundoff path silently passed: "+label)
    return {"case":label,"expected_guard":message,"status":"rejected"}


def growth():
    return expect_roundoff("positive-growth-below-spacing",1.0,1.0,1e-300,0.0,1.0,"zero-demand growth lost")


def shrink():
    return expect_roundoff("positive-shrink-below-spacing",1.0,1.0,0.0,1e-300,1.0,"positive demand-only shrinkage lost")


def mixed():
    return expect_roundoff("mixed-change-below-spacing",1.0,1.0,1.0,1.0,1e-30,"non-equilibrium thickness change lost")


def controls():
    for coefficients in ((1e-300,1e-300,0.0,0.0,1.0),(1.0,1.0,1.0,1.0,0.0),(1.0,1.0,2.0,1.0,1.0)):
        result=_advance(*coefficients,160,1e-12,1e-9)
        assert result[0]==coefficients[0] and result[2] is False
    assert math.isclose(_advance(1.0,1.0,0.0,0.25,1.0,160,1e-12,1e-9)[0],0.75)
    return {"zero-rates":True,"zero-duration":True,"true-equilibrium":True,"representable-shrink":True}


def main():
    tasks={"metadata":metadata,"stream":stream,"growth":growth,"shrink":shrink,"mixed":mixed,"controls":controls}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"targeted software/data-preservation checks only; no physical qualification"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
