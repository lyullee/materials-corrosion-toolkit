# `fabrication.surface_cleanliness_production_campaign_evidence`

**목적:** Caller criteria only; no standard comparator.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `area_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `previous_coating_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `contaminant_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `preparation_events` | 예 | `{"items": {"$ref": "#/$defs/PreparationEvent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measurements` | 예 | `{"items": {"$ref": "#/$defs/CleanlinessMeasurement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `profile` | 예 | `{"$ref": "#/$defs/CallerCleanlinessProfile"}` | 계약·필드 설명 참조 |
| `identity_and_area_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `preparation_event_order_process_and_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_locations_replicas_units_uncertainty_and_provenance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_authority_and_criteria_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SurfaceCleanlinessCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `disposition` | `1` |
| `findings` | `mixed` |
| `result_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller criteria only; no standard comparator.

## 구현 근거·독립 설명

- `authored_surface_cleanliness_production_campaign_profile`: Preserve caller-supplied substrate, area, prior coating, contaminant, preparation process, ordered events, ambient, surface and dewpoint temperatures, and salt, dust, profile, oil, visual or roughness measurements with location, uncertainty and provenance. Apply only caller-authored criteria. Do not perform image classification, embed standard comparators or limits, or claim coating qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.surface_cleanliness_production_campaign_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.surface_cleanliness_production_campaign_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "a",
  "asset_id": "asset",
  "location_id": "loc",
  "campaign_id": "c",
  "substrate_id": "steel",
  "area_ids": [
    "area"
  ],
  "previous_coating_id": "old",
  "contaminant_ids": [
    "salt"
  ],
  "preparation_events": [
    {
      "event_id": "event",
      "sequence_position": 1,
      "process_id": "blast",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "ambient_temperature_k": 295.0,
      "surface_temperature_k": 300.0,
      "dewpoint_temperature_k": 290.0,
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "event",
          "origin": "user_declared",
          "citation": "event",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "measurements": [
    {
      "measurement_id": "m1",
      "area_id": "area",
      "sample_location_id": "x1",
      "replica_group_id": "g",
      "metric_kind": "soluble_salt",
      "metric_id": "salt",
      "metric_definition": "caller salt",
      "unit_token": "kg/m^2",
      "status": "available",
      "value": 1e-05,
      "standard_uncertainty": 1e-07,
      "method_id": "m",
      "provider_id": "p",
      "provider_revision": "1",
      "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "m1",
          "origin": "user_declared",
          "citation": "m1",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "measurement_id": "m2",
      "area_id": "area",
      "sample_location_id": "x2",
      "replica_group_id": "g",
      "metric_kind": "soluble_salt",
      "metric_id": "salt",
      "metric_definition": "caller salt",
      "unit_token": "kg/m^2",
      "status": "available",
      "value": 1.1e-05,
      "standard_uncertainty": 1e-07,
      "method_id": "m",
      "provider_id": "p",
      "provider_revision": "1",
      "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "m2",
          "origin": "user_declared",
          "citation": "m2",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "profile": {
    "profile_id": "p",
    "profile_revision": "1",
    "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "permitted_substrate_ids": [
      "steel"
    ],
    "permitted_previous_coating_ids": [
      "old"
    ],
    "permitted_contaminant_ids": [
      "salt"
    ],
    "permitted_process_ids": [
      "blast"
    ],
    "minimum_surface_above_dewpoint_k": 5.0,
    "criteria": [
      {
        "criterion_id": "salt-rule",
        "metric_kind": "soluble_salt",
        "metric_id": "salt",
        "unit_token": "kg/m^2",
        "aggregation": "replica_mean",
        "minimum_inclusive": 0.0,
        "maximum_inclusive": 2e-05,
        "uncertainty_policy": "interval_must_fit",
        "uncertainty_coverage_factor": 1.0,
        "minimum_replicas": 2,
        "missing_disposition": "insufficient_evidence",
        "description": "caller"
      }
    ],
    "profile_reviewed": true,
    "evidence": [
      {
        "source_id": "profile",
        "origin": "user_declared",
        "citation": "profile",
        "license_id": null,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  },
  "identity_and_area_mapping_reviewed": true,
  "preparation_event_order_process_and_environment_reviewed": true,
  "measurement_locations_replicas_units_uncertainty_and_provenance_reviewed": true,
  "caller_profile_authority_and_criteria_reviewed": true,
  "evidence": [
    {
      "source_id": "a",
      "origin": "user_declared",
      "citation": "a",
      "license_id": null,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/surface_cleanliness_campaign.py#L311)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
