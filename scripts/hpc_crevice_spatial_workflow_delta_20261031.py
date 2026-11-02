"""Mock cell solver ordering and all-cells-before-ledger workflow contracts."""
import argparse,json
from pathlib import Path
import hpc_fatigue_crevice_bridge_delta_20261031 as transport_fixture
import hpc_aqueous_envelopes_delta_20261031 as chemistry_fixture
from matintegrity import crevice_spatial_mass_action_workflow as module
from matintegrity.contracts import Calculation,canonical_digest
ROOT=Path(__file__).resolve().parents[1]

def payload():
    binding=transport_fixture.crevice_payload();result={'status':'computed','values':{'campaign_id':'synthetic','campaign_input_sha256':canonical_digest(binding['campaign']),'geometry_history_sha256':binding['campaign']['geometry_history_sha256']}}
    cells=[]
    for i in range(2):
        system=chemistry_fixture.system(i);system['assessment_id']='cell-'+str(i);cells.append({'cell_index':i,'transport_cell_context_sha256':canonical_digest({'cell':i}),'aqueous_mass_action_input':system,'aqueous_mass_action_result':{}})
    ledger={'assessment_id':'synthetic-ledger','transport_binding':binding,'transport_binding_result':result,'transport_binding_result_sha256':canonical_digest(result),'knots':[{'knot_summary_index':0,'time_s':0.0,'geometry_side':'initial_or_interior','cells':cells}],'cell_composition_to_mass_action_constraints_reviewed':True,'mass_action_result_lineage_reviewed':True,'spatial_cells_must_remain_distinct_reviewed':True,'inventory_volume_basis_reviewed':True,'no_bulk_equilibrium_or_phase_inference_reviewed':True}
    return {'assessment_id':'synthetic-workflow','ledger_request':ledger,'local_solver_execution_authorized':True,'cell_specific_chemistry_mapping_reviewed':True}

def check(task):
    artifact=json.loads((ROOT/'metadata/crevice_workflow_snapshot.json').read_text());assert artifact['source_rows']==artifact['package_rows'];assert artifact['schema']==module.CreviceSpatialMassActionWorkflow.model_json_schema()
    calls=[];ledger_calls=[]
    def solver(system):
        calls.append(system.assessment_id)
        if task=='cell-local-solver-prefix' and system.assessment_id=='cell-1': return Calculation(status='needs_data',values={'synthetic_failure':True})
        return Calculation(values={'input_digest':canonical_digest(system.model_dump(mode='json')),'synthetic':True})
    def ledger(request):
        assert calls==['cell-0','cell-1']
        assert all(cell.aqueous_mass_action_result['status']=='computed' for knot in request.knots for cell in knot.cells)
        ledger_calls.append(True);return Calculation(values={'synthetic_ledger':True})
    module.aqueous_mass_action_speciation=solver;module.assemble_crevice_local_speciation_ledger=ledger
    request=module.CreviceSpatialMassActionWorkflow.model_validate_json(json.dumps(payload()));result=module.solve_crevice_spatial_mass_action_workflow(request)
    if task=='cell-local-solver-prefix': assert result.status=='needs_data' and result.values['completed_cell_solve_count']==1 and result.values['failed_cell_index']==1 and result.values['ledger_result'] is None and ledger_calls==[] and calls==['cell-0','cell-1']
    else: assert result.status=='computed' and result.values['completed_cell_solve_count']==2 and result.values['complete_knot_ledger_assembled'] and ledger_calls==[True]
    return {'partition':task,'mock_cell_solver_and_ledger_only':True,'exact_cell_order_prefix_and_complete_ledger_gate':True,'actual_transport_or_equilibrium_validated':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['cell-local-solver-prefix','all-cells-before-ledger'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    try: details=check(a.task)
    except Exception as e: a.output.write_text(json.dumps({'status':'failed','error':str(e)},indent=2));raise
    a.output.write_text(json.dumps({'status':'passed','details':details},indent=2))
