import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.sobol_replicate_stability import (
    SobolReplicateStabilityAssessment,
    sobol_replicate_stability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def replicate(identifier, seed, first_a, total_a, first_b, total_b, **updates):
    value = {
        "replicate_id": identifier,
        "seed": seed,
        "output_id": "output-1",
        "output_definition": "caller scalar response",
        "output_unit_token": "custom-output-unit",
        "parameter_distribution_id": "distribution-1",
        "distribution_digest": DIGEST_A,
        "dependence_assumption_id": "caller-independent-marginals",
        "design_family_id": "sobol-design-family-1",
        "design_family_digest": DIGEST_B,
        "evaluator_id": "evaluator-1",
        "evaluator_revision": "revision-1",
        "evaluator_configuration_digest": DIGEST_C,
        "sample_count": 100,
        "effective_sample_size": 80.0,
        "parameter_estimates": (
            {
                "parameter_id": "parameter-a",
                "first_order_index": first_a,
                "total_order_index": total_a,
                "first_order_estimator_uncertainty": 0.02,
                "total_order_estimator_uncertainty": 0.025,
                "uncertainty_definition": "caller standard error",
            },
            {
                "parameter_id": "parameter-b",
                "first_order_index": first_b,
                "total_order_index": total_b,
                "first_order_estimator_uncertainty": 0.015,
                "total_order_estimator_uncertainty": 0.02,
                "uncertainty_definition": "caller standard error",
            },
        ),
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def stable_replicates():
    return (
        replicate("replicate-1", 101, 0.70, 0.80, 0.20, 0.30),
        replicate("replicate-2", 102, 0.71, 0.81, 0.21, 0.31),
        replicate("replicate-3", 103, 0.69, 0.79, 0.19, 0.29),
    )


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "output_id": "output-1",
        "output_definition": "caller scalar response",
        "output_unit_token": "custom-output-unit",
        "parameter_ids": ("parameter-a", "parameter-b"),
        "parameter_distribution_id": "distribution-1",
        "distribution_digest": DIGEST_A,
        "dependence_assumption_id": "caller-independent-marginals",
        "design_family_id": "sobol-design-family-1",
        "design_family_digest": DIGEST_B,
        "evaluator_id": "evaluator-1",
        "evaluator_revision": "revision-1",
        "evaluator_configuration_digest": DIGEST_C,
        "replicates": stable_replicates(),
        "minimum_replicate_count": 3,
        "maximum_first_order_replicate_range": 0.05,
        "maximum_total_order_replicate_range": 0.05,
        "maximum_pooled_sample_standard_deviation": 0.02,
        "maximum_reported_estimator_uncertainty": 0.03,
        "rank_tie_tolerance": 0.01,
        "output_parameter_distribution_and_dependence_identity_reviewed": True,
        "design_family_and_evaluator_identity_reviewed": True,
        "replicate_independence_ids_and_seeds_reviewed": True,
        "complete_parameter_sets_reviewed": True,
        "estimator_uncertainty_ess_and_sample_counts_reviewed": True,
        "result_digests_and_missingness_reviewed": True,
        "diagnostic_tolerances_and_rank_definition_reviewed": True,
    }
    value.update(updates)
    return SobolReplicateStabilityAssessment(**value)


def test_stable_replicates_have_pooled_dispersion_and_order_diagnostics():
    result = sobol_replicate_stability(payload())
    assert result.status == "computed"
    assert result.values["rank_order_stable_at_declared_tie_tolerance"] is True
    assert result.values["dispersion_criteria_satisfied"] is True
    assert result.values["all_declared_stability_criteria_satisfied"] is True
    first = result.values["parameter_diagnostics"][0]
    assert first["first_order_mean"] == pytest.approx(0.70)
    assert first["first_order_sample_standard_deviation"] == pytest.approx(0.01)
    assert first["first_order_range"] == pytest.approx(0.02)


def test_rank_reversal_and_dispersion_failure_are_reported_not_clipped():
    unstable = (
        *stable_replicates()[:2],
        replicate("replicate-3", 103, 0.10, 0.20, 0.80, 0.90),
    )
    result = sobol_replicate_stability(payload(replicates=unstable))
    assert result.status == "computed"
    assert result.values["rank_order_stable_at_declared_tie_tolerance"] is False
    assert result.values["dispersion_criteria_satisfied"] is False
    assert result.values["first_order_unstable_parameter_pairs"][0]["parameter_pair"] == [
        "parameter-a",
        "parameter-b",
    ]


def test_identity_seed_and_complete_parameter_set_are_strict():
    mismatched = replicate(
        "replicate-3",
        103,
        0.69,
        0.79,
        0.19,
        0.29,
        distribution_digest="e" * 64,
    )
    with pytest.raises(ValueError, match="share the declared identity"):
        payload(replicates=(*stable_replicates()[:2], mismatched))

    duplicate_seed = replicate("replicate-3", 102, 0.69, 0.79, 0.19, 0.29)
    with pytest.raises(ValueError, match="seeds must be unique"):
        payload(replicates=(*stable_replicates()[:2], duplicate_seed))

    incomplete = replicate("replicate-3", 103, 0.69, 0.79, 0.19, 0.29)
    incomplete["parameter_estimates"] = incomplete["parameter_estimates"][:1]
    with pytest.raises(ValueError, match="complete declared parameter set"):
        payload(replicates=(*stable_replicates()[:2], incomplete))


def test_review_invalid_record_or_minimum_replicates_needs_data():
    assert (
        sobol_replicate_stability(payload(design_family_and_evaluator_identity_reviewed=False)).status
        == "needs_data"
    )
    invalid = replicate(
        "replicate-3",
        103,
        0.69,
        0.79,
        0.19,
        0.29,
        record_valid=False,
        invalid_or_missing_basis="caller marked invalid",
    )
    assert (
        sobol_replicate_stability(payload(replicates=(*stable_replicates()[:2], invalid))).status
        == "needs_data"
    )
    assert sobol_replicate_stability(payload(minimum_replicate_count=4)).status == "needs_data"


def test_estimator_metadata_and_context_identity_are_enforced():
    missing_metadata = replicate("replicate-3", 103, 0.69, 0.79, 0.19, 0.29)
    missing_metadata["sample_count"] = None
    missing_metadata["effective_sample_size"] = None
    missing_metadata["parameter_estimates"] = tuple(
        {
            "parameter_id": row["parameter_id"],
            "first_order_index": row["first_order_index"],
            "total_order_index": row["total_order_index"],
        }
        for row in missing_metadata["parameter_estimates"]
    )
    with pytest.raises(ValueError, match="require estimator uncertainty"):
        payload(replicates=(*stable_replicates()[:2], missing_metadata))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "reliability.sobol_replicate_stability",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
