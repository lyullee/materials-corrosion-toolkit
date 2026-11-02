# `materials.bonded_layer_integrity_assessment`

**목적:** Substrate, layer, interface, lot and process identities are caller-reviewed and preserved.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bonded_layer_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bonded_layer_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `interface_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bonding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bonding_process_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `regions` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerRegion"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_requirements` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerRequirement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_dispositions` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerDisposition"}, "type": "array"}` | 계약·필드 설명 참조 |
| `material_lot_and_process_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `regions_mutually_exclusive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `examination_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_and_disposition_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BondedLayerIntegrityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `substrate_material_id` | `1` |
| `bonded_layer_material_id` | `1` |
| `interface_system_id` | `1` |
| `target_area_m2` | `m^2` |
| `examined_area_m2` | `m^2` |
| `coverage_fraction` | `1` |
| `requirement_rows` | `mixed` |
| `unmapped_observation_ids` | `1` |
| `invalid_or_missing_observation_ids` | `1` |
| `incomplete_requirement_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Substrate, layer, interface, lot and process identities are caller-reviewed and preserved.
- Numerical comparisons require exact observation and requirement unit tokens.
- Unmapped, invalid and missing observations are retained and prevent a complete assessment.

## 구현 근거·독립 설명

- `declared_bonded_layer_observation_disposition`: Account for substrate, layer, interface, process and lot identities, region coverage, bond-strength or interface observations, expanded uncertainty, exact units and caller-owned requirements or dispositions. Preserve invalid, missing and unmapped evidence without inferring delamination growth, residual stress, fracture, lifetime or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.bonded_layer_integrity_assessment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.bonded_layer_integrity_assessment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-bonded-layer",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "substrate_material_id": "substrate-a",
  "substrate_lot_id": "substrate-lot-1",
  "bonded_layer_material_id": "layer-a",
  "bonded_layer_lot_id": "layer-lot-1",
  "interface_system_id": "interface-a",
  "bonding_process_id": "process-1",
  "bonding_process_revision": "A",
  "regions": [
    {
      "region_id": "region-1",
      "physical_location_id": "zone-1",
      "target_area_m2": 5.0,
      "examined_area_m2": 5.0,
      "unexamined_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored bonded region"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "obs-1",
      "region_id": "region-1",
      "observation_kind": "bond_strength",
      "metric_id": "bond-strength",
      "method_id": "method-1",
      "value": 12.0,
      "expanded_uncertainty": 1.0,
      "unit_token": "MPa",
      "measurement_valid": true,
      "missing_invalid_or_unmapped_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored bonded observation"
        }
      ]
    }
  ],
  "declared_requirements": [
    {
      "requirement_id": "strength-min",
      "region_id": "region-1",
      "metric_id": "bond-strength",
      "comparator": "minimum",
      "limit_value": 10.0,
      "unit_token": "MPa",
      "requirement_basis": "caller requirement",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored bonded requirement"
        }
      ]
    }
  ],
  "declared_dispositions": [
    {
      "requirement_id": "strength-min",
      "satisfied_disposition": "caller-retain",
      "not_satisfied_disposition": "caller-review",
      "indeterminate_disposition": "caller-obtain-data",
      "disposition_authority_basis": "caller workflow",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored disposition"
        }
      ]
    }
  ],
  "material_lot_and_process_identity_reviewed": true,
  "regions_mutually_exclusive_reviewed": true,
  "examination_coverage_reviewed": true,
  "method_and_calibration_reviewed": true,
  "uncertainty_basis_reviewed": true,
  "observation_mapping_reviewed": true,
  "requirement_and_disposition_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored bonded assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/bonded_layer_integrity.py#L136)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
