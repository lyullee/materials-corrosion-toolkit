# `inspection.guided_wave_reference_ensemble`

**목적:** At least three explicitly selected same-specimen baseline acquisitions, one aligned observation and one spatial window; ensemble descriptors are not detection calibration or acceptance.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `baseline_acquisition_ids` | 예 | `{"items": {"type": "string"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `observation_acquisition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `baseline_source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `baseline_selection_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `frequency_Hz` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `wave_mode` | 예 | `{"enum": ["torsional", "flexural"], "type": "string"}` | 계약·필드 설명 참조 |
| `distance_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `baseline_voltage_V` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | V |
| `observation_distance_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `observation_voltage_V` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | V |
| `window_start_m` | 예 | `{"type": "number"}` | m |
| `window_end_m` | 예 | `{"type": "number"}` | m |
| `distance_match_tolerance_m` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | m |
| `duplicate_distance_policy` | 아니오 | `{"default": "preserve_samples", "enum": ["preserve_samples", "mean_aligned_duplicates", "reject"], "type": "string"}` | 계약·필드 설명 참조 |
| `reference_statistic` | 아니오 | `{"default": "median", "enum": ["mean", "median"], "type": "string"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GuidedWaveReferenceEnsemble.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `frequency_Hz` | `Hz` |
| `window_start_m` | `m` |
| `window_end_m` | `m` |
| `maximum_distance_grid_mismatch_m` | `m` |
| `reference_rms_V` | `V` |
| `observation_rms_V` | `V` |
| `observation_residual_rms_V` | `V` |
| `normalized_observation_residual_rms` | `1` |
| `baseline_spread_rms_V` | `V` |
| `observation_to_baseline_spread_ratio` | `1` |
| `leave_one_out_residual_rms_V` | `V` |
| `leave_one_out_residual_median_V` | `V` |
| `leave_one_out_residual_q95_V` | `V` |
| `leave_one_out_residual_maximum_V` | `V` |
| `observation_to_leave_one_out_median_ratio` | `1` |
| `observation_to_leave_one_out_maximum_ratio` | `1` |
| `reference_observation_correlation` | `1` |
| `peak_absolute_difference_V` | `V` |
| `signed_mean_difference_V` | `V` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- At least three explicitly selected same-specimen baseline acquisitions, one aligned observation and one spatial window; ensemble descriptors are not detection calibration or acceptance.

## 구현 근거·독립 설명

- `guided_wave_reference_ensemble_definition`: For one physical specimen, require at least three uniquely identified caller-selected baseline acquisitions plus a distinct observation, one exact frequency/mode channel, aligned nondecreasing provider distance grids, explicit source groups, selection basis, spatial window and repeated-distance policy. Form a pointwise mean or median reference, quantify baseline spread and leave-one-out residual RMS, then compare the observation with that reference without interpolation, sorting or probability conversion. These ratios describe the selected acquisition ensemble only; they are not an anomaly probability, POD, acceptance threshold, defect dimension, remaining thickness, life or failure probability, and repeated records from one specimen do not establish independent validation or separate coupling/environment effects from damage.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.guided_wave_reference_ensemble"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.guided_wave_reference_ensemble"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "specimen_id": "example-tube",
  "baseline_acquisition_ids": [
    "baseline-1",
    "baseline-2",
    "baseline-3"
  ],
  "observation_acquisition_id": "observation-1",
  "baseline_source_group_id": "example-reference-group",
  "observation_source_group_id": "example-observation-group",
  "baseline_selection_basis": "three synthetic acquisitions selected before comparison",
  "frequency_Hz": 14000.0,
  "wave_mode": "torsional",
  "distance_m": [
    0.0,
    0.5,
    1.0
  ],
  "baseline_voltage_V": [
    [
      0.01,
      0.02,
      -0.01
    ],
    [
      0.011,
      0.019,
      -0.012
    ],
    [
      0.009,
      0.021,
      -0.011
    ]
  ],
  "observation_distance_m": [
    0.0,
    0.5,
    1.0
  ],
  "observation_voltage_V": [
    0.012,
    0.018,
    -0.015
  ],
  "window_start_m": 0.0,
  "window_end_m": 1.0,
  "distance_match_tolerance_m": 0.0,
  "duplicate_distance_policy": "preserve_samples",
  "reference_statistic": "median"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L2552)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
