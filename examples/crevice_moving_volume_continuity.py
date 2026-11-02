"""Synthetic demonstration of slit-cell liquid continuity during closure."""
from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_moving_volume_continuity import (
    CreviceMovingVolumeContinuityRequest,
    evaluate_crevice_moving_volume_continuity,
)

assessment_id = "synthetic-moving-volume-demo"
physical_scope_id = "synthetic-two-cell-slit"
time_s = (0.0, 10.0)
cell_ids = ("cell-1", "cell-2")
cell_lengths_m = (0.1, 0.1)
width_m = 0.01
aperture = ((1.0e-3, 1.0e-3), (0.9e-3, 0.9e-3))
left_flow = (0.0, 0.0)
right_flow = (2.0e-8, 2.0e-8)
geometry_record = {
    "assessment_id": assessment_id,
    "physical_scope_id": physical_scope_id,
    "time_s": list(time_s),
    "cell_ids": list(cell_ids),
    "cell_lengths_m": list(cell_lengths_m),
    "transverse_width_m": width_m,
    "aperture_m_by_knot_and_cell": [list(row) for row in aperture],
}
boundary_record = {
    "physical_scope_id": physical_scope_id,
    "time_s": list(time_s),
    "left_boundary_flow_m3_s_by_knot": list(left_flow),
    "right_boundary_flow_m3_s_by_knot": list(right_flow),
}
geometry_sha = canonical_digest(geometry_record)
boundary_sha = canonical_digest(boundary_record)
request = CreviceMovingVolumeContinuityRequest(
    assessment_id=assessment_id,
    physical_scope_id=physical_scope_id,
    time_s=time_s,
    cell_ids=cell_ids,
    cell_lengths_m=cell_lengths_m,
    transverse_width_m=width_m,
    aperture_m_by_knot_and_cell=aperture,
    left_boundary_flow_m3_s_by_knot=left_flow,
    right_boundary_flow_m3_s_by_knot=right_flow,
    geometry_sha256=geometry_sha,
    boundary_flow_sha256=boundary_sha,
    evidence=(
        Evidence(source_id="synthetic_geometry", origin="synthetic", citation="Example geometry generated for API demonstration.", license_id="synthetic-example", sha256=geometry_sha),
        Evidence(source_id="synthetic_boundary_flow", origin="synthetic", citation="Example boundary schedule generated for API demonstration.", license_id="synthetic-example", sha256=boundary_sha),
    ),
    geometry_boundary_and_sign_convention_reviewed=True,
    incompressible_liquid_and_fixed_mesh_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_crevice_moving_volume_continuity(request)
print(result.model_dump_json(indent=2))
