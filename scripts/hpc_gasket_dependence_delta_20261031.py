"""Three focused finite-scenario covariance checks; no full suite or raw data."""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import json
import math
from pathlib import Path
from runpy import run_path
from pydantic import ValidationError
from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.gasket_finite_scenario_dependence import GasketFiniteScenarioDependence, gasket_finite_scenario_dependence, specifications
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    return run_path(str(ROOT/"examples/gasket_finite_scenario_dependence.py"))["request"]


def covariance():
    request=fixture()
    result=gasket_finite_scenario_dependence(request)
    assert result.status=="computed"
    vectors=[]
    with localcontext() as context:
        context.prec=70
        d=lambda value: Decimal(str(value))
        for scenario in request.weighted_scenarios.scenario_envelope.scenarios:
            pressure=d(scenario.node_contact_pressure_Pa[0])
            delta=d(scenario.common_differential_pressure_Pa)
            area=d(scenario.node_area_m2[0])
            flux=(delta/Decimal("2000000"))*(Decimal("1e-8")+(pressure/Decimal("2000000"))*(Decimal("1e-9")-Decimal("1e-8")))
            leakage=area*flux
            vectors.append([delta,area,leakage,pressure,area,leakage])
        weights=[d(weight) for weight in request.weighted_scenarios.scenario_weights]
        means=[sum(weight*row[i] for weight,row in zip(weights,vectors,strict=True)) for i in range(6)]
        expected=[[sum(weight*(row[i]-means[i])*(row[j]-means[j]) for weight,row in zip(weights,vectors,strict=True)) for j in range(6)] for i in range(6)]
        for i in range(6):
            assert math.isclose(result.values["weighted_means"][i],float(means[i]),rel_tol=1e-11,abs_tol=1e-25)
            for j in range(6):
                target=float(expected[i][j])
                assert math.isclose(result.values["weighted_centered_second_moment_matrix"][i][j],target,rel_tol=1e-10,abs_tol=1e-28),(i,j)
    assert result.values["weighted_correlation_matrix"][1][4]==1.0
    assert result.values["weighted_correlation_matrix"][2][5]==1.0
    return {"independent_reference":"70-digit Decimal weighted means/covariance with independently evaluated bilinear leakage","matrix_dimension":6,"exact_duplicate_column_correlations":True,"probability_inferred":False}


def exact_cases():
    payload=fixture().model_dump(mode="json")
    envelope=payload["weighted_scenarios"]["scenario_envelope"]
    for scenario,pressure,delta in zip(envelope["scenarios"],(0.0,1e6,2e6),(2e6,1e6,0.0),strict=True):
        scenario["node_contact_pressure_Pa"]=[pressure]
        scenario["common_differential_pressure_Pa"]=delta
        scenario["node_area_m2"]=[0.01]
    digest=canonical_digest(envelope["scenarios"])
    envelope["scenario_set_sha256"]=digest
    for evidence in envelope["evidence"]:
        if evidence["source_id"]==envelope["scenario_provider_id"]: evidence["sha256"]=digest
    result=gasket_finite_scenario_dependence(GasketFiniteScenarioDependence.model_validate_json(json.dumps(payload)))
    assert result.status=="computed"
    matrix=result.values["weighted_correlation_matrix"]
    assert matrix[0][3]==-1.0 and matrix[0][0]==1.0
    assert all(value is None for value in matrix[1]) and all(value is None for value in matrix[4])
    assert "total_contact_area" in result.values["undefined_correlation_variable_ids"]
    assert result.values["weighted_centered_second_moment_matrix"][1][1]==0.0
    return {"exact_negative_correlation":True,"exact_self_correlation":True,"constant_columns_have_null_correlation":True}


def metadata_gates():
    request=fixture()
    artifact=json.loads((ROOT/"metadata/gasket_dependence_snapshot.json").read_text(encoding="utf-8"))
    assert artifact["schema"]==GasketFiniteScenarioDependence.model_json_schema()
    assert artifact["source_catalogs"]==artifact["package_catalogs"] and artifact["parents"]
    specs=specifications()
    registry=ModelRegistry()
    registry.register(specs[0])
    payload=request.model_dump(mode="json")
    payload["finite_set_dependence_and_variable_units_reviewed"]=False
    gated=GasketFiniteScenarioDependence.model_validate_json(json.dumps(payload))
    context=RunContext(asset_id="synthetic-asset",location_id="synthetic",time_basis="elapsed_seconds")
    assert registry.run(specs[0].model_id,gated,context).status=="needs_data"
    for change in ({"maximum_scenario_variable_pairs":1},{"selected_node_ids":["missing-node"]}):
        invalid=request.model_dump(mode="json")|change
        try: GasketFiniteScenarioDependence.model_validate_json(json.dumps(invalid))
        except ValidationError: pass
        else: raise AssertionError("invalid selection or budget accepted")
    invalid=request.model_dump(mode="json")
    invalid["weighted_scenarios"]["scenario_weights"]=[0.2,0.2,0.2]
    try: GasketFiniteScenarioDependence.model_validate_json(json.dumps(invalid))
    except ValidationError: pass
    else: raise AssertionError("non-normalized weights accepted")
    upstream=request.model_dump(mode="json")
    upstream["weighted_scenarios"]["scenario_envelope"]["computational_use_authorized"]=False
    assert gasket_finite_scenario_dependence(GasketFiniteScenarioDependence.model_validate_json(json.dumps(upstream))).status=="needs_data"
    assert not (ROOT/"data/raw").exists()
    return {"schema_ModelSpec_source_parent_package_parity":True,"own_and_upstream_reviews":True,"selection_budget_weight_rejections":True,"catalog_scope":"selected entries and captured full-file hashes; not full suite"}


def main():
    tasks={"covariance":covariance,"exact":exact_cases,"metadata":metadata_gates}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"finite synthetic scenario/software checks only; no population/causal/physical qualification"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
