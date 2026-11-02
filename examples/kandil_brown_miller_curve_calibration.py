"""Synthetic wiring example for a caller-calibrated KBM life curve."""

from matintegrity.contracts import Evidence
from matintegrity.multiaxial_life_campaign import (
    ShearNormalLifeCurvePoint,
    build_kandil_brown_miller_life_calibration,
)


def build_synthetic_calibration():
    evidence = Evidence(
        source_id="synthetic_kbm_curve",
        origin="synthetic",
        citation="Illustrative synthetic values; not material data",
        license_id="synthetic-example",
    )
    points = (
        ShearNormalLifeCurvePoint(
            cycles_to_failure=1.0e3,
            parameter_value=2.0e-2,
            evidence_source_id=evidence.source_id,
            source_record_id="synthetic-kbm-row-001",
        ),
        ShearNormalLifeCurvePoint(
            cycles_to_failure=1.0e4,
            parameter_value=8.0e-3,
            evidence_source_id=evidence.source_id,
            source_record_id="synthetic-kbm-row-002",
        ),
        ShearNormalLifeCurvePoint(
            cycles_to_failure=1.0e5,
            parameter_value=3.0e-3,
            evidence_source_id=evidence.source_id,
            source_record_id="synthetic-kbm-row-003",
        ),
    )
    return build_kandil_brown_miller_life_calibration(
        normal_strain_range_coefficient=0.5,
        curve_points=points,
        calibration_material_condition_id="synthetic-material-state",
        evidence=(evidence,),
        curve_interpolation_and_parameter_basis_reviewed=True,
        calibration_rights_and_condition_match_reviewed=True,
    )


if __name__ == "__main__":
    calibration, digest = build_synthetic_calibration()
    print(calibration.model_dump_json(indent=2))
    print(f"calibration_sha256={digest}")
