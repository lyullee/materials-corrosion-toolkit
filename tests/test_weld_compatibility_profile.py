from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.weld_compatibility_profile import (
    WeldCompatibilityAssessment,
    WeldCompatibilityAssessmentResult,
    assess_weld_compatibility,
)

SHA = "a" * 64


def evidence(label):
    return {
        "source_id": label,
        "origin": "user_declared",
        "citation": f"caller evidence {label}",
        "sha256": SHA,
    }


def fact(fact_id, subject_id, kind, metric, value, unit, uncertainty=0.001, status="available"):
    return {
        "fact_id": fact_id,
        "subject_id": subject_id,
        "fact_kind": kind,
        "metric_id": metric,
        "metric_definition": f"caller definition for {metric}",
        "unit_token": unit,
        "status": status,
        "value": value if status == "available" else None,
        "standard_uncertainty": uncertainty if status == "available" else None,
        "missing_or_invalid_basis": None if status == "available" else "caller record unavailable",
        "provider_id": "caller-lab",
        "provider_revision": "1",
        "result_digest": SHA if status == "available" else None,
        "evidence": (evidence(fact_id),),
    }


def material(subject, role, material_id, consumable=None, facts=None):
    return {
        "material_subject_id": subject,
        "material_role": role,
        "material_id": material_id,
        "material_condition_id": "as-declared",
        "material_lot_id": f"lot-{subject}",
        "consumable_id": consumable,
        "facts": facts or (fact(f"property-{subject}", subject, "property", "hardness", 200.0, "HV"),),
        "identity_reviewed": True,
        "evidence": (evidence(subject),),
    }


def profile(maximum_chromium=0.25):
    return {
        "profile_id": "caller-profile-1",
        "profile_revision": "2",
        "profile_kind": "tabulated_envelope",
        "profile_source_digest": SHA,
        "applicable_assessment_kinds": (
            "dissimilar_weld",
            "overlay_cladding",
            "consumable_selection",
        ),
        "permitted_layer_role_sequences": (("filler", "overlay"),),
        "sequence_mismatch_disposition": "reject",
        "rules": (
            {
                "rule_kind": "numeric_envelope",
                "rule_id": "caller-filler-chromium-envelope",
                "target_kind": "material_role",
                "target_value": "filler",
                "fact_kind": "chemistry",
                "metric_id": "chromium_mass_fraction",
                "unit_token": "kg/kg",
                "minimum_inclusive": 0.15,
                "maximum_inclusive": maximum_chromium,
                "uncertainty_policy": "interval_must_fit",
                "uncertainty_coverage_factor": 2.0,
                "missing_fact_disposition": "insufficient_evidence",
                "rule_description": "caller tabulated filler chemistry envelope",
            },
            {
                "rule_kind": "numeric_envelope",
                "rule_id": "caller-overlay-dilution-envelope",
                "target_kind": "layer_position",
                "target_value": "2",
                "fact_kind": "dilution",
                "metric_id": "caller_dilution_fraction",
                "unit_token": "1",
                "minimum_inclusive": 0.0,
                "maximum_inclusive": 0.2,
                "uncertainty_policy": "point_value",
                "missing_fact_disposition": "review",
                "rule_description": "caller tabulated dilution envelope",
            },
            {
                "rule_kind": "identity_envelope",
                "rule_id": "caller-consumable-envelope",
                "target_kind": "material_role",
                "target_value": "filler",
                "identity_field": "consumable_id",
                "allowed_values": ("consumable-1",),
                "mismatch_disposition": "reject",
                "rule_description": "caller consumable identity list",
            },
        ),
        "profile_reviewed": True,
        "evidence": (evidence("profile"),),
    }


