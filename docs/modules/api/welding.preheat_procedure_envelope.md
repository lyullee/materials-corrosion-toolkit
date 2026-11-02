# `welding.preheat_procedure_envelope`

**목적:** Material, joint, process, consumable, hydrogen-control and restraint identities match exactly.

**모델 버전:** `0.1.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `weld_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `consumable_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `hydrogen_control_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `restraint_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `governing_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `net_heat_input_J_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_recorded_preheat_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `maximum_recorded_interpass_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `below_preheat_duration_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `above_interpass_duration_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `minimum_recorded_interpass_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `below_interpass_duration_s` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredPreheatProcedureEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_joint_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `consumable_and_hydrogen_control_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `restraint_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thickness_and_heat_input_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `procedure_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WeldPreheatProcedureAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `selected_envelope_id` | `1` |
| `preheat_temperature_margin_K` | `K` |
| `interpass_temperature_margin_K` | `K` |
| `minimum_interpass_temperature_margin_K` | `K` |
| `below_interpass_duration_s` | `s` |
| `below_preheat_duration_s` | `s` |
| `above_interpass_duration_s` | `s` |
| `record_within_declared_procedure_envelope` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, joint, process, consumable, hydrogen-control and restraint identities match exactly.
- Thickness, heat-input and temperature requirements are supplied by a reviewed caller-owned procedure envelope.

## 구현 근거·독립 설명

- `declared_weld_preheat_procedure_envelope`: Match material, joint, process, consumable, hydrogen-control and restraint identities exactly, then compare thickness, net heat input, recorded preheat and interpass temperatures with a caller-owned procedure envelope. Do not supply welding-code tables, weldability, hydrogen-cracking resistance, mechanical properties or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.preheat_procedure_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.preheat_procedure_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-preheat-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "weld_id": "weld-1",
  "material_condition_id": "material-1",
  "joint_configuration_id": "joint-a",
  "welding_process_id": "process-a",
  "consumable_condition_id": "consumable-a",
  "hydrogen_control_descriptor": "control-a",
  "restraint_descriptor": "restraint-a",
  "governing_thickness_m": 0.02,
  "net_heat_input_J_m": 1000000.0,
  "minimum_recorded_preheat_temperature_K": 380.0,
  "maximum_recorded_interpass_temperature_K": 450.0,
  "below_preheat_duration_s": 0.0,
  "above_interpass_duration_s": 0.0,
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "material-1",
      "joint_configuration_id": "joint-a",
      "welding_process_id": "process-a",
      "consumable_condition_id": "consumable-a",
      "hydrogen_control_descriptor": "control-a",
      "restraint_descriptor": "restraint-a",
      "minimum_thickness_m": 0.01,
      "maximum_thickness_m": 0.03,
      "minimum_net_heat_input_J_m": 500000.0,
      "maximum_net_heat_input_J_m": 1500000.0,
      "minimum_required_preheat_temperature_K": 370.0,
      "maximum_supported_interpass_temperature_K": 460.0,
      "applicability_basis": "caller procedure qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored preheat envelope"
        }
      ]
    }
  ],
  "material_and_joint_identity_reviewed": true,
  "consumable_and_hydrogen_control_reviewed": true,
  "restraint_reviewed": true,
  "thickness_and_heat_input_reviewed": true,
  "temperature_records_reviewed": true,
  "procedure_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored preheat assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding_preheat.py#L102)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
