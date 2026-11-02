# `chemistry.aqueous_mass_action_speciation`

**목적:** Caller-supplied single-phase aqueous species, fixed activity coefficients, mass-action equilibrium constants, charge-balanced signed reaction stoichiometry, optional complete reviewed elemental formulas, linear analytical/charge constraints and explicit positive initial activities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_mass_action.v1", "default": "matintegrity.aqueous_mass_action.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `activity_standard_state` | 예 | `{"const": "molarity_1_mol_L", "type": "string"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/AqueousActivitySpecies"}, "maxItems": 100, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `reactions` | 예 | `{"items": {"$ref": "#/$defs/AqueousEquilibriumReaction"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `constraints` | 예 | `{"items": {"$ref": "#/$defs/AqueousLinearConstraint"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_iterations` | 아니오 | `{"default": 100, "maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `normalized_residual_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "maximum": 0.0001, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_jacobian_condition_number` | 아니오 | `{"default": 100000000000000.0, "exclusiveMinimum": 0, "maximum": 1e+16, "type": "number"}` | 계약·필드 설명 참조 |
| `local_parameter_covariance` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `local_parameter_covariance_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `activity_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `complete_aqueous_species_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_stoichiometry_and_constant_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `balance_constraints_and_charge_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_activity_coefficients_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_provider_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initial_activity_guess_and_solver_tolerance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_liquid_phase_and_no_precipitation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `elemental_formula_and_reaction_balance_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousMassActionSystem.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `species.dimensionless_activity` | `1` |
| `species.concentration_mol_L` | `mol/L` |
| `constraint_closure.target_mol_L` | `mol/L` |
| `constraint_closure.reconstructed_mol_L` | `mol/L` |
| `constraint_closure.residual_mol_L` | `mol/L` |
| `constraint_closure.normalized_residual` | `1` |
| `reaction_closure.residual_ln` | `1` |
| `reaction_closure.charge_stoichiometric_residual` | `charge-equivalent stoichiometry` |
| `reaction_closure.elemental_stoichiometric_residuals` | `atom stoichiometry` |
| `normalized_residual_norm` | `1` |
| `iterations` | `1` |
| `unknown_count` | `1` |
| `equation_count` | `1` |
| `structural_equation_rank` | `1` |
| `jacobian_rank` | `1` |
| `jacobian_condition_number` | `1` |
| `maximum_jacobian_condition_number` | `1` |
| `initial_normalized_residual_norm` | `1` |
| `final_normalized_residual_norm` | `1` |
| `accepted_steps[].accepted_damping` | `1` |
| `accepted_steps[].residual_norm` | `1` |
| `local_sensitivities.jacobian_condition_number` | `1` |
| `local_sensitivities.species[].d_ln_activity_d_parameter` | `parameter-specific derivative` |
| `local_sensitivities.species[].d_ln_concentration_d_parameter` | `parameter-specific derivative` |
| `local_sensitivities.species[].d_concentration_mol_L_d_parameter` | `mol/L per parameter unit` |
| `local_sensitivity_covariance.ln_activity_covariance` | `1^2` |
| `local_sensitivity_covariance.ln_concentration_covariance` | `1^2` |
| `local_sensitivity_covariance.concentration_covariance_mol2_L2` | `(mol/L)^2` |
| `local_sensitivity_covariance.concentration_standard_deviation_mol_L` | `mol/L` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied single-phase aqueous species, fixed activity coefficients, mass-action equilibrium constants, charge-balanced signed reaction stoichiometry, optional complete reviewed elemental formulas, linear analytical/charge constraints and explicit positive initial activities.
- No ionic strength iteration, gas/solid phase, precipitation, kinetic law or corrosion inference is included.

## 구현 근거·독립 설명

- `caller_general_aqueous_mass_action_speciation`: Solve a caller-defined square single-phase aqueous network in natural-log dimensionless activities. Use caller-supplied fixed activity coefficients and temperature-matched log10 equilibrium constants; solve caller-provided linear species amount and/or charge constraints after normalization by declared positive scales. A damped Newton method with finite-range checks and line search returns species activities, concentrations, balance closure, reaction residuals and full input/provider digests only within the declared tolerance. At a computed root, solve the converged Jacobian for implicit local derivatives of log activities and concentrations with respect to each log10(K), constraint target and fixed ln(gamma), without finite differencing. If explicitly reviewed, propagate a finite symmetric positive-semidefinite caller parameter covariance through those derivatives using first-order JΣJᵀ; condition and finite checks can make sensitivities unavailable while preserving the equilibrium result. No automatic electroneutrality, ionic-strength iteration, water balance, gas/solid phase, precipitation, kinetics, corrosion, or acceptance is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_mass_action_speciation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_mass_action_speciation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.aqueous_mass_action.v1",
  "assessment_id": "synthetic-mass-action-carbonic-acid",
  "solution_id": "synthetic-dilute-acid-solution",
  "temperature_K": 298.15,
  "activity_standard_state": "molarity_1_mol_L",
  "species": [
    {
      "species_id": "h2a",
      "charge_number": 0,
      "activity_coefficient": 1.0,
      "initial_activity": 0.009
    },
    {
      "species_id": "ha_minus",
      "charge_number": -1,
      "activity_coefficient": 0.9,
      "initial_activity": 0.0001
    },
    {
      "species_id": "a2_minus",
      "charge_number": -2,
      "activity_coefficient": 0.5,
      "initial_activity": 1e-08
    },
    {
      "species_id": "h_plus",
      "charge_number": 1,
      "activity_coefficient": 0.9,
      "initial_activity": 0.0001
    },
    {
      "species_id": "oh_minus",
      "charge_number": -1,
      "activity_coefficient": 0.9,
      "initial_activity": 1e-10
    }
  ],
  "reactions": [
    {
      "reaction_id": "dissociation-1",
      "log10_equilibrium_constant": -3.5,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 1.0
        },
        {
          "species_id": "ha_minus",
          "coefficient": 1.0
        },
        {
          "species_id": "h2a",
          "coefficient": -1.0
        }
      ]
    },
    {
      "reaction_id": "dissociation-2",
      "log10_equilibrium_constant": -7.0,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 1.0
        },
        {
          "species_id": "a2_minus",
          "coefficient": 1.0
        },
        {
          "species_id": "ha_minus",
          "coefficient": -1.0
        }
      ]
    },
    {
      "reaction_id": "water-ionization",
      "log10_equilibrium_constant": -14.0,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 1.0
        },
        {
          "species_id": "oh_minus",
          "coefficient": 1.0
        }
      ]
    }
  ],
  "constraints": [
    {
      "constraint_id": "total-dissolved-acid",
      "target_mol_L": 0.01,
      "residual_scale_mol_L": 0.01,
      "terms": [
        {
          "species_id": "h2a",
          "coefficient": 1.0
        },
        {
          "species_id": "ha_minus",
          "coefficient": 1.0
        },
        {
          "species_id": "a2_minus",
          "coefficient": 1.0
        }
      ]
    },
    {
      "constraint_id": "electroneutrality",
      "target_mol_L": 0.0,
      "residual_scale_mol_L": 0.01,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 1.0
        },
        {
          "species_id": "ha_minus",
          "coefficient": -1.0
        },
        {
          "species_id": "a2_minus",
          "coefficient": -2.0
        },
        {
          "species_id": "oh_minus",
          "coefficient": -1.0
        }
      ]
    }
  ],
  "maximum_iterations": 100,
  "normalized_residual_tolerance": 1e-10,
  "activity_provider_id": "synthetic-fixed-gamma-table",
  "activity_provider_revision": "synthetic-1",
  "activity_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "activity_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "equilibrium_provider_id": "synthetic-aqueous-constant-set",
  "equilibrium_provider_revision": "synthetic-1",
  "equilibrium_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "equilibrium_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "complete_aqueous_species_inventory_reviewed": true,
  "reaction_stoichiometry_and_constant_reviewed": true,
  "balance_constraints_and_charge_scope_reviewed": true,
  "fixed_activity_coefficients_and_standard_state_reviewed": true,
  "temperature_and_provider_lineage_reviewed": true,
  "initial_activity_guess_and_solver_tolerance_reviewed": true,
  "single_liquid_phase_and_no_precipitation_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic-mass-action-fixture",
      "origin": "synthetic",
      "citation": "Project-authored acid equilibrium API example"
    }
  ],
  "maximum_jacobian_condition_number": 100000000000000.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_mass_action.py#L736)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
