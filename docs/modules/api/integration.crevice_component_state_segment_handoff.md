# `integration.crevice_component_state_segment_handoff`

**목적:** The source BDF request and exact Calculation result are digest-pinned and the source is committed with closed total-component ledgers.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_component_state_segment_handoff.v1", "default": "matintegrity.crevice_component_state_segment_handoff.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_bdf_request` | 예 | `{"$ref": "#/$defs/CreviceComponentStateBDFRequest"}` | 계약·필드 설명 참조 |
| `source_bdf_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `source_bdf_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `source_bdf_result_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `target_segment_start_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `cell_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 300, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_length_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | m |
| `initial_aperture_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | m |
| `geometry_basis_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_basis_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_geometry` | 예 | `{"items": {"$ref": "#/$defs/HandoffPhaseGeometry"}, "maxItems": 256, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_geometry_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `phase_geometry_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `phase_geometry_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `uniform_within_cell_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_and_phase_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_work_operations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceComponentStateSegmentHandoffRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `target_segment_start_time_s` | `s` |
| `source_initial_component_moles_mol_by_component_cell.*[]` | `mol` |
| `next_initial_total_component_moles_mol_by_component_cell.*[]` | `mol` |
| `final_solid_moles_mol_by_phase_cell.*[]` | `mol` |
| `gap_occupying_solid_volume_m3_by_cell[]` | `m3` |
| `next_cell_aperture_m[]` | `m` |
| `next_cell_cross_section_m2[]` | `m2` |
| `next_cell_solution_volume_m3[]` | `m3` |
| `next_cell_solution_volume_L[]` | `L` |
| `next_face_area_m2_by_face[]` | `m2` |
| `solid_volume_aperture_closure_residual_m3_by_cell[]` | `m3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The source BDF request and exact Calculation result are digest-pinned and the source is committed with closed total-component ledgers.
- Caller phase molar volumes and gap-occupancy mappings are fixed over this exact boundary and bound to Evidence.
- Solid coverage is represented by a caller-reviewed uniform within-cell volume that reduces the open aperture; total component moles are preserved as the next segment initial state.
- This is a segment-boundary handoff only; it does not update geometry inside the BDF RHS or solve moving-boundary dynamics.

## 구현 근거·독립 설명

- `caller_mapped_component_state_bdf_fixed_segment_handoff`: Verify an exact, result-digest-pinned committed component-state BDF Calculation with closed total-component ledgers, then preserve its final per-cell total component moles as candidate next-segment initial inventory. Caller-reviewed cell geometry, phase molar volumes and gap-occupancy mapping convert final candidate-solid moles to a positive next fixed-segment aperture, volume and interpolated face-area basis. No BDF request mutation, within-stage moving-boundary feedback, reaction, phase discovery or qualification is inferred.
- `finite_volume_conserved_component_inventory_bdf_state`: Integrate per-cell conserved aqueous component moles as the BDF state on a fixed-volume mesh with closed external boundaries; species concentrations are equilibrium reconstructions and reaction-invariant component maps provide the transported inventory basis.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_component_state_segment_handoff"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_component_state_segment_handoff.py#L96)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
