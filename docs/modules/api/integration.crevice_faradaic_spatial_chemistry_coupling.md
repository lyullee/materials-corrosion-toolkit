# `integration.crevice_faradaic_spatial_chemistry_coupling`

**목적:** Caller declares all branch kinetics, standard potentials, activity quotient coefficients, conductivity mappings, reaction stoichiometry and external element reservoirs.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_faradaic_spatial_chemistry.v1", "default": "matintegrity.crevice_faradaic_spatial_chemistry.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transport_chemistry` | 예 | `{"$ref": "#/$defs/CreviceSpatialChemistryTransportRequest"}` | 계약·필드 설명 참조 |
| `mixed_potential_template` | 예 | `{"$ref": "#/$defs/CreviceSpatialOhmicMixedPotentialRequest"}` | 계약·필드 설명 참조 |
| `nernst_branch_maps` | 예 | `{"items": {"$ref": "#/$defs/CreviceNernstBranchMap"}, "maxItems": 32, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `faradaic_branch_maps` | 예 | `{"items": {"$ref": "#/$defs/CreviceFaradaicBranchMap"}, "maxItems": 32, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `background_conductivity_S_m_by_knot_and_cell` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `molar_conductivity_S_m2_mol_by_species_knot_and_cell` | 예 | `{"additionalProperties": {"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "type": "array"}, "maxProperties": 40, "minProperties": 2, "type": "object"}` | 계약·필드 설명 참조 |
| `conductivity_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `conductivity_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_faradic_charge_source_tolerance_mol_eq_s` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | s |
| `relative_faradic_charge_source_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `current_balance_tolerance_A` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_inventory_balance_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_inventory_balance_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_right_endpoint_iterations` | 아니오 | `{"default": 30, "maximum": 1000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `current_density_absolute_tolerance_A_m2` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | A/m² |
| `current_relative_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `chemistry_state_relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `current_relaxation_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_total_transport_function_evaluations` | 아니오 | `{"default": 5000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_mixed_potential_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `activity_quotient_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `branch_species_and_reservoir_stoichiometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_net_aqueous_faradic_charge_source_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mixed_potential_current_and_area_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `endpoint_trapezoid_faradic_extent_split_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_unmodeled_double_layer_or_electrochemical_transport_current_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceFaradaicSpatialChemistryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `intervals[].start_time_s` | `s` |
| `intervals[].end_time_s` | `s` |
| `intervals[].faradaic_extent_mol_by_branch_and_cell.*[]` | `mol` |
| `intervals[].net_electrode_current_A_by_cell[]` | `A` |
| `intervals[].branch_current_density_A_m2_by_id_and_cell.*[]` | `A/m^2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller declares all branch kinetics, standard potentials, activity quotient coefficients, conductivity mappings, reaction stoichiometry and external element reservoirs.
- Transport is advanced first, Faradaic branch extents are applied by endpoint trapezoid, and the local caller chemistry is then re-solved at exact knots.
- The reused variable-area transport kernel requires zero ionic current at every face; any endpoint mixed-potential result with nonzero electrolyte face current is rejected.
- No double-layer current, intrastage chemistry/electrochemistry, automatic mechanism discovery or material qualification is included.

## 구현 근거·독립 설명

- `caller_faradaic_branch_species_and_reservoir_stoichiometry`: Caller branch mapping for local species/current stoichiometry and external elemental reservoirs, tied to electron count and face area for extent conversion.
- `caller_spatial_nernst_standard_potential_and_activity_quotient`: Caller-pinned spatial standard potential and dimensionless activity quotient coefficients for each Faradaic branch.
- `caller_species_molar_conductivity_mapping`: Caller-pinned ionic molar-conductivity mapping evaluated from the local species state.
- `knotwise_spatial_mixed_potential_faradaic_inventory_split`: Endpoint split combining variable-area transport, exact-knot Faradaic extents, chemistry re-solve and local mixed-potential iteration; nonzero face current is rejected by the reused kernel contract.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_faradaic_spatial_chemistry_coupling"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_faradaic_spatial_chemistry_coupling.py#L287)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
