# `inspection.acoustic_emission_wave_speed_calibration`

**목적:** Weighted linear calibration of arrival minus known emission time against known source-sensor distance.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sensors` | 예 | `{"items": {"$ref": "#/$defs/AESpeedSensor"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `known_sources` | 예 | `{"items": {"$ref": "#/$defs/AEKnownSource"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `picks` | 예 | `{"items": {"$ref": "#/$defs/AESpeedArrivalPick"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_supported_wave_speed_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `maximum_supported_wave_speed_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `minimum_calibration_distance_span_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `minimum_calibration_source_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `sensor_source_coordinates_and_frame_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_emission_reference_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pick_methods_uncertainties_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_specimen_groups_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `homogeneous_isotropic_constant_speed_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_and_no_extrapolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AcousticEmissionWaveSpeedCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `wave_speed_m_s` | `m/s` |
| `fitted_slowness_s_m` | `s/m` |
| `clock_offset_s` | `s` |
| `calibration_distance_support_m` | `m` |
| `outside_support_holdout_pick_ids` | `1` |
| `excluded_missing_or_invalid_pick_ids` | `1` |
| `calibration_pick_ids` | `1` |
| `holdout_pick_ids` | `1` |
| `holdout_time_residual_s` | `s` |
| `holdout_weighted_time_bias_s` | `s` |
| `holdout_weighted_time_rmse_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weighted linear calibration of arrival minus known emission time against known source-sensor distance.
- One homogeneous isotropic constant speed and one clock offset are fitted from calibration picks only.
- Physical specimens and source groups cannot cross calibration and holdout partitions.

## 구현 근거·독립 설명

- `weighted_known_source_acoustic_emission_wave_speed_calibration`: Fit a homogeneous acoustic-emission wave speed and clock offset from caller-reviewed known-source geometry and arrival picks using inverse-variance weighted travel time. Preserve sensor, channel, clock, specimen, source, calibration/holdout partitions, support and immutable digests; do not generate picks, infer anisotropy or dispersion, localize unknown sources, classify mechanisms, grade damage, decide acceptance, POD or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.acoustic_emission_wave_speed_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.acoustic_emission_wave_speed_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "fit",
  "asset_id": "a",
  "location_id": "l",
  "coordinate_frame_id": "f",
  "clock_id": "clock",
  "sensors": [
    {
      "sensor_id": "s0",
      "channel_id": "c0",
      "coordinate_frame_id": "f",
      "position_m": [
        0.0,
        0.0,
        0.0
      ],
      "calibration_id": "cal",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "sensor_id": "s1",
      "channel_id": "c1",
      "coordinate_frame_id": "f",
      "position_m": [
        2.0,
        0.0,
        0.0
      ],
      "calibration_id": "cal",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "known_sources": [
    {
      "source_id": "src1",
      "physical_specimen_id": "p1",
      "source_group_id": "g1",
      "partition": "calibration",
      "coordinate_frame_id": "f",
      "position_m": [
        0.5,
        0.0,
        0.0
      ],
      "emission_reference_time_s": 0.01,
      "source_definition_id": "known",
      "source_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "source_id": "src2",
      "physical_specimen_id": "p2",
      "source_group_id": "g2",
      "partition": "calibration",
      "coordinate_frame_id": "f",
      "position_m": [
        1.0,
        0.0,
        0.0
      ],
      "emission_reference_time_s": 0.02,
      "source_definition_id": "known",
      "source_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "source_id": "src3",
      "physical_specimen_id": "p3",
      "source_group_id": "g3",
      "partition": "holdout",
      "coordinate_frame_id": "f",
      "position_m": [
        0.75,
        0.0,
        0.0
      ],
      "emission_reference_time_s": 0.03,
      "source_definition_id": "known",
      "source_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "picks": [
    {
      "pick_id": "src1s0",
      "source_id": "src1",
      "sensor_id": "s0",
      "channel_id": "c0",
      "clock_id": "clock",
      "arrival_time_s": 0.011099999999999999,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "pick_id": "src1s1",
      "source_id": "src1",
      "sensor_id": "s1",
      "channel_id": "c1",
      "clock_id": "clock",
      "arrival_time_s": 0.0113,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "pick_id": "src2s0",
      "source_id": "src2",
      "sensor_id": "s0",
      "channel_id": "c0",
      "clock_id": "clock",
      "arrival_time_s": 0.0212,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "pick_id": "src2s1",
      "source_id": "src2",
      "sensor_id": "s1",
      "channel_id": "c1",
      "clock_id": "clock",
      "arrival_time_s": 0.0212,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "pick_id": "src3s0",
      "source_id": "src3",
      "sensor_id": "s0",
      "channel_id": "c0",
      "clock_id": "clock",
      "arrival_time_s": 0.03115,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "pick_id": "src3s1",
      "source_id": "src3",
      "sensor_id": "s1",
      "channel_id": "c1",
      "clock_id": "clock",
      "arrival_time_s": 0.03125,
      "standard_uncertainty_s": 1e-06,
      "pick_method_id": "method",
      "source_trace_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "minimum_supported_wave_speed_m_s": 4000.0,
  "maximum_supported_wave_speed_m_s": 6000.0,
  "minimum_calibration_distance_span_m": 0.5,
  "minimum_calibration_source_count": 2,
  "minimum_holdout_source_count": 1,
  "sensor_source_coordinates_and_frame_reviewed": true,
  "clock_and_emission_reference_reviewed": true,
  "pick_methods_uncertainties_and_digests_reviewed": true,
  "source_specimen_groups_and_partitions_reviewed": true,
  "homogeneous_isotropic_constant_speed_assumption_reviewed": true,
  "support_and_no_extrapolation_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/acoustic_emission_speed.py#L132)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
