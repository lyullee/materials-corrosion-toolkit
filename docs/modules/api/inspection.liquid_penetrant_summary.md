# `inspection.liquid_penetrant_summary`

**목적:** Caller-controlled material, consumables, sequence, temperature, time, lighting, coverage and indication records; no embedded acceptance rule.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `examination_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `penetrant_type` | 예 | `{"enum": ["visible", "fluorescent"], "type": "string"}` | 계약·필드 설명 참조 |
| `removal_method` | 예 | `{"enum": ["water_washable", "post_emulsifiable_lipophilic", "solvent_removable", "post_emulsifiable_hydrophilic"], "type": "string"}` | 계약·필드 설명 참조 |
| `cleaner_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `penetrant_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `remover_or_emulsifier_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `developer_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `precleaning_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `drying_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `examination_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `penetrant_dwell_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `excess_removal_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `developer_application_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `development_time_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `observation_lighting_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `final_cleaning_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `areas` | 예 | `{"items": {"$ref": "#/$defs/SurfaceExaminationArea"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/SurfaceIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `areas_mutually_exclusive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_consumables_compatibility_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `process_sequence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_times_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LiquidPenetrantExamination.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `target_area_m2` | `m^2` |
| `examined_area_m2` | `m^2` |
| `unexamined_area_m2` | `m^2` |
| `coverage_fraction` | `1` |
| `maximum_reported_indication_length_m` | `m` |
| `maximum_reported_indication_width_m` | `m` |
| `examination_temperature_K` | `K` |
| `penetrant_dwell_s` | `s` |
| `development_time_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-controlled material, consumables, sequence, temperature, time, lighting, coverage and indication records; no embedded acceptance rule.

## 구현 근거·독립 설명

- `liquid_penetrant_examination_definition`: Preserve one caller-controlled penetrant procedure and revision, visible or fluorescent system, removal method, consumable batch identities, material and surface condition, precleaning and drying bases, absolute examination temperature, penetrant dwell, excess-removal basis, developer application and development time, observation lighting, final cleaning, mutually exclusive coverage areas and evidence-bound reported indications. Missing review gates or an unreviewed empty indication list remain needs-data. Process records do not establish procedure compliance, indication relevance, flaw dimensions, acceptance, probability of detection, remaining life or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.liquid_penetrant_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.liquid_penetrant_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "example-pt-001",
  "procedure_id": "user-pt-procedure",
  "procedure_revision": "1",
  "penetrant_type": "visible",
  "removal_method": "solvent_removable",
  "cleaner_batch_id": "cleaner-1",
  "penetrant_batch_id": "penetrant-1",
  "remover_or_emulsifier_batch_id": "remover-1",
  "developer_batch_id": "developer-1",
  "surface_material_id": "material-1",
  "surface_condition": "clean dry surface",
  "precleaning_basis": "user-controlled preclean record",
  "drying_basis": "user-controlled drying record",
  "examination_temperature_K": 295.15,
  "penetrant_dwell_s": 600.0,
  "excess_removal_basis": "user-controlled removal record",
  "developer_application_basis": "user-controlled developer record",
  "development_time_s": 600.0,
  "observation_lighting_basis": "user-controlled lighting record",
  "final_cleaning_basis": "user-controlled final cleaning record",
  "areas": [
    {
      "area_id": "area-a",
      "physical_location_id": "weld-a",
      "target_area_m2": 1.0,
      "examined_area_m2": 0.8,
      "unexamined_basis": "support footprint"
    }
  ],
  "indications": [
    {
      "indication_id": "pt-feature-1",
      "area_id": "area-a",
      "physical_location_id": "weld-a-clock-3",
      "reported_indication_type": "linear indication",
      "location_description": "user datum plus 0.2 m",
      "measured_length_m": 0.008,
      "measured_width_m": null,
      "evidence": [
        {
          "source_id": "example-pt-record",
          "origin": "synthetic",
          "citation": "authored API demonstration",
          "license_id": "MIT"
        }
      ]
    }
  ],
  "areas_mutually_exclusive_reviewed": true,
  "material_and_consumables_compatibility_reviewed": true,
  "process_sequence_reviewed": true,
  "temperature_and_times_reviewed": true,
  "surface_condition_reviewed": true,
  "indication_mapping_reviewed": true,
  "negative_result_reviewed": false,
  "evidence": [
    {
      "source_id": "example-pt-record",
      "origin": "synthetic",
      "citation": "authored API demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/surface_examination.py#L119)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
