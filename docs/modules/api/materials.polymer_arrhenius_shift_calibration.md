# `materials.polymer_arrhenius_shift_calibration`

**목적:** Weighted calibration is restricted to one polymer formulation, physical state and endpoint definition.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `polymer_formulation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `endpoint_definition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/PolymerShiftObservation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_specimen_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_specimen_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `formulation_physical_state_and_endpoint_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_temperature_reference_and_log_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_independence_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `weights_missingness_and_validity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_support_and_no_extrapolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PolymerArrheniusShiftCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `reference_temperature_K` | `K` |
| `log_shift_at_reference_temperature` | `1` |
| `reciprocal_temperature_slope_K` | `K` |
| `calibration_temperature_support_K` | `K` |
| `outside_support_holdout_observation_ids` | `1` |
| `excluded_missing_or_invalid_observation_ids` | `1` |
| `calibration_observation_ids` | `1` |
| `holdout_observation_ids` | `1` |
| `holdout_log_shift_bias` | `1` |
| `holdout_log_shift_rmse` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weighted calibration is restricted to one polymer formulation, physical state and endpoint definition.
- Natural-log shift factor is linear in reciprocal absolute temperature relative to a declared reference.
- Calibration and holdout specimens, source groups and independence groups are disjoint.

## 구현 근거·독립 설명

- `weighted_polymer_arrhenius_time_shift_calibration`: Fit valid calibration natural-log time-shift factors against reciprocal absolute temperature relative to a caller reference using declared weights. Preserve exact polymer formulation, physical state, endpoint, provider digests and disjoint specimen/source/independence partitions; evaluate holdout only inside temperature support without inferring chemical compatibility, long-term life, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.polymer_arrhenius_shift_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.polymer_arrhenius_shift_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "fit-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "polymer_formulation_id": "formulation-1",
  "physical_state_id": "state-1",
  "endpoint_definition_id": "endpoint-1",
  "reference_temperature_K": 300,
  "observations": [
    {
      "observation_id": "c1",
      "physical_specimen_id": "s1",
      "source_group_id": "g1",
      "independence_group_id": "g1",
      "partition": "calibration",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 280,
      "log_time_shift_factor": 0.47619047619047555,
      "log_basis": "natural",
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "c2",
      "physical_specimen_id": "s2",
      "source_group_id": "g2",
      "independence_group_id": "g2",
      "partition": "calibration",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 300,
      "log_time_shift_factor": 0,
      "log_basis": "natural",
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "c3",
      "physical_specimen_id": "s3",
      "source_group_id": "g3",
      "independence_group_id": "g3",
      "partition": "calibration",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 320,
      "log_time_shift_factor": -0.41666666666666674,
      "log_basis": "natural",
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "h1",
      "physical_specimen_id": "s4",
      "source_group_id": "g4",
      "independence_group_id": "g4",
      "partition": "holdout",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 290,
      "log_time_shift_factor": 0.22988505747126384,
      "log_basis": "natural",
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "h2",
      "physical_specimen_id": "s5",
      "source_group_id": "g5",
      "independence_group_id": "g5",
      "partition": "holdout",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 310,
      "log_time_shift_factor": -0.21505376344086063,
      "log_basis": "natural",
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "m1",
      "physical_specimen_id": "s6",
      "source_group_id": "g6",
      "independence_group_id": "g6",
      "partition": "holdout",
      "polymer_formulation_id": "formulation-1",
      "physical_state_id": "state-1",
      "endpoint_definition_id": "endpoint-1",
      "temperature_K": 300,
      "log_time_shift_factor": null,
      "log_basis": "natural",
      "weight": null,
      "record_status": "missing",
      "missing_or_invalid_basis": "result unavailable",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": null,
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
  "minimum_calibration_specimen_count": 3,
  "minimum_calibration_source_group_count": 3,
  "minimum_holdout_specimen_count": 2,
  "minimum_holdout_source_group_count": 2,
  "formulation_physical_state_and_endpoint_reviewed": true,
  "absolute_temperature_reference_and_log_basis_reviewed": true,
  "specimen_source_independence_and_partitions_reviewed": true,
  "weights_missingness_and_validity_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "calibration_support_and_no_extrapolation_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/polymer_arrhenius_shift.py#L102)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
