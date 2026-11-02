"""Authored synthetic API composition; no recommended material or design values."""

import json

from matintegrity.assembly_calculations import (
    ElasticJointLoad,
    TubeCondition,
    TubeLayout,
    elastic_joint_load,
    tube_bundle_inventory,
    tube_layout_geometry,
)
from matintegrity.critical_plane_life import CriticalPlaneFsLife, evaluate_critical_plane_fs_life
from matintegrity.fad_envelope import FadEnvelope, FadPoint, evaluate_fad_envelope


def main():
    geometry = tube_layout_geometry(
        TubeLayout(
            tube_outer_diameter_m=0.02,
            tube_inner_diameter_m=0.016,
            pitch_m=0.027,
            layout="triangular",
            tube_count=100,
        )
    )
    inventory = tube_bundle_inventory(
        (
            TubeCondition(
                tube_id="authored-1",
                inner_diameter_m=0.016,
                reference_wall_m=0.002,
                minimum_wall_m=0.0015,
                plugged=False,
            ),
            TubeCondition(
                tube_id="authored-2",
                inner_diameter_m=0.016,
                reference_wall_m=0.002,
                minimum_wall_m=0.001,
                plugged=True,
            ),
        )
    )
    joint = elastic_joint_load(
        ElasticJointLoad(
            initial_bolt_force_N=10000.0,
            bolt_stiffness_N_m=1e8,
            clamped_stiffness_N_m=3e8,
            external_separating_force_N=1000.0,
            free_clamped_minus_bolt_expansion_m=1e-6,
            linear_contact_applicability_reviewed=True,
        )
    )
    envelope = FadEnvelope(
        envelope_id="authored-curve",
        revision="1",
        lr=(0.0, 0.5, 1.0),
        kr_limit=(1.0, 0.8, 0.0),
        material_geometry_load_basis="authored-basis",
        source_sha256="a" * 64,
        reviewed=True,
    )
    fad = evaluate_fad_envelope(
        FadPoint(
            point_id="authored-point",
            lr=0.3,
            kr=0.5,
            material_geometry_load_basis="authored-basis",
            provider_result_sha256="b" * 64,
            reviewed=True,
        ),
        envelope,
    )
    fs = evaluate_critical_plane_fs_life(
        CriticalPlaneFsLife(
            analysis_id="authored-fs",
            plane_id="plane-1",
            plane_factor_result_sha256="c" * 64,
            fatemi_socie_factor=0.004,
            shear_modulus_Pa=8e10,
            shear_fatigue_strength_coefficient_Pa=6e8,
            shear_fatigue_strength_exponent=-0.1,
            shear_fatigue_ductility_coefficient=0.3,
            shear_fatigue_ductility_exponent=-0.5,
            minimum_valid_cycles=1.0,
            maximum_valid_cycles=1e9,
            engineering_shear_amplitude_and_calibration_reviewed=True,
        )
    )
    print(
        json.dumps(
            dict(tube_geometry=geometry, tube_inventory=inventory, joint=joint, fad=fad, fs_life=fs), indent=2
        )
    )


if __name__ == "__main__":
    main()
