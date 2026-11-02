# `structural.profile_capacity_rate_field_scenario`

**목적:** A caller-provided axial-by-time rate field is integrated nodewise and passed to the same reviewed profile-capacity provider.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `scenario_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `profile` | 예 | `{"$ref": "#/$defs/ProfileCapacity"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | s |
| `corrosion_rate_m_s` | 예 | `{"items": {"items": {"minimum": 0, "type": "number"}, "type": "array"}, "maxItems": 500, "minItems": 2, "type": "array"}` | m/s |
| `forecast_horizon_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ProfileCapacityRateFieldScenario.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `baseline_pressure_difference_capacity_Pa` | `Pa` |
| `forecast_pressure_difference_capacity_Pa` | `Pa` |
| `capacity_change_Pa` | `Pa` |
| `capacity_loss_fraction_of_baseline` | `1` |
| `integrated_metal_loss_by_node_m` | `m` |
| `forecast_minimum_thickness_m` | `m` |
| `forecast_capacity_reduction_factor` | `1` |
| `baseline_status` | `1` |
| `forecast_status` | `1` |
| `scenario_id` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A caller-provided axial-by-time rate field is integrated nodewise and passed to the same reviewed profile-capacity provider.
- No rate inference, spatial interpolation or temporal extrapolation is performed; provider and zero-ligament limits remain explicit.

## 구현 근거·독립 설명

- `linear_degradation`: The time of crossing a thickness requirement follows a declared linear loss trajectory.
- `piecewise_linear_history`: Interpolate recorded linear segments to intersect a declared temperature band or temperature crossing; preserve actual continuous intervals.
- `piecewise_linear_loss_geometry`: For a nodal axial window of length L and reference wall t, integrate the piecewise-linear depth to obtain A and define alpha=A/(tL). Combine the area ratio with separately supplied pressure and bulging providers; no normative coefficients are embedded.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.profile_capacity_rate_field_scenario"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.profile_capacity_rate_field_scenario"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "scenario_id": "synthetic-axial-time-rate-field",
  "profile": {
    "geometry_id": "synthetic-pipe",
    "material_condition_id": "synthetic-condition",
    "reference_wall_thickness_m": 0.01,
    "axial_position_m": [
      0.0,
      0.2,
      0.4,
      0.6,
      0.8
    ],
    "measured_remaining_thickness_m": [
      0.01,
      0.007,
      0.005,
      0.007,
      0.01
    ],
    "reference_capacity": {
      "geometry_id": "synthetic-pipe",
      "material_condition_id": "synthetic-condition",
      "capacity_basis": "Synthetic reference, no grade-specific strength rule",
      "evidence": [
        {
          "source_id": "project-synthetic",
          "origin": "synthetic",
          "citation": "Project-authored synthetic provider",
          "license_id": "MIT"
        }
      ],
      "reference_pressure_difference_Pa": 10000000.0
    },
    "bulging_table": {
      "geometry_id": "synthetic-pipe",
      "material_condition_id": "synthetic-condition",
      "window_length_m": [
        0.0,
        0.4,
        0.8
      ],
      "factor": [
        1.0,
        1.5,
        2.5
      ],
      "validity_description": "Synthetic monotone length provider for this one geometry/condition",
      "evidence": [
        {
          "source_id": "project-synthetic",
          "origin": "synthetic",
          "citation": "Project-authored synthetic provider",
          "license_id": "MIT"
        }
      ]
    },
    "maximum_supported_depth_fraction": 0.8,
    "full_axial_extent_confirmed": true,
    "blunt_metal_loss_confirmed": true,
    "internal_pressure_dominant_confirmed": true,
    "provider_applicability_reviewed": true
  },
  "time_s": [
    0.0,
    2000000.0,
    5000000.0
  ],
  "corrosion_rate_m_s": [
    [
      1e-11,
      1.5e-11,
      2e-11
    ],
    [
      2e-11,
      3e-11,
      4e-11
    ],
    [
      3e-11,
      4.5e-11,
      6e-11
    ],
    [
      4e-11,
      6e-11,
      8e-11
    ],
    [
      5e-11,
      7.5e-11,
      1e-10
    ]
  ],
  "forecast_horizon_s": 4000000.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/local_capacity.py#L319)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
