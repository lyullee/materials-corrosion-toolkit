# `welding.repair_welding`

**목적:** Caller criteria only; no WPS qualification or life inference.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"type": "string"}` | 계약·필드 설명 참조 |
| `identity` | 예 | `{"$ref": "#/$defs/RepairIdentity"}` | 계약·필드 설명 참조 |
| `excavations` | 예 | `{"items": {"$ref": "#/$defs/ExcavationEvidence"}, "type": "array"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/RepairEvent"}, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/RepairObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `profile` | 예 | `{"$ref": "#/$defs/Profile"}` | 계약·필드 설명 참조 |
| `identity_and_repair_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `defect_removal_excavation_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thermal_deposition_interpass_and_pwht_sequence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_units_uncertainty_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/RepairWeldingCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `disposition` | `1` |
| `findings` | `mixed` |
| `result_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller criteria only; no WPS qualification or life inference.

## 구현 근거·독립 설명

- `authored_repair_welding_production_campaign_profile`: Preserve caller-supplied component, repair, weld, WPS, welder, base heat, consumable, prior repair count, defect-removal and excavation geometry, ordered removal-preheat-deposition-interpass-PWHT-cooling events, and NDE, hardness, dimensional, chemistry, mechanical or leak evidence. Apply only caller-authored criteria. Do not embed code acceptance, qualify a WPS, predict crack growth or infer remaining life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.repair_welding"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.repair_welding"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "a",
  "asset_id": "asset",
  "location_id": "l",
  "identity": {
    "component_id": "comp",
    "repair_id": "r",
    "weld_id": "w",
    "wps_id": "wps",
    "wps_revision": "1",
    "welder_ids": [
      "welder"
    ],
    "base_heat_ids": [
      "h"
    ],
    "consumable_lot_ids": [
      "f"
    ],
    "repair_sequence_number": 1,
    "previous_repair_ids": [],
    "reviewed": true,
    "evidence": [
      {
        "source_id": "id",
        "origin": "user_declared",
        "citation": "id",
        "license_id": null,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  },
  "excavations": [
    {
      "defect_id": "d",
      "removal_method_id": "grind",
      "excavation_geometry_id": "g",
      "length_m": 0.1,
      "depth_m": 0.005,
      "width_m": 0.02,
      "standard_uncertainty_m": 0.0001,
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "d",
          "origin": "user_declared",
          "citation": "d",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "events": [
    {
      "event_id": "ev",
      "sequence_position": 1,
      "event_kind": "deposition",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "minimum_temperature_k": 300.0,
      "maximum_temperature_k": 500.0,
      "pass_id": null,
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "ev",
          "origin": "user_declared",
          "citation": "ev",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "nde",
      "metric_kind": "nde",
      "metric_id": "indications",
      "unit_token": "count",
      "status": "available",
      "value": 0.0,
      "standard_uncertainty": 0.0,
      "provider_id": "p",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_basis": null,
      "evidence": [
        {
          "source_id": "nde",
          "origin": "user_declared",
          "citation": "nde",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "profile": {
    "profile_id": "pr",
    "profile_revision": "1",
    "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "permitted_wps_ids": [
      "wps"
    ],
    "permitted_base_heat_ids": [
      "h"
    ],
    "permitted_consumable_lots": [
      "f"
    ],
    "maximum_repair_count": 2,
    "maximum_excavation_depth_m": 0.01,
    "maximum_event_temperature_k": 600.0,
    "criteria": [
      {
        "criterion_id": "nde-rule",
        "metric_kind": "nde",
        "metric_id": "indications",
        "unit_token": "count",
        "minimum_inclusive": 0.0,
        "maximum_inclusive": 0.0,
        "uncertainty_policy": "interval_must_fit",
        "missing_disposition": "insufficient_evidence"
      }
    ],
    "profile_reviewed": true,
    "evidence": [
      {
        "source_id": "pr",
        "origin": "user_declared",
        "citation": "pr",
        "license_id": null,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  },
  "identity_and_repair_history_reviewed": true,
  "defect_removal_excavation_geometry_reviewed": true,
  "thermal_deposition_interpass_and_pwht_sequence_reviewed": true,
  "observation_units_uncertainty_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "evidence": [
    {
      "source_id": "a",
      "origin": "user_declared",
      "citation": "a",
      "license_id": null,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/repair_welding_campaign.py#L266)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
