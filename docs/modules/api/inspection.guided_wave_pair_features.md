# `inspection.guided_wave_pair_features`

**목적:** One physical specimen, aligned provider distance grids and one declared spatial window; paired descriptors do not separate environmental change from damage.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `baseline_acquisition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_acquisition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `frequency_Hz` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `wave_mode` | 예 | `{"enum": ["torsional", "flexural"], "type": "string"}` | 계약·필드 설명 참조 |
| `baseline_distance_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `baseline_voltage_V` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | V |
| `observation_distance_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `observation_voltage_V` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | V |
| `window_start_m` | 예 | `{"type": "number"}` | m |
| `window_end_m` | 예 | `{"type": "number"}` | m |
| `distance_match_tolerance_m` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | m |
| `duplicate_distance_policy` | 아니오 | `{"default": "preserve_samples", "enum": ["preserve_samples", "mean_aligned_duplicates", "reject"], "type": "string"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GuidedWavePairFeatures.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `frequency_Hz` | `Hz` |
| `window_start_m` | `m` |
| `window_end_m` | `m` |
| `maximum_distance_grid_mismatch_m` | `m` |
| `baseline_rms_V` | `V` |
| `observation_rms_V` | `V` |
| `residual_rms_V` | `V` |
| `normalized_residual_rms` | `1` |
| `voltage_energy_ratio` | `1` |
| `correlation_coefficient` | `1` |
| `peak_absolute_difference_V` | `V` |
| `signed_mean_difference_V` | `V` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One physical specimen, aligned provider distance grids and one declared spatial window; paired descriptors do not separate environmental change from damage.

## 구현 근거·독립 설명

- `guided_wave_pair_feature_definition`: For one physical specimen, one frequency and one propagation-mode voltage channel, require separate baseline and observation acquisition identities and aligned nondecreasing provider distance grids. Select only the caller-declared inclusive spatial window without interpolation or sorting. Preserve or explicitly reject repeated distances, or average only contiguous aligned duplicate pairs under a named policy. Report raw RMS, paired residual RMS, normalized residual, energy ratio, correlation and peak/mean difference while retaining undefined normalized quantities for a zero baseline. These descriptive features do not identify machining steps, remaining thickness, defect geometry, POD, acceptance, life or failure probability, and a single baseline does not separate environmental, coupling and damage effects.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.guided_wave_pair_features"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.guided_wave_pair_features"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "specimen_id": "example-tube",
  "baseline_acquisition_id": "baseline-1",
  "observation_acquisition_id": "observation-1",
  "frequency_Hz": 14000.0,
  "wave_mode": "torsional",
  "baseline_distance_m": [
    0.0,
    0.5,
    1.0,
    1.5
  ],
  "baseline_voltage_V": [
    0.01,
    0.02,
    -0.01,
    -0.02
  ],
  "observation_distance_m": [
    0.0,
    0.5,
    1.0,
    1.5
  ],
  "observation_voltage_V": [
    0.012,
    0.018,
    -0.015,
    -0.018
  ],
  "window_start_m": 0.0,
  "window_end_m": 1.5,
  "distance_match_tolerance_m": 0.0,
  "duplicate_distance_policy": "preserve_samples"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L705)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
