# `corrosion.rate_sample_summary`

**목적:** One caller-reviewed rate summary per unique physical specimen, all from one material, condition, method and source group.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `observations` | 예 | `{"items": {"$ref": "#/$defs/CorrosionRateObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `quantile_probabilities` | 아니오 | `{"items": {"maximum": 1, "minimum": 0, "type": "number"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measurement_error_covariance_m_s2` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CorrosionRateSampleSummary.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `arithmetic_mean_rate_m_s` | `m/s` |
| `between_specimen_sample_standard_deviation_m_s` | `m/s` |
| `measurement_standard_uncertainty_of_mean_m_s` | `m/s` |
| `minimum_rate_m_s` | `m/s` |
| `maximum_rate_m_s` | `m/s` |
| `quantile_rates_m_s` | `m/s` |
| `rate_standard_uncertainties_m_s` | `m/s` |
| `specimen_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One caller-reviewed rate summary per unique physical specimen, all from one material, condition, method and source group.
- Between-specimen sample standard deviation and caller-propagated uncertainty of the equal-weight mean are distinct and reported separately.
- Empirical quantiles describe the supplied sample only and are not uncertainty bounds or life forecasts.

## 구현 근거·독립 설명

- `numpy_quantile_linear`: Compute descriptive empirical quantiles from one caller-reviewed rate summary per identified physical specimen in a single material, condition, method and source group, using NumPy's explicitly selected linear sample quantile definition. The result describes only the supplied sample and does not estimate confidence, prediction, independence, transferability or life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.rate_sample_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.rate_sample_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "observations": [
    {
      "observation_id": "synthetic-coupon-01-rate",
      "physical_specimen_id": "synthetic-coupon-01",
      "material_id": "alloy-A",
      "rate_m_s": 1.8e-09,
      "condition_signature": {
        "temperature_K": 323.15,
        "chloride_mol_L": 0.1
      },
      "condition_group_id": "synthetic-condition-01",
      "source_group_id": "synthetic-study-01",
      "measurement_method": "weight_loss"
    },
    {
      "observation_id": "synthetic-coupon-02-rate",
      "physical_specimen_id": "synthetic-coupon-02",
      "material_id": "alloy-A",
      "rate_m_s": 2.6e-09,
      "condition_signature": {
        "temperature_K": 323.15,
        "chloride_mol_L": 0.1
      },
      "condition_group_id": "synthetic-condition-01",
      "source_group_id": "synthetic-study-01",
      "measurement_method": "weight_loss"
    },
    {
      "observation_id": "synthetic-coupon-03-rate",
      "physical_specimen_id": "synthetic-coupon-03",
      "material_id": "alloy-A",
      "rate_m_s": 3.1e-09,
      "condition_signature": {
        "temperature_K": 323.15,
        "chloride_mol_L": 0.1
      },
      "condition_group_id": "synthetic-condition-01",
      "source_group_id": "synthetic-study-01",
      "measurement_method": "weight_loss"
    }
  ],
  "quantile_probabilities": [
    0.1,
    0.5,
    0.9
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/corrosion.py#L530)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
