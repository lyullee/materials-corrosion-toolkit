# `fracture.tabulated_curve_family_growth`

**목적:** Caller-reviewed curve family explicitly matched to the assessment target material/environment; each block selects one curve by explicit stress-ratio and relative-frequency tolerances.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.tabulated_curve_family_growth.v1", "default": "matintegrity.tabulated_curve_family_growth.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_depth_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `terminal_depth_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `geometry_depth_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | m |
| `geometry_factor` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `blocks` | 예 | `{"items": {"$ref": "#/$defs/TabulatedGrowthLoadBlock"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `curve_family` | 예 | `{"$ref": "#/$defs/TabulatedCrackGrowthCurveFamily"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `environment_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `curve_family_material_environment_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `fracture_toughness_Pa_sqrt_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa·√m |
| `relative_integration_tolerance` | 예 | `{"exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_cycle_tolerance` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_depth_tolerance_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `geometry_solution_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `load_to_curve_mapping_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `toughness_application_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TabulatedCurveFamilyGrowth.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `final_depth_m` | `m` |
| `cycles_evaluated` | `cycle` |
| `requested_cycles` | `cycle` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed curve family explicitly matched to the assessment target material/environment; each block selects one curve by explicit stress-ratio and relative-frequency tolerances.
- Curve conditions are not interpolated. Missing or tied candidates remain out of scope and every selected curve retains its own delta-K support.

## 구현 근거·독립 설명

- [ASTM E647-24 fatigue crack growth rate test-method scope](https://store.astm.org/standards/e647) · `astm_e647_scope`
- `tabulated_growth_interpolation_derivation`: Preserve a caller-authorized positive da/dN-versus-delta-K table, material condition, environment, stress ratio, frequency, source digest and applicability review. Interpolate linearly only between adjacent points in log(delta K)-log(da/dN) coordinates. For a reviewed nondecreasing geometry-factor table and ordered tensile blocks, integrate dN=da/(da/dN) within the curve support, split at geometry and curve knots, and invert the monotone cycle integral for depth. Keep curve support, maximum-K toughness and declared depth terminations distinct; do not infer a threshold, extrapolate, fit a design curve, model closure or retardation, or create acceptance or failure probability.
- `tabulated_curve_family_selection_derivation`: Require every curve in a family to share one reviewed material condition and environment while retaining unique curve and source identities. For each ordered tensile block, compare stress ratio by absolute difference and frequency by relative difference against caller-declared tolerances. Select only the unique minimum normalized distance inside both tolerances; stop when no candidate or an equal-distance tie remains. Do not interpolate, average or fit across stress ratio, frequency, environment, material condition or source group.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fracture.tabulated_curve_family_growth"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fracture.tabulated_curve_family_growth"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.tabulated_curve_family_growth.v1",
  "assessment_id": "authored-synthetic-family-growth-check",
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
    },
    {
      "minimum_stress_Pa": 50000000.0,
      "maximum_stress_Pa": 100000000.0,
      "cycles": 2000.0,
      "frequency_Hz": 0.1
    }
  ],
  "curve_family": {
    "schema_version": "matintegrity.tabulated_crack_growth_curve_family.v1",
    "family_id": "authored-synthetic-two-condition-family",
    "material_condition_id": "synthetic-state",
    "environment_id": "synthetic-environment",
    "curves": [
      {
        "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
        "curve_id": "authored-R01-f1",
        "source_group_id": "authored-validation",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "stress_ratio": 0.1,
        "frequency_Hz": 1.0,
        "delta_k_Pa_sqrt_m": [
          2000000.0,
          5000000.0,
          10000000.0,
          20000000.0
        ],
        "crack_growth_m_cycle": [
          8e-10,
          1.25e-08,
          1e-07,
          8e-07
        ],
        "interpolation": "log_delta_k_log_growth_linear",
        "below_minimum_policy": "out_of_scope",
        "declared_threshold_delta_k_Pa_sqrt_m": null,
        "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "pointwise_computational_use_authorized": true,
        "curve_applicability_reviewed": true,
        "physical_specimen_identity_status": "not_required_for_user_model"
      },
      {
        "schema_version": "matintegrity.tabulated_crack_growth_curve.v1",
        "curve_id": "authored-R05-f01",
        "source_group_id": "authored-validation",
        "material_condition_id": "synthetic-state",
        "environment_id": "synthetic-environment",
        "stress_ratio": 0.5,
        "frequency_Hz": 0.1,
        "delta_k_Pa_sqrt_m": [
          2000000.0,
          5000000.0,
          10000000.0,
          20000000.0
        ],
        "crack_growth_m_cycle": [
          1.6e-09,
          2.5e-08,
          2e-07,
          1.6e-06
        ],
        "interpolation": "log_delta_k_log_growth_linear",
        "below_minimum_policy": "out_of_scope",
        "declared_threshold_delta_k_Pa_sqrt_m": null,
        "source_content_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "pointwise_computational_use_authorized": true,
        "curve_applicability_reviewed": true,
        "physical_specimen_identity_status": "not_required_for_user_model"
      }
    ],
    "maximum_absolute_stress_ratio_difference": 0.0,
    "maximum_relative_frequency_difference": 0.0,
    "selection_policy": "nearest_within_declared_tolerances",
    "family_applicability_reviewed": true
  },
  "fracture_toughness_Pa_sqrt_m": 100000000.0,
  "relative_integration_tolerance": 1e-08,
  "absolute_cycle_tolerance": 1e-06,
  "absolute_depth_tolerance_m": 1e-12,
  "geometry_solution_reviewed": true,
  "load_to_curve_mapping_reviewed": true,
  "toughness_application_reviewed": true,
  "material_condition_id": "synthetic-state",
  "environment_id": "synthetic-environment",
  "curve_family_material_environment_mapping_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crack.py#L769)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
