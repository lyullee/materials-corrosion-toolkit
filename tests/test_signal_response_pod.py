import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.signal_response_pod import (
    SignalResponsePODCalibration,
    signal_response_pod_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def observed(identifier, specimen, source, partition, size, residual, weight=1.0):
    return {
        "observation_id": identifier,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": f"ind-{specimen}",
        "partition": partition,
        "flaw_size_value": size,
        "flaw_size_definition_id": "size-definition-1",
        "flaw_size_unit_token": "mm",
        "signal_definition_id": "signal-definition-1",
        "signal_unit_token": "V",
        "observation_status": "observed",
        "reported_signal_value": 0.5 + 1.2 * math.log(size) + residual,
        "nominal_weight": weight,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def envelope():
    return {
        "envelope_id": "envelope-1",
        "material_condition_id": "material-1",
        "inspection_procedure_id": "procedure-1",
        "inspection_procedure_revision": "1",
        "flaw_size_definition_id": "size-definition-1",
        "flaw_size_unit_token": "mm",
        "minimum_supported_flaw_size": 1.0,
        "maximum_supported_flaw_size": 5.0,
        "signal_definition_id": "signal-definition-1",
        "signal_unit_token": "V",
        "fixed_detection_threshold": 1.5,
        "regression_form": "normal_residual_signal_linear_in_natural_log_size",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_C,
        "data_digest": DIGEST_D,
        "minimum_calibration_physical_specimen_count": 6,
        "minimum_holdout_physical_specimen_count": 3,
        "minimum_calibration_source_group_count": 2,
        "minimum_holdout_source_group_count": 1,
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }


def observations():
    return (
        observed("cal-1", "cal-spec-1", "cal-source-a", "calibration", 1.0, -0.08),
        observed("cal-2", "cal-spec-2", "cal-source-a", "calibration", 1.2, 0.06),
        observed("cal-3", "cal-spec-3", "cal-source-a", "calibration", 1.5, -0.04, 2.0),
        observed("cal-4", "cal-spec-4", "cal-source-b", "calibration", 2.0, 0.09),
        observed("cal-5", "cal-spec-5", "cal-source-b", "calibration", 3.0, -0.05),
        observed("cal-6", "cal-spec-6", "cal-source-b", "calibration", 4.0, 0.03),
        observed("hold-1", "hold-spec-1", "hold-source", "holdout", 1.3, 0.02),
        observed("hold-2", "hold-spec-2", "hold-source", "holdout", 2.5, -0.03),
        observed("hold-3", "hold-spec-3", "hold-source", "holdout", 3.5, 0.04),
        {
            "observation_id": "hold-censored",
            "physical_specimen_id": "hold-spec-4",
            "source_group_id": "hold-source",
            "independence_group_id": "ind-hold-spec-4",
            "partition": "holdout",
            "flaw_size_value": 2.0,
            "flaw_size_definition_id": "size-definition-1",
            "flaw_size_unit_token": "mm",
            "signal_definition_id": "signal-definition-1",
            "signal_unit_token": "V",
            "observation_status": "left_censored",
            "censor_limit_value": 0.1,
            "missing_or_censor_basis": "authored instrument floor",
            "nominal_weight": 1.0,
            "provider_id": "provider-1",
            "provider_revision": "1",
            "provider_state_digest": DIGEST_A,
            "result_digest": DIGEST_B,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
    )


def payload(**updates):
    value = {
        "calibration_id": "pod-calibration-1",
        "asset_id": "asset-1",
        "location_id": "inspection-scope-1",
        "physical_scope_id": "physical-scope-1",
        "material_condition_id": "material-1",
        "inspection_procedure_id": "procedure-1",
        "inspection_procedure_revision": "1",
        "observations": observations(),
        "qualification_envelope": envelope(),
        "query_flaw_sizes": (1.2, 2.0, 3.0, 4.0),
        "target_probability_of_detection": 0.9,
        "specimen_source_and_independence_partitions_reviewed": True,
        "flaw_size_definition_and_units_reviewed": True,
        "signal_definition_threshold_and_units_reviewed": True,
        "censoring_missingness_and_weights_reviewed": True,
        "support_range_reviewed": True,
        "provider_lineage_configuration_and_digests_reviewed": True,
        "calibration_holdout_design_reviewed": True,
        "normal_residual_log_size_model_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return SignalResponsePODCalibration(**value)


def test_weighted_signal_response_fit_and_holdout_metrics_are_reported():
    result = signal_response_pod_calibration(payload())
    assert result.status == "computed"
    assert result.values["slope_signal_per_natural_log_size"] > 0
    assert result.values["holdout_observed_count"] == 3
    assert result.values["censored_observation_ids_excluded_from_fit_and_metrics"] == ["hold-censored"]
    assert 0 <= result.values["holdout_weighted_brier_score"] <= 1
    probabilities = result.values["probability_of_detection"]
    assert probabilities == sorted(probabilities)


def test_missing_review_or_provider_unit_mismatch_needs_data():
    assert (
        signal_response_pod_calibration(payload(censoring_missingness_and_weights_reviewed=False)).status
        == "needs_data"
    )
    rows = list(observations())
    rows[0] = {**rows[0], "signal_unit_token": "other"}
    result = signal_response_pod_calibration(payload(observations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["incompatible_observation_ids"] == ["cal-1"]


def test_query_or_observation_outside_support_is_not_extrapolated():
    result = signal_response_pod_calibration(payload(query_flaw_sizes=(0.5, 2.0)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_query_sizes"] == [0.5]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(observations())
    rows[6] = {**rows[6], "source_group_id": "cal-source-a"}
    with pytest.raises(ValueError, match="source group"):
        payload(observations=tuple(rows))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.signal_response_pod_calibration",
            payload(),
            RunContext(asset_id="other", location_id="inspection-scope-1", time_basis="authored"),
        )
