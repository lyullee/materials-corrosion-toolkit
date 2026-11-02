"""Steady-flux metal ceiling contracts on synthetic source/properties only."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity import scale_diffusion_metal_loss_bound as module
from matintegrity.contracts import AssessmentResult,RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    raw={'model_id':'chemistry.layered_scale_diffusion_limit','model_version':'synthetic','status':'computed','inputs':{'synthetic':True},'values':{'physical_scope_id':'scope','surface_area_basis_id':'area','transported_species_id':'S','area_average_flux_limit_mol_m2_s':0.2,'scale_state_id':'synthetic'},'units':{'area_average_flux_limit_mol_m2_s':'mol/m^2/s'},'assumptions':[],'notes':['Fabricated transport ceiling.'],'context':{'asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds'},'input_digest':'pending','source_ids':[],'qualification':'user_model','runtime':{}}
    normalized=AssessmentResult.model_validate_json(json.dumps(raw));raw['context']=normalized.context.model_dump(mode='json')
    raw['input_digest']=canonical_digest({k:raw[k] for k in ('model_id','model_version','inputs','context')});result=AssessmentResult.model_validate_json(json.dumps(raw)).model_dump(mode='json')
    paths=[{'reaction_id':name,'transported_species_id':'S','transported_species_mol_per_reaction_extent':species,'dissolved_metal_species_id':'M','metal_atoms_per_reaction_extent':metal,'metal_molar_mass_kg_mol':0.05,'metal_density_kg_m3':5000.0,'property_provider_id':'synthetic-properties','property_provider_revision':'1','property_record_id':'synthetic','property_record_sha256':'a'*64,'evidence':[{'source_id':'synthetic-properties','origin':'synthetic','citation':'Fabricated property record.','sha256':'a'*64}]} for name,species,metal in (('r1',1.0,1.0),('r2',2.0,3.0))]
    return {'assessment_id':'synthetic','physical_scope_id':'scope','scale_transport_result':result,'scale_transport_result_sha256':canonical_digest(result),'surface_area_basis_id':'area','exposure_duration_s':100.0,'candidate_pathways':paths,'sustained_steady_flux_limit_reviewed':True,'complete_productive_branch_set_reviewed':True,'reaction_stoichiometry_and_metal_mapping_reviewed':True,'common_area_density_and_uniform_recession_reviewed':True,'scope_state_and_duration_transfer_reviewed':True,'no_other_metal_loss_path_over_duration_reviewed':True,'computational_use_authorized':True}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported transport conversion accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/scale_metal_bound_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.ScaleDiffusionMetalLossBound.model_json_schema()
    cls=module.ScaleDiffusionMetalLossBound;request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_scale_diffusion_metal_loss_bound(request);assert result.status=='computed'
    assert math.isclose(result.values['maximum_uniform_penetration_rate_ceiling_m_s'],3e-6,rel_tol=1e-14) and math.isclose(result.values['maximum_uniform_penetration_loss_ceiling_m'],3e-4,rel_tol=1e-14)
    assert result.values['maximum_bound_reaction_id']=='r2' and 'reaction_branch_allocation' in result.values['not_inferred']
    registry=ModelRegistry();registry.register(module.specifications()[0]);assert registry.run(module.specifications()[0].model_id,request,request.scale_transport_result.context).values==result.values
    if task=='lineage-units-branches':
        assert result.values['scale_transport_result_sha256']==canonical_digest(request.scale_transport_result.model_dump(mode='json'))
        units=module.specifications()[0].units;assert units['maximum_uniform_penetration_loss_ceiling_m']=='m' and units['maximum_uniform_penetration_rate_ceiling_m_s']=='m/s'
        for row,path in zip(result.values['pathway_rate_ceilings'],request.candidate_pathways,strict=True):
            reference=0.2/path.transported_species_mol_per_reaction_extent*path.metal_atoms_per_reaction_extent*0.05/5000.0;assert math.isclose(row['uniform_penetration_rate_ceiling_m_s'],reference,rel_tol=1e-14)
        if module.specifications()[0].context_validator is not None: rejects(lambda:registry.run(module.specifications()[0].model_id,request,RunContext(asset_id='wrong',location_id='synthetic',time_basis='elapsed_seconds')))
    else:
        for change in ('digest','unit','area','species','property-evidence','duplicate-branch'):
            values=payload()
            if change=='digest': values['scale_transport_result_sha256']='f'*64
            elif change=='unit':
                values['scale_transport_result']['units']['area_average_flux_limit_mol_m2_s']='A/m2';values['scale_transport_result_sha256']=canonical_digest(values['scale_transport_result'])
            elif change=='area': values['surface_area_basis_id']='other'
            elif change=='species': values['candidate_pathways'][0]['transported_species_id']='other'
            elif change=='property-evidence': values['candidate_pathways'][0]['evidence'][0]['sha256']='f'*64
            else: values['candidate_pathways'][1]['reaction_id']='r1'
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        values=payload();values['complete_productive_branch_set_reviewed']=False;assert module.evaluate_scale_diffusion_metal_loss_bound(cls.model_validate_json(json.dumps(values))).status=='needs_data'
        values=payload();values['exposure_duration_s']=1e308
        for path in values['candidate_pathways']: path['metal_density_kg_m3']=1e-308
        assert module.evaluate_scale_diffusion_metal_loss_bound(cls.model_validate_json(json.dumps(values))).status=='out_of_scope'
    return {'partition':task,'synthetic_steady_flux_stoichiometry_mass_density_ceiling':True,'unknown_allocation_max_branch_envelope':True,'actual_corrosion_or_current_predicted':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['lineage-units-branches','bound-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
