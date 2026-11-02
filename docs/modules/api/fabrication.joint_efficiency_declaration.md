# `fabrication.joint_efficiency_declaration`

**목적:** Joint, process, material group, examination method and physical scope are caller-reviewed exact identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `examination_record` | 예 | `{"$ref": "#/$defs/JointExaminationRecord"}` | 계약·필드 설명 참조 |
| `candidate_rules` | 예 | `{"items": {"$ref": "#/$defs/DeclaredJointEfficiencyRule"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `joint_process_and_material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_scope_and_extent_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `examination_method_and_record_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rule_revision_and_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorization_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/JointEfficiencyDeclaration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `joint_id` | `1` |
| `physical_scope_id` | `1` |
| `selected_rule_id` | `1` |
| `rule_set_id` | `1` |
| `rule_revision` | `1` |
| `declared_requirement_outcome` | `1` |
| `examined_extent_fraction` | `1` |
| `minimum_examination_extent_fraction` | `1` |
| `maximum_examination_extent_fraction` | `1` |
| `declared_joint_efficiency_factor` | `1` |
| `computational_use_authorized` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Joint, process, material group, examination method and physical scope are caller-reviewed exact identities.
- Rule revision, extent support, efficiency factor and computational-use authorization are supplied by the caller.
- A declared factor is returned only when the exact examination extent lies inside the selected rule support.

## 구현 근거·독립 설명

- `caller_licensed_joint_efficiency_rule_evaluation`: Select exactly one caller-supplied and computationally authorized joint-efficiency rule by joint, process, material group and examination method, then return its declared factor only when the exact examined extent is inside rule support. Preserve revision and content digests; do not bundle code tables, substitute factors, calculate strength or capacity, infer inspection reliability, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.joint_efficiency_declaration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.joint_efficiency_declaration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-joint-efficiency",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "joint_id": "joint-1",
  "physical_scope_id": "scope-1",
  "joint_configuration_id": "joint-configuration-1",
  "welding_process_id": "process-1",
  "material_group_id": "material-group-1",
  "examination_record": {
    "examination_record_id": "examination-record-1",
    "joint_id": "joint-1",
    "physical_scope_id": "scope-1",
    "examination_method_id": "examination-1",
    "examined_extent_fraction": 0.75,
    "extent_definition": "authored examined joint-length fraction",
    "provider_id": "inspection-provider",
    "provider_version": "1",
    "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored examination record"
      }
    ]
  },
  "candidate_rules": [
    {
      "rule_id": "rule-1",
      "rule_set_id": "caller-rule-set",
      "rule_revision": "revision-1",
      "joint_configuration_id": "joint-configuration-1",
      "welding_process_id": "process-1",
      "material_group_id": "material-group-1",
      "examination_method_id": "examination-1",
      "minimum_examination_extent_fraction": 0.5,
      "maximum_examination_extent_fraction": 1.0,
      "declared_joint_efficiency_factor": 0.85,
      "provider_id": "rule-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "rule_content_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "computational_use_authorized": true,
      "authorization_basis": "caller confirms licensed computational use",
      "applicability_basis": "caller-reviewed rule applicability",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored rule"
        }
      ]
    }
  ],
  "joint_process_and_material_identity_reviewed": true,
  "physical_scope_and_extent_definition_reviewed": true,
  "examination_method_and_record_reviewed": true,
  "rule_revision_and_applicability_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "computational_use_authorization_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored joint-efficiency assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/joint_efficiency.py#L91)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
