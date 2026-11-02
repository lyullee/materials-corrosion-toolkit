"""Three incremental OCP partition/rights and spatial central-contract tasks."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from matintegrity.contracts import Evidence,RunContext,canonical_digest
from matintegrity.ti12mo5zr_corrosion_data import Ti12Mo5ZrRawRow,Ti12Mo5ZrWorkbookProvenance
from matintegrity import ti12mo5zr_ocp_window_summary as ocp
from matintegrity import spatial_piecewise_reaction as spatial
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]


def ocp_rows():
    path=next(iter(ocp.OCP_MEMBER_SHA256))
    provenance=Ti12Mo5ZrWorkbookProvenance(member_path=path,member_bytes=728576,member_sha256=ocp.OCP_MEMBER_SHA256[path],row_count_including_header=10201,column_count=3,source_kind="ocp_monitor")
    return tuple(Ti12Mo5ZrRawRow(provenance=provenance,source_row_number=i+2,raw_headers=ocp.OCP_HEADERS,raw_cells=(float(i),i*0.5,-0.4+2e-5*(i*0.5))) for i in range(10200))


def ocp_request(rows,start=10.25,end=20.75,review=True):
    return ocp.Ti12Mo5ZrOCPWindowRequest(rows=rows,window_start_s=start,window_end_s=end,potential_reference_label="caller-synthetic-reference",potential_reference_evidence=Evidence(source_id="synthetic-reference",origin="synthetic",citation="Fabricated signed potential/time software check; no electrode qualification.",sha256="a"*64),linear_interpolation_reviewed=review,computational_use_authorized=True,local_only_authorized=True)


def ocp_partition():
    rows=ocp_rows()
    full=ocp.summarize_ti12mo5zr_ocp_window(ocp_request(rows))
    left=ocp.summarize_ti12mo5zr_ocp_window(ocp_request(rows,end=15.0))
    right=ocp.summarize_ti12mo5zr_ocp_window(ocp_request(rows,start=15.0))
    assert full.status==left.status==right.status=="computed"
    reference=lambda t:-0.4+2e-5*t
    expected=(reference(10.25)+reference(20.75))*0.5*(20.75-10.25)
    actual=full.values["signed_potential_time_integral_V_s"]
    assert math.isclose(actual,expected,rel_tol=1e-13,abs_tol=1e-13)
    assert math.isclose(actual,left.values["signed_potential_time_integral_V_s"]+right.values["signed_potential_time_integral_V_s"],rel_tol=1e-13,abs_tol=1e-13)
    assert actual<0 and full.values["minimum_potential_V"]<0
    assert math.isclose(full.values["potential_start_V"],reference(10.25),abs_tol=1e-14)
    assert math.isclose(full.values["potential_end_V"],reference(20.75),abs_tol=1e-14)
    assert full.values["potential_reference_label"]=="caller-synthetic-reference"
    return {"fractional_boundary_linear_reference":True,"exact_knot_partition_additivity":True,"signed_potential_preserved":True,"source_rows_fabricated":True,"archive_verified":False}


def ocp_contracts():
    rows=ocp_rows()
    assert ocp.summarize_ti12mo5zr_ocp_window(ocp_request(rows,review=False)).status=="needs_data"
    assert ocp.summarize_ti12mo5zr_ocp_window(ocp_request(rows,end=5100.0)).status=="out_of_scope"
    for factory in (lambda:ocp_request(rows[:-1]),lambda:ocp_request(rows,start=15.0,end=15.0)):
        try: factory()
        except ValidationError: pass
        else: raise AssertionError("partial sequence/nonpositive window accepted")
    changed=list(rows)
    values=rows[1].model_dump(mode="json")
    values["raw_cells"][1]=0.0
    changed[1]=Ti12Mo5ZrRawRow.model_validate_json(json.dumps(values))
    assert ocp.summarize_ti12mo5zr_ocp_window(ocp_request(tuple(changed))).status=="out_of_scope"
    return {"interpolation_review_gate":True,"no_extrapolation":True,"complete_sequence_and_order":True,"source_row_data_fabricated":True}


def spatial_central():
    artifact=json.loads((ROOT/"metadata/ocp_spatial_central_snapshot.json").read_text(encoding="utf-8"))
    assert artifact["source_rows"]==artifact["package_rows"]
    for contract in (ocp.Ti12Mo5ZrOCPWindowRequest,spatial.SpatialPiecewiseMassAction,spatial.SpatialReactionInterval,spatial.SpatialMassActionReaction):
        assert artifact["schemas"][contract.__name__]==contract.model_json_schema()
    values={"provider_id":"synthetic","provider_revision":"1","network_id":"synthetic-A-B","species_ids":["A","B"],"charge_numbers":[1,1],"elemental_composition":{"A":{"X":1},"B":{"X":1}},
        "intervals":[{"start_time_s":0.0,"end_time_s":10.0},{"start_time_s":10.0,"end_time_s":20.0}],
        "reactions":[{"reaction_id":"A-B","reactants":{"A":1},"products":{"B":1},"forward_rate_constants":[2.0,4.0],"reverse_rate_constants":[0.0,0.0],"forward_rate_constant_unit":"1/s","reverse_rate_constant_unit":"1/s","calibration_record_id":"rate","calibration_sha256":"b"*64,"calibration_evidence":[{"source_id":"rate","origin":"synthetic","citation":"Fabricated interval coefficients.","sha256":"b"*64}]}],
        "concentration_activity_approximation_reviewed":True,"usage_license_id":"CC0-1.0","usage_rights_evidence":[{"source_id":"rights","origin":"synthetic","citation":"Synthetic test inputs only.","license_id":"CC0-1.0"}],"computational_use_authorized":True,"local_only_authorized":True}
    request=spatial.SpatialPiecewiseMassAction.model_validate_json(json.dumps(values))
    registry=ModelRegistry()
    registry.register(spatial.specifications()[0])
    registry.register(ocp.specifications()[0])
    context=RunContext(asset_id="synthetic",location_id="synthetic",time_basis="elapsed_seconds")
    receipt=registry.run(spatial.INTERFACE_ID,request,context)
    assert receipt.status=="computed" and receipt.values["configuration_sha256"]==canonical_digest(request.model_dump(mode="json"))
    assert receipt.values["interval_support_s"]==[0.0,20.0] and receipt.values["interval_count"]==2
    callback=spatial.build_spatial_reaction_callback(request)
    np.testing.assert_array_equal(callback(10.0,np.array([[1.0],[0.0]])),np.array([[-4.0],[4.0]]))
    assert callback.configuration_sha256==receipt.values["configuration_sha256"]
    for identifier in (spatial.INTERFACE_ID,ocp.INTERFACE_ID):
        assert artifact["source_rows"]["capabilities"][identifier]["input_schema"]==registry.describe(identifier)["input_schema"]
    return {"new_ModelSpec_runtime_and_callback_receipt_match":True,"exact_partition_boundary_after_registry_validation":True,"source_selected_package_schema_parity":True,"full_suite_replayed":False}


def main():
    tasks={"ocp-partition":ocp_partition,"ocp-contracts":ocp_contracts,"spatial-central":spatial_central}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"synthetic descriptor/integration contract checks, not physical validation"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
