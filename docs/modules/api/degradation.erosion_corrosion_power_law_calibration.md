# `degradation.erosion_corrosion_power_law_calibration`

**목적:** Log measured loss rate is linear in log velocity and log particle concentration in one reviewed regime.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `mechanism_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `regression_form` | 예 | `{"const": "log_loss_rate_intercept_plus_log_velocity_plus_log_particle_concentration", "type": "string"}` | 계약·필드 설명 참조 |
| `velocity_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `particle_concentration_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `loss_rate_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_velocity_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reference_particle_concentration_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ErosionCorrosionPowerLawObservation"}, "minItems": 8, "type": "array"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_dataset_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `holdout_dataset_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_calibration_record_count` | 예 | `{"minimum": 6, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_record_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `material_fluid_geometry_and_mechanism_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `velocity_particle_and_loss_rate_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `weights_and_positive_measurements_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_support_hull_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `regression_form_and_minimum_counts_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_power_law_regime_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ErosionCorrosionPowerLawCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `physical_scope_id` | `1` |
| `reference_velocity_value` | `velocity unit` |
| `reference_particle_concentration_value` | `particle-concentration unit` |
| `log_reference_loss_rate` | `ln(loss-rate unit)` |
| `velocity_exponent` | `1` |
| `particle_concentration_exponent` | `1` |
| `log_loss_rate_sigma` | `1` |
| `calibration_velocity_range` | `velocity unit` |
| `calibration_particle_concentration_range` | `particle-concentration unit` |
| `outside_support_holdout_ids` | `1` |
| `holdout_rows` | `mixed` |
| `holdout_weighted_log_bias` | `1` |
| `holdout_weighted_log_rmse` | `1` |
| `holdout_weighted_mean_negative_log_likelihood_loss_rate` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Log measured loss rate is linear in log velocity and log particle concentration in one reviewed regime.
- Calibration and holdout specimen, source and independence groups are disjoint.
- Units and material, fluid, geometry and mechanism-scope identities are exact caller tokens.

## 구현 근거·독립 설명

- `authored_weighted_erosion_corrosion_power_law_calibration`: Fit a positive combined measured loss rate as a weighted log-linear power law in velocity and particle concentration for one reviewed material, fluid, geometry and mechanism regime. Preserve provider digests and disjoint partitions; evaluate holdout only inside the two-dimensional calibration hull without separating erosion from corrosion, changing regimes, forecasting service loss, or inferring acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.erosion_corrosion_power_law_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.erosion_corrosion_power_law_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "calibration-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "material_condition_id": "material-1",
  "fluid_condition_id": "fluid-1",
  "geometry_condition_id": "geometry-1",
  "mechanism_scope_id": "combined-loss-regime-1",
  "regression_form": "log_loss_rate_intercept_plus_log_velocity_plus_log_particle_concentration",
  "velocity_unit_token": "m/s",
  "particle_concentration_unit_token": "kg/m^3",
  "loss_rate_unit_token": "m/s",
  "reference_velocity_value": 2,
  "reference_particle_concentration_value": 0.3,
  "observations": [
    {
      "observation_id": "cal-1",
      "physical_specimen_id": "specimen-cal-1",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-cal-1",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 1,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.1,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 8.326848466051857e-07,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-2",
      "physical_specimen_id": "specimen-cal-2",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-cal-2",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 1,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.5,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 3.4710262035716957e-06,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-3",
      "physical_specimen_id": "specimen-cal-3",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-cal-3",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 3,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.1,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 4.503335701583079e-06,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-4",
      "physical_specimen_id": "specimen-cal-4",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-cal-4",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 3,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.5,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 1.858525861932438e-05,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-5",
      "physical_specimen_id": "specimen-cal-5",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-cal-5",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 1,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.1,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 9.295078338687774e-07,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-6",
      "physical_specimen_id": "specimen-cal-6",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-cal-6",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 1,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.5,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 3.1094637576682376e-06,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-7",
      "physical_specimen_id": "specimen-cal-7",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-cal-7",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 3,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.1,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 4.878405326923877e-06,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-8",
      "physical_specimen_id": "specimen-cal-8",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-cal-8",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 3,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.5,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 1.6649309084504812e-05,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "hold-1",
      "physical_specimen_id": "specimen-hold-1",
      "source_group_id": "hold-source",
      "independence_group_id": "independence-hold-1",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 1.5,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.2,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 2.9435471355668356e-06,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "hold-2",
      "physical_specimen_id": "specimen-hold-2",
      "source_group_id": "hold-source",
      "independence_group_id": "independence-hold-2",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "fluid_condition_id": "fluid-1",
      "geometry_condition_id": "geometry-1",
      "mechanism_scope_id": "combined-loss-regime-1",
      "velocity_value": 2.5,
      "velocity_unit_token": "m/s",
      "particle_concentration_value": 0.4,
      "particle_concentration_unit_token": "kg/m^3",
      "measured_loss_rate_value": 1.048946628750523e-05,
      "loss_rate_unit_token": "m/s",
      "nominal_weight": 1,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "provider_id": "provider-1",
  "provider_revision": "1",
  "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "calibration_dataset_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "holdout_dataset_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "minimum_calibration_record_count": 8,
  "minimum_holdout_record_count": 2,
  "material_fluid_geometry_and_mechanism_scope_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "velocity_particle_and_loss_rate_units_reviewed": true,
  "weights_and_positive_measurements_reviewed": true,
  "calibration_support_hull_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "regression_form_and_minimum_counts_reviewed": true,
  "common_power_law_regime_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/erosion_corrosion_power_law.py#L101)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
