"""Synthetic example: reduce a supplied translational stiffness matrix."""

from matintegrity.models.flange_compliance_reduction import (
    FlangeComplianceReductionRequest,
    FlangeComplianceReductionHistoryRequest,
    reduce_flange_contact_compliance_history,
    reduce_flange_contact_compliance,
)


request = FlangeComplianceReductionRequest(
    reduction_id="synthetic-flange-operator",
    upstream_solver_id="caller-fea",
    upstream_solver_revision="synthetic-revision",
    stiffness_source_sha256="e" * 64,
    stiffness_matrix_N_m=(
        (3000.0, -1000.0, 0.0),
        (-1000.0, 3000.0, -1000.0),
        (0.0, -1000.0, 2000.0),
    ),
    fixed_incremental_dof_indices=(0,),
    contact_node_ids=("gasket-sector-1", "gasket-sector-2"),
    contact_normal_dof_indices=(1, 2),
    contact_closure_signs=(1, 1),
    stiffness_units_and_scaling_reviewed=True,
    fixed_supports_and_boundary_dofs_reviewed=True,
    contact_normal_dof_mapping_reviewed=True,
    incremental_linear_elastic_applicability_reviewed=True,
    computational_use_authorized=True,
)

result = reduce_flange_contact_compliance(request)
print(result.model_dump(mode="json"))

history_request = FlangeComplianceReductionHistoryRequest(
    history_id="synthetic-flange-operator-history",
    upstream_solver_id="caller-fea",
    upstream_solver_revision="synthetic-revision",
    times_s=(0.0, 10.0),
    stiffness_source_sha256=("f" * 64, "1" * 64),
    stiffness_matrices_N_m=(
        (
            (3000.0, -1000.0, 0.0),
            (-1000.0, 3000.0, -1000.0),
            (0.0, -1000.0, 2000.0),
        ),
        (
            (3200.0, -1000.0, 0.0),
            (-1000.0, 3200.0, -1000.0),
            (0.0, -1000.0, 2200.0),
        ),
    ),
    fixed_incremental_dof_indices=(0,),
    contact_node_ids=("gasket-sector-1", "gasket-sector-2"),
    contact_normal_dof_indices=(1, 2),
    contact_closure_signs=(1, 1),
    stiffness_units_and_scaling_reviewed=True,
    fixed_supports_and_boundary_dofs_reviewed=True,
    contact_normal_dof_mapping_reviewed=True,
    incremental_linear_elastic_applicability_reviewed=True,
    computational_use_authorized=True,
)
history_result = reduce_flange_contact_compliance_history(history_request)
print(history_result.model_dump(mode="json"))
