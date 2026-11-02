# `integration.aqueous_external_activity_speciation_history`

**목적:** Every exact time knot carries a separately reviewed mass-action system and caller-owned composition-dependent activity provider record.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.external_aqueous_activity_history.v1", "default": "matintegrity.external_aqueous_activity_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `knot_requests` | 예 | `{"items": {"$ref": "#/$defs/ExternalAqueousActivityIteration"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `exact_time_temperature_parameter_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stable_species_reaction_topology_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_interpolation_or_extrapolation_between_knots_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalAqueousActivityHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s[]` | `s` |
| `temperature_K[]` | `K` |
| `knot_results[].time_s` | `s` |
| `knot_results[].temperature_K` | `K` |
| `knot_results[].values.ionic_strength_mol_kg` | `mol/kg_water` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Every exact time knot carries a separately reviewed mass-action system and caller-owned composition-dependent activity provider record.
- Species identities and reaction/constraint topology remain fixed; per-knot constants and provider parameter records may vary explicitly.
- No interpolation, kinetic interpretation, phase selection or corrosion qualification is performed.

## 구현 근거·독립 설명

- `caller_external_aqueous_activity_speciation_history`: At every explicitly supplied increasing time knot, solve one independently parameterized mass-action system with the same caller-owned composition-dependent activity provider identity, revision, configuration and single-ion convention. Require a fixed species/formula/reaction/constraint topology, exact time-temperature mapping, explicit knot-specific parameter records, complete provider convergence and caller reviews. Retain per-knot request/result digest and only report computed when all knots succeed; otherwise return a failed knot and prior prefix. No interpolation, kinetic model, provider implementation, phase selection or corrosion qualification is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.aqueous_external_activity_speciation_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'activity_provider': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.aqueous_external_activity_speciation_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-external-activity-history",
  "asset_id": "synthetic-asset",
  "location_id": "synthetic-location",
  "physical_scope_id": "synthetic-aqueous-control-volume",
  "time_basis": "elapsed_seconds",
  "elapsed_time_s": [
    0.0,
    60.0
  ],
  "knot_requests": [
    {
      "system": {
        "schema_version": "matintegrity.aqueous_mass_action.v1",
        "assessment_id": "synthetic-external-activity-history-knot-0",
        "solution_id": "synthetic-aqueous-history-solution",
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
      "ionic_strength_limit_mol_kg": 10.0,
      "ionic_strength_consistency_tolerance_mol_kg": 1e-08,
      "charge_balance_tolerance_mol_kg": 1e-08,
      "activity_provider_id": "synthetic-external-activity-provider",
      "activity_provider_revision": "example-only-1",
      "activity_configuration_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "activity_parameter_record_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "single_ion_activity_convention_id": "synthetic_identity_gamma_convention",
      "maximum_outer_iterations": 40,
      "log_gamma_tolerance": 1e-08,
      "damping_fraction": 0.5,
      "water_mass_conversion_reviewed": true,
      "molarity_to_molality_standard_state_mapping_reviewed": true,
      "temperature_and_parameter_support_reviewed": true,
      "complete_inventory_and_charge_scope_reviewed": true,
      "provider_species_order_and_unit_mapping_reviewed": true,
      "single_ion_activity_convention_reviewed": true,
      "provider_parameter_coverage_and_applicability_reviewed": true,
      "deterministic_provider_re_evaluation_reviewed": true,
      "fixed_point_solver_settings_reviewed": true,
      "single_liquid_no_precipitation_scope_reviewed": true,
      "evidence": [
        {
          "source_id": "synthetic-external-activity-provider",
          "origin": "synthetic",
          "citation": "Project-authored synthetic activity-provider contract example",
          "sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        }
      ]
    },
    {
      "system": {
        "schema_version": "matintegrity.aqueous_mass_action.v1",
        "assessment_id": "synthetic-external-activity-history-knot-1",
        "solution_id": "synthetic-aqueous-history-solution",
        "temperature_K": 323.15,
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
      "ionic_strength_limit_mol_kg": 10.0,
      "ionic_strength_consistency_tolerance_mol_kg": 1e-08,
      "charge_balance_tolerance_mol_kg": 1e-08,
      "activity_provider_id": "synthetic-external-activity-provider",
      "activity_provider_revision": "example-only-1",
      "activity_configuration_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "activity_parameter_record_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "single_ion_activity_convention_id": "synthetic_identity_gamma_convention",
      "maximum_outer_iterations": 40,
      "log_gamma_tolerance": 1e-08,
      "damping_fraction": 0.5,
      "water_mass_conversion_reviewed": true,
      "molarity_to_molality_standard_state_mapping_reviewed": true,
      "temperature_and_parameter_support_reviewed": true,
      "complete_inventory_and_charge_scope_reviewed": true,
      "provider_species_order_and_unit_mapping_reviewed": true,
      "single_ion_activity_convention_reviewed": true,
      "provider_parameter_coverage_and_applicability_reviewed": true,
      "deterministic_provider_re_evaluation_reviewed": true,
      "fixed_point_solver_settings_reviewed": true,
      "single_liquid_no_precipitation_scope_reviewed": true,
      "evidence": [
        {
          "source_id": "synthetic-external-activity-provider",
          "origin": "synthetic",
          "citation": "Project-authored synthetic activity-provider contract example",
          "sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        }
      ]
    }
  ],
  "exact_time_temperature_parameter_mapping_reviewed": true,
  "stable_species_reaction_topology_reviewed": true,
  "no_interpolation_or_extrapolation_between_knots_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_external_activity_history.py#L88)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
