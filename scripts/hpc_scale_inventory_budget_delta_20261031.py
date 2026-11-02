"""Gross precipitation inventory arithmetic on a fabricated scale ledger."""
import argparse
import json
from pathlib import Path
from pydantic import ValidationError
from matintegrity import scale_precipitation_inventory_budget as module
from matintegrity.contracts import AssessmentResult,RunContext,canonical_digest
from matintegrity.registry import ModelRegistry

ROOT=Path(__file__).resolve().parents[1]

def payload():
    source_inputs={'assessment_id':'synthetic','physical_scope_id':'scope','scale_phase_id':'phase'}
    raw={'model_id':'chemistry.caller_surface_scale_kinetics','model_version':'synthetic','status':'computed','inputs':source_inputs,'values':{'assessment_id':'synthetic','physical_scope_id':'scope','scale_phase_id':'phase','input_digest':canonical_digest(source_inputs),'scale_history':[{'time_s':0.0},{'interval_id':'a','time_s':10.0,'precipitated_mol_m2':1.0,'dissolved_mol_m2':999.0},{'interval_id':'b','time_s':20.0,'precipitated_mol_m2':2.0,'dissolved_mol_m2':999.0}]},'units':{'scale_history[].precipitated_mol_m2':'mol/m^2'},'assumptions':[],'notes':['Fabricated gross inventory only.'],'context':{'asset_id':'synthetic','location_id':'synthetic','time_basis':'elapsed_seconds'},'input_digest':canonical_digest(source_inputs),'source_ids':[],'qualification':'user_model','runtime':{}}
    result=AssessmentResult.model_validate_json(json.dumps(raw)).model_dump(mode='json')
    evidence=lambda record:[{'source_id':record,'origin':'synthetic','citation':'Fabricated area/reactant/supply contract.'}]
    reactants=[]
    for species,stoich,stock,added in (('A',2.0,10.0,(1.0,2.0)),('B',1.0,20.0,(0.0,0.0))):
        reactants.append({'aqueous_species_id':species,'moles_required_per_scale_formula_mol':stoich,'initial_available_mol':stock,'initial_inventory_record_id':'stock','initial_inventory_evidence':evidence('stock'),'interval_supply':[{'interval_id':name,'added_mol':amount,'source_record_id':'supply','evidence':evidence('supply')} for name,amount in zip(('a','b'),added)]})
    return {'assessment_id':'synthetic','physical_scope_id':'scope','scale_history_result':result,'scale_history_result_sha256':canonical_digest(result),'exposed_area_m2':2.0,'exposed_area_record_id':'area','exposed_area_evidence':evidence('area'),'limiting_reactants':reactants,'scale_formula_stoichiometry_reviewed':True,'inventory_accessibility_and_interval_supply_reviewed':True,'scale_history_scope_and_area_mapping_reviewed':True,'gross_precipitation_only_no_dissolution_credit_reviewed':True,'computational_use_authorized':True}

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('unsupported source mapping accepted')

def check(task):
    artifact=json.loads((ROOT/'metadata/scale_inventory_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.ScalePrecipitationInventoryBudget.model_json_schema()
    cls=module.ScalePrecipitationInventoryBudget;request=cls.model_validate_json(json.dumps(payload()));result=module.evaluate_scale_precipitation_inventory_budget(request);assert result.status=='computed'
    assert result.values['final_available_inventory_mol']=={'A':1.0,'B':14.0}
    assert [row['gross_scale_formula_units_mol'] for row in result.values['completed_intervals']]==[2.0,4.0]
    assert all(row['gross_dissolution_credit_mol']==0.0 for row in result.values['completed_intervals'])
    registry=ModelRegistry();registry.register(module.specifications()[0]);context=request.scale_history_result.context
    assert registry.run(module.specifications()[0].model_id,request,context).values==result.values
    if task=='inventory-lineage':
        assert result.values['scale_history_result_sha256']==canonical_digest(request.scale_history_result.model_dump(mode='json'))
        assert result.values['scale_history_input_sha256']==canonical_digest(request.scale_history_result.inputs)
        units=module.specifications()[0].units;assert units['exposed_area_m2']=='m^2' and units['limiting_reactants[].moles_required_per_scale_formula_mol']=='mol/mol'
        for row in result.values['completed_intervals']:
            for reactant in row['reactants']: assert reactant['available_before_mol']-reactant['gross_precipitation_demand_mol']==reactant['remaining_after_mol']
    else:
        for field in ('asset_id','location_id','time_basis'):
            values={'asset_id':context.asset_id,'location_id':context.location_id,'time_basis':context.time_basis};values[field]='wrong-context'
            rejects(lambda:registry.run(module.specifications()[0].model_id,request,RunContext(**values)))
        values=payload();values['limiting_reactants'][0]['initial_available_mol']=8.0
        for supply in values['limiting_reactants'][0]['interval_supply']: supply['added_mol']=0.0
        shortage=module.evaluate_scale_precipitation_inventory_budget(cls.model_validate_json(json.dumps(values)));assert shortage.status=='out_of_scope' and shortage.values['completed_interval_count']==1 and shortage.values['first_inventory_shortfall_interval_id']=='b' and shortage.values['rejected_interval_is_not_committed']
        for change in ('digest','scope','supply-order','area-evidence'):
            values=payload()
            if change=='digest': values['scale_history_result_sha256']='f'*64
            elif change=='scope': values['physical_scope_id']='other'
            elif change=='supply-order': values['limiting_reactants'][0]['interval_supply'].reverse()
            else: values['exposed_area_record_id']='uncited'
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        values=payload();values['gross_precipitation_only_no_dissolution_credit_reviewed']=False;assert module.evaluate_scale_precipitation_inventory_budget(cls.model_validate_json(json.dumps(values))).status=='needs_data'
    return {'partition':task,'gross_precipitation_area_stoichiometry_inventory_closure':True,'no_dissolution_recycling_credit':True,'actual_chemistry_or_scale_kinetics_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['inventory-lineage','shortage-fail-closed'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
