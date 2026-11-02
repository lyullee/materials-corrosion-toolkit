# `chemistry.caller_scale_coverage_kinetics`

**목적:** A caller-supplied first-order surface-coverage attachment/detachment law uses a closed-form solution for constant saturation and adaptive RK4 step doubling for reviewed piecewise-linear saturation paths.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.caller_scale_coverage_kinetics.v1", "default": "matintegrity.caller_scale_coverage_kinetics.v1", "type": "string"}` | 계약·필드 설명 참조 |
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
| `initial_covered_area_fraction` | 예 | `{"maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `attachment_rate_constant_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `rate_reference_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `minimum_rate_valid_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `maximum_rate_valid_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `attachment_activation_energy_J_mol` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | J/mol |
| `attachment_supersaturation_order` | 예 | `{"exclusiveMinimum": 0, "maximum": 8.0, "type": "number"}` | 계약·필드 설명 참조 |
| `detachment_rate_constant_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `detachment_activation_energy_J_mol` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | J/mol |
| `arrhenius_temperature_scaling_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `detachment_undersaturation_order` | 예 | `{"exclusiveMinimum": 0, "maximum": 8.0, "type": "number"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/ScaleCoverageKineticInterval"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `interval_constant_saturation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `linearly_varying_saturation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `interval_temperature_profile_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_time_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `minimum_time_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `coverage_absolute_tolerance` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `coverage_relative_tolerance` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `inventory_absolute_tolerance` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `inventory_relative_tolerance` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `maximum_rate_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_rejected_steps_per_interval` | 아니오 | `{"default": 1000, "maximum": 100000, "minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `coverage_kinetic_law_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_coefficients_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scale_phase_identity_and_specimen_match_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `area_average_coverage_representation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CallerScaleCoverageKinetics.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `scale_history[].temperature_K` | `K` |
| `scale_history[].attachment_rate_constant_s` | `1/s` |
| `scale_history[].detachment_rate_constant_s` | `1/s` |
| `attachment_rate_constant_s` | `1/s` |
| `effective_attachment_rate_constant_at_temperature_s` | `1/s` |
| `rate_reference_temperature_K` | `K` |
| `minimum_rate_valid_temperature_K` | `K` |
| `maximum_rate_valid_temperature_K` | `K` |
| `attachment_activation_energy_J_mol` | `J/mol` |
| `detachment_rate_constant_s` | `1/s` |
| `effective_detachment_rate_constant_at_temperature_s` | `1/s` |
| `detachment_activation_energy_J_mol` | `J/mol` |
| `intervals[].start_time_s` | `s` |
| `intervals[].end_time_s` | `s` |
| `intervals[].saturation_ratio` | `1` |
| `intervals[].saturation_ratio_end` | `1` |
| `maximum_time_step_s` | `s` |
| `minimum_time_step_s` | `s` |
| `coverage_absolute_tolerance` | `1` |
| `coverage_relative_tolerance` | `1` |
| `inventory_absolute_tolerance` | `1` |
| `inventory_relative_tolerance` | `1` |
| `initial_covered_area_fraction` | `1` |
| `final_covered_area_fraction` | `1` |
| `maximum_absolute_coverage_balance_residual` | `1` |
| `cumulative_coverage_balance_residual` | `1` |
| `scale_history[].time_s` | `s` |
| `scale_history[].saturation_ratio_for_next_interval` | `1` |
| `scale_history[].saturation_ratio_end_for_next_interval` | `1` |
| `scale_history[].saturation_ratio` | `1` |
| `scale_history[].saturation_ratio_end` | `1` |
| `scale_history[].attachment_rate_s` | `1/s` |
| `scale_history[].detachment_rate_s` | `1/s` |
| `scale_history[].covered_area_fraction` | `1` |
| `scale_history[].cumulative_attachment_exposure` | `1` |
| `scale_history[].cumulative_detachment_exposure` | `1` |
| `scale_history[].interval_coverage_balance_residual` | `1` |
| `scale_history[].adaptive_accepted_steps` | `1` |
| `scale_history[].adaptive_rejected_steps` | `1` |
| `adaptive_maximum_error_ratio` | `1` |
| `adaptive_rate_evaluation_count` | `1` |
| `maximum_rate_evaluations` | `1` |
| `adaptive_accepted_steps` | `1` |
| `adaptive_rejected_steps` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A caller-supplied first-order surface-coverage attachment/detachment law uses a closed-form solution for constant saturation and adaptive RK4 step doubling for reviewed piecewise-linear saturation paths.
- Optional caller-supplied Arrhenius activation energies scale both reference rate constants only inside the declared absolute-temperature support. The output is an area-average coverage variable; rate-law calibration, morphology and any protective effect remain caller-owned.

## 구현 근거·독립 설명

- `caller_scale_coverage_attachment_detachment_law`: For one caller-identified scale phase, integrate the first-order area-average coverage balance d(theta)/dt = a(1-theta)-b*theta with caller-selected attachment and detachment power laws. Use a closed-form update for interval-constant saturation; for caller-reviewed piecewise-linear saturation use bounded adaptive RK4 step doubling on coverage and separate attachment/detachment inventories with caller absolute/relative tolerances. Optionally scale both caller rate constants from a reference temperature with separate supplied activation energies using the Arrhenius relation, only when target/reference and every declared piecewise-constant interval temperature lie inside the absolute-temperature support and explicit applicability review is present. Interval temperatures require complete per-interval values and an explicit profile review; no temperature interpolation occurs between intervals. Record effective temperature-specific rates, inventory closure and integration diagnostics. No nucleation, morphology, porosity, adhesion, transport protection or corrosion law is inferred.
- `arrhenius_kinetics`: Rate ratio for a single supplied activation energy between two absolute temperatures.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.caller_scale_coverage_kinetics"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.caller_scale_coverage_kinetics"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-scale-coverage",
  "physical_scope_id": "synthetic-coupon-surface",
  "substrate_condition_id": "synthetic-substrate-condition",
  "solution_condition_id": "synthetic-solution-condition",
  "scale_phase_id": "synthetic-scale-phase",
  "physical_specimen_id": "synthetic-coupon-01",
  "source_group_id": "synthetic-coverage-series",
  "provider_id": "synthetic-provider",
  "provider_revision": "1",
  "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "condition_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
  "kinetic_configuration_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
  "temperature_K": 298.15,
  "initial_covered_area_fraction": 0.1,
  "attachment_rate_constant_s": 0.002,
  "rate_reference_temperature_K": 298.15,
  "minimum_rate_valid_temperature_K": 273.15,
  "maximum_rate_valid_temperature_K": 373.15,
  "attachment_activation_energy_J_mol": 20000.0,
  "attachment_supersaturation_order": 1.0,
  "detachment_rate_constant_s": 0.001,
  "detachment_activation_energy_J_mol": 18000.0,
  "detachment_undersaturation_order": 1.0,
  "intervals": [
    {
      "interval_id": "synthetic-growth",
      "start_time_s": 0.0,
      "end_time_s": 50.0,
      "saturation_ratio": 1.5
    },
    {
      "interval_id": "synthetic-transition",
      "start_time_s": 50.0,
      "end_time_s": 100.0,
      "saturation_ratio": 1.5,
      "saturation_ratio_end": 0.5
    },
    {
      "interval_id": "synthetic-dissolution",
      "start_time_s": 100.0,
      "end_time_s": 200.0,
      "saturation_ratio": 0.5
    }
  ],
  "interval_constant_saturation_reviewed": true,
  "linearly_varying_saturation_reviewed": true,
  "arrhenius_temperature_scaling_reviewed": true,
  "maximum_time_step_s": 10.0,
  "minimum_time_step_s": 0.0001,
  "coverage_absolute_tolerance": 1e-09,
  "coverage_relative_tolerance": 1e-07,
  "inventory_absolute_tolerance": 1e-09,
  "inventory_relative_tolerance": 1e-07,
  "maximum_rate_evaluations": 200000,
  "maximum_rejected_steps_per_interval": 100,
  "coverage_kinetic_law_and_standard_state_reviewed": true,
  "rate_coefficients_and_temperature_reviewed": true,
  "scale_phase_identity_and_specimen_match_reviewed": true,
  "area_average_coverage_representation_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "caller_scale_coverage_attachment_detachment_law",
      "origin": "synthetic",
      "citation": "Synthetic API illustration only; no empirical scale behavior is claimed."
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/scale_coverage_kinetics.py#L172)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
