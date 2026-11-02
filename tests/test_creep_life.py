import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.optimize import minimize
from scipy.stats import norm

from matintegrity.adapters import probability_event
from matintegrity.contracts import RunContext
from matintegrity.models.creep import CreepLifeFit, _design, _likelihood
from matintegrity.registry import default_registry

EXAMPLES = json.loads(
    (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
)["models"]
CTX = RunContext(asset_id="synthetic", location_id="gauge", time_basis="fresh-material age in seconds")


def run(model, inputs):
    return default_registry().run_json(model, json.dumps(inputs), CTX)


def test_complete_life_fit_matches_closed_form_normal_regression():
    x = copy.deepcopy(EXAMPLES["creep.lognormal_life_fit"])
    result = run("creep.lognormal_life_fit", x)
    assert result.status == "computed"
    m = result.values["model"]
    design = np.column_stack(
        [
            np.ones(len(x["initial_stress_Pa"])),
            -np.log(np.array(x["initial_stress_Pa"]) / m["reference_stress_Pa"]),
        ]
    )
    y = np.log(x["endpoint_time_s"])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    sigma = np.sqrt(np.mean((y - design @ beta) ** 2))
    assert m["stress_exponent"] == pytest.approx(beta[1], rel=1e-7)
    assert m["log_reference_median_time_s"] == pytest.approx(beta[0], rel=1e-8)
    assert m["log_life_sigma"] == pytest.approx(sigma, rel=1e-7)
    assert m["activation_energy_J_mol"] is None
    assert result.values["negative_log_likelihood_seconds"] == pytest.approx(
        float((-norm.logpdf(y, design @ beta, sigma) + y).sum())
    )


def test_right_censored_fit_matches_independent_derivative_free_likelihood():
    x = copy.deepcopy(EXAMPLES["creep.lognormal_life_fit"])
    x["right_censored"] = [i % 4 == 3 for i in range(16)]
    # Administrative censoring at an earlier time than this synthetic failure.
    x["endpoint_time_s"] = [
        t * 0.85 if c else t for t, c in zip(x["endpoint_time_s"], x["right_censored"], strict=True)
    ]
    result = run("creep.lognormal_life_fit", x)
    assert result.status == "computed"
    m = result.values["model"]
    stress = np.log(np.array(x["initial_stress_Pa"]) / 1.5e8)
    y = np.log(x["endpoint_time_s"])
    censored = np.array(x["right_censored"])

    def objective(theta):
        mu = theta[0] - theta[1] * stress
        return -np.where(
            censored, norm.logsf(y, mu, np.exp(theta[2])), norm.logpdf(y, mu, np.exp(theta[2]))
        ).sum()

    alt = minimize(
        objective,
        [math.log(1e6), 4, -1.5],
        method="Nelder-Mead",
        options={"xatol": 1e-10, "fatol": 1e-10, "maxiter": 5000},
    )
    assert alt.success
    assert m["stress_exponent"] == pytest.approx(alt.x[1], rel=1e-5)
    assert result.values["right_censored"] == 4
    assert result.values["negative_log_likelihood_seconds"] == pytest.approx(
        float(alt.fun + y[~censored].sum()), abs=1e-7
    )


def test_censored_analytic_gradient_against_independent_finite_difference():
    d = _design([1e8, 1e8, 2e8, 2e8, 3e8, 3e8], [900, 1100] * 3, 1e8, 1000, "arrhenius_stress")
    y = np.log([1000, 50, 100, 10, 20, 3])
    theta = np.array([6.0, 3.0, 2.0, -0.5])
    censor = np.array([True, False, False, True, False, True])
    value, gradient = _likelihood(theta, d, y, censor)
    assert np.isfinite(value)
    fd = []
    for i in range(4):
        h = np.zeros(4)
        h[i] = 1e-5
        fd.append((_likelihood(theta + h, d, y, censor)[0] - _likelihood(theta - h, d, y, censor)[0]) / 2e-5)
    np.testing.assert_allclose(gradient, fd, rtol=1e-7, atol=1e-7)


def test_arrhenius_stress_fit_recovers_identifiable_two_factor_law():
    x = copy.deepcopy(EXAMPLES["creep.lognormal_life_fit"])
    conditions = [
        (s, t, e) for s in [1e8, 2e8, 3e8] for t in [900.0, 1000.0, 1100.0] for e in [-0.2, -0.07, 0.07, 0.2]
    ]
    x.update(
        family="arrhenius_stress",
        specimen_id=[f"s{i}" for i in range(len(conditions))],
        initial_stress_Pa=[s for s, t, e in conditions],
        temperature_K=[t for s, t, e in conditions],
        endpoint_time_s=[
            math.exp(
                math.log(1e6) - 4 * math.log(s / 2e8) + 200000 / 8.31446261815324 * (1 / t - 1 / 1000) + e
            )
            for s, t, e in conditions
        ],
        right_censored=[False] * len(conditions),
    )
    result = run("creep.lognormal_life_fit", x)
    assert result.status == "computed"
    assert result.values["model"]["activation_energy_J_mol"] == pytest.approx(200000, rel=1e-6)
    assert result.values["model"]["stress_exponent"] == pytest.approx(4, rel=1e-6)
    x["temperature_K"] = [1000.0] * len(conditions)
    assert run("creep.lognormal_life_fit", x).status == "needs_data"


def test_single_temperature_and_specimen_identity_guards():
    x = copy.deepcopy(EXAMPLES["creep.lognormal_life_fit"])
    x["independent_specimens_confirmed"] = False
    assert run("creep.lognormal_life_fit", x).status == "needs_data"
    x["independent_specimens_confirmed"] = True
    x["temperature_K"][0] = 1005.0
    assert run("creep.lognormal_life_fit", x).status == "needs_data"
    x["specimen_id"][1] = x["specimen_id"][0]
    with pytest.raises(ValidationError, match="unique"):
        CreepLifeFit.model_validate_json(json.dumps(x))


def test_prediction_matches_lognormal_and_survival_interval_composition():
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x.update(current_age_s=0.0, horizon_s=1e6)
    full = run("creep.conditional_life", x)
    assert full.status == "computed"
    assert full.values["probability_given_survival"] == pytest.approx(0.5, abs=1e-7)
    x["horizon_s"] = 5e5
    first = run("creep.conditional_life", x).values["probability_given_survival"]
    x["current_age_s"] = 5e5
    second = run("creep.conditional_life", x).values["probability_given_survival"]
    assert 1 - (1 - first) * (1 - second) == pytest.approx(
        full.values["probability_given_survival"], abs=1e-12
    )


def test_tiny_future_interval_preserves_hazard_limit_and_event_clock():
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x.update(current_age_s=1e6, horizon_s=1e-12)
    result = run("creep.conditional_life", x)
    sigma = x["model"]["log_life_sigma"]
    z = (math.log(1e6) - result.values["log_median_life_s"]) / sigma
    expected = norm.pdf(z) / norm.sf(z) / sigma * 1e-18
    assert result.values["probability_given_survival"] == pytest.approx(expected, rel=1e-10, abs=0)
    # An interval below representable age resolution must not turn into a zero-length event.
    with pytest.raises(ValueError):
        probability_event(
            result,
            event_id="e",
            physical_scope_id="g",
            failure_mode="creep",
            horizon_start_s=1e6,
            horizon_end_s=1e6 + 1e-12,
            conditioning="survived",
        )
    x["horizon_s"] = 10.0
    result = run("creep.conditional_life", x)
    with pytest.raises(ValueError, match="horizon"):
        probability_event(
            result,
            event_id="e",
            physical_scope_id="g",
            failure_mode="creep",
            horizon_start_s=0.0,
            horizon_end_s=10.0,
            conditioning="survived",
        )


def test_prediction_refuses_extrapolation_and_unreviewed_conditions():
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x["temperature_basis"] = "measured_representative"
    assert run("creep.conditional_life", x).status == "needs_data"
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x["initial_stress_Pa"] = 3e8
    assert run("creep.conditional_life", x).status == "out_of_scope"
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x["temperature_K"] = 1001.0
    assert run("creep.conditional_life", x).status == "out_of_scope"
    x["applicability_reviewed"] = False
    assert run("creep.conditional_life", x).status == "needs_data"
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x["horizon_s"] = x["model"]["longest_observed_failure_time_s"] * 2
    assert run("creep.conditional_life", x).status == "out_of_scope"


def test_temperature_stress_support_uses_joint_hull():
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x["model"].update(
        family="arrhenius_stress",
        activation_energy_J_mol=100000.0,
        support_stress_Pa=[1e8, 2e8, 1e8],
        support_temperature_K=[900.0, 900.0, 1100.0],
    )
    x.update(initial_stress_Pa=2e8, temperature_K=1100.0)
    assert run("creep.conditional_life", x).status == "out_of_scope"
    x.update(initial_stress_Pa=1e8, temperature_K=1000.0)
    assert run("creep.conditional_life", x).status == "computed"


def test_all_censored_and_degenerate_scatter_do_not_fabricate_fit():
    x = copy.deepcopy(EXAMPLES["creep.lognormal_life_fit"])
    x["right_censored"] = [True] * 16
    assert run("creep.lognormal_life_fit", x).status == "needs_data"
    x["right_censored"] = [False] * 16
    x["endpoint_time_s"] = [1e6 * (s / 1.5e8) ** -4 for s in x["initial_stress_Pa"]]
    assert run("creep.lognormal_life_fit", x).status == "needs_data"


def test_extreme_survival_tail_and_time_support_keep_distinct_meanings():
    x = copy.deepcopy(EXAMPLES["creep.conditional_life"])
    x.update(current_age_s=1e6, horizon_s=1.0)
    m = x["model"]
    m["log_life_sigma"] = 0.2
    m["log_reference_median_time_s"] = (
        math.log(1e6) + m["stress_exponent"] * math.log(x["initial_stress_Pa"] / m["reference_stress_Pa"]) - 8
    )
    result = run("creep.conditional_life", x)
    assert result.status == "computed"
    assert result.values["probability_given_survival"] == pytest.approx(
        1 - math.exp(norm.logsf(40 + math.log1p(1e-6) / 0.2) - norm.logsf(40)), rel=1e-8
    )
    m["log_reference_median_time_s"] = 100.0
    result = run("creep.conditional_life", x)
    assert result.values["median_life_s"] is None
    assert result.values["median_beyond_declared_time_support"]
    m["log_reference_median_time_s"] = -1000.0
    assert run("creep.conditional_life", x).status == "out_of_scope"
