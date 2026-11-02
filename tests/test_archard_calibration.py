import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.archard_calibration import (
    ArchardWearCoefficientCalibration,
    archard_wear_coefficient_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    coefficient = 1e-4

    def row(identifier, partition, force, distance, specimen, group, status="valid"):
        valid = status == "valid"
        hardness = 1e9
        return {
            "observation_id": identifier,
            "physical_specimen_id": specimen,
            "source_group_id": group,
            "partition": partition,
            "material_condition_id": "material-1",
            "counterface_material_condition_id": "counterface-1",
            "contact_geometry_id": "contact-1",
            "lubrication_regime_id": "dry-1",
            "temperature_K": 300.0,
            "normal_force_N": force,
            "sliding_distance_m": distance,
            "hardness_Pa": hardness,
            "hardness_identity_id": "hardness-1",
            "measured_wear_volume_m3": coefficient * force * distance / hardness if valid else None,
            "expanded_uncertainty_wear_volume_m3": 1e-15 if valid else None,
            "uncertainty_coverage_factor": 2.0 if valid else None,
            "weight": 1.0 if valid else None,
            "record_status": status,
            "missing_or_invalid_basis": None if valid else "missing result",
            "record_digest": D,
            "evidence": [E],
        }

    value = {
        "calibration_id": "wear-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "material_condition_id": "material-1",
        "counterface_material_condition_id": "counterface-1",
        "contact_geometry_id": "contact-1",
        "lubrication_regime_id": "dry-1",
        "observations": [
            row("c1", "calibration", 10.0, 100.0, "s1", "g1"),
            row("c2", "calibration", 20.0, 200.0, "s2", "g2"),
            row("c3", "calibration", 15.0, 150.0, "s3", "g3"),
            row("h1", "holdout", 12.0, 120.0, "s4", "g4"),
            row("h2", "holdout", 18.0, 180.0, "s5", "g5"),
            row("m1", "holdout", 14.0, 140.0, "s6", "g6", "missing"),
        ],
        "minimum_calibration_specimen_count": 3,
        "minimum_calibration_source_group_count": 3,
        "minimum_holdout_specimen_count": 2,
        "minimum_holdout_source_group_count": 2,
        "material_contact_lubrication_and_temperature_regime_reviewed": True,
        "si_units_load_distance_hardness_and_volume_reviewed": True,
        "hardness_identity_and_measurement_basis_reviewed": True,
        "specimen_source_groups_and_partitions_reviewed": True,
        "uncertainty_weights_missingness_and_validity_reviewed": True,
        "calibration_support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return ArchardWearCoefficientCalibration.model_validate_json(json.dumps(value))


def test_coefficient_and_holdout_diagnostics():
    result = archard_wear_coefficient_calibration(payload())
    assert result.status == "computed"
    assert result.values["dimensionless_wear_coefficient"] == pytest.approx(1e-4)
    assert result.values["holdout_log_coefficient_rmse"] < 1e-12
    assert result.values["excluded_missing_or_invalid_observation_ids"] == ["m1"]


def test_holdout_outside_support_is_not_diagnosed():
    base = payload()
    outside = base.observations[3].model_copy(update={"normal_force_N": 30.0})
    result = archard_wear_coefficient_calibration(
        base.model_copy(update={"observations": base.observations[:3] + (outside,) + base.observations[4:]})
    )
    assert result.status == "out_of_scope"


def test_missing_review_needs_data():
    assert (
        archard_wear_coefficient_calibration(
            payload(hardness_identity_and_measurement_basis_reviewed=False)
        ).status
        == "needs_data"
    )


def test_partition_and_context_are_strict():
    base = payload()
    leaked = base.observations[3].model_copy(update={"source_group_id": "g1"})
    with pytest.raises(ValueError, match="cannot cross"):
        ArchardWearCoefficientCalibration(
            **base.model_dump(exclude={"observations"}),
            observations=base.observations[:3] + (leaked,) + base.observations[4:],
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.archard_wear_coefficient_calibration",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
