import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fracture_toughness_evidence import (
    FractureToughnessEvidenceAssessment,
    fracture_toughness_test_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def record(partition, index, **updates):
    value = {
        "record_id": f"record-{index}",
        "physical_specimen_id": f"specimen-{index}",
        "source_group_id": f"source-group-{index}",
        "partition": partition,
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "specimen_geometry_id": "geometry-1",
        "specimen_geometry_descriptor": "caller-defined geometry",
        "notch_orientation_id": "notch-L",
        "crack_orientation_id": "crack-T",
        "temperature_K": 293.15,
        "load_rate_value": 1.0,
        "load_rate_unit_token": "custom-load-rate-unit",
        "environment_id": "laboratory-air",
        "endpoint_kind": "initiation",
        "endpoint_definition_id": "caller-initiation-endpoint",
        "reported_value": 100.0 + index,
        "reported_unit_token": "custom-toughness-unit",
        "expanded_uncertainty": 5.0,
        "uncertainty_basis": "caller uncertainty budget",
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "caller_validity_record_id": f"validity-{index}",
        "record_valid": True,
        "supports_declared_endpoint": True,
        "validity_evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "evidence_collection_id": "collection-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "records": (
            record("calibration", 1),
            record("holdout", 2),
            record("application", 3),
        ),
        "required_partitions": ("calibration", "holdout", "application"),
        "material_and_condition_identity_reviewed": True,
        "physical_specimen_identity_reviewed": True,
        "source_group_and_partition_reviewed": True,
        "geometry_and_orientation_reviewed": True,
        "temperature_rate_and_environment_reviewed": True,
        "endpoint_units_and_uncertainty_reviewed": True,
        "caller_validity_evidence_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
    }
    value.update(updates)
    return FractureToughnessEvidenceAssessment(**value)


def test_partitioned_evidence_is_preserved_without_value_conversion():
    result = fracture_toughness_test_evidence(payload())
    assert result.status == "computed"
    assert result.values["record_count"] == 3
    assert result.values["missing_required_partitions"] == []
    holdout = next(row for row in result.values["partition_summaries"] if row["partition"] == "holdout")
    assert holdout["endpoint_groups"][0]["reported_values"] == [102.0]
    assert holdout["endpoint_groups"][0]["reported_unit_token"] == "custom-toughness-unit"


def test_missing_partition_invalid_or_unsupported_evidence_needs_data():
    result = fracture_toughness_test_evidence(payload(records=(record("calibration", 1),)))
    assert result.status == "needs_data"
    assert result.values["missing_required_partitions"] == ["holdout", "application"]

    invalid = record(
        "calibration",
        1,
        record_valid=False,
        supports_declared_endpoint=False,
        invalid_or_limiting_basis="caller marked invalid",
    )
    result = fracture_toughness_test_evidence(
        payload(records=(invalid,), required_partitions=("calibration",))
    )
    assert result.status == "needs_data"
    assert result.values["invalid_record_ids"] == ["record-1"]
    assert result.values["unsupported_endpoint_record_ids"] == ["record-1"]


def test_specimen_and_source_groups_cannot_cross_partitions():
    with pytest.raises(ValueError, match="physical specimens cannot cross"):
        payload(
            records=(
                record("calibration", 1),
                record("holdout", 2, physical_specimen_id="specimen-1"),
            )
        )
    with pytest.raises(ValueError, match="source groups cannot cross"):
        payload(
            records=(
                record("calibration", 1),
                record("holdout", 2, source_group_id="source-group-1"),
            )
        )


def test_endpoint_and_uncertainty_contracts_are_explicit():
    with pytest.raises(ValueError, match="user-defined toughness endpoint requires"):
        payload(records=(record("calibration", 1, endpoint_kind="user_defined"),))
    with pytest.raises(ValueError, match="requires uncertainty"):
        payload(records=(record("calibration", 1, expanded_uncertainty=None),))
    with pytest.raises(ValueError, match="cannot carry uncertainty"):
        payload(
            records=(
                record(
                    "calibration",
                    1,
                    reported_value=None,
                    expanded_uncertainty=1.0,
                    uncertainty_basis=None,
                ),
            )
        )


def test_review_and_context_identity_are_enforced():
    assert (
        fracture_toughness_test_evidence(payload(caller_validity_evidence_reviewed=False)).status
        == "needs_data"
    )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.fracture_toughness_test_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="test clock"),
        )
