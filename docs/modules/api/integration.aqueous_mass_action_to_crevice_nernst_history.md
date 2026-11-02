# `integration.aqueous_mass_action_to_crevice_nernst_history`

**목적:** Only dimensionless activities and exact time/temperature knots from a computed digest-pinned crevice mass-action or B-dot speciation history are consumed.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_mass_action_to_nernst_history.v1", "default": "matintegrity.aqueous_mass_action_to_nernst_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `mass_action_history_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `mass_action_history_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_quotient_stoichiometry` | 예 | `{"additionalProperties": {"type": "number"}, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `electron_number` | 예 | `{"maximum": 32, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `standard_potential_V` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | V |
| `standard_potential_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `redox_reaction_direction_and_electron_number_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_standard_state_and_species_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `standard_potential_temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `local_activity_history_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `potential_only_no_rate_or_acceptance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousMassActionToNernstHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `source_inventory_sha256` | `1` |
| `elapsed_time_s` | `s` |
| `temperature_K` | `K` |
| `standard_potential_V` | `V` |
| `potential_history[].time_s` | `s` |
| `potential_history[].temperature_K` | `K` |
| `potential_history[].standard_potential_V` | `V` |
| `potential_history[].potential_V` | `V` |
| `potential_history[].ln_reaction_quotient` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only dimensionless activities and exact time/temperature knots from a computed digest-pinned crevice mass-action or B-dot speciation history are consumed.
- The caller supplies the redox equation, reference identity, electron number and standard-potential history, which must align with the solved aqueous species and time basis.
- The upstream activity-history digest supplies source lineage when no raw composition-history digest exists; B-dot parameter-record hashes remain in the upstream result.
- This composes sequential calculations; it does not perform simultaneous speciation/electrode coupling, activity inference, kinetics or corrosion qualification.

## 구현 근거·독립 설명

- `aqueous_mass_action_activities_to_crevice_nernst_potential_history`: Consume only a computed digest-pinned knotwise aqueous mass-action result and bind its strictly positive dimensionless species activities to an explicitly caller-defined redox quotient, electron count, standard-potential reference and exact-knot standard-potential history. Preserve the upstream composition and solver-result digests, source inventory identity and exact clock/temperature knots. Require all quotient species, activity standard-state mapping, potential provider Evidence and reaction-direction reviews. This sequential adapter does not solve the redox reaction, infer E0 or activities, close current back into the same chemistry trajectory, add multiphase/transport kinetics, or infer corrosion/wall loss.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.aqueous_mass_action_to_crevice_nernst_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.aqueous_mass_action_to_crevice_nernst_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-aqueous-activity-to-nernst-redox_B",
  "mass_action_history_result": {
    "schema_version": "matintegrity.assessment.v1",
    "model_id": "integration.crevice_composition_to_aqueous_mass_action_history",
    "model_version": "1.0.0",
    "status": "computed",
    "inputs": {
      "schema_version": "matintegrity.crevice_composition_to_mass_action_history.v1",
      "assessment_id": "synthetic-crevice-aqueous-speciation-history",
      "composition_result": {
        "schema_version": "matintegrity.assessment.v1",
        "model_id": "integration.crevice_electrochemical_composition_history",
        "model_version": "1.0.0",
        "status": "computed",
        "inputs": {
          "schema_version": "matintegrity.crevice_electrochemical_composition_history.v1",
          "assessment_id": "synthetic-well-mixed-composition",
          "transfer_result": {
            "schema_version": "matintegrity.assessment.v1",
            "model_id": "integration.crevice_electrochemical_inventory_transfer",
            "model_version": "1.0.0",
            "status": "computed",
            "inputs": {
              "schema_version": "matintegrity.crevice_electrochemical_inventory_integration.v1",
              "assessment_id": "synthetic-reference-area-transfer",
              "mixed_potential_result": {
                "schema_version": "matintegrity.assessment.v1",
                "model_id": "electrochemistry.crevice_mixed_potential_history",
                "model_version": "1.0.0",
                "status": "computed",
                "inputs": {
                  "schema_version": "matintegrity.crevice_mixed_potential_history.v1",
                  "assessment_id": "synthetic-two-reaction-mixed-potential",
                  "asset_id": "synthetic-loop",
                  "location_id": "synthetic-crevice",
                  "physical_scope_id": "synthetic-wet-surface",
                  "clock_id": "synthetic-elapsed-seconds",
                  "common_reference_electrode_id": "SHE",
                  "reference_area_m2": 2.0,
                  "reactions": [
                    {
                      "reaction_id": "redox_A",
                      "nernst_result": {
                        "schema_version": "matintegrity.assessment.v1",
                        "model_id": "degradation.crevice_nernst_potential_history",
                        "model_version": "1.0.0",
                        "status": "computed",
                        "inputs": {
                          "schema_version": "matintegrity.crevice_nernst_profile.v1",
                          "assessment_id": "synthetic-redox_A-nernst",
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "physical_scope_id": "synthetic-wet-surface",
                          "clock_id": "synthetic-elapsed-seconds",
                          "source_inventory_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                          "reaction_id": "redox_A",
                          "standard_potential_reference_id": "SHE",
                          "reaction_quotient_stoichiometry": {
                            "OxidizedA": 1.0
                          },
                          "electron_number": 1,
                          "elapsed_time_s": [
                            0.0,
                            30.0,
                            60.0
                          ],
                          "temperature_K": [
                            298.15,
                            298.15,
                            298.15
                          ],
                          "standard_potential_V": [
                            0.0,
                            0.0,
                            0.0
                          ],
                          "species_activity_history": {
                            "OxidizedA": [
                              1.0,
                              1.0,
                              1.0
                            ]
                          },
                          "activity_provider_id": "synthetic-activity-source",
                          "activity_provider_revision": "synthetic-1",
                          "activity_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                          "activity_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                          "standard_potential_provider_id": "synthetic-standard-potential-source",
                          "standard_potential_provider_revision": "synthetic-1",
                          "standard_potential_configuration_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                          "standard_potential_record_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                          "redox_reaction_direction_and_electron_number_reviewed": true,
                          "activity_standard_state_and_species_mapping_reviewed": true,
                          "standard_potential_temperature_history_reviewed": true,
                          "local_activity_history_applicability_reviewed": true,
                          "potential_only_no_rate_or_acceptance_reviewed": true,
                          "computational_use_authorized": true,
                          "evidence": [
                            {
                              "source_id": "synthetic-activity-source",
                              "origin": "synthetic",
                              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-standard-potential-source",
                              "origin": "synthetic",
                              "citation": "Synthetic standard-potential fixture for API wiring only.",
                              "license_id": null,
                              "sha256": null
                            }
                          ]
                        },
                        "values": {
                          "assessment_id": "synthetic-redox_A-nernst",
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "physical_scope_id": "synthetic-wet-surface",
                          "clock_id": "synthetic-elapsed-seconds",
                          "source_inventory_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                          "reaction_id": "redox_A",
                          "reaction_quotient_stoichiometry": {
                            "OxidizedA": 1.0
                          },
                          "electron_number": 1,
                          "activity_provider_id": "synthetic-activity-source",
                          "activity_provider_revision": "synthetic-1",
                          "activity_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                          "activity_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                          "standard_potential_provider_id": "synthetic-standard-potential-source",
                          "standard_potential_provider_revision": "synthetic-1",
                          "standard_potential_configuration_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                          "standard_potential_record_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                          "input_digest": "8f83e541fae91b7e9f432924e63a239a184683b9cf988d4a6156262afefbe311",
                          "potential_history": [
                            {
                              "time_s": 0.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.0,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.0
                            },
                            {
                              "time_s": 30.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.0,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.0
                            },
                            {
                              "time_s": 60.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.0,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.0
                            }
                          ],
                          "potential_history_sha256": "9783c3ce1e4e6bbb6176637fcfe96acea4d7d5b7e32b66cec2417eec683aa18d",
                          "reaction_quotient_definition": "lnQ=sum(nu_i*ln(a_i)); products positive, reactants negative; electrons excluded",
                          "standard_potential_interpretation": "caller_supplied_knotwise_history",
                          "missing_reviews": []
                        },
                        "units": {
                          "source_inventory_sha256": "1",
                          "elapsed_time_s": "s",
                          "temperature_K": "K",
                          "standard_potential_V": "V",
                          "potential_history[].time_s": "s",
                          "potential_history[].temperature_K": "K",
                          "potential_history[].standard_potential_V": "V",
                          "potential_history[].potential_V": "V",
                          "potential_history[].ln_reaction_quotient": "1",
                          "electron_number": "1",
                          "potential_history_sha256": "1"
                        },
                        "assumptions": [
                          "Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.",
                          "Reaction direction, activity standard state, species mapping and temperature applicability are reviewed caller inputs; this half-cell potential is not a mixed-potential or corrosion-rate calculation."
                        ],
                        "notes": [
                          "This is a Nernst half-cell potential calculated from caller-supplied dimensionless activities and standard-potential history.",
                          "It does not determine mixed potential, corrosion current, reaction kinetics, pH, activity coefficients, phase state, susceptibility, life or acceptance."
                        ],
                        "context": {
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "time_basis": "synthetic-elapsed-seconds",
                          "evidence": [
                            {
                              "source_id": "synthetic-activity-source",
                              "origin": "synthetic",
                              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-standard-potential-source",
                              "origin": "synthetic",
                              "citation": "Synthetic standard-potential fixture for API wiring only.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-fe-kinetics",
                              "origin": "synthetic",
                              "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-h-kinetics",
                              "origin": "synthetic",
                              "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                              "license_id": null,
                              "sha256": null
                            }
                          ],
                          "metadata": {}
                        },
                        "input_digest": "d3204ac0d701478500acd7e690c3fff8e3a81be8d228ac934acef797db62758a",
                        "source_ids": [
                          "crevice_nernst_activity_potential"
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
                      "nernst_result_sha256": "4faf28e20542c1850c1a722d6a8466d951e0bd8b51eba92779fe027a207dae0a",
                      "reference_electrode_id": "SHE",
                      "exposed_area_m2": 1.0,
                      "exchange_current_density_A_m2": 1e-05,
                      "electron_number": 1,
                      "anodic_transfer_coefficient": 0.5,
                      "cathodic_transfer_coefficient": 0.5,
                      "minimum_overpotential_V": -0.5,
                      "maximum_overpotential_V": 0.5,
                      "stoichiometric_species_coefficients": {
                        "PoolA": 1.0
                      },
                      "kinetics_provider_id": "synthetic-fe-kinetics",
                      "kinetics_provider_revision": "synthetic-1",
                      "kinetics_calibration_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                      "kinetics_and_anodic_direction_reviewed": true,
                      "species_flux_mapping_and_area_basis_reviewed": true,
                      "evidence": [
                        {
                          "source_id": "synthetic-fe-kinetics",
                          "origin": "synthetic",
                          "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                          "license_id": null,
                          "sha256": null
                        }
                      ]
                    },
                    {
                      "reaction_id": "redox_B",
                      "nernst_result": {
                        "schema_version": "matintegrity.assessment.v1",
                        "model_id": "degradation.crevice_nernst_potential_history",
                        "model_version": "1.0.0",
                        "status": "computed",
                        "inputs": {
                          "schema_version": "matintegrity.crevice_nernst_profile.v1",
                          "assessment_id": "synthetic-redox_B-nernst",
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "physical_scope_id": "synthetic-wet-surface",
                          "clock_id": "synthetic-elapsed-seconds",
                          "source_inventory_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                          "reaction_id": "redox_B",
                          "standard_potential_reference_id": "SHE",
                          "reaction_quotient_stoichiometry": {
                            "OxidizedB": 1.0
                          },
                          "electron_number": 1,
                          "elapsed_time_s": [
                            0.0,
                            30.0,
                            60.0
                          ],
                          "temperature_K": [
                            298.15,
                            298.15,
                            298.15
                          ],
                          "standard_potential_V": [
                            0.3,
                            0.3,
                            0.3
                          ],
                          "species_activity_history": {
                            "OxidizedB": [
                              1.0,
                              1.0,
                              1.0
                            ]
                          },
                          "activity_provider_id": "synthetic-activity-source",
                          "activity_provider_revision": "synthetic-1",
                          "activity_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                          "activity_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                          "standard_potential_provider_id": "synthetic-standard-potential-source",
                          "standard_potential_provider_revision": "synthetic-1",
                          "standard_potential_configuration_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                          "standard_potential_record_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                          "redox_reaction_direction_and_electron_number_reviewed": true,
                          "activity_standard_state_and_species_mapping_reviewed": true,
                          "standard_potential_temperature_history_reviewed": true,
                          "local_activity_history_applicability_reviewed": true,
                          "potential_only_no_rate_or_acceptance_reviewed": true,
                          "computational_use_authorized": true,
                          "evidence": [
                            {
                              "source_id": "synthetic-activity-source",
                              "origin": "synthetic",
                              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-standard-potential-source",
                              "origin": "synthetic",
                              "citation": "Synthetic standard-potential fixture for API wiring only.",
                              "license_id": null,
                              "sha256": null
                            }
                          ]
                        },
                        "values": {
                          "assessment_id": "synthetic-redox_B-nernst",
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "physical_scope_id": "synthetic-wet-surface",
                          "clock_id": "synthetic-elapsed-seconds",
                          "source_inventory_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                          "reaction_id": "redox_B",
                          "reaction_quotient_stoichiometry": {
                            "OxidizedB": 1.0
                          },
                          "electron_number": 1,
                          "activity_provider_id": "synthetic-activity-source",
                          "activity_provider_revision": "synthetic-1",
                          "activity_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                          "activity_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                          "standard_potential_provider_id": "synthetic-standard-potential-source",
                          "standard_potential_provider_revision": "synthetic-1",
                          "standard_potential_configuration_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                          "standard_potential_record_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                          "input_digest": "9022a735dae34f40acc5f7c4f20886a1a82f2a97814cee1bd11f33c6e20abe13",
                          "potential_history": [
                            {
                              "time_s": 0.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.3,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.3
                            },
                            {
                              "time_s": 30.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.3,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.3
                            },
                            {
                              "time_s": 60.0,
                              "temperature_K": 298.15,
                              "standard_potential_V": 0.3,
                              "ln_reaction_quotient": 0.0,
                              "potential_V": 0.3
                            }
                          ],
                          "potential_history_sha256": "420e260fcac72487b7caade0596946ab596668cc745dfef80c1be4a833bd90af",
                          "reaction_quotient_definition": "lnQ=sum(nu_i*ln(a_i)); products positive, reactants negative; electrons excluded",
                          "standard_potential_interpretation": "caller_supplied_knotwise_history",
                          "missing_reviews": []
                        },
                        "units": {
                          "source_inventory_sha256": "1",
                          "elapsed_time_s": "s",
                          "temperature_K": "K",
                          "standard_potential_V": "V",
                          "potential_history[].time_s": "s",
                          "potential_history[].temperature_K": "K",
                          "potential_history[].standard_potential_V": "V",
                          "potential_history[].potential_V": "V",
                          "potential_history[].ln_reaction_quotient": "1",
                          "electron_number": "1",
                          "potential_history_sha256": "1"
                        },
                        "assumptions": [
                          "Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.",
                          "Reaction direction, activity standard state, species mapping and temperature applicability are reviewed caller inputs; this half-cell potential is not a mixed-potential or corrosion-rate calculation."
                        ],
                        "notes": [
                          "This is a Nernst half-cell potential calculated from caller-supplied dimensionless activities and standard-potential history.",
                          "It does not determine mixed potential, corrosion current, reaction kinetics, pH, activity coefficients, phase state, susceptibility, life or acceptance."
                        ],
                        "context": {
                          "asset_id": "synthetic-loop",
                          "location_id": "synthetic-crevice",
                          "time_basis": "synthetic-elapsed-seconds",
                          "evidence": [
                            {
                              "source_id": "synthetic-activity-source",
                              "origin": "synthetic",
                              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-standard-potential-source",
                              "origin": "synthetic",
                              "citation": "Synthetic standard-potential fixture for API wiring only.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-fe-kinetics",
                              "origin": "synthetic",
                              "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                              "license_id": null,
                              "sha256": null
                            },
                            {
                              "source_id": "synthetic-h-kinetics",
                              "origin": "synthetic",
                              "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                              "license_id": null,
                              "sha256": null
                            }
                          ],
                          "metadata": {}
                        },
                        "input_digest": "f8e5ae4372ebbd7d0b8a6c83e6dfa6266cf019375caa7bd3cee7e5dfb2284339",
                        "source_ids": [
                          "crevice_nernst_activity_potential"
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
                      "nernst_result_sha256": "f226d614361b96a425f487fe067f3ab441a86cc64520d7417caf3be524c5f394",
                      "reference_electrode_id": "SHE",
                      "exposed_area_m2": 1.0,
                      "exchange_current_density_A_m2": 1e-05,
                      "electron_number": 1,
                      "anodic_transfer_coefficient": 0.5,
                      "cathodic_transfer_coefficient": 0.5,
                      "minimum_overpotential_V": -0.5,
                      "maximum_overpotential_V": 0.5,
                      "stoichiometric_species_coefficients": {
                        "PoolB": 1.0
                      },
                      "kinetics_provider_id": "synthetic-h-kinetics",
                      "kinetics_provider_revision": "synthetic-1",
                      "kinetics_calibration_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                      "kinetics_and_anodic_direction_reviewed": true,
                      "species_flux_mapping_and_area_basis_reviewed": true,
                      "evidence": [
                        {
                          "source_id": "synthetic-h-kinetics",
                          "origin": "synthetic",
                          "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                          "license_id": null,
                          "sha256": null
                        }
                      ]
                    }
                  ],
                  "quasi_steady_local_balance_reviewed": true,
                  "negligible_solution_ohmic_drop_reviewed": true,
                  "common_electronic_potential_basis_reviewed": true,
                  "reaction_set_and_area_partition_complete_reviewed": true,
                  "computational_use_authorized": true,
                  "evidence": [
                    {
                      "source_id": "synthetic-activity-source",
                      "origin": "synthetic",
                      "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-standard-potential-source",
                      "origin": "synthetic",
                      "citation": "Synthetic standard-potential fixture for API wiring only.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-fe-kinetics",
                      "origin": "synthetic",
                      "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-h-kinetics",
                      "origin": "synthetic",
                      "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                      "license_id": null,
                      "sha256": null
                    }
                  ]
                },
                "values": {
                  "assessment_id": "synthetic-two-reaction-mixed-potential",
                  "asset_id": "synthetic-loop",
                  "location_id": "synthetic-crevice",
                  "physical_scope_id": "synthetic-wet-surface",
                  "clock_id": "synthetic-elapsed-seconds",
                  "common_reference_electrode_id": "SHE",
                  "reference_area_m2": 2.0,
                  "source_inventory_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                  "reaction_ids": [
                    "redox_A",
                    "redox_B"
                  ],
                  "nernst_result_sha256_by_reaction": {
                    "redox_A": "4faf28e20542c1850c1a722d6a8466d951e0bd8b51eba92779fe027a207dae0a",
                    "redox_B": "f226d614361b96a425f487fe067f3ab441a86cc64520d7417caf3be524c5f394"
                  },
                  "kinetics_calibration_sha256_by_reaction": {
                    "redox_A": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                    "redox_B": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                  },
                  "input_sha256": "9ddee9d6241f9cb045084d78bff780d10b9fc7ea0db22e19d4ab33f1de628476",
                  "mixed_potential_history": [
                    {
                      "time_s": 0.0,
                      "temperature_K": 298.15,
                      "mixed_potential_V": 0.1500000000003183,
                      "net_current_density_on_reference_area_A_m2": 1.1508263959847387e-15,
                      "reaction_responses": [
                        {
                          "reaction_id": "redox_A",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.0,
                          "overpotential_V": 0.1500000000003183,
                          "reference_area_signed_current_density_A_m2": 9.235599238792025e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 9.262589531210534e-05,
                          "reference_area_gross_cathodic_current_density_A_m2": 2.6990292418509795e-07,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolA": 9.572024095129397e-10
                          }
                        },
                        {
                          "reaction_id": "redox_B",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.3,
                          "overpotential_V": -0.1499999999996817,
                          "reference_area_signed_current_density_A_m2": -9.235599238676942e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 2.6990292418844156e-07,
                          "reference_area_gross_cathodic_current_density_A_m2": 9.262589531095786e-05,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolB": -9.572024095010123e-10
                          }
                        }
                      ]
                    },
                    {
                      "time_s": 30.0,
                      "temperature_K": 298.15,
                      "mixed_potential_V": 0.1500000000003183,
                      "net_current_density_on_reference_area_A_m2": 1.1508263959847387e-15,
                      "reaction_responses": [
                        {
                          "reaction_id": "redox_A",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.0,
                          "overpotential_V": 0.1500000000003183,
                          "reference_area_signed_current_density_A_m2": 9.235599238792025e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 9.262589531210534e-05,
                          "reference_area_gross_cathodic_current_density_A_m2": 2.6990292418509795e-07,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolA": 9.572024095129397e-10
                          }
                        },
                        {
                          "reaction_id": "redox_B",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.3,
                          "overpotential_V": -0.1499999999996817,
                          "reference_area_signed_current_density_A_m2": -9.235599238676942e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 2.6990292418844156e-07,
                          "reference_area_gross_cathodic_current_density_A_m2": 9.262589531095786e-05,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolB": -9.572024095010123e-10
                          }
                        }
                      ]
                    },
                    {
                      "time_s": 60.0,
                      "temperature_K": 298.15,
                      "mixed_potential_V": 0.1500000000003183,
                      "net_current_density_on_reference_area_A_m2": 1.1508263959847387e-15,
                      "reaction_responses": [
                        {
                          "reaction_id": "redox_A",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.0,
                          "overpotential_V": 0.1500000000003183,
                          "reference_area_signed_current_density_A_m2": 9.235599238792025e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 9.262589531210534e-05,
                          "reference_area_gross_cathodic_current_density_A_m2": 2.6990292418509795e-07,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolA": 9.572024095129397e-10
                          }
                        },
                        {
                          "reaction_id": "redox_B",
                          "exposed_area_m2": 1.0,
                          "area_fraction_of_reference": 0.5,
                          "equilibrium_potential_V": 0.3,
                          "overpotential_V": -0.1499999999996817,
                          "reference_area_signed_current_density_A_m2": -9.235599238676942e-05,
                          "reference_area_gross_anodic_current_density_A_m2": 2.6990292418844156e-07,
                          "reference_area_gross_cathodic_current_density_A_m2": 9.262589531095786e-05,
                          "reference_area_species_flux_mol_m2_s": {
                            "PoolB": -9.572024095010123e-10
                          }
                        }
                      ]
                    }
                  ],
                  "mixed_potential_history_sha256": "7ecdba944db6f479dcca09c4956490dd434e8102e30a97505cb6e8e7d70e348a",
                  "solver": "knotwise_shared-potential_Butler-Volmer_current-balance",
                  "area_basis": "all reaction currents and species fluxes normalized to caller reference_area_m2",
                  "time_policy": "evaluate_exact_caller_knots_without_interpolation_or_integration"
                },
                "units": {
                  "reference_area_m2": "m2",
                  "mixed_potential_history[].time_s": "s",
                  "mixed_potential_history[].temperature_K": "K",
                  "mixed_potential_history[].mixed_potential_V": "V",
                  "mixed_potential_history[].net_current_density_on_reference_area_A_m2": "A/m2",
                  "mixed_potential_history[].reaction_responses[].exposed_area_m2": "m2",
                  "mixed_potential_history[].reaction_responses[].area_fraction_of_reference": "1",
                  "mixed_potential_history[].reaction_responses[].equilibrium_potential_V": "V",
                  "mixed_potential_history[].reaction_responses[].overpotential_V": "V",
                  "mixed_potential_history[].reaction_responses[].reference_area_signed_current_density_A_m2": "A/m2",
                  "mixed_potential_history[].reaction_responses[].reference_area_gross_anodic_current_density_A_m2": "A/m2",
                  "mixed_potential_history[].reaction_responses[].reference_area_gross_cathodic_current_density_A_m2": "A/m2",
                  "mixed_potential_history[].reaction_responses[].reference_area_species_flux_mol_m2_s.*": "mol/m2/s"
                },
                "assumptions": [
                  "At every aligned crevice inventory time knot, evaluate multiple caller-provided Nernst half-cell profiles and caller-calibrated Butler-Volmer reactions, area-normalize the currents, and solve for a common zero-net-current potential within all reaction overpotential supports.",
                  "The API requires the complete declared reaction set, shared clock/temperature/reference, area partition, quasi-steady state and negligible-ohmic-drop review. It returns instantaneous partial reaction currents only; no time integration, dynamic stability, activity/kinetic fitting or total corrosion qualification is included."
                ],
                "notes": [
                  "At each declared knot, the solver balances caller-calibrated anodic-positive reaction currents over the common overpotential support.",
                  "This is conditional on the complete caller reaction set, area partition, shared potential, negligible ohmic drop and quasi-steady review. It does not infer activities, kinetic parameters, dynamic stability, charge integral, total metal loss or corrosion acceptance."
                ],
                "context": {
                  "asset_id": "synthetic-loop",
                  "location_id": "synthetic-crevice",
                  "time_basis": "synthetic-elapsed-seconds",
                  "evidence": [
                    {
                      "source_id": "synthetic-activity-source",
                      "origin": "synthetic",
                      "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-standard-potential-source",
                      "origin": "synthetic",
                      "citation": "Synthetic standard-potential fixture for API wiring only.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-fe-kinetics",
                      "origin": "synthetic",
                      "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                      "license_id": null,
                      "sha256": null
                    },
                    {
                      "source_id": "synthetic-h-kinetics",
                      "origin": "synthetic",
                      "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                      "license_id": null,
                      "sha256": null
                    }
                  ],
                  "metadata": {}
                },
                "input_digest": "f45047257efed352cd59ff473d57b9372820995614e06cb3cb2281711f5d9c19",
                "source_ids": [
                  "crevice_multireaction_nernst_butler_volmer_balance"
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
              "mixed_potential_result_sha256": "bfd10e812c6f15fbeb586bc86a2bb656870d50a7de638b43093d813a50e500b1",
              "reference_area_m2": 2.0,
              "piecewise_linear_flux_between_knots_reviewed": true,
              "constant_reference_area_reviewed": true,
              "stoichiometric_inward_sign_convention_reviewed": true,
              "computational_use_authorized": true
            },
            "values": {
              "assessment_id": "synthetic-reference-area-transfer",
              "asset_id": "synthetic-loop",
              "location_id": "synthetic-crevice",
              "physical_scope_id": "synthetic-wet-surface",
              "clock_id": "synthetic-elapsed-seconds",
              "reference_area_m2": 2.0,
              "mixed_potential_result_sha256": "bfd10e812c6f15fbeb586bc86a2bb656870d50a7de638b43093d813a50e500b1",
              "mixed_potential_history_sha256": "7ecdba944db6f479dcca09c4956490dd434e8102e30a97505cb6e8e7d70e348a",
              "integration_method": "exact_piecewise_linear_flux_integral_between_declared_knots",
              "area_basis": "constant caller reference area from upstream mixed-potential result",
              "interval_inventory_transfer": [
                {
                  "start_time_s": 0.0,
                  "end_time_s": 30.0,
                  "start_temperature_K": 298.15,
                  "end_temperature_K": 298.15,
                  "reaction_species_transfer": [
                    {
                      "reaction_id": "redox_A",
                      "species_transfer": [
                        {
                          "species_id": "PoolA",
                          "signed_net_transfer_mol": 5.743214457077638e-08,
                          "inward_transfer_mol": 5.743214457077638e-08,
                          "outward_transfer_mol": 0.0,
                          "cumulative_signed_net_transfer_mol": 5.743214457077638e-08,
                          "cumulative_inward_transfer_mol": 5.743214457077638e-08,
                          "cumulative_outward_transfer_mol": 0.0
                        }
                      ]
                    },
                    {
                      "reaction_id": "redox_B",
                      "species_transfer": [
                        {
                          "species_id": "PoolB",
                          "signed_net_transfer_mol": -5.743214457006074e-08,
                          "inward_transfer_mol": 0.0,
                          "outward_transfer_mol": 5.743214457006074e-08,
                          "cumulative_signed_net_transfer_mol": -5.743214457006074e-08,
                          "cumulative_inward_transfer_mol": 0.0,
                          "cumulative_outward_transfer_mol": 5.743214457006074e-08
                        }
                      ]
                    }
                  ]
                },
                {
                  "start_time_s": 30.0,
                  "end_time_s": 60.0,
                  "start_temperature_K": 298.15,
                  "end_temperature_K": 298.15,
                  "reaction_species_transfer": [
                    {
                      "reaction_id": "redox_A",
                      "species_transfer": [
                        {
                          "species_id": "PoolA",
                          "signed_net_transfer_mol": 5.743214457077638e-08,
                          "inward_transfer_mol": 5.743214457077638e-08,
                          "outward_transfer_mol": 0.0,
                          "cumulative_signed_net_transfer_mol": 1.1486428914155276e-07,
                          "cumulative_inward_transfer_mol": 1.1486428914155276e-07,
                          "cumulative_outward_transfer_mol": 0.0
                        }
                      ]
                    },
                    {
                      "reaction_id": "redox_B",
                      "species_transfer": [
                        {
                          "species_id": "PoolB",
                          "signed_net_transfer_mol": -5.743214457006074e-08,
                          "inward_transfer_mol": 0.0,
                          "outward_transfer_mol": 5.743214457006074e-08,
                          "cumulative_signed_net_transfer_mol": -1.1486428914012148e-07,
                          "cumulative_inward_transfer_mol": 0.0,
                          "cumulative_outward_transfer_mol": 1.1486428914012148e-07
                        }
                      ]
                    }
                  ]
                }
              ],
              "cumulative_inventory_transfer_by_reaction": {
                "redox_A": {
                  "PoolA": {
                    "signed_mol": 1.1486428914155276e-07,
                    "inward_mol": 1.1486428914155276e-07,
                    "outward_mol": 0.0
                  }
                },
                "redox_B": {
                  "PoolB": {
                    "signed_mol": -1.1486428914012148e-07,
                    "inward_mol": 0.0,
                    "outward_mol": 1.1486428914012148e-07
                  }
                }
              },
              "inventory_transfer_sha256": "7bac25fd5ab88c3ac487530ed2a43d1a797815ec6ece6021054ee39fcb4e76de"
            },
            "units": {
              "reference_area_m2": "m2",
              "interval_inventory_transfer[].start_time_s": "s",
              "interval_inventory_transfer[].end_time_s": "s",
              "interval_inventory_transfer[].start_temperature_K": "K",
              "interval_inventory_transfer[].end_temperature_K": "K",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].signed_net_transfer_mol": "mol",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].inward_transfer_mol": "mol",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].outward_transfer_mol": "mol",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_signed_net_transfer_mol": "mol",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_inward_transfer_mol": "mol",
              "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_outward_transfer_mol": "mol",
              "cumulative_inventory_transfer_by_reaction.*.*.signed_mol": "mol",
              "cumulative_inventory_transfer_by_reaction.*.*.inward_mol": "mol",
              "cumulative_inventory_transfer_by_reaction.*.*.outward_mol": "mol"
            },
            "assumptions": [
              "Only a computed digest-pinned crevice mixed-potential result is accepted, and the exact upstream reference-area basis is reused.",
              "Between adjacent declared knots, each species flux is reconstructed as a straight line and integrated exactly; this policy requires explicit caller review and does not establish the true within-interval kinetics.",
              "The output is an area-scaled species transfer ledger and is not bulk concentration, metal loss, corrosion rate, protection, risk or acceptance."
            ],
            "notes": [
              "Signed branch species flux is integrated exactly for the caller-reviewed linear reconstruction between supplied knots; positive values follow the upstream inward-species sign convention.",
              "The result is a surface-area-scaled transfer amount, not a concentration, bulk inventory, metal-loss depth, corrosion rate, phase state or acceptance finding. Transport volume, stoichiometric phase selection and subsequent material-loss interpretation remain the receiving module's responsibility."
            ],
            "context": {
              "asset_id": "synthetic-loop",
              "location_id": "synthetic-crevice",
              "time_basis": "synthetic-elapsed-seconds",
              "evidence": [
                {
                  "source_id": "synthetic-activity-source",
                  "origin": "synthetic",
                  "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
                  "license_id": null,
                  "sha256": null
                },
                {
                  "source_id": "synthetic-standard-potential-source",
                  "origin": "synthetic",
                  "citation": "Synthetic standard-potential fixture for API wiring only.",
                  "license_id": null,
                  "sha256": null
                },
                {
                  "source_id": "synthetic-fe-kinetics",
                  "origin": "synthetic",
                  "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
                  "license_id": null,
                  "sha256": null
                },
                {
                  "source_id": "synthetic-h-kinetics",
                  "origin": "synthetic",
                  "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
                  "license_id": null,
                  "sha256": null
                }
              ],
              "metadata": {}
            },
            "input_digest": "38d45f4ad31014fa1ba72c3e6a570a39b99e146d42b5778a3789a7d54452e921",
            "source_ids": [
              "crevice_mixed_potential_species_flux_interval_inventory_transfer"
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
          "transfer_result_sha256": "5cbd22fcbf62c9217be667ad1ef166805ccf3faa87fa00e85ca51fec0ac54ef0",
          "initial_inventory": [
            {
              "species_id": "PoolA",
              "initial_amount_mol": 0.01
            },
            {
              "species_id": "PoolB",
              "initial_amount_mol": 0.02
            }
          ],
          "liquid_volume_history": [
            {
              "time_s": 0.0,
              "liquid_volume_m3": 0.001
            },
            {
              "time_s": 30.0,
              "liquid_volume_m3": 0.001
            },
            {
              "time_s": 60.0,
              "liquid_volume_m3": 0.001
            }
          ],
          "complete_species_inventory_reviewed": true,
          "all_other_sources_and_sinks_included_reviewed": true,
          "well_mixed_single_volume_reviewed": true,
          "fixed_basis_and_interval_transfer_mapping_reviewed": true,
          "computational_use_authorized": true
        },
        "values": {
          "assessment_id": "synthetic-well-mixed-composition",
          "asset_id": "synthetic-loop",
          "location_id": "synthetic-crevice",
          "physical_scope_id": "synthetic-wet-surface",
          "clock_id": "synthetic-elapsed-seconds",
          "reference_area_m2": 2.0,
          "transfer_result_sha256": "5cbd22fcbf62c9217be667ad1ef166805ccf3faa87fa00e85ca51fec0ac54ef0",
          "transfer_inventory_sha256": "7bac25fd5ab88c3ac487530ed2a43d1a797815ec6ece6021054ee39fcb4e76de",
          "volume_history_policy": "caller_supplied_exact_time_knots_no_interpolation",
          "inventory_balance_policy": "initial_moles_plus_all_reaction_species_transfer_on_reference_area",
          "composition_history": [
            {
              "time_s": 0.0,
              "temperature_K": 298.15,
              "liquid_volume_m3": 0.001,
              "species": [
                {
                  "species_id": "PoolA",
                  "amount_mol": 0.01,
                  "concentration_mol_m3": 10.0
                },
                {
                  "species_id": "PoolB",
                  "amount_mol": 0.02,
                  "concentration_mol_m3": 20.0
                }
              ]
            },
            {
              "time_s": 30.0,
              "temperature_K": 298.15,
              "liquid_volume_m3": 0.001,
              "interval_signed_transfer_mol_by_species": {
                "PoolA": 5.743214457077638e-08,
                "PoolB": -5.743214457006074e-08
              },
              "species": [
                {
                  "species_id": "PoolA",
                  "amount_mol": 0.010000057432144572,
                  "concentration_mol_m3": 10.00005743214457
                },
                {
                  "species_id": "PoolB",
                  "amount_mol": 0.01999994256785543,
                  "concentration_mol_m3": 19.999942567855427
                }
              ]
            },
            {
              "time_s": 60.0,
              "temperature_K": 298.15,
              "liquid_volume_m3": 0.001,
              "interval_signed_transfer_mol_by_species": {
                "PoolA": 5.743214457077638e-08,
                "PoolB": -5.743214457006074e-08
              },
              "species": [
                {
                  "species_id": "PoolA",
                  "amount_mol": 0.010000114864289143,
                  "concentration_mol_m3": 10.000114864289143
                },
                {
                  "species_id": "PoolB",
                  "amount_mol": 0.019999885135710858,
                  "concentration_mol_m3": 19.99988513571086
                }
              ]
            }
          ],
          "composition_history_sha256": "1e8b04509267b70330a8c9a755bdc923b08e30ae0c7d01fafba2deee0adfc09c"
        },
        "units": {
          "composition_history[].time_s": "s",
          "composition_history[].temperature_K": "K",
          "composition_history[].liquid_volume_m3": "m3",
          "composition_history[].species[].amount_mol": "mol",
          "composition_history[].species[].concentration_mol_m3": "mol/m3",
          "composition_history[].interval_signed_transfer_mol_by_species.*": "mol"
        },
        "assumptions": [
          "The digest-pinned upstream flux ledger is area-scaled and mapped directly into caller-declared aqueous species inventories using the caller sign convention.",
          "All affected species need initial mole inventories; all other sources/sinks and the single well-mixed liquid volume are caller-reviewed assumptions.",
          "Concentrations are only mole amounts divided by caller volume at exact knots; no equilibrium, speciation, transport or material-loss law is solved."
        ],
        "notes": [
          "Amounts are propagated by adding the upstream signed transfer ledger to the caller's initial species amounts; concentrations divide by caller-supplied liquid volumes at exact aligned knots.",
          "This is a well-mixed bookkeeping adapter. It does not solve aqueous equilibrium, transport, precipitation, liquid loss, additional source/sink kinetics, or metal wall loss; all non-electrochemical contributions must be included in the caller's declared baseline/other-sink model."
        ],
        "context": {
          "asset_id": "synthetic-loop",
          "location_id": "synthetic-crevice",
          "time_basis": "synthetic-elapsed-seconds",
          "evidence": [
            {
              "source_id": "synthetic-activity-source",
              "origin": "synthetic",
              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-standard-potential-source",
              "origin": "synthetic",
              "citation": "Synthetic standard-potential fixture for API wiring only.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-fe-kinetics",
              "origin": "synthetic",
              "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-h-kinetics",
              "origin": "synthetic",
              "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
              "license_id": null,
              "sha256": null
            }
          ],
          "metadata": {}
        },
        "input_digest": "8347d0a5843c2626535b9afdad0a20e0cc7be5c5b49d5062f45efec87f74835b",
        "source_ids": [
          "crevice_electrochemical_transfer_to_well_mixed_composition_history"
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
      "composition_result_sha256": "d106c4baf736c4adaa62f7713ffdd733376bf5c29e3793da522595f86d211681",
      "mass_action_systems_by_knot": [
        {
          "schema_version": "matintegrity.aqueous_mass_action.v1",
          "assessment_id": "synthetic-aqueous-knot-0",
          "solution_id": "synthetic-well-mixed-pool",
          "temperature_K": 298.15,
          "activity_standard_state": "molarity_1_mol_L",
          "species": [
            {
              "species_id": "PoolA",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            },
            {
              "species_id": "PoolB",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            }
          ],
          "reactions": [
            {
              "reaction_id": "synthetic_pool_exchange",
              "log10_equilibrium_constant": 0.0,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": -1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "constraints": [
            {
              "constraint_id": "synthetic_pool_total",
              "target_mol_L": 0.001,
              "residual_scale_mol_L": 0.001,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": 1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "maximum_iterations": 100,
          "normalized_residual_tolerance": 1e-10,
          "maximum_jacobian_condition_number": 100000000000000.0,
          "local_parameter_covariance": null,
          "local_parameter_covariance_reviewed": false,
          "activity_provider_id": "synthetic-activity-source",
          "activity_provider_revision": "synthetic-1",
          "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
          "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
          "equilibrium_provider_revision": "synthetic-1",
          "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
          "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "complete_aqueous_species_inventory_reviewed": true,
          "reaction_stoichiometry_and_constant_reviewed": true,
          "balance_constraints_and_charge_scope_reviewed": true,
          "fixed_activity_coefficients_and_standard_state_reviewed": true,
          "temperature_and_provider_lineage_reviewed": true,
          "initial_activity_guess_and_solver_tolerance_reviewed": true,
          "single_liquid_phase_and_no_precipitation_reviewed": true,
          "elemental_formula_and_reaction_balance_reviewed": false,
          "evidence": [
            {
              "source_id": "synthetic-activity-source",
              "origin": "synthetic",
              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-aqueous-equilibrium",
              "origin": "synthetic",
              "citation": "Synthetic equilibrium constant for API wiring only; not chemical data.",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "schema_version": "matintegrity.aqueous_mass_action.v1",
          "assessment_id": "synthetic-aqueous-knot-1",
          "solution_id": "synthetic-well-mixed-pool",
          "temperature_K": 298.15,
          "activity_standard_state": "molarity_1_mol_L",
          "species": [
            {
              "species_id": "PoolA",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            },
            {
              "species_id": "PoolB",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            }
          ],
          "reactions": [
            {
              "reaction_id": "synthetic_pool_exchange",
              "log10_equilibrium_constant": 0.0,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": -1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "constraints": [
            {
              "constraint_id": "synthetic_pool_total",
              "target_mol_L": 0.001,
              "residual_scale_mol_L": 0.001,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": 1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "maximum_iterations": 100,
          "normalized_residual_tolerance": 1e-10,
          "maximum_jacobian_condition_number": 100000000000000.0,
          "local_parameter_covariance": null,
          "local_parameter_covariance_reviewed": false,
          "activity_provider_id": "synthetic-activity-source",
          "activity_provider_revision": "synthetic-1",
          "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
          "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
          "equilibrium_provider_revision": "synthetic-1",
          "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
          "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "complete_aqueous_species_inventory_reviewed": true,
          "reaction_stoichiometry_and_constant_reviewed": true,
          "balance_constraints_and_charge_scope_reviewed": true,
          "fixed_activity_coefficients_and_standard_state_reviewed": true,
          "temperature_and_provider_lineage_reviewed": true,
          "initial_activity_guess_and_solver_tolerance_reviewed": true,
          "single_liquid_phase_and_no_precipitation_reviewed": true,
          "elemental_formula_and_reaction_balance_reviewed": false,
          "evidence": [
            {
              "source_id": "synthetic-activity-source",
              "origin": "synthetic",
              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-aqueous-equilibrium",
              "origin": "synthetic",
              "citation": "Synthetic equilibrium constant for API wiring only; not chemical data.",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "schema_version": "matintegrity.aqueous_mass_action.v1",
          "assessment_id": "synthetic-aqueous-knot-2",
          "solution_id": "synthetic-well-mixed-pool",
          "temperature_K": 298.15,
          "activity_standard_state": "molarity_1_mol_L",
          "species": [
            {
              "species_id": "PoolA",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            },
            {
              "species_id": "PoolB",
              "charge_number": 0,
              "activity_coefficient": 1.0,
              "initial_activity": 0.001,
              "elemental_composition": null
            }
          ],
          "reactions": [
            {
              "reaction_id": "synthetic_pool_exchange",
              "log10_equilibrium_constant": 0.0,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": -1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "constraints": [
            {
              "constraint_id": "synthetic_pool_total",
              "target_mol_L": 0.001,
              "residual_scale_mol_L": 0.001,
              "terms": [
                {
                  "species_id": "PoolA",
                  "coefficient": 1.0
                },
                {
                  "species_id": "PoolB",
                  "coefficient": 1.0
                }
              ]
            }
          ],
          "maximum_iterations": 100,
          "normalized_residual_tolerance": 1e-10,
          "maximum_jacobian_condition_number": 100000000000000.0,
          "local_parameter_covariance": null,
          "local_parameter_covariance_reviewed": false,
          "activity_provider_id": "synthetic-activity-source",
          "activity_provider_revision": "synthetic-1",
          "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
          "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
          "equilibrium_provider_revision": "synthetic-1",
          "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
          "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "complete_aqueous_species_inventory_reviewed": true,
          "reaction_stoichiometry_and_constant_reviewed": true,
          "balance_constraints_and_charge_scope_reviewed": true,
          "fixed_activity_coefficients_and_standard_state_reviewed": true,
          "temperature_and_provider_lineage_reviewed": true,
          "initial_activity_guess_and_solver_tolerance_reviewed": true,
          "single_liquid_phase_and_no_precipitation_reviewed": true,
          "elemental_formula_and_reaction_balance_reviewed": false,
          "evidence": [
            {
              "source_id": "synthetic-activity-source",
              "origin": "synthetic",
              "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
              "license_id": null,
              "sha256": null
            },
            {
              "source_id": "synthetic-aqueous-equilibrium",
              "origin": "synthetic",
              "citation": "Synthetic equilibrium constant for API wiring only; not chemical data.",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "composition_derived_constraint_ids": [
        "synthetic_pool_total"
      ],
      "zero_concentration_initial_activity_guess": null,
      "composition_mapping_and_constraint_basis_reviewed": true,
      "composition_derived_constraint_semantics_reviewed": true,
      "zero_concentration_seed_is_numerical_only_reviewed": true,
      "each_temperature_specific_parameter_set_reviewed": true,
      "no_automatic_phase_change_or_kinetic_interpretation_reviewed": true,
      "computational_use_authorized": true
    },
    "values": {
      "assessment_id": "synthetic-crevice-aqueous-speciation-history",
      "asset_id": "synthetic-loop",
      "location_id": "synthetic-crevice",
      "physical_scope_id": "synthetic-wet-surface",
      "clock_id": "synthetic-elapsed-seconds",
      "composition_result_sha256": "d106c4baf736c4adaa62f7713ffdd733376bf5c29e3793da522595f86d211681",
      "composition_history_sha256": "1e8b04509267b70330a8c9a755bdc923b08e30ae0c7d01fafba2deee0adfc09c",
      "activity_standard_state": "1 mol/L",
      "concentration_conversion": "mol/m3 divided by 1000 = mol/L",
      "composition_derived_constraint_ids": [
        "synthetic_pool_total"
      ],
      "constraint_target_policy": "rebuild_only_explicitly_selected_constraint_targets_from_current_composition; preserve_all_other_caller_targets",
      "temperature_policy": "one_caller_parameter_system_per_exact_composition_knot",
      "knot_results": [
        {
          "time_s": 0.0,
          "temperature_K": 298.15,
          "aqueous_system_input_sha256": "b4c89d39e82937d29ba0a760ef3d9afb99616ec27ad22c6670a6ef484a39584d",
          "status": "computed",
          "values": {
            "assessment_id": "synthetic-aqueous-knot-0-knot-0s",
            "solution_id": "synthetic-well-mixed-pool",
            "temperature_K": 298.15,
            "activity_standard_state": "molarity_1_mol_L",
            "activity_provider_id": "synthetic-activity-source",
            "activity_provider_revision": "synthetic-1",
            "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
            "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
            "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
            "equilibrium_provider_revision": "synthetic-1",
            "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
            "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
            "input_digest": "b4c89d39e82937d29ba0a760ef3d9afb99616ec27ad22c6670a6ef484a39584d",
            "solver_id": "damped_newton_log_activity_v1",
            "unknown_count": 2,
            "equation_count": 2,
            "structural_equation_rank": 2,
            "maximum_jacobian_condition_number": 100000000000000.0,
            "iterations": 6,
            "initial_normalized_residual_norm": 0.693147180559945,
            "final_normalized_residual_norm": 3.469446951953614e-15,
            "jacobian_rank": 2,
            "jacobian_condition_number": 15.000000000388242,
            "termination_reason": "residual_tolerance_reached",
            "accepted_steps": [
              {
                "iteration": 0,
                "accepted_damping": 0.5,
                "residual_norm": 0.41718486175552905
              },
              {
                "iteration": 1,
                "accepted_damping": 0.5,
                "residual_norm": 0.320526379068882
              },
              {
                "iteration": 2,
                "accepted_damping": 1.0,
                "residual_norm": 0.11408948423434831
              },
              {
                "iteration": 3,
                "accepted_damping": 1.0,
                "residual_norm": 0.00021584561099227684
              },
              {
                "iteration": 4,
                "accepted_damping": 1.0,
                "residual_norm": 7.764934528697864e-10
              },
              {
                "iteration": 5,
                "accepted_damping": 1.0,
                "residual_norm": 3.469446951953614e-15
              }
            ],
            "normalized_residual_norm": 3.469446951953614e-15,
            "species": [
              {
                "species_id": "PoolA",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              },
              {
                "species_id": "PoolB",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              }
            ],
            "constraint_closure": [
              {
                "constraint_id": "synthetic_pool_total",
                "target_mol_L": 0.03,
                "reconstructed_mol_L": 0.029999999999999995,
                "residual_mol_L": -3.469446951953614e-18,
                "normalized_residual": -3.469446951953614e-15,
                "scale_mol_L": 0.001
              }
            ],
            "reaction_closure": [
              {
                "reaction_id": "synthetic_pool_exchange",
                "charge_stoichiometric_residual": 0.0,
                "elemental_stoichiometric_residuals": null,
                "residual_ln": 0.0
              }
            ],
            "charge_balance_is_user_declared": true,
            "reaction_charge_conservation_checked": true,
            "elemental_balance_checked": false,
            "elemental_formula_and_reaction_balance_reviewed": false,
            "activity_coefficients_are_fixed": true,
            "aqueous_liquid_only": true,
            "local_sensitivity_status": "computed",
            "local_sensitivities": {
              "method": "implicit_derivative_of_converged_log_activity_system",
              "jacobian_condition_number": 14.999999999999996,
              "parameter_order": [
                {
                  "kind": "log10_equilibrium_constant",
                  "id": "synthetic_pool_exchange",
                  "unit": "1"
                },
                {
                  "kind": "constraint_target",
                  "id": "synthetic_pool_total",
                  "unit": "mol/L"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolA",
                  "unit": "1"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolB",
                  "unit": "1"
                }
              ],
              "species": [
                {
                  "species_id": "PoolA",
                  "d_ln_activity_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    -0.5,
                    0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    -0.01726938819745534,
                    0.49999999999999994,
                    -0.007499999999999999,
                    0.007499999999999999
                  ]
                },
                {
                  "species_id": "PoolB",
                  "d_ln_activity_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    -0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    0.01726938819745534,
                    0.5000000000000001,
                    0.007499999999999999,
                    -0.007499999999999999
                  ]
                }
              ]
            },
            "local_sensitivity_covariance": {
              "status": "not_requested"
            }
          },
          "notes": [
            "Activities use the declared 1 mol/L standard state and caller-supplied fixed activity coefficients; the square user reaction/constraint system is solved in log-activity coordinates. Signed reaction charge balance is checked, and complete caller elemental formulas enable per-reaction elemental conservation checks.",
            "Only the declared single aqueous liquid phase is represented. No automatic water balance, ionic strength iteration, gas-liquid equilibrium, precipitation, kinetic response, corrosion rate, or acceptance is inferred.",
            "Local sensitivities are implicit derivatives at the computed state for log10(K), declared constraint targets and fixed activity coefficients. They are not uncertainty intervals, covariance propagation, global response bounds or model validation."
          ]
        },
        {
          "time_s": 30.0,
          "temperature_K": 298.15,
          "aqueous_system_input_sha256": "9d609eabee4dd2b2450b20b279bfda850205535f9923b2c421b6cf7d7978c1ee",
          "status": "computed",
          "values": {
            "assessment_id": "synthetic-aqueous-knot-1-knot-30s",
            "solution_id": "synthetic-well-mixed-pool",
            "temperature_K": 298.15,
            "activity_standard_state": "molarity_1_mol_L",
            "activity_provider_id": "synthetic-activity-source",
            "activity_provider_revision": "synthetic-1",
            "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
            "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
            "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
            "equilibrium_provider_revision": "synthetic-1",
            "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
            "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
            "input_digest": "9d609eabee4dd2b2450b20b279bfda850205535f9923b2c421b6cf7d7978c1ee",
            "solver_id": "damped_newton_log_activity_v1",
            "unknown_count": 2,
            "equation_count": 2,
            "structural_equation_rank": 2,
            "maximum_jacobian_condition_number": 100000000000000.0,
            "iterations": 6,
            "initial_normalized_residual_norm": 0.6931385657506288,
            "final_normalized_residual_norm": 3.469446951953614e-15,
            "jacobian_rank": 2,
            "jacobian_condition_number": 15.000000000388207,
            "termination_reason": "residual_tolerance_reached",
            "accepted_steps": [
              {
                "iteration": 0,
                "accepted_damping": 0.5,
                "residual_norm": 0.41717527742298266
              },
              {
                "iteration": 1,
                "accepted_damping": 0.5,
                "residual_norm": 0.32051882531369813
              },
              {
                "iteration": 2,
                "accepted_damping": 1.0,
                "residual_norm": 0.11408661622485522
              },
              {
                "iteration": 3,
                "accepted_damping": 1.0,
                "residual_norm": 0.00021583478653289245
              },
              {
                "iteration": 4,
                "accepted_damping": 1.0,
                "residual_norm": 7.764136555898915e-10
              },
              {
                "iteration": 5,
                "accepted_damping": 1.0,
                "residual_norm": 3.469446951953614e-15
              }
            ],
            "normalized_residual_norm": 3.469446951953614e-15,
            "species": [
              {
                "species_id": "PoolA",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              },
              {
                "species_id": "PoolB",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              }
            ],
            "constraint_closure": [
              {
                "constraint_id": "synthetic_pool_total",
                "target_mol_L": 0.03,
                "reconstructed_mol_L": 0.029999999999999995,
                "residual_mol_L": -3.469446951953614e-18,
                "normalized_residual": -3.469446951953614e-15,
                "scale_mol_L": 0.001
              }
            ],
            "reaction_closure": [
              {
                "reaction_id": "synthetic_pool_exchange",
                "charge_stoichiometric_residual": 0.0,
                "elemental_stoichiometric_residuals": null,
                "residual_ln": 0.0
              }
            ],
            "charge_balance_is_user_declared": true,
            "reaction_charge_conservation_checked": true,
            "elemental_balance_checked": false,
            "elemental_formula_and_reaction_balance_reviewed": false,
            "activity_coefficients_are_fixed": true,
            "aqueous_liquid_only": true,
            "local_sensitivity_status": "computed",
            "local_sensitivities": {
              "method": "implicit_derivative_of_converged_log_activity_system",
              "jacobian_condition_number": 14.999999999999996,
              "parameter_order": [
                {
                  "kind": "log10_equilibrium_constant",
                  "id": "synthetic_pool_exchange",
                  "unit": "1"
                },
                {
                  "kind": "constraint_target",
                  "id": "synthetic_pool_total",
                  "unit": "mol/L"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolA",
                  "unit": "1"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolB",
                  "unit": "1"
                }
              ],
              "species": [
                {
                  "species_id": "PoolA",
                  "d_ln_activity_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    -0.5,
                    0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    -0.01726938819745534,
                    0.49999999999999994,
                    -0.007499999999999999,
                    0.007499999999999999
                  ]
                },
                {
                  "species_id": "PoolB",
                  "d_ln_activity_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    -0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    0.01726938819745534,
                    0.5000000000000001,
                    0.007499999999999999,
                    -0.007499999999999999
                  ]
                }
              ]
            },
            "local_sensitivity_covariance": {
              "status": "not_requested"
            }
          },
          "notes": [
            "Activities use the declared 1 mol/L standard state and caller-supplied fixed activity coefficients; the square user reaction/constraint system is solved in log-activity coordinates. Signed reaction charge balance is checked, and complete caller elemental formulas enable per-reaction elemental conservation checks.",
            "Only the declared single aqueous liquid phase is represented. No automatic water balance, ionic strength iteration, gas-liquid equilibrium, precipitation, kinetic response, corrosion rate, or acceptance is inferred.",
            "Local sensitivities are implicit derivatives at the computed state for log10(K), declared constraint targets and fixed activity coefficients. They are not uncertainty intervals, covariance propagation, global response bounds or model validation."
          ]
        },
        {
          "time_s": 60.0,
          "temperature_K": 298.15,
          "aqueous_system_input_sha256": "731ac4bc86f75228bee13ae2fdd121d6812a50ac440914649ad5aec94d1cca94",
          "status": "computed",
          "values": {
            "assessment_id": "synthetic-aqueous-knot-2-knot-60s",
            "solution_id": "synthetic-well-mixed-pool",
            "temperature_K": 298.15,
            "activity_standard_state": "molarity_1_mol_L",
            "activity_provider_id": "synthetic-activity-source",
            "activity_provider_revision": "synthetic-1",
            "activity_configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
            "activity_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
            "equilibrium_provider_id": "synthetic-aqueous-equilibrium",
            "equilibrium_provider_revision": "synthetic-1",
            "equilibrium_configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
            "equilibrium_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
            "input_digest": "731ac4bc86f75228bee13ae2fdd121d6812a50ac440914649ad5aec94d1cca94",
            "solver_id": "damped_newton_log_activity_v1",
            "unknown_count": 2,
            "equation_count": 2,
            "structural_equation_rank": 2,
            "maximum_jacobian_condition_number": 100000000000000.0,
            "iterations": 6,
            "initial_normalized_residual_norm": 0.6931299509660502,
            "final_normalized_residual_norm": 3.469446951953614e-15,
            "jacobian_rank": 2,
            "jacobian_condition_number": 15.000000000388162,
            "termination_reason": "residual_tolerance_reached",
            "accepted_steps": [
              {
                "iteration": 0,
                "accepted_damping": 0.5,
                "residual_norm": 0.4171656931999737
              },
              {
                "iteration": 1,
                "accepted_damping": 0.5,
                "residual_norm": 0.3205112716543404
              },
              {
                "iteration": 2,
                "accepted_damping": 1.0,
                "residual_norm": 0.11408374826064882
              },
              {
                "iteration": 3,
                "accepted_damping": 1.0,
                "residual_norm": 0.00021582396252800562
              },
              {
                "iteration": 4,
                "accepted_damping": 1.0,
                "residual_norm": 7.763338583099966e-10
              },
              {
                "iteration": 5,
                "accepted_damping": 1.0,
                "residual_norm": 3.469446951953614e-15
              }
            ],
            "normalized_residual_norm": 3.469446951953614e-15,
            "species": [
              {
                "species_id": "PoolA",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              },
              {
                "species_id": "PoolB",
                "charge_number": 0,
                "elemental_composition": null,
                "activity_coefficient": 1.0,
                "dimensionless_activity": 0.014999999999999998,
                "concentration_mol_L": 0.014999999999999998
              }
            ],
            "constraint_closure": [
              {
                "constraint_id": "synthetic_pool_total",
                "target_mol_L": 0.03,
                "reconstructed_mol_L": 0.029999999999999995,
                "residual_mol_L": -3.469446951953614e-18,
                "normalized_residual": -3.469446951953614e-15,
                "scale_mol_L": 0.001
              }
            ],
            "reaction_closure": [
              {
                "reaction_id": "synthetic_pool_exchange",
                "charge_stoichiometric_residual": 0.0,
                "elemental_stoichiometric_residuals": null,
                "residual_ln": 0.0
              }
            ],
            "charge_balance_is_user_declared": true,
            "reaction_charge_conservation_checked": true,
            "elemental_balance_checked": false,
            "elemental_formula_and_reaction_balance_reviewed": false,
            "activity_coefficients_are_fixed": true,
            "aqueous_liquid_only": true,
            "local_sensitivity_status": "computed",
            "local_sensitivities": {
              "method": "implicit_derivative_of_converged_log_activity_system",
              "jacobian_condition_number": 14.999999999999996,
              "parameter_order": [
                {
                  "kind": "log10_equilibrium_constant",
                  "id": "synthetic_pool_exchange",
                  "unit": "1"
                },
                {
                  "kind": "constraint_target",
                  "id": "synthetic_pool_total",
                  "unit": "mol/L"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolA",
                  "unit": "1"
                },
                {
                  "kind": "ln_activity_coefficient",
                  "id": "PoolB",
                  "unit": "1"
                }
              ],
              "species": [
                {
                  "species_id": "PoolA",
                  "d_ln_activity_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    -1.151292546497023,
                    33.333333333333336,
                    -0.5,
                    0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    -0.01726938819745534,
                    0.49999999999999994,
                    -0.007499999999999999,
                    0.007499999999999999
                  ]
                },
                {
                  "species_id": "PoolB",
                  "d_ln_activity_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    0.5
                  ],
                  "d_ln_concentration_d_parameter": [
                    1.151292546497023,
                    33.33333333333334,
                    0.5,
                    -0.5
                  ],
                  "d_concentration_mol_L_d_parameter": [
                    0.01726938819745534,
                    0.5000000000000001,
                    0.007499999999999999,
                    -0.007499999999999999
                  ]
                }
              ]
            },
            "local_sensitivity_covariance": {
              "status": "not_requested"
            }
          },
          "notes": [
            "Activities use the declared 1 mol/L standard state and caller-supplied fixed activity coefficients; the square user reaction/constraint system is solved in log-activity coordinates. Signed reaction charge balance is checked, and complete caller elemental formulas enable per-reaction elemental conservation checks.",
            "Only the declared single aqueous liquid phase is represented. No automatic water balance, ionic strength iteration, gas-liquid equilibrium, precipitation, kinetic response, corrosion rate, or acceptance is inferred.",
            "Local sensitivities are implicit derivatives at the computed state for log10(K), declared constraint targets and fixed activity coefficients. They are not uncertainty intervals, covariance propagation, global response bounds or model validation."
          ]
        }
      ],
      "knot_results_sha256": "53c1b6303a065c33a0acfd115661b62912357d0d053b5a5e86e459f396fda8ed",
      "computed_knot_count": 3
    },
    "units": {
      "knot_results[].time_s": "s",
      "knot_results[].temperature_K": "K",
      "knot_results[].values.species.concentration_mol_L": "mol/L",
      "knot_results[].values.species.dimensionless_activity": "1",
      "knot_results[].values.constraint_closure.residual_mol_L": "mol/L"
    },
    "assumptions": [
      "Every composition knot binds to a caller-supplied aqueous reaction/constraint network and exact-temperature parameter set.",
      "The transfer composition is in mol/m3 and is converted to mol/L; fixed activity coefficients map concentrations to positive dimensionless initial activity guesses under a 1 mol/L standard state.",
      "Only explicitly caller-selected linear constraint IDs are rebuilt from the current composition; unselected targets such as a reviewed zero-charge condition are preserved. The network is solved as a single aqueous phase without phase-change or wall-loss inference."
    ],
    "notes": [
      "Each mass-action system is a caller-supplied temperature-specific network. Composition concentrations seed positive activities using fixed gamma values; only constraint IDs explicitly selected by the caller are reconstructed from composition, while all other targets remain unchanged.",
      "The adapter does not infer reactions, equilibrium constants, activity coefficients, constraint meaning or temperature dependence. Precipitation, gas exchange, transport, kinetic sources and wall-loss interpretation remain outside scope."
    ],
    "context": {
      "asset_id": "synthetic-loop",
      "location_id": "synthetic-crevice",
      "time_basis": "synthetic-elapsed-seconds",
      "evidence": [
        {
          "source_id": "synthetic-activity-source",
          "origin": "synthetic",
          "citation": "Synthetic activity fixture for API wiring only; not measured or validated.",
          "license_id": null,
          "sha256": null
        },
        {
          "source_id": "synthetic-standard-potential-source",
          "origin": "synthetic",
          "citation": "Synthetic standard-potential fixture for API wiring only.",
          "license_id": null,
          "sha256": null
        },
        {
          "source_id": "synthetic-fe-kinetics",
          "origin": "synthetic",
          "citation": "Synthetic redox-A Butler-Volmer parameter fixture; not calibrated data.",
          "license_id": null,
          "sha256": null
        },
        {
          "source_id": "synthetic-h-kinetics",
          "origin": "synthetic",
          "citation": "Synthetic redox-B Butler-Volmer parameter fixture; not calibrated data.",
          "license_id": null,
          "sha256": null
        },
        {
          "source_id": "synthetic-aqueous-equilibrium",
          "origin": "synthetic",
          "citation": "Synthetic equilibrium constant for API wiring only; not chemical data.",
          "license_id": null,
          "sha256": null
        }
      ],
      "metadata": {}
    },
    "input_digest": "4a682f85c3d164f6c39196350a99e5b5f43274eeb1b10f3ea906f5ec182736ef",
    "source_ids": [
      "crevice_composition_to_caller_aqueous_mass_action_knot_history"
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
  "mass_action_history_result_sha256": "2f8822fde44e3ce59d015cfc5ae04a2b4d28a73af6e87240b97fee1734408be5",
  "asset_id": "synthetic-loop",
  "location_id": "synthetic-crevice",
  "physical_scope_id": "synthetic-wet-surface",
  "clock_id": "synthetic-elapsed-seconds",
  "reaction_id": "synthetic_pool_redox_B",
  "standard_potential_reference_id": "SHE",
  "reaction_quotient_stoichiometry": {
    "PoolA": -1.0,
    "PoolB": 1.0
  },
  "electron_number": 1,
  "standard_potential_V": [
    0.3,
    0.3,
    0.3
  ],
  "standard_potential_provider_id": "synthetic-standard-potential-source",
  "standard_potential_provider_revision": "synthetic-1",
  "standard_potential_configuration_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
  "standard_potential_record_sha256": "7777777777777777777777777777777777777777777777777777777777777777",
  "redox_reaction_direction_and_electron_number_reviewed": true,
  "activity_standard_state_and_species_mapping_reviewed": true,
  "standard_potential_temperature_history_reviewed": true,
  "local_activity_history_applicability_reviewed": true,
  "potential_only_no_rate_or_acceptance_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-standard-potential-source",
      "origin": "synthetic",
      "citation": "Synthetic standard-potential fixture for API wiring only.",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_mass_action_nernst.py#L155)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
