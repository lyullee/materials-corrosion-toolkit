"""Real registry-path regressions discovered by the complete model inventory run."""

import copy
import json
from pathlib import Path

import pytest
import scipy.integrate
import scipy.optimize

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

BASELINES = json.loads(
    (Path(__file__).parent / "data/core_physics_valid_input_baselines.json").read_text(encoding="utf8")
)["model_inputs"]


@pytest.mark.parametrize(
    "model_id",
    [
        "corrosion.crevice_hydraulic_stage_rhs",
        "fabrication.gasket_prony_relaxation_spectrum_fit",
        "fatigue.dang_van_finite_sample_limit_screen",
        "fatigue.multiaxial_invariant_limit_screen",
        "fatigue.papadopoulos_p2_finite_sample_limit_screen",
        "thermo.co2_mixture_fugacity_history",
        "thermo.co2_pure_fugacity_history",
        "thermo.coolprop_pure_water_saturated_vapor_fugacity",
        "thermo.coolprop_pure_water_single_phase_state",
        "chemistry.crevice_component_solid_partition",
        "integration.wet_co2_cylindrical_stage_speciation_scale_feedback",
        "integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback",
        "transport.crevice_spatial_activity_solid_nernst_planck_1d",
    ],
)
def test_full_json_request_returns_serializable_computed_envelope(model_id):
    registry = default_registry()
    payload = copy.deepcopy(BASELINES[model_id])
    if model_id == "thermo.coolprop_pure_water_saturated_vapor_fugacity":
        payload["wall_temperature_K"] = 300.0
    if model_id == "thermo.coolprop_pure_water_single_phase_state":
        payload.update(temperature_K=300.0, pressure_Pa=100000.0)
    if model_id == "transport.crevice_spatial_activity_solid_nernst_planck_1d":
        for knot in payload["chemistry_by_knot"]:
            for cell in knot["cells"]:
                cell["aqueous_activity_input"]["maximum_outer_iterations"] = 100
    context = RunContext(
        asset_id=payload.get("asset_id", "synthetic"),
        location_id=payload.get("location_id", "synthetic"),
        time_basis=payload.get("time_basis", payload.get("clock_id", "API contract check")),
    )
    dependencies = {name: scipy for name in registry._models[model_id].runtime_dependency_names}
    result = registry.run_json(model_id, json.dumps(payload), context, runtime_dependencies=dependencies)
    assert result.status == "computed", result.values
    assert len(result.input_digest) == 64
    encoded = result.model_dump_json()
    restored = type(result).model_validate_json(encoded)
    assert restored.model_id == model_id
    assert restored.model_dump(mode="json")["values"] == result.model_dump(mode="json")["values"]
