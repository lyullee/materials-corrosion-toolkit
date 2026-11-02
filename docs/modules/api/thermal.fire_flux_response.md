# `thermal.fire_flux_response`

**목적:** Reviewed net absorbed boundary flux composed with explicit multilayer transient conduction; no fire curve, ablation or intumescence law inferred.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `scenario_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `incident_flux_W_m2` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | W/m² |
| `absorbed_fraction` | 예 | `{"items": {"maximum": 1, "minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `incident_history_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `protection_material_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `thermal_model` | 예 | `{"$ref": "#/$defs/TransientConduction1D"}` | 계약·필드 설명 참조 |
| `incident_absorption_and_exposed_face_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FireThermalResponse.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| 가변 구조·진단·증거 결과 | 구현·예제의 `values` 확인 |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reviewed net absorbed boundary flux composed with explicit multilayer transient conduction; no fire curve, ablation or intumescence law inferred.

## 구현 근거·독립 설명

- `fire_flux_conduction_composition`: Compose aligned caller incident flux and absorbed fractions as an explicitly reviewed net inward boundary for the existing multilayer transient conduction solver. Preserve incident and material configuration digests and propagate solver status. No fire curve, ablation, intumescence or unstated surface cooling is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "thermal.fire_flux_response"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["thermal.fire_flux_response"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "scenario_id": "authored-fire-response",
  "incident_flux_W_m2": [
    1000.0,
    1000.0,
    1000.0
  ],
  "absorbed_fraction": [
    1.0,
    1.0,
    1.0
  ],
  "incident_history_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "protection_material_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "thermal_model": {
    "schema_version": "matintegrity.transient_conduction_1d.v1",
    "geometry": "planar",
    "cell_edges_m": [
      0.0,
      0.0025,
      0.005,
      0.0075,
      0.01
    ],
    "planar_area_m2": 1.0,
    "cylinder_length_m": null,
    "materials": [
      {
        "material_id": "authored-constant-property-solid",
        "temperature_K": [
          300.0
        ],
        "conductivity_W_m_K": [
          20.0
        ],
        "volumetric_heat_capacity_J_m3_K": [
          4000000.0
        ]
      }
    ],
    "cell_material_ids": [
      "authored-constant-property-solid",
      "authored-constant-property-solid",
      "authored-constant-property-solid",
      "authored-constant-property-solid"
    ],
    "initial_temperature_K": [
      300.0,
      300.0,
      300.0,
      300.0
    ],
    "time_s": [
      0.0,
      5.0,
      10.0
    ],
    "left_boundary": {
      "boundary_id": "authored-net-flux",
      "kind": "prescribed_heat_flux",
      "heat_flux_into_solid_W_m2": [
        1000.0,
        1000.0,
        1000.0
      ]
    },
    "right_boundary": {
      "boundary_id": "cool-face",
      "kind": "convection_radiation",
      "convection_W_m2_K": [
        25.0,
        25.0,
        25.0
      ],
      "ambient_temperature_K": [
        300.0,
        300.0,
        300.0
      ],
      "emissivity": 0.2,
      "radiative_environment_temperature_K": [
        300.0,
        300.0,
        300.0
      ]
    },
    "volumetric_heat_generation_W_m3": null,
    "distributed_exchange": null,
    "maximum_step_s": 0.1,
    "nonlinear_absolute_tolerance_K": 1e-08,
    "nonlinear_relative_tolerance": 1e-10,
    "maximum_nonlinear_iterations": 80,
    "maximum_relative_energy_balance_error": 1e-07,
    "one_dimensional_geometry_reviewed": true,
    "material_property_support_reviewed": true,
    "boundary_conditions_reviewed": true,
    "phase_change_absent_or_included_in_capacity_reviewed": true
  },
  "incident_absorption_and_exposed_face_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/history_composition.py#L66)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
