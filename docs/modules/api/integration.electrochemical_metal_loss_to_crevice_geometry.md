# `integration.electrochemical_metal_loss_to_crevice_geometry`

**목적:** Only a computed digest-pinned electrochemical metal-loss result with every selected reaction explicitly allocated is accepted.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.electrochemical_crevice_geometry_history.v1", "default": "matintegrity.electrochemical_crevice_geometry_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `metal_loss_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `metal_loss_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_cell_ids` | 아니오 | `{"default": [], "items": {"type": "string"}, "maxItems": 2000, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `initial_cell_aperture_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `reference_cross_section_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reactive_broad_face_count` | 예 | `{"enum": [1, 2], "type": "integer"}` | 계약·필드 설명 참조 |
| `cell_volume_allocations` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ReactionCellVolumeAllocation"}, "maxItems": 32, "type": "array"}` | 계약·필드 설명 참조 |
| `supported_minimum_aperture_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `supported_maximum_aperture_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `reaction_surface_to_slit_face_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cell_volume_allocation_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_volume_conservation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_recession_is_per_combined_reactive_area_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `opposing_face_recession_is_equal_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cell_center_to_face_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_clock_origin_rebasing_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ElectrochemicalCreviceGeometryHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `geometry_states[].elapsed_time_s` | `s` |
| `source_time_origin_s` | `s` |
| `source_to_elapsed_time_s[].source_time_s` | `s` |
| `source_to_elapsed_time_s[].elapsed_time_s` | `s` |
| `geometry_states[].cell_aperture_m` | `m` |
| `geometry_states[].axial_cross_section_m2` | `m2` |
| `geometry_states[].cell_volume_m3` | `m3` |
| `cellwise_signed_metal_volume_m3[].volume_m3` | `m3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only a computed digest-pinned electrochemical metal-loss result with every selected reaction explicitly allocated is accepted.
- Legacy metal-loss results require caller-supplied per-reaction volume fractions at every exact knot; the current-carrying extent bridge instead uses its digest-pinned per-cell volume ledger directly.
- The first supplied source time is mapped to elapsed geometry time zero; a nonzero origin requires explicit caller review and is retained in result lineage.
- Reaction-to-face, allocation, combined-area, cell-center mapping, geometry and computational-use reviews are mandatory; two-face use also requires equal-face recession review.
- The existing planar-slit remap computes sequential geometry only inside caller aperture support. This is not local current prediction or a fully coupled moving-boundary solver.

## 구현 근거·독립 설명

- `electrochemical_metal_loss_to_crevice_geometry`: Require the computed digest-pinned metal-loss AssessmentResult and caller-declared slit geometry. Convert each reaction cumulative signed mass ledger to signed transferred volume using its evidence-linked caller density, distribute that volume over cells using caller-supplied cumulative per-reaction fractions at every exact time knot, and enforce unit fraction sums plus total signed-volume closure. Map the first supplied source time to elapsed geometry time zero; a nonzero source origin requires explicit review and the source-to-elapsed mapping is retained. Divide cell volume by the caller-declared combined reactive wall area and pass the resulting cellwise recession history to the existing sequential aperture remap. Require explicit reaction-to-face, cell allocation, volume conservation, area basis, cell mapping, geometry basis, equal-face (for two-face geometry) and computational-use reviews. No local current distribution, wall-reaction allocation, moving-boundary transport or physical validation is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.electrochemical_metal_loss_to_crevice_geometry"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.electrochemical_metal_loss_to_crevice_geometry"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-electrochemical-crevice-geometry",
  "metal_loss_result": {
    "schema_version": "matintegrity.assessment.v1",
    "model_id": "integration.electrochemical_partial_current_metal_loss",
    "model_version": "1.0.0",
    "status": "computed",
    "inputs": {
      "schema_version": "matintegrity.electrochemical_metal_loss_history.v1",
      "assessment_id": "synthetic-electrochemical-metal-loss",
      "material_condition_id": "synthetic-fe-condition-v1",
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
      "metal_reactions": [
        {
          "reaction_id": "redox_A",
          "metal_species_id": "Fe2+",
          "metal_atoms_per_reaction_extent": 1.0,
          "molar_mass_kg_mol": 0.055845,
          "density_kg_m3": 7870.0,
          "metal_data_provider_id": "synthetic-metal-property-source",
          "metal_data_provider_revision": "synthetic-1",
          "metal_data_record_id": "synthetic-fe-property-record-v1",
          "metal_data_sha256": "c119cb95d01562491d0192c06daaa44222954bbaa9f4183adaeed21bba1d7250",
          "anodic_direction_is_metal_dissolution_reviewed": true,
          "alloy_and_metal_basis_reviewed": true,
          "evidence": [
            {
              "source_id": "synthetic-metal-property-source",
              "origin": "synthetic",
              "citation": "Synthetic metal-property values for API wiring only; not material data.",
              "license_id": null,
              "sha256": "c119cb95d01562491d0192c06daaa44222954bbaa9f4183adaeed21bba1d7250"
            }
          ]
        }
      ],
      "linear_current_reconstruction_reviewed": true,
      "mixed_potential_reference_area_reviewed": true,
      "reaction_to_removed_metal_mapping_reviewed": true,
      "uniform_recession_over_mapped_area_reviewed": true,
      "computational_use_authorized": true
    },
    "values": {
      "assessment_id": "synthetic-electrochemical-metal-loss",
      "material_condition_id": "synthetic-fe-condition-v1",
      "asset_id": "synthetic-loop",
      "location_id": "synthetic-crevice",
      "physical_scope_id": "synthetic-wet-surface",
      "clock_id": "synthetic-elapsed-seconds",
      "mixed_potential_result_sha256": "bfd10e812c6f15fbeb586bc86a2bb656870d50a7de638b43093d813a50e500b1",
      "mixed_potential_history_sha256": "7ecdba944db6f479dcca09c4956490dd434e8102e30a97505cb6e8e7d70e348a",
      "reference_area_m2": 2.0,
      "integration_method": "piecewise_linear_current_density_exact_trapezoid",
      "reaction_to_metal_mapping": [
        {
          "reaction_id": "redox_A",
          "metal_species_id": "Fe2+",
          "metal_atoms_per_reaction_extent": 1.0,
          "molar_mass_kg_mol": 0.055845,
          "density_kg_m3": 7870.0,
          "metal_data_provider_id": "synthetic-metal-property-source",
          "metal_data_provider_revision": "synthetic-1",
          "metal_data_record_id": "synthetic-fe-property-record-v1",
          "metal_data_sha256": "c119cb95d01562491d0192c06daaa44222954bbaa9f4183adaeed21bba1d7250",
          "anodic_direction_is_metal_dissolution_reviewed": true,
          "alloy_and_metal_basis_reviewed": true,
          "evidence": [
            {
              "source_id": "synthetic-metal-property-source",
              "origin": "synthetic",
              "citation": "Synthetic metal-property values for API wiring only; not material data.",
              "license_id": null,
              "sha256": "c119cb95d01562491d0192c06daaa44222954bbaa9f4183adaeed21bba1d7250"
            }
          ]
        }
      ],
      "interval_metal_loss": [
        {
          "start_time_s": 0.0,
          "end_time_s": 30.0,
          "reaction_metal_loss": [
            {
              "reaction_id": "redox_A",
              "metal_species_id": "Fe2+",
              "electron_number": 1,
              "exposed_area_m2": 1.0,
              "anodic_charge_C": 0.0055575537187263204,
              "cathodic_charge_C": 1.6194175451105878e-05,
              "signed_charge_C": 0.005541359543275215,
              "anodic_metal_removal_mol": 5.759998537004221e-08,
              "cathodic_metal_equivalent_mol": 1.6784080123608247e-10,
              "net_metal_removal_mol": 5.743214456880613e-08,
              "anodic_mass_loss_kg": 3.216671182990007e-09,
              "cathodic_metal_equivalent_kg": 9.373069545029024e-12,
              "signed_net_mass_loss_kg": 3.207298113444978e-09,
              "signed_area_average_recession_m": 4.0753470310609634e-13,
              "cumulative": {
                "anodic_charge_C": 0.0055575537187263204,
                "cathodic_charge_C": 1.6194175451105878e-05,
                "signed_charge_C": 0.005541359543275215,
                "anodic_metal_mol": 5.759998537004221e-08,
                "cathodic_metal_mol": 1.6784080123608247e-10,
                "net_metal_removal_mol": 5.743214456880613e-08,
                "anodic_mass_kg": 3.216671182990007e-09,
                "cathodic_mass_kg": 9.373069545029024e-12,
                "signed_mass_loss_kg": 3.207298113444978e-09,
                "signed_recession_m": 4.0753470310609634e-13
              }
            }
          ]
        },
        {
          "start_time_s": 30.0,
          "end_time_s": 60.0,
          "reaction_metal_loss": [
            {
              "reaction_id": "redox_A",
              "metal_species_id": "Fe2+",
              "electron_number": 1,
              "exposed_area_m2": 1.0,
              "anodic_charge_C": 0.0055575537187263204,
              "cathodic_charge_C": 1.6194175451105878e-05,
              "signed_charge_C": 0.005541359543275215,
              "anodic_metal_removal_mol": 5.759998537004221e-08,
              "cathodic_metal_equivalent_mol": 1.6784080123608247e-10,
              "net_metal_removal_mol": 5.743214456880613e-08,
              "anodic_mass_loss_kg": 3.216671182990007e-09,
              "cathodic_metal_equivalent_kg": 9.373069545029024e-12,
              "signed_net_mass_loss_kg": 3.207298113444978e-09,
              "signed_area_average_recession_m": 4.0753470310609634e-13,
              "cumulative": {
                "anodic_charge_C": 0.011115107437452641,
                "cathodic_charge_C": 3.2388350902211756e-05,
                "signed_charge_C": 0.01108271908655043,
                "anodic_metal_mol": 1.1519997074008442e-07,
                "cathodic_metal_mol": 3.3568160247216493e-10,
                "net_metal_removal_mol": 1.1486428913761226e-07,
                "anodic_mass_kg": 6.433342365980014e-09,
                "cathodic_mass_kg": 1.874613909005805e-11,
                "signed_mass_loss_kg": 6.414596226889956e-09,
                "signed_recession_m": 8.150694062121927e-13
              }
            }
          ]
        }
      ],
      "cumulative_metal_loss_by_reaction": {
        "redox_A": {
          "anodic_charge_C": 0.011115107437452641,
          "cathodic_charge_C": 3.2388350902211756e-05,
          "signed_charge_C": 0.01108271908655043,
          "anodic_metal_mol": 1.1519997074008442e-07,
          "cathodic_metal_mol": 3.3568160247216493e-10,
          "net_metal_removal_mol": 1.1486428913761226e-07,
          "anodic_mass_kg": 6.433342365980014e-09,
          "cathodic_mass_kg": 1.874613909005805e-11,
          "signed_mass_loss_kg": 6.414596226889956e-09,
          "signed_recession_m": 8.150694062121927e-13
        }
      },
      "metal_loss_history_sha256": "3de60db1fc862cfa02f5ceec05585b207d3c8dbfb6ed47ef5144426a32174d86"
    },
    "units": {
      "reference_area_m2": "m2",
      "interval_metal_loss[].start_time_s": "s",
      "interval_metal_loss[].end_time_s": "s",
      "interval_metal_loss[].reaction_metal_loss[].anodic_charge_C": "C",
      "interval_metal_loss[].reaction_metal_loss[].cathodic_charge_C": "C",
      "interval_metal_loss[].reaction_metal_loss[].signed_charge_C": "C",
      "interval_metal_loss[].reaction_metal_loss[].anodic_metal_removal_mol": "mol",
      "interval_metal_loss[].reaction_metal_loss[].cathodic_metal_equivalent_mol": "mol",
      "interval_metal_loss[].reaction_metal_loss[].net_metal_removal_mol": "mol",
      "interval_metal_loss[].reaction_metal_loss[].anodic_mass_loss_kg": "kg",
      "interval_metal_loss[].reaction_metal_loss[].cathodic_metal_equivalent_kg": "kg",
      "interval_metal_loss[].reaction_metal_loss[].signed_net_mass_loss_kg": "kg",
      "interval_metal_loss[].reaction_metal_loss[].signed_area_average_recession_m": "m",
      "cumulative_metal_loss_by_reaction.*.signed_recession_m": "m"
    },
    "assumptions": [
      "A digest-pinned computed mixed-potential history is required; branch electron number and exposed area are read from that exact upstream request.",
      "Partial current is integrated using an exact trapezoidal integral under an explicit piecewise-linear between-knot review.",
      "Metal mapping, anodic dissolution direction, alloy basis and uniform area-average recession are caller-reviewed inputs; cathodic-equivalent and signed net quantities remain separately visible."
    ],
    "notes": [
      "Positive mapped anodic reaction extent is caller-declared metal dissolution; cathodic equivalent and signed net transfer are reported separately.",
      "Current density is integrated exactly for the caller-reviewed linear interpolation between upstream time knots and the pinned reference area. Uniform recession is a caller-reviewed area average, not localized attack.",
      "This conversion does not qualify kinetics, infer alloy dissolution selectivity, model films/passivity, or establish corrosion rate acceptance, life, probability or fitness for service."
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
    "input_digest": "e6dd43c2cd09d0e43004f45001fc7cf173a7dfccf9135ff35498f5b810fb0fe9",
    "source_ids": [
      "electrochemical_partial_current_to_metal_loss"
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
  "metal_loss_result_sha256": "072bcfcc5b2bd431ea2a55065cc47a922f4eac4d139b23306a925fae8ed6d30c",
  "geometry_id": "synthetic-two-cell-slit",
  "geometry_source_sha256": "9999999999999999999999999999999999999999999999999999999999999999",
  "cell_widths_m": [
    0.005,
    0.005
  ],
  "initial_cell_aperture_m": [
    0.001,
    0.001
  ],
  "transverse_width_m": 0.1,
  "reference_cross_section_m2": 0.0001,
  "reactive_broad_face_count": 1,
  "cell_volume_allocations": [
    {
      "reaction_id": "redox_A",
      "cumulative_cell_volume_fraction": [
        [
          0.5,
          0.5
        ],
        [
          0.5,
          0.5
        ],
        [
          0.5,
          0.5
        ]
      ]
    }
  ],
  "supported_minimum_aperture_m": 1e-05,
  "supported_maximum_aperture_m": 0.005,
  "reaction_surface_to_slit_face_mapping_reviewed": true,
  "cell_volume_allocation_basis_reviewed": true,
  "reaction_volume_conservation_reviewed": true,
  "wall_recession_is_per_combined_reactive_area_reviewed": true,
  "opposing_face_recession_is_equal_reviewed": false,
  "cell_center_to_face_mapping_reviewed": true,
  "geometry_basis_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_crevice_geometry.py#L196)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
