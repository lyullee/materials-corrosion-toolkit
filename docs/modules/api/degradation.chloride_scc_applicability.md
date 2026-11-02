# `degradation.chloride_scc_applicability`

**목적:** Material condition and metallurgy identities must match the caller-owned test envelope exactly.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `metallurgy_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposures` | 예 | `{"items": {"$ref": "#/$defs/ChlorideSCCExposure"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/ChlorideSCCEnvelope"}` | 계약·필드 설명 참조 |
| `material_and_metallurgy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `concentration_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `environment_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_descriptors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_duration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ChlorideSCCApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `exposure_comparisons` | `1` |
| `cumulative_exposure_s` | `s` |
| `remaining_supported_exposure_s` | `s` |
| `cumulative_exposure_within_support` | `1` |
| `outside_support_exposure_ids` | `1` |
| `test_evidence_summary` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material condition and metallurgy identities must match the caller-owned test envelope exactly.
- Chloride and dissolved-oxygen values are compared only when their unit tokens match exactly; no hidden conversion is performed.
- Applied and residual stress states are caller-defined descriptors, not calculated stresses or thresholds.

## 구현 근거·독립 설명

- `declared_chloride_scc_qualification_envelope`: Match material and metallurgical condition, chloride-unit convention, oxidizing-state or dissolved-oxygen basis, and applied or residual stress descriptor to caller-owned qualification evidence, then compare reviewed temperature, pH and exposure support. Do not infer SCC thresholds, initiation, growth, lifetime, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.chloride_scc_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.chloride_scc_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-chloride-scc",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "wetted-region-1",
  "clock_id": "authored-service-clock",
  "material_condition_id": "material-1",
  "metallurgy_id": "metallurgy-1",
  "exposures": [
    {
      "exposure_id": "e1",
      "start_time_s": 0.0,
      "end_time_s": 1000.0,
      "chloride_concentration": 0.5,
      "chloride_unit": "kg/m^3",
      "temperature_K": 320.0,
      "pH": 7.0,
      "oxidizing_basis": "dissolved_oxygen",
      "dissolved_oxygen_concentration": 0.01,
      "dissolved_oxygen_unit": "kg/m^3",
      "oxidizing_state_descriptor": null,
      "applied_stress_descriptor": "operating-a",
      "residual_stress_descriptor": "residual-a",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored SCC exposure"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "scc-envelope-1",
    "material_condition_id": "material-1",
    "metallurgy_id": "metallurgy-1",
    "chloride_unit": "kg/m^3",
    "minimum_chloride_concentration": 0.0,
    "maximum_chloride_concentration": 1.0,
    "minimum_temperature_K": 280.0,
    "maximum_temperature_K": 350.0,
    "minimum_pH": 5.0,
    "maximum_pH": 9.0,
    "oxidizing_basis": "dissolved_oxygen",
    "dissolved_oxygen_unit": "kg/m^3",
    "minimum_dissolved_oxygen_concentration": 0.0,
    "maximum_dissolved_oxygen_concentration": 0.02,
    "supported_oxidizing_state_descriptors": [],
    "supported_applied_stress_descriptors": [
      "operating-a"
    ],
    "supported_residual_stress_descriptors": [
      "residual-a"
    ],
    "maximum_cumulative_exposure_s": 2000.0,
    "test_evidence": [
      {
        "evidence_record_id": "evidence-1",
        "test_id": "test-1",
        "specimen_id": "specimen-1",
        "source_group_id": "group-1",
        "material_condition_id": "material-1",
        "metallurgy_id": "metallurgy-1",
        "record_valid": true,
        "supports_declared_envelope": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored SCC evidence"
          }
        ]
      }
    ],
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored SCC envelope"
      }
    ]
  },
  "material_and_metallurgy_reviewed": true,
  "concentration_units_reviewed": true,
  "environment_records_reviewed": true,
  "stress_descriptors_reviewed": true,
  "clock_and_duration_reviewed": true,
  "qualification_evidence_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/chloride_scc.py#L153)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
