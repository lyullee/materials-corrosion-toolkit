import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.erosion_corrosion_power_law import (
    ErosionCorrosionPowerLawCalibration,
    erosion_corrosion_power_law_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
REF_VELOCITY = 2.0
REF_PARTICLE = 0.3


def record(identifier, partition, velocity, particle, residual, source=None):
    log_rate = (
        -12.0 + 1.5 * math.log(velocity / REF_VELOCITY) + 0.8 * math.log(particle / REF_PARTICLE) + residual
    )
    return {
        "observation_id": identifier,
        "physical_specimen_id": f"specimen-{identifier}",
        "source_group_id": source or f"source-{partition}",
        "independence_group_id": f"independence-{identifier}",
        "partition": partition,
        "material_condition_id": "material-1",
        "fluid_condition_id": "fluid-1",
        "geometry_condition_id": "geometry-1",
        "mechanism_scope_id": "combined-loss-regime-1",
        "velocity_value": velocity,
        "velocity_unit_token": "m/s",
        "particle_concentration_value": particle,
        "particle_concentration_unit_token": "kg/m^3",
        "measured_loss_rate_value": math.exp(log_rate),
        "loss_rate_unit_token": "m/s",
        "nominal_weight": 1.0,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def observations():
    return (
        record("cal-1", "calibration", 1.0, 0.1, -0.08, "cal-source-a"),
        record("cal-2", "calibration", 1.0, 0.5, 0.06, "cal-source-a"),
        record("cal-3", "calibration", 3.0, 0.1, -0.04, "cal-source-a"),
        record("cal-4", "calibration", 3.0, 0.5, 0.09, "cal-source-a"),
        record("cal-5", "calibration", 1.0, 0.1, 0.03, "cal-source-b"),
        record("cal-6", "calibration", 1.0, 0.5, -0.05, "cal-source-b"),
        record("cal-7", "calibration", 3.0, 0.1, 0.04, "cal-source-b"),
        record("cal-8", "calibration", 3.0, 0.5, -0.02, "cal-source-b"),
        record("hold-1", "holdout", 1.5, 0.2, 0.02, "hold-source"),
        record("hold-2", "holdout", 2.5, 0.4, -0.03, "hold-source"),
    )


def payload(**updates):
    value = {
        "calibration_id": "calibration-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "material_condition_id": "material-1",
        "fluid_condition_id": "fluid-1",
        "geometry_condition_id": "geometry-1",
        "mechanism_scope_id": "combined-loss-regime-1",
        "regression_form": "log_loss_rate_intercept_plus_log_velocity_plus_log_particle_concentration",
        "velocity_unit_token": "m/s",
        "particle_concentration_unit_token": "kg/m^3",
        "loss_rate_unit_token": "m/s",
        "reference_velocity_value": REF_VELOCITY,
        "reference_particle_concentration_value": REF_PARTICLE,
        "observations": observations(),
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "calibration_dataset_digest": DIGEST_B,
        "holdout_dataset_digest": DIGEST_C,
        "minimum_calibration_record_count": 8,
        "minimum_holdout_record_count": 2,
        "material_fluid_geometry_and_mechanism_scope_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "velocity_particle_and_loss_rate_units_reviewed": True,
        "weights_and_positive_measurements_reviewed": True,
        "calibration_support_hull_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "regression_form_and_minimum_counts_reviewed": True,
        "common_power_law_regime_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ErosionCorrosionPowerLawCalibration(**value)


def test_weighted_power_law_and_holdout_diagnostics_compute():
    result = erosion_corrosion_power_law_calibration(payload())
    assert result.status == "computed"
    assert result.values["velocity_exponent"] == pytest.approx(1.5, abs=0.15)
    assert result.values["particle_concentration_exponent"] == pytest.approx(0.8, abs=0.15)
    assert math.isfinite(result.values["holdout_weighted_log_rmse"])
    assert len(result.values["holdout_rows"]) == 2


def test_missing_review_or_identity_unit_mismatch_needs_data():
    assert (
        erosion_corrosion_power_law_calibration(payload(common_power_law_regime_reviewed=False)).status
        == "needs_data"
    )
    rows = list(observations())
    rows[0] = {**rows[0], "loss_rate_unit_token": "mm/year"}
    result = erosion_corrosion_power_law_calibration(payload(observations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["identity_or_unit_mismatch_ids"] == ["cal-1"]


@pytest.mark.parametrize(
    "unit_field",
    ["velocity_unit_token", "particle_concentration_unit_token", "loss_rate_unit_token"],
)
def test_each_observation_unit_must_match_the_declared_calibration_unit(unit_field):
    rows = list(observations())
    rows[0] = {**rows[0], unit_field: "intentionally-incompatible-unit"}
    result = erosion_corrosion_power_law_calibration(payload(observations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["identity_or_unit_mismatch_ids"] == ["cal-1"]


def test_holdout_outside_two_dimensional_hull_is_not_extrapolated():
    rows = list(observations())
    rows[8] = record("hold-1", "holdout", 4.0, 0.8, 0.02, "hold-source")
    result = erosion_corrosion_power_law_calibration(payload(observations=tuple(rows)))
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
            "degradation.erosion_corrosion_power_law_calibration",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
