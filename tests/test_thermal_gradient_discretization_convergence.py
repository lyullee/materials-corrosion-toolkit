import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_gradient_discretization_convergence import (
    ThermalGradientDiscretizationConvergence,
    specifications,
    thermal_gradient_discretization_convergence,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored refinement test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64
DIGEST_F = "f" * 64


def query_result(identifier, temperature, digest):
    return {
        "query_id": identifier,
        "temperature_K": temperature,
        "provider_query_result_digest": digest,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }


def level(identifier, ordinal, relationship, size, step, scale, temperatures, **updates):
    row = {
        "level_id": identifier,
        "ordinal": ordinal,
        "relationship_to_previous": relationship,
        "spatial_characteristic_size_m": size,
        "maximum_time_step_s": step,
        "spatial_cell_count": 10 * 2**ordinal,
        "time_step_count": 20 * 2**ordinal,
        "refinement_path_scale": scale,
        "mesh_id": f"mesh-{ordinal}",
        "mesh_digest": DIGEST_A,
        "time_step_schedule_id": f"time-{ordinal}",
        "time_step_digest": DIGEST_B,
        "provider_input_digest": DIGEST_C,
        "provider_result_digest": DIGEST_D,
        "level_record_digest": DIGEST_E,
        "query_temperatures": (
            query_result("q-1", temperatures[0], DIGEST_A),
            query_result("q-2", temperatures[1], DIGEST_B),
        ),
        "level_record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def payload(**updates):
    row = {
        "comparison_id": "thermal-refinement-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "physical_scope_definition": "reviewed external transient solver scope",
        "time_basis": "solver elapsed seconds",
        "geometry_id": "geometry-1",
        "geometry_digest": DIGEST_A,
        "boundary_condition_id": "boundary-1",
        "boundary_condition_digest": DIGEST_B,
        "material_property_state_id": "property-state-1",
        "material_property_state_digest": DIGEST_C,
        "provider_id": "provider-1",
        "solver_id": "solver-1",
        "solver_revision": "rev-1",
        "provider_configuration_digest": DIGEST_D,
        "common_queries": (
            {
                "query_id": "q-1",
                "elapsed_time_s": 5.0,
                "position_m": 0.1,
                "query_definition": "temperature at first reviewed coordinate",
                "comparison_weight": 1.0,
                "evidence": (EVIDENCE,),
            },
            {
                "query_id": "q-2",
                "elapsed_time_s": 10.0,
                "position_m": 0.2,
                "query_definition": "temperature at second reviewed coordinate",
                "comparison_weight": 1.0,
                "evidence": (EVIDENCE,),
            },
        ),
        "refinement_levels": (
            level("coarse", 0, "initial", 0.1, 1.0, 1.0, (300.0, 320.0)),
            level("medium", 1, "nested_refinement", 0.05, 0.5, 0.5, (302.0, 318.0)),
            level("fine", 2, "nested_refinement", 0.025, 0.25, 0.25, (303.0, 317.0)),
        ),
        "refinement_path_scale_definition": "caller dimensionless joint space-time path coordinate",
        "temperature_change_normalization_scale_K": 100.0,
        "maximum_adjacent_weighted_rms_change_K": 1.5,
        "maximum_adjacent_relative_rms_change": 0.02,
        "observed_order_refinement_ratio_tolerance": 1e-9,
        "geometry_boundary_property_and_provider_identity_reviewed": True,
        "input_result_mesh_and_time_step_digests_reviewed": True,
        "common_query_identity_units_and_weights_reviewed": True,
        "refinement_order_and_relationships_reviewed": True,
        "refinement_path_scale_definition_reviewed": True,
        "level_validity_and_missingness_reviewed": True,
        "diagnostic_norm_tolerances_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ThermalGradientDiscretizationConvergence.model_validate(row)


def test_adjacent_norms_rates_and_observed_order_are_diagnostic():
    result = thermal_gradient_discretization_convergence(payload())
    assert result.status == "computed"
    first, second = result.values["adjacent_level_diagnostics"]
    assert first["weighted_signed_temperature_change_K"] == pytest.approx(0.0)
    assert first["weighted_rms_temperature_change_K"] == pytest.approx(2.0)
    assert first["maximum_absolute_temperature_change_K"] == pytest.approx(2.0)
    assert first["weighted_rms_change_per_refinement_path_scale_K"] == pytest.approx(4.0)
    assert second["weighted_rms_temperature_change_K"] == pytest.approx(1.0)
    order = result.values["observed_order_diagnostics"][0]
    assert order["diagnostic_observed_order"] == pytest.approx(1.0)
    assert result.values["all_adjacent_levels_meet_declared_rms_diagnostics"] is False


def test_unequal_refinement_ratios_withhold_observed_order():
    data = payload().model_dump()
    data["refinement_levels"][2]["refinement_path_scale"] = 0.2
    result = thermal_gradient_discretization_convergence(
        ThermalGradientDiscretizationConvergence.model_validate(data)
    )
    order = result.values["observed_order_diagnostics"][0]
    assert order["diagnostic_observed_order"] is None
    assert "ratios differ" in order["observed_order_unavailable_basis"]


def test_invalid_results_or_missing_review_need_data():
    assert (
        thermal_gradient_discretization_convergence(
            payload(level_validity_and_missingness_reviewed=False)
        ).status
        == "needs_data"
    )
    data = payload().model_dump()
    data["refinement_levels"][1]["query_temperatures"][0]["record_valid"] = False
    data["refinement_levels"][1]["query_temperatures"][0]["invalid_or_missing_basis"] = (
        "reviewed provider failure"
    )
    result = thermal_gradient_discretization_convergence(
        ThermalGradientDiscretizationConvergence.model_validate(data)
    )
    assert result.status == "needs_data"
    assert result.values["invalid_query_result_ids"] == ["medium:q-1"]


def test_refinement_order_and_complete_common_queries_are_strict():
    data = payload().model_dump()
    data["refinement_levels"][1]["maximum_time_step_s"] = 2.0
    with pytest.raises(ValueError, match="maximum time step cannot increase"):
        ThermalGradientDiscretizationConvergence.model_validate(data)

    data = payload().model_dump()
    data["refinement_levels"][2]["query_temperatures"] = data["refinement_levels"][2]["query_temperatures"][
        :-1
    ]
    with pytest.raises(ValueError, match="complete common query set"):
        ThermalGradientDiscretizationConvergence.model_validate(data)


def test_specification_identity_input_source_and_context():
    spec = specifications()[0]
    assert spec.model_id == "structural.thermal_gradient_discretization_convergence"
    assert spec.input_type is ThermalGradientDiscretizationConvergence
    assert spec.source_ids == ("authored_external_thermal_discretization_refinement_diagnostic",)
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="solver elapsed seconds")
    spec.context_validator(payload(), context)
    with pytest.raises(ValueError, match="identity and clock must match"):
        spec.context_validator(
            payload(),
            RunContext(asset_id="asset-1", location_id="other", time_basis="solver elapsed seconds"),
        )
