"""Four focused phase-proposal/wall-shear checks on a minimal immutable closure."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity.aqueous_solid_phase_candidates import AqueousSolidPhaseCandidateEnumeration, enumerate_aqueous_solid_phase_candidates
from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.crevice_wall_shear_exposure import CreviceWallShearExposure, crevice_wall_shear_exposure, specifications as shear_specs
from matintegrity.models.planar_slit_transient_hydraulic import PlanarSlitTransientHydraulicHistory, specifications as hydraulic_specs
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]


def phase_request(**changes):
    values={"enumeration_id":"synthetic-phase","aqueous_species":[
        {"species_id":"Na+","charge_number":1,"elemental_composition":{"Na":1}},
        {"species_id":"Cl-","charge_number":-1,"elemental_composition":{"Cl":1}}],
        "proposed_solid_phases":[{"species_id":"NaCl-solid","charge_number":0,"elemental_composition":{"Na":1,"Cl":1}}],
        "maximum_total_stoichiometric_order":3,"species_formula_and_charge_reviewed":True,
        "closed_aqueous_and_solid_inventory_reviewed":True,"candidate_use_and_manual_phase_selection_reviewed":True,
        "evidence":[{"source_id":"synthetic","origin":"synthetic","citation":"Integer-balance software fixture, no phase stability evidence."}]}
    return AqueousSolidPhaseCandidateEnumeration.model_validate_json(json.dumps(values|changes))


def phase_balanced():
    result=enumerate_aqueous_solid_phase_candidates(phase_request())
    assert result.status=="computed" and result.values["phase_candidate_count"]==1
    row=result.values["phase_candidates"][0]
    products={item["species_id"]:item["coefficient"] for item in row["aqueous_products"]}
    assert row["solid"]=={"species_id":"NaCl-solid","coefficient":1} and products=={"Cl-":1,"Na+":1}
    assert sum(products[key]*charge for key,charge in (("Na+",1),("Cl-",-1)))==0
    body={key:row[key] for key in ("solid","aqueous_products","balanced_elements","charge_stoichiometric_residual")}
    assert canonical_digest(body)==row["candidate_sha256"]
    assert result.values["phase_stability_assessed"] is False and result.values["equilibrium_constants_assigned"] is False
    return {"balanced_proposals":1,"independent_integer_charge_check":True,"phase_stability_inferred":False}


def parity():
    artifact=json.loads((ROOT/"metadata/phase_shear_snapshot.json").read_text(encoding="utf-8"))
    for contract in (AqueousSolidPhaseCandidateEnumeration,CreviceWallShearExposure,PlanarSlitTransientHydraulicHistory):
        assert contract.model_json_schema()==artifact["schemas"][contract.__name__]
    assert artifact["source_catalogs"]==artifact["package_catalogs"]
    assert all(artifact["parent_ids"].values())
    return artifact


def phase_gates():
    assert enumerate_aqueous_solid_phase_candidates(phase_request(species_formula_and_charge_reviewed=False)).status=="needs_data"
    limited=enumerate_aqueous_solid_phase_candidates(phase_request(maximum_candidate_pair_checks=1))
    assert limited.status=="out_of_scope" and limited.values["phase_candidates"]==[]
    assert limited.values["partial_catalog_returned"] is False
    invalid=phase_request().model_dump(mode="json")
    invalid["proposed_solid_phases"][0]["charge_number"]=1
    try: AqueousSolidPhaseCandidateEnumeration.model_validate_json(json.dumps(invalid))
    except ValidationError: pass
    else: raise AssertionError("charged proposed solid accepted")
    parity()
    return {"review_gate":True,"budget_no_partial_catalog":True,"charged_solid_rejection":True,"metadata_parity":True}


def hydraulic():
    registry=ModelRegistry()
    registry.register(hydraulic_specs()[0])
    registry.register(shear_specs()[0])
    evidence=[{"source_id":name,"origin":"synthetic","citation":"Fabricated hydraulic source.","sha256":digit*64} for name,digit in (("geometry","1"),("pressure","2"),("fluid","3"))]
    values={"assessment_id":"synthetic-flow","asset_id":"synthetic","location_id":"synthetic","physical_scope_id":"synthetic-only","time_basis":"elapsed_seconds",
        "time_s":[0.0,0.005,0.01],"cell_ids":["c0"],"cell_widths_m":[0.01],"aperture_by_interval_m":[[1e-4],[1e-4]],
        "transverse_width_m":0.01,"pressure_drop_by_interval_Pa":[120.0,-30.0],"initial_volumetric_flow_m3_s":0.0,
        "density_kg_m3":1000.0,"dynamic_viscosity_Pa_s":1e-3,"geometry_provider_id":"geometry","geometry_provider_revision":"1","geometry_record_sha256":"1"*64,
        "pressure_provider_id":"pressure","pressure_provider_revision":"1","pressure_record_sha256":"2"*64,
        "fluid_property_provider_id":"fluid","fluid_property_provider_revision":"1","fluid_property_record_sha256":"3"*64,
        "evidence":evidence,"usage_rights_evidence":[{"source_id":"synthetic-rights","origin":"synthetic","citation":"Fabricated inputs only.","license_id":"CC0-1.0"}],"usage_license_id":"CC0-1.0"}
    for key in ("geometry_clock_and_grid_reviewed","pressure_reference_sign_and_clock_reviewed","incompressible_newtonian_property_support_reviewed","wide_slit_aspect_ratio_reviewed","laminar_fully_developed_resistance_reviewed","unsteady_lumped_inertance_applicability_reviewed","signed_flow_reversal_reviewed","usage_rights_reviewed","computational_use_authorized"): values[key]=True
    request=PlanarSlitTransientHydraulicHistory.model_validate_json(json.dumps(values))
    context=RunContext(asset_id="synthetic",location_id="synthetic",time_basis="elapsed_seconds")
    source=registry.run(hydraulic_specs()[0].model_id,request,context)
    assert source.status=="computed"
    wall=CreviceWallShearExposure(assessment_id="synthetic-shear",hydraulic_result=source,hydraulic_result_sha256=canonical_digest(source.model_dump(mode="json")),wall_shear_relation_and_wide_slit_profile_reviewed=True,quasi_steady_wall_shear_on_lumped_flow_reviewed=True,shear_exposure_is_descriptor_only_reviewed=True,computational_use_authorized=True)
    return wall


def shear_reference():
    from scipy.integrate import quad
    request=hydraulic()
    result=crevice_wall_shear_exposure(request)
    assert result.status=="computed"
    mu,width,gap,length,rho=1e-3,0.01,1e-4,0.01,1000.0
    resistance=12*mu*length/(width*gap**3)
    inertance=rho*length/(width*gap)
    rate=resistance/inertance
    factor=6*mu/(width*gap**2)
    previous=0.0
    records=[]
    for pressure,row in zip((120.0,-30.0),result.values["wall_shear_history"],strict=True):
        equilibrium=pressure/resistance
        q=lambda t: equilibrium+(previous-equilibrium)*math.exp(-rate*t)
        duration=row["duration_s"]
        root=None
        ratio=-equilibrium/(previous-equilibrium)
        if 0.0<ratio<1.0:
            possible=-math.log(ratio)/rate
            if 0.0<possible<duration: root=possible
        points=[] if root is None else [root]
        signed=quad(lambda t:factor*q(t),0.0,duration,epsabs=1e-13,points=points)[0]
        absolute=quad(lambda t:abs(factor*q(t)),0.0,duration,epsabs=1e-13,points=points)[0]
        cell=row["cells"][0]
        assert math.isclose(cell["signed_wall_shear_impulse_Pa_s"],signed,rel_tol=1e-9,abs_tol=1e-12)
        assert math.isclose(cell["absolute_wall_shear_impulse_Pa_s"],absolute,rel_tol=1e-9,abs_tol=1e-12)
        records.append({"signed_reference_Pa_s":signed,"absolute_reference_Pa_s":absolute,"internal_reversal_elapsed_s":root})
        previous=q(duration)
    assert records[-1]["internal_reversal_elapsed_s"] is not None
    assert records[-1]["absolute_reference_Pa_s"]>abs(records[-1]["signed_reference_Pa_s"])
    return {"independent_geometry_R_I_and_quad":records,"erosion_or_corrosion_prediction":False}


def shear_gates():
    request=hydraulic()
    invalid=request.model_dump(mode="json")
    invalid["hydraulic_result_sha256"]="f"*64
    try: CreviceWallShearExposure.model_validate_json(json.dumps(invalid))
    except ValidationError: pass
    else: raise AssertionError("source result digest mismatch accepted")
    values=request.model_dump(mode="json")
    values["computational_use_authorized"]=False
    assert crevice_wall_shear_exposure(CreviceWallShearExposure.model_validate_json(json.dumps(values))).status=="needs_data"
    parity()
    return {"pinned_digest_rejection":True,"review_gate":True,"metadata_source_parent_package_parity":True}


def main():
    tasks={"phase-balanced":phase_balanced,"phase-gates":phase_gates,"shear-reference":shear_reference,"shear-gates":shear_gates}
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",choices=tasks,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task":args.task,"status":"failed","exception_type":type(error).__name__,"message":str(error)},indent=2),encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task":args.task,"status":"passed","details":details,"meaning":"targeted mathematical/software checks; no physical qualification"},indent=2),encoding="utf-8")


if __name__=="__main__": main()
