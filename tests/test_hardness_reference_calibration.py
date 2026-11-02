import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hardness_reference_calibration import (
    HardnessReferenceBlockCalibration,
    hardness_reference_block_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def record(identifier, partition, block, certified, temperature, residual, source=None):
    return {
        "observation_id": identifier,
        "physical_reference_block_id": block,
        "source_group_id": source or f"source-{partition}",
        "independence_group_id": f"independence-{block}",
        "partition": partition,
        "reference_block_condition_id": "block-material-1",
        "method_id": "method-1",
        "scale_id": "scale-1",
        "indenter_id": "indenter-1",
        "applied_load_value": 10.0,
        "applied_load_unit_token": "kgf",
        "dwell_time_s": 10.0,
        "instrument_id": "instrument-1",
        "instrument_configuration_id": "configuration-1",
        "instrument_configuration_digest": DIGEST_A,
        "specimen_temperature_K": temperature,
        "certified_hardness_value": certified,
        "certified_standard_uncertainty": 0.5,
        "certificate_weight": 1.0,
        "observed_hardness_value": certified + 2.0 + residual,
        "hardness_unit_token": "scale-1-unit",
        "certificate_provider_id": "certificate-provider",
        "certificate_revision": "1",
        "certificate_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def observations():
    return (
        record("cal-1", "calibration", "block-cal-1", 100.0, 293.0, -1.0, "cal-source-a"),
        record("cal-2", "calibration", "block-cal-1", 100.0, 293.0, 0.5, "cal-source-a"),
        record("cal-3", "calibration", "block-cal-2", 180.0, 295.0, -0.4, "cal-source-a"),
        record("cal-4", "calibration", "block-cal-2", 180.0, 295.0, 0.8, "cal-source-a"),
        record("cal-5", "calibration", "block-cal-3", 240.0, 297.0, -0.7, "cal-source-b"),
        record("cal-6", "calibration", "block-cal-3", 240.0, 297.0, 0.3, "cal-source-b"),
        record("cal-7", "calibration", "block-cal-4", 300.0, 298.0, -0.2, "cal-source-b"),
        record("cal-8", "calibration", "block-cal-4", 300.0, 298.0, 0.7, "cal-source-b"),
        record("hold-1", "holdout", "block-hold-1", 150.0, 294.0, 0.2, "hold-source"),
        record("hold-2", "holdout", "block-hold-2", 260.0, 297.0, -0.3, "hold-source"),
    )


def payload(**updates):
    value = {
        "calibration_id": "calibration-1",
        "asset_id": "asset-1",
        "location_id": "lab-1",
        "physical_scope_id": "instrument-scope-1",
        "reference_block_condition_id": "block-material-1",
        "method_id": "method-1",
        "scale_id": "scale-1",
        "indenter_id": "indenter-1",
        "applied_load_value": 10.0,
        "applied_load_unit_token": "kgf",
        "dwell_time_s": 10.0,
        "dwell_time_tolerance_s": 0.1,
        "instrument_id": "instrument-1",
        "instrument_configuration_id": "configuration-1",
        "instrument_configuration_digest": DIGEST_A,
        "hardness_unit_token": "scale-1-unit",
        "temperature_support_tolerance_K": 0.5,
        "observations": observations(),
        "minimum_calibration_record_count": 8,
        "minimum_calibration_physical_block_count": 4,
        "minimum_holdout_record_count": 2,
        "method_scale_indenter_load_and_dwell_reviewed": True,
        "instrument_identity_configuration_and_digest_reviewed": True,
        "reference_block_condition_and_temperature_reviewed": True,
        "certificate_values_uncertainties_and_weights_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "certificate_and_result_digests_reviewed": True,
        "calibration_holdout_support_reviewed": True,
        "bias_and_repeatability_model_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return HardnessReferenceBlockCalibration(**value)


def test_bias_repeatability_and_holdout_diagnostics_compute():
    result = hardness_reference_block_calibration(payload())
    assert result.status == "computed"
    assert result.values["estimated_bias_observed_minus_certified"] == pytest.approx(2.0, abs=0.5)
    assert result.values["repeatability_standard_deviation"] > 0
    assert len(result.values["holdout_rows"]) == 2
    assert math.isfinite(result.values["holdout_weighted_bias_corrected_rmse"])


def test_missing_review_or_configuration_mismatch_needs_data():
    assert (
        hardness_reference_block_calibration(payload(bias_and_repeatability_model_reviewed=False)).status
        == "needs_data"
    )
    rows = list(observations())
    rows[0] = {**rows[0], "scale_id": "other-scale"}
    result = hardness_reference_block_calibration(payload(observations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["incompatible_observation_ids"] == ["cal-1"]


def test_holdout_outside_certified_value_support_is_not_extrapolated():
    rows = list(observations())
    rows[8] = record("hold-1", "holdout", "block-hold-1", 350.0, 294.0, 0.2, "hold-source")
    result = hardness_reference_block_calibration(payload(observations=tuple(rows)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_holdout_ids"] == ["hold-1"]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(observations())
    rows[8] = {**rows[8], "source_group_id": "cal-source-a"}
    with pytest.raises(ValueError, match="source group"):
        payload(observations=tuple(rows))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.hardness_reference_block_calibration",
            payload(),
            RunContext(asset_id="other", location_id="lab-1", time_basis="authored"),
        )
