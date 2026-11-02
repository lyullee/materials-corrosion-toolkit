# `integration.crevice_moving_volume_liquid_continuity`

**목적:** Linear aperture change between exact knots implies constant interval-mean volume rate.

**모델 버전:** `0.1.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"default": "matintegrity.crevice_moving_volume_continuity.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | s |
| `cell_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_lengths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 300, "minItems": 1, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `aperture_m_by_knot_and_cell` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `left_boundary_flow_m3_s_by_knot` | 예 | `{"items": {"type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `right_boundary_flow_m3_s_by_knot` | 예 | `{"items": {"type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `boundary_flow_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_boundary_and_sign_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incompressible_liquid_and_fixed_mesh_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_flow_closure_tolerance_m3_s` | 아니오 | `{"default": 1e-15, "exclusiveMinimum": 0, "type": "number"}` | m³/s |
| `relative_flow_closure_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceMovingVolumeContinuityRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `cell_volume_m3_by_knot_and_cell[][]` | `m^3` |
| `cell_volume_rate_m3_s_by_interval_and_cell[][]` | `m^3/s` |
| `face_flow_m3_s_by_interval_and_face[][]` | `m^3/s` |
| `cell_continuity_residual_m3_s_by_interval_and_cell[][]` | `m^3/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Linear aperture change between exact knots implies constant interval-mean volume rate.
- Positive face flow is left-to-right and each cell obeys dV/dt = Q_left - Q_right.
- This operator supplies a conservative kinematic schedule only; it does not solve pressure-driven momentum or reactive transport.

## 구현 근거·독립 설명

- `caller_evidenced_slit_volume_and_boundary_flow_continuity`: Use caller-supplied ordered cell lengths, slit width, aperture history and both signed boundary-flow histories to close interval-mean incompressible liquid continuity on a fixed mesh. Linear aperture interpolation is an explicit interval assumption; the operator does not infer a pressure-flow relation or physical qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_moving_volume_liquid_continuity"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_moving_volume_continuity.py#L94)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
