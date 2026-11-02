# `inspection.replica_feature_density_summary`

**목적:** Frame calibration, SI scale and uncertainty are caller-reviewed and traceable.

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
| `replica_campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_location_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_exposure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_clock_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_exposure_duration_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `minimum_service_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `maximum_service_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `fields` | 예 | `{"items": {"$ref": "#/$defs/ReplicaReviewedField"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `replica_location_material_and_service_exposure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `frame_and_calibration_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `si_scale_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `segmentation_provider_revision_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observer_review_and_feature_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `feature_ids_types_coordinates_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `duplicate_overlap_and_edge_censoring_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ReplicaFeatureDensityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `component_id` | `1` |
| `material_id` | `1` |
| `material_condition_id` | `1` |
| `service_exposure_id` | `1` |
| `field_count` | `1` |
| `field_summaries` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Frame calibration, SI scale and uncertainty are caller-reviewed and traceable.
- Feature inventory, identifiers, coordinates, geometry, overlap and edge handling are reviewed.
- Outputs are geometric field summaries and retain source, provider and observer lineage.

## 구현 근거·독립 설명

- `authored_replica_feature_geometry_reduction`: Preserve replica field, frame calibration, segmentation, observer review, caller feature type, centroid, bounding box, area, uncertainty, overlap, edge handling, validity and immutable evidence identities. Compute field area, reviewed feature count and density, segmented area fraction and nearest-neighbor spacing without automatically classifying creep cavities, assigning damage grade, predicting life, deciding acceptance or creating probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.replica_feature_density_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.replica_feature_density_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "replica-density-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "component_id": "component-1",
  "replica_campaign_id": "campaign-1",
  "physical_location_definition": "outer surface at caller datum A",
  "material_id": "material-1",
  "material_condition_id": "condition-1",
  "service_exposure_id": "exposure-1",
  "service_clock_definition": "caller elapsed operating clock",
  "service_exposure_duration_s": 1000.0,
  "minimum_service_temperature_K": 500.0,
  "maximum_service_temperature_K": 600.0,
  "fields": [
    {
      "field_id": "field-1",
      "replica_id": "replica-1",
      "frame_id": "frame-1",
      "physical_source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "calibration": {
        "calibration_id": "scale-1",
        "coordinate_unit": "px",
        "frame_width": 100.0,
        "frame_height": 100.0,
        "pixel_size_x_m_per_px": 1e-06,
        "pixel_size_y_m_per_px": 2e-06,
        "expanded_pixel_size_x_uncertainty_m_per_px": 1e-08,
        "expanded_pixel_size_y_uncertainty_m_per_px": 2e-08,
        "uncertainty_coverage_factor": 2.0,
        "calibration_provider_id": "cal-provider",
        "calibration_provider_revision": "rev-1",
        "calibration_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "invalid_or_missing_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored geometry test",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "segmentation_method_id": "method-1",
      "segmentation_provider_id": "seg-provider",
      "segmentation_provider_revision": "rev-2",
      "segmentation_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "segmentation_input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "segmentation_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observer_review_id": "observer-review-1",
      "observer_review_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "feature_inventory_complete": true,
      "field_record_valid": true,
      "invalid_or_missing_basis": null,
      "features": [
        {
          "feature_id": "f-1",
          "caller_feature_type": "reviewed-dark-feature",
          "centroid_x": 10.0,
          "centroid_y": 10.0,
          "bounding_box_min_x": 9.0,
          "bounding_box_min_y": 9.0,
          "bounding_box_max_x": 11.0,
          "bounding_box_max_y": 11.0,
          "segmented_area": 4.0,
          "expanded_centroid_uncertainty": 0.2,
          "expanded_area_uncertainty": 0.4,
          "uncertainty_coverage_factor": 2.0,
          "segmentation_feature_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "overlaps_feature_ids": [],
          "touches_frame_edge": false,
          "include_in_summary": true,
          "edge_censoring_basis": null,
          "record_available": true,
          "record_valid": true,
          "missing_or_invalid_basis": null,
          "observer_review_id": "observer-review-1",
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored geometry test",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "feature_id": "f-2",
          "caller_feature_type": "reviewed-dark-feature",
          "centroid_x": 13.0,
          "centroid_y": 14.0,
          "bounding_box_min_x": 12.0,
          "bounding_box_min_y": 13.0,
          "bounding_box_max_x": 14.0,
          "bounding_box_max_y": 15.0,
          "segmented_area": 4.0,
          "expanded_centroid_uncertainty": 0.2,
          "expanded_area_uncertainty": 0.4,
          "uncertainty_coverage_factor": 2.0,
          "segmentation_feature_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          "overlaps_feature_ids": [],
          "touches_frame_edge": false,
          "include_in_summary": true,
          "edge_censoring_basis": null,
          "record_available": true,
          "record_valid": true,
          "missing_or_invalid_basis": null,
          "observer_review_id": "observer-review-1",
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored geometry test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored geometry test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "replica_location_material_and_service_exposure_reviewed": true,
  "frame_and_calibration_identity_reviewed": true,
  "si_scale_units_and_uncertainty_reviewed": true,
  "segmentation_provider_revision_and_digests_reviewed": true,
  "observer_review_and_feature_inventory_reviewed": true,
  "feature_ids_types_coordinates_and_geometry_reviewed": true,
  "duplicate_overlap_and_edge_censoring_reviewed": true,
  "physical_source_and_independence_groups_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored geometry test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/replica_feature_density.py#L186)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
