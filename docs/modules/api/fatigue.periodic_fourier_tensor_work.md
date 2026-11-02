# `fatigue.periodic_fourier_tensor_work`

**목적:** Stress and strain use the same ordered closed tensor cycle and a caller-declared tensor or engineering shear convention.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `analysis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"$ref": "#/$defs/Evidence"}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 4097, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `stress_tensor_components_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 4097, "minItems": 4, "type": "array"}` | Pa |
| `strain_tensor_components` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 4097, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `strain_shear_convention` | 예 | `{"enum": ["tensor", "engineering"], "type": "string"}` | 계약·필드 설명 참조 |
| `maximum_trigonometric_term_work` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `tensor_basis_and_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uniform_periodic_sampling_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `closed_cycle_and_path_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_strain_conjugacy_and_work_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fourier_reconstruction_suitability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PeriodicFourierTensorWork.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `signed_work_density_J_m3` | `J/m^3` |
| `component_work_density_J_m3` | `J/m^3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Stress and strain use the same ordered closed tensor cycle and a caller-declared tensor or engineering shear convention.
- The signed closed-cycle integral is exact only for the full-bandwidth periodic trigonometric interpolant of the uniform samples.
- Net work is not identified as plastic dissipation or mapped to fatigue damage or life.

## 구현 근거·독립 설명

- `caller_exact_closed_tensor_work_fourier_orthogonality_integral`: Compute exact signed closed-cycle stress-strain work for the caller's finite-bandwidth real Fourier tensor interpolant using coefficient orthogonality and the declared tensor/engineering shear convention. The result is exact for that interpolant only and is not automatically plastic dissipation or a fatigue metric.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.periodic_fourier_tensor_work"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/multiaxial_fourier_tensor_work.py#L52)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
