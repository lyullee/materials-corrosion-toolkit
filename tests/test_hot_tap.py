import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hot_tap import HotTapApplicability, hot_tap_applicability, specifications
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def result(metric_id, result_kind, value, unit):
    return {
        "result_id": f"result-{metric_id}",
        "result_kind": result_kind,
        "metric_id": metric_id,
        "metric_definition": f"authored {metric_id}",
        "reported_value": value,
        "unit_token": unit,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "input_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def metric_support(metric_id, result_kind, unit, minimum, maximum):
    return {
        "result_kind": result_kind,
        "metric_id": metric_id,
        "unit_token": unit,
        "minimum_supported_value": minimum,
        "maximum_supported_value": maximum,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "support_basis": "authored support",
    }


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "host_pipe_id": "pipe-1",
        "host_material_condition_id": "material-1",
        "pressure_basis": "absolute_internal_pressure",
        "minimum_operating_pressure_Pa": 100000.0,
        "maximum_operating_pressure_Pa": 5000000.0,
        "minimum_operating_temperature_K": 280.0,
        "maximum_operating_temperature_K": 400.0,
        "minimum_wall_thickness_m": 0.005,
        "maximum_wall_thickness_m": 0.03,
        "supported_flow_heat_extraction_descriptors": ("flowing-product-a",),
        "supported_branch_geometry_ids": ("branch-geometry-1",),
        "supported_joint_geometry_ids": ("joint-geometry-1",),
        "supported_welding_process_ids": ("process-1",),
        "supported_consumable_condition_ids": ("consumable-1",),
        "supported_hydrogen_control_descriptors": ("control-1",),
        "provider_metric_support": (
            metric_support(
                "thermal-margin", "thermal_or_burn_through_screen", "custom-temperature", 0.0, 500.0
            ),
            metric_support("hydrogen-index", "hydrogen_cracking_screen", "custom-index", 0.0, 1.0),
        ),
        "qualification_evidence": (
            {
                "evidence_record_id": "evidence-1",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "partition": "qualification",
                "supported_metric_ids": ("thermal-margin", "hydrogen-index"),
                "method_id": "method-1",
                "provider_id": "provider-1",
                "provider_revision": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_D,
                "expanded_uncertainty": 0.05,
                "uncertainty_unit_token": "custom-uncertainty",
                "record_valid": True,
                "supports_declared_envelope": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "minimum_qualification_source_group_count": 1,
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "hot-tap-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "host_pipe_id": "pipe-1",
        "host_material_condition_id": "material-1",
        "pressure_basis": "absolute_internal_pressure",
        "operating_pressure_Pa": 2000000.0,
        "operating_temperature_K": 320.0,
        "wall_thickness_m": 0.01,
        "flow_heat_extraction_descriptor": "flowing-product-a",
        "branch_geometry_id": "branch-geometry-1",
        "joint_geometry_id": "joint-geometry-1",
        "welding_process_id": "process-1",
        "consumable_condition_id": "consumable-1",
        "hydrogen_control_descriptor": "control-1",
        "provider_results": (
            result("thermal-margin", "thermal_or_burn_through_screen", 200.0, "custom-temperature"),
            result("hydrogen-index", "hydrogen_cracking_screen", 0.2, "custom-index"),
        ),
        "candidate_envelopes": (envelope(),),
        "host_pipe_material_and_condition_reviewed": True,
        "operating_pressure_basis_and_temperature_reviewed": True,
        "wall_thickness_and_geometry_reviewed": True,
        "flow_and_heat_extraction_reviewed": True,
        "welding_process_consumable_and_hydrogen_control_reviewed": True,
        "provider_results_units_and_support_reviewed": True,
        "qualification_specimens_and_source_groups_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return HotTapApplicability(**value)


def test_reviewed_case_is_within_caller_support():
    computed = hot_tap_applicability(payload())
    assert computed.status == "computed"
    assert computed.values["declared_applicability_outcome"] == "within_support"
    assert computed.values["qualification_source_group_count"] == 1


def test_geometry_and_provider_range_outside_support_are_visible():
    outside_results = (
        result("thermal-margin", "thermal_or_burn_through_screen", 700.0, "custom-temperature"),
        result("hydrogen-index", "hydrogen_cracking_screen", 0.2, "custom-index"),
    )
    assessed = hot_tap_applicability(
        payload(branch_geometry_id="other-branch", provider_results=outside_results)
    )
    assert assessed.status == "out_of_scope"
    assert assessed.values["outside_metric_ids"] == ["thermal-margin"]
    assert assessed.values["outside_support_reasons"] == [
        "branch_geometry_id",
        "provider_metric_range",
    ]


def test_missing_review_or_provider_identity_mismatch_needs_data():
    assert hot_tap_applicability(payload(flow_and_heat_extraction_reviewed=False)).status == "needs_data"
    mismatched = result("hydrogen-index", "hydrogen_cracking_screen", 0.2, "custom-index")
    mismatched["provider_revision"] = "other"
    assessed = hot_tap_applicability(
        payload(
            provider_results=(
                result("thermal-margin", "thermal_or_burn_through_screen", 200.0, "custom-temperature"),
                mismatched,
            )
        )
    )
    assert assessed.status == "needs_data"
    assert assessed.values["unit_or_provider_mismatch_ids"] == ["hydrogen-index"]


def test_result_kind_completeness_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="both provider result kinds"):
        payload(
            provider_results=(
                result("thermal-a", "thermal_or_burn_through_screen", 1.0, "u"),
                result("thermal-b", "thermal_or_burn_through_screen", 2.0, "u"),
            )
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.hot_tap_applicability",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
