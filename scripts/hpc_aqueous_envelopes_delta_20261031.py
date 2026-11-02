"""Analytic two-species finite-case envelopes and exact topology boundaries."""
import argparse
import json
import math
from pathlib import Path
from pydantic import ValidationError
from matintegrity.contracts import canonical_digest

ROOT=Path(__file__).resolve().parents[1]

def system(index,topology=False):
    factor=2.0 if topology and index else 1.0
    values={'assessment_id':'synthetic-'+str(index),'solution_id':'synthetic','temperature_K':300.0,'activity_standard_state':'molarity_1_mol_L','species':[{'species_id':name,'charge_number':0,'activity_coefficient':1.0,'initial_activity':1.0,'elemental_composition':{'X':1}} for name in ('A','B')],'reactions':[{'reaction_id':'R'+str(index) if topology else 'R','log10_equilibrium_constant':math.log10(3.0)*factor if index else 0.0,'terms':[{'species_id':'A','coefficient':-factor},{'species_id':'B','coefficient':factor}]}],'constraints':[{'constraint_id':'total','target_mol_L':3.0,'residual_scale_mol_L':3.0,'terms':[{'species_id':'A','coefficient':1.0},{'species_id':'B','coefficient':1.0}]}],'activity_provider_id':'synthetic-activity','activity_provider_revision':'1','activity_configuration_digest':'a'*64,'activity_record_digest':'b'*64,'equilibrium_provider_id':'synthetic-equilibrium','equilibrium_provider_revision':'1','equilibrium_configuration_digest':'c'*64,'equilibrium_record_digest':'d'*64,'evidence':[{'source_id':'synthetic','origin':'synthetic','citation':'Fabricated neutral isomer mass-action system only.'}]}
    for field in ('complete_aqueous_species_inventory_reviewed','reaction_stoichiometry_and_constant_reviewed','balance_constraints_and_charge_scope_reviewed','fixed_activity_coefficients_and_standard_state_reviewed','temperature_and_provider_lineage_reviewed','initial_activity_guess_and_solver_tolerance_reviewed','single_liquid_phase_and_no_precipitation_reviewed','elemental_formula_and_reaction_balance_reviewed'): values[field]=True
    return values

def payload(topology):
    if topology:
        values={'comparison_id':'synthetic','topologies':[{'topology_id':'case-'+str(i),'description':'Fabricated reaction topology '+str(i),'request':system(i,True)} for i in range(2)]}
        fields=('alternative_networks_are_complete_caller_systems_reviewed','fixed_species_inventory_and_solution_state_reviewed','common_balance_constraints_and_standard_state_reviewed','provider_revisions_and_topology_comparability_reviewed','finite_topology_set_and_no_probability_interpretation_reviewed')
    else:
        values={'envelope_id':'synthetic','scenarios':[{'scenario_id':'case-'+str(i),'scenario_label':'Fabricated numeric case '+str(i),'request':system(i)} for i in range(2)]}
        fields=('solution_identity_and_fixed_network_topology_reviewed','finite_scenario_set_is_caller_owned_and_complete_for_comparison_reviewed','provider_family_and_revision_are_comparable_reviewed','no_probability_or_distribution_interpretation_reviewed')
    values.update({field:True for field in fields});return values

def rejects(factory):
    try: factory()
    except (ValueError,ValidationError): return
    raise AssertionError('incomparable finite cases accepted')

def check(task):
    kind,partition=task.split('-');topology=kind=='topology'
    if topology:
        from matintegrity import aqueous_mass_action_topology_envelope as module
        cls=module.AqueousMassActionTopologyEnvelope;evaluator=module.evaluate_aqueous_mass_action_topology_envelope;collection='topologies';prefix='topology'
    else:
        from matintegrity import aqueous_mass_action_scenario_envelope as module
        cls=module.AqueousMassActionScenarioEnvelope;evaluator=module.evaluate_aqueous_mass_action_scenario_envelope;collection='scenarios';prefix='scenario'
    artifact=json.loads((ROOT/f'metadata/aqueous_{kind}_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==cls.model_json_schema()
    values=payload(topology);request=cls.model_validate_json(json.dumps(values));result=evaluator(request);assert result.status=='computed'
    envelope={r['species_id']:r for r in result.values['species_envelope']}
    for species,minimum,maximum in (('A',0.75,1.5),('B',1.5,2.25)):
        assert math.isclose(envelope[species]['concentration_min_mol_L'],minimum,rel_tol=1e-8) and math.isclose(envelope[species]['concentration_max_mol_L'],maximum,rel_tol=1e-8)
    assert result.values['probability_or_confidence'] is None and result.values['distribution_interpretation']=='none'
    assert module.specifications()[0].units['species_envelope[].concentration_span_mol_L']=='mol/L'
    results=result.values['topology_results' if topology else 'scenario_results']
    for source,row in zip(getattr(request,collection),results,strict=True): assert row['request_sha256']==canonical_digest(source.request.model_dump(mode='json'))
    if partition=='failure':
        values=payload(topology);values[collection][1]['request']['complete_aqueous_species_inventory_reviewed']=False
        failed=evaluator(cls.model_validate_json(json.dumps(values)));assert failed.status=='needs_data' and failed.values['completed_'+prefix+'_count']==1
        assert failed.values['species_envelope' if topology else 'envelope'] is None
        for change in ('provider','topology-state','unit'):
            values=payload(topology);other=values[collection][1]['request']
            if change=='provider': other['equilibrium_provider_revision']='incomparable'
            elif change=='unit': other['activity_standard_state']='unsupported_molality_basis'
            elif topology: other['temperature_K']=301.0
            else:
                other['reactions'][0]['terms'][0]['coefficient']=-2.0;other['reactions'][0]['terms'][1]['coefficient']=2.0
            rejects(lambda:cls.model_validate_json(json.dumps(values)))
        if topology:
            values=payload(True);values['topologies'][1]['request']['reactions']=values['topologies'][0]['request']['reactions'];rejects(lambda:cls.model_validate_json(json.dumps(values)))
    return {'partition':task,'independent_analytic_isomer_ratios_1_and_3_total_3':True,'complete_case_extrema_and_prefix_policy':True,'actual_chemistry_or_global_probability_bound_validated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['scenario-envelope','scenario-failure','topology-envelope','topology-failure'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(args.task)
    except Exception as error:
        args.output.write_text(json.dumps({'status':'failed','error':str(error)},indent=2));raise
    args.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
