"""Post-snapshot strict-integer and callback-readiness regression partitions."""
import argparse
import json
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from matintegrity import spatial_piecewise_reaction as spatial
from matintegrity.contracts import RunContext
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    evidence={"source_id":"rate","origin":"synthetic","citation":"Fabricated strict-contract regression coefficients.","sha256":"b"*64,"license_id":"CC0-1.0"}
    return {"provider_id":"synthetic","provider_revision":"1","network_id":"A-B","species_ids":["A","B"],"charge_numbers":[1,1],"elemental_composition":{"A":{"X":1},"B":{"X":1}},"intervals":[{"start_time_s":0.0,"end_time_s":10.0},{"start_time_s":10.0,"end_time_s":20.0}],"reactions":[{"reaction_id":"A-B","reactants":{"A":1},"products":{"B":1},"forward_rate_constants":[2.0,4.0],"reverse_rate_constants":[0.0,0.0],"forward_rate_constant_unit":"1/s","reverse_rate_constant_unit":"1/s","calibration_record_id":"rate","calibration_sha256":"b"*64,"calibration_evidence":[evidence]}],"concentration_activity_approximation_reviewed":True,"usage_license_id":"CC0-1.0","usage_rights_evidence":[evidence],"computational_use_authorized":True,"local_only_authorized":True}

def request(values): return spatial.SpatialPiecewiseMassAction.model_validate_json(json.dumps(values))

def check(task):
    if task=="strict-schema":
        artifact=json.loads((ROOT/"metadata/spatial_strict_snapshot.json").read_text())
        assert artifact["source_rows"]==artifact["package_rows"]
        for cls in (spatial.SpatialPiecewiseMassAction,spatial.SpatialMassActionReaction,spatial.SpatialReactionInterval): assert artifact["schemas"][cls.__name__]==cls.model_json_schema()
        request(payload())
        rejected=0
        for bad in (True,1.0,"1",0,-1):
            for field in ("reactants","products","charge_numbers","elemental_composition"):
                values=payload()
                if field in ("reactants","products"): values["reactions"][0][field]["A" if field=="reactants" else "B"]=bad
                elif field=="charge_numbers":
                    if bad in (0,-1) and not isinstance(bad,bool): continue
                    values[field][0]=bad
                else:
                    if bad==0 and not isinstance(bad,bool): continue
                    values[field]["A"]["X"]=bad
                try: request(values)
                except ValidationError: rejected+=1
                else: raise AssertionError('invalid integer contract accepted: '+field+' '+repr(bad))
        return {"strict_integer_rejections":rejected,"schema_selected_catalog_parity":True}
    values=payload()
    if task=="with-activity": values.update(activity_provider_id="gamma",activity_provider_revision="1",activity_configuration_sha256="c"*64)
    model=request(values)
    registry=ModelRegistry()
    registry.register(spatial.specifications()[0])
    result=registry.run(spatial.INTERFACE_ID,model,RunContext(asset_id="synthetic",location_id="synthetic",time_basis="elapsed_seconds"))
    assert result.status=="computed" and result.values["callback_contract_ready"] is True
    assert result.values["activity_callback_required"]==(task=="with-activity")
    assert "callback_created" not in result.values
    def gamma(time,concentration): return np.full_like(concentration,2.0)
    gamma.provider_id="gamma"
    gamma.provider_revision="1"
    gamma.configuration_sha256="c"*64
    callback=spatial.build_spatial_reaction_callback(model,**({"activity_coefficients":gamma} if task=="with-activity" else {}))
    np.testing.assert_array_equal(callback(10.0,np.array([[1.0],[0.0]])),np.array([[-8.0],[8.0]]) if task=="with-activity" else np.array([[-4.0],[4.0]]))
    try: spatial.build_spatial_reaction_callback(model,**({} if task=="with-activity" else {"activity_coefficients":gamma}))
    except ValueError: pass
    else: raise AssertionError('provider presence mismatch accepted')
    for time in (-0.01,20.01):
        try: callback(time,np.array([[1.0],[0.0]]))
        except ValueError: pass
        else: raise AssertionError('extrapolation accepted')
    if task=="with-activity":
        gamma.configuration_sha256="d"*64
        try: spatial.build_spatial_reaction_callback(model,activity_coefficients=gamma)
        except ValueError: pass
        else: raise AssertionError('activity digest mismatch accepted')
    return {"contract_ready_not_created":True,"activity_required_flag":task=="with-activity","presence_and_extrapolation_fail_closed":True,"exact_boundary_source":True}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--task',choices=['strict-schema','with-activity','without-activity'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({"status":"failed","error":str(error)},indent=2))
        raise
    args.output.write_text(json.dumps({"status":"passed","details":details,"physical_validation":False},indent=2))
