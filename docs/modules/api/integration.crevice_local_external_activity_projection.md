# `integration.crevice_local_external_activity_projection`

**목적:** Transported cell compositions set only the explicitly selected mass-action constraint targets; each exact cell then solves an independent caller-reviewed activity fixed point.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_local_mass_action_projection.v1", "default": "matintegrity.crevice_local_mass_action_projection.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transport_binding` | 예 | `{"$ref": "#/$defs/CreviceTransportCompositionBridge"}` | 계약·필드 설명 참조 |
| `transport_binding_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `transport_binding_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `knots` | 예 | `{"items": {"$ref": "#/$defs/CreviceMassActionProjectionKnot"}, "maxItems": 500, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `composition_derived_constraint_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `zero_concentration_initial_activity_guess` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `cell_composition_to_constraint_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_component_inventory_and_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_activity_and_equilibrium_parameter_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cell_specific_temperature_and_solution_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_liquid_no_solid_transition_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_interknot_kinetics_or_transport_feedback_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_concentration_seed_is_numerical_only_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_iteration_template` | 예 | `{"$ref": "#/$defs/ExternalAqueousActivityIteration"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceLocalExternalActivityProjectionRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `knots[].time_s` | `s` |
| `knots[].cells[].system_template.temperature_K` | `K` |
| `knots[].cells[].system_template.constraints[].target_mol_L` | `mol/L` |
| `knots[].cells[].species_inventory_mol.*` | `mol` |
| `knots[].cells[].activity_coefficient_molarity_standard_state_by_species.*` | `1` |
| `knots[].cells[].external_activity_fixed_point_residual_ln` | `1` |
| `knots[].cells[].external_activity_fixed_point_iteration_count` | `1` |
| `final_knot_total_species_inventory_mol.*` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Transported cell compositions set only the explicitly selected mass-action constraint targets; each exact cell then solves an independent caller-reviewed activity fixed point.
- The activity provider is injected as an explicit runtime dependency and must match the provider identity, revision, configuration digest, parameter digest, species ordering and molality standard state in the request.
- Reaction topology, equilibrium constants, cell temperature, water-mass conversion, activity convention and one-liquid scope are caller declared; no phase transition, inter-knot kinetic evolution or transport feedback is computed.
- Only complete exact transport knots are committed, and the mass-action ledger retains both the converged inner-system input digest and external-provider transcript.

## 구현 근거·독립 설명

- `caller_component_constraint_basis_for_crevice_local_speciation`: For each cell and exact knot of a digest-pinned crevice transport-composition campaign, replace only the caller-selected linear mass-action constraint targets with the corresponding caller-declared component sums of that cell concentration converted from mol/m3 to mol/L, preserve every unselected target, and execute the supplied fixed-activity single-liquid mass-action solver. Keep the activity coefficients, reaction network, equilibrium constants, temperature and phase scope caller supplied. Preserve complete-knot prefixes and cell/result lineage. This is an independent local operator-split equilibrium projection; it does not feed results back to transport, interpolate time, discover phases, or infer corrosion or qualification.
- `caller_crevice_local_speciation_volume_ledger`: Bind separately computed, digest-pinned aqueous mass-action results to every cell at exact knots of one digest-pinned crevice transport-composition campaign. Require explicit review of state-to-constraint mapping, species/result lineage, spatial separation, volume basis and no bulk/phase inference. Convert declared mol/L species concentrations to conditional per-cell inventories from the supplied m3 volumes; report charge and available elemental totals as diagnostics and retain only complete exact-knot prefixes. Do not solve equilibrium, mix compartments, infer charge closure, kinetics, corrosion or acceptance.
- `caller_external_aqueous_activity_provider`: Accept caller-computed composition-dependent molality-standard-state activity coefficients from an external Python callback and couple them to the existing molarity-standard-state mass-action solver with bounded damped fixed-point iteration. Bind each provider request to the exact temperature, ordered species/charges, molality vector, ionic strength and water-mass basis; require provider identity/revision, configuration and parameter digests, exact species coverage/order, echoed request digest, declared single-ion convention, ionic-strength agreement, evidence and explicit applicability reviews. Convert gamma_m to gamma_c=gamma_m/w for the 1 mol/L mass-action basis. The same provider boundary can supply molality gamma values to a restricted-transport callback at each mouth/cell state using the caller-declared fixed solvent-mass basis. The project imports and bundles no thermodynamic provider, parameter table or license-restricted implementation; the adapter does not qualify provider equations, parameter coverage, local equilibrium or solution chemistry.
- `caller_crevice_local_external_activity_projection`: For each exact digest-bound transport cell, derive only the explicitly selected mass-action constraint targets from the caller-declared component basis, then solve that cell's liquid mass-action state with a caller-injected, evidence-bound molality activity provider using the existing damped activity fixed-point solver. Bind provider identity, revision, configuration and parameter digests; preserve the exact converged inner mass-action input digest, provider transcript and complete-knot prefix. Reaction topology, equilibrium constants, temperature support, solvent conversion and single-ion convention remain caller declared. The independent cell solves do not create phase transitions, inter-knot kinetics, transport feedback, a qualified aqueous activity model or corrosion rate.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_local_external_activity_projection"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'activity_provider': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_local_speciation_ledger.py#L704)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
