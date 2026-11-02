# `welding.temper_bead_qualification`

**목적:** Repair scope, joint, base/deposited material conditions and process match exactly.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `repair_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `deposited_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pass_records` | 예 | `{"items": {"$ref": "#/$defs/TemperBeadPassRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/TemperBeadObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/TemperBeadQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `repair_joint_and_material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deposition_sequence_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_input_and_interpass_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temper_bead_descriptors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_methods_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_and_source_group_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TemperBeadQualificationAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `repair_scope_id` | `1` |
| `qualification_envelope_id` | `1` |
| `observed_layer_sequence` | `1` |
| `required_layer_sequence` | `1` |
| `layer_sequence_matches` | `1` |
| `outside_support_pass_record_ids` | `1` |
| `outside_support_observation_ids` | `1` |
| `physical_specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `observation_requirement_comparisons` | `mixed` |
| `declared_qualification_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Repair scope, joint, base/deposited material conditions and process match exactly.
- Pass order, heat input, interpass temperature and descriptor support are caller declarations.
- Observation support does not establish code acceptance, metallurgy or crack probability.

## 구현 근거·독립 설명

- `reviewed_temper_bead_qualification_envelope`: Compare an ordered non-overlapping deposition-pass and layer sequence, heat input, interpass temperature and temper-bead descriptors with caller-owned hardness, microstructure or NDE evidence. Preserve specimen/source partitions and provider digests; do not bundle code limits or infer metallurgy, cracking, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.temper_bead_qualification"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.temper_bead_qualification"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-temper-bead",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "repair_scope_id": "repair-1",
  "joint_configuration_id": "joint-1",
  "base_material_condition_id": "base-1",
  "deposited_material_condition_id": "deposit-1",
  "welding_process_id": "process-1",
  "clock_id": "clock-1",
  "pass_records": [
    {
      "pass_record_id": "pass-1",
      "sequence_position": 1,
      "layer_id": "layer-1",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "heat_input_value": 1.0,
      "heat_input_unit_token": "custom-energy-per-length",
      "interpass_temperature_K": 400.0,
      "temper_bead_descriptor": "caller-sequence-a",
      "provider_id": "recorder-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored pass"
        }
      ]
    },
    {
      "pass_record_id": "pass-2",
      "sequence_position": 2,
      "layer_id": "layer-2",
      "start_time_s": 10.0,
      "end_time_s": 20.0,
      "heat_input_value": 1.0,
      "heat_input_unit_token": "custom-energy-per-length",
      "interpass_temperature_K": 400.0,
      "temper_bead_descriptor": "caller-sequence-a",
      "provider_id": "recorder-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored pass"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "obs-1",
      "observation_kind": "hardness",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "physical_region_id": "haz-1",
      "method_id": "hardness-method",
      "result_definition": "caller hardness metric",
      "reported_value": 250.0,
      "result_unit_token": "custom-hardness-unit",
      "expanded_uncertainty": 5.0,
      "uncertainty_coverage_factor": 2.0,
      "provider_id": "laboratory-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored temper-bead observation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "repair_scope_id": "repair-1",
      "joint_configuration_id": "joint-1",
      "base_material_condition_id": "base-1",
      "deposited_material_condition_id": "deposit-1",
      "welding_process_id": "process-1",
      "required_layer_sequence": [
        "layer-1",
        "layer-2"
      ],
      "supported_temper_bead_descriptors": [
        "caller-sequence-a"
      ],
      "minimum_heat_input_value": 0.5,
      "maximum_heat_input_value": 1.5,
      "heat_input_unit_token": "custom-energy-per-length",
      "minimum_interpass_temperature_K": 350.0,
      "maximum_interpass_temperature_K": 450.0,
      "observation_requirements": [
        {
          "requirement_id": "hardness-1",
          "observation_kind": "hardness",
          "method_id": "hardness-method",
          "result_definition": "caller hardness metric",
          "result_unit_token": "custom-hardness-unit",
          "minimum_value": 200.0,
          "maximum_value": 300.0,
          "requirement_basis": "authored plan"
        }
      ],
      "minimum_physical_specimen_count": 1,
      "minimum_source_group_count": 1,
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored temper-bead envelope"
        }
      ]
    }
  ],
  "repair_joint_and_material_identity_reviewed": true,
  "deposition_sequence_and_clock_reviewed": true,
  "heat_input_and_interpass_temperature_reviewed": true,
  "temper_bead_descriptors_reviewed": true,
  "observation_methods_units_and_uncertainty_reviewed": true,
  "specimen_and_source_group_partitions_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/temper_bead.py#L196)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
