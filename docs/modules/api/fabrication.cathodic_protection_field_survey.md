# `fabrication.cathodic_protection_field_survey`

**목적:** Field potential conventions, reference-electrode calibration and IR-drop status remain explicit.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `survey_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `structure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `zone_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `electrolyte_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_calibrations` | 예 | `{"items": {"$ref": "#/$defs/ReferenceElectrodeCalibration"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `potential_observations` | 예 | `{"items": {"$ref": "#/$defs/CathodicPotentialObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `current_observations` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CathodicCurrentObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_thresholds` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CallerPotentialThreshold"}, "type": "array"}` | 계약·필드 설명 참조 |
| `structure_zone_reference_and_location_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_electrode_calibrations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `potential_conventions_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rectifier_anode_current_and_sign_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ir_drop_handling_status_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_electrolyte_and_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_provider_and_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missing_and_invalid_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_threshold_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CathodicProtectionFieldSurvey.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `survey_id` | `1` |
| `physical_scope_id` | `1` |
| `structure_id` | `1` |
| `zone_id` | `1` |
| `clock_id` | `1` |
| `potential_summary_by_native_convention` | `mixed` |
| `current_summary_by_source_kind` | `mixed` |
| `potential_threshold_margins` | `mixed` |
| `ir_drop_handling_records` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Field potential conventions, reference-electrode calibration and IR-drop status remain explicit.
- Current signs, source identities, clock and environment are caller-reviewed records.
- Thresholds are caller inputs and yield margins only, without compliance inference.

## 구현 근거·독립 설명

- `authored_cathodic_protection_field_survey_summary`: Preserve native, on, off and instant-off potential conventions, reference-electrode calibration support, IR-drop handling, rectifier or anode current, environment, uncertainty and immutable evidence identities. Summarize observations and caller-owned directional threshold margins without embedded protection criteria, coating inference, remaining life, compliance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.cathodic_protection_field_survey"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.cathodic_protection_field_survey"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "survey_id": "survey-1",
  "asset_id": "asset-1",
  "location_id": "survey-location-1",
  "physical_scope_id": "structure-zone-scope-1",
  "structure_id": "structure-1",
  "zone_id": "zone-1",
  "clock_id": "clock-1",
  "electrolyte_id": "electrolyte-1",
  "environment_id": "environment-1",
  "reference_calibrations": [
    {
      "calibration_id": "calibration-1",
      "reference_electrode_id": "reference-1",
      "reference_electrode_type_id": "reference-type-1",
      "minimum_supported_temperature_K": 285.0,
      "maximum_supported_temperature_K": 305.0,
      "reported_offset_V": 0.0,
      "expanded_uncertainty_V": 0.005,
      "provider_id": "calibration-provider",
      "provider_revision": "1",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "potential_observations": [
    {
      "observation_id": "p-1",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "measurement_location_id": "location-p-1",
      "location_definition": "authored survey location",
      "elapsed_time_s": 0.0,
      "potential_convention": "native",
      "reference_electrode_id": "reference-1",
      "calibration_id": "calibration-1",
      "potential_V": -0.65,
      "expanded_uncertainty_V": 0.01,
      "ir_drop_handling_status": "not_applicable",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "p-2",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "measurement_location_id": "location-p-2",
      "location_definition": "authored survey location",
      "elapsed_time_s": 10.0,
      "potential_convention": "on",
      "reference_electrode_id": "reference-1",
      "calibration_id": "calibration-1",
      "potential_V": -0.95,
      "expanded_uncertainty_V": 0.01,
      "ir_drop_handling_status": "not_corrected",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "p-3",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "measurement_location_id": "location-p-3",
      "location_definition": "authored survey location",
      "elapsed_time_s": 20.0,
      "potential_convention": "instant_off",
      "reference_electrode_id": "reference-1",
      "calibration_id": "calibration-1",
      "potential_V": -0.9,
      "expanded_uncertainty_V": 0.01,
      "ir_drop_handling_status": "instant_off_used",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "p-4",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "measurement_location_id": "location-p-4",
      "location_definition": "authored survey location",
      "elapsed_time_s": 30.0,
      "potential_convention": "instant_off",
      "reference_electrode_id": "reference-1",
      "calibration_id": "calibration-1",
      "potential_V": -0.88,
      "expanded_uncertainty_V": 0.01,
      "ir_drop_handling_status": "instant_off_used",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "current_observations": [
    {
      "observation_id": "c-1",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "source_kind": "rectifier",
      "source_id": "source-rectifier-1",
      "measurement_location_id": "current-location-1",
      "elapsed_time_s": 0.0,
      "current_A": 10.0,
      "expanded_uncertainty_A": 0.1,
      "current_sign_basis": "positive current delivered to structure",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "c-2",
      "structure_id": "structure-1",
      "zone_id": "zone-1",
      "source_kind": "rectifier",
      "source_id": "source-rectifier-1",
      "measurement_location_id": "current-location-1",
      "elapsed_time_s": 10.0,
      "current_A": 12.0,
      "expanded_uncertainty_A": 0.1,
      "current_sign_basis": "positive current delivered to structure",
      "specimen_temperature_K": 295.0,
      "electrolyte_id": "electrolyte-1",
      "environment_id": "environment-1",
      "record_status": "observed",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_thresholds": [
    {
      "threshold_id": "threshold-1",
      "potential_convention": "instant_off",
      "reference_electrode_id": "reference-1",
      "comparison_direction": "at_or_more_negative",
      "threshold_V": -0.85,
      "threshold_basis": "authored caller threshold",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "structure_zone_reference_and_location_identity_reviewed": true,
  "reference_electrode_calibrations_reviewed": true,
  "potential_conventions_and_clock_reviewed": true,
  "rectifier_anode_current_and_sign_basis_reviewed": true,
  "ir_drop_handling_status_reviewed": true,
  "temperature_electrolyte_and_environment_reviewed": true,
  "uncertainty_provider_and_result_digests_reviewed": true,
  "missing_and_invalid_records_reviewed": true,
  "caller_threshold_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/cathodic_protection_survey.py#L169)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
