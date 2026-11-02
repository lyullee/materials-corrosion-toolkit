# `chemistry.crevice_competing_solid_equilibrium`

**목적:** One fixed, homogeneous solution volume and one temperature are used with fixed caller activity coefficients and standard states.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `standard_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `aqueous_species` | 예 | `{"items": {"$ref": "#/$defs/CreviceEquilibriumAqueousSpecies"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `solid_phases` | 예 | `{"items": {"$ref": "#/$defs/CreviceCompetingSolidPhase"}, "maxItems": 12, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_charge_balance_tolerance_mol_charge_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_inventory_balance_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `relative_inventory_balance_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0.0, "maximum": 0.0001, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_log_saturation_residual` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_state_convergence_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0.0, "maximum": 0.0001, "type": "number"}` | 계약·필드 설명 참조 |
| `solid_presence_tolerance_mol_m3` | 아니오 | `{"default": 1e-12, "minimum": 0, "type": "number"}` | mol/m³ |
| `maximum_active_set_sweeps` | 아니오 | `{"default": 100, "maximum": 10000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `fixed_gamma_standard_states_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equilibrium_constants_applicable_to_declared_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `instantaneous_equilibrium_no_kinetic_barrier_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `shared_solution_volume_and_complete_candidate_set_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceCompetingSolidEquilibriumRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `aqueous_species[].initial_concentration_mol_m3` | `mol/m^3` |
| `aqueous_species[].final_concentration_mol_m3` | `mol/m^3` |
| `solid_phases[].initial_solid_moles_per_solution_volume_mol_m3` | `mol/m^3` |
| `solid_phases[].final_solid_moles_per_solution_volume_mol_m3` | `mol/m^3` |
| `solid_phases[].net_extent_mol_m3` | `mol/m^3` |
| `aqueous_charge_balance_residual_mol_charge_m3` | `mol-charge/m^3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One fixed, homogeneous solution volume and one temperature are used with fixed caller activity coefficients and standard states.
- Each candidate phase is a neutral pure solid with explicit charge and elemental balance in its dissolution/precipitation reaction.
- The bounded sequential active-set iteration must converge and satisfy present/absent phase complementarity before values are committed.
- The calculation is an equilibrium screen, not a kinetic or global phase-stability solver.

## 구현 근거·독립 설명

- `caller_competing_solid_aqueous_state`: Caller supplies the initial shared aqueous state, explicit charge/element composition, activity reference concentration and fixed activity coefficients, with a digest-bound record for each species; no speciation or electrolyte properties are inferred.
- `caller_competing_solid_equilibrium_constants`: Caller supplies a finite candidate set of neutral pure solids, balanced aqueous reactant stoichiometries, initial solid inventories and digest-bound dimensionless solubility products at the declared temperature and standard state; no phase is selected or parameterized automatically.
- `bounded_sequential_active_set_multi_solid_equilibrium`: Apply an ordered bounded scalar equilibrium update over a finite caller phase list, iterate the shared liquid inventory until state convergence, and enforce present/absent saturation complementarity plus charge and extent closure. This software composition is not a global Gibbs-energy minimization or empirical validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.crevice_competing_solid_equilibrium"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_competing_solid_equilibrium.py#L212)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
