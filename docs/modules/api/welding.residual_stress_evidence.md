# `welding.residual_stress_evidence`

**목적:** Each residual-stress value retains its declared tensor-component meaning and coordinate frame.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

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
| `records` | 예 | `{"items": {"$ref": "#/$defs/ResidualStressEvidenceRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_supports` | 예 | `{"items": {"$ref": "#/$defs/DeclaredResidualStressSupport"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `weld_and_material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coordinate_frames_and_components_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_identity_and_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_holdout_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ResidualStressEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `weld_id` | `1` |
| `material_condition_id` | `1` |
| `record_count` | `1` |
| `partition_counts` | `1` |
| `partition_record_ids` | `mixed` |
| `record_source_lineage` | `mixed` |
| `provider_support_lineage` | `mixed` |
| `record_comparisons` | `mixed` |
| `application_record_count` | `1` |
| `application_compared_record_count` | `1` |
| `application_records_within_declared_support_count` | `1` |
| `all_application_records_within_declared_support` | `1` |
| `unsupported_application_record_ids` | `1` |
| `unmatched_application_record_ids` | `1` |
| `ambiguous_application_record_ids` | `1` |
| `record_match_issue_reasons` | `mixed` |
| `unmatched_record_ids` | `1` |
| `ambiguous_record_ids` | `1` |
| `invalid_qualification_support_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each residual-stress value retains its declared tensor-component meaning and coordinate frame.
- The full declared expanded-uncertainty interval must remain inside provider stress support.
- Calibration, holdout and application source groups must be mutually disjoint.
- Provider identity, version, state digest and caller-owned support are exact-match evidence contracts.
- Calibration and holdout source groups are independent when the provider qualification declares them independent.

## 구현 근거·독립 설명

- `reviewed_residual_stress_evidence_record`: Map measured or modelled residual-stress components and uncertainty to exact coordinate, provider, calibration and holdout support supplied by the caller. Do not infer redistribution, fracture, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.residual_stress_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.residual_stress_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-residual-stress",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "weld_id": "weld-1",
  "material_condition_id": "condition-1",
  "records": [
    {
      "record_id": "record-1",
      "method_kind": "modelled",
      "provider_id": "solver-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "partition": "application",
      "source_group_id": "application-1",
      "component_definition": "axial normal stress",
      "coordinate_frame_id": "weld-local",
      "coordinate_frame_definition_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "coordinate_names": [
        "distance_along_weld",
        "depth"
      ],
      "coordinates_m": [
        0.01,
        0.002
      ],
      "stress_Pa": 120000000.0,
      "expanded_uncertainty_Pa": 10000000.0,
      "coverage_factor": 2.0,
      "uncertainty_basis": "authored uncertainty",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored residual-stress record"
        }
      ]
    }
  ],
  "candidate_supports": [
    {
      "support_id": "support-1",
      "method_kind": "modelled",
      "provider_id": "solver-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "component_definition": "axial normal stress",
      "coordinate_frame_id": "weld-local",
      "coordinate_frame_definition_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "coordinate_names": [
        "distance_along_weld",
        "depth"
      ],
      "minimum_coordinates_m": [
        0.0,
        0.0
      ],
      "maximum_coordinates_m": [
        1.0,
        0.02
      ],
      "minimum_supported_stress_Pa": -300000000.0,
      "maximum_supported_stress_Pa": 300000000.0,
      "maximum_supported_expanded_uncertainty_Pa": 30000000.0,
      "applicability_basis": "authored provider support",
      "qualification": {
        "qualification_id": "qualification-1",
        "calibration_dataset_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "holdout_dataset_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "calibration_observation_count": 24,
        "holdout_observation_count": 8,
        "holdout_metric_definition": "authored stress difference metric",
        "holdout_metric_value": 12000000.0,
        "holdout_metric_unit": "Pa",
        "maximum_supported_holdout_metric": 20000000.0,
        "maximum_supported_holdout_metric_unit": "Pa",
        "calibration_and_holdout_independent": true,
        "qualification_basis": "authored qualification",
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored residual-stress qualification"
          }
        ]
      },
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored residual-stress support"
        }
      ]
    }
  ],
  "weld_and_material_identity_reviewed": true,
  "coordinate_frames_and_components_reviewed": true,
  "units_and_uncertainty_reviewed": true,
  "provider_identity_and_state_reviewed": true,
  "record_digests_reviewed": true,
  "calibration_and_holdout_reviewed": true,
  "support_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored residual-stress assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding_residual_stress.py#L156)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
