# `integration.crevice_solid_volume_inventory`

**목적:** Each phase inventory is nonnegative amount per caller-reviewed reference area for the same exact snapshot and spatial cell mapping.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_solid_volume_inventory.v1", "default": "matintegrity.crevice_solid_volume_inventory.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `phase_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_solid_inventory_mol_m2_by_phase` | 예 | `{"additionalProperties": {"items": {"type": "number"}, "type": "array"}, "type": "object"}` | 계약·필드 설명 참조 |
| `solid_molar_volume_m3_mol_by_phase` | 예 | `{"additionalProperties": {"type": "number"}, "type": "object"}` | 계약·필드 설명 참조 |
| `inventory_state_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_inventory_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `molar_volume_state_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_area_and_cell_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_morphology_or_aperture_inference_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceSolidVolumeInventoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `cell_solid_inventory_mol_m2_by_phase.*` | `mol/m2` |
| `solid_molar_volume_m3_mol_by_phase.*` | `m3/mol` |
| `cell_solid_volume_per_reference_area_m` | `m3/m2` |
| `phase_solid_volume_per_reference_area_m.*` | `m3/m2` |
| `total_solid_volume_per_reference_area_m` | `m3/m2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each phase inventory is nonnegative amount per caller-reviewed reference area for the same exact snapshot and spatial cell mapping.
- Each supplied molar volume applies to the stated solid phase and snapshot; product inventory times molar volume gives its compact-solid volume equivalent.
- Summation preserves cell identity; the output is volume per reference area and is not assigned to a wall or converted to aperture closure.
- Evidence is caller supplied and is not automatically qualified or independently validated by this adapter.

## 구현 근거·독립 설명

- `caller_crevice_solid_molar_volume_inventory`: Convert each caller-supplied, digest-bound solid-phase inventory per reference area into a volume contribution using its Evidence-backed caller molar volume. Preserve exact chemistry/result identity, cell and phase order, and review gates. This is volume bookkeeping only; it does not determine deposition location, porosity, morphology, aperture closure, transport, kinetics, corrosion or qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_solid_volume_inventory"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_solid_volume_inventory.py#L67)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
