# `corrosion.gumbel_area_maximum`

**목적:** Equal-area complete independent block maxima from one declared surface population and exposure; caller-selected Gumbel or generalized extreme-value maximum approximation with explicit diagnostics.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `extreme_value_family` | 아니오 | `{"default": "gumbel", "enum": ["gumbel", "gev"], "type": "string"}` | 계약·필드 설명 참조 |
| `population_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `block_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 5000, "minItems": 8, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_depth_m` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 8, "type": "array"}` | m |
| `block_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `target_block_count` | 예 | `{"maximum": 1000000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `independent_equivalent_blocks` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `same_exposure_and_surface_population` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_uncensored_block_maxima` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_target_to_sampled_area_ratio` | 예 | `{"minimum": 1, "type": "number"}` | 계약·필드 설명 참조 |
| `depth_threshold_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `quantile_probability` | 예 | `{"exclusiveMaximum": 1, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `confidence_level` | 예 | `{"exclusiveMaximum": 1, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `diagnostic_resamples` | 예 | `{"maximum": 1999, "minimum": 99, "type": "integer"}` | 계약·필드 설명 참조 |
| `parameter_resamples` | 예 | `{"maximum": 1999, "minimum": 99, "type": "integer"}` | 계약·필드 설명 참조 |
| `seed` | 예 | `{"minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_goodness_of_fit_pvalue` | 예 | `{"exclusiveMaximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_negative_depth_probability` | 예 | `{"maximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GumbelAreaMaximum.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `fitted_block_location_m` | `m` |
| `fitted_block_scale_m` | `m` |
| `fitted_shape_parameter_scipy` | `1` |
| `observed_area_m2` | `m^2` |
| `target_area_m2` | `m^2` |
| `target_maximum_depth_quantile_m` | `m` |
| `depth_quantile_parameter_interval_m` | `m` |
| `area_depth_exceedance_probability` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Equal-area complete independent block maxima from one declared surface population and exposure; caller-selected Gumbel or generalized extreme-value maximum approximation with explicit diagnostics.

## 구현 근거·독립 설명

- [NIST extreme-value maximum distribution and estimation](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366g.htm) · `nist_gumbel`
- [SciPy generalized extreme-value distribution, shape convention, CDF and survival-function methods](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html) · `scipy_genextreme`
- [SciPy refitted parametric goodness-of-fit inference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.goodness_of_fit.html) · `scipy_goodness_of_fit`
- `independent_area_maxima`: For k independent equivalent surface blocks at the same exposure, P(max<=d)=F(d)^k. A Gumbel maximum law shifts location by scale*log(k); no time-growth or structural-failure law is inferred.

확률 의미: `{"area_depth_exceedance_probability": "spatial_size_exceedance_at_one_exposure"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.gumbel_area_maximum"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.gumbel_area_maximum"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "population_id": "synthetic-uniform-surface",
  "exposure_condition_id": "synthetic-one-exposure",
  "block_ids": [
    "block-0",
    "block-1",
    "block-2",
    "block-3",
    "block-4",
    "block-5",
    "block-6",
    "block-7",
    "block-8",
    "block-9",
    "block-10",
    "block-11",
    "block-12",
    "block-13",
    "block-14",
    "block-15",
    "block-16",
    "block-17",
    "block-18",
    "block-19",
    "block-20",
    "block-21",
    "block-22",
    "block-23",
    "block-24",
    "block-25",
    "block-26",
    "block-27",
    "block-28",
    "block-29",
    "block-30",
    "block-31",
    "block-32",
    "block-33",
    "block-34",
    "block-35",
    "block-36",
    "block-37",
    "block-38",
    "block-39"
  ],
  "maximum_depth_m": [
    0.001704497736128972,
    0.001762223231975624,
    0.0017960437118923547,
    0.0018219189665794372,
    0.0018436949534327183,
    0.0018629637565412817,
    0.0018805541362757966,
    0.0018969596211891972,
    0.0019125021962522128,
    0.0019274067060850784,
    0.0019418389324620028,
    0.0019559268737078094,
    0.0019697734923557145,
    0.001983464810561131,
    0.001997075327947851,
    0.002010671836913198,
    0.002024316256502727,
    0.002038067865109843,
    0.002051985180210948,
    0.0020661276606380036,
    0.0020805573691804148,
    0.0020953407187191708,
    0.0021105504286294584,
    0.0021262678394285135,
    0.0021425857762972086,
    0.0021596122249893106,
    0.0021774752035570574,
    0.0021963294110954523,
    0.002216365567686524,
    0.0022378239381521167,
    0.002261014577630685,
    0.0022863488191910124,
    0.0023143905054546767,
    0.002345944046547129,
    0.0023822165625064446,
    0.0024251444186897775,
    0.0024781364441475726,
    0.0025480986013020714,
    0.0026528729216135144,
    0.0028751487672603673
  ],
  "block_area_m2": 0.0001,
  "target_block_count": 400,
  "independent_equivalent_blocks": true,
  "same_exposure_and_surface_population": true,
  "complete_uncensored_block_maxima": true,
  "maximum_target_to_sampled_area_ratio": 10.0,
  "depth_threshold_m": 0.003,
  "quantile_probability": 0.95,
  "confidence_level": 0.95,
  "diagnostic_resamples": 99,
  "parameter_resamples": 99,
  "seed": 260626,
  "minimum_goodness_of_fit_pvalue": 0.01,
  "maximum_negative_depth_probability": 0.001
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pitting.py#L45)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
