"""Run a bounded eddy-current acquisition summary with caller-reviewed inputs."""

from matintegrity import evaluate
from matintegrity.contracts import RunContext

evidence = {"source_id": "user-ec", "origin": "user_declared", "citation": "user procedure"}
inputs = {
    "examination_id": "exam-1",
    "procedure_id": "procedure-1",
    "procedure_revision": "1",
    "physical_scope_id": "surface-1",
    "material_id": "material-1",
    "material_condition_id": "condition-1",
    "probe": {
        "probe_id": "probe-1",
        "probe_mode": "absolute",
        "coil_configuration": "user-declared coil",
        "nominal_excitation_frequencies_Hz": [100000.0],
        "active_channel_ids": ["real", "imaginary"],
        "probe_geometry_basis": "user record",
        "lift_off_control_basis": "user procedure",
        "evidence": [evidence],
    },
    "reference_standard": {
        "reference_standard_id": "reference-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "applicable_probe_ids": ["probe-1"],
        "applicable_frequencies_Hz": [100000.0],
        "features": [
            {
                "feature_id": "feature-1",
                "feature_kind": "user reference feature",
                "geometry_description": "user-reviewed geometry",
                "physical_feature_identity_reviewed": True,
                "evidence": [evidence],
            }
        ],
        "evidence": [evidence],
    },
    "scans": [
        {
            "scan_id": "scan-1",
            "probe_id": "probe-1",
            "excitation_frequency_Hz": 100000.0,
            "data_sha256": "1" * 64,
            "row_count": 20,
            "column_count": 253,
            "component_order": ["real", "imaginary"],
            "signal_encoding": "signed_int16_with_external_scale",
            "signal_unit_token": "provider-token",
            "acquisition_order": 0,
            "time_basis": "user acquisition order",
        }
    ],
    "indications": [],
    "probe_identity_reviewed": True,
    "reference_standard_reviewed": True,
    "excitation_and_receiver_settings_reviewed": True,
    "lift_off_and_surface_condition_reviewed": True,
    "encoder_calibration_reviewed": True,
    "scan_identity_reviewed": True,
    "indication_mapping_reviewed": True,
    "negative_result_reviewed": True,
    "evidence": [evidence],
}

result = evaluate(
    "inspection.eddy_current_acquisition_summary",
    inputs,
    RunContext(asset_id="asset-1", location_id="surface-1", time_basis="scan order"),
)
print(result.status, result.values)
