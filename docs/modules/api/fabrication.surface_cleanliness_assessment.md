# `fabrication.surface_cleanliness_assessment`

**목적:** Area coverage is summed only after the caller reviews areas as mutually exclusive.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `areas` | 예 | `{"items": {"$ref": "#/$defs/PreparedSurfaceArea"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 아니오 | `{"items": {"$ref": "#/$defs/CleanlinessObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_requirements` | 예 | `{"items": {"$ref": "#/$defs/DeclaredCleanlinessRequirement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `areas_mutually_exclusive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `preparation_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SurfaceCleanlinessAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `procedure_id` | `1` |
| `procedure_revision` | `1` |
| `target_area_m2` | `m^2` |
| `inspected_area_m2` | `m^2` |
| `uninspected_area_m2` | `m^2` |
| `coverage_fraction` | `1` |
| `observation_count` | `1` |
| `observation_counts_by_metric` | `1` |
| `requirement_rows` | `mixed` |
| `missing_requirement_observation_ids` | `1` |
| `missing_reviews` | `1` |
| `all_declared_requirements_satisfied` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Area coverage is summed only after the caller reviews areas as mutually exclusive.
- Observation values and expanded uncertainties share the exact caller-declared unit token.
- Every comparison is against a caller-owned requirement with separately preserved authority evidence.

## 구현 근거·독립 설명

- `declared_surface_cleanliness_comparison`: Compare reviewed surface observations and their caller-supplied expanded uncertainties with caller-owned metric limits. Preserve inspected-area coverage, observation and requirement identities, exact unit tokens and missing evidence; do not supply a coating, fabrication or design-code acceptance rule.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.surface_cleanliness_assessment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.surface_cleanliness_assessment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-cleanliness-example",
  "procedure_id": "authored-preparation-procedure",
  "procedure_revision": "A",
  "areas": [
    {
      "area_id": "area-1",
      "physical_location_id": "synthetic",
      "material_condition_id": "authored-prepared-steel",
      "preparation_process_id": "authored-process",
      "target_area_m2": 10.0,
      "inspected_area_m2": 10.0,
      "uninspected_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored surface area"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-1",
      "area_id": "area-1",
      "metric_id": "authored-residue-metric",
      "method_id": "authored-method",
      "value": 18.0,
      "expanded_uncertainty": 2.0,
      "unit_token": "mg/m^2",
      "sample_location_description": "authored sample point",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored observation"
        }
      ]
    }
  ],
  "declared_requirements": [
    {
      "requirement_id": "requirement-1",
      "area_id": "area-1",
      "metric_id": "authored-residue-metric",
      "comparator": "maximum",
      "limit_value": 20.0,
      "unit_token": "mg/m^2",
      "requirement_basis": "authored caller-owned limit",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored limit"
        }
      ]
    }
  ],
  "areas_mutually_exclusive_reviewed": true,
  "preparation_identity_reviewed": true,
  "method_applicability_reviewed": true,
  "calibration_and_uncertainty_reviewed": true,
  "observation_mapping_reviewed": true,
  "requirement_authority_reviewed": true,
  "negative_result_reviewed": false,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fabrication_surface.py#L520)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
