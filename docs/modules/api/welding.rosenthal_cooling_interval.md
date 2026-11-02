# `welding.rosenthal_cooling_interval`

**목적:** Compose a fixed-point sampled Rosenthal moving-source history with caller-selected cooling-branch interval extraction.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `thermal_history` | 예 | `{"$ref": "#/$defs/RosenthalPointSource3D"}` | 계약·필드 설명 참조 |
| `upper_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `lower_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `cooling_branch_start_index` | 아니오 | `{"default": 0, "minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `cooling_branch_end_index` | 아니오 | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/RosenthalCoolingIntervalLink.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `thermal_history_sha256` | `1` |
| `rosenthal_request_sha256` | `1` |
| `cooling_interval_request_sha256` | `1` |
| `input_history_sha256` | `1` |
| `thermal_history_time_s` | `s` |
| `thermal_history_temperature_K` | `K` |
| `upper_crossing_s` | `s` |
| `lower_crossing_s` | `s` |
| `cooling_interval_s` | `s` |
| `maximum_selected_sample_spacing_s` | `s` |
| `upper_crossing_available` | `1` |
| `lower_crossing_available` | `1` |
| `upper_crossing_bracket_sample_indices` | `1` |
| `lower_crossing_bracket_sample_indices` | `1` |
| `selected_cooling_branch_sample_indices_inclusive` | `1` |
| `selected_branch_sha256` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Compose a fixed-point sampled Rosenthal moving-source history with caller-selected cooling-branch interval extraction.
- The quasi-steady semi-infinite constant-property history is not a qualified thermal-cycle or t8/5 prediction.

## 구현 근거·독립 설명

- [Tsai and Eagar, Changes of Weld Pool Shape by Variations in the Distribution of Heat Source in Arc Welding](https://eagar.mit.edu/publications/Eagar032.pdf) · `rosenthal_welding_heat_source`
- `piecewise_linear_history`: Interpolate recorded linear segments to intersect a declared temperature band or temperature crossing; preserve actual continuous intervals.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.rosenthal_cooling_interval"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.rosenthal_cooling_interval"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "thermal_history": {
    "absorbed_power_W": 500.0,
    "travel_speed_m_s": 0.005,
    "thermal_conductivity_W_m_K": 45.0,
    "density_kg_m3": 7850.0,
    "specific_heat_J_kg_K": 600.0,
    "initial_temperature_K": 300.0,
    "source_relative_x_m": [
      0.01,
      0.0095,
      0.009000000000000001,
      0.0085,
      0.008,
      0.0075,
      0.007,
      0.006500000000000001,
      0.006,
      0.0055,
      0.005,
      0.0045,
      0.004,
      0.0034999999999999996,
      0.003000000000000001,
      0.0025000000000000005,
      0.002,
      0.0014999999999999996,
      0.0009999999999999992,
      0.0005000000000000004,
      0.0,
      -0.0005000000000000004,
      -0.0010000000000000009,
      -0.0014999999999999996,
      -0.002,
      -0.0025000000000000005,
      -0.003000000000000001,
      -0.0035000000000000014,
      -0.003999999999999998,
      -0.004499999999999999,
      -0.004999999999999999,
      -0.005500000000000001,
      -0.006,
      -0.006500000000000001,
      -0.007000000000000001,
      -0.0075000000000000015,
      -0.008000000000000002,
      -0.008500000000000002,
      -0.009,
      -0.0095,
      -0.01,
      -0.010499999999999997,
      -0.011000000000000001,
      -0.011499999999999998,
      -0.012000000000000002,
      -0.012499999999999999,
      -0.013,
      -0.0135,
      -0.014,
      -0.0145,
      -0.015000000000000001,
      -0.015499999999999998,
      -0.016,
      -0.0165,
      -0.017,
      -0.0175,
      -0.017999999999999995,
      -0.018500000000000003,
      -0.018999999999999996,
      -0.019500000000000003,
      -0.019999999999999997
    ],
    "transverse_y_m": [
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005,
      0.005
    ],
    "depth_z_m": [
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002,
      0.002
    ],
    "time_s": [
      0.0,
      0.1,
      0.2,
      0.3,
      0.4,
      0.5,
      0.6,
      0.7,
      0.8,
      0.9,
      1.0,
      1.1,
      1.2,
      1.3,
      1.4,
      1.5,
      1.6,
      1.7,
      1.8,
      1.9,
      2.0,
      2.1,
      2.2,
      2.3,
      2.4,
      2.5,
      2.6,
      2.7,
      2.8,
      2.9,
      3.0,
      3.1,
      3.2,
      3.3,
      3.4,
      3.5,
      3.6,
      3.7,
      3.8,
      3.9,
      4.0,
      4.1,
      4.2,
      4.3,
      4.4,
      4.5,
      4.6,
      4.7,
      4.8,
      4.9,
      5.0,
      5.1,
      5.2,
      5.3,
      5.4,
      5.5,
      5.6,
      5.7,
      5.8,
      5.9,
      6.0
    ],
    "threshold_temperatures_K": [],
    "semi_infinite_half_space_reviewed": true,
    "constant_properties_reviewed": true,
    "phase_change_and_latent_heat_neglected_reviewed": true,
    "convection_radiation_and_pool_flow_neglected_reviewed": true,
    "point_source_and_steady_moving_frame_reviewed": true
  },
  "upper_temperature_K": 400.0,
  "lower_temperature_K": 380.0,
  "cooling_branch_start_index": 30,
  "cooling_branch_end_index": 60
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fabrication.py#L191)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