def payload(kind="dissimilar_weld", **changes):
    materials = (
        material("base-a", "base_a", "material-a"),
        material("base-b", "base_b", "material-b"),
        material(
            "filler-1",
            "filler",
            "filler-material",
            consumable="consumable-1",
            facts=(
                fact(
                    "filler-cr",
                    "filler-1",
                    "chemistry",
                    "chromium_mass_fraction",
                    0.20,
                    "kg/kg",
                    0.005,
                ),
            ),
        ),
        material("overlay-1", "overlay", "overlay-material"),
    )
    data = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "assessment_kind": kind,
        "materials": materials,
        "layers": (
            {
                "layer_id": "layer-1",
                "sequence_position": 1,
                "layer_role": "filler",
                "material_subject_id": "filler-1",
                "process_id": "process-1",
                "procedure_id": "procedure-1",
                "dilution_parent_subject_ids": ("base-a", "base-b"),
                "facts": (),
                "sequence_and_parentage_reviewed": True,
                "evidence": (evidence("layer-1"),),
            },
            {
                "layer_id": "layer-2",
                "sequence_position": 2,
                "layer_role": "overlay",
                "material_subject_id": "overlay-1",
                "process_id": "process-2",
                "procedure_id": "procedure-2",
                "dilution_parent_subject_ids": ("filler-1",),
                "facts": (
                    fact(
                        "layer-dilution",
                        "layer-2",
                        "dilution",
                        "caller_dilution_fraction",
                        0.10,
                        "1",
                        0.01,
                    ),
                ),
                "sequence_and_parentage_reviewed": True,
                "evidence": (evidence("layer-2"),),
            },
        ),
        "service_environment": {
            "service_environment_id": "service-1",
            "environment_definition": "caller-defined process environment",
            "minimum_temperature_k": 290.0,
            "maximum_temperature_k": 500.0,
            "maximum_absolute_pressure_pa": 2_000_000.0,
            "medium_component_ids": ("water", "chloride"),
            "facts": (),
            "environment_reviewed": True,
            "evidence": (evidence("service-1"),),
        },
        "profile": profile(),
        "material_fact_units_uncertainty_and_lineage_reviewed": True,
        "layer_sequence_parentage_and_dilution_facts_reviewed": True,
        "service_environment_and_fact_support_reviewed": True,
        "profile_authority_applicability_and_plugin_identity_reviewed": True,
        "evidence": (evidence("assessment"),),
    }
    data.update(changes)
    return WeldCompatibilityAssessment.model_validate(data)


@pytest.mark.parametrize("kind", ["dissimilar_weld", "overlay_cladding", "consumable_selection"])
def test_all_three_assessment_kinds_accept_only_with_caller_profile(kind):
    result = assess_weld_compatibility(payload(kind))
    assert result.disposition == "accept"
    assert result.assessment_kind == kind
    assert all(row.outcome == "pass" for row in result.findings)
    assert not result.code_standard_or_diagram_qualification_claim
    assert not result.physical_validation_claim


def test_uncertainty_interval_identity_and_sequence_rules_can_reject():
    rejected = assess_weld_compatibility(payload(profile=profile(maximum_chromium=0.205)))
    assert rejected.disposition == "reject"
    chemistry = next(row for row in rejected.findings if row.rule_id == "caller-filler-chromium-envelope")
    assert chemistry.evaluated_upper == pytest.approx(0.21)
    assert chemistry.outcome == "fail"

    layers = tuple(reversed(payload().layers))
    renumbered = tuple(
        row.model_copy(update={"sequence_position": index}) for index, row in enumerate(layers, start=1)
    )
    sequence_reject = assess_weld_compatibility(payload(layers=renumbered))
    assert sequence_reject.disposition == "reject"


def test_missing_fact_review_and_insufficient_evidence_are_distinct():
    values = payload().model_dump(mode="python")
    values["layers"][1]["facts"][0]["status"] = "missing"
    values["layers"][1]["facts"][0]["value"] = None
    values["layers"][1]["facts"][0]["standard_uncertainty"] = None
    values["layers"][1]["facts"][0]["result_digest"] = None
    values["layers"][1]["facts"][0]["missing_or_invalid_basis"] = "not measured"
    reviewed = assess_weld_compatibility(WeldCompatibilityAssessment.model_validate(values))
    assert reviewed.disposition == "review"

    incomplete = assess_weld_compatibility(
        payload(material_fact_units_uncertainty_and_lineage_reviewed=False)
    )
    assert incomplete.disposition == "insufficient_evidence"


def test_plugin_profile_identity_and_exact_units_are_strict():
    plugin = profile()
    plugin["profile_kind"] = "plugin_style_rules"
    with pytest.raises(ValidationError, match="plugin-style"):
        payload(profile=plugin)

    plugin.update(
        {
            "plugin_adapter_id": "caller-plugin-adapter",
            "plugin_adapter_revision": "1",
            "plugin_configuration_digest": SHA,
        }
    )
    assert assess_weld_compatibility(payload(profile=plugin)).disposition == "accept"

    bad = profile()
    rules = list(bad["rules"])
    rules[0] = {**rules[0], "unit_token": "mass_percent"}
    bad["rules"] = tuple(rules)
    result = assess_weld_compatibility(payload(profile=bad))
    assert result.disposition == "insufficient_evidence"


def test_deterministic_digest_is_traceable_and_tamper_evident():
    first = assess_weld_compatibility(payload())
    second = assess_weld_compatibility(payload())
    assert first.input_digest == second.input_digest
    assert first.result_digest == second.result_digest
    assert WeldCompatibilityAssessmentResult.model_validate_json(first.model_dump_json()) == first

    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        WeldCompatibilityAssessmentResult.model_validate(changed)
