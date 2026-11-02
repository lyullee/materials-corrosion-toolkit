import copy
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.integrate import quad

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

INPUT = json.loads(
    (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
)["models"]["structural.profile_capacity"]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="one static profile")


def run(inputs):
    return default_registry().run_json("structural.profile_capacity", json.dumps(inputs), CONTEXT)


def test_profile_scan_matches_independent_all_window_quadrature():
    result = run(INPUT)
    assert result.status == "computed"
    assert result.values["pressure_basis"] == "internal_minus_external"
    x = np.array(INPUT["axial_position_m"])
    t = np.array(INPUT["measured_remaining_thickness_m"])
    reference = INPUT["reference_wall_thickness_m"]
    expected = []
    for i in range(len(x) - 1):
        for j in range(i + 1, len(x)):
            loss = quad(
                lambda position: reference - float(np.interp(position, x, t)),
                x[i],
                x[j],
                points=x[i + 1 : j],
                epsabs=1e-14,
            )[0]
            alpha = loss / (reference * (x[j] - x[i]))
            m = np.interp(
                x[j] - x[i], INPUT["bulging_table"]["window_length_m"], INPUT["bulging_table"]["factor"]
            )
            expected.append(((1 - alpha) / (1 - alpha / m), i, j))
    ratio, i, j = min(expected)
    assert result.values["capacity_reduction_factor"] == pytest.approx(ratio)
    assert result.values["critical_window"]["start_index"] == i
    assert result.values["critical_window"]["end_index"] == j
    assert result.values["scanned_nodal_windows"] == 10


def test_intact_uniform_loss_and_unit_bulging_limits():
    inputs = copy.deepcopy(INPUT)
    inputs["measured_remaining_thickness_m"] = [0.01] * 5
    assert run(inputs).values["capacity_reduction_factor"] == 1
    inputs["measured_remaining_thickness_m"] = [0.006] * 5
    result = run(inputs)
    assert result.values["capacity_reduction_factor"] == pytest.approx(0.6 / (1 - 0.4 / 2.5))
    assert result.values["critical_window"]["length_m"] == 0.8
    inputs["bulging_table"]["factor"] = [1.0] * 3
    assert run(inputs).values["capacity_reduction_factor"] == pytest.approx(1)


def test_local_window_can_control_in_a_long_mostly_intact_profile():
    inputs = copy.deepcopy(INPUT)
    inputs["axial_position_m"] = [0.0, 3.6, 3.8, 4.0, 4.2, 4.4, 8.0]
    inputs["measured_remaining_thickness_m"] = [0.01, 0.01, 0.007, 0.005, 0.007, 0.01, 0.01]
    inputs["bulging_table"]["window_length_m"] = [0.0, 0.4, 0.8, 8.0]
    inputs["bulging_table"]["factor"] = [1.0, 1.5, 2.5, 3.0]
    result = run(inputs)
    assert result.values["critical_window"]["length_m"] < 1
    assert result.values["capacity_reduction_factor"] < 0.9


def test_nested_spatial_refinement_and_length_unit_scaling():
    base = run(INPUT)
    refined = copy.deepcopy(INPUT)
    old = np.array(refined["axial_position_m"])
    nodes = np.sort(np.r_[old, (old[:-1] + old[1:]) / 2])
    refined["measured_remaining_thickness_m"] = np.interp(
        nodes, old, refined["measured_remaining_thickness_m"]
    ).tolist()
    refined["axial_position_m"] = nodes.tolist()
    assert (
        run(refined).values["capacity_reduction_factor"] <= base.values["capacity_reduction_factor"] + 1e-12
    )
    scaled = copy.deepcopy(INPUT)
    for key in ["axial_position_m", "measured_remaining_thickness_m"]:
        scaled[key] = [v * 1000 for v in scaled[key]]
    scaled["reference_wall_thickness_m"] *= 1000
    scaled["bulging_table"]["window_length_m"] = [
        v * 1000 for v in scaled["bulging_table"]["window_length_m"]
    ]
    result = run(scaled)
    assert result.values["declared_model_pressure_difference_capacity_Pa"] == pytest.approx(
        base.values["declared_model_pressure_difference_capacity_Pa"]
    )
    assert result.values["critical_window"]["projected_loss_area_m2"] == pytest.approx(
        base.values["critical_window"]["projected_loss_area_m2"] * 1e6
    )


@pytest.mark.parametrize(
    "flag",
    [
        "full_axial_extent_confirmed",
        "blunt_metal_loss_confirmed",
        "internal_pressure_dominant_confirmed",
        "provider_applicability_reviewed",
    ],
)
def test_incomplete_applicability_is_not_a_completed_capacity(flag):
    inputs = copy.deepcopy(INPUT)
    inputs[flag] = False
    assert run(inputs).status == "needs_data"


def test_identity_ranges_zero_ligament_and_apparent_thickening_propagate():
    inputs = copy.deepcopy(INPUT)
    inputs["bulging_table"]["geometry_id"] = "other"
    assert run(inputs).status == "needs_data"
    inputs = copy.deepcopy(INPUT)
    inputs["bulging_table"]["window_length_m"][-1] = 0.7
    assert run(inputs).status == "out_of_scope"
    inputs = copy.deepcopy(INPUT)
    inputs["maximum_supported_depth_fraction"] = 0.4
    assert run(inputs).status == "out_of_scope"
    inputs = copy.deepcopy(INPUT)
    inputs["measured_remaining_thickness_m"][2] = 0.0
    result = run(inputs)
    assert result.status == "out_of_scope" and not result.values
    inputs = copy.deepcopy(INPUT)
    inputs["measured_remaining_thickness_m"][0] = 0.011
    assert run(inputs).status == "needs_data"


def test_provider_license_and_monotonicity_are_explicit():
    inputs = copy.deepcopy(INPUT)
    inputs["bulging_table"]["evidence"][0]["license_id"] = None
    with pytest.raises(ValidationError, match="license"):
        run(inputs)
    inputs = copy.deepcopy(INPUT)
    inputs["bulging_table"]["factor"] = [1.0, 2.0, 1.5]
    with pytest.raises(ValidationError, match="nondecreasing"):
        run(inputs)
