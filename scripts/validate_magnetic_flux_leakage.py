"""Verify authored MFL encoder and magnetic-vector identities."""

from __future__ import annotations

import json
import math
from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.models.magnetic_flux_leakage import (
    MflExamination,
    magnetic_flux_leakage_acquisition_summary,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/magnetic_flux_leakage_math.json"


def main():
    evidence = Evidence(source_id="authored-mfl-validation", origin="synthetic", citation="authored identity")
    examination = MflExamination(
        examination_id="mfl-validation",
        procedure_id="authored-procedure",
        procedure_revision="1",
        physical_scope_id="authored-plate",
        material_id="authored-steel",
        material_condition_id="authored-condition",
        surface_condition="authored surface",
        magnetizer={
            "magnetizer_id": "magnetizer",
            "excitation_type": "permanent_magnet",
            "nominal_magnetization_direction": "axial",
            "pole_spacing_m": 0.1,
            "magnetization_control_basis": "authored fixture",
            "evidence": [evidence],
        },
        sensor_arrays=[
            {
                "sensor_array_id": "array",
                "channel_ids": ["radial"],
                "measured_components": ["radial"],
                "channel_component_by_id": {"radial": "radial"},
                "nominal_channel_pitch_m": 0.002,
                "lift_off_control_basis": "authored spacer",
                "calibration_id": "authored-calibration",
                "calibration_basis": "authored exact values",
                "evidence": [evidence],
            }
        ],
        reference_standard={
            "reference_standard_id": "reference",
            "material_id": "authored-steel",
            "material_condition_id": "authored-condition",
            "wall_thickness_m": 0.01,
            "applicable_magnetizer_ids": ["magnetizer"],
            "applicable_sensor_array_ids": ["array"],
            "features": [
                {
                    "feature_id": "recess",
                    "feature_kind": "authored recess",
                    "surface": "external",
                    "geometry_description": "authored geometry",
                    "nominal_depth_m": 0.002,
                    "physical_feature_identity_reviewed": True,
                    "evidence": [evidence],
                }
            ],
            "evidence": [evidence],
        },
        magnetic_field_checkpoints=[
            {
                "checkpoint_id": "field",
                "physical_location_description": "authored centre",
                "coordinate_frame": "authored orthogonal frame",
                "magnetic_field_strength_A_m": (3000.0, 4000.0, 0.0),
                "magnetic_flux_density_T": (0.6, 0.8, 0.0),
                "measurement_temperature_K": 293.15,
                "measurement_basis": "authored exact vectors",
                "state_identity_reviewed": True,
                "evidence": [evidence],
            }
        ],
        scans=[
            {
                "scan_id": "scan",
                "magnetizer_id": "magnetizer",
                "sensor_array_id": "array",
                "active_channel_ids": ["radial"],
                "data_sha256": "1" * 64,
                "sample_count": 6,
                "signal_encoding": "authored",
                "signal_unit_token": "T",
                "pass_direction": "forward",
                "scan_speed_m_s": 0.05,
                "scan_speed_basis": "authored speed",
                "sample_spacing_m": 0.002,
                "encoder_origin_m": 0.1,
                "coordinate_mapping_basis": "authored encoder",
                "acquisition_order": 0,
                "time_basis": "authored order",
            }
        ],
        indications=[],
        magnetizer_identity_reviewed=True,
        sensor_calibration_reviewed=True,
        reference_standard_reviewed=True,
        magnetization_state_reviewed=True,
        lift_off_and_surface_condition_reviewed=True,
        encoder_calibration_reviewed=True,
        scan_identity_reviewed=True,
        indication_mapping_reviewed=True,
        negative_result_reviewed=True,
        evidence=[evidence],
    )
    result = magnetic_flux_leakage_acquisition_summary(examination)
    checkpoint = result.values["magnetic_field_checkpoints"]["field"]
    observed = {
        "encoded_span_m": result.values["scan_geometry_by_id"]["scan"]["encoded_span_m"],
        "magnetic_field_strength_magnitude_A_m": checkpoint["magnetic_field_strength_magnitude_A_m"],
        "magnetic_flux_density_magnitude_T": checkpoint["magnetic_flux_density_magnitude_T"],
        "magnitude_ratio_B_T_per_H_A_m": checkpoint["magnitude_ratio_B_T_per_H_A_m"],
    }
    expected = {
        "encoded_span_m": 0.01,
        "magnetic_field_strength_magnitude_A_m": math.hypot(3000.0, 4000.0),
        "magnetic_flux_density_magnitude_T": math.hypot(0.6, 0.8),
        "magnitude_ratio_B_T_per_H_A_m": 2e-4,
    }
    absolute_error = {key: abs(observed[key] - expected[key]) for key in expected}
    assert result.status == "computed"
    assert max(absolute_error.values()) <= 1e-15
    payload = {
        "schema_version": "matintegrity.validation.magnetic_flux_leakage_math.v1",
        "model_id": "inspection.magnetic_flux_leakage_acquisition_summary",
        "case": "authored encoder and Euclidean magnetic-vector identities",
        "expected": expected,
        "observed": observed,
        "absolute_error": absolute_error,
        "qualification": (
            "Mathematical identity and contract verification only; no magnetic saturation, field uniformity, "
            "signal processing, detection, sizing, POD or acceptance qualification."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
