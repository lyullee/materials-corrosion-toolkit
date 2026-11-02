"""Generate a complete API reference from executable schemas and authored examples."""

import json
from pathlib import Path

from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXAMPLES = {
    "inspection.impact_metric_crossings": "examples/impact_metric_crossings.py",
    "materials.steel_composition_index": "examples/composition_index_recipe.py",
    "materials.composition_index_recipe": "examples/composition_index_recipe.py",
    **dict.fromkeys(("mechanics.lame_cylinder", "mechanics.plane_stress", "mechanics.thermal_restraint",
        "fracture.stress_intensity", "materials.tensile_point", "materials.ductility_retention",
        "corrosion.charge_to_loss", "thermal.cylindrical_layers", "thermal.lumped_temperature",
        "welding.heat_treatment_history", "welding.cooling_interval", "structural.pressure_temperature_envelope"),
        "examples/reviewed_core_calculations.py"),
    "design.piping_class_assessment": "examples/piping_class.py",
    "inspection.boil_off_calorimetry": "examples/pressure_and_boil_off.py",
    "design.relief_pressure_envelope": "examples/pressure_and_boil_off.py",
    "testing.rockwell_depth": "examples/depth_and_knoop_hardness.py",
    "testing.knoop": "examples/depth_and_knoop_hardness.py",
    "welding.carbon_equivalent_recipe": "examples/engineering_correlations.py",
    "fabrication.measured_pipe_ovality": "examples/engineering_correlations.py",
    "welding.measured_energy_per_length": "examples/engineering_correlations.py",
    "welding.power_travel_energy": "examples/engineering_correlations.py",
    "inspection.pipe_membrane_test_pressure": "examples/engineering_correlations.py",
    "inspection.reference_energy_mass": "examples/engineering_correlations.py",
    "piping.displacement_stress_allowance": "examples/engineering_correlations.py",
    "welding.cooling_time_correlation": "examples/engineering_correlations.py",
    "welding.flux_moisture_hydrogen": "examples/engineering_correlations.py",
    "inspection.coupling_pressure": "examples/engineering_correlations.py",
    "inspection.thread_connection_pressure": "examples/engineering_correlations.py",
    "corrosion.crevice_moving_volume_hydraulic_history": "examples/crevice_moving_volume_hydraulic_history.py",
    "integration.crevice_moving_volume_liquid_continuity": "examples/crevice_moving_volume_continuity.py",
    "integration.aqueous_vant_hoff_saturation_history": "examples/aqueous_vant_hoff_saturation_history.py",
    "integration.electrochemical_wall_thickness_scenario_envelope": "examples/electrochemical_wall_thickness_scenario_envelope.py",
    "fabrication.gasket_leakage_weighted_scenario_moments": "examples/gasket_leakage_weighted_scenario_moments.py",
    "fabrication.gasket_contact_pressure_screen": "examples/gasket_contact_pressure_screen.py",
    "fatigue.critical_plane_findley_calibrated_life": "examples/findley_calibrated_life.py",
    "chemistry.layered_scale_history_stack_transport": "examples/layered_scale_history_stack.py",
}
PYTHON_INPUT_EXAMPLES = {
    "chemistry.competitive_solid_sit_equilibrium": "examples/competitive_solid_sit_equilibrium.py",
    "chemistry.competitive_solid_bdot_equilibrium": "examples/competitive_solid_bdot_equilibrium.py",
    "integration.crevice_solid_volume_hydraulic_stage": "examples/crevice_solid_volume_hydraulic_stage.py",
}


