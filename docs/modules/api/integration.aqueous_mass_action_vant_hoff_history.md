# `integration.aqueous_mass_action_vant_hoff_history`

**목적:** Integrate the van't Hoff relation with caller-supplied reference reaction enthalpy, then solve the existing single-phase aqueous mass-action system independently at aligned temperature knots.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `reaction_enthalpy_standard_state` | 예 | `{"const": "same_as_mass_action_equilibrium_standard_state", "type": "string"}` | 계약·필드 설명 참조 |
| `times_s` | 예 | `{"items": {"type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | s |
| `temperatures_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | K |
| `mass_action_system_at_reference` | 예 | `{"$ref": "#/$defs/AqueousMassActionSystem"}` | 계약·필드 설명 참조 |
| `reaction_enthalpies` | 예 | `{"items": {"$ref": "#/$defs/ReactionEnthalpyReference"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `activity_coefficients_by_knot` | 아니오 | `{"anyOf": [{"items": {"$ref": "#/$defs/ActivityCoefficientKnot"}, "maxItems": 1000, "minItems": 2, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `maximum_absolute_log10_equilibrium_constant` | 아니오 | `{"default": 300.0, "exclusiveMinimum": 0, "maximum": 1000, "type": "number"}` | 계약·필드 설명 참조 |
| `reaction_thermochemistry_temperature_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `constant_reaction_heat_capacity_change_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_dependent_reaction_heat_capacity_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_activity_coefficients_temperature_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_coefficient_temperature_history_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_support_and_time_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousMassActionVanTHoffHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `times_s` | `s` |
| `temperatures_K` | `K` |
| `equilibrium_history[].reaction_log10_equilibrium_constants[].temperature_log10_K` | `1` |
| `equilibrium_history[].calculation.values.species[].concentration_mol_L` | `mol/L` |
| `activity_coefficients_by_knot[].activity_coefficients[]` | `1` |
| `reaction_enthalpy_source_records[].delta_h_reference_J_mol` | `J/mol` |
| `reaction_enthalpy_source_records[].delta_cp_reference_J_mol_K` | `J/(mol K)` |
| `reaction_enthalpy_source_records[].delta_cp_slope_J_mol_K2` | `J/(mol K^2)` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Integrate the van't Hoff relation with caller-supplied reference reaction enthalpy, then solve the existing single-phase aqueous mass-action system independently at aligned temperature knots.
- A reviewed caller-supplied reaction thermochemistry model is required. Optional constant or linearly temperature-dependent reaction heat-capacity models require separate review gates. Activity coefficients are supplied per knot or retained as fixed only after review. No temperature extrapolation, phase discovery, precipitation, kinetics, gas-liquid equilibrium or corrosion validity is inferred.

## 구현 근거·독립 설명

- `caller_vant_hoff_aqueous_mass_action_history`: For each caller-declared temperature knot, integrate the van't Hoff relation using caller-supplied reference log10(K) and reaction enthalpy, optionally with constant or linearly temperature-dependent caller-supplied reaction heat-capacity change over an explicit validity interval. Re-solve the existing single-phase aqueous mass-action system independently at every knot, preserving reaction stoichiometry and balance constraints. Require exact reaction-record coverage, Evidence/source-record lineage, thermochemistry-model and time/temperature reviews, and bounded log10(K). Either consume complete caller-supplied per-knot activity coefficients in exact species order with consistent provider ID/revision/configuration digest and their own evidence/review, or retain reference coefficients only after an explicit fixed-gamma applicability review. Do not infer enthalpy, heat capacity or activity data, extrapolate, discover phases, calculate precipitation or infer corrosion kinetics.
- [IDAES: Equilibrium Constant Forms — van 't Hoff equation](https://idaes-pse.readthedocs.io/en/2.13.0/explanations/components/property_package/general_reactions/equil_constant.html) · `idaes_van_t_hoff_equilibrium_constant`
- [NIST CODATA 2022: molar gas constant](https://physics.nist.gov/cgi-bin/cuu/Value?r%7Csearch_for=R) · `nist_molar_gas_constant`
- [IUPAC Gold Book: standard equilibrium constant](https://goldbook.iupac.org/terms/view/S05915) · `iupac_standard_equilibrium_constant`
- [OECD NEA Thermochemical Database: temperature corrections to thermodynamic data and enthalpy calculations](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb4new_2020-09-02_11-54-56_843.pdf) · `oecd_nea_reaction_heat_capacity_temperature_correction`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.aqueous_mass_action_vant_hoff_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.aqueous_mass_action_vant_hoff_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-aqueous-vant-hoff-history",
  "reference_temperature_K": 298.15,
  "reaction_enthalpy_standard_state": "same_as_mass_action_equilibrium_standard_state",
  "times_s": [
    0.0,
    3600.0
  ],
  "temperatures_K": [
    298.15,
    323.15
  ],
  "mass_action_system_at_reference": {
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
  "reaction_enthalpies": [
    {
      "reaction_id": "dissociation-1",
      "delta_h_reference_J_mol": 12000.0,
      "minimum_valid_temperature_K": 273.15,
      "maximum_valid_temperature_K": 373.15,
      "source_record_id": "synthetic-thermochemistry-dissociation-1",
      "evidence": {
        "source_id": "synthetic-vant-hoff-thermochemistry",
        "origin": "synthetic",
        "citation": "Synthetic reaction enthalpy for API wiring only; not a measured or validated thermochemical value.",
        "license_id": null,
        "sha256": null
      },
      "delta_cp_reference_J_mol_K": 15.0,
      "delta_cp_slope_J_mol_K2": 0.02
    },
    {
      "reaction_id": "dissociation-2",
      "delta_h_reference_J_mol": 14500.0,
      "minimum_valid_temperature_K": 273.15,
      "maximum_valid_temperature_K": 373.15,
      "source_record_id": "synthetic-thermochemistry-dissociation-2",
      "evidence": {
        "source_id": "synthetic-vant-hoff-thermochemistry",
        "origin": "synthetic",
        "citation": "Synthetic reaction enthalpy for API wiring only; not a measured or validated thermochemical value.",
        "license_id": null,
        "sha256": null
      },
      "delta_cp_reference_J_mol_K": 10.0
    },
    {
      "reaction_id": "water-ionization",
      "delta_h_reference_J_mol": 17000.0,
      "minimum_valid_temperature_K": 273.15,
      "maximum_valid_temperature_K": 373.15,
      "source_record_id": "synthetic-thermochemistry-water-ionization",
      "evidence": {
        "source_id": "synthetic-vant-hoff-thermochemistry",
        "origin": "synthetic",
        "citation": "Synthetic reaction enthalpy for API wiring only; not a measured or validated thermochemical value.",
        "license_id": null,
        "sha256": null
      },
      "delta_cp_reference_J_mol_K": 5.0
    }
  ],
  "fixed_activity_coefficients_temperature_applicability_reviewed": false,
  "temperature_support_and_time_mapping_reviewed": true,
  "computational_use_authorized": true,
  "activity_coefficients_by_knot": [
    {
      "activity_coefficients": [
        1.0,
        0.9,
        0.5,
        0.9,
        0.9
      ],
      "source_record_id": "synthetic-gamma-at-reference",
      "evidence": {
        "source_id": "synthetic-temperature-activity-coefficients",
        "origin": "synthetic",
        "citation": "Synthetic activity-coefficient rows for API wiring only; not measured or thermodynamic data.",
        "license_id": null,
        "sha256": null
      },
      "provider_id": "synthetic-gamma-provider",
      "provider_revision": "1",
      "provider_configuration_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    },
    {
      "activity_coefficients": [
        1.0,
        0.92,
        0.54,
        0.92,
        0.92
      ],
      "source_record_id": "synthetic-gamma-at-second-knot",
      "evidence": {
        "source_id": "synthetic-temperature-activity-coefficients",
        "origin": "synthetic",
        "citation": "Synthetic activity-coefficient rows for API wiring only; not measured or thermodynamic data.",
        "license_id": null,
        "sha256": null
      },
      "provider_id": "synthetic-gamma-provider",
      "provider_revision": "1",
      "provider_configuration_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    }
  ],
  "activity_coefficient_temperature_history_reviewed": true,
  "reaction_thermochemistry_temperature_model_reviewed": true,
  "constant_reaction_heat_capacity_change_reviewed": true,
  "temperature_dependent_reaction_heat_capacity_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_vant_hoff_history.py#L126)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
