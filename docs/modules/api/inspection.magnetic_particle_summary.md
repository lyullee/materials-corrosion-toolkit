# `inspection.magnetic_particle_summary`

**목적:** Caller-reviewed ferromagnetic applicability, media, equipment, field adequacy, directional requirement, coverage and indication records; no embedded acceptance rule.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `examination_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `particle_medium` | 예 | `{"enum": ["dry", "wet_visible", "wet_fluorescent"], "type": "string"}` | 계약·필드 설명 참조 |
| `particle_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `carrier_batch_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `observation_lighting_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_direction_separation_rad` | 예 | `{"exclusiveMinimum": 0, "maximum": 1.5707963267948966, "type": "number"}` | 계약·필드 설명 참조 |
| `directional_coverage_requirement_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `areas` | 예 | `{"items": {"$ref": "#/$defs/SurfaceExaminationArea"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `magnetization_passes` | 예 | `{"items": {"$ref": "#/$defs/MagnetizationPass"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/SurfaceIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `areas_mutually_exclusive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ferromagnetic_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equipment_and_media_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `field_adequacy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `directional_requirement_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MagneticParticleExamination.json)

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
| `maximum_unoriented_direction_separation_rad_by_area` | `rad` |
| `minimum_direction_separation_rad` | `rad` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed ferromagnetic applicability, media, equipment, field adequacy, directional requirement, coverage and indication records; no embedded acceptance rule.

## 구현 근거·독립 설명

- `magnetic_particle_examination_definition`: Preserve one caller-controlled magnetic-particle procedure and revision, material and surface condition, particle/carrier batch, observation lighting, physical coverage areas, evidence-bound reported indications and uniquely identified magnetization passes. Each pass retains technique, current mode, unoriented field direction on a half-circle, field-adequacy basis, equipment and optional current magnitude. Compare each area's maximum acute separation only with a caller-declared reviewed minimum; zero or one direction remains insufficient. Ferromagnetic applicability, field adequacy and directional records do not establish procedure compliance, subsurface sensitivity, indication relevance, acceptance, probability of detection, remaining life or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.magnetic_particle_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.magnetic_particle_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "example-mt-001",
  "procedure_id": "user-mt-procedure",
  "procedure_revision": "1",
  "surface_material_id": "ferromagnetic-material-1",
  "surface_condition": "clean dry surface",
  "particle_medium": "wet_fluorescent",
  "particle_batch_id": "particles-1",
  "carrier_batch_id": "carrier-1",
  "observation_lighting_basis": "user-controlled lighting record",
  "minimum_direction_separation_rad": 1.0471975511965976,
  "directional_coverage_requirement_basis": "user-approved directional requirement",
  "areas": [
    {
      "area_id": "area-a",
      "physical_location_id": "weld-a",
      "target_area_m2": 1.0,
      "examined_area_m2": 1.0,
      "unexamined_basis": null
    }
  ],
  "magnetization_passes": [
    {
      "pass_id": "pass-0",
      "area_id": "area-a",
      "technique": "yoke",
      "current_mode": "ac",
      "field_direction_rad": 0.0,
      "field_adequacy_basis": "user-controlled field indicator record",
      "equipment_id": "yoke-1",
      "magnetizing_current_A": null
    },
    {
      "pass_id": "pass-90",
      "area_id": "area-a",
      "technique": "yoke",
      "current_mode": "ac",
      "field_direction_rad": 1.5707963267948966,
      "field_adequacy_basis": "user-controlled field indicator record",
      "equipment_id": "yoke-1",
      "magnetizing_current_A": null
    }
  ],
  "indications": [],
  "areas_mutually_exclusive_reviewed": true,
  "ferromagnetic_applicability_reviewed": true,
  "equipment_and_media_reviewed": true,
  "field_adequacy_reviewed": true,
  "directional_requirement_reviewed": true,
  "surface_condition_reviewed": true,
  "indication_mapping_reviewed": true,
  "negative_result_reviewed": true,
  "evidence": [
    {
      "source_id": "example-mt-record",
      "origin": "synthetic",
      "citation": "authored API demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/surface_examination.py#L214)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
