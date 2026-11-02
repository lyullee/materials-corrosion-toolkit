# `materials.phase_microstructure_assessment`

**목적:** Every phase fraction and expanded uncertainty is a reviewed measurement on an explicit sample and region.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `processing_history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/PhaseFractionObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_ranges` | 예 | `{"items": {"$ref": "#/$defs/DeclaredPhaseFractionRange"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `sample_and_region_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_processing_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PhaseMicrostructureAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `comparison_rows` | `mixed` |
| `invalid_observation_ids` | `1` |
| `missing_requirement_observation_ids` | `1` |
| `outside_declared_range_observation_ids` | `1` |
| `missing_reviews` | `1` |
| `all_observations_within_declared_ranges` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Every phase fraction and expanded uncertainty is a reviewed measurement on an explicit sample and region.
- Caller-owned ranges are compared without inferring unmeasured phase balance or material properties.

## 구현 근거·독립 설명

- `declared_phase_fraction_evidence_comparison`: Compare explicit sample- and region-identified phase-fraction measurements and expanded uncertainty intervals with caller-owned ranges. Preserve invalid and missing observations and do not infer unmeasured phase balance, strength, toughness, corrosion resistance, cracking or service life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.phase_microstructure_assessment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.phase_microstructure_assessment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-phase-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "material_condition_id": "condition-1",
  "processing_history_id": "history-1",
  "observations": [
    {
      "observation_id": "o1",
      "sample_id": "s1",
      "region_id": "region-1",
      "phase_id": "phase-a",
      "measured_fraction": 0.55,
      "expanded_uncertainty_fraction": 0.03,
      "method_id": "method-1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase observation"
        }
      ]
    },
    {
      "observation_id": "o2",
      "sample_id": "s1",
      "region_id": "region-1",
      "phase_id": "phase-b",
      "measured_fraction": 0.45,
      "expanded_uncertainty_fraction": 0.03,
      "method_id": "method-1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase observation"
        }
      ]
    }
  ],
  "declared_ranges": [
    {
      "requirement_id": "r1",
      "region_id": "region-1",
      "phase_id": "phase-a",
      "minimum_fraction": 0.5,
      "maximum_fraction": 0.6,
      "requirement_basis": "caller range",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase range"
        }
      ]
    },
    {
      "requirement_id": "r2",
      "region_id": "region-1",
      "phase_id": "phase-b",
      "minimum_fraction": 0.4,
      "maximum_fraction": 0.5,
      "requirement_basis": "caller range",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase range"
        }
      ]
    }
  ],
  "sample_and_region_mapping_reviewed": true,
  "material_and_processing_identity_reviewed": true,
  "method_applicability_reviewed": true,
  "uncertainty_basis_reviewed": true,
  "phase_identity_reviewed": true,
  "requirement_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/phase_microstructure.py#L87)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
