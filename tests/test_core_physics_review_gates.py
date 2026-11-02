"""Review/unit flags must withhold the calculation or output they govern."""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.registry import default_registry

_ROOT = Path(__file__).parent
_BASELINES = json.loads(
    (_ROOT / "data" / "core_physics_valid_input_baselines.json").read_text(encoding="utf-8")
)["model_inputs"]
_PROBES = json.loads(
    (_ROOT / "data" / "core_physics_review_gate_probe_results.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    "model_id,field_name,expected,expected_values",
    [(row[0], row[1], row[2], row[3] if len(row) > 3 else {}) for row in _PROBES],
)
def test_false_review_flag_blocks_its_declared_scope(
    model_id: str, field_name: str, expected: str, expected_values: dict
) -> None:
    if model_id == "fatigue.multiaxial_sines_life_fit":
        # Exercise only the evaluator's review gate. A registry-valid request
        # would imply unavailable specimen identity and local stress histories.
        from matintegrity.multiaxial_sines_life_fit import (
            FIT_SOURCE_ID,
            MultiaxialSinesLifeFit,
            evaluate_multiaxial_sines_life_fit,
        )

        review_fields = (
            "independent_specimen_identity_reviewed",
            "failure_endpoint_and_observation_rights_reviewed",
            "loglog_power_law_form_and_fit_domain_reviewed",
        )
        request = MultiaxialSinesLifeFit.model_construct(
            campaign_id="review-gate-unit-probe",
            material_condition_id="review-gate-unit-probe",
            tests=(),
            fit_source_id=FIT_SOURCE_ID,
            **{name: name != field_name for name in review_fields},
        )
        result = evaluate_multiaxial_sines_life_fit(request)
        assert result.status == expected
        assert result.values["reason"] == "specimen_endpoint_rights_and_loglog_fit_review_required"
        return

    request = json.loads(json.dumps(_BASELINES[model_id]))
    parts = field_name.split(".")
    target = request
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    final = parts[-1]
    if isinstance(target, list):
        target[int(final)] = False
    else:
        target[final] = False
    context = RunContext(
        asset_id=request.get("asset_id", "synthetic"),
        location_id=request.get("location_id", "synthetic"),
        time_basis=request.get(
            "time_basis", request.get("time_basis_id", request.get("clock_id", "input-gate probe"))
        ),
    )
    registry = default_registry()
    dependencies = {}
    if model_id == "fabrication.gasket_prony_relaxation_spectrum_fit":
        import scipy

        dependencies["scipy"] = SimpleNamespace(optimize=scipy.optimize)
    if model_id == "integration.gasket_leakage_pressure_inventory_decay":
        import scipy

        dependencies["scipy"] = SimpleNamespace(integrate=scipy.integrate)
    if model_id == "integration.wet_co2_cylindrical_transient_transport":
        import scipy

        dependencies["scipy"] = SimpleNamespace(integrate=scipy.integrate)
    if model_id == "integration.wet_co2_lumped_wall_thermal_condensation_history":
        import scipy

        dependencies["scipy"] = SimpleNamespace(integrate=scipy.integrate)
    if model_id == "transport.crevice_activity_corrected_reactive_nernst_planck_1d":
        import scipy

        dependencies["scipy"] = SimpleNamespace(integrate=scipy.integrate)
    if model_id == "integration.wet_co2_scale_corrosion_simultaneous_history":
        import scipy

        dependencies["scipy"] = SimpleNamespace(integrate=scipy.integrate)

    if expected.startswith("ERROR"):
        with pytest.raises(ValidationError):
            registry.run_json(model_id, json.dumps(request), context)
        return

    # All registry adapters now return Calculation, including legacy fatigue screens.
    result = registry.run_json(model_id, json.dumps(request), context, runtime_dependencies=dependencies)
    assert result.status == expected
    if field_name == "linear_rupture_time_fraction_reviewed":
        assert result.values["linear_rupture_time_fraction"] is None
    if field_name == "deterministic_rate_bounds_reviewed":
        assert result.values["deterministic_rate_bounds_status"] == "needs_data"
        assert result.values["cumulative_deterministic_loss_bounds"] is None
    if field_name == "wall_thickness_limit_state_reviewed":
        assert result.values["wall_thickness_limit_state"]["status"] == "needs_data"
    for path, expected_value in expected_values.items():
        value = result.values
        for part in path.split("."):
            value = value[part]
        assert value == expected_value


@pytest.mark.parametrize(
    "model_id,field_name,extreme_value",
    [
        ("creep.norton", "stress_Pa", 1e308),
        ("creep.norton", "reference_stress_Pa", 1e-308),
        ("degradation.archard_wear", "dimensionless_wear_coefficient", 1e308),
        ("degradation.archard_wear", "hardness_Pa", 1e-308),
        ("fracture.stress_intensity", "crack_depth_m", 1e308),
        ("fracture.stress_intensity", "geometry_factor", 1e-308),
        ("fracture.stress_intensity", "fracture_toughness_Pa_sqrt_m", 1e308),
        ("materials.ramberg_osgood", "stress_amplitude_Pa", 1e308),
        ("materials.ramberg_osgood", "elastic_modulus_Pa", 1e-308),
        ("materials.ramberg_osgood", "cyclic_strength_coefficient_Pa", 1e-308),
        ("transport.semi_infinite_diffusion", "diffusivity_m2_s", 1e308),
        ("transport.semi_infinite_diffusion", "surface_concentration_mol_m3", 1e308),
    ],
)
def test_finite_extreme_inputs_return_supported_status(
    model_id: str, field_name: str, extreme_value: float
) -> None:
    request = dict(_BASELINES[model_id])
    request[field_name] = extreme_value
    result = default_registry().run_json(
        model_id,
        json.dumps(request, allow_nan=False),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="finite boundary probe"),
    )
    assert result.status in {"computed", "out_of_scope", "needs_data"}
    json.dumps(result.model_dump(mode="json"), allow_nan=False)
    if result.status == "out_of_scope":
        assert result.values == {}
    else:
        assert all(math.isfinite(value) for value in result.values.values() if isinstance(value, float))


