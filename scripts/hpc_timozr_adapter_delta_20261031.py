"""Low-cost synthetic adapter tests; the raw workbook reader is substituted."""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
import math
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from matintegrity import ti12mo5zr_mass_balance as adapter
from matintegrity.ti12mo5zr_corrosion_data import Ti12Mo5ZrRawRow, Ti12Mo5ZrWorkbookProvenance


def request(**changes):
    values={"local_archive_path":"not-opened/zenodo_APSUC_2024.zip","density_kg_m3":4000.0,
        "density_evidence":{"source_id":"synthetic-density","origin":"synthetic","citation":"Fabricated 4000 kg/m3 software verification density; not material evidence.","sha256":"a"*64,"license_id":"CC0-1.0"},
        "alloy_label":"Ti-12Mo-5Zr","analyzed_elements":["Ti","Mo","Zr"],
        "computational_use_authorized":True,"local_only_authorized":True,
        "source_time_axis_is_valid_for_interval_integration":True,
        "provider_positive_rate_means_outward_loss_reviewed":True,
        "analyzed_element_coverage_is_complete_for_this_conversion":True,
        "uniform_area_and_density_equivalent_penetration_reviewed":True,
        "linear_interpolation_between_time_rows_reviewed":True}
    return adapter.Ti12Mo5ZrMassBalanceRequest.model_validate_json(json.dumps(values|changes))


def rows(times=None,count=6121,missing=False):
    provenance=Ti12Mo5ZrWorkbookProvenance(member_path=adapter.AESEC_MEMBER,member_bytes=582144,
        member_sha256="52aef79a7284b88296f00ade100756efbdd60893028fe302a1e29fee4c9ae024",
        row_count_including_header=6122,column_count=4,source_kind="aesec_elemental_dissolution_rate")
    for index in range(count):
        time=float(index) if times is None else times[index]
        values=(time,3.0,None if missing else -1.0,2.0)
        yield Ti12Mo5ZrRawRow(provenance=provenance,source_row_number=index+2,raw_headers=adapter.SOURCE_HEADERS,raw_cells=values)


def units():
    expected_factor=float(Decimal("1e-12")/Decimal("1e-4"))
    assert adapter.NG_S_CM2_TO_KG_M2_S==expected_factor==1e-8
    with patch.object(adapter,"iter_local_rows",return_value=rows()):
        result=adapter.calculate_mass_balance(request())
    assert result.input_row_count==6121
    for point in (result.points[0],result.points[-1]):
        assert point.elemental_mass_flux_kg_m2_s["Mo"]==-1e-8
        assert math.isclose(point.signed_net_mass_flux_kg_m2_s,4e-8,rel_tol=1e-14)
        assert math.isclose(point.signed_equivalent_penetration_velocity_m_s,1e-11,rel_tol=1e-14)
    assert math.isclose(result.signed_net_integrated_penetration_m,6120e-11,rel_tol=1e-10)
    assert result.negative_cumulative_penetration_m==0.0
    return {"ng_per_s_cm2_to_kg_per_m2_s":expected_factor,"negative_Mo_channel_preserved":True,
        "constant_velocity_m_s":1e-11,"integrated_seconds":6120,"reader_substituted_with_fabricated_rows":True,"real_archive_verified":False}


def signed():
    cases=[]
    for v0,v1,dt,positive,negative in ((2.0,4.0,3.0,9.0,0.0),(-2.0,-4.0,3.0,0.0,-9.0),
        (2.0,-2.0,4.0,2.0,-2.0),(-2.0,2.0,4.0,2.0,-2.0),(0.0,2.0,3.0,3.0,0.0)):
        actual=adapter._positive_negative_interval(v0,v1,dt)
        assert math.isclose(actual[0],positive,abs_tol=1e-14) and math.isclose(actual[1],negative,abs_tol=1e-14)
        exact_signed=float((Decimal(str(v0))+Decimal(str(v1)))*Decimal(str(dt))/2)
        assert math.isclose(math.fsum(actual),exact_signed,abs_tol=1e-14)
        cases.append({"v0":v0,"v1":v1,"positive_integral":positive,"negative_integral":negative})
    return {"independent_triangle_trapezoid_cases":cases,"signed_zero_crossings_retained":True}


def gates():
    for field in ("computational_use_authorized","local_only_authorized","source_time_axis_is_valid_for_interval_integration",
                  "provider_positive_rate_means_outward_loss_reviewed","analyzed_element_coverage_is_complete_for_this_conversion",
                  "uniform_area_and_density_equivalent_penetration_reviewed","linear_interpolation_between_time_rows_reviewed"):
        try: request(**{field:False})
        except ValidationError: pass
        else: raise AssertionError("false review accepted: "+field)
    for changes in ({"density_evidence":None},{"density_kg_m3":0.0}):
        try: request(**changes)
        except ValidationError: pass
        else: raise AssertionError("missing density evidence/nonpositive density accepted")
    with patch.object(adapter,"iter_local_rows",side_effect=AssertionError("reader must not be called")):
        try: adapter.calculate_mass_balance(request(analyzed_elements=["Ti","Mo"]))
        except ValueError: pass
        else: raise AssertionError("incomplete element coverage accepted")
    for source,label in ((rows(times=[0.0,0.0],count=2),"nonincreasing-time"),(rows(count=2,missing=True),"missing-cell"),(rows(count=2),"incomplete-row-count")):
        with patch.object(adapter,"iter_local_rows",return_value=source):
            try: adapter.calculate_mass_balance(request())
            except (ValueError,ValidationError): pass
            else: raise AssertionError("malformed row source accepted: "+label)
    return {"review_attestations_fail_closed":True,"density_evidence_required":True,"coverage_time_missing_and_count_rejections":True,
            "reader_substituted":True,"archive_opened_or_acquired":False}


def main():
    tasks={"units":units,"signed":signed,"gates":gates}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"synthetic adapter arithmetic/gates only; no archive, dataset or physical validation"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
