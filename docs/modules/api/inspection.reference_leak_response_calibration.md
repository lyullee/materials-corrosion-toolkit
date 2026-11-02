# `inspection.reference_leak_response_calibration`

**목적:** Only valid detected rows with positive traceable molar leak rate and response enter the fit.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_gas_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `boundary_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `leak_quantity_definition` | 아니오 | `{"const": "molar_flow_rate", "default": "molar_flow_rate", "type": "string"}` | 계약·필드 설명 참조 |
| `leak_rate_unit_token` | 아니오 | `{"const": "mol/s", "default": "mol/s", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_temperature_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `log_reference_leak_rate_mol_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `log_reference_response_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_clock_alignment_error_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ReferenceLeakResponseObservation"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_detected_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_detected_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_independence_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `instrument_configuration_gas_and_boundary_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_alignment_and_physical_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `si_leak_quantity_pressure_and_temperature_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_traceability_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `response_definition_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `partition_and_group_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `censored_missing_and_invalid_status_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_and_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ReferenceLeakResponseCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `observation_clock_id` | `1` |
| `log_response_intercept` | `1` |
| `log_response_log_leak_slope` | `1` |
| `calibration_leak_rate_minimum_mol_s` | `mol/s` |
| `calibration_leak_rate_maximum_mol_s` | `mol/s` |
| `included_calibration_observation_ids` | `1` |
| `included_holdout_observation_ids` | `1` |
| `excluded_observations` | `mixed` |
| `outside_calibration_support_holdout_ids` | `1` |
| `calibration_source_group_ids` | `1` |
| `holdout_source_group_ids` | `1` |
| `holdout_independence_group_ids` | `1` |
| `holdout_log_response_bias` | `1` |
| `holdout_log_response_rmse` | `1` |
| `holdout_residuals` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only valid detected rows with positive traceable molar leak rate and response enter the fit.
- Calibration and holdout specimens, reference leaks, source groups and independence groups are disjoint.
- Holdout leak rates are evaluated only inside calibration support; no unknown-leak inversion is performed.

## 구현 근거·독립 설명

- `authored_reference_leak_log_response_regression`: Fit detected, clock-aligned instrument response against traceable positive molar reference-leak rate in a fixed weighted log-log regression. Preserve gas, boundary, instrument configuration, uncertainties, provider digests and excluded non-detect/censored/missing rows; evaluate holdout only inside reference-leak support without inverting unknown leaks, estimating detection probability, deciding acceptance or creating FTA probabilities.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.reference_leak_response_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.reference_leak_response_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "leak-calibration-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "observation_clock_id": "clock-1",
  "time_basis": "reference-clock",
  "instrument_id": "instrument-1",
  "instrument_configuration_id": "configuration-1",
  "test_gas_id": "gas-1",
  "boundary_condition_id": "boundary-1",
  "leak_quantity_definition": "molar_flow_rate",
  "leak_rate_unit_token": "mol/s",
  "pressure_basis": "caller absolute upstream and downstream pressure basis",
  "reference_temperature_basis": "caller traceable reference temperature basis",
  "response_definition": "caller instrument response amplitude",
  "response_unit_token": "custom-response-unit",
  "log_reference_leak_rate_mol_s": 1,
  "log_reference_response_value": 1,
  "maximum_clock_alignment_error_s": 0.1,
  "observations": [
    {
      "observation_id": "calibration-a",
      "partition": "calibration",
      "physical_specimen_id": "specimen-calibration-a",
      "reference_leak_id": "reference-calibration-a",
      "source_group_id": "source-calibration-a",
      "independence_group_id": "independence-calibration-a",
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "test_gas_id": "gas-1",
      "boundary_condition_id": "boundary-1",
      "observation_clock_id": "clock-1",
      "reference_time_s": 10,
      "response_time_s": 10,
      "reporting_status": "detected",
      "reference_leak_rate_mol_s": 1,
      "expanded_reference_leak_uncertainty_mol_s": 0.01,
      "response_value": 2,
      "response_unit_token": "custom-response-unit",
      "expanded_response_uncertainty": 0.04,
      "response_detection_limit": null,
      "sample_weight": 1,
      "exclusion_or_status_basis": null,
      "reference_provider_id": "reference-provider",
      "reference_provider_revision": "1",
      "reference_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "instrument_provider_id": "instrument-provider",
      "instrument_provider_revision": "1",
      "instrument_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
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
      "observation_id": "calibration-b",
      "partition": "calibration",
      "physical_specimen_id": "specimen-calibration-b",
      "reference_leak_id": "reference-calibration-b",
      "source_group_id": "source-calibration-b",
      "independence_group_id": "independence-calibration-b",
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "test_gas_id": "gas-1",
      "boundary_condition_id": "boundary-1",
      "observation_clock_id": "clock-1",
      "reference_time_s": 10,
      "response_time_s": 10,
      "reporting_status": "detected",
      "reference_leak_rate_mol_s": 4,
      "expanded_reference_leak_uncertainty_mol_s": 0.04,
      "response_value": 4,
      "response_unit_token": "custom-response-unit",
      "expanded_response_uncertainty": 0.08,
      "response_detection_limit": null,
      "sample_weight": 1,
      "exclusion_or_status_basis": null,
      "reference_provider_id": "reference-provider",
      "reference_provider_revision": "1",
      "reference_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "instrument_provider_id": "instrument-provider",
      "instrument_provider_revision": "1",
      "instrument_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
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
      "observation_id": "calibration-c",
      "partition": "calibration",
      "physical_specimen_id": "specimen-calibration-c",
      "reference_leak_id": "reference-calibration-c",
      "source_group_id": "source-calibration-c",
      "independence_group_id": "independence-calibration-c",
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "test_gas_id": "gas-1",
      "boundary_condition_id": "boundary-1",
      "observation_clock_id": "clock-1",
      "reference_time_s": 10,
      "response_time_s": 10,
      "reporting_status": "detected",
      "reference_leak_rate_mol_s": 16,
      "expanded_reference_leak_uncertainty_mol_s": 0.16,
      "response_value": 8,
      "response_unit_token": "custom-response-unit",
      "expanded_response_uncertainty": 0.16,
      "response_detection_limit": null,
      "sample_weight": 1,
      "exclusion_or_status_basis": null,
      "reference_provider_id": "reference-provider",
      "reference_provider_revision": "1",
      "reference_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "instrument_provider_id": "instrument-provider",
      "instrument_provider_revision": "1",
      "instrument_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
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
      "observation_id": "holdout-d",
      "partition": "holdout",
      "physical_specimen_id": "specimen-holdout-d",
      "reference_leak_id": "reference-holdout-d",
      "source_group_id": "source-holdout-d",
      "independence_group_id": "independence-holdout-d",
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "test_gas_id": "gas-1",
      "boundary_condition_id": "boundary-1",
      "observation_clock_id": "clock-1",
      "reference_time_s": 10,
      "response_time_s": 10,
      "reporting_status": "detected",
      "reference_leak_rate_mol_s": 9,
      "expanded_reference_leak_uncertainty_mol_s": 0.09,
      "response_value": 6,
      "response_unit_token": "custom-response-unit",
      "expanded_response_uncertainty": 0.12,
      "response_detection_limit": null,
      "sample_weight": 1,
      "exclusion_or_status_basis": null,
      "reference_provider_id": "reference-provider",
      "reference_provider_revision": "1",
      "reference_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "instrument_provider_id": "instrument-provider",
      "instrument_provider_revision": "1",
      "instrument_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
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
  "minimum_calibration_detected_count": 3,
  "minimum_holdout_detected_count": 1,
  "minimum_calibration_source_group_count": 3,
  "minimum_holdout_source_group_count": 1,
  "minimum_holdout_independence_group_count": 1,
  "instrument_configuration_gas_and_boundary_reviewed": true,
  "clock_alignment_and_physical_scope_reviewed": true,
  "si_leak_quantity_pressure_and_temperature_basis_reviewed": true,
  "reference_traceability_and_uncertainty_reviewed": true,
  "response_definition_units_and_uncertainty_reviewed": true,
  "partition_and_group_independence_reviewed": true,
  "censored_missing_and_invalid_status_reviewed": true,
  "provider_and_result_digests_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reference_leak_calibration.py#L144)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
