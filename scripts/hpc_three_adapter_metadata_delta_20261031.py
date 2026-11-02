"""Independent synthetic contrast and strict contract/central metadata checks."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import wet_co2_matched_contrast as wet
from matintegrity import multiaxial_cycle_block_result_summary as cycle
from matintegrity.models import external_flange_diagnostic_screen as flange
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]
MODULES={"wet":wet,"flange":flange,"cycle":cycle}

def check(task):
    module=MODULES[task]
    spec=module.specifications()[0]
    artifact=json.loads((ROOT/"metadata/three_adapter_snapshot.json").read_text())
    registry=ModelRegistry()
    registry.register(spec)
    assert artifact["schemas"][spec.model_id]==registry.describe(spec.model_id)["input_schema"]
    for name in ("capabilities","sources"):
        assert artifact["source_rows"][name]==artifact["package_rows"][name]
    assert artifact["source_rows"]["capabilities"][spec.model_id]["input_schema"]==spec.input_type.model_json_schema()
    try: spec.input_type.model_validate_json('{}')
    except ValidationError: pass
    else: raise AssertionError('empty contract accepted')
    details={"runtime_schema_catalog_source_package_parity":True,"empty_request_rejected":True,"physical_validation":False}
    if task=="wet":
        row={"provider_row":2,"source_archive_sha256":"a"*64,"temperature_K":300.0,"flow_velocity_m_s":1.0,"co2_pressure_Pa":100000.0,"internal_pressure_Pa":200000.0,"corrosion_inhibitor_efficiency_fraction":0.0,"shear_stress_Pa":1.0,"ph":5.0,"corrosion_rate_m_s":1e-9,"evidence":[{"source_id":"norsok-m506-simulation-grid","origin":"open_dataset","citation":"Synthetic provenance-shaped descriptor; no archive was read.","license_id":"CC-BY-4.0","sha256":"a"*64}]}
        high=dict(row,provider_row=3,temperature_K=600.0,corrosion_rate_m_s=4e-9)
        payload={"lower_factor_row":row,"upper_factor_row":high,"varied_factor":"temperature_K","provider_pairing_and_ceteris_paribus_reviewed":True,"simulation_output_scope_reviewed":True}
        request=spec.input_type.model_validate_json(json.dumps(payload))
        result=wet.wet_co2_matched_contrast(request)
        assert result.status=="computed"
        assert math.isclose(result.values["finite_difference_m_s_per_factor_unit"],1e-11,rel_tol=1e-14)
        assert math.isclose(result.values["log_log_secant_elasticity"],2.0,rel_tol=1e-13)
        assert not result.values["causal_effect_inferred"]
        payload["simulation_output_scope_reviewed"]=False
        assert wet.wet_co2_matched_contrast(spec.input_type.model_validate_json(json.dumps(payload))).status=="needs_data"
        payload["upper_factor_row"]["ph"]=6.0
        try: spec.input_type.model_validate_json(json.dumps(payload))
        except ValidationError: pass
        else: raise AssertionError('unmatched nonvaried input accepted')
        details.update(synthetic_finite_difference_and_elasticity=True,review_and_exact_pair_gates=True,archive_read=False)
    if task=="flange":
        value={"criterion_id":"synthetic","diagnostic_id":"residual","category":"equilibrium","metric_id":"residual","metric_definition":"Synthetic normalized residual only.","unit_token":"1","maximum_absolute_value_plus_uncertainty":0.1,"compatible_uncertainty_reviewed":True,"evidence":[{"source_id":"synthetic","origin":"synthetic","citation":"Fabricated caller threshold."}]}
        criterion=flange.FlangeDiagnosticCriterion.model_validate_json(json.dumps(value))
        assert criterion.maximum_absolute_value_plus_uncertainty==0.1
        for field,bad in (("maximum_absolute_value_plus_uncertainty",-1.0),("category","physical_acceptance"),("evidence",[])):
            changed=dict(value,**{field:bad})
            try: flange.FlangeDiagnosticCriterion.model_validate_json(json.dumps(changed))
            except ValidationError: pass
            else: raise AssertionError('invalid criterion accepted: '+field)
        details.update(caller_criterion_bounds_category_evidence_rejected=True,solver_receipt_numerical_screen_exercised=False)
    if task=="cycle":
        for bad in ('{}','{"stateful_result_sha256":"bad"}','{"receipt":{},"bound_request":{},"stateful_result":{},"stateful_result_sha256":"'+'a'*64+'"}'):
            try: spec.input_type.model_validate_json(bad)
            except ValidationError: pass
            else: raise AssertionError('incomplete lineage accepted')
        details.update(incomplete_receipt_request_result_lineage_rejected=True,complete_ledger_numerics_exercised=False)
    return details

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--task',choices=MODULES,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({"status":"failed","error":str(error)},indent=2))
        raise
    args.output.write_text(json.dumps({"status":"passed","details":details},indent=2))
