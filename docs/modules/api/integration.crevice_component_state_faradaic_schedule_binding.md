# `integration.crevice_component_state_faradaic_schedule_binding`

**목적:** Producer and component-state time knots, species order/charge, cell order and initial conserved inventories must match.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_state_request` | 예 | `{"$ref": "#/$defs/CreviceComponentStateBDFRequest"}` | 계약·필드 설명 참조 |
| `current_carrying_request` | 예 | `{"$ref": "#/$defs/CreviceCurrentCarryingNernstPlanckRequest"}` | 계약·필드 설명 참조 |
| `current_carrying_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `cell_bindings` | 예 | `{"items": {"$ref": "#/$defs/CreviceCurrentCarryingCellBinding"}, "maxItems": 300, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_order_and_physical_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sequential_endpoint_current_reconstruction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_and_reservoir_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `derived_current_schedule_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceCurrentCarryingComponentStateBinding.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `current_carrying_result.values.exact_knot_ionic_face_current_A_by_boundary[][]` | `A` |
| `current_carrying_result.values.exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]` | `A/m^2` |
| `component_state_request.electrochemical_sources[].extent_rate_mol_s_by_knot_and_cell[][]` | `mol/s` |
| `component_state_request.ionic_face_current_schedule.current_A_by_knot_and_face[][]` | `A` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Producer and component-state time knots, species order/charge, cell order and initial conserved inventories must match.
- Exact-knot current density is converted to extent rate using the producer's declared per-cell reactive area and electron number.
- The resulting current and extent schedules are linearly reconstructed between exact knots; no stage mixed-potential feedback is implied.
- Caller source, reservoir, current, cell mapping and computational-use reviews are mandatory.

## 구현 근거·독립 설명

- `bound_crevice_current_carrying_result_to_component_state_schedules`: Bind a fully committed, digest-matched exact-knot CREVICE current-carrying result into a conserved-component BDF request. Preserve cell order, match initial component inventories, convert caller branch current densities to signed per-cell extent-rate schedules using the declared electron number and reactive area, carry ionic face currents, and require review of the sequential reconstruction. Reject stage-re-solved mixed-potential results because endpoint knots cannot reproduce their within-stage current history.
- `caller_evidenced_ionic_face_current_schedule`: Use review-gated caller-supplied exact-knot ionic currents on all faces, zero external boundary currents, and matching source-schedule times. Check each cell charge balance against Faraday-scaled reaction extents, solve the Nernst-Planck migration gradient to reproduce the requested interior current, and report ampere residuals and integrated charge; currents are not inferred from mixed-potential or Butler-Volmer kinetics.
- `nist_codata_faraday_constant_2022`: CODATA Faraday constant used as an exact conversion constant; no source data table or prose is reproduced.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_component_state_faradaic_schedule_binding"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_component_state_faradaic_binding.py#L248)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
