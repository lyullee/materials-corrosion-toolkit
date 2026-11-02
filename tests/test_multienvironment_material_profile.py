from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.multienvironment_material_profile import (
    MultiEnvironmentMaterialAssessment,
    MultiEnvironmentMaterialAssessmentResult,
    assess_multienvironment_material,
)

SHA = "a" * 64


def ev(label):
    return {"source_id": label, "origin": "user_declared", "citation": label, "sha256": SHA}


def identity(kind):
    values = {
        "material_state_id": f"state-{kind}",
        "material_kind": kind,
        "material_grade_id": "grade-1",
        "material_condition_id": "condition-1",
        "material_lot_id": "lot-1",
        "manufacturing_condition_id": "manufacturing-1",
        "identity_reviewed": True,
        "evidence": (ev("identity"),),
    }
    if kind == "composite":
        values.update({"resin_id": "resin-1", "fiber_id": "fiber-1", "layup_id": "layup-1"})
    if kind == "seal":
        values["seal_geometry_id"] = "seal-geometry-1"
    return values


def envelope(envelope_id, environment, media, component):
    return {
        "envelope_id": envelope_id,
        "environment_id": environment,
        "media_id": media,
        "component_id": component,
        "concentration_unit_token": "kg/kg",
        "minimum_concentration": 0.0,
        "maximum_concentration": 0.1,
        "minimum_temperature_k": 280.0,
        "maximum_temperature_k": 400.0,
        "minimum_absolute_pressure_pa": 0.0,
        "maximum_absolute_pressure_pa": 2_000_000.0,
        "maximum_interval_duration_s": 100.0,
        "allowed_mechanical_state_ids": ("unloaded",),
        "mismatch_disposition": "reject",
    }


def exposure(exposure_id, position, start, environment, media, component):
    return {
        "exposure_id": exposure_id,
        "sequence_position": position,
        "clock_id": "clock-1",
        "start_time_s": start,
        "end_time_s": start + 50.0,
        "environment_id": environment,
        "media_id": media,
        "media_components": ({"component_id": component, "concentration": 0.05, "unit_token": "kg/kg"},),
        "minimum_temperature_k": 300.0,
        "maximum_temperature_k": 350.0,
        "minimum_absolute_pressure_pa": 100_000.0,
        "maximum_absolute_pressure_pa": 1_000_000.0,
        "mechanical_state_id": "unloaded",
        "provider_id": "history-provider",
        "provider_revision": "1",
        "result_digest": SHA,
        "record_valid": True,
        "evidence": (ev(exposure_id),),
    }


