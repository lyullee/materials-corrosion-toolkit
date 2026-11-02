"""Synthetic complete-spectrum conversion tests; no raw archive is read."""
from __future__ import annotations
import argparse
import cmath
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import ti12mo5zr_eis_complex as adapter
from matintegrity.ti12mo5zr_corrosion_data import Ti12Mo5ZrRawRow, Ti12Mo5ZrWorkbookProvenance

ROOT=Path(__file__).resolve().parents[1]


def request(sign=1):
    member=next(iter(adapter.EIS_MEMBER_SHA256))
    provenance=Ti12Mo5ZrWorkbookProvenance(member_path=member,member_bytes=33280,member_sha256=adapter.EIS_MEMBER_SHA256[member],row_count_including_header=75,column_count=5,source_kind="eis_spectrum")
    phases=(0.0,90.0,-90.0,180.0,-180.0,45.0,-45.0,360.0,1e308,-1e308)
    rows=tuple(Ti12Mo5ZrRawRow(provenance=provenance,source_row_number=i+2,raw_headers=adapter.EIS_HEADERS,
        raw_cells=(i+1,(500.0,1000.0,50.0)[i%3],float(i%4),(1.0,2.0,10.0)[i%3],phases[i%len(phases)])) for i in range(74))
    return adapter.Ti12Mo5ZrComplexEISRequest(rows=rows,phase_sign=sign,phase_convention="reported_phase_positive_imaginary" if sign==1 else "reported_phase_negative_imaginary",
        phase_convention_evidence={"source_id":adapter.PHASE_CONVENTION_SOURCE_ID,"origin":"synthetic","citation":"Fabricated phase-sign choices; no instrument sign qualification."},
        phase_convention_reviewed=True,computational_use_authorized=True,local_only_authorized=True)


def components():
    positive=adapter.evaluate_ti12mo5zr_complex_eis(request(1))
    negative=adapter.evaluate_ti12mo5zr_complex_eis(request(-1))
    assert positive.status==negative.status=="computed"
    with localcontext() as context:
        context.prec=450
        for source,p,n in zip(request(1).rows,positive.values["points"],negative.values["points"],strict=True):
            phase=Decimal.from_float(float(source.raw_cells[4])).remainder_near(Decimal(360))
            reference=cmath.rect(float(source.raw_cells[3]),float(phase)*math.pi/180.0)
            assert math.isclose(p["impedance_real_ohm"],reference.real,rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(p["impedance_imaginary_ohm"],reference.imag,rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(math.hypot(p["impedance_real_ohm"],p["impedance_imaginary_ohm"]),p["magnitude_ohm"],rel_tol=1e-12)
            assert p["impedance_real_ohm"]==n["impedance_real_ohm"]
            assert p["impedance_imaginary_ohm"]==-n["impedance_imaginary_ohm"]
            assert p["provider_frequency_Hz"]==source.raw_cells[1] and p["provider_time_s"]==source.raw_cells[2]
    assert positive.values["equivalent_circuit_fit_performed"] is False and positive.values["provider_order_preserved"] is True
    return {"points":74,"independent_reference":"450-digit Decimal phase remainder then complex polar conversion","both_phase_signs":True,
        "very_large_finite_phase_supported":True,"scrambled_frequency_and_scan_time_preserved":True,"synthetic_provider_shaped_rows_only":True,"archive_verified":False}


def reject(payload):
    try: adapter.Ti12Mo5ZrComplexEISRequest.model_validate_json(json.dumps(payload))
    except ValidationError: return
    raise AssertionError("malformed spectrum accepted")


def lineage():
    original=request().model_dump(mode="json")
    for length in (73,75):
        changed=json.loads(json.dumps(original)); changed["rows"]=changed["rows"][:length] if length==73 else changed["rows"]+[changed["rows"][-1]]; reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"].reverse(); reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"][0]["provenance"]["member_path"]="unsupported/path.xls"; reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"][0]["provenance"]["member_sha256"]="a"*64; reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"][5]["provenance"]["member_bytes"]=33279; reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"][0]["provenance"]["archive_sha256"]="a"*64; reject(changed)
    changed=json.loads(json.dumps(original)); changed["rows"][0]["raw_headers"].reverse(); reject(changed)
    result=adapter.evaluate_ti12mo5zr_complex_eis(request())
    assert [row["source_row_number"] for row in result.values["points"]]==list(range(2,76))
    return {"complete_cardinality_required":True,"row_order_headers_and_common_member_required":True,"member_archive_digest_rejections":True,"real_archive_checked":False}


def gates():
    original=request().model_dump(mode="json")
    for extra in ("sort_by_frequency","equivalent_circuit_fit","local_archive_path"):
        changed=json.loads(json.dumps(original)); changed[extra]=True; reject(changed)
    changed=json.loads(json.dumps(original)); changed["phase_sign"]=0; reject(changed)
    changed=json.loads(json.dumps(original)); changed["phase_convention"]="reported_phase_negative_imaginary"; reject(changed)
    changed=json.loads(json.dumps(original)); changed["phase_convention_evidence"]["source_id"]="wrong"; reject(changed)
    changed=json.loads(json.dumps(original)); changed["phase_convention_evidence"]["origin"]="open_dataset"; reject(changed)
    changed=json.loads(json.dumps(original)); changed["phase_convention_reviewed"]=False
    assert adapter.evaluate_ti12mo5zr_complex_eis(adapter.Ti12Mo5ZrComplexEISRequest.model_validate_json(json.dumps(changed))).status=="needs_data"
    for index,value in ((1,0.0),(2,-1.0),(3,-1.0),(4,None)):
        changed=json.loads(json.dumps(original)); changed["rows"][3]["raw_cells"][index]=value
        result=adapter.evaluate_ti12mo5zr_complex_eis(adapter.Ti12Mo5ZrComplexEISRequest.model_validate_json(json.dumps(changed)))
        assert result.status=="out_of_scope" and result.values["completed_point_count"]==3 and result.values["source_row_number"]==5
    spec=adapter.specifications()[0]
    assert spec.units["points[].impedance_imaginary_ohm"]=="ohm"
    artifact=json.loads((ROOT/"metadata/eis_schema_snapshot.json").read_text(encoding="utf-8"))
    for contract in (adapter.Ti12Mo5ZrComplexEISRequest,adapter.Ti12Mo5ZrComplexEISPoint): assert artifact[contract.__name__]==contract.model_json_schema()
    return {"phase_review_evidence_and_label_gates":True,"invalid_numeric_cells_keep_completed_prefix":True,
        "unsupported_sort_fit_and_path_rejected":True,"runtime_contract_snapshot_parity":True,"archive_verified":False}


def main():
    tasks={"components":components,"lineage":lineage,"gates":gates}
    parser=argparse.ArgumentParser(); parser.add_argument("--task",choices=tasks,required=True); parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8"); raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"synthetic adapter/contract checks only; no archive authenticity, instrument convention or physical validation"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
