# `inspection.tensile_offset_yield_curve`

**목적:** The supplied curve is a reviewed monotonic engineering-strain loading branch inside a pre-necking analysis window.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensile_test_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `independence_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `extensometer_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `gauge_length_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `instrument_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `extensometer_calibration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `curve_data_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `result_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `result_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `result_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `engineering_strain_unit_token` | 아니오 | `{"const": "1", "default": "1", "type": "string"}` | 계약·필드 설명 참조 |
| `engineering_stress_unit_token` | 아니오 | `{"const": "Pa", "default": "Pa", "type": "string"}` | 계약·필드 설명 참조 |
| `curve_points` | 예 | `{"items": {"$ref": "#/$defs/EngineeringStressStrainPoint"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `elastic_fit_start_point_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elastic_fit_end_point_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `analysis_start_point_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `analysis_end_point_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `offset_strain` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `crossing_zero_tolerance_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `reference_comparison` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/OffsetYieldReferenceComparison"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `specimen_gauge_and_extensometer_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `instrument_calibration_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `engineering_units_and_raw_curve_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `monotonic_loading_branch_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `elastic_fit_window_and_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `offset_and_linear_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pre_necking_analysis_window_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `crossing_uniqueness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `optional_reference_comparison_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TensileOffsetYieldCurveAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `tensile_test_id` | `1` |
| `physical_specimen_id` | `1` |
| `elastic_fit_point_ids` | `1` |
| `analysis_point_ids` | `1` |
| `fitted_elastic_modulus_Pa` | `Pa` |
| `fitted_elastic_intercept_Pa` | `Pa` |
| `elastic_fit_weighted_sse_Pa2` | `Pa^2*weight` |
| `elastic_fit_weighted_r_squared` | `1` |
| `offset_strain` | `1` |
| `crossing_candidates` | `mixed` |
| `offset_yield_stress_Pa` | `Pa` |
| `intersection_engineering_strain` | `1` |
| `intersection_kind` | `1` |
| `intersection_point_ids` | `1` |
| `reference_comparison` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The supplied curve is a reviewed monotonic engineering-strain loading branch inside a pre-necking analysis window.
- Elastic fit weights, offset and crossing tolerance are caller-reviewed inputs.
- A unique adjacent-point crossing is descriptive test reduction, not specification acceptance.

## 구현 근거·독립 설명

- `authored_weighted_elastic_offset_line_intersection`: Fit a weighted elastic line on a caller-reviewed window of a strictly ordered engineering stress-strain branch and locate the unique linearly interpolated crossing with a declared parallel offset line inside a reviewed pre-necking window. Preserve specimen, extensometer, instrument and source digests; optionally compare an independent reference result without true-stress conversion, acceptance or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.tensile_offset_yield_curve"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.tensile_offset_yield_curve"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "specimen-location-1",
  "tensile_test_id": "test-1",
  "physical_specimen_id": "specimen-1",
  "source_group_id": "source-1",
  "independence_group_id": "independence-1",
  "material_condition_id": "condition-1",
  "specimen_geometry_id": "geometry-1",
  "extensometer_id": "extensometer-1",
  "gauge_length_m": 0.05,
  "instrument_provider_id": "instrument-provider",
  "instrument_provider_revision": "1",
  "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "extensometer_calibration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "curve_data_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "result_provider_id": "result-provider",
  "result_provider_revision": "1",
  "result_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "engineering_strain_unit_token": "1",
  "engineering_stress_unit_token": "Pa",
  "curve_points": [
    {
      "point_id": "p0",
      "engineering_strain": 0,
      "engineering_stress_Pa": 0,
      "elastic_fit_weight": 1,
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
      "point_id": "p1",
      "engineering_strain": 0.001,
      "engineering_stress_Pa": 200000000,
      "elastic_fit_weight": 1,
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
      "point_id": "p2",
      "engineering_strain": 0.002,
      "engineering_stress_Pa": 400000000,
      "elastic_fit_weight": 1,
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
      "point_id": "p3",
      "engineering_strain": 0.004,
      "engineering_stress_Pa": 500000000,
      "elastic_fit_weight": 1,
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
      "point_id": "p4",
      "engineering_strain": 0.006,
      "engineering_stress_Pa": 550000000,
      "elastic_fit_weight": 1,
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
      "point_id": "p5",
      "engineering_strain": 0.008,
      "engineering_stress_Pa": 600000000,
      "elastic_fit_weight": 1,
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
  "elastic_fit_start_point_id": "p0",
  "elastic_fit_end_point_id": "p2",
  "analysis_start_point_id": "p0",
  "analysis_end_point_id": "p5",
  "offset_strain": 0.002,
  "crossing_zero_tolerance_Pa": 1e-06,
  "reference_comparison": null,
  "specimen_gauge_and_extensometer_identity_reviewed": true,
  "instrument_calibration_configuration_and_digests_reviewed": true,
  "engineering_units_and_raw_curve_reviewed": true,
  "monotonic_loading_branch_reviewed": true,
  "elastic_fit_window_and_weights_reviewed": true,
  "offset_and_linear_interpolation_reviewed": true,
  "pre_necking_analysis_window_reviewed": true,
  "crossing_uniqueness_reviewed": true,
  "optional_reference_comparison_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/tensile_offset_yield_curve.py#L132)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