def payload(kind="polymer", interpolation="linear", **changes):
    state = identity(kind)
    data = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "material_state": state,
        "exposures": (
            exposure("exposure-1", 1, 0.0, "hot-water", "water", "water"),
            exposure("exposure-2", 2, 50.0, "chloride", "brine", "chloride"),
        ),
        "property_observations": (
            {
                "observation_id": "retention-1",
                "material_state_id": state["material_state_id"],
                "linked_exposure_ids": ("exposure-1", "exposure-2"),
                "exposure_time_s": 150.0,
                "metric_kind": "property_retention",
                "metric_id": "tensile_strength_retention",
                "metric_definition": "caller retained tensile-strength ratio",
                "unit_token": "1",
                "status": "available",
                "value": 0.85,
                "standard_uncertainty": 0.01,
                "method_id": "property-method",
                "provider_id": "property-provider",
                "provider_revision": "1",
                "result_digest": SHA,
                "evidence": (ev("retention"),),
            },
        ),
        "profile": {
            "profile_id": "caller-profile-1",
            "profile_revision": "1",
            "source_digest": SHA,
            "permitted_material_state_ids": (state["material_state_id"],),
            "environment_envelopes": (
                envelope("water-envelope", "hot-water", "water", "water"),
                envelope("chloride-envelope", "chloride", "brine", "chloride"),
            ),
            "property_rules": (
                {
                    "rule_id": "retention-rule",
                    "metric_kind": "property_retention",
                    "metric_id": "tensile_strength_retention",
                    "unit_token": "1",
                    "points": (
                        {"exposure_time_s": 100.0, "minimum_inclusive": 0.8, "maximum_inclusive": 1.0},
                        {"exposure_time_s": 200.0, "minimum_inclusive": 0.7, "maximum_inclusive": 1.0},
                    ),
                    "interpolation_policy": interpolation,
                    "uncertainty_policy": "interval_must_fit",
                    "uncertainty_coverage_factor": 2.0,
                    "missing_or_unsupported_disposition": "review",
                    "rule_description": "caller property-retention envelope",
                },
            ),
            "profile_reviewed": True,
            "evidence": (ev("profile"),),
        },
        "material_resin_matrix_fiber_reinforcement_layup_or_seal_identity_reviewed": True,
        "exposure_clock_media_concentration_temperature_pressure_and_time_reviewed": True,
        "property_metric_units_uncertainty_and_lineage_reviewed": True,
        "caller_profile_authority_envelopes_rules_and_interpolation_reviewed": True,
        "evidence": (ev("assessment"),),
    }
    data.update(changes)
    return MultiEnvironmentMaterialAssessment.model_validate(data)


@pytest.mark.parametrize("kind", ["polymer", "seal", "composite"])
def test_polymer_seal_and_composite_multi_environment_evidence_accepts(kind):
    result = assess_multienvironment_material(payload(kind))
    assert result.disposition == "accept"
    retention = next(row for row in result.findings if row.rule_id == "retention-rule")
    assert retention.evaluated_lower == pytest.approx(0.83)
    assert "linear interpolation" in retention.basis
    assert not result.compatibility_table_or_standard_limit_claim
    assert not result.qualification_or_physical_validation_claim


def test_interpolation_occurs_only_when_explicit_and_environment_can_reject():
    reviewed = assess_multienvironment_material(payload(interpolation="none"))
    assert reviewed.disposition == "review"
    assert any("interpolation not explicitly supported" in row.basis for row in reviewed.findings)

    rows = list(payload().exposures)
    rows[1] = rows[1].model_copy(update={"maximum_temperature_k": 450.0})
    rejected = assess_multienvironment_material(payload(exposures=tuple(rows)))
    assert rejected.disposition == "reject"


def test_exact_unit_and_missing_review_are_insufficient_evidence():
    value = payload().model_dump(mode="python")
    value["property_observations"][0]["unit_token"] = "percent"
    result = assess_multienvironment_material(MultiEnvironmentMaterialAssessment.model_validate(value))
    assert result.disposition == "insufficient_evidence"

    result = assess_multienvironment_material(
        payload(property_metric_units_uncertainty_and_lineage_reviewed=False)
    )
    assert result.disposition == "insufficient_evidence"


def test_identity_and_clock_links_are_strict():
    with pytest.raises(ValidationError, match="seal geometry"):
        MultiEnvironmentMaterialAssessment.model_validate(
            {
                **payload("seal").model_dump(mode="python"),
                "material_state": {**identity("polymer"), "material_kind": "seal"},
            }
        )
    rows = list(payload().exposures)
    rows[1] = rows[1].model_copy(update={"clock_id": "different"})
    with pytest.raises(ValidationError, match="one nonoverlapping"):
        payload(exposures=tuple(rows))


def test_deterministic_digest_round_trip_and_tamper_detection():
    first = assess_multienvironment_material(payload("composite"))
    second = assess_multienvironment_material(payload("composite"))
    assert first.result_digest == second.result_digest
    assert MultiEnvironmentMaterialAssessmentResult.model_validate_json(first.model_dump_json()) == first
    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        MultiEnvironmentMaterialAssessmentResult.model_validate(changed)
