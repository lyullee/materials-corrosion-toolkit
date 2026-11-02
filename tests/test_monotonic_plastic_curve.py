import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.monotonic_plastic_curve import (
    MonotonicHollomonCalibration,
    monotonic_hollomon_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    K = 1000.0
    n = 0.2
    modulus = 200000.0

    def row(i, p, ep, s, g):
        stress = K * ep**n
        return {
            "point_id": i,
            "physical_specimen_id": s,
            "source_group_id": g,
            "independence_group_id": g,
            "partition": p,
            "material_condition_id": "m1",
            "quantity_convention": "true",
            "stress_value": stress,
            "stress_unit_token": "MPa",
            "total_strain": ep + stress / modulus,
            "strain_unit_token": "1",
            "elastic_modulus": modulus,
            "elastic_modulus_unit_token": "MPa",
            "stress_standard_uncertainty": 1.0,
            "weight": 1.0,
            "pre_necking_window_id": "window-1",
            "pre_necking_reviewed": True,
            "record_digest": D,
            "record_valid": True,
            "evidence": [E],
        }

    v = {
        "calibration_id": "f1",
        "asset_id": "a1",
        "location_id": "l1",
        "material_condition_id": "m1",
        "quantity_convention": "true",
        "points": [
            row("c1", "calibration", 0.001, "s1", "g1"),
            row("c2", "calibration", 0.004, "s2", "g2"),
            row("c3", "calibration", 0.01, "s3", "g3"),
            row("h1", "holdout", 0.002, "s4", "g4"),
        ],
        "minimum_calibration_specimen_count": 3,
        "minimum_calibration_source_group_count": 3,
        "minimum_holdout_specimen_count": 1,
        "minimum_holdout_source_group_count": 1,
        "monotonic_loading_and_quantity_convention_reviewed": True,
        "stress_strain_units_sign_and_elastic_subtraction_reviewed": True,
        "pre_necking_windows_reviewed": True,
        "specimen_source_independence_and_partitions_reviewed": True,
        "uncertainty_weights_validity_and_digests_reviewed": True,
        "calibration_support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return MonotonicHollomonCalibration.model_validate_json(json.dumps(v))


def test_fit():
    r = monotonic_hollomon_calibration(payload())
    assert r.status == "computed"
    assert r.values["strength_coefficient"] == pytest.approx(1000)
    assert r.values["strain_hardening_exponent"] == pytest.approx(0.2)
    assert r.values["holdout_log_stress_rmse"] < 1e-12


def test_outside():
    b = payload()
    h = b.points[-1]
    stress = 1000 * 0.02**0.2
    h = h.model_copy(update={"stress_value": stress, "total_strain": 0.02 + stress / 200000})
    assert (
        monotonic_hollomon_calibration(b.model_copy(update={"points": b.points[:-1] + (h,)})).status
        == "out_of_scope"
    )


def test_needs():
    assert monotonic_hollomon_calibration(payload(pre_necking_windows_reviewed=False)).status == "needs_data"


def test_partition_context():
    b = payload()
    bad = b.points[-1].model_copy(update={"physical_specimen_id": "s1"})
    with pytest.raises(ValueError, match="cannot cross"):
        MonotonicHollomonCalibration(**b.model_dump(exclude={"points"}), points=b.points[:-1] + (bad,))
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "materials.monotonic_hollomon_calibration",
            b,
            RunContext(asset_id="other", location_id="l1", time_basis="monotonic"),
        )
