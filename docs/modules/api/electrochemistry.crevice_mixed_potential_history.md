# `electrochemistry.crevice_mixed_potential_history`

**목적:** At every aligned knot, evaluate multiple caller-provided Nernst half-cell profiles and caller-calibrated Butler-Volmer reactions, area-normalize the currents, and solve for a common zero-net-current potential within all reaction overpotential supports.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_mixed_potential_history.v1", "default": "matintegrity.crevice_mixed_potential_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `common_reference_electrode_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reactions` | 예 | `{"items": {"$ref": "#/$defs/CreviceMixedPotentialReaction"}, "maxItems": 32, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `quasi_steady_local_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negligible_solution_ohmic_drop_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_electronic_potential_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_set_and_area_partition_complete_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceMixedPotentialHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `source_history_sha256` | `1` |
| `source_inventory_sha256` | `1` |
| `source_activity_history_sha256` | `1` |
| `reference_area_m2` | `m2` |
| `mixed_potential_history[].time_s` | `s` |
| `mixed_potential_history[].temperature_K` | `K` |
| `mixed_potential_history[].mixed_potential_V` | `V` |
| `mixed_potential_history[].net_current_density_on_reference_area_A_m2` | `A/m2` |
| `mixed_potential_history[].reaction_responses[].exposed_area_m2` | `m2` |
| `mixed_potential_history[].reaction_responses[].area_fraction_of_reference` | `1` |
| `mixed_potential_history[].reaction_responses[].equilibrium_potential_V` | `V` |
| `mixed_potential_history[].reaction_responses[].overpotential_V` | `V` |
| `mixed_potential_history[].reaction_responses[].reference_area_signed_current_density_A_m2` | `A/m2` |
| `mixed_potential_history[].reaction_responses[].reference_area_gross_anodic_current_density_A_m2` | `A/m2` |
| `mixed_potential_history[].reaction_responses[].reference_area_gross_cathodic_current_density_A_m2` | `A/m2` |
| `mixed_potential_history[].reaction_responses[].reference_area_species_flux_mol_m2_s.*` | `mol/m2/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- At every aligned knot, evaluate multiple caller-provided Nernst half-cell profiles and caller-calibrated Butler-Volmer reactions, area-normalize the currents, and solve for a common zero-net-current potential within all reaction overpotential supports.
- Branches must carry the same explicit source-history lineage. Raw inventory digests remain available where supplied; aqueous mass-action and B-dot activity-history digests are retained under separate names.
- The API requires the complete declared reaction set, shared clock/temperature/reference, area partition, quasi-steady state and negligible-ohmic-drop review. It returns instantaneous partial reaction currents only; no time integration, dynamic stability, activity/kinetic fitting or total corrosion qualification is included.

## 구현 근거·독립 설명

- `crevice_multireaction_nernst_butler_volmer_balance`: At aligned caller crevice inventory knots, combine two or more digest-pinned half-cell potential profiles and calibrated Butler-Volmer branches, scale each partial current by caller exposed area relative to a reference area, and solve a common zero-net-current potential over the shared calibrated support. Require common clock, temperature and potential reference, complete caller reaction/area review, quasi-steady balance and negligible solution ohmic drop. Return instantaneous branch current and stoichiometric flux without time interpolation/integration, activity or kinetic inference, dynamic stability, total metal loss or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "electrochemistry.crevice_mixed_potential_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["electrochemistry.crevice_mixed_potential_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
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
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crevice_mixed_potential_history.py#L165)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
