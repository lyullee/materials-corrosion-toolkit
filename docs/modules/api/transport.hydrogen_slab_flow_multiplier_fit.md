# `transport.hydrogen_slab_flow_multiplier_fit`

**목적:** One reviewed positive history multiplier, calibrated against signed outward planar hydrogen-atom flow with a predeclared calibration/holdout partition and all other transport inputs fixed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.hydrogen_slab_flow_multiplier_fit.v1", "default": "matintegrity.hydrogen_slab_flow_multiplier_fit.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `fit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_series_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `detector_calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observed_surface` | 예 | `{"enum": ["left", "right"], "type": "string"}` | 계약·필드 설명 참조 |
| `observed_surface_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_slab` | 예 | `{"$ref": "#/$defs/HydrogenSlab"}` | 계약·필드 설명 참조 |
| `physical_surface_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `observation_id` | 예 | `{"items": {"type": "string"}, "maxItems": 4096, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `partition` | 예 | `{"items": {"enum": ["calibration", "holdout"], "type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "type": "array"}` | s |
| `outward_hydrogen_atoms_mol_s` | 예 | `{"items": {"type": "number"}, "type": "array"}` | 계약·필드 설명 참조 |
| `outward_flow_standard_uncertainty_mol_s` | 아니오 | `{"anyOf": [{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `residual_scale_mol_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `parameter_target` | 예 | `{"enum": ["lattice_diffusivity", "trap_capture_frequency", "trap_release_frequency", "left_transfer_coefficient", "right_transfer_coefficient", "left_absorption_capacity", "right_absorption_capacity", "left_desorption_capacity", "right_desorption_capacity"], "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_target_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_multiplier` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `multiplier_bounds` | 예 | `{"maxItems": 2, "minItems": 2, "prefixItems": [{"exclusiveMinimum": 0, "type": "number"}, {"exclusiveMinimum": 0, "type": "number"}], "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_jacobian_norm` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_function_evaluations` | 아니오 | `{"default": 80, "maximum": 1000, "minimum": 5, "type": "integer"}` | 계약·필드 설명 참조 |
| `observation_conversion_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_surface_area_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_inputs_independent_of_holdout_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `one_parameter_scope_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_partition_predeclared` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenSlabFlowMultiplierFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `physical_surface_area_m2` | `m^2` |
| `fitted_multiplier` | `1` |
| `fitted_multiplier_standard_uncertainty` | `1` |
| `fitted_log_multiplier_variance` | `1` |
| `fitted_target_history` | `target-dependent SI units` |
| `calibration_jacobian_norm` | `1` |
| `calibration_flow_rmse_mol_s` | `mol/s` |
| `holdout_flow_rmse_mol_s` | `mol/s` |
| `calibration_normalized_rmse` | `1` |
| `holdout_normalized_rmse` | `1` |
| `forward_relative_mass_balance_error` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One reviewed positive history multiplier, calibrated against signed outward planar hydrogen-atom flow with a predeclared calibration/holdout partition and all other transport inputs fixed.

## 구현 근거·독립 설명

- `hydrogen_slab_flow_multiplier_fit_derivation`: Preserve a reviewed signed outward hydrogen-atom flow series, exact elapsed-time alignment, physical slab area and a predeclared calibration/holdout partition. Apply one positive multiplier to one named complete transport-parameter history while fixing every other initial, geometric, boundary and trap input. Run the conservative planar forward solver inside bounded nonlinear least squares using calibration rows only; evaluate holdout residuals after fitting. Report local log-multiplier sensitivity, conditional uncertainty, boundary activity, the fitted reusable slab contract and its digest. This restricted profile does not establish global identifiability or cover fixed-input, model-form, detector, clock or source-group uncertainty.
- [SciPy nonlinear least-squares and robust residual losses](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html) · `scipy_least_squares`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.hydrogen_slab_flow_multiplier_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["transport.hydrogen_slab_flow_multiplier_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "fit_id": "synthetic-diffusivity-multiplier-fit",
  "observation_series_id": "synthetic-exit-flow",
  "specimen_id": "synthetic-slab",
  "detector_calibration_id": "synthetic-ideal-flow",
  "observed_surface": "right",
  "observed_surface_id": "synthetic-exit",
  "base_slab": {
    "material_condition_id": "synthetic-state",
    "reference_lattice_id": "synthetic-lattice",
    "elapsed_time_origin_id": "synthetic-charging-start",
    "thickness_m": 1.0,
    "cell_count": 2,
    "lattice_site_density_mol_m3": 1.0,
    "initial_lattice_hydrogen_atoms_mol_m3": [
      0.0,
      0.0
    ],
    "elapsed_time_s": [
      0.0,
      0.05,
      0.1,
      0.2,
      0.4,
      0.8
    ],
    "uniform_temperature_K": [
      300.0,
      300.0,
      300.0,
      300.0,
      300.0,
      300.0
    ],
    "lattice_diffusivity_m2_s": [
      0.1,
      0.1,
      0.1,
      0.1,
      0.1,
      0.1
    ],
    "left_boundary": {
      "boundary_id": "synthetic-entry",
      "kind": "prescribed_lattice_concentration",
      "lattice_hydrogen_atoms_mol_m3": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
      ],
      "evidence": [
        {
          "source_id": "authored-synthetic",
          "origin": "synthetic",
          "citation": "Authored planar hydrogen-flow inverse demonstration",
          "license_id": "MIT"
        }
      ]
    },
    "right_boundary": {
      "boundary_id": "synthetic-exit",
      "kind": "prescribed_lattice_concentration",
      "lattice_hydrogen_atoms_mol_m3": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
      ],
      "evidence": [
        {
          "source_id": "authored-synthetic",
          "origin": "synthetic",
          "citation": "Authored planar hydrogen-flow inverse demonstration",
          "license_id": "MIT"
        }
      ]
    },
    "traps": [],
    "maximum_supported_lattice_occupancy": 1.0,
    "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
    "planar_geometry_reviewed": true,
    "fixed_populations_and_uniform_temperature_reviewed": true,
    "independent_single_occupancy_and_dilute_trap_regime_reviewed": true,
    "negligible_stress_gradient_reviewed": true,
    "detailed_balance_rate_ratio_reviewed": true,
    "relative_tolerance": 0.0001,
    "absolute_occupancy_tolerance": 1e-11,
    "maximum_step_s": 0.05
  },
  "physical_surface_area_m2": 1.0,
  "observation_id": [
    "synthetic-point-0",
    "synthetic-point-1",
    "synthetic-point-2",
    "synthetic-point-3",
    "synthetic-point-4",
    "synthetic-point-5"
  ],
  "source_group_id": [
    "synthetic-holdout",
    "synthetic-calibration",
    "synthetic-calibration",
    "synthetic-holdout",
    "synthetic-calibration",
    "synthetic-calibration"
  ],
  "partition": [
    "holdout",
    "calibration",
    "calibration",
    "holdout",
    "calibration",
    "calibration"
  ],
  "elapsed_time_s": [
    0.0,
    0.05,
    0.1,
    0.2,
    0.4,
    0.8
  ],
  "outward_hydrogen_atoms_mol_s": [
    0.0,
    0.0011851797849124796,
    0.00438192242415886,
    0.015022994623681306,
    0.044701638924310554,
    0.1040459450438412
  ],
  "residual_scale_mol_s": 0.001,
  "parameter_target": "lattice_diffusivity",
  "parameter_target_id": "synthetic-lattice",
  "initial_multiplier": 1.0,
  "multiplier_bounds": [
    0.25,
    4.0
  ],
  "minimum_calibration_jacobian_norm": 1e-06,
  "maximum_function_evaluations": 60,
  "observation_conversion_reviewed": true,
  "physical_surface_area_reviewed": true,
  "fixed_inputs_independent_of_holdout_reviewed": true,
  "one_parameter_scope_reviewed": true,
  "holdout_partition_predeclared": true,
  "evidence": [
    {
      "source_id": "authored-synthetic",
      "origin": "synthetic",
      "citation": "Authored planar hydrogen-flow inverse demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_inverse.py#L164)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
