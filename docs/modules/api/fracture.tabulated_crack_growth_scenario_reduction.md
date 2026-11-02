# `fracture.tabulated_crack_growth_scenario_reduction`

**목적:** Portable reduction of externally evaluated complete crack-growth scenarios with exact manifest coverage, input digests and one evaluator identity/configuration.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.tabulated_crack_growth_scenario_reduction.v1", "default": "matintegrity.tabulated_crack_growth_scenario_reduction.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `ensemble_run_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `distribution_definition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sample_design_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `manifest` | 예 | `{"items": {"$ref": "#/$defs/CrackGrowthScenarioManifestRow"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `evaluations` | 예 | `{"items": {"$ref": "#/$defs/CrackGrowthScenarioEvaluation"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `requested_quantiles` | 예 | `{"items": {"type": "number"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `depth_exceedance_threshold_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `maximum_weight_sum_error` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `evaluator_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `external_evaluations_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `normalized_weight_meaning_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `common_physical_scope_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TabulatedCrackGrowthScenarioReduction.json)

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

- Portable reduction of externally evaluated complete crack-growth scenarios with exact manifest coverage, input digests and one evaluator identity/configuration.
- Every noncomputed row is retained and suppresses aggregate statistics; the reducer does not validate scheduler execution, scenario probabilities or physical model form.

## 구현 근거·독립 설명

- `complete_crack_growth_scenario_ensemble`: Accept two or more caller-reviewed normalized weighted scenarios, each containing a complete deterministic single-curve or curve-family crack-growth input and its own joint source identity and digest. Require a common physical scope while allowing joint changes to individual curve points, curve-family composition, geometry knots, ordered load blocks, toughness and numerical controls. Preserve the canonical digest and result of every complete input. Form weighted moments, discrete inverse-CDF quantiles and declared-depth exceedance mass only when every scenario computes. Never generate, fit, normalize, interpolate between, discard or assign probabilities to scenarios, and never relabel their push-forward mass as a period first-failure probability, FTA basic-event probability, model-form validation, confidence bound or code acceptance result.
- `portable_crack_growth_scenario_reduction`: Split a reviewed complete-input crack-growth ensemble into independently schedulable rows and bind every external evaluation to its scenario ID, canonical deterministic-input digest, evaluator identity, evaluator revision, evaluator-configuration digest and result digest. Before reduction, require unique manifest and evaluation identities, exact set coverage, a common physical scope, normalized manifest weights and exact input/evaluator matches. Preserve manifest order. Retain invalid, failed, needs-data and out-of-scope evaluations and withhold all aggregate statistics instead of filtering or renormalizing them. Do not infer scheduler correctness, scenario probabilities, model-form validity, period failure probability, FTA basic-event probability, confidence bounds or acceptance.

확률 의미: `{"model_implied_depth_exceedance_probability": "model_implied_input_uncertainty_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fracture.tabulated_crack_growth_scenario_reduction"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fracture.tabulated_crack_growth_scenario_reduction"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.tabulated_crack_growth_scenario_reduction.v1",
  "ensemble_run_id": "authored-complete-input-ensemble",
  "distribution_definition_id": "authored-discrete-input-mass",
  "sample_design_id": "authored-two-complete-inputs",
  "manifest": [
    {
      "schema_version": "matintegrity.crack_growth_scenario_manifest_row.v1",
      "scenario_id": "scenario-a",
      "normalized_weight": 0.5,
      "joint_scenario_source_id": "authored-scenario-a",
      "joint_scenario_source_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "input_sha256": "15bdd7e5ffe0c087d8e28c39b3742094410789de9f5f6202b217dc0fc4ffc14b",
      "physical_scope_id": "synthetic-crack-front"
    },
    {
      "schema_version": "matintegrity.crack_growth_scenario_manifest_row.v1",
      "scenario_id": "scenario-b",
      "normalized_weight": 0.5,
      "joint_scenario_source_id": "authored-scenario-b",
      "joint_scenario_source_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "input_sha256": "4c4bc007ee753a78adcf4994aee523933e3ec213123018578b4cfa173f14c300",
      "physical_scope_id": "synthetic-crack-front"
    }
  ],
  "evaluations": [
    {
      "schema_version": "matintegrity.crack_growth_scenario_evaluation.v1",
      "scenario_id": "scenario-a",
      "input_sha256": "15bdd7e5ffe0c087d8e28c39b3742094410789de9f5f6202b217dc0fc4ffc14b",
      "evaluator_id": "matintegrity-tabulated-growth",
      "evaluator_revision": "local-smoke-v1",
      "evaluator_configuration_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
      "status": "computed",
      "final_depth_m": 0.0010182814966900715,
      "cycles_evaluated": 1000.0,
      "termination_reason": "requested_blocks_completed",
      "result_sha256": "308456193e4046d44051bf70859e15299b237724a5b7947456b880178ae8f05b"
    },
    {
      "schema_version": "matintegrity.crack_growth_scenario_evaluation.v1",
      "scenario_id": "scenario-b",
      "input_sha256": "4c4bc007ee753a78adcf4994aee523933e3ec213123018578b4cfa173f14c300",
      "evaluator_id": "matintegrity-tabulated-growth",
      "evaluator_revision": "local-smoke-v1",
      "evaluator_configuration_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
      "status": "computed",
      "final_depth_m": 0.0010147112928311289,
      "cycles_evaluated": 1000.0,
      "termination_reason": "requested_blocks_completed",
      "result_sha256": "28167476b193570a3e192c79ee44103e4df8afc1832d1e089e0ccdf44056495c"
    }
  ],
  "requested_quantiles": [
    0.25,
    0.5,
    0.9
  ],
  "depth_exceedance_threshold_m": 0.00102,
  "maximum_weight_sum_error": 1e-12,
  "evaluator_id": "matintegrity-tabulated-growth",
  "evaluator_revision": "local-smoke-v1",
  "evaluator_configuration_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
  "external_evaluations_reviewed": true,
  "normalized_weight_meaning_reviewed": true,
  "common_physical_scope_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crack.py#L1329)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
