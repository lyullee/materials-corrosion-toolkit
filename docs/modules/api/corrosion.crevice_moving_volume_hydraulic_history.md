# `corrosion.crevice_moving_volume_hydraulic_history`

**목적:** Aperture varies linearly within each caller interval, so liquid volume rate is interval constant.

**모델 버전:** `0.1.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"default": "matintegrity.crevice_moving_volume_hydraulic_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `cell_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_lengths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | m |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | m |
| `aperture_m_by_knot_and_cell` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `pressure_drop_Pa_by_interval` | 예 | `{"items": {"type": "number"}, "maxItems": 4999, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_left_boundary_flow_m3_s` | 예 | `{"type": "number"}` | m³/s |
| `density_kg_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | kg/m³ |
| `dynamic_viscosity_Pa_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa·s |
| `geometry_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_tolerance_flow_m3_s` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m³/s |
| `relative_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_pressure_closure_tolerance_Pa` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | Pa |
| `relative_pressure_closure_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 아니오 | `{"default": 1000000.0, "exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_righthand_evaluations` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_output_cell_intervals` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_width_to_aperture_ratio` | 아니오 | `{"default": 20.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 20.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_reviewed_reynolds_number` | 아니오 | `{"default": 1000.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_and_volume_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_reference_and_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incompressible_newtonian_fluid_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wide_laminar_slit_resistance_and_inertance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceMovingVolumeHydraulicHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `pressure_drop_Pa_by_interval[]` | `Pa` |
| `left_boundary_flow_m3_s_by_knot[]` | `m^3/s` |
| `interval_mean_face_flow_m3_s_by_interval[][]` | `m^3/s` |
| `cell_continuity_residual_m3_s_by_interval_and_cell[][]` | `m^3/s` |
| `maximum_absolute_cell_continuity_residual_m3_s` | `m^3/s` |
| `integrated_boundary_volume_change_residual_m3_by_interval[]` | `m^3` |
| `maximum_absolute_boundary_volume_change_residual_m3` | `m^3` |
| `cell_pressure_drop_Pa_by_interval_and_cell[][]` | `Pa` |
| `cell_volume_rate_m3_s_by_interval_and_cell[][]` | `m^3/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Aperture varies linearly within each caller interval, so liquid volume rate is interval constant.
- One common pressure forcing drives the series momentum balance; continuity determines downstream face-flow offsets from cell volume rates.
- The reduced slit resistance/inertance law is only used inside declared wide-slit, laminar and fluid-property support.

## 구현 근거·독립 설명

- `caller_evidenced_pressure_driven_moving_slit_volume_history`: Use caller-supplied exact-knot cell apertures, ordered dimensions, fluid density/viscosity, signed total pressure-drop intervals and initial inlet flow. Treat aperture as linear and pressure as constant inside each declared interval; apply incompressible continuity to recover cell face-flow differences and independently integrate the resulting reduced series momentum ODE. No pressure, geometry, fluid property, deposit morphology or applicability parameter is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.crevice_moving_volume_hydraulic_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_moving_volume_hydraulic_history.py#L109)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
