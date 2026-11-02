# `degradation.alkaline_scc_applicability`

**목적:** Material, heat treatment, alkaline chemistry, temperature, electrochemical descriptor, stresses and duration are checked only against caller-qualified evidence envelopes.

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
| `heat_treatment_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `qualification_tests` | 예 | `{"items": {"$ref": "#/$defs/AlkalineSCCTestEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelopes` | 예 | `{"items": {"$ref": "#/$defs/AlkalineSCCQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposure_intervals` | 예 | `{"items": {"$ref": "#/$defs/AlkalineExposureInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_heat_treatment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `alkaline_chemistry_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `electrochemical_descriptor_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applied_and_residual_stress_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_tests_and_envelopes_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AlkalineSCCApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `qualification_test_count` | `count` |
| `qualification_envelope_count` | `count` |
| `exposure_interval_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, heat treatment, alkaline chemistry, temperature, electrochemical descriptor, stresses and duration are checked only against caller-qualified evidence envelopes.
- Invalid or unmatched evidence needs data; valid exposure outside an otherwise complete declared envelope remains outside model scope.

## 구현 근거·독립 설명

- `alkaline_scc_qualification_envelope_accounting`: Match material and heat-treatment identities, alkaline species and exact concentration unit, temperature, electrochemical descriptor, reference and potential, applied and residual stress descriptors, and exposure duration to linked caller-owned qualification evidence. Do not infer SCC thresholds, initiation, growth, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.alkaline_scc_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.alkaline_scc_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-alkaline-scc",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-exposure-clock",
  "material_condition_id": "material-a",
  "heat_treatment_condition_id": "heat-treatment-a",
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
          "citation": "authored alkaline test"
        }
      ]
    }
  ],
  "qualification_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_ids": [
        "material-a"
      ],
      "heat_treatment_condition_ids": [
        "heat-treatment-a"
      ],
      "alkaline_species_id": "species-a",
      "concentration_unit": "mol/m^3",
      "minimum_concentration": 10.0,
      "maximum_concentration": 100.0,
      "minimum_temperature_K": 280.0,
      "maximum_temperature_K": 350.0,
      "electrochemical_descriptor_id": "controlled-potential",
      "potential_reference_id": "reference-a",
      "minimum_potential_V": -0.5,
      "maximum_potential_V": -0.2,
      "applied_stress_definition": "caller applied stress",
      "minimum_applied_stress_Pa": 0.0,
      "maximum_applied_stress_Pa": 200000000.0,
      "residual_stress_definition": "caller residual stress",
      "minimum_residual_stress_Pa": -50000000.0,
      "maximum_residual_stress_Pa": 250000000.0,
      "maximum_exposure_duration_s": 10000.0,
      "test_evidence_ids": [
        "test-1"
      ],
      "applicability_basis": "caller envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored alkaline envelope"
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
      "alkaline_species_id": "species-a",
      "concentration": 50.0,
      "concentration_unit": "mol/m^3",
      "temperature_K": 320.0,
      "electrochemical_descriptor_id": "controlled-potential",
      "potential_reference_id": "reference-a",
      "potential_V": -0.3,
      "applied_stress_definition": "caller applied stress",
      "applied_stress_Pa": 100000000.0,
      "residual_stress_definition": "caller residual stress",
      "residual_stress_Pa": 50000000.0,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored alkaline exposure"
        }
      ]
    }
  ],
  "material_and_heat_treatment_reviewed": true,
  "alkaline_chemistry_and_units_reviewed": true,
  "temperature_history_reviewed": true,
  "electrochemical_descriptor_reviewed": true,
  "applied_and_residual_stress_reviewed": true,
  "exposure_clock_reviewed": true,
  "qualification_tests_and_envelopes_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored alkaline assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/alkaline_scc.py#L161)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
