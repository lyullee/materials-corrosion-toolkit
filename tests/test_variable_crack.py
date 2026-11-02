import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from matintegrity import evaluate
from matintegrity.contracts import RunContext

EXAMPLE = json.loads(
    (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
)["models"]["fracture.variable_paris"]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="ordered load blocks")


def test_constant_geometry_recovers_closed_form_depth_and_cycle_budget():
    v = evaluate("fracture.variable_paris", EXAMPLE, CONTEXT).values
    rate_factor = 1e-28 * (1.12 * 1e8 * math.sqrt(math.pi)) ** 3
    expected = (0.001**-0.5 - rate_factor * 10000 / 2) ** -2
    assert v["final_depth_m"] == pytest.approx(expected, rel=1e-8)
    assert v["cycles_evaluated"] == 10000
    assert abs(v["block_results"][0]["cycle_inversion_residual"]) < 0.001


def test_geometry_table_matches_independent_forward_ode_across_a_knot():
    x = copy.deepcopy(EXAMPLE)
    x["geometry_depth_m"] = [0.0005, 0.00105, 0.005]
    x["geometry_factor"] = [1.0, 1.1, 1.5]
    x["blocks"][0]["cycles"] = 5000.0
    result = evaluate("fracture.variable_paris", x, CONTEXT)

    def derivative(_, state):
        a = state[0]
        y = np.interp(a, x["geometry_depth_m"], x["geometry_factor"])
        return [1e-28 * (y * 1e8 * math.sqrt(math.pi * a)) ** 3]

    independent = solve_ivp(derivative, (0, 5000), [0.001], rtol=1e-10, atol=1e-14, max_step=5)
    assert result.values["final_depth_m"] > 0.00105
    assert result.values["final_depth_m"] == pytest.approx(independent.y[0, -1], rel=1e-7)


@pytest.mark.parametrize("termination", ["calibration", "toughness"])
def test_domain_and_toughness_limits_have_distinct_termination_semantics(termination):
    x = copy.deepcopy(EXAMPLE)
    x["blocks"][0]["cycles"] = 1e6
    limit = 1.12 * 1e8 * math.sqrt(math.pi * 0.002)
    if termination == "calibration":
        x["maximum_calibrated_delta_K_Pa_sqrt_m"] = limit
    else:
        x["fracture_toughness_Pa_sqrt_m"] = limit
    result = evaluate("fracture.variable_paris", x, CONTEXT)
    assert result.values["final_depth_m"] == pytest.approx(0.002, rel=1e-8)
    assert result.status == ("out_of_scope" if termination == "calibration" else "computed")
    assert result.values["termination_reason"] == (
        "growth_calibration_limit_reached" if termination == "calibration" else "toughness_limit_reached"
    )


def test_threshold_does_not_invent_growth_and_geometry_extrapolation_is_rejected():
    x = copy.deepcopy(EXAMPLE)
    x["threshold_delta_K_Pa_sqrt_m"] = 1e7
    result = evaluate("fracture.variable_paris", x, CONTEXT)
    assert result.values["final_depth_m"] == 0.001
    assert result.values["cycles_evaluated"] == 10000
    x["terminal_depth_m"] = 0.006
    with pytest.raises(ValueError, match="geometry table"):
        evaluate("fracture.variable_paris", x, CONTEXT)


def test_late_high_mean_peak_can_fail_after_prior_growth_but_not_before():
    x = copy.deepcopy(EXAMPLE)
    factor = 1e-28 * (1.12 * 1e8 * math.sqrt(math.pi)) ** 3
    growth_cycles = 2 * (0.001**-0.5 - 0.002**-0.5) / factor
    peak = 50e6 / (1.12 * math.sqrt(math.pi * 0.0015))
    growth = dict(minimum_stress_Pa=0.0, maximum_stress_Pa=1e8, cycles=growth_cycles)
    peak_block = dict(minimum_stress_Pa=peak - 1000.0, maximum_stress_Pa=peak, cycles=1.0)
    x["threshold_delta_K_Pa_sqrt_m"] = 1e5
    x["blocks"] = [growth, peak_block]
    late = evaluate("fracture.variable_paris", x, CONTEXT)
    x["blocks"] = [peak_block, growth]
    early = evaluate("fracture.variable_paris", x, CONTEXT)
    assert late.values["termination_reason"] == "toughness_limit_reached"
    assert early.values["termination_reason"] == "requested_blocks_completed"


def test_insufficient_depth_root_resolution_does_not_pass_numerical_checks():
    inputs = copy.deepcopy(EXAMPLE)
    inputs["absolute_depth_tolerance_m"] = 0.001
    with pytest.raises(RuntimeError, match="root resolution"):
        evaluate("fracture.variable_paris", inputs, CONTEXT)
