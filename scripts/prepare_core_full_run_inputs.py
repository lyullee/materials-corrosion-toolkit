"""Build project-authored execution cases; keep generated file paths in ignored artifacts."""

import copy
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0, str(ROOT / "tests"))
    inputs = {}
    factories = [
        ("inspection.homogeneous_fmc_tfm", "tests/test_fmc_tfm.py", "request"),
        ("inspection.planar_multiview_fmc_tfm", "tests/test_planar_multiview_tfm.py", "request"),
        ("fabrication.friction_resolved_bolt_torque", "tests/test_blind_hole_and_bolt_torque.py", "torque"),
        (
            "degradation.device_pressure_drop_cavitation_index",
            "tests/test_flow_descriptor_arithmetic.py",
            "cavitation",
        ),
        ("welding.well_mixed_gas_purge", "tests/test_well_mixed_gas_purge.py", "request"),
        (
            "structural.declared_pressure_thickness_relation",
            "examples/declared_pressure_thickness.py",
            "request",
        ),
        (
            "fatigue.critical_plane_findley_calibrated_life",
            "examples/findley_calibrated_life.py",
            "build_synthetic_request",
        ),
        (
            "integration.crevice_component_state_bdf",
            "tests/test_crevice_component_state_bdf_kinetics.py",
            "build_synthetic_request",
        ),
    ]
    for model, path, function in factories:
        value = runpy.run_path(str(ROOT / path))[function]()
        inputs[model] = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    b = json.loads((ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8"))[
        "model_inputs"
    ]
    inputs.update(runpy.run_path(str(ROOT / "examples/core_full_execution_cases.py"))["sample_requests"]())
    inputs["fatigue.sampled_stress_invariant_history"] = b["fatigue.multiaxial_sines_mean_limit_screen"][
        "stress_history"
    ]
    inputs["thermo.coolprop_pure_water_saturated_vapor_fugacity"] = b[
        "thermo.coolprop_pure_water_saturated_vapor_fugacity"
    ] | {"wall_temperature_K": 300.0}
    inputs["thermo.coolprop_pure_water_single_phase_state"] = b[
        "thermo.coolprop_pure_water_single_phase_state"
    ] | {"temperature_K": 300.0, "pressure_Pa": 100000.0}
    for model, changes in [
        (
            "degradation.wet_co2_gas_side_mass_transfer",
            dict(
                gas_mean_velocity_m_s=10.0,
                gas_density_kg_m3=1.0,
                gas_dynamic_viscosity_Pa_s=1e-5,
                co2_gas_diffusivity_m2_s=1e-5,
                hydraulic_diameter_m=0.1,
                gas_wall_shear_stress_Pa=0.1,
            ),
        ),
        (
            "degradation.wet_co2_liquid_side_mass_transfer",
            dict(
                liquid_mean_velocity_m_s=1.0,
                liquid_density_kg_m3=1000.0,
                liquid_dynamic_viscosity_Pa_s=0.001,
                corrosive_species_diffusivity_m2_s=1e-9,
                hydraulic_diameter_m=0.1,
                liquid_wall_shear_stress_Pa=3.0,
            ),
        ),
    ]:
        inputs[model] = copy.deepcopy(b[model])
        inputs[model].update(changes)
        for evidence in inputs[model]["evidence"]:
            evidence.update(
                origin="synthetic",
                citation="Project-authored turbulent-flow execution fixture; not empirical data.",
            )
    model = "fabrication.gasket_multi_bolt_sector_equilibrium"
    inputs[model] = copy.deepcopy(b[model])
    inputs[model]["gasket_sectors"][0]["initial_compression_m"] = 0.0002
    inputs[model].update(minimum_opening_m=-0.0001, maximum_opening_m=0.0002)
    inputs[model]["gasket_sectors"][0]["force_compression_curve"].append(
        dict(compression_m=0.0004, compressive_force_N=40000.0)
    )
    model = "transport.crevice_spatial_activity_solid_nernst_planck_1d"
    inputs[model] = copy.deepcopy(b[model])
    for knot in inputs[model]["chemistry_by_knot"]:
        for cell in knot["cells"]:
            cell["aqueous_activity_input"]["maximum_outer_iterations"] = 100
    from matintegrity.contracts import canonical_digest
    from matintegrity.models.gasket_leakage_calibration import GasketLeakageHistory

    model = "integration.gasket_leakage_pressure_inventory_decay"
    inputs[model] = copy.deepcopy(b[model])
    payload = inputs[model]
    payload["leakage_history"]["mean_contact_pressure_history_Pa"] = [[500000.0], [500000.0]]
    history = GasketLeakageHistory.model_validate_json(json.dumps(payload["leakage_history"]))
    record = {
        key: payload[key]
        for key in (
            "provider_id",
            "provider_revision",
            "gas_volume_m3",
            "gas_temperature_K",
            "downstream_absolute_pressure_Pa",
            "initial_upstream_absolute_pressure_Pa",
        )
    }
    record["leakage_history_sha256"] = canonical_digest(history.model_dump(mode="json"))
    payload["inventory_record_sha256"] = canonical_digest(record)
    for item in payload["evidence"]:
        item["sha256"] = payload["inventory_record_sha256"]
    for model in ("fatigue.papadopoulos_p1_calibrated_life", "fatigue.papadopoulos_p1_miner_blocks"):
        inputs[model] = copy.deepcopy(b[model])
        requests = (
            [inputs[model]["p1_request"]]
            if "p1_request" in inputs[model]
            else [block["p1_request"] for block in inputs[model]["blocks"]]
        )
        for request in requests:
            request["shear_systems"][0].update(
                plane_normal=[0.0, 0.0, 1.0], in_plane_shear_direction=[1.0, 0.0, 0.0]
            )
    factory = runpy.run_path(str(ROOT / "tests/test_file_fmc_tfm.py"))["frame"]
    for planar in (False, True):
        folder = ROOT / "tmp/full_run_frames" / str(planar)
        folder.mkdir(parents=True, exist_ok=True)
        value = factory(folder, planar=planar)
        inputs[
            "inspection.file_planar_multiview_fmc_tfm" if planar else "inspection.file_homogeneous_fmc_tfm"
        ] = value.model_dump(mode="json")
    # Reuse an already validated nested request only when its exact public
    # input class matches; no inference from field names or numeric shapes.
    from pydantic import BaseModel

    from matintegrity.registry import default_registry

    registry = default_registry()
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    targets = json.loads((ROOT / "tests/data/core_physics_full_run_targets.json").read_text(encoding="utf8"))[
        "groups"
    ]
    target_ids = {m for group in targets for m in group["model_ids"]}
    wanted = {
        registry._models[m].input_type: m
        for m in target_ids
        if m not in inputs and m not in b and m not in examples
    }

    def visit(value):
        if isinstance(value, BaseModel):
            if type(value) in wanted:
                inputs[wanted[type(value)]] = value.model_dump(mode="json")
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, (tuple, list)):
            for child in value:
                if isinstance(child, (BaseModel, tuple, list, dict)):
                    visit(child)
        elif isinstance(value, dict):
            for child in value.values():
                if isinstance(child, (BaseModel, tuple, list, dict)):
                    visit(child)

    for model, payload in list(b.items()) + list(examples.items()) + list(inputs.items()):
        if model not in registry._models:
            continue
        try:
            request = registry._models[model].input_type.model_validate_json(json.dumps(payload))
        except ValueError:
            continue
        visit(request)
    output = ROOT / "artifacts/validation/full_core_calculations"
    output.mkdir(parents=True, exist_ok=True)
    (output / "execution_inputs.local.json").write_text(
        json.dumps(
            {
                "basis": "Project-authored synthetic software execution only; generated absolute file paths are local-only.",
                "model_inputs": inputs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    print(f"prepared synthetic execution cases: {len(inputs)}")


if __name__ == "__main__":
    main()
