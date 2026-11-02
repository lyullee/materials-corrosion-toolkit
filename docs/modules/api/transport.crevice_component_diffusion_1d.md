# `transport.crevice_component_diffusion_1d`

**목적:** A caller-defined scalar component diffuses along a constant-cross-section one-dimensional crevice with fixed mouth concentration and a closed tip.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bulk_solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `crevice_length_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `constant_cross_section_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `cell_count` | 예 | `{"maximum": 500, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `initial_component_concentration_mol_m3` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | mol/m³ |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/CreviceComponentDiffusionInterval"}, "maxItems": 4999, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `supports` | 예 | `{"items": {"$ref": "#/$defs/CreviceComponentDiffusionSupport"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_internal_step_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_relative_mass_balance_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_and_constant_cross_section_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `component_definition_and_initial_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mouth_boundary_and_closed_tip_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `independent_fickian_component_transport_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `diffusivity_and_source_provider_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_interval_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `numerical_step_and_balance_tolerance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceComponentDiffusionHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cell_center_position_m` | `m` |
| `concentration_history[].time_s` | `s` |
| `concentration_history[].component_concentration_mol_m3` | `mol/m^3` |
| `concentration_history[].total_component_amount_mol` | `mol` |
| `interval_mass_balance[].mouth_boundary_transfer_mol` | `mol` |
| `interval_mass_balance[].volumetric_source_transfer_mol` | `mol` |
| `interval_mass_balance[].inventory_change_mol` | `mol` |
| `interval_mass_balance[].mass_balance_residual_mol` | `mol` |
| `interval_mass_balance[].relative_mass_balance_error` | `1` |
| `maximum_relative_mass_balance_error` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A caller-defined scalar component diffuses along a constant-cross-section one-dimensional crevice with fixed mouth concentration and a closed tip.
- Diffusivity, mouth concentration and cellwise volumetric source are piecewise constant over each caller clock interval.
- Backward-Euler cell-centered finite volumes preserve an explicit component balance; provider support prevents hidden property or concentration extrapolation.

## 구현 근거·독립 설명

- `finite_volume_fick_component_diffusion`: Solve caller-defined one-dimensional constant-area component diffusion with a cell-centered finite-volume spatial balance and backward-Euler time steps, fixed mouth concentration, no-flux blind tip and explicit cellwise source. Subdivide each interval within declared provider support and report discrete inventory/boundary/source closure; do not infer electromigration, species speciation, chemistry, electrochemistry or moving geometry.
- `declared_crevice_transport_provider`: Require digest-pinned caller transport geometry, diffusivity, source, mouth concentration and declared parameter support for one explicitly named transported component. The provider declaration does not imply a universal property model or calibration.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.crevice_component_diffusion_1d"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/crevice_component_diffusion.py#L176)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
