# `welding.local_heat_treatment`

**목적:** Sensor positions and synchronized histories are reviewed caller records.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `weld_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `treatment_procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sensor_histories` | 예 | `{"items": {"$ref": "#/$defs/LocalHeatTreatmentSensorHistory"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/LocalHeatTreatmentProcedureEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `sensor_layout_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `time_and_temperature_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_joint_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `procedure_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_state_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `procedure_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LocalHeatTreatmentAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `selected_envelope_id` | `1` |
| `maximum_heating_rate_K_s` | `K/s` |
| `maximum_cooling_rate_K_s` | `K/s` |
| `minimum_sensor_hold_band_duration_s` | `s` |
| `maximum_spatial_gradient_K_m` | `K/m` |
| `record_within_declared_procedure_envelope` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Sensor positions and synchronized histories are reviewed caller records.
- Treatment bounds and heat-zone applicability are supplied by a reviewed caller-owned procedure envelope.

## 구현 근거·독립 설명

- `reviewed_local_heat_treatment_record_comparison`: Compare synchronized spatial temperature records with a caller-owned local heat-treatment envelope. Preserve sensor, heat-zone, provider and state identity; do not embed welding-code limits, metallurgical response or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.local_heat_treatment"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.local_heat_treatment"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-local-treatment",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "weld_id": "weld-1",
  "material_condition_id": "condition-1",
  "joint_configuration_id": "joint-1",
  "treatment_procedure_id": "procedure-1",
  "sensor_histories": [
    {
      "sensor_id": "sensor-a",
      "heat_zone_id": "zone-1",
      "sensor_position_m": 0.0,
      "time_s": [
        0.0,
        20.0,
        40.0,
        60.0
      ],
      "temperature_K": [
        300.0,
        610.0,
        620.0,
        400.0
      ],
      "acquisition_provider_id": "logger",
      "acquisition_provider_version": "1",
      "acquisition_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored temperature history"
        }
      ]
    },
    {
      "sensor_id": "sensor-b",
      "heat_zone_id": "zone-1",
      "sensor_position_m": 0.1,
      "time_s": [
        0.0,
        20.0,
        40.0,
        60.0
      ],
      "temperature_K": [
        300.0,
        605.0,
        615.0,
        405.0
      ],
      "acquisition_provider_id": "logger",
      "acquisition_provider_version": "1",
      "acquisition_state_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored temperature history"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "condition-1",
      "joint_configuration_id": "joint-1",
      "treatment_procedure_id": "procedure-1",
      "qualified_heat_zone_ids": [
        "zone-1"
      ],
      "minimum_hold_temperature_K": 600.0,
      "maximum_hold_temperature_K": 650.0,
      "minimum_hold_duration_s": 20.0,
      "maximum_heating_rate_K_s": 20.0,
      "maximum_cooling_rate_K_s": 20.0,
      "maximum_spatial_gradient_K_m": 500.0,
      "procedure_provider_id": "caller-procedure-provider",
      "procedure_provider_version": "1",
      "procedure_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "applicability_basis": "authored caller-owned envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored local-treatment envelope"
        }
      ]
    }
  ],
  "sensor_layout_reviewed": true,
  "time_and_temperature_records_reviewed": true,
  "material_and_joint_identity_reviewed": true,
  "procedure_identity_reviewed": true,
  "provider_state_digests_reviewed": true,
  "procedure_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored local-treatment assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding_local_heat_treatment.py#L167)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
