import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.polymer_arrhenius_shift import (
    PolymerArrheniusShiftCalibration,
    polymer_arrhenius_shift_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
D = "a" * 64


def payload(**updates):
    reference = 300.0
    slope = 2000.0

    def row(identifier, partition, temperature, specimen, group, status="valid"):
        valid = status == "valid"
        return {
            "observation_id": identifier,
            "physical_specimen_id": specimen,
            "source_group_id": group,
            "independence_group_id": group,
            "partition": partition,
            "polymer_formulation_id": "formulation-1",
            "physical_state_id": "state-1",
            "endpoint_definition_id": "endpoint-1",
            "temperature_K": temperature,
            "log_time_shift_factor": slope * (1 / temperature - 1 / reference) if valid else None,
            "log_basis": "natural",
            "weight": 1.0 if valid else None,
            "record_status": status,
            "missing_or_invalid_basis": None if valid else "result unavailable",
            "provider_id": "provider-1",
            "provider_revision": "1",
            "provider_record_digest": D,
            "result_digest": D if valid else None,
            "evidence": [E],
        }

    value = {
        "calibration_id": "fit-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "polymer_formulation_id": "formulation-1",
        "physical_state_id": "state-1",
        "endpoint_definition_id": "endpoint-1",
        "reference_temperature_K": reference,
        "observations": [
            row("c1", "calibration", 280.0, "s1", "g1"),
            row("c2", "calibration", 300.0, "s2", "g2"),
            row("c3", "calibration", 320.0, "s3", "g3"),
            row("h1", "holdout", 290.0, "s4", "g4"),
            row("h2", "holdout", 310.0, "s5", "g5"),
            row("m1", "holdout", 300.0, "s6", "g6", "missing"),
        ],
        "minimum_calibration_specimen_count": 3,
        "minimum_calibration_source_group_count": 3,
        "minimum_holdout_specimen_count": 2,
        "minimum_holdout_source_group_count": 2,
        "formulation_physical_state_and_endpoint_reviewed": True,
        "absolute_temperature_reference_and_log_basis_reviewed": True,
        "specimen_source_independence_and_partitions_reviewed": True,
        "weights_missingness_and_validity_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "calibration_support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return PolymerArrheniusShiftCalibration.model_validate_json(json.dumps(value))


def test_weighted_fit_and_holdout_diagnostics():
    result = polymer_arrhenius_shift_calibration(payload())
    assert result.status == "computed"
    assert result.values["reciprocal_temperature_slope_K"] == pytest.approx(2000.0)
    assert result.values["holdout_log_shift_rmse"] < 1e-12
    assert result.values["excluded_missing_or_invalid_observation_ids"] == ["m1"]


def test_holdout_outside_calibration_temperature_is_not_extrapolated():
    base = payload()
    outside = base.observations[3].model_copy(update={"temperature_K": 330.0})
    result = polymer_arrhenius_shift_calibration(
        base.model_copy(update={"observations": base.observations[:3] + (outside,) + base.observations[4:]})
    )
    assert result.status == "out_of_scope"


def test_missing_review_needs_data():
    assert (
        polymer_arrhenius_shift_calibration(payload(provider_lineage_and_digests_reviewed=False)).status
        == "needs_data"
    )


def test_partition_and_context_identity_are_strict():
    base = payload()
    leaked = base.observations[3].model_copy(update={"physical_specimen_id": "s1"})
    with pytest.raises(ValueError, match="cannot cross"):
        PolymerArrheniusShiftCalibration(
            **base.model_dump(exclude={"observations"}),
            observations=base.observations[:3] + (leaked,) + base.observations[4:],
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.polymer_arrhenius_shift_calibration",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
