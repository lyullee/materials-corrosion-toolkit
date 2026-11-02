# `integration.crevice_component_state_segment_transition`

**목적:** Source BDF result is full-digest-bound, committed and component-ledger closed.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_component_state_segment_transition.v1", "default": "matintegrity.crevice_component_state_segment_transition.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_request` | 예 | `{"$ref": "#/$defs/CreviceComponentStateBDFRequest"}` | 계약·필드 설명 참조 |
| `source_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `source_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `source_result_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `next_request_template` | 예 | `{"$ref": "#/$defs/CreviceComponentStateBDFRequest"}` | 계약·필드 설명 참조 |
| `next_geometry` | 예 | `{"$ref": "#/$defs/CreviceSegmentGeometry"}` | 계약·필드 설명 참조 |
| `boundary_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `committed_result_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `component_basis_continuity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_transition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_work_operations` | 아니오 | `{"default": 500000, "maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceComponentStateSegmentTransitionRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `boundary_time_s` | `s` |
| `next_geometry.aperture_m[]` | `m` |
| `next_geometry.solution_volume_L[]` | `L` |
| `next_geometry.interior_face_area_m2[]` | `m^2` |
| `next_geometry.center_distance_m[]` | `m` |
| `next_initial_component_inventory[].inventory_mol_by_cell[]` | `mol` |
| `source_segment_component_inventory_change_mol_by_component_cell.*[]` | `mol` |
| `cell_volume_change_L[]` | `L` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Source BDF result is full-digest-bound, committed and component-ledger closed.
- Caller supplies digest/Evidence-bound next geometry and retains cell identity/order.
- Final conserved component moles transfer cellwise as the next segment initial state without concentration remapping.
- This is an operator-split segment transition, not an intrastep moving-boundary or monolithic solver.

## 구현 근거·독립 설명

- `caller_mapped_committed_component_bdf_segment_transition`: Bind a committed, full-digest-pinned component-state BDF result and an Evidence-pinned caller-supplied target segment geometry. Preserve each conserved component mole inventory cellwise at the exact segment boundary, validate component/species identity and aperture-derived solution-volume closure, and construct a typed next-segment BDF request. This is an operator-split boundary transition; it does not derive geometry from deposits, remap across changing cell topology, or feed geometry back within a BDF RHS.
- `finite_volume_conserved_component_inventory_bdf_state`: Integrate per-cell conserved aqueous component moles as the BDF state on a fixed-volume mesh with closed external boundaries; species concentrations are equilibrium reconstructions and reaction-invariant component maps provide the transported inventory basis.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_component_state_segment_transition"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_component_state_segment_transition.py#L127)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
