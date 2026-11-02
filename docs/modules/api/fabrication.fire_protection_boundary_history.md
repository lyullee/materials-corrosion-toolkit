# `fabrication.fire_protection_boundary_history`

**목적:** The caller supplies the incident flux, protection states, transfer fractions and their reviewed support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thermal_boundary_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `incident_heat_flux_W_m2` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | W/m² |
| `transmitted_flux_fraction` | 예 | `{"items": {"maximum": 1, "minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `protection_state_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `transfer_record_digests` | 예 | `{"items": {"type": "string"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `exposed_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `transfer_support` | 예 | `{"$ref": "#/$defs/FireProtectionTransferSupport"}` | 계약·필드 설명 참조 |
| `clock_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incident_flux_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `protection_state_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `transfer_provider_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thermal_boundary_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FireProtectionBoundaryHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `clock_id` | `1` |
| `elapsed_time_s` | `s` |
| `incident_heat_flux_W_m2` | `W/m^2` |
| `transmitted_heat_flux_into_solid_W_m2` | `W/m^2` |
| `interval_incident_energy_J_m2` | `J/m^2` |
| `interval_transmitted_energy_J_m2` | `J/m^2` |
| `total_incident_energy_J_m2` | `J/m^2` |
| `total_transmitted_energy_J_m2` | `J/m^2` |
| `total_incident_energy_J` | `J` |
| `total_transmitted_energy_J` | `J` |
| `thermal_boundary_contract` | `mixed` |
| `outside_incident_flux_support_indices` | `1` |
| `unsupported_protection_state_indices` | `1` |
| `missing_reviews` | `1` |
| `support_id` | `1` |
| `provider_id` | `1` |
| `provider_version` | `1` |
| `provider_digest` | `1` |
| `transfer_record_digests` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies the incident flux, protection states, transfer fractions and their reviewed support.
- Heat flux is positive into the solid and the caller reviews boundary orientation.
- The transfer history is not extrapolated beyond declared flux or state support.

## 구현 근거·독립 설명

- `reviewed_fire_protection_flux_coupling`: Combine caller-supplied incident heat-flux and reviewed protection transfer-fraction histories within exact provider flux and state support. Integrate their linearly interpolated product and emit a prescribed heat-flux boundary without supplying a fire curve, material properties, degradation, failure or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.fire_protection_boundary_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.fire_protection_boundary_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "authored-fire-protection",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-fire-clock",
  "thermal_boundary_id": "protected-surface",
  "elapsed_time_s": [
    0.0,
    60.0,
    180.0
  ],
  "incident_heat_flux_W_m2": [
    10000.0,
    30000.0,
    20000.0
  ],
  "transmitted_flux_fraction": [
    0.1,
    0.2,
    0.15
  ],
  "protection_state_ids": [
    "intact",
    "intact",
    "intact"
  ],
  "transfer_record_digests": [
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  ],
  "exposed_area_m2": 2.0,
  "transfer_support": {
    "support_id": "authored-transfer-support",
    "provider_id": "caller-fire-provider",
    "provider_version": "1",
    "provider_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "incident_flux_min_W_m2": 0.0,
    "incident_flux_max_W_m2": 50000.0,
    "supported_protection_state_ids": [
      "intact"
    ],
    "calibration_basis": "authored caller-owned transfer support",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored fire transfer support"
      }
    ]
  },
  "clock_alignment_reviewed": true,
  "incident_flux_basis_reviewed": true,
  "protection_state_history_reviewed": true,
  "transfer_provider_and_calibration_reviewed": true,
  "thermal_boundary_orientation_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored fire boundary example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fire_protection.py#L87)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
