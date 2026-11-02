# `chemistry.fixed_fugacity_carbonate_scenario_ensemble`

**목적:** Each row is a complete reviewed fixed-fugacity carbonate-equilibrium case with common sample identity and caller-normalized weights.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `ensemble_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sample_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_interval_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios` | 예 | `{"items": {"$ref": "#/$defs/FixedFugacityCarbonateScenario"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `scenario_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_sample_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `weight_meaning` | 예 | `{"enum": ["caller_scenario_mass_not_event_probability", "caller_distribution_weights_model_implied_uncertainty"], "type": "string"}` | 계약·필드 설명 참조 |
| `input_distribution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `input_distribution_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FixedFugacityCarbonateEnsemble.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `ensemble_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `sample_id` | `1` |
| `exposure_interval_id` | `1` |
| `source_group_id` | `1` |
| `input_distribution_id` | `1` |
| `input_distribution_digest` | `1` |
| `weight_meaning` | `1` |
| `scenario_count` | `1` |
| `aggregate_returned` | `1` |
| `summaries` | `mixed` |
| `scenario_results` | `mixed` |
| `event_probability_inferred` | `1` |
| `corrosion_rate_inferred` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each row is a complete reviewed fixed-fugacity carbonate-equilibrium case with common sample identity and caller-normalized weights.
- All rows must compute before weighted summaries are returned; summaries are descriptive and do not infer probability or corrosion rate.

## 구현 근거·독립 설명

- `caller_weighted_fixed_fugacity_carbonate_equilibrium_scenarios`: Propagate caller-supplied complete fixed-fugacity carbonate-equilibrium cases for one sample and exposure scope with normalized weights. Preserve each case and provider digest, fail aggregation if any scenario is unresolved, and report only descriptive weighted state summaries. Weights do not represent failure probability, event frequency or corrosion-rate distribution.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.fixed_fugacity_carbonate_scenario_ensemble"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.fixed_fugacity_carbonate_scenario_ensemble"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "ensemble_id": "synthetic-co2-ensemble-01",
  "asset_id": "synthetic-loop",
  "location_id": "test-sample-port",
  "physical_scope_id": "sample-volume-01",
  "sample_id": "sample-01",
  "exposure_interval_id": "hold-01",
  "source_group_id": "synthetic-study-01",
  "scenarios": [
    {
      "scenario_id": "alkalinity-low",
      "normalized_weight": 0.25,
      "equilibrium": {
        "assessment_id": "synthetic-co2-ensemble-low",
        "asset_id": "synthetic-loop",
        "location_id": "test-sample-port",
        "sample_id": "sample-01",
        "temperature_K": 298.15,
        "co2_fugacity_Pa": 100000.0,
        "gas_fugacity_provider_id": "synthetic-gas-provider",
        "gas_fugacity_provider_revision": "fixture-1",
        "gas_fugacity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "gas_fugacity_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "sample_solvent_composition_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "henry": {
          "temperature_K": 298.15,
          "coefficient_mol_L_Pa": 1e-07,
          "convention": "aqueous_CO2star_concentration_over_gas_fugacity",
          "solvent_composition_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "provider_id": "synthetic-henry-provider",
          "provider_revision": "fixture-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "evidence": [
            {
              "source_id": "synthetic-carbonate-fixture",
              "origin": "synthetic",
              "citation": "Synthetic closed-form values for API demonstration",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        "constants": {
          "activity_standard_state": "molarity_1_mol_L",
          "temperature_K": 298.15,
          "K1_activity": 1e-06,
          "K2_activity": 1e-09,
          "Kw_activity": 1e-14,
          "gamma_h_plus": 1.0,
          "gamma_hco3_minus": 1.0,
          "gamma_co3_double_minus": 1.0,
          "gamma_oh_minus": 1.0,
          "constants_provider_id": "synthetic-equilibrium-provider",
          "constants_provider_revision": "fixture-1",
          "constants_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "constants_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "evidence": [
            {
              "source_id": "synthetic-carbonate-fixture",
              "origin": "synthetic",
              "citation": "Synthetic closed-form values for API demonstration",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        "measured_total_alkalinity_mol_L": 0.101,
        "alkalinity_provider_id": "synthetic-alkalinity-provider",
        "alkalinity_provider_revision": "fixture-1",
        "alkalinity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "alkalinity_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "expanded_total_alkalinity_uncertainty_mol_L": 0.001,
        "alkalinity_uncertainty_basis": "synthetic expanded uncertainty with caller-declared coverage convention",
        "ph_search_lower": 4.0,
        "ph_search_upper": 10.0,
        "ph_tolerance": 1e-10,
        "alkalinity_closure_tolerance_mol_L": 1e-12,
        "temperature_match_tolerance_K": 0.0,
        "maximum_iterations": 256,
        "carbonate_only_alkalinity_reviewed": true,
        "gas_fugacity_reviewed": true,
        "fixed_fugacity_reservoir_reviewed": true,
        "henry_convention_reviewed": true,
        "solvent_composition_match_reviewed": true,
        "activity_scales_reviewed": true,
        "constants_temperature_basis_reviewed": true,
        "alkalinity_measurement_reviewed": true,
        "gas_equilibrium_review_id": "synthetic-gas-review-01",
        "henry_record_review_id": "synthetic-henry-review-01",
        "alkalinity_record_review_id": "synthetic-alkalinity-review-low",
        "evidence": [
          {
            "source_id": "synthetic-carbonate-fixture",
            "origin": "synthetic",
            "citation": "Synthetic closed-form values for API demonstration",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    },
    {
      "scenario_id": "alkalinity-high",
      "normalized_weight": 0.75,
      "equilibrium": {
        "assessment_id": "synthetic-co2-ensemble-high",
        "asset_id": "synthetic-loop",
        "location_id": "test-sample-port",
        "sample_id": "sample-01",
        "temperature_K": 298.15,
        "co2_fugacity_Pa": 100000.0,
        "gas_fugacity_provider_id": "synthetic-gas-provider",
        "gas_fugacity_provider_revision": "fixture-1",
        "gas_fugacity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "gas_fugacity_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "sample_solvent_composition_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "henry": {
          "temperature_K": 298.15,
          "coefficient_mol_L_Pa": 1e-07,
          "convention": "aqueous_CO2star_concentration_over_gas_fugacity",
          "solvent_composition_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "provider_id": "synthetic-henry-provider",
          "provider_revision": "fixture-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "evidence": [
            {
              "source_id": "synthetic-carbonate-fixture",
              "origin": "synthetic",
              "citation": "Synthetic closed-form values for API demonstration",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        "constants": {
          "activity_standard_state": "molarity_1_mol_L",
          "temperature_K": 298.15,
          "K1_activity": 1e-06,
          "K2_activity": 1e-09,
          "Kw_activity": 1e-14,
          "gamma_h_plus": 1.0,
          "gamma_hco3_minus": 1.0,
          "gamma_co3_double_minus": 1.0,
          "gamma_oh_minus": 1.0,
          "constants_provider_id": "synthetic-equilibrium-provider",
          "constants_provider_revision": "fixture-1",
          "constants_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "constants_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "evidence": [
            {
              "source_id": "synthetic-carbonate-fixture",
              "origin": "synthetic",
              "citation": "Synthetic closed-form values for API demonstration",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        "measured_total_alkalinity_mol_L": 0.103,
        "alkalinity_provider_id": "synthetic-alkalinity-provider",
        "alkalinity_provider_revision": "fixture-1",
        "alkalinity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "alkalinity_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "expanded_total_alkalinity_uncertainty_mol_L": 0.001,
        "alkalinity_uncertainty_basis": "synthetic expanded uncertainty with caller-declared coverage convention",
        "ph_search_lower": 4.0,
        "ph_search_upper": 10.0,
        "ph_tolerance": 1e-10,
        "alkalinity_closure_tolerance_mol_L": 1e-12,
        "temperature_match_tolerance_K": 0.0,
        "maximum_iterations": 256,
        "carbonate_only_alkalinity_reviewed": true,
        "gas_fugacity_reviewed": true,
        "fixed_fugacity_reservoir_reviewed": true,
        "henry_convention_reviewed": true,
        "solvent_composition_match_reviewed": true,
        "activity_scales_reviewed": true,
        "constants_temperature_basis_reviewed": true,
        "alkalinity_measurement_reviewed": true,
        "gas_equilibrium_review_id": "synthetic-gas-review-01",
        "henry_record_review_id": "synthetic-henry-review-01",
        "alkalinity_record_review_id": "synthetic-alkalinity-review-high",
        "evidence": [
          {
            "source_id": "synthetic-carbonate-fixture",
            "origin": "synthetic",
            "citation": "Synthetic closed-form values for API demonstration",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    }
  ],
  "scenario_weights_reviewed": true,
  "common_sample_scope_reviewed": true,
  "weight_meaning": "caller_distribution_weights_model_implied_uncertainty",
  "input_distribution_id": "synthetic-two-point-alkalinity-draw",
  "input_distribution_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "Synthetic two-scenario input fixture",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/co2_fixed_fugacity_equilibrium.py#L478)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