def main():
    registry = default_registry()
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"]
    sources = json.loads((ROOT / "data/catalogs/sources.json").read_text(encoding="utf-8"))["sources"]
    lookup = {row["id"]: row for row in sources}
    lines = [
        "# 계산 모델 API 목록",
        "",
        "이 문서는 `scripts/build_model_reference.py`가 실행 가능한 입력 스키마와 직접 작성한 합성 예제로 생성한다. 입력 숫자는 설명용이며 재료 권장값이나 설계 허용값이 아니다. Python 입력은 `ModelRegistry.run(model_id, inputs, context)`, JSON 입력은 `run_json(model_id, inputs_json, context)`로 호출한다. 상세 수학과 해석 한계는 `METHODS_KO.md`를 함께 읽는다.",
        "",
    ]
    for identifier in registry.list_models():
        description = registry.describe(identifier)
        lines.extend(
            [
                f"## `{identifier}`",
                "",
                " ".join(description["assumptions"]),
                "",
            ]
        )
        if description.get("runtime_dependencies"):
            lines.extend([
                "Runtime 의존성: `" + "`, `".join(description["runtime_dependencies"]) + "` 이름으로 실행 시점에 Python callable/provider를 주입한다. 해당 provider 객체는 JSON 입력에 포함되지 않으며, 입력 계약에 기록한 provider ID·revision·configuration/record digest와 Evidence가 실행계보를 식별한다.",
                "",
            ])
        lines.extend([
                "입력 필드:",
                "",
                "| 필드 | 필수 | 타입·제약 |",
                "|---|---|---|",
            ]
        )
        schema = description["input_schema"]
        for key, value in schema["properties"].items():
            constraints = {k: v for k, v in value.items() if k not in {"title", "description"}}
            lines.append(
                f"| `{key}` | {'예' if key in schema.get('required', []) else '아니오'} | `{json.dumps(constraints, ensure_ascii=False)}` |"
            )
        lines.extend(["", "출력 단위:", "", "| 필드 | 단위 |", "|---|---|"])
        lines.extend(f"| `{key}` | `{value}` |" for key, value in description["output_units"].items())
        if description["probability_semantics"]:
            lines.extend(["", "확률의 의미:", "", "| 필드 | 의미 |", "|---|---|"])
            lines.extend(
                f"| `{key}` | `{value}` |" for key, value in description["probability_semantics"].items()
            )
        lines.extend(["", "API 실행용 합성 입력:", ""])
        if identifier in examples:
            lines.extend(
                [
                    "```json",
                    json.dumps(examples[identifier], ensure_ascii=False, indent=2),
                    "```",
                ]
            )
        elif identifier in PYTHON_EXAMPLES:
            lines.append(
                "이 계산기는 선행 AssessmentResult를 받아 구성하는 모델이어서 독립 JSON 입력 대신 "
                f"registry 실행을 포함한 합성 Python wiring example `{PYTHON_EXAMPLES[identifier]}`를 제공한다. "
                "예제 입력은 구조 연결 설명용 합성값이며 물성 검증 자료가 아니다."
            )
        elif identifier in PYTHON_INPUT_EXAMPLES:
            lines.append(
                "독립 JSON fixture 대신 호출자가 직접 구성하는 Python request 예제를 제공한다: "
                f"`{PYTHON_INPUT_EXAMPLES[identifier]}`. 이 값은 API 배선 예시일 뿐 parameter 권고나 물성 검증이 아니다."
            )
        else:
            lines.append(
                "이 모델의 검토된 독립 합성 입력은 아직 `examples/model_inputs.json`에 없다. "
                "위 입력 스키마를 사용하되, 모델별 prerequisite와 Evidence를 직접 구성한다."
            )
        lines.extend(["", "구현 근거:", ""])
        for source in description["source_ids"]:
            row = lookup[source]
            lines.append(
                f"- [{row['title']}]({row['url']}) (`{source}`)"
                if "url" in row
                else f"- `{source}`: {row['derivation']}"
            )
        lines.extend(
            [
                "",
                "`computed`는 선언된 모델의 계산 완료 상태다. 구조 안전·규격 적합·외부 실험 검증의 의미는 아니다. 중첩 입력의 전체 정의는 `describe()`의 `$defs`를 확인한다.",
                "",
            ]
        )
    (ROOT / "docs/MODEL_REFERENCE_KO.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
