import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_spray import (
    ThermalSprayConditionAssessment,
    specifications,
    thermal_spray_condition,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def observation(observation_id, partition, source_group, specimen, value):
    return {
        "observation_id": observation_id,
        "region_id": "region-1",
        "physical_specimen_id": specimen,
        "source_group_id": source_group,
        "partition": partition,
        "metric_id": "porosity",
        "metric_kind": "porosity_fraction",
        "metric_definition": "reviewed area fraction",
        "value": value,
        "expanded_uncertainty": 0.01,
        "unit_token": "1",
        "method_id": "method-1",
        "provider_id": "provider-1",
        "provider_version": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    value = {
        "assessment_id": "spray-1",
        "asset_id": "asset-1",
        "location_id": "surface-1",
        "coating_system_id": "system-1",
        "spray_process_id": "process-1",
        "feedstock_lot_id": "lot-1",
        "substrate_material_condition_id": "substrate-1",
        "procedure_id": "procedure-1",
        "procedure_revision": "1",
        "procedure_state_digest": DIGEST_A,
        "regions": (
            {
                "region_id": "region-1",
                "physical_scope_id": "scope-1",
                "nominal_area_m2": 2.0,
                "examined_area_m2": 1.0,
                "surface_preparation_id": "prep-1",
                "deposition_pass_group_id": "passes-1",
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": (
            observation("q-1", "qualification", "q-group", "q-specimen", 0.04),
            observation("p-1", "production", "p-group", "p-specimen", 0.05),
        ),
        "declared_requirements": (
            {
                "requirement_id": "porosity-limit",
                "metric_id": "porosity",
                "metric_kind": "porosity_fraction",
                "metric_definition": "reviewed area fraction",
                "applicable_region_ids": ("region-1",),
                "required_partitions": ("qualification", "production"),
                "comparator": "maximum",
                "limit_value": 0.08,
                "unit_token": "1",
                "authority_basis": "caller-owned requirement",
                "evidence": (EVIDENCE,),
            },
        ),
        "system_and_lot_identity_reviewed": True,
        "surface_preparation_and_pass_traceability_reviewed": True,
        "region_coverage_reviewed": True,
        "measurement_methods_reviewed": True,
        "uncertainty_and_provider_lineage_reviewed": True,
        "requirement_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ThermalSprayConditionAssessment(**value)


def test_partitioned_comparisons_and_coverage():
    result = thermal_spray_condition(payload())
    assert result.status == "computed"
    assert result.values["examined_area_fraction"] == pytest.approx(0.5)
    assert all(
        row["all_observations_satisfy_declared_requirement"] for row in result.values["comparison_rows"]
    )


def test_caller_limit_excursion_is_visible_without_acceptance_claim():
    assessment = payload()
    changed = tuple(
        row.model_copy(update={"value": 0.09}) if row.partition == "production" else row
        for row in assessment.observations
    )
    result = thermal_spray_condition(assessment.model_copy(update={"observations": changed}))
    assert result.status == "computed"
    assert result.values["comparison_rows"][1]["all_observations_satisfy_declared_requirement"] is False


def test_missing_partition_and_source_group_leak_are_rejected_or_reported():
    assessment = payload()
    result = thermal_spray_condition(
        assessment.model_copy(update={"observations": (assessment.observations[0],)})
    )
    assert result.status == "needs_data"
    with pytest.raises(ValueError, match="source groups"):
        payload(
            observations=(
                observation("q-1", "qualification", "same", "q-specimen", 0.04),
                observation("p-1", "production", "same", "p-specimen", 0.05),
            )
        )


def test_review_and_context_identity_are_enforced():
    assert thermal_spray_condition(payload(measurement_methods_reviewed=False)).status == "needs_data"
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.thermal_spray_condition",
            payload(),
            RunContext(asset_id="other", location_id="surface-1", time_basis="authored"),
        )