def test_unbalanced_ionic_inventory_is_withheld_even_after_reviews() -> None:
    model_id = "chemistry.aqueous_extended_debye_huckel_activity"
    request = dict(_BASELINES[model_id])
    request["species"] = [dict(row) for row in request["species"]]
    request["species"][0]["molality_mol_kg"] = 0.11
    result = default_registry().run_json(
        model_id,
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="input-gate probe"),
    )
    assert result.status == "needs_data"
    assert result.values["out_of_scope_reason"] == "ionic_inventory_charge_balance_tolerance_exceeded"


def test_wang_brown_rainflow_sample_count_mismatch_is_withheld() -> None:
    model_id = "fatigue.wang_brown_temporal_normal_excursion"
    request = dict(_BASELINES[model_id])
    request["projected_rainflow_result"] = json.loads(json.dumps(request["projected_rainflow_result"]))
    request["projected_rainflow_result"]["values"]["sample_count"] = 4
    request["projected_rainflow_result_sha256"] = canonical_digest(request["projected_rainflow_result"])
    result = default_registry().run_json(
        model_id,
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="input-gate probe"),
    )
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "sample_count_mismatch"


@pytest.mark.parametrize(
    "failure,expected_reason",
    [
        ("missing_A_evidence", "missing_or_duplicate_SIT_evidence_source"),
        ("unhashed_A_evidence", "SIT_A_parameter_evidence_missing_sha256"),
    ],
)
def test_competitive_sit_requires_parameter_evidence(failure: str, expected_reason: str) -> None:
    model_id = "chemistry.competitive_solid_sit_equilibrium"
    request = json.loads(json.dumps(_BASELINES[model_id]))
    if failure == "missing_A_evidence":
        request["A_evidence_source_id"] = "undeclared-source"
    else:
        request["evidence"][0]["sha256"] = None
    result = default_registry().run_json(
        model_id,
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="input-gate probe"),
    )
    assert result.status == "needs_data"
    assert result.values["out_of_scope_reason"] == expected_reason


@pytest.mark.parametrize(
    "failure,expected_status,expected_reason",
    [
        ("missing_species_evidence", "needs_data", "Bdot_parameter_evidence_digest_mismatch"),
        ("species_parameter_order", "needs_data", "Bdot_parameters_do_not_match_phase_species_order"),
        ("parameter_temperature", "out_of_scope", "Bdot_parameter_temperature_mismatch"),
    ],
)
def test_competitive_bdot_parameter_lineage_is_enforced(
    failure: str, expected_status: str, expected_reason: str
) -> None:
    model_id = "chemistry.competitive_solid_bdot_equilibrium"
    request = json.loads(json.dumps(_BASELINES[model_id]))
    if failure == "missing_species_evidence":
        request["evidence"] = request["evidence"][:-1]
    elif failure == "species_parameter_order":
        request["species_parameters"][0], request["species_parameters"][1] = (
            request["species_parameters"][1],
            request["species_parameters"][0],
        )
    else:
        request["parameter_temperature_K"] += 10.0
    result = default_registry().run_json(
        model_id,
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="input-gate probe"),
    )
    assert result.status == expected_status
    assert result.values["out_of_scope_reason"] == expected_reason


def test_moving_scale_history_preserves_nested_tuple_contracts_when_updating_film() -> None:
    model_id = "integration.wet_co2_scale_corrosion_moving_geometry_history"
    request = (
        default_registry()
        ._models[model_id]
        .input_type.model_validate_json(json.dumps(_BASELINES[model_id], allow_nan=False))
    )
    result = default_registry()._models[model_id].evaluator(request)
    assert result.status == "computed"
    assert result.values.get("reason") != "evolved_scale_transport_request_invalid"


@pytest.mark.parametrize(
    "model_id,field_name,expected_reason",
    [
        (
            "fabrication.flange_nonlinear_viscoelastic_contact_history",
            "maximum_contact_work_units",
            "nonlinear_spatial_contact_work_budget_exceeded",
        ),
        (
            "fabrication.flange_viscoelastic_contact_history",
            "maximum_contact_work_units",
            "contact_active_set_not_converged_or_work_budget_exceeded",
        ),
    ],
)
def test_runtime_contact_work_budget_is_enforced(
    model_id: str, field_name: str, expected_reason: str
) -> None:
    request = dict(_BASELINES[model_id])
    request[field_name] = 1
    result = default_registry().run_json(
        model_id,
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="runtime budget probe"),
    )
    assert result.status == "out_of_scope"
    assert result.values.get("reason", result.values.get("out_of_scope_reason")) == expected_reason
