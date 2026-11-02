# `degradation.sour_environment_applicability`

**목적:** Material, units, H2S partial-pressure definition and stress-state descriptors use exact matching.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_grade_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_heat_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `microstructure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `hardness_value` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `hardness_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `h2s_partial_pressure_Pa_abs` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `h2s_partial_pressure_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pH` | 예 | `{"maximum": 14, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `chloride_concentration` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `chloride_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_duration_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `stress_state_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_records` | 예 | `{"items": {"$ref": "#/$defs/SourEnvironmentTestRecord"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/SourApplicabilityEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_identity_and_hardness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `media_composition_and_pH_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_partial_pressure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_exposure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_partition_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_transfer_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SourEnvironmentApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `material_grade_id` | `1` |
| `material_heat_id` | `1` |
| `selected_envelope_id` | `1` |
| `identity_matching_envelope_ids` | `1` |
| `fully_matching_envelope_ids` | `1` |
| `test_record_count_by_partition` | `1` |
| `candidate_diagnostics` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, units, H2S partial-pressure definition and stress-state descriptors use exact matching.
- Numerical service conditions are compared only with caller-qualified ranges.
- Only calibration-partition records may be cited as defining an envelope.

## 구현 근거·독립 설명

- `declared_sour_environment_applicability_envelope`: Match material grade, heat, microstructure, hardness-unit convention, absolute H2S partial-pressure basis and stress descriptor to caller-owned qualification envelopes, then compare reviewed pH, temperature, chloride and exposure ranges with partitioned test evidence. Do not supply standard thresholds, SSC or HIC rates, crack growth, lifetime or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.sour_environment_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.sour_environment_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-sour-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "material_grade_id": "steel-a",
  "material_heat_id": "heat-1",
  "microstructure_id": "tempered",
  "hardness_value": 220.0,
  "hardness_unit_token": "HV",
  "h2s_partial_pressure_Pa_abs": 10000.0,
  "h2s_partial_pressure_basis": "reviewed gas partial pressure",
  "pH": 4.0,
  "temperature_K": 300.0,
  "chloride_concentration": 3.0,
  "chloride_unit_token": "mass_percent",
  "exposure_duration_s": 100000.0,
  "stress_state_descriptor": "constant-tensile",
  "test_records": [
    {
      "test_record_id": "cal-1",
      "source_group_id": "group-cal",
      "partition": "calibration",
      "material_grade_id": "steel-a",
      "material_heat_id": "heat-1",
      "microstructure_id": "tempered",
      "hardness_value": 220.0,
      "hardness_unit_token": "HV",
      "h2s_partial_pressure_Pa_abs": 10000.0,
      "h2s_partial_pressure_basis": "reviewed gas partial pressure",
      "pH": 4.0,
      "temperature_K": 300.0,
      "chloride_concentration": 3.0,
      "chloride_unit_token": "mass_percent",
      "exposure_duration_s": 100000.0,
      "stress_state_descriptor": "constant-tensile",
      "reported_outcome": "authored calibration outcome",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored sour test"
        }
      ]
    },
    {
      "test_record_id": "hold-1",
      "source_group_id": "group-hold",
      "partition": "holdout",
      "material_grade_id": "steel-a",
      "material_heat_id": "heat-1",
      "microstructure_id": "tempered",
      "hardness_value": 220.0,
      "hardness_unit_token": "HV",
      "h2s_partial_pressure_Pa_abs": 10000.0,
      "h2s_partial_pressure_basis": "reviewed gas partial pressure",
      "pH": 4.0,
      "temperature_K": 300.0,
      "chloride_concentration": 3.0,
      "chloride_unit_token": "mass_percent",
      "exposure_duration_s": 100000.0,
      "stress_state_descriptor": "constant-tensile",
      "reported_outcome": "authored holdout outcome",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored sour test"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "sour-envelope-1",
      "material_grade_id": "steel-a",
      "heat_applicability": "exact_heats",
      "applicable_heat_ids": [
        "heat-1"
      ],
      "applicable_microstructure_ids": [
        "tempered"
      ],
      "hardness_min": 180.0,
      "hardness_max": 250.0,
      "hardness_unit_token": "HV",
      "h2s_partial_pressure_min_Pa_abs": 1000.0,
      "h2s_partial_pressure_max_Pa_abs": 20000.0,
      "h2s_partial_pressure_basis": "reviewed gas partial pressure",
      "pH_min": 3.0,
      "pH_max": 5.0,
      "temperature_min_K": 280.0,
      "temperature_max_K": 330.0,
      "chloride_min": 0.0,
      "chloride_max": 5.0,
      "chloride_unit_token": "mass_percent",
      "exposure_duration_min_s": 1000.0,
      "exposure_duration_max_s": 200000.0,
      "applicable_stress_state_descriptors": [
        "constant-tensile"
      ],
      "qualification_test_record_ids": [
        "cal-1"
      ],
      "applicability_basis": "caller-owned test envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored sour envelope"
        }
      ]
    }
  ],
  "material_identity_and_hardness_reviewed": true,
  "media_composition_and_pH_reviewed": true,
  "absolute_partial_pressure_reviewed": true,
  "temperature_and_exposure_reviewed": true,
  "stress_state_reviewed": true,
  "test_partition_independence_reviewed": true,
  "envelope_authority_reviewed": true,
  "heat_transfer_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored sour assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/sour_environment.py#L188)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
