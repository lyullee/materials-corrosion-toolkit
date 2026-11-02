import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.creep_rupture_calibration import (
    CreepRuptureFit,
    creep_rupture_fit,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
REF_STRESS = 150e6
REF_TEMPERATURE = 750.0


def record(identifier, partition, stress, temperature, residual, censored=False, source=None):
    log_time = (
        8.0
        + 2.0 * math.log(REF_STRESS / stress)
        + 3000.0 * (1 / temperature - 1 / REF_TEMPERATURE)
        + residual
    )
    return {
        "observation_id": identifier,
        "physical_specimen_id": f"specimen-{identifier}",
        "source_group_id": source or f"source-{partition}",
        "independence_group_id": f"independence-{identifier}",
        "partition": partition,
        "material_condition_id": "material-1",
        "load_control_id": "constant-load-1",
        "stress_convention": "initial_nominal_constant_load",
        "stress_value_Pa": stress,
        "stress_unit_token": "Pa",
        "temperature_K": temperature,
        "temperature_unit_token": "K",
        "endpoint_time_s": math.exp(log_time),
        "time_unit_token": "s",
        "endpoint_status": "right_censored" if censored else "rupture",
        "nominal_weight": 1.0,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def observations():
    return (
        record("cal-1", "calibration", 100e6, 700.0, -0.08, source="cal-source-a"),
        record("cal-2", "calibration", 100e6, 800.0, 0.06, source="cal-source-a"),
        record("cal-3", "calibration", 200e6, 700.0, -0.04, source="cal-source-a"),
        record("cal-4", "calibration", 200e6, 800.0, 0.09, source="cal-source-a"),
        record("cal-5", "calibration", 100e6, 700.0, 0.03, source="cal-source-b"),
        record("cal-6", "calibration", 100e6, 800.0, -0.05, source="cal-source-b"),
        record("cal-7", "calibration", 200e6, 700.0, 0.04, censored=True, source="cal-source-b"),
        record("cal-8", "calibration", 200e6, 800.0, 0.15, censored=True, source="cal-source-b"),
        record("hold-1", "holdout", 130e6, 730.0, 0.02, source="hold-source"),
        record("hold-2", "holdout", 160e6, 770.0, -0.03, source="hold-source"),
        record("hold-3", "holdout", 145e6, 760.0, 0.08, censored=True, source="hold-source"),
    )


def payload(**updates):
    value = {
        "fit_id": "fit-1",
        "asset_id": "asset-1",
        "location_id": "creep-location-1",
        "physical_scope_id": "creep-scope-1",
        "material_condition_id": "material-1",
        "load_control_id": "constant-load-1",
        "stress_convention": "initial_nominal_constant_load",
        "regression_form": "log_time_intercept_plus_log_inverse_stress_plus_reciprocal_temperature",
        "reference_stress_Pa": REF_STRESS,
        "reference_temperature_K": REF_TEMPERATURE,
        "observations": observations(),
        "minimum_calibration_record_count": 8,
        "minimum_calibration_rupture_count": 6,
        "minimum_holdout_record_count": 3,
        "material_load_and_stress_convention_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "stress_temperature_time_units_reviewed": True,
        "rupture_and_right_censor_definitions_reviewed": True,
        "censoring_independence_and_weights_reviewed": True,
        "common_mechanism_over_support_reviewed": True,
        "calibration_support_hull_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "regression_form_and_minimum_counts_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CreepRuptureFit(**value)


def test_weighted_censored_fit_and_holdout_diagnostics_compute():
    result = creep_rupture_fit(payload())
    assert result.status == "computed"
    assert result.values["log_inverse_stress_coefficient"] > 0
    assert result.values["reciprocal_temperature_coefficient_K"] > 0
    assert result.values["log_time_sigma"] > 0
    assert len(result.values["holdout_rows"]) == 3
    assert math.isfinite(result.values["holdout_weighted_mean_negative_log_likelihood_seconds"])


def test_missing_review_or_minimum_count_needs_data():
    assert creep_rupture_fit(payload(common_mechanism_over_support_reviewed=False)).status == "needs_data"
    assert creep_rupture_fit(payload(minimum_calibration_rupture_count=7)).status == "needs_data"


def test_holdout_outside_calibration_hull_is_out_of_scope():
    rows = list(observations())
    rows[8] = record("hold-1", "holdout", 250e6, 850.0, 0.02, source="hold-source")
    result = creep_rupture_fit(payload(observations=tuple(rows)))
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
            "creep.accelerated_lognormal_rupture_fit",
            payload(),
            RunContext(asset_id="other", location_id="creep-location-1", time_basis="authored"),
        )
