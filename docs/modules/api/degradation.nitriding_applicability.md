# `degradation.nitriding_applicability`

**목적:** Material, condition, nitrogen species and driving-force basis, temperature, absolute pressure, gas environment and duration are compared only with caller-qualified evidence envelopes.

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
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `qualification_tests` | 예 | `{"items": {"$ref": "#/$defs/NitridingTestEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelopes` | 예 | `{"items": {"$ref": "#/$defs/NitridingQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposure_intervals` | 예 | `{"items": {"$ref": "#/$defs/NitridingExposureInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `nitrogen_species_basis_and_unit_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_pressure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `gas_environment_descriptor_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_tests_and_envelopes_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/NitridingApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `qualification_test_count` | `count` |
| `qualification_envelope_count` | `count` |
| `exposure_interval_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, condition, nitrogen species and driving-force basis, temperature, absolute pressure, gas environment and duration are compared only with caller-qualified evidence envelopes.
- Invalid or unmatched evidence needs data; valid exposure outside an otherwise complete declared envelope remains outside model scope.

## 구현 근거·독립 설명

- `nitriding_qualification_envelope_accounting`: Match material condition, nitrogen species, exact driving-force basis and unit, temperature, absolute pressure, gas descriptor and exposure duration to linked caller-owned qualification evidence. Do not infer nitrogen profiles, diffusion, kinetics, nitride phase or property changes, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.nitriding_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.nitriding_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-nitriding",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-exposure-clock",
  "material_id": "alloy-a",
  "material_condition_id": "condition-a",
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
          "citation": "authored nitriding test"
        }
      ]
    }
  ],
  "qualification_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_ids": [
        "alloy-a"
      ],
      "material_condition_ids": [
        "condition-a"
      ],
      "nitrogen_species_id": "species-a",
      "nitrogen_driving_force_basis": "caller activity definition",
      "nitrogen_driving_force_unit": "1",
      "minimum_nitrogen_driving_force": 0.1,
      "maximum_nitrogen_driving_force": 0.8,
      "minimum_temperature_K": 600.0,
      "maximum_temperature_K": 900.0,
      "minimum_pressure_Pa_abs": 90000.0,
      "maximum_pressure_Pa_abs": 200000.0,
      "gas_environment_descriptor_id": "gas-a",
      "maximum_exposure_duration_s": 10000.0,
      "test_evidence_ids": [
        "test-1"
      ],
      "applicability_basis": "caller envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored nitriding envelope"
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
      "nitrogen_species_id": "species-a",
      "nitrogen_driving_force_basis": "caller activity definition",
      "nitrogen_driving_force_unit": "1",
      "nitrogen_driving_force": 0.5,
      "temperature_K": 750.0,
      "pressure_Pa_abs": 101325.0,
      "gas_environment_descriptor_id": "gas-a",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored nitriding exposure"
        }
      ]
    }
  ],
  "material_and_condition_reviewed": true,
  "nitrogen_species_basis_and_unit_reviewed": true,
  "temperature_history_reviewed": true,
  "absolute_pressure_reviewed": true,
  "gas_environment_descriptor_reviewed": true,
  "exposure_clock_reviewed": true,
  "qualification_tests_and_envelopes_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored nitriding assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/nitriding_degradation.py#L146)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
