# `chemistry.caller_surface_scale_kinetics`

**목적:** Integrate caller-calibrated single-phase precipitation and dissolution flux laws over constant or explicitly reviewed linear saturation intervals, with inventory-bounded dissolution.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.caller_surface_scale_kinetics.v1", "default": "matintegrity.caller_surface_scale_kinetics.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scale_phase_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `condition_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `initial_scale_thickness_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `precipitation_rate_constant_mol_m2_s` | 예 | `{"minimum": 0, "type": "number"}` | mol/(m²·s) |
| `rate_reference_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `minimum_rate_valid_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `maximum_rate_valid_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `precipitation_activation_energy_J_mol` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | J/mol |
| `precipitation_order` | 예 | `{"exclusiveMinimum": 0, "maximum": 8.0, "type": "number"}` | 계약·필드 설명 참조 |
| `dissolution_rate_constant_mol_m2_s` | 예 | `{"minimum": 0, "type": "number"}` | mol/(m²·s) |
| `dissolution_activation_energy_J_mol` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | J/mol |
| `dissolution_order` | 예 | `{"exclusiveMinimum": 0, "maximum": 8.0, "type": "number"}` | 계약·필드 설명 참조 |
| `scale_molar_volume_m3_mol` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m³/mol |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/SurfaceScaleKineticInterval"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `interval_constant_saturation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `linearly_varying_saturation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `interval_temperature_profile_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `arrhenius_temperature_scaling_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `supersaturation_kinetics_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `precipitation_and_dissolution_coefficients_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scale_phase_identity_and_molar_volume_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_uniform_scale_layer_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CallerSurfaceScaleKinetics.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `rate_reference_temperature_K` | `K` |
| `minimum_rate_valid_temperature_K` | `K` |
| `maximum_rate_valid_temperature_K` | `K` |
| `initial_scale_thickness_m` | `m` |
| `precipitation_rate_constant_mol_m2_s` | `mol/m2/s` |
| `effective_precipitation_rate_constant_at_temperature_mol_m2_s` | `mol/m2/s` |
| `precipitation_activation_energy_J_mol` | `J/mol` |
| `dissolution_rate_constant_mol_m2_s` | `mol/m2/s` |
| `effective_dissolution_rate_constant_at_temperature_mol_m2_s` | `mol/m2/s` |
| `dissolution_activation_energy_J_mol` | `J/mol` |
| `final_scale_thickness_m` | `m` |
| `scale_history[].time_s` | `s` |
| `scale_history[].saturation_ratio` | `1` |
| `scale_history[].precipitation_flux_mol_m2_s` | `mol/m2/s` |
| `scale_history[].dissolution_flux_mol_m2_s` | `mol/m2/s` |
| `scale_history[].precipitated_mol_m2` | `mol/m2` |
| `scale_history[].dissolved_mol_m2` | `mol/m2` |
| `scale_history[].scale_thickness_m` | `m` |
| `scale_history[].cumulative_precipitated_mol_m2` | `mol/m2` |
| `scale_history[].cumulative_dissolved_mol_m2` | `mol/m2` |
| `cumulative_precipitated_mol_m2` | `mol/m2` |
| `cumulative_dissolved_mol_m2` | `mol/m2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Integrate caller-calibrated single-phase precipitation and dissolution flux laws over constant or explicitly reviewed linear saturation intervals, with inventory-bounded dissolution.
- Caller supplies phase identity, condition-specific rate constants, reaction orders, molar volume and saturation history; linear positive-part power exposure is integrated analytically, and optional Arrhenius scaling is bounded by explicit temperature support and review. The uniform-layer thickness is descriptive and confers no protective credit.

## 구현 근거·독립 설명

- `caller_surface_scale_kinetic_balance`: Integrate caller-calibrated precipitation and dissolution molar flux laws for one identified scale phase over ordered intervals with either constant saturation or explicitly reviewed linear saturation endpoints. Analytically integrate positive-part power laws max(Ω−1,0)^n and max(1−Ω,0)^n across the threshold Ω=1. Bound dissolution by the existing uniform scale inventory; for a descending supersaturated-to-undersaturated interval, generated precipitate may dissolve after the crossing, whereas an ascending path cannot spend future precipitation. Convert cumulative net molar amount per area to thickness using caller molar volume. Optionally scale both rate constants from a reference temperature with separate activation energies inside explicitly reviewed absolute-temperature support. Preserve physical scope, specimen/source/condition/provider/configuration digests and every interval balance. Do not solve saturation chemistry, phase competition, nucleation, morphology, transport, scale protection, corrosion rate, life or acceptance.
- `arrhenius_kinetics`: Rate ratio for a single supplied activation energy between two absolute temperatures.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.caller_surface_scale_kinetics"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.caller_surface_scale_kinetics"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.caller_surface_scale_kinetics.v1",
  "assessment_id": "synthetic-single-scale-history",
  "physical_scope_id": "synthetic-surface-coupon",
  "substrate_condition_id": "synthetic-steel-condition",
  "solution_condition_id": "synthetic-aqueous-condition",
  "scale_phase_id": "synthetic-scale-phase",
  "physical_specimen_id": "synthetic-no-test-specimen",
  "source_group_id": "synthetic-example-only",
  "provider_id": "example://caller-kinetic-constants",
  "provider_revision": "synthetic-1",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "condition_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "kinetic_configuration_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "temperature_K": 298.15,
  "initial_scale_thickness_m": 1e-08,
  "precipitation_rate_constant_mol_m2_s": 1e-06,
  "rate_reference_temperature_K": 298.15,
  "minimum_rate_valid_temperature_K": 273.15,
  "maximum_rate_valid_temperature_K": 373.15,
  "precipitation_activation_energy_J_mol": 20000.0,
  "precipitation_order": 1.0,
  "dissolution_rate_constant_mol_m2_s": 5e-07,
  "dissolution_activation_energy_J_mol": 18000.0,
  "dissolution_order": 1.0,
  "scale_molar_volume_m3_mol": 2e-05,
  "intervals": [
    {
      "interval_id": "supersaturated-hold",
      "start_time_s": 0.0,
      "end_time_s": 3600.0,
      "saturation_ratio": 1.3
    },
    {
      "interval_id": "undersaturated-hold",
      "start_time_s": 3600.0,
      "end_time_s": 7200.0,
      "saturation_ratio": 0.8
    }
  ],
  "interval_constant_saturation_reviewed": true,
  "arrhenius_temperature_scaling_reviewed": true,
  "supersaturation_kinetics_and_standard_state_reviewed": true,
  "precipitation_and_dissolution_coefficients_reviewed": true,
  "scale_phase_identity_and_molar_volume_reviewed": true,
  "single_uniform_scale_layer_scope_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-scale-kinetics-fixture",
      "origin": "synthetic",
      "citation": "Project-authored phase-specific kinetic integration example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/surface_scale_kinetics.py#L175)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
