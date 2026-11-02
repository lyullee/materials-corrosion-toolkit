# `inspection.cryogenic_leak_testing_campaign_quality`

**목적:** Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied.

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
| `campaign_family` | 예 | `{"enum": ["leak_rate", "vacuum_testing", "cryogenic_leak_testing"], "type": "string"}` | 계약·필드 설명 참조 |
| `method_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `test_gas_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `states` | 예 | `{"items": {"$ref": "#/$defs/LeakCampaignStateIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `reference_points` | 예 | `{"items": {"$ref": "#/$defs/ReferenceLeakCampaignPoint"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `blank_background_observations` | 예 | `{"items": {"$ref": "#/$defs/BlankBackgroundObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `detection_capability` | 예 | `{"$ref": "#/$defs/DetectionCapabilityEvidence"}` | 계약·필드 설명 참조 |
| `acceptance_profile` | 예 | `{"$ref": "#/$defs/LeakCampaignAcceptanceProfile"}` | 계약·필드 설명 참조 |
| `campaign_method_instrument_and_gas_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_pressure_and_state_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_leak_traceability_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `blank_and_background_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `repeatability_and_drift_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `detection_threshold_or_uncertainty_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_acceptance_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_digests_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LeakTestCampaignQualityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `campaign_family` | `1` |
| `quality_outcome` | `1` |
| `acceptance_profile_id` | `1` |
| `acceptance_profile_version` | `1` |
| `metric_values` | `mixed` |
| `criterion_findings` | `mixed` |
| `reference_point_ids` | `1` |
| `blank_background_observation_ids` | `1` |
| `state_ids` | `1` |
| `detection_capability_evidence_id` | `1` |
| `caller_acceptance_profile_only` | `1` |
| `physical_qualification` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied.
- Criteria and pass/review/fail boundaries are caller owned and unit exact.
- Campaign quality is separate from calibration, physical qualification and field acceptance.

## 구현 근거·독립 설명

- `authored_caller_leak_campaign_quality_audit`: Aggregate caller-supplied traceable reference-leak responses, blanks, state identities, repeat groups, sequence, uncertainty or detection-threshold evidence. Compare only derived repeatability, drift, background and uncertainty descriptors with caller-authored criteria. Do not fit a leak calibration, infer detection probability, solve leak physics, apply a published acceptance table or claim physical qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.cryogenic_leak_testing_campaign_quality"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.cryogenic_leak_testing_campaign_quality"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "cryogenic_leak_testing-campaign-audit-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "campaign_family": "cryogenic_leak_testing",
  "method_id": "method-1",
  "instrument_id": "instrument-1",
  "instrument_configuration_id": "instrument-config-1",
  "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "test_gas_id": "gas-1",
  "response_definition": "caller instrument response",
  "response_unit_token": "instrument-count",
  "clock_id": "clock-1",
  "states": [
    {
      "state_id": "state-1",
      "temperature_K": 300.0,
      "expanded_temperature_uncertainty_K": 0.5,
      "internal_pressure_Pa": 100000.0,
      "external_pressure_Pa": 1000.0,
      "expanded_pressure_uncertainty_Pa": 100.0,
      "pressure_basis": "caller absolute pressure basis",
      "thermal_and_phase_state_descriptor": "caller stable test state",
      "state_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "reference_points": [
    {
      "point_id": "reference-point-1",
      "sequence_index": 0,
      "elapsed_time_s": 0.0,
      "state_id": "state-1",
      "physical_reference_id": "reference-1",
      "reference_level_id": "level-1",
      "reference_leak_rate_mol_s": 1e-09,
      "expanded_reference_leak_uncertainty_mol_s": 1e-11,
      "response_value": 100.0,
      "expanded_response_uncertainty": 0.5,
      "response_unit_token": "instrument-count",
      "repeatability_group_id": "repeat-1",
      "drift_group_id": "drift-1",
      "source_group_id": "reference-source-1",
      "independence_group_id": "reference-independence-1",
      "observation_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "point_id": "reference-point-2",
      "sequence_index": 3,
      "elapsed_time_s": 10.0,
      "state_id": "state-1",
      "physical_reference_id": "reference-1",
      "reference_level_id": "level-1",
      "reference_leak_rate_mol_s": 1e-09,
      "expanded_reference_leak_uncertainty_mol_s": 1e-11,
      "response_value": 102.0,
      "expanded_response_uncertainty": 0.5,
      "response_unit_token": "instrument-count",
      "repeatability_group_id": "repeat-1",
      "drift_group_id": "drift-1",
      "source_group_id": "reference-source-1",
      "independence_group_id": "reference-independence-1",
      "observation_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "blank_background_observations": [
    {
      "observation_id": "background-1",
      "observation_kind": "background",
      "sequence_index": 1,
      "elapsed_time_s": 1.0,
      "state_id": "state-1",
      "response_value": 1.0,
      "expanded_response_uncertainty": 0.1,
      "response_unit_token": "instrument-count",
      "source_group_id": "background-source-1",
      "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "background-2",
      "observation_kind": "background",
      "sequence_index": 2,
      "elapsed_time_s": 2.0,
      "state_id": "state-1",
      "response_value": 1.5,
      "expanded_response_uncertainty": 0.1,
      "response_unit_token": "instrument-count",
      "source_group_id": "background-source-1",
      "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "detection_capability": {
    "evidence_id": "capability-1",
    "mode": "response_uncertainty_profile",
    "detection_threshold_response": null,
    "response_unit_token": null,
    "uncertainty_profile_id": "uncertainty-profile-1",
    "uncertainty_profile_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "capability_definition": "caller-reviewed response capability evidence",
    "capability_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "record_valid": true,
    "invalid_or_missing_basis": null,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored campaign test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "acceptance_profile": {
    "profile_id": "cryogenic_leak_testing-profile-1",
    "profile_version": "1.0.0",
    "campaign_family": "cryogenic_leak_testing",
    "criteria": [
      {
        "criterion_id": "criterion-reference_point_count",
        "metric_id": "reference_point_count",
        "direction": "minimum",
        "pass_limit": 2.0,
        "fail_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-distinct_reference_level_count",
        "metric_id": "distinct_reference_level_count",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-blank_background_count",
        "metric_id": "blank_background_count",
        "direction": "minimum",
        "pass_limit": 2.0,
        "fail_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-mean_absolute_blank_background_response",
        "metric_id": "mean_absolute_blank_background_response",
        "direction": "maximum",
        "pass_limit": 2.0,
        "fail_limit": 3.0,
        "unit_token": "instrument-count",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-maximum_repeatability_relative_standard_deviation",
        "metric_id": "maximum_repeatability_relative_standard_deviation",
        "direction": "maximum",
        "pass_limit": 0.05,
        "fail_limit": 0.1,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-maximum_drift_relative_change",
        "metric_id": "maximum_drift_relative_change",
        "direction": "maximum",
        "pass_limit": 0.05,
        "fail_limit": 0.1,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality boundary"
      },
      {
        "criterion_id": "criterion-maximum_relative_response_uncertainty",
        "metric_id": "maximum_relative_response_uncertainty",
        "direction": "maximum",
        "pass_limit": 0.2,
        "fail_limit": 0.4,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality boundary"
      }
    ],
    "profile_provider_id": "caller-profile-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_acceptance_authority": "caller engineering review group",
    "built_in_standard_criteria_used": false,
    "physical_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored campaign test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "campaign_method_instrument_and_gas_reviewed": true,
  "temperature_pressure_and_state_identity_reviewed": true,
  "reference_leak_traceability_and_uncertainty_reviewed": true,
  "blank_and_background_records_reviewed": true,
  "repeatability_and_drift_groups_reviewed": true,
  "detection_threshold_or_uncertainty_profile_reviewed": true,
  "caller_acceptance_profile_reviewed": true,
  "record_digests_and_missingness_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored campaign test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/leak_campaign_quality.py#L267)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
