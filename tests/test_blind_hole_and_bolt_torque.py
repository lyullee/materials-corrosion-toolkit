import json
import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    BlindIndicatorHoleLigament,
    BoltReferenceTorqueScaling,
    FrictionResolvedBoltTorque,
    blind_indicator_hole_ligament,
    bolt_reference_torque_scaling,
    friction_resolved_bolt_torque,
)
from matintegrity.registry import default_registry


def bind(contract, values):
    digest = canonical_digest(contract.model_construct(**values).model_dump(mode="json", exclude={"basis"}))
    basis = {
        "source_id": "authored",
        "revision": "1",
        "license_id": "authored-test",
        "record_sha256": digest,
        "applicability_and_units_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [
            {
                "source_id": "authored",
                "origin": "synthetic",
                "citation": "authored geometry and coefficients",
                "license_id": "authored-test",
                "sha256": digest,
            }
        ],
    }
    return contract.model_validate_json(json.dumps(values | {"basis": basis}))


def hole(**updates):
    return bind(
        BlindIndicatorHoleLigament,
        {
            "component_id": "shell",
            "physical_location_id": "station",
            "hole_id": "indicator",
            "local_wall_thickness_m": 0.01,
            "drilled_depth_m": 0.008,
            "reference_required_wall_m": 0.005,
            "same_location_depth_direction_and_blind_hole_role_reviewed": True,
        }
        | updates,
    )


def torque(**updates):
    return bind(
        FrictionResolvedBoltTorque,
        {
            "bolt_id": "bolt",
            "target_preload_N": 1000.0,
            "mean_bearing_diameter_m": 0.02,
            "thread_pitch_diameter_m": 0.01,
            "lead_m_per_turn": math.pi * 0.001,
            "thread_half_angle_rad": 0.0,
            "bearing_friction_coefficient": 0.1,
            "thread_friction_coefficient": 0.2,
        }
        | updates,
    )


def scaling(**updates):
    return bind(
        BoltReferenceTorqueScaling,
        {
            "bolt_id": "bolt",
            "common_geometry_thread_bearing_and_lubrication_condition_id": "condition",
            "reference_record_digest": "c" * 64,
            "reference_torque_N_m": 100.0,
            "reference_tensile_stress_Pa": 1e8,
            "target_tensile_stress_Pa": 1.5e8,
            "unchanged_geometry_and_friction_conditions_reviewed": True,
        }
        | updates,
    )


@pytest.mark.parametrize("stress,expected", [(0.0, 0.0), (0.5e8, 50.0), (1.5e8, 150.0)])
def test_reference_torque_stress_scaling(stress, expected):
    result = bolt_reference_torque_scaling(scaling(target_tensile_stress_Pa=stress))
    assert result.status == "computed"
    assert result.values["target_torque_N_m"] == expected


def test_scaling_requires_unchanged_friction_and_finite_ratio():
    assert (
        bolt_reference_torque_scaling(
            scaling(unchanged_geometry_and_friction_conditions_reviewed=False)
        ).status
        == "needs_data"
    )
    assert bolt_reference_torque_scaling(scaling(reference_tensile_stress_Pa=1e-300)).status == "out_of_scope"


def test_hole_wall_depth_and_reference_are_distinct():
    result = blind_indicator_hole_ligament(hole())
    assert result.status == "computed"
    assert result.values["remaining_ligament_m"] == pytest.approx(0.002)
    assert result.values["remaining_wall_fraction"] == pytest.approx(0.2)
    assert result.values["depth_to_reference_required_wall_ratio"] == pytest.approx(1.6)


@pytest.mark.parametrize("depth,remaining", [(0.01, 0.0), (0.02, -0.01)])
def test_through_and_overdepth_are_outside_blind_hole_scope(depth, remaining):
    result = blind_indicator_hole_ligament(hole(drilled_depth_m=depth))
    assert result.status == "out_of_scope"
    assert result.values["remaining_ligament_m"] == remaining
    assert not result.values["positive_blind_ligament_present"]


def test_hole_requires_role_review_and_checks_ratio_range():
    assert (
        blind_indicator_hole_ligament(
            hole(same_location_depth_direction_and_blind_hole_role_reviewed=False)
        ).status
        == "needs_data"
    )
    assert blind_indicator_hole_ligament(hole(reference_required_wall_m=1e-320)).status == "out_of_scope"


def test_square_thread_and_bearing_torque_are_resolved_separately():
    result = friction_resolved_bolt_torque(torque())
    assert result.status == "computed"
    assert result.values["bearing_friction_torque_N_m"] == 1.0
    assert result.values["thread_raising_torque_N_m"] == pytest.approx(5.0 * 0.3 / 0.98)
    assert result.values["target_torque_N_m"] == pytest.approx(1.0 + 5.0 * 0.3 / 0.98)


def test_profile_half_angle_matches_independent_effective_friction_angle():
    value = torque(thread_half_angle_rad=0.5)
    result = friction_resolved_bolt_torque(value)
    lead_angle = math.atan(value.lead_m_per_turn / (math.pi * value.thread_pitch_diameter_m))
    friction_angle = math.atan(value.thread_friction_coefficient / math.cos(value.thread_half_angle_rad))
    expected_thread = (
        value.target_preload_N * value.thread_pitch_diameter_m / 2 * math.tan(lead_angle + friction_angle)
    )
    assert result.values["thread_raising_torque_N_m"] == pytest.approx(expected_thread)


@pytest.mark.parametrize("lead_multiplier", [1.0, 2.0, 3.0])
def test_frictionless_thread_work_per_turn_matches_axial_work(lead_multiplier):
    value = torque(
        lead_m_per_turn=0.002 * lead_multiplier,
        thread_half_angle_rad=0.4,
        bearing_friction_coefficient=0.0,
        thread_friction_coefficient=0.0,
    )
    result = friction_resolved_bolt_torque(value)
    assert result.values["target_torque_N_m"] * 2.0 * math.pi == pytest.approx(
        value.target_preload_N * value.lead_m_per_turn
    )


def test_nonpositive_denominator_and_nonfinite_torque_are_out_of_scope():
    assert (
        friction_resolved_bolt_torque(
            torque(lead_m_per_turn=math.pi * 0.01, thread_friction_coefficient=2.0)
        ).status
        == "out_of_scope"
    )
    result = friction_resolved_bolt_torque(torque(target_preload_N=1e308, mean_bearing_diameter_m=1e308))
    assert result.status == "out_of_scope"
    json.dumps(result.values, allow_nan=False)


def test_zero_preload_and_invalid_profile_angle():
    assert friction_resolved_bolt_torque(torque(target_preload_N=0.0)).values["target_torque_N_m"] == 0.0
    with pytest.raises(ValueError):
        torque(thread_half_angle_rad=math.pi / 2)


@pytest.mark.parametrize(
    "model_id,factory",
    [
        ("inspection.blind_indicator_hole_ligament", hole),
        ("fabrication.friction_resolved_bolt_torque", torque),
        ("fabrication.bolt_reference_torque_scaling", scaling),
    ],
)
def test_default_registry_python_json_exchange(model_id, factory):
    registry = default_registry()
    value = factory()
    context = RunContext(asset_id="asset", location_id="station", time_basis="synthetic")
    direct = registry.run(model_id, value, context)
    assert direct.status == "computed"
    assert direct.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
