# `degradation.atmospheric_multi_year_loss_history`

**목적:** First-year loss and time exponent are externally supplied, reviewed quantities in exact caller units.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_zone_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `climate_pollutant_descriptor_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `first_year_loss` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `loss_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `first_year_loss_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `first_year_loss_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `time_exponent` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `elapsed_time_years` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `transfer_envelope` | 예 | `{"$ref": "#/$defs/AtmosphericTimeTransferEnvelope"}` | 계약·필드 설명 참조 |
| `exposure_material_surface_and_environment_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `first_year_endpoint_value_and_unit_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `time_exponent_definition_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_ordered_time_knots_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_partitions_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `transfer_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AtmosphericMultiYearLossHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `transfer_envelope_id` | `1` |
| `outside_support_reasons` | `1` |
| `elapsed_time_years` | `year` |
| `cumulative_loss` | `caller_unit` |
| `loss_increment` | `caller_unit` |
| `time_exponent` | `1` |
| `qualification_partition_counts` | `count` |
| `declared_transfer_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- First-year loss and time exponent are externally supplied, reviewed quantities in exact caller units.
- Exposure zone, material, surface and climate/pollutant descriptor identities are constant over the history.
- The power transfer is evaluated only inside a caller-qualified envelope and is not a general atmospheric corrosion law.

## 구현 근거·독립 설명

- `reviewed_atmospheric_first_year_time_transfer_envelope`: Apply the caller-qualified transfer identity loss(t)=loss at one year times t raised to a caller-supplied exponent only at ordered supported exposure times. Preserve material, surface, exposure-zone, climate/pollutant descriptors, provider digests and independent calibration/holdout evidence; do not infer climate effects, extrapolate, or create localized penetration, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.atmospheric_multi_year_loss_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.atmospheric_multi_year_loss_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "h-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "exposure_zone_id": "zone-1",
  "material_condition_id": "condition-1",
  "surface_condition_id": "surface-1",
  "climate_pollutant_descriptor_id": "climate-1",
  "first_year_loss": 0.0001,
  "loss_unit_token": "m",
  "first_year_loss_provider_id": "provider-first",
  "first_year_loss_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "time_exponent": 0.6,
  "elapsed_time_years": [
    0.0,
    1.0,
    2.0,
    5.0
  ],
  "transfer_envelope": {
    "envelope_id": "e-1",
    "exposure_zone_id": "zone-1",
    "material_condition_id": "condition-1",
    "surface_condition_id": "surface-1",
    "climate_pollutant_descriptor_id": "climate-1",
    "loss_unit_token": "m",
    "time_unit_token": "year",
    "minimum_first_year_loss": 1e-05,
    "maximum_first_year_loss": 0.001,
    "minimum_time_exponent": 0.2,
    "maximum_time_exponent": 1.0,
    "maximum_supported_elapsed_years": 10.0,
    "provider_id": "provider-transfer",
    "provider_revision": "1",
    "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "qualification_records": [
      {
        "record_id": "1",
        "partition": "calibration",
        "physical_specimen_id": "s-1",
        "source_group_id": "g1",
        "exposure_zone_id": "zone-1",
        "material_condition_id": "condition-1",
        "surface_condition_id": "surface-1",
        "climate_pollutant_descriptor_id": "climate-1",
        "provider_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "invalid_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored calibration"
          }
        ]
      },
      {
        "record_id": "2",
        "partition": "holdout",
        "physical_specimen_id": "s-2",
        "source_group_id": "g2",
        "exposure_zone_id": "zone-1",
        "material_condition_id": "condition-1",
        "surface_condition_id": "surface-1",
        "climate_pollutant_descriptor_id": "climate-1",
        "provider_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "invalid_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored holdout"
          }
        ]
      }
    ],
    "qualification_basis": "authored",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored transfer envelope"
      }
    ]
  },
  "exposure_material_surface_and_environment_identity_reviewed": true,
  "first_year_endpoint_value_and_unit_reviewed": true,
  "time_exponent_definition_and_support_reviewed": true,
  "clock_and_ordered_time_knots_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_partitions_and_source_groups_reviewed": true,
  "transfer_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/atmospheric_multiyear.py#L109)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
