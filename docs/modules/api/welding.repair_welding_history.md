# `welding.repair_welding_history`

**목적:** Recorded repair steps use one reviewed clock, remain ordered and cannot overlap.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `repair_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `steps` | 예 | `{"items": {"$ref": "#/$defs/RepairWeldingStep"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_workflow_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredRepairWorkflowEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `repair_scope_and_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sequence_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `procedure_and_provider_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `step_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `workflow_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/RepairWeldingHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `selected_workflow_envelope_id` | `1` |
| `recorded_step_kind_counts` | `count` |
| `recorded_stage_sequence` | `1` |
| `required_stage_sequence` | `1` |
| `stage_sequence_matches_exactly` | `1` |
| `missing_required_stage_ids` | `1` |
| `unrecognized_stage_ids` | `1` |
| `stage_comparisons` | `mixed` |
| `identity_mismatch_stage_ids` | `1` |
| `missing_required_metric_ids` | `1` |
| `unit_mismatch_metric_ids` | `1` |
| `outside_declared_metric_envelope_ids` | `1` |
| `all_steps_within_declared_workflow_envelope` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Recorded repair steps use one reviewed clock, remain ordered and cannot overlap.
- The exact stage sequence, procedure/provider revisions, state digests and metric envelopes are supplied by the caller.
- Missing stages, metrics, units or invalid evidence remain explicit and prevent a complete result.

## 구현 근거·독립 설명

- `declared_repair_welding_workflow_accounting`: Compare an ordered, non-overlapping repair-welding history with an exact caller-owned sequence of removal, inspection, deposition, heat-treatment and subsequent-examination stages, provider digests and metric envelopes. Do not infer repair effectiveness, structural integrity, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.repair_welding_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.repair_welding_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "authored-repair-history",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "repair_scope_id": "repair-scope-1",
  "component_condition_id": "condition-1",
  "clock_id": "repair-clock",
  "horizon_start_s": 0.0,
  "horizon_end_s": 100.0,
  "steps": [
    {
      "step_record_id": "step-1",
      "stage_id": "removal",
      "step_kind": "removal",
      "physical_scope_id": "scope-1",
      "location_id": "synthetic",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "procedure_id": "procedure-1",
      "procedure_revision": "1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "activity_descriptor": "authored removal",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair step"
        }
      ]
    },
    {
      "step_record_id": "step-2",
      "stage_id": "pre-inspection",
      "step_kind": "pre_deposition_inspection",
      "physical_scope_id": "scope-1",
      "location_id": "synthetic",
      "start_time_s": 20.0,
      "end_time_s": 30.0,
      "procedure_id": "procedure-1",
      "procedure_revision": "1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "activity_descriptor": "authored pre-inspection",
      "reported_finding_or_outcome": "recorded observation",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair step"
        }
      ]
    },
    {
      "step_record_id": "step-3",
      "stage_id": "deposition",
      "step_kind": "deposition",
      "physical_scope_id": "scope-1",
      "location_id": "synthetic",
      "start_time_s": 40.0,
      "end_time_s": 50.0,
      "procedure_id": "procedure-1",
      "procedure_revision": "1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "activity_descriptor": "authored deposition",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair step"
        }
      ]
    },
    {
      "step_record_id": "step-4",
      "stage_id": "heat-treatment",
      "step_kind": "heat_treatment",
      "physical_scope_id": "scope-1",
      "location_id": "synthetic",
      "start_time_s": 60.0,
      "end_time_s": 70.0,
      "procedure_id": "procedure-1",
      "procedure_revision": "1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "activity_descriptor": "authored heat treatment",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair step"
        }
      ]
    },
    {
      "step_record_id": "step-5",
      "stage_id": "final-examination",
      "step_kind": "subsequent_examination",
      "physical_scope_id": "scope-1",
      "location_id": "synthetic",
      "start_time_s": 80.0,
      "end_time_s": 90.0,
      "procedure_id": "procedure-1",
      "procedure_revision": "1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "activity_descriptor": "authored final examination",
      "reported_finding_or_outcome": "recorded observation",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair step"
        }
      ]
    }
  ],
  "candidate_workflow_envelopes": [
    {
      "envelope_id": "workflow-1",
      "repair_scope_id": "repair-scope-1",
      "component_condition_id": "condition-1",
      "repair_location_id": "synthetic",
      "required_stages": [
        {
          "stage_id": "removal",
          "step_kind": "removal",
          "procedure_id": "procedure-1",
          "procedure_revision": "1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "required_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "required_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "requirement_basis": "authored workflow",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored repair workflow"
            }
          ]
        },
        {
          "stage_id": "pre-inspection",
          "step_kind": "pre_deposition_inspection",
          "procedure_id": "procedure-1",
          "procedure_revision": "1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "required_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "required_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "requirement_basis": "authored workflow",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored repair workflow"
            }
          ]
        },
        {
          "stage_id": "deposition",
          "step_kind": "deposition",
          "procedure_id": "procedure-1",
          "procedure_revision": "1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "required_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "required_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "requirement_basis": "authored workflow",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored repair workflow"
            }
          ]
        },
        {
          "stage_id": "heat-treatment",
          "step_kind": "heat_treatment",
          "procedure_id": "procedure-1",
          "procedure_revision": "1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "required_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "required_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "requirement_basis": "authored workflow",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored repair workflow"
            }
          ]
        },
        {
          "stage_id": "final-examination",
          "step_kind": "subsequent_examination",
          "procedure_id": "procedure-1",
          "procedure_revision": "1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "required_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "required_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "requirement_basis": "authored workflow",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored repair workflow"
            }
          ]
        }
      ],
      "declaration_basis": "authored caller workflow",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored repair workflow"
        }
      ]
    }
  ],
  "repair_scope_and_location_reviewed": true,
  "sequence_and_clock_reviewed": true,
  "procedure_and_provider_identity_reviewed": true,
  "provider_digests_reviewed": true,
  "step_evidence_reviewed": true,
  "workflow_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/repair_welding.py#L173)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
