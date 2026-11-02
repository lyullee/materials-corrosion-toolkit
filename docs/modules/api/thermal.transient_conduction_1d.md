# `thermal.transient_conduction_1d`

**목적:** One-dimensional planar or radial conduction with caller-supplied property curves, boundaries, distributed convection/gray radiation and heat generation.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.transient_conduction_1d.v1", "default": "matintegrity.transient_conduction_1d.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry` | 예 | `{"enum": ["planar", "cylindrical"], "type": "string"}` | 계약·필드 설명 참조 |
| `cell_edges_m` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 501, "minItems": 3, "type": "array"}` | m |
| `planar_area_m2` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `cylinder_length_m` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `materials` | 예 | `{"items": {"$ref": "#/$defs/ThermalMaterialProperties"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_material_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | K |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `left_boundary` | 예 | `{"$ref": "#/$defs/ThermalBoundary"}` | 계약·필드 설명 참조 |
| `right_boundary` | 예 | `{"$ref": "#/$defs/ThermalBoundary"}` | 계약·필드 설명 참조 |
| `volumetric_heat_generation_W_m3` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `distributed_exchange` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/DistributedHeatExchange"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `nonlinear_absolute_tolerance_K` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "type": "number"}` | K |
| `nonlinear_relative_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_nonlinear_iterations` | 아니오 | `{"default": 80, "maximum": 500, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_relative_energy_balance_error` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `one_dimensional_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_property_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `boundary_conditions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_change_absent_or_included_in_capacity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TransientConduction1D.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cell_centers_m` | `m` |
| `temperature_history_K` | `K` |
| `boundary_surface_temperature_K` | `K` |
| `boundary_heat_rate_into_solid_W` | `W` |
| `distributed_heat_rate_into_solid_W` | `W` |
| `volumetric_generation_rate_W` | `W` |
| `cumulative_boundary_energy_into_solid_J` | `J` |
| `cumulative_distributed_energy_into_solid_J` | `J` |
| `cumulative_generated_energy_J` | `J` |
| `maximum_absolute_discrete_energy_balance_error_J` | `J` |
| `maximum_relative_discrete_energy_balance_error` | `1` |
| `internal_steps` | `1` |
| `maximum_nonlinear_iterations_used` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One-dimensional planar or radial conduction with caller-supplied property curves, boundaries, distributed convection/gray radiation and heat generation.

## 구현 근거·독립 설명

- `transient_fvm_enthalpy`: Independently balance cell enthalpy against face conduction, signed boundary heat, optional distributed convection and volumetric generation. Use planar or radial cell volumes, series face resistances, backward Euler time integration and a linear-work tridiagonal solve. Integrate linearly tabulated volumetric heat capacity to enthalpy and refuse property extrapolation. Iteratively linearize temperature-dependent properties and gray-surface radiation; report discrete energy residuals separately from geometry, property and experiment qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "thermal.transient_conduction_1d"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["thermal.transient_conduction_1d"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
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
    "boundary_id": "hot-face",
    "kind": "prescribed_temperature",
    "temperature_K": [
      400.0,
      400.0,
      400.0
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
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_transient.py#L636)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
