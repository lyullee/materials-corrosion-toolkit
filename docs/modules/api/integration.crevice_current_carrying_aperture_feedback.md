# `integration.crevice_current_carrying_aperture_feedback`

**목적:** Caller-specified solid molar volumes map endpoint aqueous/solid states to trial aperture histories.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_current_carrying_aperture_feedback.v1", "default": "matintegrity.crevice_current_carrying_aperture_feedback.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `current_carrying_request` | 예 | `{"$ref": "#/$defs/CreviceCurrentCarryingNernstPlanckRequest"}` | 계약·필드 설명 참조 |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `face_area_weight_by_face_and_cell` | 예 | `{"items": {"items": {"minimum": 0, "type": "number"}, "type": "array"}, "maxItems": 301, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `deposit_volume_to_gap_change_factor_by_cell` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 300, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `solid_molar_volume_m3_mol_by_phase` | 예 | `{"additionalProperties": {"exclusiveMinimum": 0, "type": "number"}, "maxProperties": 32, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `solid_molar_volume_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `solid_molar_volume_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `aperture_mapping_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `aperture_mapping_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell` | 예 | `{"items": {"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `hydraulic_sensitivity_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `hydraulic_sensitivity_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_geometry_fixed_point_iterations` | 아니오 | `{"default": 30, "maximum": 1000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_transport_function_evaluations` | 아니오 | `{"default": 5000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_mixed_potential_function_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `aperture_absolute_tolerance_m` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | m |
| `aperture_relative_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `velocity_absolute_tolerance_m_s` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m/s |
| `velocity_relative_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `relaxation_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `solid_volume_to_gap_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `hydraulic_sensitivity_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `face_area_mapping_and_potential_mesh_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `current_carrying_transport_geometry_feedback_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_kinetics_and_flow_laws_only_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computation_budgets_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceCurrentCarryingApertureFeedbackRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `aperture_history_m_by_knot_and_cell[][]` | `m` |
| `cell_cross_section_area_m2_by_knot[][]` | `m^2` |
| `face_velocity_m_s_by_knot_and_face[][]` | `m/s` |
| `aperture_fixed_point_residual_m` | `m` |
| `hydraulic_fixed_point_residual_m_s` | `m/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-specified solid molar volumes map endpoint aqueous/solid states to trial aperture histories.
- Caller-specified face-velocity sensitivity maps aperture departures from the initial history to hydraulic histories.
- Each fixed-point iteration reruns the complete current-carrying Nernst-Planck, mixed-potential, Faradaic and exact-knot chemistry path.
- Only a bounded converged geometry/hydraulic trial is returned; nonconvergence preserves iteration digest lineage and fails closed.
- Sensitivity updates are explicit caller linear maps, not general deposition morphology or hydraulic constitutive laws.

## 구현 근거·독립 설명

- `bounded_picard_feedback_of_current_carrying_crevice_transport_geometry`: Repeat the complete current-carrying Nernst–Planck/Faradaic and exact-knot chemistry trajectory using caller-provided solid-volume/aperture and aperture/face-velocity sensitivity mappings. Rebuild digest-pinned area histories on every trial and commit only after both geometry and hydraulic residuals satisfy caller tolerances. This knotwise outer iteration is not a continuous within-step geometry integration and has no general uniqueness or physical-qualification guarantee.
- `bounded_geometry_hydraulic_chemistry_picard_iteration`: Bounded outer iteration over registered spatial crevice chemistry-transport, caller solid-volume/aperture mapping and caller aperture/velocity sensitivity, requiring both residual classes and inherited mass-balance gates before commit.
- `caller_solid_volume_to_aperture_response`: Caller-evidenced mapping from finite solid inventory to a spatial aperture change; this parameterized mapping does not infer deposits, porosity or roughness.
- `caller_aperture_to_hydraulic_velocity_response`: Caller-provided aperture-to-face-velocity sensitivity with pinned units, geometry, evidence and record digest; not a hydraulic constitutive law.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_current_carrying_aperture_feedback"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_current_carrying_aperture_feedback.py#L192)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
