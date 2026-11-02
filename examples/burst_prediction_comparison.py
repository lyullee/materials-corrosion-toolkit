"""Compare caller-supplied pressure predictions without embedding a standard equation."""

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

row = {
    "observation_id": "test-001",
    "physical_specimen_id": "specimen-001",
    "source_group_id": "qualified-test-program-a",
    "partition": "external_validation",
    "material_condition_id": "steel-heat-and-condition",
    "geometry_id": "pipe-and-defect-geometry-001",
    "load_case_id": "monotonic-internal-pressure",
    "observed_pressure_basis": "internal_minus_external",
    "predicted_pressure_basis": "internal_minus_external",
    "observed_burst_pressure_Pa": 12.0e6,
    "predicted_failure_pressure_Pa": 11.4e6,
    "observation_source_sha256": "a" * 64,
    "prediction_input_digest": "b" * 64,
    "observation_use_authorized": True,
    "experimental_endpoint_reviewed": True,
    "geometry_and_material_reviewed": True,
    "pressure_basis_reviewed": True,
}

result = default_registry().run(
    "structural.burst_pressure_comparison",
    {
        "comparison_id": "provider-vs-qualified-test",
        "prediction_provider_id": "user.pressure-provider",
        "prediction_provider_version": "1.0.0",
        "prediction_configuration_digest": "c" * 64,
        "rows": (row,),
        "physical_specimen_independence_reviewed": True,
        "source_group_partitioning_reviewed": True,
        "prediction_frozen_before_evaluation": True,
    },
    RunContext(asset_id="test-program", location_id="pipe-defects", time_basis="burst endpoint"),
)
print(result.model_dump_json(indent=2))
