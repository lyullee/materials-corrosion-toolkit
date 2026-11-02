# `integration.crevice_calibrated_wall_flux_callback`

**목적:** A calibrated effective wall-transfer velocity and a caller-supplied equilibrium surface concentration define inward flux J=k_w(C_surface-C_bulk).

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_calibrated_wall_flux_callback.v1", "default": "matintegrity.crevice_calibrated_wall_flux_callback.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `callback_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `species_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibrated_wall_rate_history_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `calibrated_wall_rate_history_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_history` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `geometry_history_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `wall_equilibrium_concentration_mol_m3_by_knot_by_cell` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 256, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `temperature_clock_and_geometry_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_species_restricted_transport_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `linear_inter_knot_rate_and_surface_state_path_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `robin_flux_sign_and_surface_concentration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibrated_condition_and_geometry_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceCalibratedWallFluxRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s[]` | `s` |
| `wall_transfer_velocity_m_s[]` | `m/s` |
| `concentration_support_mol_m3[][]` | `mol/m3` |
| `wall_flux_sign_convention` | `mol/(m2 s)` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A calibrated effective wall-transfer velocity and a caller-supplied equilibrium surface concentration define inward flux J=k_w(C_surface-C_bulk).
- Rate, surface concentration and geometry histories share exact ordered knots and cell identity; interpolation is linear only between the supplied knots and no time extrapolation is allowed.
- The callback supports one species and returns one inward molar flux per cell; the transport solver applies its wall-area-per-volume geometry exactly once.
- The caller's equilibrium surface concentration and application condition must be physically reviewed; no surface chemistry is solved here.
- The callback is intended for the existing restricted-transport/crevice campaign wall boundary and does not run or alter a transport calculation.

## 구현 근거·독립 설명

- `caller_crevice_calibrated_wall_flux_boundary`: Build a bounded, evidence-linked callable wall-flux boundary from a digest-verified calibrated effective wall-transfer history and caller surface-concentration history. Require exact shared time/cell geometry, species and condition identity, and explicit sign/interpolation reviews. Flux is inward-positive and supplied to the transport solver, which owns area weighting; the adapter neither runs transport nor models surface chemistry or corrosion.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_calibrated_wall_flux_callback"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_calibrated_wall_flux_callback.py#L165)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
