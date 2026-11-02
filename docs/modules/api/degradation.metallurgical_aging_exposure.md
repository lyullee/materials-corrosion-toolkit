# `degradation.metallurgical_aging_exposure`

**목적:** Each interval uses a caller-calibrated equivalent-time rate multiplier at a reviewed temperature.

**모델 버전:** `1.0.2` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `aging_mechanism_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/AgingExposureInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposure_envelope` | 예 | `{"$ref": "#/$defs/DeclaredAgingExposureEnvelope"}` | 계약·필드 설명 참조 |
| `material_and_mechanism_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `multiplier_provider_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `interval_completeness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MetallurgicalAgingExposure.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `clock_id` | `1` |
| `material_condition_id` | `1` |
| `aging_mechanism_id` | `1` |
| `history_span_s` | `s` |
| `uncovered_duration_s` | `s` |
| `uncovered_intervals_s` | `s` |
| `envelope_id` | `1` |
| `reference_temperature_K` | `K` |
| `elapsed_exposure_s` | `s` |
| `equivalent_exposure_s` | `s` |
| `maximum_equivalent_exposure_s` | `s` |
| `remaining_equivalent_exposure_s` | `s` |
| `within_declared_equivalent_exposure` | `1` |
| `interval_contributions` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each interval uses a caller-calibrated equivalent-time rate multiplier at a reviewed temperature.
- One exact material condition, aging mechanism and multiplier provider apply to the full history.

## 구현 근거·독립 설명

- `declared_metallurgical_aging_equivalent_exposure`: Integrate explicit interval duration times caller-calibrated nonnegative equivalent-time rate multipliers within one reviewed material, mechanism and provider support. Compare only with a caller-owned equivalent-exposure limit; do not infer phase fraction, embrittlement, strength, toughness, remaining life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.metallurgical_aging_exposure"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.metallurgical_aging_exposure"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-aging-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-thermal-clock",
  "material_condition_id": "material-1",
  "aging_mechanism_id": "mechanism-1",
  "intervals": [
    {
      "interval_id": "i1",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "temperature_K": 600.0,
      "equivalent_time_rate_multiplier": 2.0,
      "multiplier_provider_id": "provider-1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored aging interval"
        }
      ]
    },
    {
      "interval_id": "i2",
      "start_time_s": 100.0,
      "end_time_s": 300.0,
      "temperature_K": 550.0,
      "equivalent_time_rate_multiplier": 0.5,
      "multiplier_provider_id": "provider-1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored aging interval"
        }
      ]
    }
  ],
  "exposure_envelope": {
    "envelope_id": "envelope-1",
    "material_condition_id": "material-1",
    "aging_mechanism_id": "mechanism-1",
    "reference_temperature_K": 575.0,
    "multiplier_provider_id": "provider-1",
    "minimum_supported_temperature_K": 500.0,
    "maximum_supported_temperature_K": 650.0,
    "maximum_equivalent_exposure_s": 400.0,
    "applicability_basis": "caller calibration",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored aging envelope"
      }
    ]
  },
  "material_and_mechanism_reviewed": true,
  "clock_and_temperature_history_reviewed": true,
  "multiplier_provider_reviewed": true,
  "interval_completeness_reviewed": true,
  "envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/metallurgical_aging.py#L92)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
