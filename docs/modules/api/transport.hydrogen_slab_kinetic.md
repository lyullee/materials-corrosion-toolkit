# `transport.hydrogen_slab_kinetic`

**목적:** Planar Fickian lattice transport with fixed independent dilute trap populations, reviewed detailed-balance or independent-frequency kinetics, spatially uniform temperature and declared surface boundaries.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_lattice_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_origin_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `cell_count` | 예 | `{"maximum": 512, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `lattice_site_density_mol_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `initial_lattice_hydrogen_atoms_mol_m3` | 예 | `{"items": {"minimum": 0, "type": "number"}, "type": "array"}` | mol/m³ |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 4096, "minItems": 2, "type": "array"}` | s |
| `uniform_temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | K |
| `lattice_diffusivity_m2_s` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | m²/s |
| `left_boundary` | 예 | `{"$ref": "#/$defs/LatticeBoundary"}` | 계약·필드 설명 참조 |
| `right_boundary` | 예 | `{"$ref": "#/$defs/LatticeBoundary"}` | 계약·필드 설명 참조 |
| `traps` | 아니오 | `{"items": {"$ref": "#/$defs/HydrogenKineticTrap"}, "maxItems": 16, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_supported_lattice_occupancy` | 예 | `{"exclusiveMinimum": 0, "maximum": 1, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_supported_total_trap_to_lattice_site_ratio` | 예 | `{"exclusiveMaximum": 1, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `planar_geometry_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_populations_and_uniform_temperature_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `independent_single_occupancy_and_dilute_trap_regime_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `negligible_stress_gradient_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `detailed_balance_rate_ratio_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `relative_tolerance` | 아니오 | `{"default": 0.0001, "maximum": 0.01, "minimum": 1e-09, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_occupancy_tolerance` | 아니오 | `{"default": 1e-10, "maximum": 0.001, "minimum": 1e-18, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `maximum_step_attempts` | 아니오 | `{"default": 50000, "maximum": 500000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_relative_mass_balance_error` | 아니오 | `{"default": 1e-07, "maximum": 0.01, "minimum": 1e-12, "type": "number"}` | 계약·필드 설명 참조 |
| `store_profiles` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenSlab.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `cell_centers_m` | `m` |
| `final_lattice_hydrogen_atoms_mol_m3` | `mol/m^3` |
| `lattice_mean_hydrogen_atoms_mol_m3` | `mol/m^3` |
| `lattice_profiles_hydrogen_atoms_mol_m3` | `mol/m^3` |
| `hydrogen_inventory_mol_m2` | `mol/m^2` |
| `left_inward_flux_mol_m2_s` | `mol/(m^2*s)` |
| `right_inward_flux_mol_m2_s` | `mol/(m^2*s)` |
| `cumulative_left_exchange_mol_m2` | `mol/m^2` |
| `cumulative_right_exchange_mol_m2` | `mol/m^2` |
| `mass_balance_residual_mol_m2` | `mol/m^2` |
| `relative_mass_balance_error` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Planar Fickian lattice transport with fixed independent dilute trap populations, reviewed detailed-balance or independent-frequency kinetics, spatially uniform temperature and declared surface boundaries.

## 구현 근거·독립 설명

- [Diaz, Alegre, Cuesta and Martinez-Paneda, coupled hydrogen transport and frequency-based trapping kinetics](https://doi.org/10.1016/j.engfracmech.2025.111007) · `diaz_kinetic_transport`
- `hydrogen_slab_fvm_derivation`: Independently derive cell-average conservation on a uniform planar grid. Use half-cell distances at prescribed surfaces, zero normal flux at sealed surfaces, or combine a declared linear transfer or reduced reversible surface-reaction conductance with half-cell diffusion resistance. For each trap either derive the release/capture ratio from a reviewed binding-energy convention or interpolate separately reviewed capture and release histories without overwriting them from temperature. Eliminate each fixed-site backward-Euler kinetic state algebraically, then solve the monotone tridiagonal lattice residual with a bounded Newton iteration. Compare one full step with two half steps for occupancy and boundary-exchange error control; retain the two conservative half steps and their signed surface exchanges. Prescribed histories are piecewise linear, densities fixed, temperature spatially uniform. Check global inventory against surface exchanges; temporal local control does not prove spatial/global accuracy.
- `hydrogen_reduced_surface_reaction_derivation`: At each reviewed temperature knot, evaluate separate Arrhenius limiting absorption and desorption atom-molar flux capacities in log space. Multiply the absorption capacity by the square root of caller-supplied hydrogen fugacity divided by a declared reference fugacity, or use hydrogen partial pressure only after an explicit ideal-gas approximation review. Define the reduced net inward surface flux as J_abs times one minus lattice-surface occupancy minus J_des times lattice-surface occupancy. Algebraically eliminate the surface occupancy against the adjacent half-cell Fickian resistance, preserving signed flux and total atom inventory. This effective one-state boundary is not a full adsorption microkinetic model, a bulk solubility relation or a parameter inference method.
- [SciPy banded linear solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html) · `scipy_banded`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.hydrogen_slab_kinetic"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["transport.hydrogen_slab_kinetic"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "material_condition_id": "synthetic-state",
  "reference_lattice_id": "synthetic-sites",
  "elapsed_time_origin_id": "synthetic-charging-start",
  "thickness_m": 0.001,
  "cell_count": 12,
  "lattice_site_density_mol_m3": 1000.0,
  "initial_lattice_hydrogen_atoms_mol_m3": [
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01
  ],
  "elapsed_time_s": [
    0.0,
    1.0,
    5.0,
    10.0
  ],
  "uniform_temperature_K": [
    300.0,
    300.0,
    320.0,
    330.0
  ],
  "lattice_diffusivity_m2_s": [
    1e-09,
    1e-09,
    2e-09,
    3e-09
  ],
  "left_boundary": {
    "boundary_id": "entry",
    "kind": "prescribed_lattice_concentration",
    "lattice_hydrogen_atoms_mol_m3": [
      0.02,
      0.02,
      0.02,
      0.02
    ],
    "evidence": [
      {
        "source_id": "authored-synthetic",
        "origin": "synthetic",
        "citation": "Authored parameter demonstration"
      }
    ]
  },
  "right_boundary": {
    "boundary_id": "exit",
    "kind": "prescribed_lattice_concentration",
    "lattice_hydrogen_atoms_mol_m3": [
      0.005,
      0.005,
      0.005,
      0.005
    ],
    "evidence": [
      {
        "source_id": "authored-synthetic",
        "origin": "synthetic",
        "citation": "Authored parameter demonstration"
      }
    ]
  },
  "traps": [
    {
      "population": {
        "trap_id": "population-one",
        "material_condition_id": "synthetic-state",
        "reference_lattice_id": "synthetic-sites",
        "site_density_mol_m3": 10.0,
        "binding_energy_J_mol": 5000.0,
        "maximum_supported_occupancy": 0.8,
        "evidence": [
          {
            "source_id": "authored-synthetic",
            "origin": "synthetic",
            "citation": "Authored parameter demonstration"
          }
        ]
      },
      "capture_frequency_per_s": [
        0.2,
        0.2,
        0.3,
        0.4
      ],
      "initial_occupancy": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
      ],
      "rate_evidence": [
        {
          "source_id": "authored-synthetic",
          "origin": "synthetic",
          "citation": "Authored parameter demonstration"
        }
      ]
    }
  ],
  "maximum_supported_lattice_occupancy": 0.01,
  "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
  "planar_geometry_reviewed": true,
  "fixed_populations_and_uniform_temperature_reviewed": true,
  "independent_single_occupancy_and_dilute_trap_regime_reviewed": true,
  "negligible_stress_gradient_reviewed": true,
  "detailed_balance_rate_ratio_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_kinetics.py#L370)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
