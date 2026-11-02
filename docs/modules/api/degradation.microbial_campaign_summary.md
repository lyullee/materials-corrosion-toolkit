# `degradation.microbial_campaign_summary`

**목적:** Campaign, site, clock, sample validity, assay identity, detection limits, water context and biofilm/deposit observations remain separate evidence fields.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `site_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `samples` | 예 | `{"items": {"$ref": "#/$defs/MicrobialSample"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `assays` | 아니오 | `{"items": {"$ref": "#/$defs/MicrobialAssay"}, "type": "array"}` | 계약·필드 설명 참조 |
| `water_context` | 아니오 | `{"items": {"$ref": "#/$defs/WaterContextObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `biofilm_deposit_observations` | 아니오 | `{"items": {"$ref": "#/$defs/BiofilmDepositObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_indicators` | 아니오 | `{"items": {"$ref": "#/$defs/CallerMicrobialIndicator"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_sampling_location_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_assay_target_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_water_context_parameter_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `biofilm_deposit_observation_required` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `campaign_site_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sampling_plan_and_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sample_validity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `assay_method_units_and_detection_limits_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `water_context_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `biofilm_deposit_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_indicator_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MicrobialCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `sample_count` | `count` |
| `valid_sample_count` | `count` |
| `assay_count` | `count` |
| `water_context_observation_count` | `count` |
| `biofilm_deposit_observation_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Campaign, site, clock, sample validity, assay identity, detection limits, water context and biofilm/deposit observations remain separate evidence fields.
- Caller indicators compare only matching target, method and unit; censored results and incomplete coverage remain explicit.

## 구현 근거·독립 설명

- `microbial_campaign_evidence_accounting`: Account for campaign, site, clock, location coverage, valid samples, target- and method-specific assays, exact units, detection limits, censored below-detection records, water context and biofilm or deposit observations against caller-owned indicator definitions. Do not infer microbial corrosion causality, rate, lifetime or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.microbial_campaign_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.microbial_campaign_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "campaign_id": "authored-microbial-campaign",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "site_id": "site-1",
  "clock_id": "authored-campaign-clock",
  "samples": [
    {
      "sample_id": "sample-1",
      "sampling_location_id": "inlet",
      "sample_time_s": 0.0,
      "sample_matrix": "water",
      "collection_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored microbial sample"
        }
      ]
    }
  ],
  "assays": [
    {
      "assay_id": "assay-a",
      "sample_id": "sample-1",
      "target_id": "target-a",
      "method_id": "method-a",
      "result_qualifier": "quantified",
      "reported_value": 120.0,
      "unit": "copies/mL",
      "detection_limit": 10.0,
      "caller_indicator_id": "indicator-a",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored assay"
        }
      ]
    },
    {
      "assay_id": "assay-b",
      "sample_id": "sample-1",
      "target_id": "target-b",
      "method_id": "method-b",
      "result_qualifier": "below_detection",
      "reported_value": null,
      "unit": "CFU/mL",
      "detection_limit": 5.0,
      "caller_indicator_id": "indicator-b",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored assay"
        }
      ]
    }
  ],
  "water_context": [
    {
      "observation_id": "context-ph",
      "sample_id": "sample-1",
      "parameter_id": "pH",
      "reported_value": 7.1,
      "unit": "1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored water context"
        }
      ]
    }
  ],
  "biofilm_deposit_observations": [
    {
      "observation_id": "deposit-1",
      "sample_id": "sample-1",
      "observation_method_id": "visual-1",
      "reported_description": "authored deposit observation",
      "metric_id": "covered-area",
      "reported_value": 0.01,
      "unit": "m^2",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored deposit observation"
        }
      ]
    }
  ],
  "caller_indicators": [
    {
      "indicator_id": "indicator-a",
      "target_id": "target-a",
      "method_id": "method-a",
      "unit": "copies/mL",
      "maximum_value": 100.0,
      "definition_basis": "caller monitoring plan",
      "caller_disposition_id_if_outside": "review-a"
    },
    {
      "indicator_id": "indicator-b",
      "target_id": "target-b",
      "method_id": "method-b",
      "unit": "CFU/mL",
      "maximum_value": 20.0,
      "definition_basis": "caller monitoring plan",
      "caller_disposition_id_if_outside": "review-b"
    }
  ],
  "required_sampling_location_ids": [
    "inlet"
  ],
  "required_assay_target_ids": [
    "target-a",
    "target-b"
  ],
  "required_water_context_parameter_ids": [
    "pH"
  ],
  "biofilm_deposit_observation_required": true,
  "campaign_site_and_clock_reviewed": true,
  "sampling_plan_and_coverage_reviewed": true,
  "sample_validity_reviewed": true,
  "assay_method_units_and_detection_limits_reviewed": true,
  "water_context_reviewed": true,
  "biofilm_deposit_mapping_reviewed": true,
  "caller_indicator_definitions_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored microbial campaign"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/microbial_corrosion.py#L180)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
