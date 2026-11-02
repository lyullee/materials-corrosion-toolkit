# `fabrication.gasket_compression_hysteresis_energy`

**목적:** Every cycle is a caller-segmented ordered compression force-displacement loop with a reviewed repeated count and closed endpoints.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_compression_hysteresis_energy.v1", "default": "matintegrity.gasket_compression_hysteresis_energy.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `initial_gasket_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `loaded_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `loops` | 예 | `{"items": {"$ref": "#/$defs/GasketCompressionLoop"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_endpoint_displacement_error_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `maximum_endpoint_force_error_N` | 예 | `{"minimum": 0, "type": "number"}` | N |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measured_displacement_is_gasket_compression_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `force_area_temperature_and_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `loop_boundaries_and_repeat_counts_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `representativeness_and_condition_transfer_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketCompressionHysteresisEnergy.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cycle_results[].signed_loop_work_J` | `J` |
| `cycle_results[].dissipated_energy_J_per_cycle` | `J` |
| `cycle_results[].dissipated_energy_density_J_m3_per_cycle` | `J/m^3` |
| `cycle_results[].positive_compression_work_J_per_cycle` | `J` |
| `cycle_results[].unloading_return_work_J_per_cycle` | `J` |
| `cycle_results[].hysteresis_loss_fraction_of_positive_work` | `1` |
| `total_repeated_dissipated_energy_J` | `J` |
| `total_repeated_dissipated_energy_density_J_m3` | `J/m^3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Every cycle is a caller-segmented ordered compression force-displacement loop with a reviewed repeated count and closed endpoints.
- The path between measurement points is reconstructed as piecewise linear and integrated by the trapezoidal work rule.
- Energy is normalized by caller initial thickness times loaded area; no constitutive law or damage criterion is inferred.

## 구현 근거·독립 설명

- `caller_gasket_compression_force_displacement_loops`: Caller-supplied ordered measured compression force-displacement loops and repeat counts with specimen Evidence.
- `caller_gasket_specimen_area_thickness_and_condition`: Caller-declared initial thickness, loaded area, material condition and measurement convention.
- `piecewise_linear_force_displacement_loop_work_integral`: Piecewise-linear reconstruction with trapezoidal force-displacement work integration.
- `closed_loop_work_as_measured_hysteresis_energy_summary`: Signed loop work and its magnitude are reported as measured-loop summaries only; no constitutive or damage law is fitted.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_compression_hysteresis_energy"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_compression_hysteresis_energy.py#L99)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
