# `materials.composite_compatibility_assessment`

**목적:** Laminate, resin, fiber, manufacturing, layup and environment identities must match exactly.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `laminate_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `resin_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fiber_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `manufacturing_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `layup_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposures` | 예 | `{"items": {"$ref": "#/$defs/CompositeExposure"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/CompositeQualificationEnvelope"}` | 계약·필드 설명 참조 |
| `material_and_layup_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `manufacturing_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `environment_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CompositeCompatibility.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `exposure_comparisons` | `1` |
| `cumulative_exposure_s` | `s` |
| `remaining_declared_exposure_s` | `s` |
| `cumulative_exposure_within_envelope` | `1` |
| `violating_exposure_ids` | `1` |
| `qualification_evidence_summary` | `1` |
| `declared_compatibility_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Laminate, resin, fiber, manufacturing, layup and environment identities must match exactly.
- Service states are recorded as constant values within nonoverlapping intervals on one reviewed clock.
- Calibration and holdout source groups remain separated and only support a caller-declared envelope.

## 구현 근거·독립 설명

- `declared_composite_qualification_envelope`: Preserve laminate, resin, fiber, manufacturing, layup and environment identities with coupon and source-group calibration or holdout partitions, then compare reviewed temperature, moisture, absolute-pressure and cumulative-time ranges with caller-owned qualification envelopes. Do not infer micromechanics, strength reduction, delamination, lifetime or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.composite_compatibility_assessment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.composite_compatibility_assessment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-composite-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "laminate-region-1",
  "clock_id": "authored-service-clock",
  "laminate_system_id": "laminate-a",
  "resin_system_id": "resin-a",
  "fiber_system_id": "fiber-a",
  "manufacturing_condition_id": "cure-a",
  "layup_id": "layup-a",
  "environment_id": "environment-a",
  "exposures": [
    {
      "exposure_id": "e1",
      "start_time_s": 0.0,
      "end_time_s": 1000.0,
      "temperature_K": 320.0,
      "moisture_mass_fraction": 0.02,
      "pressure_Pa_abs": 200000.0,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored composite exposure"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "qualification-a",
    "laminate_system_id": "laminate-a",
    "resin_system_id": "resin-a",
    "fiber_system_id": "fiber-a",
    "manufacturing_condition_id": "cure-a",
    "layup_id": "layup-a",
    "environment_id": "environment-a",
    "minimum_temperature_K": 280.0,
    "maximum_temperature_K": 350.0,
    "minimum_moisture_mass_fraction": 0.0,
    "maximum_moisture_mass_fraction": 0.05,
    "minimum_pressure_Pa_abs": 100000.0,
    "maximum_pressure_Pa_abs": 500000.0,
    "maximum_cumulative_exposure_s": 3000.0,
    "qualification_records": [
      {
        "record_id": "cal-1",
        "coupon_id": "coupon-cal",
        "source_group_id": "group-cal",
        "partition": "calibration",
        "laminate_system_id": "laminate-a",
        "resin_system_id": "resin-a",
        "fiber_system_id": "fiber-a",
        "manufacturing_condition_id": "cure-a",
        "layup_id": "layup-a",
        "environment_id": "environment-a",
        "record_valid": true,
        "supports_declared_envelope": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored calibration coupon"
          }
        ]
      },
      {
        "record_id": "hold-1",
        "coupon_id": "coupon-hold",
        "source_group_id": "group-hold",
        "partition": "holdout",
        "laminate_system_id": "laminate-a",
        "resin_system_id": "resin-a",
        "fiber_system_id": "fiber-a",
        "manufacturing_condition_id": "cure-a",
        "layup_id": "layup-a",
        "environment_id": "environment-a",
        "record_valid": true,
        "supports_declared_envelope": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored holdout coupon"
          }
        ]
      }
    ],
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored composite envelope"
      }
    ]
  },
  "material_and_layup_identity_reviewed": true,
  "manufacturing_condition_reviewed": true,
  "environment_and_clock_reviewed": true,
  "exposure_records_reviewed": true,
  "qualification_evidence_reviewed": true,
  "calibration_holdout_partition_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/composite_compatibility.py#L118)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
