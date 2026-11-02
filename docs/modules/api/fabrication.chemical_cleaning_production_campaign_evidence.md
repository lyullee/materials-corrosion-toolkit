# `fabrication.chemical_cleaning_production_campaign_evidence`

**목적:** Caller criteria only; no kinetics or compatibility inference.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `area_ids` | 예 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `circuit_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `precondition_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `batches` | 예 | `{"items": {"$ref": "#/$defs/ChemicalBatch"}, "type": "array"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/CleaningEvent"}, "type": "array"}` | 계약·필드 설명 참조 |
| `measurements` | 예 | `{"items": {"$ref": "#/$defs/CleaningMeasurement"}, "type": "array"}` | 계약·필드 설명 참조 |
| `waste_records` | 예 | `{"items": {"$ref": "#/$defs/WasteDisposition"}, "type": "array"}` | 계약·필드 설명 참조 |
| `profile` | 예 | `{"$ref": "#/$defs/Profile"}` | 계약·필드 설명 참조 |
| `identity_precondition_batch_and_composition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `event_sequence_state_units_and_time_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_uncertainty_provenance_and_digest_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `waste_disposition_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ChemicalCleaningCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `disposition` | `1` |
| `findings` | `mixed` |
| `result_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller criteria only; no kinetics or compatibility inference.

## 구현 근거·독립 설명

- `authored_chemical_cleaning_production_campaign_profile`: Preserve caller-supplied asset, material, area, circuit, precondition, chemical batch composition and concentration, ordered fill-circulate-soak-rinse-neutralize-dry events, process conditions, coupon, solution, surface, residue, chemistry or NDE measurements, and waste-disposition evidence. Apply only caller-authored criteria. Do not infer kinetics, corrosion rate, material compatibility or standard acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.chemical_cleaning_production_campaign_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.chemical_cleaning_production_campaign_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "a",
  "asset_id": "asset",
  "location_id": "l",
  "campaign_id": "c",
  "material_id": "m",
  "area_ids": [
    "a1"
  ],
  "circuit_id": "cir",
  "precondition_id": "pre",
  "batches": [
    {
      "batch_id": "b",
      "composition": [
        {
          "component_id": "acid",
          "concentration": 0.1,
          "unit_token": "kg/kg"
        }
      ],
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "b",
          "origin": "user_declared",
          "citation": "b",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "events": [
    {
      "event_id": "fill",
      "sequence_position": 1,
      "event_kind": "fill",
      "batch_id": "b",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "minimum_temperature_k": 290.0,
      "maximum_temperature_k": 320.0,
      "minimum_pressure_pa_abs": 100000.0,
      "maximum_pressure_pa_abs": 200000.0,
      "flow_m3_s": 0.01,
      "ph": 2.0,
      "conductivity_s_m": 1.0,
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
      "measurement_id": "res",
      "sample_location_id": "x",
      "metric_kind": "residue",
      "metric_id": "residue",
      "unit_token": "kg/m2",
      "status": "available",
      "value": 0.01,
      "standard_uncertainty": 0.001,
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_basis": null,
      "evidence": [
        {
          "source_id": "res",
          "origin": "user_declared",
          "citation": "res",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "waste_records": [
    {
      "waste_record_id": "w",
      "waste_stream_id": "ws",
      "disposition_method_id": "method",
      "destination_id": "dest",
      "manifest_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_reviewed": true,
      "evidence": [
        {
          "source_id": "w",
          "origin": "user_declared",
          "citation": "w",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "profile": {
    "profile_id": "pr",
    "profile_revision": "1",
    "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "permitted_material_ids": [
      "m"
    ],
    "permitted_precondition_ids": [
      "pre"
    ],
    "permitted_component_units": [
      "kg/kg"
    ],
    "maximum_event_temperature_k": 350.0,
    "maximum_pressure_pa_abs": 300000.0,
    "criteria": [
      {
        "criterion_id": "r",
        "metric_kind": "residue",
        "metric_id": "residue",
        "unit_token": "kg/m2",
        "minimum_inclusive": 0.0,
        "maximum_inclusive": 0.02,
        "uncertainty_policy": "interval_must_fit",
        "missing_disposition": "insufficient_evidence"
      }
    ],
    "profile_reviewed": true,
    "evidence": [
      {
        "source_id": "pr",
        "origin": "user_declared",
        "citation": "pr",
        "license_id": null,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  },
  "identity_precondition_batch_and_composition_reviewed": true,
  "event_sequence_state_units_and_time_reviewed": true,
  "measurement_uncertainty_provenance_and_digest_reviewed": true,
  "waste_disposition_evidence_reviewed": true,
  "caller_profile_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/chemical_cleaning_campaign.py#L274)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
