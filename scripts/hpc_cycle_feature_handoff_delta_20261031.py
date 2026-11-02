"""Focused ordered receipt replay and integer-block feature binding checks."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity.adaptive_cycle_block_damage import AdaptiveCycleBlockDamageRequest
from matintegrity.contracts import AssessmentResult, RunContext, canonical_digest
from matintegrity.multiaxial_cycle_block_feature_handoff import CycleBlockFeatureHandoffRequest, CycleBlockFeatureBinding, TensorCycleBlockFeatureInput, FiniteCyclePlane, bind_cycle_features_to_adaptive_request, cycle_block_feature_handoff, specifications
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    def evidence(name,digit): return {"source_id":name,"origin":"synthetic","citation":"Fabricated tensor handoff verification input only.","sha256":digit*64,"license_id":"CC0-1.0"}
    blocks=[]
    for index in range(2):
        factor=float(index+1)
        cycle={"cycle_id":"cycle-"+str(index),"allocated_cycle_count":1.0,"sample_ids":["start","peak","close"],
            "stress_tensor_components_Pa":[[0.0]*6,[factor*100e6,0.0,0.0,0.0,0.0,0.0],[0.0]*6],
            "strain_tensor_components":[[0.0]*6,[factor*0.001,0.0,0.0,factor*0.002,0.0,0.0],[0.0]*6]}
        blocks.append({"block_id":"block-"+str(index),"cycle_population_id":"population","loading_state_id":"load-"+str(index),"cycle_count":index+2,"source_record_id":"block-source","source_record_sha256":"3"*64,"cycle":cycle,"evidence":[evidence("block-source","3")]})
    payload={"assessment_id":"synthetic-handoff","physical_scope_id":"scope","material_condition_id":"material","location_id":"location","cycle_count_basis_id":"basis",
        "history_provider_id":"history","history_provider_revision":"1","history_provider_configuration_sha256":"4"*64,"history_provider_record_sha256":"0"*64,
        "stress_history_source_id":"stress","stress_history_sha256":"1"*64,"strain_history_source_id":"strain","strain_history_sha256":"2"*64,
        "strain_shear_convention":"engineering","maximum_stress_closure_error_Pa":0.0,"maximum_strain_closure_error":0.0,
        "finite_planes":[{"plane_id":"x-y","normal":[1.0,0.0,0.0],"engineering_shear_direction":[0.0,1.0,0.0]}],"blocks":blocks,
        "parameter_bindings":[{"plane_id":"x-y","feature_id":"normal_stress_max_Pa","parameter_id":"sigma"},{"plane_id":"x-y","feature_id":"engineering_shear_strain_amplitude","parameter_id":"gamma"}],
        "evidence":[evidence("history","0"),evidence("stress","1"),evidence("strain","2")]}
    for key in ("tensor_order_units_and_shear_convention_reviewed","closed_cycle_and_representative_repetition_reviewed","finite_plane_selection_and_feature_mapping_reviewed","feature_parameter_semantics_reviewed","source_evidence_and_usage_rights_reviewed","downstream_caller_law_remains_external_reviewed","computational_use_authorized"): payload[key]=True
    source=CycleBlockFeatureHandoffRequest.model_validate_json(json.dumps(payload))
    registry=ModelRegistry()
    registry.register(specifications()[0])
    result=registry.run(specifications()[0].model_id,source,RunContext(asset_id="synthetic",location_id="location",time_basis="integer-cycle"))
    assert result.status=="computed"
    target={"analysis_id":"synthetic-target","physical_scope_id":"scope","material_condition_id":"material","cycle_count_basis_id":"basis","provider_id":"law","provider_revision":"1","provider_configuration_sha256":"5"*64,"calibration_sha256":"6"*64,
        "state_variable_ids":["state"],"state_units":["1"],"initial_state":[0.0],"minimum_state":[0.0],"maximum_state":[1.0],
        "blocks":[{"block_id":b["block_id"],"cycle_population_id":b["cycle_population_id"],"loading_state_id":b["loading_state_id"],"cycle_count":b["cycle_count"],"source_sha256":"7"*64} for b in blocks],
        "initial_step_cycles":1.0,"minimum_step_cycles":0.1,"maximum_step_cycles":1.0,"state_absolute_tolerance":[1e-8],"state_relative_tolerance":1e-8,"damage_absolute_tolerance":1e-8,"damage_relative_tolerance":1e-8,
        "evidence":[evidence("law","6")]}
    for key in ("ordered_integer_blocks_and_cycle_count_basis_reviewed","state_law_and_nonnegative_damage_rate_reviewed","initialization_bounds_and_event_meaning_reviewed","deterministic_repeat_evaluation_reviewed","adaptive_controls_and_local_error_meaning_reviewed","material_calibration_and_usage_rights_reviewed","computational_use_authorized"): target[key]=True
    return source,result,AdaptiveCycleBlockDamageRequest.model_validate_json(json.dumps(target))


def replay():
    source,result,target=fixture()
    replayed=cycle_block_feature_handoff(source)
    assert replayed.status=="computed" and replayed.values==result.values
    assert canonical_digest(result.values["integer_cycle_blocks"])==result.values["integer_cycle_blocks_sha256"]
    bound=bind_cycle_features_to_adaptive_request(target,result)
    assert [b.block_id for b in bound.blocks]==["block-0","block-1"]
    assert [b.cycle_count for b in bound.blocks]==[2,3]
    for index,item in enumerate(bound.blocks,start=1):
        assert [p.parameter_id for p in item.parameters]==["sigma","gamma"]
        assert [p.unit for p in item.parameters]==["Pa","1"]
        assert math.isclose(item.parameters[0].value,index*100e6)
        assert math.isclose(item.parameters[1].value,index*0.001)
        assert item.source_sha256==result.values["block_feature_ledger"][index-1]["derived_block_source_sha256"]
    reversed_payload=source.model_dump(mode="json")
    reversed_payload["blocks"].reverse()
    reverse=cycle_block_feature_handoff(CycleBlockFeatureHandoffRequest.model_validate_json(json.dumps(reversed_payload)))
    assert reverse.values["handoff_receipt_sha256"]!=result.values["handoff_receipt_sha256"]
    return {"ordered_block_ids":["block-0","block-1"],"input_replay_identical":True,"exact_parameter_units_and_values":True,"order_changes_receipt":True,"handoff_receipt_sha256":result.values["handoff_receipt_sha256"]}


def failures():
    source,result,target=fixture()
    rejected=[]
    for name,change in (("receipt-digest",lambda p:p["values"].update(handoff_receipt_sha256="f"*64)),
        ("parameter-payload",lambda p:p["values"]["integer_cycle_blocks"][0]["parameters"][0].update(value=123.0))):
        changed=result.model_dump(mode="json")
        change(changed)
        try: bind_cycle_features_to_adaptive_request(target,AssessmentResult.model_validate_json(json.dumps(changed)))
        except ValueError: rejected.append(name)
        else: raise AssertionError("altered receipt accepted: "+name)
    for name in ("order","count","scope"):
        payload=target.model_dump(mode="json")
        if name=="order": payload["blocks"].reverse()
        elif name=="count": payload["blocks"][0]["cycle_count"]+=1
        else: payload["physical_scope_id"]="different-scope"
        try: bind_cycle_features_to_adaptive_request(AdaptiveCycleBlockDamageRequest.model_validate_json(json.dumps(payload)),result)
        except ValueError: rejected.append(name)
        else: raise AssertionError("incorrect target binding accepted: "+name)
    payload=source.model_dump(mode="json")
    payload["parameter_bindings"][1]["parameter_id"]="sigma"
    try: CycleBlockFeatureHandoffRequest.model_validate_json(json.dumps(payload))
    except ValidationError: rejected.append("duplicate-parameter-id")
    else: raise AssertionError("duplicate parameter binding accepted")
    return {"rejected_paths":rejected,"fatigue_law_or_damage_evaluated":False}


def metadata():
    source,_,_=fixture()
    payload=source.model_dump(mode="json")
    payload["computational_use_authorized"]=False
    assert cycle_block_feature_handoff(CycleBlockFeatureHandoffRequest.model_validate_json(json.dumps(payload))).status=="needs_data"
    artifact=json.loads((ROOT/"metadata/cycle_feature_snapshot.json").read_text(encoding="utf-8"))
    for contract in (CycleBlockFeatureHandoffRequest,CycleBlockFeatureBinding,TensorCycleBlockFeatureInput,FiniteCyclePlane): assert artifact["schemas"][contract.__name__]==contract.model_json_schema()
    assert artifact["source_catalogs"]==artifact["package_catalogs"] and artifact["parents"]
    return {"runtime_contract_and_selected_metadata_parity":True,"review_gate":True,"full_registry_or_full_pytest":False}


def main():
    tasks={"replay":replay,"failures":failures,"metadata":metadata}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"synthetic feature receipt/binding checks only; no fatigue/damage/life qualification"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
