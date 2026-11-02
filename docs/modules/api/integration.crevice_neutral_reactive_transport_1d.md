# `integration.crevice_neutral_reactive_transport_1d`

**목적:** Caller-defined neutral chemical species undergo reversible local mass-action reactions while diffusing through a fixed one-dimensional finite-volume geometry.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `model_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `model_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `length_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `cross_section_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `cell_count` | 예 | `{"maximum": 300, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `output_time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | s |
| `species` | 예 | `{"items": {"$ref": "#/$defs/ReactiveTransportSpecies"}, "maxItems": 30, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `reactions` | 예 | `{"items": {"$ref": "#/$defs/ReactiveTransportReaction"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `mouth_boundary_concentration_mol_m3_by_species` | 예 | `{"additionalProperties": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxProperties": 30, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `maximum_step_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_function_evaluations` | 아니오 | `{"default": 200000, "maximum": 10000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `provider_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_and_spatial_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `homogeneous_neutral_mass_action_network_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `kinetic_parameter_support_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_advection_and_fixed_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceNeutralReactiveTransportRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cell_width_m` | `m` |
| `maximum_absolute_finite_volume_balance_residual_mol` | `mol` |
| `finite_volume_balance_residual_mol_by_species.*[]` | `mol` |
| `state_history[].time_s` | `s` |
| `state_history[].concentration_mol_m3_by_species.*[]` | `mol/m^3` |
| `state_history[].inventory_mol_by_species.*` | `mol` |
| `state_history[].integrated_boundary_transfer_mol_by_species.*` | `mol` |
| `state_history[].integrated_reaction_transfer_mol_by_species.*` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-defined neutral chemical species undergo reversible local mass-action reactions while diffusing through a fixed one-dimensional finite-volume geometry.
- The caller supplies rate constant values at each output knot; both boundary concentrations and rate constants are linearly interpolated between knots.
- The mouth is Dirichlet and the blind tip is no-flux; advection, electromigration and wall reaction are excluded.

## 구현 근거·독립 설명

- `caller_crevice_neutral_reaction_diffusion_network`: Require a caller-defined finite neutral-species reaction network with atom-balanced reversible mass-action terms, species diffusivities, fixed geometry and explicit kinetic parameter lineage. No ionic activity, wall reaction, phase equilibrium or corrosion mechanism is implied.
- `caller_crevice_reactive_transport_mouth_history`: Apply caller-provided ordered mouth concentration and reaction-rate schedules at explicit time knots to a fixed-geometry, blind-tip crevice transport calculation. Input interpolation and boundary meaning remain caller reviewed.
- `finite_volume_diffusion_with_local_reversible_mass_action`: Co-integrate one-dimensional fixed-geometry Fick diffusion and caller-defined local reversible mass-action kinetics using finite volumes and a stiff initial-value solver. Track boundary transfer, reaction transfer and species inventory residuals; no convection, electromigration, wall kinetics or corrosion is inferred.
- [SciPy scipy.integrate.solve_ivp API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) · `scipy_integrate_solve_ivp`
- `scipy_integrate_bdf`: Integrate the declared stiff initial-value transport system with SciPy's variable-order backward differentiation formula implementation using caller-selected tolerances and ordered output times; numerical solver choice does not establish physical validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_neutral_reactive_transport_1d"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_reactive_transport_1d.py#L153)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
