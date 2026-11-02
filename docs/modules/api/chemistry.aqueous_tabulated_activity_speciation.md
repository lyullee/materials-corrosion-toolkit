# `chemistry.aqueous_tabulated_activity_speciation`

**목적:** Caller-defined single-liquid mass-action equations are iterated with species-specific caller activity tables using bounded piecewise-linear interpolation of ln(gamma) in ionic strength and, when supplied, temperature.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_tabulated_activity_iteration.v1", "default": "matintegrity.aqueous_tabulated_activity_iteration.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `system` | 예 | `{"$ref": "#/$defs/AqueousMassActionSystem"}` | 계약·필드 설명 참조 |
| `activity_table_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `water_mass_per_solution_volume_kg_L` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `species_activity_curves` | 예 | `{"items": {"$ref": "#/$defs/AqueousSpeciesActivityCurve"}, "maxItems": 100, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `activity_table_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_table_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_table_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `activity_table_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `interpolation_method` | 아니오 | `{"default": "piecewise_linear", "enum": ["piecewise_linear", "shape_preserving_pchip"], "type": "string"}` | 계약·필드 설명 참조 |
| `interpolation_method_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `ionic_strength_limit_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `charge_balance_tolerance_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `maximum_outer_iterations` | 아니오 | `{"default": 100, "maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `log_gamma_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `damping_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `temperature_solvent_and_table_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `water_mass_conversion_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `table_species_and_standard_state_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_inventory_and_charge_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_point_solver_settings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_liquid_no_precipitation_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_activity_table_points` | 아니오 | `{"default": 250000, "maximum": 10000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousTabulatedActivityIteration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `activity_table_temperature_K` | `K` |
| `ionic_strength_mol_kg` | `mol/kg` |
| `charge_balance_residual_mol_kg` | `mol/kg` |
| `species.activity_coefficient` | `1` |
| `species.dimensionless_activity` | `1` |
| `species.concentration_mol_L` | `mol/L` |
| `species.molality_mol_kg` | `mol/kg` |
| `species.ionic_strength_contribution_mol_kg` | `mol/kg` |
| `species.table_target_activity_coefficient` | `1` |
| `species.activity_coefficient_fixed_point_residual_ln` | `1` |
| `maximum_log_gamma_fixed_point_residual` | `1` |
| `activity_table_point_count` | `1` |
| `maximum_activity_table_points` | `1` |
| `inner_normalized_residual_norm` | `1` |
| `outer_iterations` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-defined single-liquid mass-action equations are iterated with species-specific caller activity tables using bounded piecewise-linear interpolation of ln(gamma) in ionic strength and, when supplied, temperature.
- No extrapolation, table fitting, solvent transfer, alternative phase, precipitation kinetics or model qualification is inferred.

## 구현 근거·독립 설명

- `caller_tabulated_aqueous_activity_coefficients`: Iterate a caller-defined single-liquid mass-action network with species-specific activity-coefficient tables indexed by molal ionic strength. Recalculate ionic strength from caller water-mass conversion and solved concentrations, interpolate ln(gamma) using caller-selected piecewise linear or explicitly reviewed shape-preserving PCHIP only inside each caller table support, and damp updates in log space. Require measured/open dataset knots to map both source_id and source_record_id to declared licensed Evidence. Preserve separate normalized-table, row-lineage, Evidence, provider and configuration digests through speciation and transport callbacks, together with charge/reaction closure, fixed-point history and explicit temperature/solvent/species mapping review. This is a user-supplied table evaluator, not a qualified electrolyte law; no extrapolation, table fitting, phase change, precipitation, scale protection or corrosion rate is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_tabulated_activity_speciation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_tabulated_activity_speciation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.aqueous_tabulated_activity_iteration.v1",
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
    "activity_provider_id": "synthetic-species-gamma-table",
    "activity_provider_revision": "synthetic-table-1",
    "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
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
  "activity_table_temperature_K": 298.15,
  "water_mass_per_solution_volume_kg_L": 0.997,
  "species_activity_curves": [
    {
      "species_id": "h2a",
      "points": [
        {
          "ionic_strength_mol_kg": 0.0,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.1,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.5,
          "activity_coefficient": 1.0
        }
      ]
    },
    {
      "species_id": "ha_minus",
      "points": [
        {
          "ionic_strength_mol_kg": 0.0,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.1,
          "activity_coefficient": 0.82
        },
        {
          "ionic_strength_mol_kg": 0.5,
          "activity_coefficient": 0.76
        }
      ]
    },
    {
      "species_id": "a2_minus",
      "points": [
        {
          "ionic_strength_mol_kg": 0.0,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.1,
          "activity_coefficient": 0.58
        },
        {
          "ionic_strength_mol_kg": 0.5,
          "activity_coefficient": 0.48
        }
      ]
    },
    {
      "species_id": "h_plus",
      "points": [
        {
          "ionic_strength_mol_kg": 0.0,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.1,
          "activity_coefficient": 0.82
        },
        {
          "ionic_strength_mol_kg": 0.5,
          "activity_coefficient": 0.76
        }
      ]
    },
    {
      "species_id": "oh_minus",
      "points": [
        {
          "ionic_strength_mol_kg": 0.0,
          "activity_coefficient": 1.0
        },
        {
          "ionic_strength_mol_kg": 0.1,
          "activity_coefficient": 0.82
        },
        {
          "ionic_strength_mol_kg": 0.5,
          "activity_coefficient": 0.76
        }
      ]
    }
  ],
  "activity_table_provider_id": "synthetic-species-gamma-table",
  "activity_table_provider_revision": "synthetic-table-1",
  "activity_table_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
  "activity_table_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
  "ionic_strength_limit_mol_kg": 0.5,
  "charge_balance_tolerance_mol_kg": 1e-08,
  "maximum_outer_iterations": 100,
  "log_gamma_tolerance": 1e-08,
  "damping_fraction": 0.5,
  "temperature_solvent_and_table_condition_reviewed": true,
  "water_mass_conversion_reviewed": true,
  "table_species_and_standard_state_mapping_reviewed": true,
  "complete_inventory_and_charge_scope_reviewed": true,
  "fixed_point_solver_settings_reviewed": true,
  "single_liquid_no_precipitation_scope_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic-tabulated-activity-fixture",
      "origin": "synthetic",
      "citation": "Project-authored activity-table coupling example; no experimental measurements"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_tabulated_activity.py#L323)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
