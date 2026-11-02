# `degradation.selective_leaching_applicability`

**목적:** Alloy, composition, phase, environment, temperature, pH, electrochemical descriptor and exposure duration are compared only with caller-qualified support.

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
| `alloy_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `composition_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `phase_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `qualification_tests` | 예 | `{"items": {"$ref": "#/$defs/SelectiveLeachingTestEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelopes` | 예 | `{"items": {"$ref": "#/$defs/SelectiveLeachingQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposure_intervals` | 예 | `{"items": {"$ref": "#/$defs/SelectiveLeachingExposure"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 아니오 | `{"items": {"$ref": "#/$defs/SelectiveLeachingObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_observation_ranges` | 아니오 | `{"items": {"$ref": "#/$defs/CallerObservationRange"}, "type": "array"}` | 계약·필드 설명 참조 |
| `alloy_composition_and_phase_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `environment_temperature_and_pH_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `redox_or_potential_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `microscopy_and_composition_observations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_tests_envelopes_and_ranges_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SelectiveLeachingApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `observation_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Alloy, composition, phase, environment, temperature, pH, electrochemical descriptor and exposure duration are compared only with caller-qualified support.
- Microscopy and composition observations compare only with exactly matching caller ranges while retaining supplied uncertainty.

## 구현 근거·독립 설명

- `selective_leaching_observation_envelope_accounting`: Compare exact alloy, composition, phase, environment, redox or potential basis and exposure conditions with linked caller-owned qualification evidence, then separately compare microscopy or composition observations and expanded uncertainty with exact method, definition and unit ranges. Do not infer dealloyed-depth growth, residual strength, fracture, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.selective_leaching_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.selective_leaching_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-selective-leaching",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-exposure-clock",
  "alloy_id": "alloy-a",
  "composition_condition_id": "composition-a",
  "phase_condition_id": "phase-a",
  "qualification_tests": [
    {
      "test_id": "test-1",
      "physical_specimen_id": "specimen-1",
      "test_method_id": "method-1",
      "reported_endpoint": "authored completed exposure",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored leaching test"
        }
      ]
    }
  ],
  "qualification_envelopes": [
    {
      "envelope_id": "envelope-1",
      "alloy_ids": [
        "alloy-a"
      ],
      "composition_condition_ids": [
        "composition-a"
      ],
      "phase_condition_ids": [
        "phase-a"
      ],
      "environment_id": "water-a",
      "minimum_temperature_K": 280.0,
      "maximum_temperature_K": 350.0,
      "minimum_pH": 5.0,
      "maximum_pH": 9.0,
      "redox_or_potential_descriptor_id": "controlled-potential",
      "potential_basis": "reference-a",
      "potential_unit": "V",
      "minimum_potential": -0.5,
      "maximum_potential": 0.1,
      "maximum_exposure_duration_s": 10000.0,
      "test_evidence_ids": [
        "test-1"
      ],
      "applicability_basis": "caller envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored leaching envelope"
        }
      ]
    }
  ],
  "exposure_intervals": [
    {
      "interval_id": "interval-1",
      "envelope_id": "envelope-1",
      "start_time_s": 0.0,
      "end_time_s": 1000.0,
      "environment_id": "water-a",
      "temperature_K": 320.0,
      "pH": 7.0,
      "redox_or_potential_descriptor_id": "controlled-potential",
      "potential_basis": "reference-a",
      "potential_unit": "V",
      "potential_value": -0.2,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored leaching exposure"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "obs-1",
      "physical_region_id": "surface-a",
      "observation_kind": "microscopy",
      "method_id": "method-a",
      "metric_definition": "caller affected dimension",
      "reported_value": 0.009,
      "expanded_uncertainty": 0.002,
      "unit": "m",
      "caller_range_id": "range-1",
      "reported_description": "authored contrast region",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored leaching observation"
        }
      ]
    }
  ],
  "caller_observation_ranges": [
    {
      "range_id": "range-1",
      "observation_kind": "microscopy",
      "method_id": "method-a",
      "metric_definition": "caller affected dimension",
      "unit": "m",
      "maximum_value": 0.01,
      "range_basis": "caller plan",
      "caller_disposition_id_if_outside": "engineering-review"
    }
  ],
  "alloy_composition_and_phase_reviewed": true,
  "environment_temperature_and_pH_reviewed": true,
  "redox_or_potential_basis_reviewed": true,
  "exposure_clock_reviewed": true,
  "microscopy_and_composition_observations_reviewed": true,
  "measurement_units_and_uncertainty_reviewed": true,
  "qualification_tests_envelopes_and_ranges_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored leaching assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/selective_leaching.py#L204)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
