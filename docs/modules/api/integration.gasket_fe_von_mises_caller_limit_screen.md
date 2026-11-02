# `integration.gasket_fe_von_mises_caller_limit_screen`

**목적:** Six imported symmetric Cauchy stress components in one caller-mapped Cartesian frame are reduced by the J2/von Mises invariant.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_fe_von_mises_caller_limit_screen.v1", "default": "matintegrity.gasket_fe_von_mises_caller_limit_screen.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `imported_fe_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `imported_fe_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `expected_asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `expected_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `expected_joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `expected_physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `expected_provider_component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `expected_coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `tensor_component_mapping` | 예 | `{"items": {"$ref": "#/$defs/TensorComponentBinding"}, "maxItems": 6, "minItems": 6, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_caller_von_mises_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `criterion_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_basis_description` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `criterion_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `tensor_component_frame_and_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_temperature_material_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `averaging_basis_and_hotspot_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_limit_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketFEVonMisesCallerLimitScreen.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `maximum_caller_von_mises_stress_Pa` | `Pa` |
| `findings[].time_s` | `s` |
| `findings[].von_mises_equivalent_stress_Pa` | `Pa` |
| `findings[].caller_limit_Pa` | `Pa` |
| `findings[].margin_Pa` | `Pa` |
| `maximum_stress_witness.von_mises_equivalent_stress_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Six imported symmetric Cauchy stress components in one caller-mapped Cartesian frame are reduced by the J2/von Mises invariant.
- The computed scalar is compared with an explicitly supplied evidence-bound caller limit at one declared material state and temperature.
- A passing threshold relation is not code stress acceptance, material qualification or proof of physical integrity.

## 구현 근거·독립 설명

- `imported_gasket_fe_stress_tensor_components_and_frame`: Imported six-component symmetric Cauchy stress tensor field with provider frame and exact scope lineage.
- `three_dimensional_j2_von_mises_equivalent_stress_invariant`: Independent three-dimensional J2 equivalent stress invariant applied to the imported tensor components.
- `caller_material_condition_temperature_and_equivalent_stress_limit`: Caller-supplied material condition, temperature and evidence-bound scalar stress threshold.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.gasket_fe_von_mises_caller_limit_screen"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_fe_von_mises_caller_limit_screen.py#L114)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
