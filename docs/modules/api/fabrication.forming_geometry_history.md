# `fabrication.forming_geometry_history`

**목적:** Caller-reviewed circular-arc bend geometry with a mid-thickness neutral axis.

**모델 버전:** `1.0.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `strain_convention` | 예 | `{"enum": ["engineering", "true"], "type": "string"}` | 계약·필드 설명 참조 |
| `records` | 예 | `{"items": {"$ref": "#/$defs/FormingGeometryRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_supported_radius_to_original_thickness` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_supported_radius_to_original_thickness` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_supported_bend_angle_rad` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `caller_maximum_tensile_surface_strain` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `caller_maximum_thinning_measure` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `material_condition_mode_and_direction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `original_final_thickness_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_and_strain_conventions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_uncertainty_and_record_status_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_identity_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_and_caller_threshold_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FormingGeometryHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `component_id` | `1` |
| `strain_convention` | `1` |
| `record_summaries` | `mixed` |
| `outside_support_record_ids` | `1` |
| `excluded_missing_or_invalid_record_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed circular-arc bend geometry with a mid-thickness neutral axis.
- Original/final thickness, inside radius, angle and uncertainties retain specimen and source identity.
- Thresholds are optional caller values used only for signed arithmetic margins.

## 구현 근거·독립 설명

- `reviewed_forming_geometry_strain_summary`: Preserve caller-reviewed original and final thickness, inside bend radius, angle, forming mode, direction, material condition, specimen/source identity, uncertainty and digests. Under one explicit circular-arc neutral-axis convention, summarize surface strain and thinning in one declared engineering or true convention, with caller threshold margins only and no embedded limits, heat-treatment requirement, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.forming_geometry_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.forming_geometry_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "forming-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "component_id": "component-1",
  "material_condition_id": "condition-1",
  "strain_convention": "engineering",
  "records": [
    {
      "record_id": "record-1",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "material_condition_id": "condition-1",
      "forming_mode": "cold",
      "forming_direction_id": "transverse",
      "geometry_convention": "mid_thickness_neutral_axis_circular_arc",
      "strain_convention": "engineering",
      "original_thickness_m": 0.01,
      "final_thickness_m": 0.009,
      "inside_radius_m": 0.02,
      "bend_angle_rad": 1.0,
      "thickness_standard_uncertainty_m": 0.0001,
      "radius_standard_uncertainty_m": 0.0002,
      "angle_standard_uncertainty_rad": 0.01,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "minimum_supported_radius_to_original_thickness": 1.0,
  "maximum_supported_radius_to_original_thickness": 5.0,
  "maximum_supported_bend_angle_rad": 2.0,
  "caller_maximum_tensile_surface_strain": 0.25,
  "caller_maximum_thinning_measure": 0.2,
  "material_condition_mode_and_direction_reviewed": true,
  "original_final_thickness_and_geometry_reviewed": true,
  "geometry_and_strain_conventions_reviewed": true,
  "measurement_uncertainty_and_record_status_reviewed": true,
  "specimen_source_identity_and_digests_reviewed": true,
  "support_and_caller_threshold_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/forming_geometry_history.py#L95)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
