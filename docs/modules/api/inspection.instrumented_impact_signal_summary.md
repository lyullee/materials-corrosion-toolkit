# `inspection.instrumented_impact_signal_summary`

**목적:** The supplied signal is calibrated SI force, displacement and time with a reviewed sign convention and valid window.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `impact_test_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `independence_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `notch_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `notch_orientation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_orientation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `signal_source_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `force_unit_token` | 아니오 | `{"const": "N", "default": "N", "type": "string"}` | 계약·필드 설명 참조 |
| `displacement_unit_token` | 아니오 | `{"const": "m", "default": "m", "type": "string"}` | 계약·필드 설명 참조 |
| `time_unit_token` | 아니오 | `{"const": "s", "default": "s", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration` | 예 | `{"$ref": "#/$defs/ImpactInstrumentCalibration"}` | 계약·필드 설명 참조 |
| `signal_points` | 예 | `{"items": {"$ref": "#/$defs/ImpactSignalPoint"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `valid_window_start_sample_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `valid_window_end_sample_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `absorbed_energy_force_direction_multiplier` | 예 | `{"enum": [-1, 1], "type": "integer"}` | 계약·필드 설명 참조 |
| `force_sign_convention` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `peak_force_plateau_tolerance_N` | 예 | `{"minimum": 0, "type": "number"}` | N |
| `negative_absorbed_energy_tolerance_J` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `machine_reported_energy` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/MachineReportedImpactEnergy"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `specimen_notch_orientation_and_material_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_temperature_striker_and_instrument_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_si_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_digest_and_raw_signal_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `monotonic_displacement_and_time_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `valid_window_and_force_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `trapezoidal_integration_and_peak_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `machine_energy_comparison_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/InstrumentedImpactSignalAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `impact_test_id` | `1` |
| `physical_specimen_id` | `1` |
| `valid_window_sample_ids` | `1` |
| `valid_window_start_time_s` | `s` |
| `valid_window_end_time_s` | `s` |
| `valid_window_start_displacement_m` | `m` |
| `valid_window_end_displacement_m` | `m` |
| `force_direction_multiplier` | `1` |
| `trapezoidal_interval_work` | `mixed` |
| `absorbed_energy_J` | `J` |
| `peak_directed_force_N` | `N` |
| `peak_plateau_sample_ids` | `1` |
| `peak_first_time_s` | `s` |
| `peak_last_time_s` | `s` |
| `peak_first_displacement_m` | `m` |
| `peak_last_displacement_m` | `m` |
| `invalid_samples_outside_window_ids` | `1` |
| `machine_energy_comparison` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The supplied signal is calibrated SI force, displacement and time with a reviewed sign convention and valid window.
- Displacement is monotonic nondecreasing and energy uses adjacent-sample trapezoidal integration without filtering.
- Signal reduction does not identify crack initiation or establish toughness, transition behavior or acceptance.

## 구현 근거·독립 설명

- `authored_trapezoidal_instrumented_impact_reduction`: Reduce one provenance-bound instrumented impact force-displacement-time signal over a caller-reviewed valid window using explicit force sign, trapezoidal work integration and plateau-aware peak reporting. Preserve specimen, notch, orientation, temperature, striker, calibration and optional independent machine-energy evidence without inferring crack initiation, transition temperature, toughness, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.instrumented_impact_signal_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.instrumented_impact_signal_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "impact-machine-1",
  "impact_test_id": "impact-test-1",
  "physical_specimen_id": "specimen-1",
  "source_group_id": "source-1",
  "independence_group_id": "independence-1",
  "material_condition_id": "condition-1",
  "specimen_geometry_id": "geometry-1",
  "notch_geometry_id": "notch-1",
  "notch_orientation_id": "notch-orientation-1",
  "specimen_orientation_id": "specimen-orientation-1",
  "test_temperature_K": 250.0,
  "signal_source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "force_unit_token": "N",
  "displacement_unit_token": "m",
  "time_unit_token": "s",
  "calibration": {
    "calibration_record_id": "calibration-1",
    "striker_id": "striker-1",
    "striker_configuration_id": "striker-configuration-1",
    "force_instrument_id": "force-instrument-1",
    "displacement_instrument_id": "displacement-instrument-1",
    "timebase_id": "timebase-1",
    "force_calibration_id": "force-calibration-1",
    "displacement_calibration_id": "displacement-calibration-1",
    "force_calibration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "displacement_calibration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "timebase_calibration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "instrument_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "provider_id": "calibration-provider",
    "provider_revision": "1",
    "calibration_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "record_valid": true,
    "invalid_or_missing_basis": null,
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
  "signal_points": [
    {
      "sample_id": "p0",
      "elapsed_time_s": 0.0,
      "displacement_m": 0.0,
      "signed_force_N": 0.0,
      "expanded_force_uncertainty_N": 10.0,
      "expanded_displacement_uncertainty_m": 1e-06,
      "record_valid": true,
      "invalid_or_missing_basis": null,
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
      "sample_id": "p1",
      "elapsed_time_s": 0.001,
      "displacement_m": 0.001,
      "signed_force_N": 1000.0,
      "expanded_force_uncertainty_N": 10.0,
      "expanded_displacement_uncertainty_m": 1e-06,
      "record_valid": true,
      "invalid_or_missing_basis": null,
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
      "sample_id": "p2",
      "elapsed_time_s": 0.002,
      "displacement_m": 0.002,
      "signed_force_N": 1000.0,
      "expanded_force_uncertainty_N": 10.0,
      "expanded_displacement_uncertainty_m": 1e-06,
      "record_valid": true,
      "invalid_or_missing_basis": null,
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
      "sample_id": "p3",
      "elapsed_time_s": 0.003,
      "displacement_m": 0.003,
      "signed_force_N": 500.0,
      "expanded_force_uncertainty_N": 10.0,
      "expanded_displacement_uncertainty_m": 1e-06,
      "record_valid": true,
      "invalid_or_missing_basis": null,
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
      "sample_id": "p4",
      "elapsed_time_s": 0.004,
      "displacement_m": 0.004,
      "signed_force_N": 0.0,
      "expanded_force_uncertainty_N": 10.0,
      "expanded_displacement_uncertainty_m": 1e-06,
      "record_valid": true,
      "invalid_or_missing_basis": null,
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
  "valid_window_start_sample_id": "p0",
  "valid_window_end_sample_id": "p4",
  "absorbed_energy_force_direction_multiplier": 1,
  "force_sign_convention": "positive force performs positive work along increasing displacement",
  "peak_force_plateau_tolerance_N": 0.0,
  "negative_absorbed_energy_tolerance_J": 1e-12,
  "machine_reported_energy": {
    "comparison_record_id": "machine-energy-1",
    "reported_energy_J": 2.6,
    "expanded_uncertainty_J": 0.1,
    "uncertainty_coverage_factor": 2.0,
    "reporting_method_id": "machine-channel-1",
    "independent_data_path_declared": true,
    "provider_id": "machine-provider",
    "provider_revision": "1",
    "configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "record_valid": true,
    "invalid_or_missing_basis": null,
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
  "specimen_notch_orientation_and_material_reviewed": true,
  "test_temperature_striker_and_instrument_identity_reviewed": true,
  "calibration_and_si_units_reviewed": true,
  "source_digest_and_raw_signal_reviewed": true,
  "monotonic_displacement_and_time_order_reviewed": true,
  "valid_window_and_force_sign_reviewed": true,
  "trapezoidal_integration_and_peak_definition_reviewed": true,
  "machine_energy_comparison_independence_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/instrumented_impact_signal.py#L135)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
