import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.stats import genextreme

from matintegrity import evaluate
from matintegrity.contracts import RunContext

ROOT = Path(__file__).resolve().parents[1]
INPUT = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
    "corrosion.gumbel_area_maximum"
]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="one synthetic exposure")


def run(inputs):
    return evaluate("corrosion.gumbel_area_maximum", inputs, CONTEXT)


@pytest.fixture(scope="module")
def fitted():
    return run(INPUT)


def test_gumbel_fit_matches_independent_mle_score_and_area_cdf(fitted):
    assert fitted.status == "computed"
    v = fitted.values
    mu, beta = v["fitted_block_location_m"], v["fitted_block_scale_m"]
    depths = np.array(INPUT["maximum_depth_m"])
    weights = np.exp(-(depths - depths.min()) / beta)
    assert (depths.mean() - np.dot(depths, weights) / weights.sum()) / beta == pytest.approx(1, abs=2e-7)
    assert np.exp(-(depths - mu) / beta).mean() == pytest.approx(1, abs=2e-7)
    assert mu == pytest.approx(0.002, rel=0.01)
    assert beta == pytest.approx(0.0002, rel=0.05)
    block_cdf = math.exp(-math.exp(-(INPUT["depth_threshold_m"] - mu) / beta))
    assert v["area_depth_exceedance_probability"] == pytest.approx(1 - block_cdf**400)
    quantile = v["target_maximum_depth_quantile_m"]
    assert math.exp(-400 * math.exp(-(quantile - mu) / beta)) == pytest.approx(0.95)
    assert v["observed_area_m2"] == pytest.approx(0.004)
    assert v["target_area_m2"] == pytest.approx(0.04)


@pytest.mark.parametrize("factor", [1000.0, 1e200])
def test_area_shift_unit_scaling_seeded_intervals_and_one_block(fitted, factor):
    scaled = copy.deepcopy(INPUT)
    scaled["maximum_depth_m"] = [v * factor for v in scaled["maximum_depth_m"]]
    scaled["depth_threshold_m"] *= factor
    actual = run(scaled).values
    assert actual["area_depth_exceedance_probability"] == pytest.approx(
        fitted.values["area_depth_exceedance_probability"], abs=1e-10
    )
    assert np.array(actual["depth_quantile_parameter_interval_m"]) / factor == pytest.approx(
        fitted.values["depth_quantile_parameter_interval_m"], abs=1e-10
    )
    single = copy.deepcopy(INPUT)
    single["target_block_count"] = 1
    one = run(single).values
    assert fitted.values["target_maximum_depth_quantile_m"] - one[
        "target_maximum_depth_quantile_m"
    ] == pytest.approx(fitted.values["fitted_block_scale_m"] * math.log(400))
    assert fitted.values["area_depth_exceedance_probability"] > one["area_depth_exceedance_probability"]


@pytest.mark.parametrize(
    "flag",
    [
        "independent_equivalent_blocks",
        "same_exposure_and_surface_population",
        "complete_uncensored_block_maxima",
    ],
)
def test_sampling_assumptions_must_be_explicit(flag):
    inputs = copy.deepcopy(INPUT)
    inputs[flag] = False
    assert run(inputs).status == "needs_data"
    inputs = copy.deepcopy(INPUT)
    inputs["block_ids"][1] = inputs["block_ids"][0]
    with pytest.raises(ValidationError):
        run(inputs)


def test_constant_area_bound_and_negative_support_are_not_silent_success():
    inputs = copy.deepcopy(INPUT)
    inputs["maximum_depth_m"] = [0.001] * 40
    assert run(inputs).status == "needs_data"
    inputs = copy.deepcopy(INPUT)
    inputs["target_block_count"] = 401
    assert run(inputs).status == "out_of_scope"
    inputs = copy.deepcopy(INPUT)
    inputs["maximum_negative_depth_probability"] = 0.0
    inputs["maximum_depth_m"] = [d - min(INPUT["maximum_depth_m"]) for d in INPUT["maximum_depth_m"]]
    result = run(inputs)
    assert result.status == "needs_data"
    assert result.values["fitted_negative_block_depth_probability"] > 0
    inputs = copy.deepcopy(INPUT)
    inputs["block_area_m2"] = 1e308
    assert run(inputs).status == "out_of_scope"


def test_refitted_diagnostic_rejects_two_concentrated_populations():
    inputs = copy.deepcopy(INPUT)
    inputs["maximum_depth_m"] = [0.001] * 20 + [0.003] * 20
    inputs["minimum_goodness_of_fit_pvalue"] = 0.05
    result = run(inputs)
    assert result.status == "needs_data"
    assert result.values["refitted_parametric_gof_pvalue"] < 0.05


def test_exceedance_extreme_tail_avoids_probability_cancellation(fitted):
    inputs = copy.deepcopy(INPUT)
    inputs["depth_threshold_m"] = (
        fitted.values["fitted_block_location_m"] + 50 * fitted.values["fitted_block_scale_m"]
    )
    result = run(inputs)
    assert result.status == "computed"
    assert 0 < result.values["area_depth_exceedance_probability"] < 1e-15
    assert result.values["area_depth_exceedance_probability"] == pytest.approx(
        400 * math.exp(-50), rel=1e-8, abs=0
    )


def test_gev_fit_uses_max_stability_for_area_quantile_and_exceedance():
    inputs = copy.deepcopy(INPUT)
    rng = np.random.default_rng(8675309)
    depths = genextreme.rvs(-0.12, loc=0.002, scale=0.0002, size=80, random_state=rng)
    inputs["block_ids"] = [f"gev-block-{index}" for index in range(len(depths))]
    inputs["maximum_depth_m"] = depths.tolist()
    inputs["extreme_value_family"] = "gev"
    inputs["target_block_count"] = 25
    inputs["minimum_goodness_of_fit_pvalue"] = 0.0
    inputs["maximum_negative_depth_probability"] = 1.0
    result = run(inputs)

    assert result.status == "computed"
    assert result.values["extreme_value_family"] == "gev"
    assert result.values["fitted_shape_parameter_scipy"] != 0.0
    threshold = (inputs["depth_threshold_m"] - depths.mean()) / depths.std()
    fitted = genextreme.fit((depths - depths.mean()) / depths.std())
    expected_probability = 1 - genextreme.cdf(threshold, *fitted) ** inputs["target_block_count"]
    expected_quantile = depths.mean() + depths.std() * genextreme.ppf(
        inputs["quantile_probability"] ** (1 / inputs["target_block_count"]), *fitted
    )
    assert result.values["area_depth_exceedance_probability"] == pytest.approx(expected_probability, rel=1e-9)
    assert result.values["target_maximum_depth_quantile_m"] == pytest.approx(expected_quantile, rel=1e-9)
    assert run(inputs).values == result.values


def test_unknown_extreme_value_family_is_rejected():
    inputs = copy.deepcopy(INPUT)
    inputs["extreme_value_family"] = "frechet"
    with pytest.raises(ValidationError):
        run(inputs)
