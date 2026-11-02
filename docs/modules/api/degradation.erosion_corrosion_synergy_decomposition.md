# `degradation.erosion_corrosion_synergy_decomposition`

**목적:** Pure erosion, pure corrosion and combined loss are caller-supplied matched observations; residual synergy is their signed arithmetic difference.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `rate_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/ErosionCorrosionSynergyInterval"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `wall_thickness_baseline` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/ErosionCorrosionWallThicknessBaseline"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `matched_conditions_and_rate_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `component_definitions_and_accounting_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `interval_clock_and_measurements_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence_and_usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deterministic_rate_bounds_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_thickness_limit_state_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ErosionCorrosionSynergyAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `interval_results[].duration_s` | `s` |
| `interval_results[].pure_erosion_rate_m_s` | `m/s` |
| `interval_results[].pure_corrosion_rate_m_s` | `m/s` |
| `interval_results[].combined_rate_m_s` | `m/s` |
| `interval_results[].residual_synergy_rate_m_s` | `m/s` |
| `interval_results[].pure_erosion_loss_m` | `m` |
| `interval_results[].pure_corrosion_loss_m` | `m` |
| `interval_results[].combined_loss_m` | `m` |
| `interval_results[].residual_synergy_loss_m` | `m` |
| `interval_results[].residual_synergy_rate_lower_bound_m_s` | `m/s` |
| `interval_results[].residual_synergy_rate_upper_bound_m_s` | `m/s` |
| `interval_results[].pure_erosion_loss_lower_bound_m` | `m` |
| `interval_results[].pure_erosion_loss_upper_bound_m` | `m` |
| `interval_results[].pure_corrosion_loss_lower_bound_m` | `m` |
| `interval_results[].pure_corrosion_loss_upper_bound_m` | `m` |
| `interval_results[].combined_loss_lower_bound_m` | `m` |
| `interval_results[].combined_loss_upper_bound_m` | `m` |
| `interval_results[].residual_synergy_loss_lower_bound_m` | `m` |
| `interval_results[].residual_synergy_loss_upper_bound_m` | `m` |
| `interval_results[].erosion_accelerated_corrosion_rate_lower_bound_m_s` | `m/s` |
| `interval_results[].erosion_accelerated_corrosion_rate_upper_bound_m_s` | `m/s` |
| `interval_results[].corrosion_accelerated_erosion_rate_lower_bound_m_s` | `m/s` |
| `interval_results[].corrosion_accelerated_erosion_rate_upper_bound_m_s` | `m/s` |
| `interval_results[].erosion_accelerated_corrosion_loss_lower_bound_m` | `m` |
| `interval_results[].erosion_accelerated_corrosion_loss_upper_bound_m` | `m` |
| `interval_results[].corrosion_accelerated_erosion_loss_lower_bound_m` | `m` |
| `interval_results[].corrosion_accelerated_erosion_loss_upper_bound_m` | `m` |
| `interval_results[].remaining_thickness_limit_state_margin_m` | `m` |
| `interval_results[].remaining_thickness_margin_lower_bound_m` | `m` |
| `interval_results[].remaining_thickness_margin_upper_bound_m` | `m` |
| `wall_thickness_limit_state.measured_thickness_m` | `m` |
| `wall_thickness_limit_state.required_thickness_m` | `m` |
| `wall_thickness_limit_state.initial_remaining_thickness_limit_state_margin_m` | `m` |
| `wall_thickness_limit_state.baseline_time_s` | `s` |
| `wall_thickness_limit_state.first_point_limit_crossing_interval.start_time_s` | `s` |
| `wall_thickness_limit_state.first_point_limit_crossing_interval.end_time_s` | `s` |
| `wall_thickness_limit_state.first_possible_limit_crossing_interval.start_time_s` | `s` |
| `wall_thickness_limit_state.first_possible_limit_crossing_interval.end_time_s` | `s` |
| `wall_thickness_limit_state.first_definite_limit_crossing_interval.start_time_s` | `s` |
| `wall_thickness_limit_state.first_definite_limit_crossing_interval.end_time_s` | `s` |
| `cumulative_component_losses` | `m` |
| `cumulative_deterministic_loss_bounds` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Pure erosion, pure corrosion and combined loss are caller-supplied matched observations; residual synergy is their signed arithmetic difference.
- Optional interaction partition requires a separately supplied corrosion rate measured during erosion; no mechanism, prediction, probability or acceptance is inferred.
- Optional rate endpoint propagation is deterministic interval arithmetic, not a confidence or probability interval.
- An optional digest-linked wall thickness limit state reports deterministic margins only, not failure probability or code acceptance.

