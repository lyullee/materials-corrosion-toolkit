# `inspection.cryogenic_leak_test_evidence`

**목적:** Cycle temperature and pressure extrema, medium identity and pressure basis are reviewed caller records.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_article_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_medium_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"enum": ["absolute", "gauge"], "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cycles` | 예 | `{"items": {"$ref": "#/$defs/CryogenicThermalCycle"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `leak_observations` | 예 | `{"items": {"$ref": "#/$defs/CryogenicLeakObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredCryogenicLeakEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `article_and_medium_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_cycle_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_pressure_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thermal_stabilization_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `leak_methods_and_locations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_and_detection_limits_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CryogenicLeakTestAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `test_article_id` | `1` |
| `selected_envelope_id` | `1` |
| `cycle_count` | `count` |
| `cycle_support` | `mixed` |
| `outside_support_cycle_ids` | `1` |
| `leak_observation_comparisons` | `mixed` |
| `definition_mismatch_observation_ids` | `1` |
| `insufficient_test_location_cycle_ids` | `1` |
| `outside_declared_maximum_observation_ids` | `1` |
| `all_exact_test_observations_within_declared_maximum` | `1` |
| `source_group_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Cycle temperature and pressure extrema, medium identity and pressure basis are reviewed caller records.
- Leak method, metric, unit, uncertainty, detection limit and maximum comparison value are caller-owned.
- Background, control and test observations retain their declared roles and source groups.

## 구현 근거·독립 설명

- `reviewed_cryogenic_cycle_leak_evidence`: Compare reviewed cryogenic temperature-pressure cycles and background, control and test leak observations with an exact caller-owned medium, method, metric, unit, detection-limit and support envelope. Preserve below-detection values as limits; do not infer a leak source, service leakage, POD, failure or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.cryogenic_leak_test_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.cryogenic_leak_test_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-cryogenic-leak",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "test_article_id": "article-1",
  "test_medium_id": "medium-1",
  "pressure_basis": "absolute",
  "clock_id": "clock-1",
  "cycles": [
    {
      "cycle_id": "cycle-1",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "minimum_temperature_K": 80.0,
      "maximum_temperature_K": 300.0,
      "minimum_pressure_Pa": 100000.0,
      "maximum_pressure_Pa": 200000.0,
      "temperature_provider_id": "temperature-logger",
      "pressure_provider_id": "pressure-logger",
      "acquisition_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "thermal_stabilization_basis": "authored plateau",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored cryogenic cycle"
        }
      ]
    }
  ],
  "leak_observations": [
    {
      "observation_id": "leak-1",
      "cycle_id": "cycle-1",
      "physical_location_id": "seat-1",
      "source_group_id": "run-1",
      "observation_role": "test",
      "method_id": "method-1",
      "metric_id": "leak-rate",
      "metric_definition": "caller calibrated leak-rate signal",
      "unit_token": "Pa*m^3/s",
      "reporting_status": "below_detection",
      "detection_limit": 1e-07,
      "provider_id": "detector-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored leak observation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "test_medium_id": "medium-1",
      "pressure_basis": "absolute",
      "minimum_supported_temperature_K": 70.0,
      "maximum_supported_temperature_K": 310.0,
      "minimum_supported_pressure_Pa": 90000.0,
      "maximum_supported_pressure_Pa": 210000.0,
      "supported_method_ids": [
        "method-1"
      ],
      "metric_id": "leak-rate",
      "metric_definition": "caller calibrated leak-rate signal",
      "unit_token": "Pa*m^3/s",
      "maximum_conservative_value": 2e-07,
      "minimum_valid_cycles": 1,
      "minimum_test_locations_per_cycle": 1,
      "envelope_provider_id": "caller-envelope",
      "envelope_provider_version": "1",
      "envelope_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "authority_basis": "authored caller plan",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored cryogenic envelope"
        }
      ]
    }
  ],
  "article_and_medium_identity_reviewed": true,
  "clock_and_cycle_alignment_reviewed": true,
  "temperature_and_pressure_basis_reviewed": true,
  "thermal_stabilization_reviewed": true,
  "leak_methods_and_locations_reviewed": true,
  "uncertainty_and_detection_limits_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored cryogenic assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/cryogenic_leak_testing.py#L160)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
