# `degradation.nonisothermal_parabolic_oxidation`

**목적:** A retained protective scale follows a caller-qualified parabolic law over the full history.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_oxide_thickness_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `temperature_history` | 예 | `{"items": {"$ref": "#/$defs/OxidationTemperatureKnot"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `rate_table` | 예 | `{"$ref": "#/$defs/TemperatureDependentParabolicRateTable"}` | 계약·필드 설명 참조 |
| `material_surface_and_environment_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_clock_and_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_units_and_temperature_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `retained_parabolic_scale_regime_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_table_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/NonisothermalParabolicOxidation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `physical_scope_id` | `1` |
| `clock_id` | `1` |
| `table_id` | `1` |
| `interpolation_policy` | `1` |
| `interval_thickness_squared_increments` | `mixed` |
| `cumulative_thickness_squared_increment_m2` | `m^2` |
| `final_oxide_thickness_m` | `m` |
| `oxide_growth_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A retained protective scale follows a caller-qualified parabolic law over the full history.
- Temperature is linear between ordered history knots and rate is linear between table temperatures.
- The rate table is not extrapolated and material, surface and environment identities are exact.

## 구현 근거·독립 설명

- `reviewed_temperature_dependent_parabolic_oxidation_rate_table`: Split a piecewise-linear temperature history at caller-owned rate-table knots and exactly integrate the linearly interpolated parabolic coefficient to obtain the oxide-thickness-squared increment. Do not extrapolate or infer spallation, breakaway oxidation, metal consumption, acceptance, remaining life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.nonisothermal_parabolic_oxidation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.nonisothermal_parabolic_oxidation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "history-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "surface-scope-1",
  "clock_id": "clock-1",
  "material_condition_id": "material-1",
  "surface_condition_id": "surface-1",
  "environment_id": "environment-1",
  "initial_oxide_thickness_m": 1e-06,
  "temperature_history": [
    {
      "knot_id": "knot-1",
      "elapsed_time_s": 0.0,
      "temperature_K": 300.0,
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored knot"
        }
      ]
    },
    {
      "knot_id": "knot-2",
      "elapsed_time_s": 100.0,
      "temperature_K": 500.0,
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored knot"
        }
      ]
    }
  ],
  "rate_table": {
    "table_id": "table-1",
    "material_condition_id": "material-1",
    "surface_condition_id": "surface-1",
    "environment_id": "environment-1",
    "rate_unit_token": "m^2/s",
    "interpolation_policy": "linear_rate_vs_temperature",
    "points": [
      {
        "point_id": "point-300",
        "temperature_K": 300.0,
        "parabolic_rate_m2_s": 1e-12,
        "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored rate"
          }
        ]
      },
      {
        "point_id": "point-400",
        "temperature_K": 400.0,
        "parabolic_rate_m2_s": 3e-12,
        "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored rate"
          }
        ]
      },
      {
        "point_id": "point-500",
        "temperature_K": 500.0,
        "parabolic_rate_m2_s": 7e-12,
        "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored rate"
          }
        ]
      }
    ],
    "provider_id": "provider-1",
    "provider_revision": "1",
    "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "data_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "qualification_evidence": [
      {
        "evidence_record_id": "q-cal",
        "physical_specimen_id": "specimen-cal",
        "source_group_id": "source-cal",
        "partition": "calibration",
        "method_id": "method-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "record_valid": true,
        "supports_declared_table": true,
        "invalid_or_limiting_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored calibration"
          }
        ]
      },
      {
        "evidence_record_id": "q-hold",
        "physical_specimen_id": "specimen-hold",
        "source_group_id": "source-hold",
        "partition": "holdout",
        "method_id": "method-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "record_valid": true,
        "supports_declared_table": true,
        "invalid_or_limiting_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored holdout"
          }
        ]
      }
    ],
    "qualification_basis": "authored qualification",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored rate table"
      }
    ]
  },
  "material_surface_and_environment_identity_reviewed": true,
  "temperature_clock_and_interpolation_reviewed": true,
  "rate_units_and_temperature_support_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "calibration_holdout_and_source_groups_reviewed": true,
  "retained_parabolic_scale_regime_reviewed": true,
  "rate_table_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored oxidation example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/nonisothermal_oxidation.py#L174)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
