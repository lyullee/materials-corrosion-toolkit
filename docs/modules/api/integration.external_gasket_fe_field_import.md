# `integration.external_gasket_fe_field_import`

**목적:** The adapter validates caller-supplied field metadata, array digests, direct location mapping, support data and exact solver-step time bindings against a structural provider receipt.

**모델 버전:** `1.0.0` · **구현 분류:** `data_import` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.external_gasket_fe_field_import.v1", "default": "matintegrity.external_gasket_fe_field_import.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `run_context` | 예 | `{"$ref": "#/$defs/RunContext"}` | 계약·필드 설명 참조 |
| `node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_contact_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_locations` | 예 | `{"items": {"$ref": "#/$defs/GasketFEContactLocation"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `field_selections` | 예 | `{"items": {"$ref": "#/$defs/GasketFEFieldSelection"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `snapshots` | 예 | `{"items": {"$ref": "#/$defs/GasketFEContactSnapshot"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `coordinate_and_contact_area_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exact_solver_step_to_time_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `field_quantity_frame_and_unit_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_field_array_normalization_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_area_to_nodal_force_projection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `contact_field_semantics_and_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_condition_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalGasketFEFieldImportRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history[].time_s` | `s` |
| `history[].response_field[].contact_force_N` | `N` |
| `history[].response_field[].mean_contact_pressure_Pa` | `Pa` |
| `history[].response_field[].contact_area_m2` | `m^2` |
| `history[].response_field[].contact_gap_m` | `m` |
| `history[].response_field[].gasket_compression_m` | `m` |
| `history[].response_field[].gasket_stress_components_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The adapter validates caller-supplied field metadata, array digests, direct location mapping, support data and exact solver-step time bindings against a structural provider receipt.
- It preserves only selected pressure, force, gap, compression and stress-tensor fields; it does not solve FE equations, interpolate fields or infer acceptance criteria.
- Pressure-to-force multiplication is used only when the caller supplies tributary area and reviews that lumped projection basis.

## 구현 근거·독립 설명

- `caller_finite_element_gasket_field_receipt_and_normalized_arrays`: Caller-authorized provider receipt, selected normalized FE arrays and exact provider digests.
- `caller_mesh_contact_location_area_and_coordinate_mapping`: Caller-mapped mesh nodes, contact areas, frames and direct one-to-one result locations.
- `caller_solver_step_time_and_support_boundary_records`: Caller-bound FE solver-step time and optional explicit support observations; no hidden interpolation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.external_gasket_fe_field_import"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/external_gasket_fe_field_import.py#L292)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
