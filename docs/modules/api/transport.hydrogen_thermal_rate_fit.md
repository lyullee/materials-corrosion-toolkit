# `transport.hydrogen_thermal_rate_fit`

**목적:** Weighted log-linear calibration of one reviewed effective Arrhenius or fixed-transmission transition-state frequency law with preserved calibration/holdout identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.hydrogen_thermal_rate_fit.v1", "default": "matintegrity.hydrogen_thermal_rate_fit.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `fit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `frequency_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `frequency_role` | 예 | `{"enum": ["capture", "release"], "type": "string"}` | 계약·필드 설명 참조 |
| `kind` | 예 | `{"enum": ["arrhenius", "transition_state"], "type": "string"}` | 계약·필드 설명 참조 |
| `trap_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_lattice_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `energy_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_id` | 예 | `{"items": {"type": "string"}, "maxItems": 10000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `partition` | 예 | `{"items": {"enum": ["calibration", "holdout"], "type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | K |
| `frequency_per_s` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | 1/s |
| `log_frequency_standard_uncertainty` | 아니오 | `{"anyOf": [{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `transmission_coefficient` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "maximum": 1, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `minimum_calibration_temperature_span_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `calibration_observations_independent_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_observation_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `common_energy_reference_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_partition_predeclared` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenThermalRateFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_temperature_support_K` | `K` |
| `calibration_temperature_span_K` | `K` |
| `calibration_log_frequency_rmse` | `1` |
| `holdout_log_frequency_rmse` | `1` |
| `normalized_design_condition_number` | `1` |
| `residual_log_frequency_variance` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weighted log-linear calibration of one reviewed effective Arrhenius or fixed-transmission transition-state frequency law with preserved calibration/holdout identities.

## 구현 근거·독립 설명

- [Eyring, The Activated Complex in Chemical Reactions, Journal of Chemical Physics 3 (1935) 107-115](https://doi.org/10.1063/1.1749604) · `eyring_transition_state`
- `hydrogen_thermal_rate_fit_derivation`: Transform reviewed positive rate observations to log frequency versus inverse temperature. For Arrhenius fitting use log(k)=log(A)-E/(RT). For fixed-transmission transition-state fitting use log[k h/(kappa k_B T)]=DeltaS/R-DeltaH/(RT). Fit only caller-labelled calibration rows with a centered and scaled weighted two-column design, transform the coefficient covariance to physical parameters, and evaluate untouched holdout rows only inside calibration temperature support. A rate-only transition-state fit cannot separate transmission coefficient from activation entropy, and conditional regression covariance excludes model-form, source-group and transport-inversion uncertainty.
- [NumPy least-squares solver documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) · `numpy_lstsq`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.hydrogen_thermal_rate_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["transport.hydrogen_thermal_rate_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "fit_id": "synthetic-capture-fit",
  "frequency_id": "synthetic-capture-law",
  "frequency_role": "capture",
  "kind": "arrhenius",
  "trap_id": "synthetic-trap",
  "material_condition_id": "synthetic-state",
  "reference_lattice_id": "synthetic-sites",
  "energy_reference_id": "synthetic-lattice-site-zero",
  "observation_id": [
    "rate-0",
    "rate-1",
    "rate-2",
    "rate-3",
    "rate-4",
    "rate-5",
    "rate-6"
  ],
  "source_group_id": [
    "synthetic-calibration",
    "synthetic-calibration",
    "synthetic-calibration",
    "synthetic-calibration",
    "synthetic-calibration",
    "synthetic-holdout",
    "synthetic-holdout"
  ],
  "partition": [
    "calibration",
    "calibration",
    "calibration",
    "calibration",
    "calibration",
    "holdout",
    "holdout"
  ],
  "temperature_K": [
    300.0,
    350.0,
    400.0,
    450.0,
    500.0,
    375.0,
    425.0
  ],
  "frequency_per_s": [
    121.68391997069784,
    1348.6696804462333,
    8192.37636596036,
    33327.453469675726,
    102403.76364231255,
    3529.9987790011164,
    17219.848031618538
  ],
  "log_frequency_standard_uncertainty": [
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05
  ],
  "minimum_calibration_temperature_span_K": 100.0,
  "calibration_observations_independent_reviewed": true,
  "rate_observation_mapping_reviewed": true,
  "common_energy_reference_reviewed": true,
  "holdout_partition_predeclared": true,
  "evidence": [
    {
      "source_id": "authored-synthetic",
      "origin": "synthetic",
      "citation": "Authored thermal-rate fit demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_calibration.py#L92)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
