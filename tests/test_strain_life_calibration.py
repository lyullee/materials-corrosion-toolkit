import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.strain_life_calibration import (
    StrainLifeCoefficientCalibration,
    specifications,
    strain_life_coefficient_calibration,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    def row(i, p, n, s, g, status="failure"):
        return {
            "observation_id": i,
            "physical_specimen_id": s,
            "source_group_id": g,
            "independence_group_id": g,
            "partition": p,
            "material_condition_id": "m1",
            "endpoint_status": status,
            "cycles_value": n,
            "cycles_definition": "cycles to authored endpoint",
            "elastic_strain_amplitude": 0.01 * (2 * n) ** -0.1 if status == "failure" else None,
            "plastic_strain_amplitude": 0.5 * (2 * n) ** -0.5 if status == "failure" else None,
            "strain_unit_token": "1",
            "weight": 1.0,
            "record_digest": D,
            "record_valid": True,
            "evidence": [E],
        }

    v = {
        "calibration_id": "fit1",
        "asset_id": "a1",
        "location_id": "l1",
        "material_condition_id": "m1",
        "elastic_modulus": 200000.0,
        "stress_unit_token": "MPa",
        "observations": [
            row("c1", "calibration", 100, "s1", "g1"),
            row("c2", "calibration", 1000, "s2", "g2"),
            row("c3", "calibration", 10000, "s3", "g3"),
            row("h1", "holdout", 500, "s4", "g4"),
            row("h2", "holdout", 5000, "s5", "g5"),
            row("r1", "holdout", 20000, "s6", "g6", "runout"),
        ],
        "minimum_calibration_failure_specimen_count": 3,
        "minimum_calibration_failure_source_group_count": 3,
        "minimum_holdout_failure_specimen_count": 2,
        "minimum_holdout_failure_source_group_count": 2,
        "stabilized_cycle_and_failure_endpoint_reviewed": True,
        "elastic_plastic_component_definition_reviewed": True,
        "cycles_reversals_and_units_reviewed": True,
        "censoring_and_runout_status_reviewed": True,
        "specimen_source_independence_and_partitions_reviewed": True,
        "weights_validity_and_digests_reviewed": True,
        "support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return StrainLifeCoefficientCalibration.model_validate_json(json.dumps(v))


def test_fit():
    r = strain_life_coefficient_calibration(payload())
    assert r.status == "computed"
    assert r.values["fatigue_strength_exponent"] == pytest.approx(-0.1)
    assert r.values["fatigue_ductility_exponent"] == pytest.approx(-0.5)
    assert r.values["excluded_runout_or_censored_observation_ids"] == ["r1"]


def test_outside():
    b = payload()
    h = b.observations[3].model_copy(update={"cycles_value": 10.0})
    assert (
        strain_life_coefficient_calibration(
            b.model_copy(update={"observations": b.observations[:3] + (h,) + b.observations[4:]})
        ).status
        == "out_of_scope"
    )


def test_needs():
    assert (
        strain_life_coefficient_calibration(payload(censoring_and_runout_status_reviewed=False)).status
        == "needs_data"
    )


def test_context():
    b = payload()
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "materials.strain_life_coefficient_calibration",
            b,
            RunContext(asset_id="other", location_id="l1", time_basis="cycles"),
        )
