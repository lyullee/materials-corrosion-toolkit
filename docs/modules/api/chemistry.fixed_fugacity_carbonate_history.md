# `chemistry.fixed_fugacity_carbonate_history`

**목적:** Solves each caller-supplied fixed-fugacity carbonate/alkalinity state at one exact ordered time point; no interpolation or kinetics are added.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.fixed_fugacity_carbonate_history.v1", "default": "matintegrity.fixed_fugacity_carbonate_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | s |
| `equilibria` | 예 | `{"items": {"$ref": "#/$defs/FixedFugacityCarbonateEquilibrium"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `history_clock_and_sample_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_point_evaluations` | 아니오 | `{"default": 20000, "maximum": 20000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FixedFugacityCarbonateHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `time_basis` | `1` |
| `time_s[]` | `s` |
| `temperature_K_history[]` | `K` |
| `co2_fugacity_Pa_history[]` | `Pa` |
| `ph_activity_history[]` | `1` |
| `co2star_mol_L_history[]` | `mol/L` |
| `hco3_mol_L_history[]` | `mol/L` |
| `co3_mol_L_history[]` | `mol/L` |
| `calculated_total_alkalinity_mol_L_history[]` | `mol/L` |
| `alkalinity_closure_residual_mol_L_history[]` | `mol/L` |
| `point_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Solves each caller-supplied fixed-fugacity carbonate/alkalinity state at one exact ordered time point; no interpolation or kinetics are added.
- Each point retains independent gas, Henry, solvent, activity-constant and alkalinity lineage; the first failed point stops evaluation and preserves the computed prefix.
- The history does not close a finite gas inventory, discover species/phases, predict corrosion, scale, life, failure probability or acceptance.

## 구현 근거·독립 설명

- [USGS PHREEQC 3 documentation: gas-phase Henry solubility and fixed-pressure/fixed-volume boundaries](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-17.htm) · `usgs_phreeqc_gas_liquid_equilibrium`
- [USGS advanced carbonate and bicarbonate speciation method](https://water.usgs.gov/water-resources/memos/memo.php?id=2098) · `usgs_advanced_carbonate_speciation`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.fixed_fugacity_carbonate_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.fixed_fugacity_carbonate_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-fixed-fugacity-carbonate-history",
  "asset_id": "synthetic-loop",
  "location_id": "test-sample-port",
  "physical_scope_id": "synthetic-sample-volume-history",
  "time_basis": "elapsed_seconds_from_declared_origin",
  "time_s": [
    0.0,
    60.0
  ],
  "equilibria": [
    {
      "assessment_id": "synthetic-co2-history-point-01",
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
      "measured_total_alkalinity_mol_L": 0.102,
      "alkalinity_provider_id": "synthetic-alkalinity-provider",
      "alkalinity_provider_revision": "fixture-1",
      "alkalinity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "alkalinity_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "alkalinity_record_review_id": "synthetic-alkalinity-review-01",
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
    {
      "assessment_id": "synthetic-co2-history-point-02",
      "asset_id": "synthetic-loop",
      "location_id": "test-sample-port",
      "sample_id": "sample-02",
      "temperature_K": 298.15,
      "co2_fugacity_Pa": 90000.0,
      "gas_fugacity_provider_id": "synthetic-gas-provider",
      "gas_fugacity_provider_revision": "fixture-1",
      "gas_fugacity_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "gas_fugacity_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
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
      "measured_total_alkalinity_mol_L": 0.09,
      "alkalinity_provider_id": "synthetic-alkalinity-provider",
      "alkalinity_provider_revision": "fixture-1",
      "alkalinity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "alkalinity_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "alkalinity_record_review_id": "synthetic-alkalinity-review-01",
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
  ],
  "history_clock_and_sample_alignment_reviewed": true,
  "maximum_point_evaluations": 100
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/co2_fixed_fugacity_equilibrium.py#L397)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
