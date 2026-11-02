# `fabrication.coating_qualification_assessment`

**목적:** Specimens and source groups are assigned once to calibration or holdout and cannot cross partitions.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `qualification_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `protocol_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `protocol_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimens` | 예 | `{"items": {"$ref": "#/$defs/CoatingQualificationSpecimen"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `measurements` | 예 | `{"items": {"$ref": "#/$defs/CoatingQualificationMeasurement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_requirements` | 예 | `{"items": {"$ref": "#/$defs/DeclaredCoatingRequirement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `specimen_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coating_lot_traceability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_methods_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `partition_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CoatingQualificationAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `qualification_id` | `1` |
| `coating_system_id` | `1` |
| `protocol_id` | `1` |
| `protocol_revision` | `1` |
| `specimen_count_by_partition` | `1` |
| `coating_lot_ids` | `1` |
| `exposure_ids` | `1` |
| `partition_metric_summaries` | `mixed` |
| `declared_requirement_rows` | `mixed` |
| `incomplete_requirement_partition_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Specimens and source groups are assigned once to calibration or holdout and cannot cross partitions.
- Comparisons use exact unit-token agreement and the caller-provided expanded uncertainty.
- No transfer from laboratory exposure to field service is inferred.

## 구현 근거·독립 설명

- `partitioned_coating_observation_summary`: Keep coating specimens and source groups in fixed calibration or holdout partitions, summarize exact-unit observations and expanded uncertainties, and compare them only with caller-owned one-sided limits. Do not infer laboratory-to-field transfer, coating service life, corrosion rate or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.coating_qualification_assessment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.coating_qualification_assessment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "qualification_id": "authored-coating-example",
  "coating_system_id": "system-1",
  "protocol_id": "protocol-1",
  "protocol_revision": "A",
  "specimens": [
    {
      "specimen_id": "cal-1",
      "coating_system_id": "system-1",
      "coating_lot_id": "lot-cal",
      "substrate_condition_id": "prepared-steel",
      "exposure_id": "exposure-1",
      "source_group_id": "group-cal",
      "partition": "calibration",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored calibration specimen"
        }
      ]
    },
    {
      "specimen_id": "hold-1",
      "coating_system_id": "system-1",
      "coating_lot_id": "lot-hold",
      "substrate_condition_id": "prepared-steel",
      "exposure_id": "exposure-1",
      "source_group_id": "group-hold",
      "partition": "holdout",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored holdout specimen"
        }
      ]
    }
  ],
  "measurements": [
    {
      "measurement_id": "m-cal",
      "specimen_id": "cal-1",
      "metric_id": "dft",
      "metric_kind": "dry_film_thickness",
      "value": 200.0,
      "expanded_uncertainty": 5.0,
      "unit_token": "um",
      "measurement_valid": true,
      "missing_or_invalid_basis": null,
      "method_id": "authored-dft-method",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored calibration measurement"
        }
      ]
    },
    {
      "measurement_id": "m-hold",
      "specimen_id": "hold-1",
      "metric_id": "dft",
      "metric_kind": "dry_film_thickness",
      "value": 210.0,
      "expanded_uncertainty": 5.0,
      "unit_token": "um",
      "measurement_valid": true,
      "missing_or_invalid_basis": null,
      "method_id": "authored-dft-method",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored holdout measurement"
        }
      ]
    }
  ],
  "declared_requirements": [
    {
      "requirement_id": "dft-min",
      "metric_id": "dft",
      "comparator": "minimum",
      "limit_value": 190.0,
      "unit_token": "um",
      "applicability_description": "authored system",
      "authority_basis": "caller-owned requirement",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored coating requirement"
        }
      ]
    }
  ],
  "specimen_identity_reviewed": true,
  "coating_lot_traceability_reviewed": true,
  "exposure_identity_reviewed": true,
  "measurement_methods_reviewed": true,
  "uncertainty_basis_reviewed": true,
  "partition_independence_reviewed": true,
  "requirement_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored coating qualification"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/coating_qualification.py#L147)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
