# `electrochemistry.restricted_transport_campaign`

**목적:** Caller-calibrated homogeneous ionic reactions and Butler-Volmer tip/wall boundaries on a fixed one-dimensional transport grid; an optional digest-matched activity-coefficient correction multiplies species concentrations in homogeneous rates only when separately reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transport` | 예 | `{"$ref": "#/$defs/RestrictedTransportRequest"}` | 계약·필드 설명 참조 |
| `network` | 예 | `{"$ref": "#/$defs/MassActionNetwork"}` | 계약·필드 설명 참조 |
| `surface_reactions` | 예 | `{"items": {"$ref": "#/$defs/ButlerVolmerReaction"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `wall_surface_reactions` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ButlerVolmerReaction"}, "type": "array"}` | 계약·필드 설명 참조 |
| `wall_surface_composition_and_reference_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `equipotential_wall_and_metal_potential_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `homogeneous_reaction_activity_correction_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `metal_potential_V` | 예 | `{"type": "number"}` | V |
| `common_potential_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_composition_and_reference_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `free_corrosion_zero_current_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `concentration_laws` | 아니오 | `{"additionalProperties": {"$ref": "#/$defs/ConcentrationKineticLaw"}, "type": "object"}` | 계약·필드 설명 참조 |
| `scale_limited_surface_flux` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/ScaleLimitedSurfaceFlux"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `additional_scale_limited_surface_fluxes` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ScaleLimitedSurfaceFlux"}, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ElectrochemicalTransport.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| 가변 구조·진단·증거 결과 | 구현·예제의 `values` 확인 |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-calibrated homogeneous ionic reactions and Butler-Volmer tip/wall boundaries on a fixed one-dimensional transport grid; an optional digest-matched activity-coefficient correction multiplies species concentrations in homogeneous rates only when separately reviewed. Wall kinetics require explicit area-density, local potential and reviewed equipotential-metal assumptions.

## 구현 근거·독립 설명

- `electrochemical_transport_composition`: Compose exact species/charge-ordered homogeneous mass-action sources with Butler-Volmer tip and optional cellwise wall boundary fluxes at imposed potential or an explicitly reviewed zero-current condition. Bind tip and wall reaction configurations to separate digests; wall reactions use cell-local solution potential, caller-supplied area density, and an explicit reviewed equipotential-metal assumption. An optional ideal single-solid split transport request must match the base transport exactly and retain elemental, time and phase-input identities. Do not infer competing phases, protective-scale effects, calibrated CO2 chemistry or qualified metal recession.
- `caller_gamma_corrected_effective_concentration_kinetics`: For a caller-calibrated concentration-basis homogeneous mass-action network, optionally multiply each local species concentration by the matching caller-supplied activity coefficient before evaluating the unchanged forward and reverse concentration-rate expressions. Require an explicit review gate and the exact pinned transport activity provider identity/configuration. Preserve the original rate-constant units and calibration. This effective-concentration correction is not a standard-state transformation, equilibrium solver, automatic kinetic law, or validation of the activity model or rate coefficients.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "electrochemistry.restricted_transport_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["electrochemistry.restricted_transport_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "campaign_id": "synthetic-electrochemistry",
  "transport": {
    "simulation_id": "synthetic-transport",
    "species_ids": [
      "CO2_aq",
      "H2O",
      "H2CO3",
      "H_plus",
      "HCO3_minus",
      "CO3_2minus",
      "OH_minus",
      "Fe_2plus",
      "H2_aq"
    ],
    "length_m": 0.0001,
    "cell_count": 4,
    "cell_widths_m": null,
    "cell_cross_section_m2": null,
    "face_cross_section_m2": null,
    "reference_cross_section_m2": null,
    "variable_area_one_dimensional_reduction_reviewed": false,
    "diffusivity_m2_s": [
      1e-09,
      1e-09,
      1e-09,
      1e-09,
      1e-09,
      1e-09,
      1e-09,
      1e-09,
      1e-09
    ],
    "initial_concentration_mol_m3": [
      [
        1.0,
        1.0,
        1.0,
        1.0
      ],
      [
        55000.0,
        55000.0,
        55000.0,
        55000.0
      ],
      [
        0.01,
        0.01,
        0.01,
        0.01
      ],
      [
        0.001,
        0.001,
        0.001,
        0.001
      ],
      [
        0.001,
        0.001,
        0.001,
        0.001
      ],
      [
        1e-06,
        1e-06,
        1e-06,
        1e-06
      ],
      [
        1e-06,
        1e-06,
        1e-06,
        1e-06
      ],
      [
        0.001,
        0.001,
        0.001,
        0.001
      ],
      [
        0.01,
        0.01,
        0.01,
        0.01
      ]
    ],
    "mouth_concentration_mol_m3": [
      1.0,
      55000.0,
      0.01,
      0.001,
      0.001,
      1e-06,
      1e-06,
      0.001,
      0.01
    ],
    "output_times_s": [
      0.0,
      1e-05,
      0.0001
    ],
    "mouth_concentration_history_mol_m3": null,
    "mouth_history_interpolation_reviewed": false,
    "reaction_provider_id": "synthetic-carbonate:extended",
    "reaction_configuration_sha256": "10335e2fc7283e8d2b20658bb1475f37b1ea7c1e359e629295dd50a836feb2c0",
    "geometry_diffusion_reaction_basis_reviewed": true,
    "charge_numbers": [
      0,
      0,
      0,
      1,
      -1,
      -2,
      -1,
      2,
      0
    ],
    "prescribed_potential_V": [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
    ],
    "migration_temperature_K": 298.15,
    "prescribed_field_migration_reviewed": true,
    "poisson_permittivity_F_m": null,
    "poisson_mouth_potential_V": 0.0,
    "fixed_charge_mol_charge_m3": null,
    "poisson_boundary_and_charge_reviewed": false,
    "tip_surface_provider_id": "synthetic-surface",
    "tip_surface_configuration_sha256": "86d95479c753f4cdfa3970e904654e2b84627ce19fd8b826646069a7da5109aa",
    "tip_surface_flux_basis_reviewed": true,
    "activity_provider_id": null,
    "activity_configuration_sha256": null,
    "activity_chemical_potential_and_tracer_diffusivity_reviewed": false,
    "wall_area_per_volume_m2_m3": null,
    "wall_surface_provider_id": null,
    "wall_surface_configuration_sha256": null,
    "wall_surface_flux_basis_reviewed": false,
    "inventory_absolute_tolerance_mol_m2": 1e-08,
    "inventory_relative_tolerance": 1e-06,
    "solver_relative_tolerance": 1e-07,
    "concentration_absolute_tolerance_mol_m3": 1e-10,
    "integrated_amount_absolute_tolerance_mol_m2": 1e-10,
    "maximum_solver_step_s": null,
    "callbacks_cell_locality_reviewed": true,
    "maximum_dense_state_count": 4000,
    "axial_advection_velocity_m_s": [
      1e-06,
      1e-06,
      1e-06,
      1e-06,
      1e-06
    ],
    "axial_advection_provider_id": "synthetic-mouth-to-tip-flow",
    "axial_advection_configuration_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "axial_advection_and_flow_continuity_reviewed": true
  },
  "network": {
    "network_id": "synthetic-carbonate:extended",
    "species_ids": [
      "CO2_aq",
      "H2O",
      "H2CO3",
      "H_plus",
      "HCO3_minus",
      "CO3_2minus",
      "OH_minus",
      "Fe_2plus",
      "H2_aq"
    ],
    "charge_numbers": [
      0,
      0,
      0,
      1,
      -1,
      -2,
      -1,
      2,
      0
    ],
    "reactions": [
      {
        "reaction_id": "co2_hydration",
        "reactants": {
          "CO2_aq": 1,
          "H2O": 1
        },
        "products": {
          "H2CO3": 1
        },
        "forward_rate_constant": 1e-08,
        "reverse_rate_constant": 1e-08,
        "forward_rate_constant_unit": "(mol/m3)^-1/s",
        "reverse_rate_constant_unit": "1/s",
        "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      {
        "reaction_id": "carbonic_dissociation",
        "reactants": {
          "H2CO3": 1
        },
        "products": {
          "H_plus": 1,
          "HCO3_minus": 1
        },
        "forward_rate_constant": 1e-08,
        "reverse_rate_constant": 1e-08,
        "forward_rate_constant_unit": "1/s",
        "reverse_rate_constant_unit": "(mol/m3)^-1/s",
        "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      {
        "reaction_id": "bicarbonate_dissociation",
        "reactants": {
          "HCO3_minus": 1
        },
        "products": {
          "H_plus": 1,
          "CO3_2minus": 1
        },
        "forward_rate_constant": 1e-08,
        "reverse_rate_constant": 1e-08,
        "forward_rate_constant_unit": "1/s",
        "reverse_rate_constant_unit": "(mol/m3)^-1/s",
        "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      {
        "reaction_id": "water_dissociation",
        "reactants": {
          "H2O": 1
        },
        "products": {
          "H_plus": 1,
          "OH_minus": 1
        },
        "forward_rate_constant": 1e-08,
        "reverse_rate_constant": 1e-08,
        "forward_rate_constant_unit": "1/s",
        "reverse_rate_constant_unit": "(mol/m3)^-1/s",
        "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ],
    "concentration_activity_approximation_and_rates_reviewed": true,
    "elemental_composition": {
      "CO2_aq": {
        "C": 1,
        "O": 2
      },
      "H2O": {
        "H": 2,
        "O": 1
      },
      "H2CO3": {
        "H": 2,
        "C": 1,
        "O": 3
      },
      "H_plus": {
        "H": 1
      },
      "HCO3_minus": {
        "H": 1,
        "C": 1,
        "O": 3
      },
      "CO3_2minus": {
        "C": 1,
        "O": 3
      },
      "OH_minus": {
        "H": 1,
        "O": 1
      },
      "Fe_2plus": {
        "Fe": 1
      },
      "H2_aq": {
        "H": 2
      }
    }
  },
  "surface_reactions": [
    {
      "reaction_id": "synthetic-iron",
      "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "exchange_current_density_A_m2": 1e-06,
      "electron_count": 2,
      "anodic_transfer_coefficient": 0.5,
      "cathodic_transfer_coefficient": 0.5,
      "equilibrium_potential_V": -0.4,
      "temperature_K": 298.15,
      "minimum_overpotential_V": -0.8,
      "maximum_overpotential_V": 0.8,
      "stoichiometric_species_coefficients": {
        "Fe_2plus": 1.0
      },
      "calibration_and_reaction_direction_reviewed": true
    },
    {
      "reaction_id": "synthetic-hydrogen",
      "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "exchange_current_density_A_m2": 1e-06,
      "electron_count": 2,
      "anodic_transfer_coefficient": 0.5,
      "cathodic_transfer_coefficient": 0.5,
      "equilibrium_potential_V": 0.0,
      "temperature_K": 298.15,
      "minimum_overpotential_V": -0.8,
      "maximum_overpotential_V": 0.8,
      "stoichiometric_species_coefficients": {
        "H_plus": 2.0,
        "H2_aq": -1.0
      },
      "calibration_and_reaction_direction_reviewed": true
    }
  ],
  "metal_potential_V": -0.2,
  "common_potential_reference_id": "authored-reference",
  "surface_composition_and_reference_reviewed": true,
  "free_corrosion_zero_current_reviewed": true,
  "concentration_laws": {}
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_numeric.py#L135)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
