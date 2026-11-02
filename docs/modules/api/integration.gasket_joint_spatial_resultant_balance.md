# `integration.gasket_joint_spatial_resultant_balance`

**목적:** Only exact-knot per-bolt forces from one computed multi-bolt joint result are reconciled with one computed static unilateral contact field.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_joint_spatial_resultant_balance.v1", "default": "matintegrity.gasket_joint_spatial_resultant_balance.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bolt_load_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `bolt_load_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `selected_step_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `contact_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `contact_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `contact_evaluation_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `contact_time_alignment_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `contact_time_alignment_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `contact_time_alignment_usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `contact_time_alignment_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `bolt_positions` | 예 | `{"items": {"$ref": "#/$defs/GasketBoltPlanarPosition"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_node_positions` | 예 | `{"items": {"$ref": "#/$defs/GasketContactNodePlanarPosition"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_center_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `external_moment_Mx_Nm` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `external_moment_My_Nm` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `external_moment_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `external_moment_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `external_moment_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `external_moment_usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `external_moment_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `force_balance_tolerance_N` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | N |
| `moment_balance_tolerance_Nm` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `bolt_contact_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exact_knot_time_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `planar_coordinate_and_sign_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `external_moment_not_double_counted_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_lineage_and_license_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `external_moment_lineage_and_license_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketJointSpatialResultantBalance.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `selected_time_s` | `s` |
| `bolt_closing_force_sum_N` | `N` |
| `gasket_compressive_contact_force_sum_N` | `N` |
| `axial_force_balance_residual_N` | `N` |
| `bolt_closing_moment_Mx_Nm` | `N*m` |
| `bolt_closing_moment_My_Nm` | `N*m` |
| `gasket_contact_opening_moment_Mx_Nm` | `N*m` |
| `gasket_contact_opening_moment_My_Nm` | `N*m` |
| `moment_balance_residual_Mx_Nm` | `N*m` |
| `moment_balance_residual_My_Nm` | `N*m` |
| `gasket_contact_center_of_pressure_xy_m` | `m` |
| `finite_node_total_area_m2` | `m^2` |
| `finite_node_contact_area_m2` | `m^2` |
| `finite_node_contact_area_fraction` | `1` |
| `maximum_nodal_mean_contact_pressure_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only exact-knot per-bolt forces from one computed multi-bolt joint result are reconciled with one computed static unilateral contact field.
- Planar moment arms are caller-evidenced coordinates relative to one named reference center; Mx=Σ(yF), My=−Σ(xF) for declared force magnitudes.
- External moment values and their sign convention are caller-supplied and digest-bound; upstream scalar separating force is used exactly once.
- Finite-node contact-area fraction and nodal pressure resultants are descriptors of the supplied mesh/discretization, not continuous-field integrals.
- Residual tolerance indicators are descriptive; no seal acceptance, local stress, leakage, code compliance, life or probability is inferred.

## 구현 근거·독립 설명

- `caller_gasket_joint_spatial_resultant_balance`: Reconcile digest-pinned per-bolt tensile forces and a computed unilateral contact field at a caller-reviewed exact common time. Compute discrete axial force and planar moment residuals, center of pressure and finite-node area/pressure descriptors from caller geometry; do not infer continuous fields or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.gasket_joint_spatial_resultant_balance"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_joint_spatial_resultants.py#L207)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
