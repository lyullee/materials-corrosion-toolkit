# `integration.tube_bundle_lame_stress_history`

**목적:** Each tube is modeled as a homogeneous isotropic linear-elastic annular cylinder using the caller's current inner diameter and minimum wall.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.tube_bundle_lame_stress_history.v1", "default": "matintegrity.tube_bundle_lame_stress_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"maxLength": 200, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"maxLength": 200, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exchanger_id` | 예 | `{"maxLength": 200, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bundle_id` | 예 | `{"maxLength": 200, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_reference_basis_id` | 예 | `{"maxLength": 200, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_histories` | 예 | `{"items": {"$ref": "#/$defs/TubePressureStressHistory"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `tube_bundle_and_material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `current_bore_and_minimum_wall_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_is_uniform_and_axisymmetric_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_pressure_units_and_common_reference_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_history_clock_and_record_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `elastic_isotropic_axisymmetric_lame_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `axial_end_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_acceptance_capacity_or_life_claim_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_work_units` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TubeBundleLameStressHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `histories[].inner_radius_m` | `m` |
| `histories[].outer_radius_m` | `m` |
| `histories[].knot_results[].time_s` | `s` |
| `histories[].knot_results[].internal_pressure_Pa` | `Pa` |
| `histories[].knot_results[].external_pressure_Pa` | `Pa` |
| `histories[].knot_results[].surface_stresses.*.evaluation_radius_m` | `m` |
| `histories[].knot_results[].surface_stresses.*.hoop_stress_Pa` | `Pa` |
| `histories[].knot_results[].surface_stresses.*.radial_stress_Pa` | `Pa` |
| `histories[].knot_results[].surface_stresses.*.axial_stress_Pa` | `Pa` |
| `histories[].knot_results[].surface_stresses.*.von_mises_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each tube is modeled as a homogeneous isotropic linear-elastic annular cylinder using the caller's current inner diameter and minimum wall.
- Internal and external absolute pressures are nonnegative, share one caller-reviewed Pa reference, and are evaluated only at exact supplied knots.
- The caller declares the axial end condition; plugged-tube pressure paths require a separate explicit review.
- Stress descriptors are not code acceptance, pressure capacity, remaining life, or qualification results.

## 구현 근거·독립 설명

- `caller_reviewed_tube_bundle_pressure_stress_history`: Evaluate caller-supplied absolute internal/external pressure and current minimum-wall geometry at exact tube-specific time knots using the registered Lamé thick-cylinder solution at inner and outer wall surfaces. Require matched asset/bundle/tube/clock/reference identities, digest-pinned geometry and pressure records, explicit axial-end and uniform axisymmetric elasticity reviews, and bounded work. No pressure capacity, code acceptance or remaining life is inferred.
- [Cambridge engineering notes on thick cylinders](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/textbooks_dvd_only/DAN/cylinders/thick/thick.html) · `cambridge_lame`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.tube_bundle_lame_stress_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/tube_bundle_lame_stress_history.py#L129)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
