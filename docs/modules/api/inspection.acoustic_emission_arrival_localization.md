# `inspection.acoustic_emission_arrival_localization`

**목적:** Multi-sensor arrival-time localization in one reviewed frame with fixed caller-supplied wave speed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sensors` | 예 | `{"items": {"$ref": "#/$defs/AESensorLocation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/AELocalizationEvent"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `wave_speed_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `wave_speed_standard_uncertainty_m_s` | 예 | `{"minimum": 0, "type": "number"}` | m/s |
| `wave_speed_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wave_speed_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wave_speed_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_supported_wave_speed_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `maximum_supported_wave_speed_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `support_minimum_position_m` | 예 | `{"maxItems": 3, "minItems": 3, "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}], "type": "array"}` | m |
| `support_maximum_position_m` | 예 | `{"maxItems": 3, "minItems": 3, "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}], "type": "array"}` | m |
| `maximum_iterations` | 예 | `{"maximum": 100, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `position_tolerance_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `sensor_frame_channel_calibration_and_coupling_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `homogeneous_isotropic_constant_speed_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pick_clock_method_uncertainty_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_source_partitions_and_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_position_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AEArrivalLocalization.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `coordinate_frame_id` | `1` |
| `event_localizations` | `mixed` |
| `rank_deficient_event_ids` | `1` |
| `outside_position_support_event_ids` | `1` |
| `holdout_position_errors_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Multi-sensor arrival-time localization in one reviewed frame with fixed caller-supplied wave speed.
- Pick and speed uncertainties weight the nonlinear least-squares residuals.
- Calibration and holdout physical sources and source groups are disjoint.

## 구현 근거·독립 설명

- `weighted_constant_speed_acoustic_emission_localization`: Estimate one acoustic-emission source position and origin time by weighted nonlinear least squares from caller-reviewed multi-sensor arrival picks, fixed homogeneous isotropic wave speed, sensor geometry, clock and uncertainty evidence. Preserve calibration/holdout source partitions, rank and spatial support diagnostics without generating picks or wave speed, classifying mechanisms, grading damage, deciding acceptance, life, POD or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.acoustic_emission_arrival_localization"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.acoustic_emission_arrival_localization"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "ae-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "coordinate_frame_id": "frame-1",
  "sensors": [
    {
      "sensor_id": "s0",
      "channel_id": "c0",
      "coordinate_frame_id": "frame-1",
      "position_m": [
        0.0,
        0.0,
        0.0
      ],
      "calibration_id": "cal-1",
      "coupling_state_id": "coupling-1",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "coupling_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "coordinate_frame_id": "frame-1",
      "position_m": [
        1.0,
        0.0,
        0.0
      ],
      "calibration_id": "cal-1",
      "coupling_state_id": "coupling-1",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "coupling_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "sensor_id": "s2",
      "channel_id": "c2",
      "coordinate_frame_id": "frame-1",
      "position_m": [
        0.0,
        1.0,
        0.0
      ],
      "calibration_id": "cal-1",
      "coupling_state_id": "coupling-1",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "coupling_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "sensor_id": "s3",
      "channel_id": "c3",
      "coordinate_frame_id": "frame-1",
      "position_m": [
        0.0,
        0.0,
        1.0
      ],
      "calibration_id": "cal-1",
      "coupling_state_id": "coupling-1",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "coupling_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "sensor_id": "s4",
      "channel_id": "c4",
      "coordinate_frame_id": "frame-1",
      "position_m": [
        1.0,
        1.0,
        1.0
      ],
      "calibration_id": "cal-1",
      "coupling_state_id": "coupling-1",
      "calibration_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "coupling_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
  "events": [
    {
      "event_id": "e1",
      "physical_source_id": "src1",
      "source_group_id": "g1",
      "partition": "calibration",
      "clock_id": "clock-1",
      "picks": [
        {
          "pick_id": "e1-p0",
          "sensor_id": "s0",
          "channel_id": "c0",
          "clock_id": "clock-1",
          "arrival_time_s": 0.010107703296142691,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e1-p1",
          "sensor_id": "s1",
          "channel_id": "c1",
          "clock_id": "clock-1",
          "arrival_time_s": 0.010188679622641132,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e1-p2",
          "sensor_id": "s2",
          "channel_id": "c2",
          "clock_id": "clock-1",
          "arrival_time_s": 0.010166132477258361,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e1-p3",
          "sensor_id": "s3",
          "channel_id": "c3",
          "clock_id": "clock-1",
          "arrival_time_s": 0.01014,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e1-p4",
          "sensor_id": "s4",
          "channel_id": "c4",
          "clock_id": "clock-1",
          "arrival_time_s": 0.010244131112314675,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
      "known_source_position_m": [
        0.2,
        0.3,
        0.4
      ],
      "known_source_position_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "event_id": "e2",
      "physical_source_id": "src2",
      "source_group_id": "g2",
      "partition": "holdout",
      "clock_id": "clock-1",
      "picks": [
        {
          "pick_id": "e2-p0",
          "sensor_id": "s0",
          "channel_id": "c0",
          "clock_id": "clock-1",
          "arrival_time_s": 0.02008774964387392,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e2-p1",
          "sensor_id": "s1",
          "channel_id": "c1",
          "clock_id": "clock-1",
          "arrival_time_s": 0.020153948043183406,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e2-p2",
          "sensor_id": "s2",
          "channel_id": "c2",
          "clock_id": "clock-1",
          "arrival_time_s": 0.02017804493814765,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e2-p3",
          "sensor_id": "s3",
          "channel_id": "c3",
          "clock_id": "clock-1",
          "arrival_time_s": 0.020166433169770934,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
          "pick_id": "e2-p4",
          "sensor_id": "s4",
          "channel_id": "c4",
          "clock_id": "clock-1",
          "arrival_time_s": 0.020260192236625153,
          "standard_uncertainty_s": 1e-06,
          "pick_method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
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
      "known_source_position_m": [
        0.3,
        0.2,
        0.25
      ],
      "known_source_position_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
  "wave_speed_m_s": 5000.0,
  "wave_speed_standard_uncertainty_m_s": 10.0,
  "wave_speed_provider_id": "speed-provider",
  "wave_speed_provider_revision": "1",
  "wave_speed_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "minimum_supported_wave_speed_m_s": 4000.0,
  "maximum_supported_wave_speed_m_s": 6000.0,
  "support_minimum_position_m": [
    0.0,
    0.0,
    0.0
  ],
  "support_maximum_position_m": [
    1.0,
    1.0,
    1.0
  ],
  "maximum_iterations": 30,
  "position_tolerance_m": 1e-10,
  "sensor_frame_channel_calibration_and_coupling_reviewed": true,
  "homogeneous_isotropic_constant_speed_assumption_reviewed": true,
  "pick_clock_method_uncertainty_and_digests_reviewed": true,
  "physical_source_partitions_and_independence_reviewed": true,
  "caller_position_support_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/acoustic_emission_localization.py#L182)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
