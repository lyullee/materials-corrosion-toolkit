# `inspection.hardness_reference_block_calibration`

**목적:** One exact method, scale, indenter, load, dwell and instrument configuration is calibrated.

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
| `reference_block_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `method_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scale_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `indenter_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `applied_load_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `applied_load_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `dwell_time_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `dwell_time_tolerance_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `instrument_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `instrument_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `hardness_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_support_tolerance_K` | 예 | `{"minimum": 0, "type": "number"}` | K |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/HardnessReferenceObservation"}, "minItems": 8, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_record_count` | 예 | `{"minimum": 6, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_physical_block_count` | 예 | `{"minimum": 3, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_record_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `method_scale_indenter_load_and_dwell_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `instrument_identity_configuration_and_digest_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_block_condition_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `certificate_values_uncertainties_and_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `certificate_and_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bias_and_repeatability_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HardnessReferenceBlockCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `physical_scope_id` | `1` |
| `method_id` | `1` |
| `scale_id` | `1` |
| `instrument_configuration_id` | `1` |
| `hardness_unit_token` | `1` |
| `estimated_bias_observed_minus_certified` | `hardness unit` |
| `repeatability_standard_deviation` | `hardness unit` |
| `calibration_certified_hardness_range` | `hardness unit` |
| `calibration_temperature_range_K` | `K` |
| `outside_support_holdout_ids` | `1` |
| `holdout_rows` | `mixed` |
| `holdout_weighted_bias_corrected_error` | `hardness unit` |
| `holdout_weighted_bias_corrected_rmse` | `hardness unit` |
| `holdout_weighted_mean_negative_log_likelihood` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One exact method, scale, indenter, load, dwell and instrument configuration is calibrated.
- Reference certificate standard uncertainty and caller weight enter the likelihood explicitly.
- Calibration and holdout block, source and independence groups are disjoint.

## 구현 근거·독립 설명

- `authored_hardness_reference_block_bias_repeatability_calibration`: Estimate observed-minus-certified bias and instrument repeatability for one exact hardness method, scale, indenter, load, dwell and configuration using certified reference blocks and their stated uncertainty. Preserve disjoint physical-block/source/independence partitions and evaluate corrected holdout residuals only inside certified-value and temperature support without converting scales, inferring strength, deciding acceptance or creating probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.hardness_reference_block_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.hardness_reference_block_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "calibration-1",
  "asset_id": "asset-1",
  "location_id": "lab-1",
  "physical_scope_id": "instrument-scope-1",
  "reference_block_condition_id": "block-material-1",
  "method_id": "method-1",
  "scale_id": "scale-1",
  "indenter_id": "indenter-1",
  "applied_load_value": 10,
  "applied_load_unit_token": "kgf",
  "dwell_time_s": 10,
  "dwell_time_tolerance_s": 0.1,
  "instrument_id": "instrument-1",
  "instrument_configuration_id": "configuration-1",
  "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "hardness_unit_token": "scale-1-unit",
  "temperature_support_tolerance_K": 0.5,
  "observations": [
    {
      "observation_id": "cal-1",
      "physical_reference_block_id": "block-cal-1",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-block-cal-1",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 293,
      "certified_hardness_value": 100,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 101,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-2",
      "physical_reference_block_id": "block-cal-1",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-block-cal-1",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 293,
      "certified_hardness_value": 100,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 102.5,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-3",
      "physical_reference_block_id": "block-cal-2",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-block-cal-2",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 295,
      "certified_hardness_value": 180,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 181.6,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-4",
      "physical_reference_block_id": "block-cal-2",
      "source_group_id": "cal-source-a",
      "independence_group_id": "independence-block-cal-2",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 295,
      "certified_hardness_value": 180,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 182.8,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-5",
      "physical_reference_block_id": "block-cal-3",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-block-cal-3",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 297,
      "certified_hardness_value": 240,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 241.3,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-6",
      "physical_reference_block_id": "block-cal-3",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-block-cal-3",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 297,
      "certified_hardness_value": 240,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 242.3,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-7",
      "physical_reference_block_id": "block-cal-4",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-block-cal-4",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 298,
      "certified_hardness_value": 300,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 301.8,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "cal-8",
      "physical_reference_block_id": "block-cal-4",
      "source_group_id": "cal-source-b",
      "independence_group_id": "independence-block-cal-4",
      "partition": "calibration",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 298,
      "certified_hardness_value": 300,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 302.7,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "hold-1",
      "physical_reference_block_id": "block-hold-1",
      "source_group_id": "hold-source",
      "independence_group_id": "independence-block-hold-1",
      "partition": "holdout",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 294,
      "certified_hardness_value": 150,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 152.2,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
    },
    {
      "observation_id": "hold-2",
      "physical_reference_block_id": "block-hold-2",
      "source_group_id": "hold-source",
      "independence_group_id": "independence-block-hold-2",
      "partition": "holdout",
      "reference_block_condition_id": "block-material-1",
      "method_id": "method-1",
      "scale_id": "scale-1",
      "indenter_id": "indenter-1",
      "applied_load_value": 10,
      "applied_load_unit_token": "kgf",
      "dwell_time_s": 10,
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "instrument_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "specimen_temperature_K": 297,
      "certified_hardness_value": 260,
      "certified_standard_uncertainty": 0.5,
      "certificate_weight": 1,
      "observed_hardness_value": 261.7,
      "hardness_unit_token": "scale-1-unit",
      "certificate_provider_id": "certificate-provider",
      "certificate_revision": "1",
      "certificate_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
  "minimum_calibration_record_count": 8,
  "minimum_calibration_physical_block_count": 4,
  "minimum_holdout_record_count": 2,
  "method_scale_indenter_load_and_dwell_reviewed": true,
  "instrument_identity_configuration_and_digest_reviewed": true,
  "reference_block_condition_and_temperature_reviewed": true,
  "certificate_values_uncertainties_and_weights_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "certificate_and_result_digests_reviewed": true,
  "calibration_holdout_support_reviewed": true,
  "bias_and_repeatability_model_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/hardness_reference_calibration.py#L115)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
