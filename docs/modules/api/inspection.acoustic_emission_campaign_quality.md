# `inspection.acoustic_emission_campaign_quality`

**목적:** Array, coupling, acquisition, baseline, observation and reference identities are caller supplied.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `family` | 예 | `{"enum": ["acoustic_emission", "guided_waves"], "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `extent_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `acquisition_configuration` | 예 | `{"$ref": "#/$defs/WaveAcquisitionConfiguration"}` | 계약·필드 설명 참조 |
| `records` | 예 | `{"items": {"$ref": "#/$defs/WaveAcquisitionRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `acceptance_profile` | 예 | `{"$ref": "#/$defs/WaveCampaignAcceptanceProfile"}` | 계약·필드 설명 참조 |
| `procedure_array_and_acquisition_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coupling_and_clock_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_reference_source_checks_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `baseline_observation_identity_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `channel_mapping_and_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `timing_amplitude_noise_localization_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_acceptance_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_validity_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WaveCampaignQualityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `family` | `1` |
| `quality_outcome` | `1` |
| `acceptance_profile_id` | `1` |
| `metric_values` | `mixed` |
| `criterion_findings` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_acceptance_profile_only` | `1` |
| `automatic_damage_detection_or_sizing` | `1` |
| `pod_claimed` | `1` |
| `physical_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Array, coupling, acquisition, baseline, observation and reference identities are caller supplied.
- No automatic damage detection, sizing, POD, acceptance or physical qualification is produced.

## 구현 근거·독립 설명

- `authored_wave_reference_baseline_campaign_quality_audit`: Aggregate caller-supplied acoustic-emission or guided-wave array, coupling, acquisition, baseline, observation, channel, coverage and reference-check evidence. Compare timing, amplitude, noise, localization and reference consistency only with caller-authored criteria. Do not detect or size damage, estimate POD, apply published acceptance limits or claim physical qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.acoustic_emission_campaign_quality"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.acoustic_emission_campaign_quality"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "acoustic_emission-assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "family": "acoustic_emission",
  "procedure_id": "procedure-1",
  "procedure_revision": "rev-1",
  "extent_unit_token": "m",
  "acquisition_configuration": {
    "configuration_id": "configuration-1",
    "family": "acoustic_emission",
    "array_id": "array-1",
    "elements": [
      {
        "element_id": "element-1",
        "channel_id": "channel-1",
        "element_kind": "sensor",
        "physical_position_definition": "reviewed asset coordinate",
        "calibration_id": "calibration-1",
        "calibration_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored wave audit",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "coupling_method": "caller documented coupling method",
    "coupling_state_id": "coupling-state-1",
    "coupling_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "clock_id": "clock-1",
    "sampling_rate_hz": 1000000.0,
    "acquisition_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored wave audit",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "records": [
    {
      "record_id": "baseline-1",
      "record_role": "baseline",
      "configuration_id": "configuration-1",
      "coupling_state_id": "coupling-state-1",
      "clock_id": "clock-1",
      "source_group_id": "source-baseline-1",
      "independence_group_id": "independence-baseline-1",
      "active_channel_ids": [
        "channel-1"
      ],
      "target_extent": 100.0,
      "examined_extent": 100.0,
      "extent_unit_token": "m",
      "encoded_data_id": "data-baseline-1",
      "encoded_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "encoded_data_format": "caller encoded waveform container",
      "reference_checks": [
        {
          "check_id": "baseline-1-pre",
          "sequence_index": 0,
          "elapsed_time_s": 0.0,
          "check_stage": "pre_acquisition",
          "reference_source_id": "reference-source-1",
          "reference_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "channel_id": "channel-1",
          "source_group_id": "source-group-1",
          "independence_group_id": "independence-group-1",
          "timing_error_s": 0.0001,
          "expanded_timing_uncertainty_s": 2e-05,
          "amplitude_metric": 10.0,
          "amplitude_unit_token": "signal-unit",
          "expanded_amplitude_uncertainty": 0.2,
          "noise_metric": 1.0,
          "noise_unit_token": "noise-unit",
          "expanded_noise_uncertainty": 0.1,
          "localization_error_m": 0.02,
          "expanded_localization_uncertainty_m": 0.005,
          "reference_consistency_error": 0.02,
          "expanded_consistency_uncertainty": 0.01,
          "check_method_definition": "caller reference-source consistency check",
          "check_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored wave audit",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "check_id": "baseline-1-post",
          "sequence_index": 1,
          "elapsed_time_s": 1.0,
          "check_stage": "post_acquisition",
          "reference_source_id": "reference-source-1",
          "reference_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "channel_id": "channel-1",
          "source_group_id": "source-group-1",
          "independence_group_id": "independence-group-1",
          "timing_error_s": 0.0001,
          "expanded_timing_uncertainty_s": 2e-05,
          "amplitude_metric": 10.0,
          "amplitude_unit_token": "signal-unit",
          "expanded_amplitude_uncertainty": 0.2,
          "noise_metric": 1.0,
          "noise_unit_token": "noise-unit",
          "expanded_noise_uncertainty": 0.1,
          "localization_error_m": 0.02,
          "expanded_localization_uncertainty_m": 0.005,
          "reference_consistency_error": 0.02,
          "expanded_consistency_uncertainty": 0.01,
          "check_method_definition": "caller reference-source consistency check",
          "check_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored wave audit",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored wave audit",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "record_id": "observation-1",
      "record_role": "observation",
      "configuration_id": "configuration-1",
      "coupling_state_id": "coupling-state-1",
      "clock_id": "clock-1",
      "source_group_id": "source-observation-1",
      "independence_group_id": "independence-observation-1",
      "active_channel_ids": [
        "channel-1"
      ],
      "target_extent": 100.0,
      "examined_extent": 100.0,
      "extent_unit_token": "m",
      "encoded_data_id": "data-observation-1",
      "encoded_data_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "encoded_data_format": "caller encoded waveform container",
      "reference_checks": [
        {
          "check_id": "observation-1-pre",
          "sequence_index": 2,
          "elapsed_time_s": 2.0,
          "check_stage": "pre_acquisition",
          "reference_source_id": "reference-source-1",
          "reference_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "channel_id": "channel-1",
          "source_group_id": "source-group-1",
          "independence_group_id": "independence-group-1",
          "timing_error_s": 0.0001,
          "expanded_timing_uncertainty_s": 2e-05,
          "amplitude_metric": 10.0,
          "amplitude_unit_token": "signal-unit",
          "expanded_amplitude_uncertainty": 0.2,
          "noise_metric": 1.0,
          "noise_unit_token": "noise-unit",
          "expanded_noise_uncertainty": 0.1,
          "localization_error_m": 0.02,
          "expanded_localization_uncertainty_m": 0.005,
          "reference_consistency_error": 0.02,
          "expanded_consistency_uncertainty": 0.01,
          "check_method_definition": "caller reference-source consistency check",
          "check_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored wave audit",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "check_id": "observation-1-post",
          "sequence_index": 3,
          "elapsed_time_s": 3.0,
          "check_stage": "post_acquisition",
          "reference_source_id": "reference-source-1",
          "reference_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "channel_id": "channel-1",
          "source_group_id": "source-group-1",
          "independence_group_id": "independence-group-1",
          "timing_error_s": 0.0001,
          "expanded_timing_uncertainty_s": 2e-05,
          "amplitude_metric": 10.0,
          "amplitude_unit_token": "signal-unit",
          "expanded_amplitude_uncertainty": 0.2,
          "noise_metric": 1.0,
          "noise_unit_token": "noise-unit",
          "expanded_noise_uncertainty": 0.1,
          "localization_error_m": 0.02,
          "expanded_localization_uncertainty_m": 0.005,
          "reference_consistency_error": 0.02,
          "expanded_consistency_uncertainty": 0.01,
          "check_method_definition": "caller reference-source consistency check",
          "check_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored wave audit",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored wave audit",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "acceptance_profile": {
    "profile_id": "acoustic_emission-profile-1",
    "profile_version": "1.0.0",
    "family": "acoustic_emission",
    "required_check_stages": [
      "pre_acquisition",
      "post_acquisition"
    ],
    "amplitude_metric_definition": "caller reference response amplitude",
    "amplitude_unit_token": "signal-unit",
    "noise_metric_definition": "caller background noise measure",
    "noise_unit_token": "noise-unit",
    "reference_consistency_metric_definition": "absolute caller reference consistency error",
    "criteria": [
      {
        "criterion_id": "criterion-record_count",
        "metric_id": "record_count",
        "direction": "minimum",
        "pass_limit": 2.0,
        "fail_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-baseline_count",
        "metric_id": "baseline_count",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-observation_count",
        "metric_id": "observation_count",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-coverage_fraction",
        "metric_id": "coverage_fraction",
        "direction": "minimum",
        "pass_limit": 0.9,
        "fail_limit": 0.7,
        "unit_token": "1",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-channel_coverage_fraction",
        "metric_id": "channel_coverage_fraction",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-reference_stage_coverage_fraction",
        "metric_id": "reference_stage_coverage_fraction",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-maximum_absolute_timing_error_s",
        "metric_id": "maximum_absolute_timing_error_s",
        "direction": "maximum",
        "pass_limit": 0.001,
        "fail_limit": 0.01,
        "unit_token": "s",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-minimum_amplitude_metric",
        "metric_id": "minimum_amplitude_metric",
        "direction": "minimum",
        "pass_limit": 8.0,
        "fail_limit": 5.0,
        "unit_token": "signal-unit",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-maximum_noise_metric",
        "metric_id": "maximum_noise_metric",
        "direction": "maximum",
        "pass_limit": 2.0,
        "fail_limit": 4.0,
        "unit_token": "noise-unit",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-maximum_localization_error_m",
        "metric_id": "maximum_localization_error_m",
        "direction": "maximum",
        "pass_limit": 0.05,
        "fail_limit": 0.1,
        "unit_token": "m",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      },
      {
        "criterion_id": "criterion-maximum_reference_consistency_error",
        "metric_id": "maximum_reference_consistency_error",
        "direction": "maximum",
        "pass_limit": 0.05,
        "fail_limit": 0.1,
        "unit_token": "1",
        "criterion_basis": "caller-authored wave campaign quality threshold"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_acceptance_authority": "caller inspection review team",
    "built_in_code_or_standard_limits_used": false,
    "automatic_damage_detection_or_sizing_claimed": false,
    "pod_claimed": false,
    "physical_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored wave audit",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "procedure_array_and_acquisition_identity_reviewed": true,
  "coupling_and_clock_identity_reviewed": true,
  "calibration_and_reference_source_checks_reviewed": true,
  "baseline_observation_identity_and_digests_reviewed": true,
  "channel_mapping_and_coverage_reviewed": true,
  "timing_amplitude_noise_localization_units_and_uncertainty_reviewed": true,
  "source_and_independence_groups_reviewed": true,
  "caller_acceptance_profile_reviewed": true,
  "record_validity_and_missingness_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored wave audit",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/wave_campaign_quality.py#L312)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
