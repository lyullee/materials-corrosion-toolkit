# `integration.wet_co2_reactive_film_transfer`

**목적:** One-dimensional steady stagnant liquid-film diffusion with constant diffusivity and a caller-supplied irreversible first-order sink in CO2star.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_reactive_film_transfer.v1", "default": "matintegrity.wet_co2_reactive_film_transfer.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `gas_co2_fugacity_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `bulk_co2star_concentration_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `henry_concentration_over_fugacity_mol_m3_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `gas_film_coefficient_mol_m2_s_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `liquid_physical_film_coefficient_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `co2star_diffusivity_m2_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m²/s |
| `apparent_irreversible_first_order_sink_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `state_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `state_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `state_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `state_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `state_units_and_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `first_order_irreversible_sink_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `excess_reactant_and_constant_rate_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `film_model_and_co2star_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_property_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2ReactiveFilmTransferRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `temperature_K` | `K` |
| `hatta_number` | `1` |
| `gas_to_liquid_co2_uptake_flux_mol_m2_s` | `mol/(m2 s)` |
| `liquid_film_to_bulk_co2star_flux_mol_m2_s` | `mol/(m2 s)` |
| `liquid_film_reaction_sink_flux_mol_m2_s` | `mol/(m2 s)` |
| `interfacial_flux_balance_residual_mol_m2_s` | `mol/(m2 s)` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One-dimensional steady stagnant liquid-film diffusion with constant diffusivity and a caller-supplied irreversible first-order sink in CO2star.
- Gas-side film is physical; local Henry relation is linear and both phase bulk states remain fixed during the calculation.
- The liquid film sink kinetics are valid and pseudo-first-order across the film; no competing reactions or reagent depletion are represented.
- The result is a local instantaneous flux split and carries no geometry, corrosion, or lifetime interpretation.

## 구현 근거·독립 설명

- `caller_pseudofirst_order_co2_film_kinetics`: Solve a steady one-dimensional stagnant-film diffusion/reaction balance using a caller apparent irreversible first-order CO2star sink coupled algebraically with gas-film resistance. Report gas uptake, liquid-film reaction consumption and bulk CO2star delivery separately with mass-balance residual. No kinetic fit, carbonate equilibrium, flow renewal, corrosion or risk is inferred.
- [Determination of fast gas-liquid reaction kinetics in flow](https://doi.org/10.1039/C9RE00390H) · `rsc_fast_gas_liquid_reaction_kinetics`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_reactive_film_transfer"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_reactive_film_transfer.py#L86)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
