# `welding.peening_treatment_evidence`

**목적:** Component, material, zones, treatment clock, method, media, equipment and direction are caller reviewed.

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
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `treatment_records` | 예 | `{"items": {"$ref": "#/$defs/PeeningTreatmentRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `residual_stress_observations` | 예 | `{"items": {"$ref": "#/$defs/PeeningResidualStressObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredPeeningQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `component_material_and_zone_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `treatment_clock_and_sequence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_media_equipment_and_direction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `intensity_coverage_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_coordinate_method_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_group_and_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PeeningTreatmentAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `component_id` | `1` |
| `selected_envelope_id` | `1` |
| `declared_qualification_outcome` | `1` |
| `treatment_comparisons` | `mixed` |
| `definition_or_unit_mismatch_treatment_ids` | `1` |
| `outside_support_treatment_ids` | `1` |
| `stress_requirement_counts` | `count` |
| `missing_stress_requirement_ids` | `1` |
| `outside_support_stress_observation_ids` | `1` |
| `physical_specimen_count` | `count` |
| `source_group_count` | `count` |
| `evidence_partition_counts_sufficient` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Component, material, zones, treatment clock, method, media, equipment and direction are caller reviewed.
- Intensity, coverage and residual-stress metrics, exact units, uncertainty and support are caller-owned.
- Qualification observations preserve coordinate, depth, specimen, source-group and partition identities.

## 구현 근거·독립 설명

- `reviewed_peening_treatment_qualification_envelope`: Compare time-ordered zone treatment records, method, media, direction, exact intensity and coverage metrics with coordinate-, depth-, specimen- and source-group-identified residual-stress evidence inside caller-owned support. Do not infer stress redistribution, fatigue improvement, crack initiation, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.peening_treatment_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.peening_treatment_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-peening",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "component_id": "component-1",
  "material_condition_id": "condition-1",
  "clock_id": "clock-1",
  "treatment_records": [
    {
      "treatment_record_id": "treatment-1",
      "zone_id": "zone-1",
      "method_id": "method-1",
      "media_condition_id": "media-1",
      "media_lot_id": "lot-1",
      "equipment_id": "equipment-1",
      "direction_descriptor": "direction-a",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "intensity_metric_definition": "caller intensity",
      "intensity_value": 0.4,
      "intensity_unit_token": "custom-intensity",
      "intensity_expanded_uncertainty": 0.02,
      "coverage_metric_definition": "caller coverage",
      "coverage_value": 1.0,
      "coverage_unit_token": "custom-coverage",
      "coverage_expanded_uncertainty": 0.05,
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored peening record"
        }
      ]
    }
  ],
  "residual_stress_observations": [
    {
      "observation_id": "stress-1",
      "zone_id": "zone-1",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "independence_group_id": "independent-1",
      "partition": "qualification",
      "coordinate_frame_id": "surface-frame",
      "stress_component_id": "tangential",
      "depth_m": 0.0001,
      "method_id": "stress-method-1",
      "reported_value": -200.0,
      "unit_token": "custom-stress",
      "expanded_uncertainty": 20.0,
      "provider_id": "laboratory-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored stress observation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "condition-1",
      "supported_method_ids": [
        "method-1"
      ],
      "supported_media_condition_ids": [
        "media-1"
      ],
      "supported_direction_descriptors": [
        "direction-a"
      ],
      "intensity_metric_definition": "caller intensity",
      "intensity_unit_token": "custom-intensity",
      "minimum_intensity_value": 0.2,
      "maximum_intensity_value": 0.6,
      "coverage_metric_definition": "caller coverage",
      "coverage_unit_token": "custom-coverage",
      "minimum_coverage_value": 0.9,
      "maximum_coverage_value": 1.1,
      "stress_requirements": [
        {
          "requirement_id": "stress-requirement-1",
          "stress_component_id": "tangential",
          "method_id": "stress-method-1",
          "unit_token": "custom-stress",
          "minimum_depth_m": 0.0,
          "maximum_depth_m": 0.001,
          "minimum_value": -400.0,
          "maximum_value": -50.0,
          "minimum_record_count": 1,
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
          "citation": "authored peening envelope"
        }
      ]
    }
  ],
  "component_material_and_zone_identity_reviewed": true,
  "treatment_clock_and_sequence_reviewed": true,
  "method_media_equipment_and_direction_reviewed": true,
  "intensity_coverage_units_and_uncertainty_reviewed": true,
  "stress_coordinate_method_units_and_uncertainty_reviewed": true,
  "specimen_source_group_and_partition_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored peening assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/peening_treatment.py#L181)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
