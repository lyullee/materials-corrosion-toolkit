import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.optimize import minimize_scalar
from scipy.special import logit

from matintegrity import evaluate
from matintegrity.contracts import RunContext

CONTEXT = RunContext(
    asset_id="synthetic", location_id="synthetic", time_basis="independent synthetic specimen trials"
)


def grouped_data():
    sizes = []
    hits = []
    for z, count in [(-2, 2), (0, 10), (2, 18)]:
        sizes.extend([0.001 * math.exp(z)] * 20)
        hits.extend([True] * count + [False] * (20 - count))
    return dict(
        specimen_ids=[f"specimen-{i}" for i in range(60)],
        flaw_size_m=sizes,
        detected=hits,
        query_sizes_m=[0.001 * math.exp(-2), 0.001, 0.001 * math.exp(2)],
        target_probability=0.9,
        confidence_level=0.95,
        maximum_threshold_size_m=0.1,
        independent_trials_declared=True,
    )


def test_pod_recovers_analytical_grouped_logits_and_profile_boundary():
    inputs = grouped_data()
    result = evaluate("inspection.hit_miss_pod", inputs, CONTEXT)
    assert result.status == "computed"
    v = result.values
    assert [p["probability"] for p in v["predictions"]] == pytest.approx([0.1, 0.5, 0.9], rel=1e-6)
    assert v["target_size_estimate_m"] == pytest.approx(0.001 * math.exp(2), rel=1e-6)
    upper = v["target_size_upper_confidence_m"]
    assert upper > v["target_size_estimate_m"]
    sizes = np.log(np.asarray(inputs["flaw_size_m"]))
    y = np.asarray(inputs["detected"], float)
    theta = float(logit(0.9))

    def independent_nll(slope):
        eta = theta + slope * (sizes - math.log(upper))
        return float(np.sum(np.logaddexp(0, eta) - y * eta))

    profile = minimize_scalar(independent_nll, bounds=(0, 20), method="bounded", options={"xatol": 1e-12})
    assert 2 * (profile.fun - v["negative_log_likelihood"]) == pytest.approx(
        v["likelihood_ratio_cutoff"], rel=1e-6
    )
    for p in v["predictions"]:
        assert 0 < p["pointwise_lower_confidence_probability"] < p["probability"]


def test_pod_size_scale_invariance():
    inputs = grouped_data()
    baseline = evaluate("inspection.hit_miss_pod", inputs, CONTEXT).values
    inputs["flaw_size_m"] = [1000 * v for v in inputs["flaw_size_m"]]
    inputs["query_sizes_m"] = [1000 * v for v in inputs["query_sizes_m"]]
    inputs["maximum_threshold_size_m"] *= 1000
    scaled = evaluate("inspection.hit_miss_pod", inputs, CONTEXT).values
    assert scaled["target_size_upper_confidence_m"] == pytest.approx(
        1000 * baseline["target_size_upper_confidence_m"], rel=1e-6
    )
    assert [p["pointwise_lower_confidence_probability"] for p in scaled["predictions"]] == pytest.approx(
        [p["pointwise_lower_confidence_probability"] for p in baseline["predictions"]], rel=1e-6
    )


def test_fitted_curve_parameters_and_inspection_update_preserve_meaning():
    fit = evaluate("inspection.hit_miss_pod", grouped_data(), CONTEXT).values
    for size, probability in zip(
        grouped_data()["query_sizes_m"], fit["probability_of_detection"], strict=True
    ):
        prediction = evaluate(
            "inspection.logistic_pod",
            dict(
                flaw_size_m=size,
                midpoint_size_m=fit["logistic_midpoint_size_m"],
                log_size_scale=fit["logistic_log_size_scale"],
            ),
            CONTEXT,
        )
        assert prediction.values["probability_of_detection"] == pytest.approx(probability)
    prior = np.array([0.2, 0.5, 0.3])
    likelihood = 1 - np.array(fit["probability_of_detection"])
    posterior = evaluate(
        "inspection.no_indication_update",
        dict(
            prior_weights=prior.tolist(),
            probabilities_of_detection=fit["probability_of_detection"],
            coverage_fraction=1.0,
        ),
        CONTEXT,
    )
    assert posterior.values["posterior_weights"] == pytest.approx(
        prior * likelihood / np.sum(prior * likelihood)
    )


def test_pod_rejects_separation_dependence_and_duplicate_specimens():
    inputs = grouped_data()
    inputs["detected"] = [False] * 20 + [True] * 40
    assert evaluate("inspection.hit_miss_pod", inputs, CONTEXT).status == "needs_data"
    inputs = grouped_data()
    inputs["independent_trials_declared"] = False
    assert evaluate("inspection.hit_miss_pod", inputs, CONTEXT).status == "needs_data"
    inputs = grouped_data()
    inputs["specimen_ids"][1] = inputs["specimen_ids"][0]
    with pytest.raises(ValidationError, match="unique"):
        evaluate("inspection.hit_miss_pod", inputs, CONTEXT)


def test_unbounded_threshold_does_not_become_a_finite_claim():
    inputs = grouped_data()
    inputs["maximum_threshold_size_m"] = 0.008
    v = evaluate("inspection.hit_miss_pod", inputs, CONTEXT).values
    assert v["target_size_upper_confidence_m"] is None
    assert v["upper_confidence_bound_status"] == "not_bounded_within_declared_search_domain"


def test_exact_binomial_extreme_counts_match_closed_forms():
    inputs = dict(
        opportunities=29,
        positive_responses=29,
        confidence_level=0.95,
        response_kind="detection_at_declared_size",
        independent_trials_declared=True,
    )
    v = evaluate("inspection.binomial_evidence", inputs, CONTEXT).values
    assert v["one_sided_lower_probability"] == pytest.approx(0.05 ** (1 / 29))
    inputs.update(positive_responses=0, response_kind="false_call_on_blank")
    v = evaluate("inspection.binomial_evidence", inputs, CONTEXT).values
    assert v["one_sided_upper_probability"] == pytest.approx(1 - 0.05 ** (1 / 29))
