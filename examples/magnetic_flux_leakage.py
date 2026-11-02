"""Synthetic magnetic-flux-leakage acquisition record."""

from matintegrity import evaluate
from matintegrity.contracts import Evidence, RunContext


def main():
    evidence = [Evidence(source_id="authored-example", origin="synthetic", citation="authored example")]
    inputs = {
        "examination_id": "example-mfl",
        "procedure_id": "example-procedure",
        "procedure_revision": "A",
        "physical_scope_id": "synthetic-plate",
        "material_id": "synthetic-steel",
        "material_condition_id": "synthetic-condition",
        "surface_condition": "synthetic clean surface",
        "magnetizer": {
            "magnetizer_id": "magnetizer-1",
            "excitation_type": "permanent_magnet",
            "nominal_magnetization_direction": "axial",
            "pole_spacing_m": 0.1,
            "magnetization_control_basis": "synthetic fixture",
            "evidence": evidence,
        },
        "sensor_arrays": [
            {
                "sensor_array_id": "array-1",
                "channel_ids": ["radial-1"],
                "measured_components": ["radial"],
                "channel_component_by_id": {"radial-1": "radial"},
                "nominal_channel_pitch_m": 0.002,
                "lift_off_control_basis": "synthetic fixed spacer",
                "calibration_id": "synthetic-calibration",
                "calibration_basis": "authored example",
                "evidence": evidence,
            }
        ],
        "reference_standard": {
            "reference_standard_id": "reference-1",
            "material_id": "synthetic-steel",
            "material_condition_id": "synthetic-condition",
            "wall_thickness_m": 0.01,
            "applicable_magnetizer_ids": ["magnetizer-1"],
            "applicable_sensor_array_ids": ["array-1"],
            "features": [
                {
                    "feature_id": "recess-1",
                    "feature_kind": "synthetic recess",
                    "surface": "external",
                    "geometry_description": "authored rectangular recess",
                    "nominal_depth_m": 0.002,
                    "physical_feature_identity_reviewed": True,
                    "evidence": evidence,
                }
            ],
            "evidence": evidence,
        },
        "magnetic_field_checkpoints": [
            {
                "checkpoint_id": "field-1",
                "physical_location_description": "synthetic plate centre",
                "coordinate_frame": "x axial, y circumferential, z outward",
                "magnetic_field_strength_A_m": (5000.0, 0.0, 0.0),
                "magnetic_flux_density_T": (1.0, 0.0, 0.0),
                "measurement_temperature_K": 293.15,
                "measurement_basis": "authored exact vector",
                "state_identity_reviewed": True,
                "evidence": evidence,
            }
        ],
        "scans": [
            {
                "scan_id": "scan-1",
                "magnetizer_id": "magnetizer-1",
                "sensor_array_id": "array-1",
                "active_channel_ids": ["radial-1"],
                "data_sha256": "1" * 64,
                "sample_count": 6,
                "signal_encoding": "synthetic float",
                "signal_unit_token": "T",
                "pass_direction": "forward",
                "scan_speed_m_s": 0.05,
                "scan_speed_basis": "synthetic constant speed",
                "sample_spacing_m": 0.002,
                "encoder_origin_m": 0.0,
                "coordinate_mapping_basis": "synthetic encoder",
                "acquisition_order": 0,
                "time_basis": "synthetic scan order",
            }
        ],
        "indications": [],
        "magnetizer_identity_reviewed": True,
        "sensor_calibration_reviewed": True,
        "reference_standard_reviewed": True,
        "magnetization_state_reviewed": True,
        "lift_off_and_surface_condition_reviewed": True,
        "encoder_calibration_reviewed": True,
        "scan_identity_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": True,
        "evidence": evidence,
    }
    result = evaluate(
        "inspection.magnetic_flux_leakage_acquisition_summary",
        inputs,
        RunContext(asset_id="synthetic", location_id="synthetic-plate", time_basis="scan order"),
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
