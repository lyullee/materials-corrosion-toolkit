# `fabrication.thermal_spray_condition`

**목적:** System, process, feedstock lot, substrate condition and procedure identities are caller-reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spray_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `feedstock_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `regions` | 예 | `{"items": {"$ref": "#/$defs/ThermalSprayRegion"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ThermalSprayObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `declared_requirements` | 예 | `{"items": {"$ref": "#/$defs/DeclaredThermalSprayRequirement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `system_and_lot_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_preparation_and_pass_traceability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `region_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_methods_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_and_provider_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalSprayConditionAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `coating_system_id` | `1` |
| `spray_process_id` | `1` |
| `feedstock_lot_id` | `1` |
| `nominal_area_m2` | `m^2` |
| `examined_area_m2` | `m^2` |
| `examined_area_fraction` | `1` |
| `comparison_rows` | `mixed` |
| `invalid_observation_ids` | `1` |
| `incomplete_requirement_scope_ids` | `1` |
| `physical_specimen_ids` | `1` |
| `source_group_ids_by_partition` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- System, process, feedstock lot, substrate condition and procedure identities are caller-reviewed.
- Metric definitions, units, uncertainty and one-sided requirements are caller-owned.
- Qualification and production observations are evidence partitions, not assumed independent populations.

## 구현 근거·독립 설명

- `partitioned_thermal_spray_condition_accounting`: Keep thermal-spray qualification and production observations in separate source groups, preserve coating-system, process, feedstock, substrate, region and provider lineage, and compare exact metric definitions, units and expanded uncertainty with caller-owned requirements. Do not infer coating life, corrosion rate, structural capacity or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.thermal_spray_condition"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.thermal_spray_condition"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-thermal-spray",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "coating_system_id": "system-1",
  "spray_process_id": "process-1",
  "feedstock_lot_id": "lot-1",
  "substrate_material_condition_id": "substrate-1",
  "procedure_id": "procedure-1",
  "procedure_revision": "1",
  "procedure_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "regions": [
    {
      "region_id": "region-1",
      "physical_scope_id": "scope-1",
      "nominal_area_m2": 2.0,
      "examined_area_m2": 1.0,
      "surface_preparation_id": "prep-1",
      "deposition_pass_group_id": "passes-1",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored spray region"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "q-1",
      "region_id": "region-1",
      "physical_specimen_id": "q-specimen",
      "source_group_id": "q-group",
      "partition": "qualification",
      "metric_id": "porosity",
      "metric_kind": "porosity_fraction",
      "metric_definition": "reviewed area fraction",
      "value": 0.04,
      "expanded_uncertainty": 0.01,
      "unit_token": "1",
      "method_id": "method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored spray observation"
        }
      ]
    },
    {
      "observation_id": "p-1",
      "region_id": "region-1",
      "physical_specimen_id": "p-specimen",
      "source_group_id": "p-group",
      "partition": "production",
      "metric_id": "porosity",
      "metric_kind": "porosity_fraction",
      "metric_definition": "reviewed area fraction",
      "value": 0.05,
      "expanded_uncertainty": 0.01,
      "unit_token": "1",
      "method_id": "method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored spray observation"
        }
      ]
    }
  ],
  "declared_requirements": [
    {
      "requirement_id": "porosity-limit",
      "metric_id": "porosity",
      "metric_kind": "porosity_fraction",
      "metric_definition": "reviewed area fraction",
      "applicable_region_ids": [
        "region-1"
      ],
      "required_partitions": [
        "qualification",
        "production"
      ],
      "comparator": "maximum",
      "limit_value": 0.08,
      "unit_token": "1",
      "authority_basis": "authored caller requirement",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored spray requirement"
        }
      ]
    }
  ],
  "system_and_lot_identity_reviewed": true,
  "surface_preparation_and_pass_traceability_reviewed": true,
  "region_coverage_reviewed": true,
  "measurement_methods_reviewed": true,
  "uncertainty_and_provider_lineage_reviewed": true,
  "requirement_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored thermal-spray assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_spray.py#L149)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
