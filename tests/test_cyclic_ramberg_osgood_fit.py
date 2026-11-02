import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.cyclic_ramberg_osgood_fit import (
    CyclicRambergOsgoodFit,
    cyclic_ramberg_osgood_fit,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    K = 1000.0
    n = 0.2

    def row(i, p, eps, spec, grp):
        return {
            "observation_id": i,
            "physical_specimen_id": spec,
            "source_group_id": grp,
            "independence_group_id": grp,
            "partition": p,
            "material_condition_id": "m1",
            "stress_amplitude": K * eps**n,
            "stress_unit_token": "MPa",
            "total_strain_amplitude": eps,
            "strain_unit_token": "1",
            "plastic_strain_definition": "explicit_reported",
            "reported_plastic_strain_amplitude": eps,
            "weight": 1.0,
            "record_digest": D,
            "record_valid": True,
            "evidence": [E],
        }

    v = {
        "fit_id": "f1",
        "asset_id": "a1",
        "location_id": "l1",
        "material_condition_id": "m1",
        "observations": [
            row("c1", "calibration", 0.001, "s1", "g1"),
            row("c2", "calibration", 0.004, "s2", "g2"),
            row("c3", "calibration", 0.01, "s3", "g3"),
            row("h1", "holdout", 0.002, "s4", "g4"),
        ],
        "minimum_calibration_specimen_count": 3,
        "minimum_calibration_source_group_count": 3,
        "minimum_holdout_specimen_count": 1,
        "minimum_holdout_source_group_count": 1,
        "material_and_stabilized_cycle_definition_reviewed": True,
        "stress_strain_amplitudes_units_and_sign_reviewed": True,
        "plastic_strain_definition_and_elastic_modulus_reviewed": True,
        "specimen_source_independence_and_partitions_reviewed": True,
        "weights_and_record_validity_reviewed": True,
        "support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return CyclicRambergOsgoodFit.model_validate_json(json.dumps(v))


def test_fit():
    r = cyclic_ramberg_osgood_fit(payload())
    assert r.status == "computed"
    assert r.values["cyclic_strength_coefficient"] == pytest.approx(1000)
    assert r.values["cyclic_strain_hardening_exponent"] == pytest.approx(0.2)
    assert r.values["holdout_log_stress_rmse"] < 1e-12


def test_no_extrapolation():
    b = payload()
    h = b.observations[-1].model_copy(
        update={"reported_plastic_strain_amplitude": 0.02, "total_strain_amplitude": 0.02}
    )
    assert (
        cyclic_ramberg_osgood_fit(b.model_copy(update={"observations": b.observations[:-1] + (h,)})).status
        == "out_of_scope"
    )


def test_needs():
    assert (
        cyclic_ramberg_osgood_fit(payload(weights_and_record_validity_reviewed=False)).status == "needs_data"
    )


def test_derived_plastic_strain_requires_identical_stress_and_modulus_units():
    base = payload()
    row = base.observations[0].model_copy(
        update={
            "plastic_strain_definition": "total_minus_elastic",
            "reported_plastic_strain_amplitude": None,
            "elastic_modulus": 200.0,
            "elastic_modulus_unit_token": "GPa",
        }
    )
    result = cyclic_ramberg_osgood_fit(
        base.model_copy(update={"observations": (row,) + base.observations[1:]})
    )
    assert result.status == "needs_data"
    assert result.values["mismatched_elastic_modulus_unit_observation_ids"] == ["c1"]


def test_partition_context():
    b = payload()
    bad = b.observations[-1].model_copy(update={"physical_specimen_id": "s1"})
    with pytest.raises(ValueError, match="cannot cross"):
        CyclicRambergOsgoodFit(
            **b.model_dump(exclude={"observations"}), observations=b.observations[:-1] + (bad,)
        )
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "materials.cyclic_ramberg_osgood_fit",
            b,
            RunContext(asset_id="other", location_id="l1", time_basis="cycles"),
        )