## 구현 근거·독립 설명

- `caller_erosion_corrosion_component_accounting`: For strictly matched caller-supplied thickness-loss rates, define signed residual synergy as the combined erosion-corrosion rate minus the independently supplied pure erosion and pure corrosion rates. When a corrosion rate measured during erosion is also supplied, derive the concurrent erosion contribution by subtraction from the total and retain both signed changes relative to the pure baselines. Optional caller-reviewed lower/upper rate endpoints propagate by interval arithmetic without a statistical interpretation. Integrate each piecewise-constant rate only over its explicitly recorded interval. Do not infer an interaction mechanism, clamp negative values, extrapolate, or qualify the material.
- [S. Zhou, M. M. Stack and R. C. Newman, Characterization of synergistic effects between erosion and corrosion in an aqueous environment using electrochemical techniques (1996)](https://doi.org/10.5006/1.3292087) · `erosion_corrosion_1996_electrochemical_measurements`
- `erosion_corrosion_wall_limit_state_link`: At each complete contiguous erosion-corrosion interval, subtract cumulative caller-supplied combined thickness loss from a digest-linked measured wall thickness and then compare with the caller-required minimum thickness. When complete deterministic loss endpoints exist, propagate the margin by reversing the cumulative loss bounds and report the earliest possible/definite crossing only as an observed interval bracket. Require asset/location/physical-scope/material/geometry identity and exact baseline-clock continuity. Report a deterministic threshold relation only; do not interpolate a crossing root or infer failure probability, inspection reliability, code acceptance or remaining life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.erosion_corrosion_synergy_decomposition"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.erosion_corrosion_synergy_decomposition"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-erosion-corrosion-synergy",
  "asset_id": "synthetic-slurry-loop",
  "location_id": "synthetic-elbow-location",
  "time_basis_id": "synthetic-run-seconds",
  "material_condition_id": "synthetic-carbon-steel-condition",
  "fluid_condition_id": "synthetic-saline-slurry",
  "geometry_condition_id": "synthetic-coupon-geometry",
  "physical_scope_id": "synthetic-erosion-coupon",
  "rate_basis_id": "synthetic-thickness-loss-rate",
  "intervals": [
    {
      "interval_id": "synthetic-interval-001",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "pure_erosion": {
        "record_id": "pure-erosion-001",
        "provider_id": "synthetic-pure-erosion",
        "provider_revision": "1",
        "record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "material_condition_id": "synthetic-carbon-steel-condition",
        "fluid_condition_id": "synthetic-saline-slurry",
        "geometry_condition_id": "synthetic-coupon-geometry",
        "physical_scope_id": "synthetic-erosion-coupon",
        "location_id": "synthetic-elbow-location",
        "rate_basis_id": "synthetic-thickness-loss-rate",
        "rate_m_s": 1e-10,
        "evidence": [
          {
            "source_id": "synthetic-pure-erosion",
            "origin": "synthetic",
            "citation": "Project-authored synthetic wiring fixture only; no empirical erosion-corrosion measurement.",
            "license_id": "CC0-1.0",
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ],
        "start_time_s": 0.0,
        "end_time_s": 10.0,
        "lower_rate_bound_m_s": 9e-11,
        "upper_rate_bound_m_s": 1.1000000000000001e-10
      },
      "pure_corrosion": {
        "record_id": "pure-corrosion-001",
        "provider_id": "synthetic-pure-corrosion",
        "provider_revision": "1",
        "record_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "material_condition_id": "synthetic-carbon-steel-condition",
        "fluid_condition_id": "synthetic-saline-slurry",
        "geometry_condition_id": "synthetic-coupon-geometry",
        "physical_scope_id": "synthetic-erosion-coupon",
        "location_id": "synthetic-elbow-location",
        "rate_basis_id": "synthetic-thickness-loss-rate",
        "rate_m_s": 2e-10,
        "evidence": [
          {
            "source_id": "synthetic-pure-corrosion",
            "origin": "synthetic",
            "citation": "Project-authored synthetic wiring fixture only; no empirical erosion-corrosion measurement.",
            "license_id": "CC0-1.0",
            "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
          }
        ],
        "start_time_s": 0.0,
        "end_time_s": 10.0,
        "lower_rate_bound_m_s": 1.8e-10,
        "upper_rate_bound_m_s": 2.2000000000000002e-10
      },
      "combined_erosion_corrosion": {
        "record_id": "combined-loss-001",
        "provider_id": "synthetic-combined-loss",
        "provider_revision": "1",
        "record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "material_condition_id": "synthetic-carbon-steel-condition",
        "fluid_condition_id": "synthetic-saline-slurry",
        "geometry_condition_id": "synthetic-coupon-geometry",
        "physical_scope_id": "synthetic-erosion-coupon",
        "location_id": "synthetic-elbow-location",
        "rate_basis_id": "synthetic-thickness-loss-rate",
        "rate_m_s": 4e-10,
        "evidence": [
          {
            "source_id": "synthetic-combined-loss",
            "origin": "synthetic",
            "citation": "Project-authored synthetic wiring fixture only; no empirical erosion-corrosion measurement.",
            "license_id": "CC0-1.0",
            "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
          }
        ],
        "start_time_s": 0.0,
        "end_time_s": 10.0,
        "lower_rate_bound_m_s": 3.6e-10,
        "upper_rate_bound_m_s": 4.4000000000000003e-10
      },
      "corrosion_during_erosion": {
        "record_id": "corrosion-under-erosion-001",
        "provider_id": "synthetic-corrosion-under-erosion",
        "provider_revision": "1",
        "record_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "material_condition_id": "synthetic-carbon-steel-condition",
        "fluid_condition_id": "synthetic-saline-slurry",
        "geometry_condition_id": "synthetic-coupon-geometry",
        "physical_scope_id": "synthetic-erosion-coupon",
        "location_id": "synthetic-elbow-location",
        "rate_basis_id": "synthetic-thickness-loss-rate",
        "rate_m_s": 2.5e-10,
        "evidence": [
          {
            "source_id": "synthetic-corrosion-under-erosion",
            "origin": "synthetic",
            "citation": "Project-authored synthetic wiring fixture only; no empirical erosion-corrosion measurement.",
            "license_id": "CC0-1.0",
            "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
          }
        ],
        "start_time_s": 0.0,
        "end_time_s": 10.0,
        "lower_rate_bound_m_s": 2.2500000000000002e-10,
        "upper_rate_bound_m_s": 2.7500000000000003e-10
      }
    }
  ],
  "matched_conditions_and_rate_basis_reviewed": true,
  "component_definitions_and_accounting_convention_reviewed": true,
  "interval_clock_and_measurements_reviewed": true,
  "evidence_and_usage_rights_reviewed": true,
  "computational_use_authorized": true,
  "deterministic_rate_bounds_reviewed": true,
  "wall_thickness_baseline": {
    "baseline_id": "synthetic-wall-thickness-baseline",
    "provider_id": "synthetic-wall-thickness-provider",
    "provider_revision": "1",
    "record_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "asset_id": "synthetic-slurry-loop",
    "location_id": "synthetic-elbow-location",
    "physical_scope_id": "synthetic-erosion-coupon",
    "material_condition_id": "synthetic-carbon-steel-condition",
    "geometry_condition_id": "synthetic-coupon-geometry",
    "baseline_time_s": 0.0,
    "measured_thickness_m": 0.012,
    "required_thickness_m": 0.008,
    "evidence": [
      {
        "source_id": "synthetic-wall-thickness-provider",
        "origin": "synthetic",
        "citation": "Project-authored synthetic thickness fixture for API wiring only.",
        "license_id": "CC0-1.0",
        "sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
      }
    ]
  },
  "wall_thickness_limit_state_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/erosion_corrosion.py#L394)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
