# `structural.burst_pressure_comparison`

**목적:** Partition-aware descriptive comparison of caller-supplied pressure predictions with qualified burst tests; no pressure equation, acceptance limit or standard table is bundled.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `comparison_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prediction_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prediction_provider_version` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prediction_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `rows` | 예 | `{"items": {"$ref": "#/$defs/BurstPressureComparisonRow"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `physical_specimen_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_group_partitioning_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `prediction_frozen_before_evaluation` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BurstPressureComparison.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `partition_summaries.calibration.arithmetic_mean_predicted_to_observed_ratio` | `1` |
| `partition_summaries.holdout.arithmetic_mean_predicted_to_observed_ratio` | `1` |
| `partition_summaries.external_validation.arithmetic_mean_predicted_to_observed_ratio` | `1` |
| `partition_summaries.calibration.root_mean_square_log_error` | `1` |
| `partition_summaries.holdout.root_mean_square_log_error` | `1` |
| `partition_summaries.external_validation.root_mean_square_log_error` | `1` |
| `pointwise_comparisons.predicted_to_observed_pressure_ratio` | `1` |
| `pointwise_comparisons.log_predicted_to_observed_pressure_ratio` | `1` |
| `observation_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Partition-aware descriptive comparison of caller-supplied pressure predictions with qualified burst tests; no pressure equation, acceptance limit or standard table is bundled.

## 구현 근거·독립 설명

- `burst_prediction_comparison_definition`: Preserve each reviewed experimental burst endpoint, physical specimen, source group, partition, material, geometry, load case, pressure basis, source hash and prediction-input digest. Require authorized observation use, one row per physical specimen, matching observed/predicted pressure bases, a prediction frozen before evaluation and no source group crossing from calibration into evaluation. Report pointwise predicted-to-observed ratios and separate calibration, holdout and external-validation descriptive summaries. These errors do not supply a pressure model, standard limit, safety factor, prediction interval, population coverage, remaining life or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.burst_pressure_comparison"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.burst_pressure_comparison"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "comparison_id": "synthetic-provider-comparison",
  "prediction_provider_id": "synthetic.pressure-provider",
  "prediction_provider_version": "1.0.0",
  "prediction_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "rows": [
    {
      "observation_id": "synthetic-test-001",
      "physical_specimen_id": "synthetic-specimen-001",
      "source_group_id": "synthetic-external-program",
      "partition": "external_validation",
      "material_condition_id": "synthetic-steel-condition",
      "geometry_id": "synthetic-pipe-defect-001",
      "load_case_id": "synthetic-monotonic-pressure",
      "observed_pressure_basis": "internal_minus_external",
      "predicted_pressure_basis": "internal_minus_external",
      "observed_burst_pressure_Pa": 12000000.0,
      "predicted_failure_pressure_Pa": 11400000.0,
      "observation_source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "prediction_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "observation_use_authorized": true,
      "experimental_endpoint_reviewed": true,
      "geometry_and_material_reviewed": true,
      "pressure_basis_reviewed": true
    }
  ],
  "physical_specimen_independence_reviewed": true,
  "source_group_partitioning_reviewed": true,
  "prediction_frozen_before_evaluation": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/burst_validation.py#L78)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
