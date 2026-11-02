# `degradation.under_deposit_calibrated_loss`

**목적:** Each interval has a reviewed deposit state and an external calibrated local-loss rate within one provider support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

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
| `environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `assessed_surface_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/UnderDepositLossInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rate_support` | 예 | `{"$ref": "#/$defs/UnderDepositRateSupport"}` | 계약·필드 설명 참조 |
| `material_and_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_interval_completeness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deposit_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stagnation_and_aeration_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibrated_rate_provider_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UnderDepositExposureHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `support_id` | `1` |
| `elapsed_exposure_s` | `s` |
| `deposit_covered_area_time_m2_s` | `m^2*s` |
| `cumulative_calibrated_local_loss_m` | `m` |
| `maximum_deposit_coverage_fraction` | `1` |
| `interval_contributions` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each interval has a reviewed deposit state and an external calibrated local-loss rate within one provider support.
- Rates are constant over their explicit intervals and are not generated from deposit observations.

## 구현 근거·독립 설명

- `external_under_deposit_local_loss_accounting`: Integrate explicit interval duration times externally calibrated local under-deposit loss rate while accounting for deposit-covered area-time inside one reviewed material, environment, temperature, coverage, stagnation, differential-aeration and provider support. Do not infer mechanism synergy, geometry evolution, remaining life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.under_deposit_calibrated_loss"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.under_deposit_calibrated_loss"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-under-deposit",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-exposure-clock",
  "material_condition_id": "material-1",
  "environment_id": "environment-1",
  "assessed_surface_area_m2": 10.0,
  "intervals": [
    {
      "interval_id": "i1",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "temperature_K": 320.0,
      "deposit_coverage_fraction": 0.2,
      "stagnation_descriptor": "stagnant",
      "differential_aeration_descriptor": "differential-a",
      "calibrated_local_loss_rate_m_s": 1e-09,
      "rate_provider_id": "provider-1",
      "rate_provider_state_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored deposit interval"
        }
      ]
    },
    {
      "interval_id": "i2",
      "start_time_s": 100.0,
      "end_time_s": 300.0,
      "temperature_K": 330.0,
      "deposit_coverage_fraction": 0.5,
      "stagnation_descriptor": "stagnant",
      "differential_aeration_descriptor": "differential-a",
      "calibrated_local_loss_rate_m_s": 2e-09,
      "rate_provider_id": "provider-1",
      "rate_provider_state_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored deposit interval"
        }
      ]
    }
  ],
  "rate_support": {
    "support_id": "support-1",
    "material_condition_id": "material-1",
    "environment_id": "environment-1",
    "rate_provider_id": "provider-1",
    "minimum_temperature_K": 300.0,
    "maximum_temperature_K": 350.0,
    "minimum_deposit_coverage_fraction": 0.0,
    "maximum_deposit_coverage_fraction": 0.8,
    "supported_stagnation_descriptors": [
      "stagnant"
    ],
    "supported_differential_aeration_descriptors": [
      "differential-a"
    ],
    "support_basis": "caller calibration",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored deposit support"
      }
    ]
  },
  "material_and_environment_reviewed": true,
  "clock_and_interval_completeness_reviewed": true,
  "deposit_coverage_reviewed": true,
  "stagnation_and_aeration_mapping_reviewed": true,
  "calibrated_rate_provider_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/under_deposit.py#L100)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
