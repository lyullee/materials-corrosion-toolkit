# `fracture.tabulated_crack_growth_scenario_ensemble`

**목적:** Caller-reviewed weighted complete inputs for the single-curve or curve-family deterministic model preserve joint variation in curve points, geometry, ordered loads, toughness and controls.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.tabulated_crack_growth_scenario_ensemble.v1", "default": "matintegrity.tabulated_crack_growth_scenario_ensemble.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `ensemble_run_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `distribution_definition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sample_design_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios` | 예 | `{"items": {"$ref": "#/$defs/CrackGrowthScenario"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `requested_quantiles` | 예 | `{"items": {"type": "number"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `depth_exceedance_threshold_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `maximum_weight_sum_error` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `full_scenario_inputs_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `dependence_preserved_inside_scenarios` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `normalized_weight_meaning_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `common_physical_scope_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TabulatedCrackGrowthScenarioEnsemble.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `scenario_count` | `1` |
| `weight_sum` | `1` |
| `weighted_mean_final_depth_m` | `m` |
| `weighted_standard_deviation_final_depth_m` | `m` |
| `depth_exceedance_threshold_m` | `m` |
| `model_implied_depth_exceedance_probability` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed weighted complete inputs for the single-curve or curve-family deterministic model preserve joint variation in curve points, geometry, ordered loads, toughness and controls.
- All scenarios must compute before aggregate moments, quantiles or exceedance mass are reported; scenario probabilities and model-form validity are never inferred.

## 구현 근거·독립 설명

- `tabulated_growth_interpolation_derivation`: Preserve a caller-authorized positive da/dN-versus-delta-K table, material condition, environment, stress ratio, frequency, source digest and applicability review. Interpolate linearly only between adjacent points in log(delta K)-log(da/dN) coordinates. For a reviewed nondecreasing geometry-factor table and ordered tensile blocks, integrate dN=da/(da/dN) within the curve support, split at geometry and curve knots, and invert the monotone cycle integral for depth. Keep curve support, maximum-K toughness and declared depth terminations distinct; do not infer a threshold, extrapolate, fit a design curve, model closure or retardation, or create acceptance or failure probability.
- `complete_crack_growth_scenario_ensemble`: Accept two or more caller-reviewed normalized weighted scenarios, each containing a complete deterministic single-curve or curve-family crack-growth input and its own joint source identity and digest. Require a common physical scope while allowing joint changes to individual curve points, curve-family composition, geometry knots, ordered load blocks, toughness and numerical controls. Preserve the canonical digest and result of every complete input. Form weighted moments, discrete inverse-CDF quantiles and declared-depth exceedance mass only when every scenario computes. Never generate, fit, normalize, interpolate between, discard or assign probabilities to scenarios, and never relabel their push-forward mass as a period first-failure probability, FTA basic-event probability, model-form validation, confidence bound or code acceptance result.

확률 의미: `{"model_implied_depth_exceedance_probability": "model_implied_input_uncertainty_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fracture.tabulated_crack_growth_scenario_ensemble"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fracture.tabulated_crack_growth_scenario_ensemble"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.tabulated_crack_growth_scenario_ensemble.v1",
  "ensemble_run_id": "authored-complete-input-ensemble",
  "distribution_definition_id": "authored-discrete-input-mass",
  "sample_design_id": "authored-two-complete-inputs",
  "scenarios": [
    {
      "schema_version": "matintegrity.crack_growth_scenario.v1",
      "scenario_id": "scenario-a",
      "normalized_weight": 0.5,
      "joint_scenario_source_id": "authored-scenario-a",
      "joint_scenario_source_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "growth": {
        "schema_version": "matintegrity.tabulated_crack_growth.v1",
        "assessment_id": "authored-complete-scenario-a",
        "physical_scope_id": "synthetic-crack-front",
        "initial_depth_m": 0.001,
        "terminal_depth_m": 0.004,
        "geometry_depth_m": [
          0.0005,
          0.004
        ],
        "geometry_factor": [
          1.12,
          1.12
        ],
        "blocks": [
          {
            "minimum_stress_Pa": 10000000.0,
            "maximum_stress_Pa": 100000000.0,
            "cycles": 1000.0,
            "frequency_Hz": 1.0
          }
        ],
        "curve": {
          "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
          "curve_id": "authored-complete-curve-a",
          "source_group_id": "authored-validation",
          "material_condition_id": "synthetic-state",
          "environment_id": "synthetic-environment",
          "stress_ratio": 0.1,
          "frequency_Hz": 1.0,
          "delta_k_Pa_sqrt_m": [
            2000000.0,
            40000000.0
          ],
          "crack_growth_m_cycle": [
            8e-10,
            6.4e-06
          ],
          "interpolation": "log_delta_k_log_growth_linear",
          "below_minimum_policy": "out_of_scope",
          "declared_threshold_delta_k_Pa_sqrt_m": null,
          "source_content_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
          "pointwise_computational_use_authorized": true,
          "curve_applicability_reviewed": true,
          "physical_specimen_identity_status": "not_required_for_user_model"
        },
        "maximum_absolute_stress_ratio_difference": 0.0,
        "maximum_relative_frequency_difference": 0.0,
        "fracture_toughness_Pa_sqrt_m": 100000000.0,
        "relative_integration_tolerance": 1e-08,
        "absolute_cycle_tolerance": 1e-06,
        "absolute_depth_tolerance_m": 1e-12,
        "geometry_solution_reviewed": true,
        "load_to_curve_mapping_reviewed": true,
        "toughness_application_reviewed": true,
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "curve_material_environment_mapping_reviewed": true
      }
    },
    {
      "schema_version": "matintegrity.crack_growth_scenario.v1",
      "scenario_id": "scenario-b",
      "normalized_weight": 0.5,
      "joint_scenario_source_id": "authored-scenario-b",
      "joint_scenario_source_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "growth": {
        "schema_version": "matintegrity.tabulated_crack_growth.v1",
        "assessment_id": "authored-complete-scenario-b",
        "physical_scope_id": "synthetic-crack-front",
        "initial_depth_m": 0.001,
        "terminal_depth_m": 0.004,
        "geometry_depth_m": [
          0.0005,
          0.004
        ],
        "geometry_factor": [
          1.12,
          1.2
        ],
        "blocks": [
          {
            "minimum_stress_Pa": 9000000.0,
            "maximum_stress_Pa": 90000000.0,
            "cycles": 1000.0,
            "frequency_Hz": 1.0
          }
        ],
        "curve": {
          "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
          "curve_id": "authored-complete-curve-b",
          "source_group_id": "authored-validation",
          "material_condition_id": "synthetic-state",
          "environment_id": "synthetic-environment",
          "stress_ratio": 0.1,
          "frequency_Hz": 1.0,
          "delta_k_Pa_sqrt_m": [
            2000000.0,
            40000000.0
          ],
          "crack_growth_m_cycle": [
            8e-10,
            8e-06
          ],
          "interpolation": "log_delta_k_log_growth_linear",
          "below_minimum_policy": "out_of_scope",
          "declared_threshold_delta_k_Pa_sqrt_m": null,
          "source_content_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
          "pointwise_computational_use_authorized": true,
          "curve_applicability_reviewed": true,
          "physical_specimen_identity_status": "not_required_for_user_model"
        },
        "maximum_absolute_stress_ratio_difference": 0.0,
        "maximum_relative_frequency_difference": 0.0,
        "fracture_toughness_Pa_sqrt_m": 90000000.0,
        "relative_integration_tolerance": 1e-08,
        "absolute_cycle_tolerance": 1e-06,
        "absolute_depth_tolerance_m": 1e-12,
        "geometry_solution_reviewed": true,
        "load_to_curve_mapping_reviewed": true,
        "toughness_application_reviewed": true,
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "curve_material_environment_mapping_reviewed": true
      }
    }
  ],
  "requested_quantiles": [
    0.25,
    0.5,
    0.9
  ],
  "depth_exceedance_threshold_m": 0.00102,
  "maximum_weight_sum_error": 1e-12,
  "full_scenario_inputs_reviewed": true,
  "dependence_preserved_inside_scenarios": true,
  "normalized_weight_meaning_reviewed": true,
  "common_physical_scope_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crack.py#L1098)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
