# `degradation.acid_dissolution_history`

**목적:** Dissolution rates are externally calibrated, explicitly supplied and constant within each declared interval.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `acid_species_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `concentration_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `concentration_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | s |
| `rate_intervals` | 예 | `{"items": {"$ref": "#/$defs/AcidDissolutionRateInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rate_supports` | 예 | `{"items": {"$ref": "#/$defs/AcidDissolutionRateSupport"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_acid_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `concentration_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `flow_mass_transfer_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_provider_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_interval_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AcidDissolutionHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `clock_id` | `1` |
| `interval_metal_loss_m` | `m` |
| `cumulative_metal_loss_m` | `m` |
| `total_metal_loss_m` | `m` |
| `interval_diagnostics` | `mixed` |
| `invalid_or_unmatched_interval_ids` | `1` |
| `outside_support_interval_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Dissolution rates are externally calibrated, explicitly supplied and constant within each declared interval.
- Material, acid, concentration unit and basis, and flow or mass-transfer descriptors require exact matching.
- No extrapolation, automatic unit conversion or hidden empirical coefficient is used.

## 구현 근거·독립 설명

- `caller_calibrated_acid_dissolution_rate_integration`: Integrate explicit interval duration times externally calibrated nonnegative acid-dissolution rate within exact material, acid, concentration-unit and basis, flow-descriptor and provider support. Preserve provider version and state digests; do not extrapolate or infer reaction chemistry, inhibitor depletion, localized attack, lifetime or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.acid_dissolution_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.acid_dissolution_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "authored-acid-history",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-clock",
  "material_condition_id": "alloy-a",
  "acid_species_id": "acid-a",
  "concentration_unit_token": "mass_percent",
  "concentration_basis": "caller analytical definition",
  "elapsed_time_s": [
    0.0,
    100.0,
    300.0
  ],
  "rate_intervals": [
    {
      "interval_id": "a-interval",
      "support_id": "support-1",
      "concentration": 5.0,
      "temperature_K": 320.0,
      "flow_mass_transfer_descriptor": "stirred-a",
      "dissolution_rate_m_s": 1e-08,
      "rate_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "rate_valid": true,
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored acid rate"
        }
      ]
    },
    {
      "interval_id": "b-interval",
      "support_id": "support-1",
      "concentration": 5.0,
      "temperature_K": 320.0,
      "flow_mass_transfer_descriptor": "stirred-a",
      "dissolution_rate_m_s": 2e-08,
      "rate_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "rate_valid": true,
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored acid rate"
        }
      ]
    }
  ],
  "rate_supports": [
    {
      "support_id": "support-1",
      "material_condition_id": "alloy-a",
      "acid_species_id": "acid-a",
      "concentration_min": 1.0,
      "concentration_max": 10.0,
      "concentration_unit_token": "mass_percent",
      "concentration_basis": "caller analytical definition",
      "temperature_min_K": 290.0,
      "temperature_max_K": 350.0,
      "applicable_flow_mass_transfer_descriptors": [
        "stirred-a"
      ],
      "rate_provider_id": "provider-a",
      "rate_provider_version": "1",
      "rate_provider_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "calibration_basis": "caller calibration",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored acid support"
        }
      ]
    }
  ],
  "material_and_acid_identity_reviewed": true,
  "concentration_definition_reviewed": true,
  "temperature_history_reviewed": true,
  "flow_mass_transfer_history_reviewed": true,
  "rate_provider_and_calibration_reviewed": true,
  "clock_and_interval_alignment_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored acid history"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/acid_dissolution.py#L97)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
