# `integration.aqueous_candidate_network_speciation`

**목적:** Only the exact computed mass-action system assembled by a digest-pinned candidate workflow is passed to the established aqueous speciation solver.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `candidate_workflow_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `candidate_workflow_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousCandidateNetworkSpeciation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `speciation.species[].dimensionless_activity` | `1` |
| `speciation.species[].concentration_mol_L` | `mol/L` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only the exact computed mass-action system assembled by a digest-pinned candidate workflow is passed to the established aqueous speciation solver.
- Species inventory, reaction direction, equilibrium constants, constraints, temperature and activity standard state remain caller selected and Evidence backed upstream.
- This composition does not discover reactions or phases, infer kinetics, predict corrosion, or qualify material performance.

## 구현 근거·독립 설명

- `caller_composed_aqueous_candidate_network_speciation`: Consume only the mass-action system emitted by a computed digest-pinned caller candidate-network workflow. Verify workflow AssessmentResult input/context/result digest, assembly and system digests, temperature and activity standard state, then call the existing fixed-gamma aqueous mass-action speciation solver. Preserve workflow, enumeration, binding, assembly and solve lineage. Do not discover reactions/phases, infer constants/activity data, precipitation, kinetics, corrosion or qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.aqueous_candidate_network_speciation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.aqueous_candidate_network_speciation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-candidate-network-speciation",
  "candidate_workflow_result": {
    "schema_version": "matintegrity.assessment.v1",
    "model_id": "integration.aqueous_candidate_network_workflow",
    "model_version": "1.0.0",
    "status": "computed",
    "inputs": {
      "workflow_id": "synthetic-candidate-network-workflow",
      "enumeration": {
        "enumeration_id": "synthetic-hydration-reaction-candidates",
        "species": [
          {
            "species_id": "water",
            "charge_number": 0,
            "elemental_composition": {
              "H": 2,
              "O": 1
            }
          },
          {
            "species_id": "proton",
            "charge_number": 1,
            "elemental_composition": {
              "H": 1
            }
          },
          {
            "species_id": "hydronium",
            "charge_number": 1,
            "elemental_composition": {
              "H": 3,
              "O": 1
            }
          },
          {
            "species_id": "chloride",
            "charge_number": -1,
            "elemental_composition": {
              "Cl": 1
            }
          }
        ],
        "maximum_total_stoichiometric_order": 3,
        "maximum_side_multisets": 250000,
        "maximum_candidate_pair_checks": 250000,
        "maximum_candidate_reactions": 50000,
        "species_formula_and_charge_reviewed": true,
        "closed_candidate_species_inventory_reviewed": true,
        "candidate_use_and_manual_selection_reviewed": true,
        "evidence": [
          {
            "source_id": "synthetic-stoichiometry-example",
            "origin": "synthetic",
            "citation": "API wiring fixture only; no chemical recommendation",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "binding": {
        "schema_version": "matintegrity.aqueous_candidate_reaction_binding.v1",
        "binding_id": "synthetic-equilibrium-binding",
        "candidate_enumeration_input_sha256": "293b0172632a4a3e64137aa2ce5d5af672f16f0c2646327a97c682555be46b50",
        "target_mass_action_temperature_K": 298.15,
        "temperature_match_tolerance_K": 0.0,
        "target_activity_standard_state": "molarity_1_mol_L",
        "selections": [
          {
            "candidate_id": "balanced-reaction:b33c4682487e5eb6d6865cc9",
            "candidate_sha256": "b33c4682487e5eb6d6865cc9438e9160323936f30b0e0856c5d168d0823b70f1",
            "reaction_id": "caller-selected-hydration-reaction",
            "direction": "candidate_reverse",
            "log10_equilibrium_constant": 0.0,
            "temperature_K": 298.15,
            "equilibrium_parameter_set_id": "synthetic-K-record",
            "equilibrium_record_id": "synthetic-record-1",
            "equilibrium_record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ],
        "reaction_selection_and_constant_reviewed": true,
        "evidence": [
          {
            "source_id": "synthetic-K-record",
            "origin": "synthetic",
            "citation": "Invented record identifier for input wiring only",
            "license_id": null,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ]
      },
      "assembly": {
        "schema_version": "matintegrity.aqueous_mass_action_assembly.v1",
        "assessment_id": "synthetic-aqueous-assembly",
        "solution_id": "synthetic-solution",
        "temperature_K": 298.15,
        "activity_standard_state": "molarity_1_mol_L",
        "species": [
          {
            "species_id": "water",
            "charge_number": 0,
            "activity_coefficient": 1.0,
            "initial_activity": 0.5,
            "elemental_composition": {
              "H": 2,
              "O": 1
            }
          },
          {
            "species_id": "proton",
            "charge_number": 1,
            "activity_coefficient": 1.0,
            "initial_activity": 0.2,
            "elemental_composition": {
              "H": 1
            }
          },
          {
            "species_id": "hydronium",
            "charge_number": 1,
            "activity_coefficient": 1.0,
            "initial_activity": 0.1,
            "elemental_composition": {
              "H": 3,
              "O": 1
            }
          },
          {
            "species_id": "chloride",
            "charge_number": -1,
            "activity_coefficient": 1.0,
            "initial_activity": 0.3,
            "elemental_composition": {
              "Cl": 1
            }
          }
        ],
        "constraints": [
          {
            "constraint_id": "total-hydrogen",
            "target_mol_L": 1.5,
            "residual_scale_mol_L": 1.0,
            "terms": [
              {
                "species_id": "water",
                "coefficient": 2.0
              },
              {
                "species_id": "proton",
                "coefficient": 1.0
              },
              {
                "species_id": "hydronium",
                "coefficient": 3.0
              }
            ]
          },
          {
            "constraint_id": "total-chloride",
            "target_mol_L": 0.3,
            "residual_scale_mol_L": 1.0,
            "terms": [
              {
                "species_id": "chloride",
                "coefficient": 1.0
              }
            ]
          },
          {
            "constraint_id": "charge-balance",
            "target_mol_L": 0.0,
            "residual_scale_mol_L": 1.0,
            "terms": [
              {
                "species_id": "proton",
                "coefficient": 1.0
              },
              {
                "species_id": "hydronium",
                "coefficient": 1.0
              },
              {
                "species_id": "chloride",
                "coefficient": -1.0
              }
            ]
          }
        ],
        "maximum_iterations": 100,
        "normalized_residual_tolerance": 1e-10,
        "maximum_jacobian_condition_number": 100000000000000.0,
        "local_parameter_covariance": null,
        "local_parameter_covariance_reviewed": false,
        "activity_provider_id": "synthetic-ideal-activity",
        "activity_provider_revision": "1",
        "activity_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "activity_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "equilibrium_provider_id": "synthetic-equilibrium-provider",
        "equilibrium_provider_revision": "1",
        "equilibrium_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "complete_aqueous_species_inventory_reviewed": true,
        "reaction_stoichiometry_and_constant_reviewed": true,
        "balance_constraints_and_charge_scope_reviewed": true,
        "fixed_activity_coefficients_and_standard_state_reviewed": true,
        "temperature_and_provider_lineage_reviewed": true,
        "initial_activity_guess_and_solver_tolerance_reviewed": true,
        "single_liquid_phase_and_no_precipitation_reviewed": true,
        "elemental_formula_and_reaction_balance_reviewed": true,
        "evidence": [
          {
            "source_id": "synthetic-activity-record",
            "origin": "synthetic",
            "citation": "Invented activity record for input wiring only",
            "license_id": null,
            "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
          },
          {
            "source_id": "synthetic-K-record",
            "origin": "synthetic",
            "citation": "Invented record identifier for input wiring only",
            "license_id": null,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ]
      }
    },
    "values": {
      "workflow_id": "synthetic-candidate-network-workflow",
      "workflow_sha256": "e3a1fa6249eb264418d1058ff07c91f171f9f8bff32b81864fb2203c04c7e295",
      "enumeration_input_sha256": "293b0172632a4a3e64137aa2ce5d5af672f16f0c2646327a97c682555be46b50",
      "enumeration_result_sha256": "1eac2e4cecc69e3fd65838909218bb5836be8e779f47db3d67977870f7d06260",
      "binding_input_sha256": "8aabb10ded82139373ae5163588acd46bc70e36ffebc26f8b61ce7dc2fe92a56",
      "binding_result_sha256": "19675a3256360a0461f1c2a2c6817ad4f87779b5b03cafc8f28d2a0a942158da",
      "assembly_input_sha256": "32d30423e9c42ade2a6852fa13d5407a320aa1d08cd6f471d6b08e038ab1029b",
      "assembly_result_sha256": "350115b1bd7d463517846fd7c9d665e952f9e133f4f988530aca349cadb75db2",
      "enumeration": {
        "values": {
          "enumeration_id": "synthetic-hydration-reaction-candidates",
          "input_sha256": "293b0172632a4a3e64137aa2ce5d5af672f16f0c2646327a97c682555be46b50",
          "species_ids": [
            "water",
            "proton",
            "hydronium",
            "chloride"
          ],
          "maximum_total_stoichiometric_order": 3,
          "maximum_side_multisets": 250000,
          "maximum_candidate_pair_checks": 250000,
          "maximum_candidate_reactions": 50000,
          "enumerated_chemical_reactions": false,
          "equilibrium_constants_assigned": false,
          "reaction_direction_selected": false,
          "enumerated_side_multiset_count": 34,
          "candidate_pair_checks": 44,
          "candidate_reaction_count": 1,
          "candidate_reactions": [
            {
              "reactants": [
                {
                  "species_id": "hydronium",
                  "coefficient": 1
                }
              ],
              "products": [
                {
                  "species_id": "water",
                  "coefficient": 1
                },
                {
                  "species_id": "proton",
                  "coefficient": 1
                }
              ],
              "balanced_elements": [
                "Cl",
                "H",
                "O"
              ],
              "charge_stoichiometric_residual": 0,
              "candidate_id": "balanced-reaction:b33c4682487e5eb6d6865cc9",
              "candidate_sha256": "b33c4682487e5eb6d6865cc9438e9160323936f30b0e0856c5d168d0823b70f1"
            }
          ]
        },
        "status": "computed",
        "notes": [
          "Candidates are bounded integer stoichiometries satisfying only caller-supplied elemental and charge balances. This enumeration does not establish chemical feasibility, reaction mechanism, phases, kinetics, equilibrium constants, direction, or completeness outside the declared species/order bounds; every candidate requires independent review before use.",
          "candidate_id is a stable digest-derived reference to the normalized, direction-neutral stoichiometric split; it does not identify a validated chemical reaction or provide thermodynamic data."
        ]
      },
      "binding": {
        "values": {
          "binding_id": "synthetic-equilibrium-binding",
          "input_sha256": "8aabb10ded82139373ae5163588acd46bc70e36ffebc26f8b61ce7dc2fe92a56",
          "candidate_enumeration_input_sha256": "293b0172632a4a3e64137aa2ce5d5af672f16f0c2646327a97c682555be46b50",
          "candidate_enumeration_result_sha256": "1eac2e4cecc69e3fd65838909218bb5836be8e779f47db3d67977870f7d06260",
          "target_mass_action_temperature_K": 298.15,
          "temperature_match_tolerance_K": 0.0,
          "activity_standard_state": "molarity_1_mol_L",
          "temperature_K_by_reaction": [
            {
              "reaction_id": "caller-selected-hydration-reaction",
              "temperature_K": 298.15
            }
          ],
          "reactions": [
            {
              "reaction_id": "caller-selected-hydration-reaction",
              "log10_equilibrium_constant": -0.0,
              "terms": [
                {
                  "species_id": "hydronium",
                  "coefficient": 1.0
                },
                {
                  "species_id": "water",
                  "coefficient": -1.0
                },
                {
                  "species_id": "proton",
                  "coefficient": -1.0
                }
              ]
            }
          ],
          "reaction_lineage": [
            {
              "reaction_id": "caller-selected-hydration-reaction",
              "candidate_id": "balanced-reaction:b33c4682487e5eb6d6865cc9",
              "candidate_sha256": "b33c4682487e5eb6d6865cc9438e9160323936f30b0e0856c5d168d0823b70f1",
              "direction": "candidate_reverse",
              "source_log10_equilibrium_constant": 0.0,
              "signed_log10_equilibrium_constant": -0.0,
              "bound_reaction_sha256": "db03065b82934f90a1588705f6d97958aba231b51687264e5adf9de19f74130b",
              "temperature_K": 298.15,
              "equilibrium_parameter_set_id": "synthetic-K-record",
              "equilibrium_record_id": "synthetic-record-1",
              "equilibrium_record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ],
          "reaction_count": 1,
          "source_candidate_enumeration_sha256": "1eac2e4cecc69e3fd65838909218bb5836be8e779f47db3d67977870f7d06260",
          "equilibrium_data_inferred": false,
          "chemical_feasibility_inferred": false
        },
        "status": "computed",
        "notes": [
          "Candidate selection, reaction direction, equilibrium constants and temperature applicability are caller-supplied. Verify each bound reaction against the mass-action system temperature and standard state before use."
        ]
      },
      "assembly": {
        "values": {
          "assessment_id": "synthetic-aqueous-assembly",
          "solution_id": "synthetic-solution",
          "input_sha256": "32d30423e9c42ade2a6852fa13d5407a320aa1d08cd6f471d6b08e038ab1029b",
          "binding_result_sha256": "19675a3256360a0461f1c2a2c6817ad4f87779b5b03cafc8f28d2a0a942158da",
          "temperature_K": 298.15,
          "activity_standard_state": "molarity_1_mol_L",
          "mass_action_system": {
            "schema_version": "matintegrity.aqueous_mass_action.v1",
            "assessment_id": "synthetic-aqueous-assembly",
            "solution_id": "synthetic-solution",
            "temperature_K": 298.15,
            "activity_standard_state": "molarity_1_mol_L",
            "species": [
              {
                "species_id": "water",
                "charge_number": 0,
                "activity_coefficient": 1.0,
                "initial_activity": 0.5,
                "elemental_composition": {
                  "H": 2,
                  "O": 1
                }
              },
              {
                "species_id": "proton",
                "charge_number": 1,
                "activity_coefficient": 1.0,
                "initial_activity": 0.2,
                "elemental_composition": {
                  "H": 1
                }
              },
              {
                "species_id": "hydronium",
                "charge_number": 1,
                "activity_coefficient": 1.0,
                "initial_activity": 0.1,
                "elemental_composition": {
                  "H": 3,
                  "O": 1
                }
              },
              {
                "species_id": "chloride",
                "charge_number": -1,
                "activity_coefficient": 1.0,
                "initial_activity": 0.3,
                "elemental_composition": {
                  "Cl": 1
                }
              }
            ],
            "reactions": [
              {
                "reaction_id": "caller-selected-hydration-reaction",
                "log10_equilibrium_constant": -0.0,
                "terms": [
                  {
                    "species_id": "hydronium",
                    "coefficient": 1.0
                  },
                  {
                    "species_id": "water",
                    "coefficient": -1.0
                  },
                  {
                    "species_id": "proton",
                    "coefficient": -1.0
                  }
                ]
              }
            ],
            "constraints": [
              {
                "constraint_id": "total-hydrogen",
                "target_mol_L": 1.5,
                "residual_scale_mol_L": 1.0,
                "terms": [
                  {
                    "species_id": "water",
                    "coefficient": 2.0
                  },
                  {
                    "species_id": "proton",
                    "coefficient": 1.0
                  },
                  {
                    "species_id": "hydronium",
                    "coefficient": 3.0
                  }
                ]
              },
              {
                "constraint_id": "total-chloride",
                "target_mol_L": 0.3,
                "residual_scale_mol_L": 1.0,
                "terms": [
                  {
                    "species_id": "chloride",
                    "coefficient": 1.0
                  }
                ]
              },
              {
                "constraint_id": "charge-balance",
                "target_mol_L": 0.0,
                "residual_scale_mol_L": 1.0,
                "terms": [
                  {
                    "species_id": "proton",
                    "coefficient": 1.0
                  },
                  {
                    "species_id": "hydronium",
                    "coefficient": 1.0
                  },
                  {
                    "species_id": "chloride",
                    "coefficient": -1.0
                  }
                ]
              }
            ],
            "maximum_iterations": 100,
            "normalized_residual_tolerance": 1e-10,
            "maximum_jacobian_condition_number": 100000000000000.0,
            "local_parameter_covariance": null,
            "local_parameter_covariance_reviewed": false,
            "activity_provider_id": "synthetic-ideal-activity",
            "activity_provider_revision": "1",
            "activity_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "activity_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "equilibrium_provider_id": "synthetic-equilibrium-provider",
            "equilibrium_provider_revision": "1",
            "equilibrium_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "equilibrium_record_digest": "d6946bcb01c35ea2022e5a232b730dc02e16fab177ac1b75397bc371b2261de1",
            "complete_aqueous_species_inventory_reviewed": true,
            "reaction_stoichiometry_and_constant_reviewed": true,
            "balance_constraints_and_charge_scope_reviewed": true,
            "fixed_activity_coefficients_and_standard_state_reviewed": true,
            "temperature_and_provider_lineage_reviewed": true,
            "initial_activity_guess_and_solver_tolerance_reviewed": true,
            "single_liquid_phase_and_no_precipitation_reviewed": true,
            "elemental_formula_and_reaction_balance_reviewed": true,
            "evidence": [
              {
                "source_id": "synthetic-activity-record",
                "origin": "synthetic",
                "citation": "Invented activity record for input wiring only",
                "license_id": null,
                "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
              },
              {
                "source_id": "synthetic-K-record",
                "origin": "synthetic",
                "citation": "Invented record identifier for input wiring only",
                "license_id": null,
                "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              }
            ]
          },
          "mass_action_system_sha256": "69fc2a85bbd9aaaf6235f7a5e29c272508ee23172b7bbbd38ef9a4f3e1b68dc8",
          "equilibrium_record_digest": "d6946bcb01c35ea2022e5a232b730dc02e16fab177ac1b75397bc371b2261de1",
          "reaction_lineage": [
            {
              "reaction_id": "caller-selected-hydration-reaction",
              "candidate_id": "balanced-reaction:b33c4682487e5eb6d6865cc9",
              "candidate_sha256": "b33c4682487e5eb6d6865cc9438e9160323936f30b0e0856c5d168d0823b70f1",
              "direction": "candidate_reverse",
              "source_log10_equilibrium_constant": 0.0,
              "signed_log10_equilibrium_constant": -0.0,
              "bound_reaction_sha256": "db03065b82934f90a1588705f6d97958aba231b51687264e5adf9de19f74130b",
              "temperature_K": 298.15,
              "equilibrium_parameter_set_id": "synthetic-K-record",
              "equilibrium_record_id": "synthetic-record-1",
              "equilibrium_record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ],
          "reaction_count": 1,
          "species_count": 4,
          "constraint_count": 3
        },
        "status": "computed",
        "notes": [
          "The returned mass_action_system can be passed as inputs to chemistry.aqueous_mass_action_speciation. Its equilibrium_record_digest is the digest of the ordered bound reaction lineage; retain reaction_lineage with the result.",
          "This assembly applies the declared square-system contract. It does not check convergence, chemical feasibility, thermodynamic quality, or independent validation."
        ]
      },
      "workflow_scope": "bounded stoichiometric candidate enumeration followed by caller-selected, evidence-backed equilibrium constants and strict single-phase mass-action system assembly; no reaction or phase is automatically selected"
    },
    "units": {
      "candidate_reaction_count": "1",
      "reaction_count": "1"
    },
    "assumptions": [
      "A caller-defined closed candidate species inventory and formula/charge set is screened with explicit search budgets.",
      "Reaction selections, direction, equilibrium records, temperature match, constraints, activity coefficients and phase scope remain caller supplied and evidence bound.",
      "The workflow assembles but does not solve, discover phases, infer kinetics, or qualify wet-CO2 corrosion."
    ],
    "notes": [
      "This adapter composes existing bounded contracts and preserves every stage digest; it does not infer chemical feasibility, missing species, phase stability, equilibrium constants or kinetics.",
      "The returned system is an assembly artifact. A separate explicitly parameterized speciation calculation is required to solve for activities."
    ],
    "context": {
      "asset_id": "synthetic-aqueous-asset",
      "location_id": "synthetic-aqueous-location",
      "time_basis": "elapsed_seconds",
      "evidence": [],
      "metadata": {}
    },
    "input_digest": "47ac7cee32fc3d7a5a78c432a21a7cb49a635523ab0572145c1f14846506c0ad",
    "source_ids": [
      "caller_composed_aqueous_candidate_network_workflow"
    ],
    "qualification": "user_model",
    "runtime": {
      "matintegrity": "0.1.0.dev0",
      "python": "3.12.14",
      "numpy": "2.3.5",
      "pydantic": "2.14.1",
      "pint": "0.26.2",
      "scipy": "1.18.1",
      "rainflow": "3.2.0"
    },
    "probability_semantics": {}
  },
  "candidate_workflow_result_sha256": "27455c3c57c70d22974ad3e35256ae3fd89caa738504c20016db883964b10eea",
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_candidate_speciation.py#L74)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
