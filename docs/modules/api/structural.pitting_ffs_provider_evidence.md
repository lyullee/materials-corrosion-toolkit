# `structural.pitting_ffs_provider_evidence`

**목적:** Component, material, coordinate frame, pressure and load bases are caller-reviewed exact identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_type_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wall_thickness_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `wall_thickness_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"enum": ["internal_minus_external", "external_minus_internal"], "type": "string"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pit_geometries` | 예 | `{"items": {"$ref": "#/$defs/PitGeometryRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `provider_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_input_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `result_metric_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `result_metric_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `result_value` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `result_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/PittingFFSProviderEnvelope"}` | 계약·필드 설명 참조 |
| `component_material_location_and_frame_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_thickness_pressure_and_load_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pit_geometry_definition_units_and_clusters_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspection_uncertainty_and_pod_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_model_revision_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_metric_definition_and_unit_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_partitions_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PittingFFSProviderEvidence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `component_id` | `1` |
| `selected_envelope_id` | `1` |
| `pit_geometry_comparisons` | `mixed` |
| `outside_support_pit_field_ids` | `1` |
| `load_case_within_support` | `1` |
| `provider_result` | `mixed` |
| `qualification_partition_counts` | `count` |
| `declared_provider_evidence_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Component, material, coordinate frame, pressure and load bases are caller-reviewed exact identities.
- Geometry, inspection and result metrics retain their original definitions, units, uncertainty and content digests.
- The model exchanges a qualified provider result without implementing FFS equations or acceptance limits.

## 구현 근거·독립 설명

- `reviewed_pitting_ffs_provider_qualification_envelope`: Preserve component, material, coordinate frame, measured wall thickness, differential-pressure basis, pit-field or cluster geometry definition, units and digests, supplied inspection uncertainty or POD evidence, load case and external provider result with calibration and holdout partitions. Do not bundle proprietary FFS equations, reconstruct pits, infer interaction, capacity, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.pitting_ffs_provider_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.pitting_ffs_provider_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-pitting-ffs",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "component_id": "component-1",
  "component_type_id": "pipe",
  "material_condition_id": "condition-1",
  "coordinate_frame_id": "frame-1",
  "wall_thickness_value": 0.01,
  "wall_thickness_unit_token": "m",
  "pressure_basis": "internal_minus_external",
  "load_case_id": "case-1",
  "pit_geometries": [
    {
      "pit_field_id": "field-1",
      "cluster_id": "cluster-1",
      "geometry_definition_id": "box-1",
      "coordinate_frame_id": "frame-1",
      "length_value": 0.01,
      "width_value": 0.005,
      "depth_value": 0.002,
      "geometry_unit_token": "m",
      "geometry_content_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "inspection_method_id": "method-1",
      "sizing_uncertainty_value": 0.0002,
      "sizing_uncertainty_unit_token": "m",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored pit geometry"
        }
      ]
    }
  ],
  "provider_model_id": "provider-model",
  "provider_revision": "1",
  "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "provider_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "provider_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "result_metric_id": "provider-output",
  "result_metric_definition": "authored external metric",
  "result_value": 1.2,
  "result_unit_token": "custom",
  "qualification_envelope": {
    "envelope_id": "env-1",
    "component_type_id": "pipe",
    "material_condition_id": "condition-1",
    "coordinate_frame_id": "frame-1",
    "pressure_basis": "internal_minus_external",
    "wall_thickness_unit_token": "m",
    "geometry_unit_token": "m",
    "supported_geometry_definition_ids": [
      "box-1"
    ],
    "supported_inspection_method_ids": [
      "method-1"
    ],
    "supported_load_case_ids": [
      "case-1"
    ],
    "result_metric_id": "provider-output",
    "result_metric_definition": "authored external metric",
    "result_unit_token": "custom",
    "provider_model_id": "provider-model",
    "provider_revision": "1",
    "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "qualification_records": [
      {
        "record_id": "q1",
        "partition": "calibration",
        "physical_specimen_id": "s1",
        "source_group_id": "g1",
        "provider_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored calibration"
          }
        ]
      },
      {
        "record_id": "q2",
        "partition": "holdout",
        "physical_specimen_id": "s2",
        "source_group_id": "g2",
        "provider_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored holdout"
          }
        ]
      }
    ],
    "qualification_basis": "authored",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored pitting envelope"
      }
    ]
  },
  "component_material_location_and_frame_reviewed": true,
  "wall_thickness_pressure_and_load_basis_reviewed": true,
  "pit_geometry_definition_units_and_clusters_reviewed": true,
  "inspection_uncertainty_and_pod_evidence_reviewed": true,
  "provider_model_revision_and_digests_reviewed": true,
  "result_metric_definition_and_unit_reviewed": true,
  "qualification_partitions_and_source_groups_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored pitting assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pitting_ffs_provider.py#L137)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
