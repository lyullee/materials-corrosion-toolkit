# `welding.reheat_cracking_applicability`

**목적:** Material, weld, HAZ and welding-process identities are exact caller-reviewed tokens.

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
| `weld_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `haz_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `heat_input_value` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `heat_input_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thermal_history` | 예 | `{"items": {"$ref": "#/$defs/ReheatThermalInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `stress_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_value` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `stress_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `restraint_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/ReheatCrackingEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_weld_and_haz_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `welding_process_and_heat_input_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_treatment_clock_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_and_restraint_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_region_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_method_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ReheatCrackingApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `clock_id` | `1` |
| `envelope_id` | `1` |
| `cumulative_reheat_duration_s` | `s` |
| `outside_thermal_interval_ids` | `1` |
| `qualification_source_group_count` | `1` |
| `unsupported_qualification_observation_ids` | `1` |
| `outside_support_reasons` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, weld, HAZ and welding-process identities are exact caller-reviewed tokens.
- Temperature, time, stress, restraint and heat-input support comes from caller-owned evidence.
- Qualification observations preserve specimen, source group, method, units, uncertainty and digests.

## 구현 근거·독립 설명

- `reviewed_reheat_cracking_qualification_envelope`: Compare exact material, weld and heat-affected-zone condition, welding process, heat input, ordered reheat history, stress and restraint descriptors with partitioned caller-owned qualification evidence. Do not bundle material rankings or infer cracking susceptibility, probability, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.reheat_cracking_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.reheat_cracking_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-reheat",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "haz-scope-1",
  "clock_id": "clock-1",
  "material_condition_id": "material-1",
  "weld_condition_id": "weld-1",
  "haz_condition_id": "haz-condition-1",
  "welding_process_id": "process-1",
  "heat_input_value": 1.0,
  "heat_input_unit_token": "custom-heat-input",
  "thermal_history": [
    {
      "interval_id": "interval-1",
      "stage_kind": "postweld_heat_treatment",
      "start_time_s": 0.0,
      "end_time_s": 3600.0,
      "minimum_temperature_K": 750.0,
      "maximum_temperature_K": 800.0,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored reheat interval"
        }
      ]
    }
  ],
  "stress_descriptor": "residual-plus-applied",
  "stress_value": 100.0,
  "stress_unit_token": "custom-stress",
  "restraint_descriptor": "high-restraint",
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "material-1",
      "weld_condition_id": "weld-1",
      "haz_condition_id": "haz-condition-1",
      "welding_process_id": "process-1",
      "heat_input_unit_token": "custom-heat-input",
      "minimum_heat_input_value": 0.5,
      "maximum_heat_input_value": 2.0,
      "minimum_reheat_temperature_K": 700.0,
      "maximum_reheat_temperature_K": 1000.0,
      "maximum_cumulative_reheat_duration_s": 7200.0,
      "stress_unit_token": "custom-stress",
      "minimum_stress_value": 0.0,
      "maximum_stress_value": 200.0,
      "supported_stress_descriptors": [
        "residual-plus-applied"
      ],
      "supported_restraint_descriptors": [
        "high-restraint"
      ],
      "supported_region_ids": [
        "haz-1"
      ],
      "supported_method_ids": [
        "method-1"
      ],
      "minimum_qualification_source_group_count": 1,
      "qualification_observations": [
        {
          "observation_id": "obs-1",
          "physical_specimen_id": "specimen-1",
          "source_group_id": "source-1",
          "partition": "qualification",
          "region_id": "haz-1",
          "method_id": "method-1",
          "metric_definition": "caller-defined examination metric",
          "reported_value": 0.1,
          "unit_token": "custom-metric",
          "expanded_uncertainty": 0.01,
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored reheat observation"
            }
          ]
        }
      ],
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored reheat envelope"
        }
      ]
    }
  ],
  "material_weld_and_haz_identity_reviewed": true,
  "welding_process_and_heat_input_reviewed": true,
  "heat_treatment_clock_and_temperature_reviewed": true,
  "stress_and_restraint_basis_reviewed": true,
  "specimen_region_and_source_groups_reviewed": true,
  "observation_method_units_and_uncertainty_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored reheat assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reheat_cracking.py#L169)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
