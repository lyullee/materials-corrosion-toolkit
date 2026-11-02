# `inspection.replica_metallography_evidence`

**목적:** Replica sites and physical source groups retain caller-reviewed mappings.

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
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `replica_sites` | 예 | `{"items": {"$ref": "#/$defs/ReplicaSiteRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ReplicaMicrostructureObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/CallerReplicaObservationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `component_material_and_locations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_preparation_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_and_microscope_configuration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_identity_and_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `morphology_and_metric_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_digests_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_holdout_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ReplicaMetallographyEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `component_id` | `1` |
| `material_condition_id` | `1` |
| `replica_site_count` | `1` |
| `total_replicated_area_m2` | `m^2` |
| `invalid_preparation_site_ids` | `1` |
| `observation_count` | `1` |
| `partition_counts` | `1` |
| `unavailable_observation_ids` | `1` |
| `unmatched_observation_ids` | `1` |
| `ambiguous_observation_ids` | `1` |
| `invalid_qualification_envelope_ids` | `1` |
| `observation_comparisons` | `mixed` |
| `all_application_observations_within_declared_envelopes` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Replica sites and physical source groups retain caller-reviewed mappings.
- Surface preparation, microscope configuration and provider state are traceable by identifiers and digests.
- Observation envelopes and qualification limits are supplied and reviewed by the caller.

## 구현 근거·독립 설명

- `reviewed_replica_metallography_evidence`: Map replica sites, sampled area, preparation, microscope configuration, morphology descriptors and quantitative observations to caller-owned provider support with partition and uncertainty lineage. Do not fabricate grades or phases or infer aging class, damage rate, creep life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.replica_metallography_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.replica_metallography_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-replica",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "component_id": "component-1",
  "material_condition_id": "condition-1",
  "replica_sites": [
    {
      "replica_site_id": "site-1",
      "physical_source_group_id": "surface-1",
      "location_definition": "authored mapped surface",
      "replicated_area_m2": 0.0001,
      "surface_preparation_id": "prep-1",
      "surface_preparation_description": "authored preparation",
      "surface_preparation_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "preparation_record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored replica site"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-1",
      "replica_site_id": "site-1",
      "partition": "application",
      "physical_source_group_id": "surface-1",
      "method_id": "method-1",
      "microscope_id": "microscope-1",
      "microscope_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "morphology_descriptor": "caller-descriptor-a",
      "metric_definition": "caller feature area fraction",
      "observed_value": 0.12,
      "expanded_uncertainty": 0.02,
      "coverage_factor": 2.0,
      "unit": "1",
      "uncertainty_basis": "authored uncertainty",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_available": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored replica observation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "method_id": "method-1",
      "microscope_id": "microscope-1",
      "microscope_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "supported_morphology_descriptors": [
        "caller-descriptor-a"
      ],
      "metric_definition": "caller feature area fraction",
      "unit": "1",
      "minimum_supported_value": 0.0,
      "maximum_supported_value": 0.5,
      "maximum_supported_expanded_uncertainty": 0.05,
      "minimum_supported_replicated_area_m2": 5e-05,
      "maximum_supported_replicated_area_m2": 0.0002,
      "applicability_basis": "authored caller envelope",
      "provider_qualification": {
        "qualification_id": "qualification-1",
        "calibration_dataset_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "holdout_dataset_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "calibration_physical_source_group_count": 10,
        "holdout_physical_source_group_count": 4,
        "calibration_and_holdout_independent": true,
        "validation_metric_definition": "authored absolute error",
        "validation_metric_value": 0.03,
        "validation_metric_unit": "1",
        "maximum_supported_validation_metric": 0.05,
        "qualification_basis": "authored qualification",
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored replica qualification"
          }
        ]
      },
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored replica envelope"
        }
      ]
    }
  ],
  "component_material_and_locations_reviewed": true,
  "physical_source_groups_reviewed": true,
  "surface_preparation_records_reviewed": true,
  "method_and_microscope_configuration_reviewed": true,
  "provider_identity_and_state_reviewed": true,
  "morphology_and_metric_definitions_reviewed": true,
  "units_and_uncertainty_reviewed": true,
  "result_digests_and_missingness_reviewed": true,
  "calibration_and_holdout_reviewed": true,
  "caller_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored replica assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection_replica_metallography.py#L181)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
