"""Verify authored eddy-current raster and classical skin-depth identities."""

import json
import math
from pathlib import Path

from matintegrity.models.eddy_current import (
    VACUUM_PERMEABILITY_H_M,
    EddyCurrentExamination,
    eddy_current_acquisition_summary,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/eddy_current_math.json"


def main():
    evidence = {"source_id": "authored-eddy-current", "origin": "synthetic", "citation": "authored identity"}
    frequency = 100000.0
    conductivity = 58e6
    examination = EddyCurrentExamination.model_validate(
        {
            "examination_id": "authored-ec-exam",
            "procedure_id": "authored-ec-procedure",
            "procedure_revision": "1",
            "physical_scope_id": "synthetic-surface",
            "material_id": "synthetic-conductor",
            "material_condition_id": "synthetic-linear-homogeneous",
            "probe": {
                "probe_id": "probe",
                "probe_mode": "absolute",
                "coil_configuration": "authored coil",
                "nominal_excitation_frequencies_Hz": [frequency],
                "active_channel_ids": ["real", "imaginary"],
                "probe_geometry_basis": "authored",
                "lift_off_control_basis": "authored",
                "evidence": [evidence],
            },
            "reference_standard": {
                "reference_standard_id": "reference",
                "material_id": "synthetic-conductor",
                "material_condition_id": "synthetic-linear-homogeneous",
                "applicable_probe_ids": ["probe"],
                "applicable_frequencies_Hz": [frequency],
                "conductivity_S_m": conductivity,
                "relative_magnetic_permeability": 1.0,
                "property_temperature_K": 293.15,
                "electromagnetic_property_basis": "authored exact value",
                "features": [
                    {
                        "feature_id": "feature",
                        "feature_kind": "authored slot",
                        "geometry_description": "authored",
                        "nominal_depth_m": 0.001,
                        "physical_feature_identity_reviewed": True,
                        "evidence": [evidence],
                    }
                ],
                "evidence": [evidence],
            },
            "scans": [
                {
                    "scan_id": "scan",
                    "probe_id": "probe",
                    "excitation_frequency_Hz": frequency,
                    "data_sha256": "1" * 64,
                    "row_count": 3,
                    "column_count": 4,
                    "component_order": ["real", "imaginary"],
                    "signal_encoding": "authored",
                    "signal_unit_token": "authored",
                    "x_increment_m": 0.001,
                    "y_increment_m": 0.002,
                    "coordinate_mapping_basis": "authored exact raster",
                    "scan_origin_x_m": 0.0,
                    "scan_origin_y_m": 0.0,
                    "acquisition_order": 0,
                    "time_basis": "authored order",
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
            "linear_homogeneous_skin_depth_applicable": True,
            "negative_result_reviewed": True,
            "evidence": [evidence],
        }
    )
    result = eddy_current_acquisition_summary(examination)
    geometry = result.values["scan_geometry_by_id"]["scan"]
    observed = {
        "x_span_m": geometry["x_span_m"],
        "y_span_m": geometry["y_span_m"],
        "sample_position_count": geometry["sample_position_count"],
        "skin_depth_m": result.values["skin_depth_m_by_frequency_Hz"][str(frequency)],
    }
    expected = {
        "x_span_m": 0.003,
        "y_span_m": 0.004,
        "sample_position_count": 12,
        "skin_depth_m": math.sqrt(1 / (math.pi * frequency * VACUUM_PERMEABILITY_H_M * conductivity)),
    }
    errors = {key: abs(observed[key] - expected[key]) for key in ("x_span_m", "y_span_m", "skin_depth_m")}
    if result.status != "computed" or max(errors.values()) > 1e-15:
        raise AssertionError("eddy-current authored identity verification failed")
    report = {
        "schema_version": "matintegrity.validation.eddy_current_math.v1",
        "model_id": "inspection.eddy_current_acquisition_summary",
        "case": "authored raster and linear homogeneous skin-depth identity",
        "expected": expected,
        "observed": observed,
        "absolute_error": errors,
        "qualification": "Mathematical identity and contract verification only; no field, lift-off, signal-processing, detection, sizing, POD or acceptance qualification.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
