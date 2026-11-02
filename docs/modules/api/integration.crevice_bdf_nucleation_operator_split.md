# `integration.crevice_bdf_nucleation_operator_split`

**목적:** Each original interval is operator split: aqueous-only fixed-volume component BDF first, cellwise seed/growth ledger second.

**모델 버전:** `0.1.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_bdf_nucleation_operator_split.v1", "default": "matintegrity.crevice_bdf_nucleation_operator_split.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bdf_request` | 예 | `{"$ref": "#/$defs/CreviceComponentStateBDFRequest"}` | 계약·필드 설명 참조 |
| `kinetic_cells` | 예 | `{"items": {"$ref": "#/$defs/FixedKineticCell"}, "maxItems": 300, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetic_cell_order_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_cell_order_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_total_bdf_rhs_evaluations` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_stage_equilibrium_calls` | 아니오 | `{"default": 2000000, "maximum": 40000000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_nested_equilibrium_iteration_work` | 아니오 | `{"default": 100000000, "maximum": 2000000000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_kinetic_ledger_evaluations` | 아니오 | `{"default": 2000000, "maximum": 40000000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_output_records` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `bdf_then_kinetics_split_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_component_projection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_geometry_and_volume_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_external_sources_or_boundary_advection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceBDFNucleationOperatorSplitRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `state_history[].aqueous_concentration_mol_m3_by_cell[][]` | `mol/m^3` |
| `state_history[].solid_inventory_mol_m3_by_cell[][]` | `mol/m^3` |
| `state_history[].aqueous_component_moles_by_component_and_cell.*[]` | `mol` |
| `maximum_aqueous_plus_solid_component_closure_residual_mol` | `mol` |
| `maximum_kinetic_charge_closure_residual_mol_eq` | `mol_eq` |
| `interval_ledgers[].absolute_start_time_s` | `s` |
| `interval_ledgers[].absolute_end_time_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each original interval is operator split: aqueous-only fixed-volume component BDF first, cellwise seed/growth ledger second.
- Post-kinetic dissolved species are projected through explicit BDF conserved-component maps; solid phase amounts remain separately carried between intervals.
- Absolute caller saturation record digests are retained while the existing zero-origin batch ledger uses an exact relative-time translation per interval.
- No transport occurs during kinetic substeps and no geometry feedback is applied.

## 구현 근거·독립 설명

- `caller_component_bdf_then_cellwise_seed_kinetic_operator_split`: For each exact interval, integrate fixed-volume aqueous conserved-component BDF transport, apply independent digest-bound cell seed/growth ledgers, verify species-to-component and aqueous-plus-solid closure, and carry post-kinetic aqueous and solid inventories to the next interval. This sequential operator split rejects source, hydraulic, Faradaic, prescribed-current and moving-geometry modes.
- `exact_translation_of_absolute_saturation_interval_to_local_ledger_clock`: Translate each absolute caller saturation interval to the zero-origin local clock required by the closed-batch kinetic ledger, pin the derived interval digest, preserve the original source digest and record the exact affine map for absolute event times.
- `finite_volume_conserved_component_inventory_bdf_state`: Integrate per-cell conserved aqueous component moles as the BDF state on a fixed-volume mesh with closed external boundaries; species concentrations are equilibrium reconstructions and reaction-invariant component maps provide the transported inventory basis.
- `caller_fixed_volume_cellwise_seed_threshold_kinetic_ledgers`: Apply digest-bound, exact seed-threshold nucleation/growth ledgers independently to ordered fixed-volume cells, convert concentration histories to cell moles and aggregate after every cell commits. The operator-split adapter has no inter-cell transport or geometry feedback.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_bdf_nucleation_operator_split"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_bdf_nucleation_operator_split.py#L313)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
