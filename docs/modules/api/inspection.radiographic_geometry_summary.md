# `inspection.radiographic_geometry_summary`

**목적:** Caller-controlled radiographic source, exposure, detector, image, IQI, projection geometry and indication record; no embedded acceptance rule.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `examination_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_kind` | 예 | `{"enum": ["x_ray", "gamma"], "type": "string"}` | 계약·필드 설명 참조 |
| `source_equipment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_voltage_V` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | V |
| `isotope_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_activity_Bq` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_activity_reference` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `focal_spot_size_m` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `exposure_time_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `source_object_distance_m` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `object_detector_distance_m` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `nominal_object_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `detector_kind` | 예 | `{"enum": ["film", "computed_radiography", "digital_detector_array", "other"], "type": "string"}` | 계약·필드 설명 참조 |
| `detector_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `detector_calibration_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `image_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `image_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `image_width_px` | 예 | `{"exclusiveMinimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `image_height_px` | 예 | `{"exclusiveMinimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `detector_pixel_pitch_m` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `image_quality_records` | 예 | `{"items": {"$ref": "#/$defs/RadiographicImageQualityRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/RadiographicImageIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `source_configuration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `projection_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `detector_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `image_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `image_quality_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/RadiographicExamination.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `exposure_time_s` | `s` |
| `nominal_object_thickness_m` | `m` |
| `source_detector_distance_m` | `m` |
| `magnification` | `1` |
| `geometric_unsharpness_m` | `m` |
| `object_plane_pixel_pitch_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-controlled radiographic source, exposure, detector, image, IQI, projection geometry and indication record; no embedded acceptance rule.

## 구현 근거·독립 설명

- `radiographic_examination_geometry_definition`: Preserve one caller-controlled radiographic procedure and revision, physical scope, material condition, mutually exclusive X-ray or gamma source identity, exposure, detector, immutable image identity, image dimensions, image-quality indicator records and evidence-bound image-space indications. Require object mapping to carry a physical location and mapping basis together. Compute pinhole magnification, focal-spot geometric unsharpness and object-plane pixel pitch only from explicitly supplied geometry. Missing geometry, review gates, unreviewed image-quality records, unmapped indications or an unreviewed empty indication list remain needs-data. Projection descriptors do not establish total resolution, procedure compliance, flaw identity or size, acceptance, probability of detection, remaining life or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.radiographic_geometry_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.radiographic_geometry_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "example-rt-001",
  "procedure_id": "user-rt-procedure",
  "procedure_revision": "1",
  "physical_scope_id": "weld-17",
  "material_condition_id": "steel-weld-condition-a",
  "source_kind": "x_ray",
  "source_equipment_id": "xray-set-2",
  "tube_voltage_V": 200000.0,
  "isotope_id": null,
  "source_activity_Bq": null,
  "source_activity_reference": null,
  "focal_spot_size_m": 0.001,
  "exposure_time_s": 20.0,
  "source_object_distance_m": 1.0,
  "object_detector_distance_m": 0.2,
  "nominal_object_thickness_m": 0.02,
  "detector_kind": "digital_detector_array",
  "detector_id": "dda-4",
  "detector_calibration_basis": "user-controlled calibration record",
  "image_id": "image-0001",
  "image_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "image_width_px": 2000,
  "image_height_px": 1000,
  "detector_pixel_pitch_m": 0.0002,
  "image_quality_records": [
    {
      "iqi_id": "iqi-1",
      "iqi_type": "caller-selected wire indicator",
      "placement": "source_side",
      "placement_basis": "user-controlled placement record",
      "reported_image_quality_result": "caller-reported visible element",
      "result_basis": "user-controlled image review",
      "reviewed": true,
      "evidence": [
        {
          "source_id": "example-rt-record",
          "origin": "synthetic",
          "citation": "authored API demonstration",
          "license_id": "MIT"
        }
      ]
    }
  ],
  "indications": [],
  "source_configuration_reviewed": true,
  "projection_geometry_reviewed": true,
  "exposure_reviewed": true,
  "detector_calibration_reviewed": true,
  "image_identity_reviewed": true,
  "image_quality_reviewed": true,
  "indication_mapping_reviewed": true,
  "negative_result_reviewed": true,
  "evidence": [
    {
      "source_id": "example-rt-record",
      "origin": "synthetic",
      "citation": "authored API demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/radiography.py#L112)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
