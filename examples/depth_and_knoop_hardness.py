"""Synthetic geometry examples; no material or procedure qualification."""
from matintegrity.contracts import RunContext
from matintegrity.models.testmethods import KnoopIndent, RockwellDepth
from matintegrity.registry import default_registry


def sample_requests():
    return (
        ("testing.rockwell_depth", RockwellDepth(
            initial_depth_m=0.0, final_depth_m=80e-6, scale_id="HRC",
            scale_offset=100.0, depth_per_scale_unit_m=2e-6,
            scale_definition_basis="NIST depth-scale principle; synthetic readings",
            applicability_reviewed=True)),
        ("testing.knoop", KnoopIndent(
            test_force_N=9.80665, long_diagonal_m=0.001,
            longitudinal_edge_angle_deg=172.5, transverse_edge_angle_deg=130.0,
            indenter_geometry_basis="Synthetic ideal rhombic indenter geometry")),
    )


if __name__ == "__main__":
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="indent", time_basis="example")
    for model_id, inputs in sample_requests():
        print(registry.run(model_id, inputs, context).model_dump_json(indent=2))
