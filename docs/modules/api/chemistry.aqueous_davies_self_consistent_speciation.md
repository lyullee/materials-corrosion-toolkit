# `chemistry.aqueous_davies_self_consistent_speciation`

**목적:** Caller-defined square aqueous equilibrium/constraint system is solved repeatedly while Davies coefficients are recalculated from speciation-derived molal ionic strength.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_davies_iteration.v1", "default": "matintegrity.aqueous_davies_iteration.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `system` | 예 | `{"$ref": "#/$defs/AqueousMassActionSystem"}` | 계약·필드 설명 참조 |
| `water_mass_per_solution_volume_kg_L` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `davies_A_at_temperature` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `davies_A_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `davies_A_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `davies_A_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `davies_A_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `ionic_strength_limit_mol_kg` | 예 | `{"exclusiveMinimum": 0, "maximum": 0.5, "type": "number"}` | mol/kg |
| `charge_balance_tolerance_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `maximum_outer_iterations` | 아니오 | `{"default": 100, "maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `log_gamma_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `damping_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `water_mass_conversion_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `Davies_A_temperature_solvent_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `molarity_to_molality_standard_state_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_inventory_and_charge_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_point_solver_settings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_liquid_no_precipitation_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousDaviesIteration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `ionic_strength_mol_kg` | `mol/kg` |
| `charge_balance_residual_mol_kg` | `mol/kg` |
| `species.activity_coefficient` | `1` |
| `species.davies_target_molality_activity_coefficient` | `1` |
| `species.davies_target_molarity_activity_coefficient` | `1` |
| `species.dimensionless_activity` | `1` |
| `species.concentration_mol_L` | `mol/L` |
| `species.molality_mol_kg` | `mol/kg` |
| `species.ionic_strength_contribution_mol_kg` | `mol/kg` |
| `species.activity_coefficient_fixed_point_residual_ln` | `1` |
| `maximum_log_gamma_fixed_point_residual` | `1` |
| `inner_normalized_residual_norm` | `1` |
| `outer_iterations` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-defined square aqueous equilibrium/constraint system is solved repeatedly while Davies coefficients are recalculated from speciation-derived molal ionic strength.
- Requires caller water-mass-per-solution-volume conversion, temperature-specific Davies A, charge tolerance and explicit single-liquid applicability; ionic strength is limited to the declared ceiling no greater than 0.5 mol/kg.
- The mass-action solver uses the molarity standard state; Davies molality gamma is mapped by gamma_c=gamma_m/w and both values are reported.
- No species, reactions, charge constraints, gas/solid phases, kinetic scale, salting-out, corrosion rate or acceptance are inferred.

## 구현 근거·독립 설명

- `caller_general_aqueous_mass_action_speciation`: Solve a caller-defined square single-phase aqueous network in natural-log dimensionless activities. Use caller-supplied fixed activity coefficients and temperature-matched log10 equilibrium constants; solve caller-provided linear species amount and/or charge constraints after normalization by declared positive scales. A damped Newton method with finite-range checks and line search returns species activities, concentrations, balance closure, reaction residuals and full input/provider digests only within the declared tolerance. At a computed root, solve the converged Jacobian for implicit local derivatives of log activities and concentrations with respect to each log10(K), constraint target and fixed ln(gamma), without finite differencing. If explicitly reviewed, propagate a finite symmetric positive-semidefinite caller parameter covariance through those derivatives using first-order JΣJᵀ; condition and finite checks can make sensitivities unavailable while preserving the equilibrium result. No automatic electroneutrality, ionic-strength iteration, water balance, gas/solid phase, precipitation, kinetics, corrosion, or acceptance is inferred.
- [USGS PHREEQC 3 documentation: Davies activity-coefficient model](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm) · `usgs_phreeqc_davies_activity_coefficients`
- [USGS WSP 2254: Davies approximation for aqueous activity coefficients](https://pubs.usgs.gov/wsp/wsp2254/pdf/wsp2254a.pdf) · `usgs_davies_ionic_strength_approximation`
- `molality_to_molarity_activity_standard_state_bridge`: Map a molality-standard-state coefficient to a molarity-standard-state coefficient by equating the same dimensionless activity: gamma_c*c/(1 mol/L) = gamma_m*m/(1 mol/kg-water), with m=c/w and caller-supplied w in kg-water/L-solution, giving gamma_c=gamma_m/w. Require review of the water-mass conversion and standard-state mapping, preserve both coefficients, and fail closed outside finite numeric range. This algebraic basis does not infer solution water content or validate an activity model.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_davies_self_consistent_speciation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_davies_self_consistent_speciation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.aqueous_davies_iteration.v1",
  "system": {
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
  },
  "water_mass_per_solution_volume_kg_L": 0.997,
  "davies_A_at_temperature": 0.5,
  "davies_A_provider_id": "synthetic-temperature-solvent-activity-record",
  "davies_A_provider_revision": "example-only-1",
  "davies_A_configuration_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "davies_A_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "ionic_strength_limit_mol_kg": 0.5,
  "charge_balance_tolerance_mol_kg": 1e-08,
  "maximum_outer_iterations": 100,
  "log_gamma_tolerance": 1e-08,
  "damping_fraction": 0.5,
  "water_mass_conversion_reviewed": true,
  "Davies_A_temperature_solvent_basis_reviewed": true,
  "molarity_to_molality_standard_state_mapping_reviewed": true,
  "complete_inventory_and_charge_scope_reviewed": true,
  "fixed_point_solver_settings_reviewed": true,
  "single_liquid_no_precipitation_scope_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic-mass-action-fixture",
      "origin": "synthetic",
      "citation": "Project-authored fixed-point coupling example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_activity_iteration.py#L200)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
