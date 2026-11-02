# `welding.dissimilar_weld_applicability_evidence`

**목적:** Base A/B, deposited layers, fusion-boundary sides, procedures, thermal history and service environment retain exact identities.

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
| `joint_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_environment_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thermal_clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_material_a_subject_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_material_b_subject_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_evidence` | 예 | `{"items": {"$ref": "#/$defs/DissimilarWeldMaterialEvidence"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `layers` | 예 | `{"items": {"$ref": "#/$defs/DissimilarWeldLayer"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `fusion_boundaries` | 예 | `{"items": {"$ref": "#/$defs/FusionBoundaryRegion"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `thermal_history` | 예 | `{"items": {"$ref": "#/$defs/DissimilarWeldThermalInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `transition_measurements` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/DissimilarWeldTransitionMeasurement"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_review_subject_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `compatibility_reviews` | 예 | `{"items": {"$ref": "#/$defs/DissimilarWeldCompatibilityReview"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `unresolved_items` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/DissimilarWeldUnresolvedItem"}, "type": "array"}` | 계약·필드 설명 참조 |
| `joint_material_layer_and_boundary_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `location_coordinate_frame_and_region_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `procedure_pwht_and_thermal_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `service_environment_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `composition_property_provider_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `transition_measurement_definitions_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `compatibility_review_authority_and_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `unresolved_item_completeness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/DissimilarWeldApplicabilityEvidence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `joint_id` | `1` |
| `joint_location_id` | `1` |
| `coordinate_frame_id` | `1` |
| `service_environment_id` | `1` |
| `base_material_subject_ids` | `1` |
| `layer_sequence` | `mixed` |
| `fusion_boundary_ids_by_side` | `1` |
| `thermal_interval_ids` | `1` |
| `transition_measurements` | `mixed` |
| `missing_required_review_subject_ids` | `1` |
| `unresolved_review_subject_ids` | `1` |
| `limited_review_subject_ids` | `1` |
| `out_of_scope_review_subject_ids` | `1` |
| `unresolved_items` | `mixed` |
| `invalid_material_subject_ids` | `1` |
| `invalid_thermal_interval_ids` | `1` |
| `invalid_transition_measurement_ids` | `1` |
| `missing_reviews` | `1` |
| `review_record_reconciliation` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Base A/B, deposited layers, fusion-boundary sides, procedures, thermal history and service environment retain exact identities.
- Compatibility outcomes and unresolved items are caller-reviewed records, not inferred alloy rules.
- A complete evidence reconciliation is not acceptance, life or failure-probability qualification.

## 구현 근거·독립 설명

- `authored_dissimilar_weld_review_reconciliation`: Reconcile caller-owned applicability reviews for two base materials, deposited layers, fusion-boundary regions, ordered thermal history, service environment and optional transition measurements. Preserve material/provider/procedure/frame/digest identities and unresolved evidence without embedding alloy-pair rules, inferring compatibility, predicting life, deciding acceptance or creating probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.dissimilar_weld_applicability_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.dissimilar_weld_applicability_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "weld-location-1",
  "joint_id": "joint-1",
  "joint_location_id": "joint-location-1",
  "coordinate_frame_id": "joint-frame-1",
  "service_environment_id": "environment-1",
  "service_environment_definition": "caller service environment",
  "thermal_clock_id": "thermal-clock-1",
  "base_material_a_subject_id": "base-a",
  "base_material_b_subject_id": "base-b",
  "material_evidence": [
    {
      "material_subject_id": "base-a",
      "material_role": "base_a",
      "material_id": "material-base-a",
      "material_condition_id": "condition-base-a",
      "material_lot_id": "lot-base-a",
      "composition_provider_id": "composition-provider",
      "composition_provider_revision": "1",
      "composition_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "property_provider_id": "property-provider",
      "property_provider_revision": "1",
      "property_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "material_subject_id": "base-b",
      "material_role": "base_b",
      "material_id": "material-base-b",
      "material_condition_id": "condition-base-b",
      "material_lot_id": "lot-base-b",
      "composition_provider_id": "composition-provider",
      "composition_provider_revision": "1",
      "composition_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "property_provider_id": "property-provider",
      "property_provider_revision": "1",
      "property_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "material_subject_id": "deposit-1",
      "material_role": "filler_deposit",
      "material_id": "material-deposit-1",
      "material_condition_id": "condition-deposit-1",
      "material_lot_id": "lot-deposit-1",
      "composition_provider_id": "composition-provider",
      "composition_provider_revision": "1",
      "composition_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "property_provider_id": "property-provider",
      "property_provider_revision": "1",
      "property_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "material_subject_id": "butter-1",
      "material_role": "buttering",
      "material_id": "material-butter-1",
      "material_condition_id": "condition-butter-1",
      "material_lot_id": "lot-butter-1",
      "composition_provider_id": "composition-provider",
      "composition_provider_revision": "1",
      "composition_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "property_provider_id": "property-provider",
      "property_provider_revision": "1",
      "property_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "layers": [
    {
      "layer_id": "layer-butter",
      "sequence_position": 1,
      "layer_role": "buttering",
      "applied_side": "base_a",
      "material_subject_id": "butter-1",
      "welding_procedure_id": "procedure-butter",
      "welding_procedure_revision": "1",
      "physical_region_id": "region-butter",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "layer_id": "layer-deposit",
      "sequence_position": 2,
      "layer_role": "filler_deposit",
      "applied_side": "joint",
      "material_subject_id": "deposit-1",
      "welding_procedure_id": "procedure-deposit",
      "welding_procedure_revision": "1",
      "physical_region_id": "region-deposit",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "fusion_boundaries": [
    {
      "boundary_region_id": "boundary-a",
      "side": "base_a",
      "base_material_subject_id": "base-a",
      "adjacent_layer_id": "layer-butter",
      "joint_location_id": "joint-location-1",
      "coordinate_frame_id": "joint-frame-1",
      "transition_zone_definition": "caller side-A transition zone",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "boundary_region_id": "boundary-b",
      "side": "base_b",
      "base_material_subject_id": "base-b",
      "adjacent_layer_id": "layer-deposit",
      "joint_location_id": "joint-location-1",
      "coordinate_frame_id": "joint-frame-1",
      "transition_zone_definition": "caller side-B transition zone",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "thermal_history": [
    {
      "interval_id": "welding-1",
      "interval_kind": "welding",
      "procedure_id": "procedure-deposit",
      "procedure_revision": "1",
      "start_time_s": 0,
      "end_time_s": 100,
      "minimum_temperature_K": 300,
      "maximum_temperature_K": 1600,
      "provider_id": "thermal-provider",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "interval_id": "pwht-1",
      "interval_kind": "post_weld_heat_treatment",
      "procedure_id": "pwht-procedure",
      "procedure_revision": "1",
      "start_time_s": 200,
      "end_time_s": 500,
      "minimum_temperature_K": 800,
      "maximum_temperature_K": 850,
      "provider_id": "thermal-provider",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "transition_measurements": [
    {
      "measurement_id": "measurement-1",
      "boundary_region_id": "boundary-a",
      "coordinate_frame_id": "joint-frame-1",
      "measurement_kind": "dilution_metric",
      "metric_definition": "caller dilution area fraction",
      "value": 0.2,
      "unit_token": "fraction",
      "expanded_uncertainty": 0.02,
      "uncertainty_coverage_factor": 2,
      "method_id": "method-1",
      "provider_id": "measurement-provider",
      "provider_revision": "1",
      "provider_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "required_review_subject_ids": [
    "material-pair",
    "deposit",
    "buttering",
    "boundary-a-review",
    "boundary-b-review",
    "pwht-review",
    "service-review"
  ],
  "compatibility_reviews": [
    {
      "review_id": "review-material-pair",
      "review_subject_id": "material-pair",
      "review_subject_kind": "base_material_pair",
      "linked_identity_ids": [
        "base-a",
        "base-b"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-deposit",
      "review_subject_id": "deposit",
      "review_subject_kind": "filler_or_deposit",
      "linked_identity_ids": [
        "deposit-1",
        "layer-deposit"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-buttering",
      "review_subject_id": "buttering",
      "review_subject_kind": "buttering_or_overlay",
      "linked_identity_ids": [
        "butter-1",
        "layer-butter"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-boundary-a-review",
      "review_subject_id": "boundary-a-review",
      "review_subject_kind": "fusion_boundary",
      "linked_identity_ids": [
        "boundary-a"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-boundary-b-review",
      "review_subject_id": "boundary-b-review",
      "review_subject_kind": "fusion_boundary",
      "linked_identity_ids": [
        "boundary-b"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-pwht-review",
      "review_subject_id": "pwht-review",
      "review_subject_kind": "heat_treatment",
      "linked_identity_ids": [
        "pwht-1"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "review_id": "review-service-review",
      "review_subject_id": "service-review",
      "review_subject_kind": "service_environment",
      "linked_identity_ids": [
        "environment-1"
      ],
      "review_status": "reviewed_supported",
      "review_basis": "caller engineering review",
      "limitation_or_unresolved_basis": null,
      "reviewer_or_provider_id": "reviewer-1",
      "reviewer_or_provider_revision": "1",
      "review_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "review_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "unresolved_items": [],
  "joint_material_layer_and_boundary_identity_reviewed": true,
  "location_coordinate_frame_and_region_mapping_reviewed": true,
  "procedure_pwht_and_thermal_history_reviewed": true,
  "service_environment_identity_reviewed": true,
  "composition_property_provider_lineage_reviewed": true,
  "transition_measurement_definitions_units_and_uncertainty_reviewed": true,
  "compatibility_review_authority_and_scope_reviewed": true,
  "unresolved_item_completeness_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/dissimilar_weld_evidence.py#L273)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
