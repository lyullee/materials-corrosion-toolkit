# `welding.production_weld_test_campaign_evidence`

**목적:** Caller criteria only; no WPS or code qualification claim.

**모델 버전:** `1.0.2` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welds` | 예 | `{"items": {"$ref": "#/$defs/ProductionWeldIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `specimens` | 예 | `{"items": {"$ref": "#/$defs/WeldCouponSpecimen"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measurements` | 예 | `{"items": {"$ref": "#/$defs/WeldTestMeasurement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `profile` | 예 | `{"$ref": "#/$defs/CallerProductionWeldTestProfile"}` | 계약·필드 설명 참조 |
| `weld_joint_wps_welder_consumable_and_heat_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coupon_specimen_extraction_location_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_metric_units_uncertainty_status_and_provenance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_authority_and_criteria_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ProductionWeldTestCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `disposition` | `1` |
| `findings` | `mixed` |
| `result_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller criteria only; no WPS or code qualification claim.

## 구현 근거·독립 설명

- `authored_production_weld_test_campaign_profile`: Preserve caller-supplied weld, joint, WPS revision, welder, consumable lot, base heat, coupon extraction and bend, tensile, impact, hardness, macro, NDE, chemistry or user measurement evidence with uncertainty and independence lineage. Apply only caller-authored criteria. Do not embed code acceptance, qualify a WPS, convert strength or automatically accept production welds.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.production_weld_test_campaign_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.production_weld_test_campaign_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "a",
  "asset_id": "asset",
  "location_id": "loc",
  "campaign_id": "c",
  "welds": [
    {
      "weld_id": "w",
      "joint_id": "j",
      "wps_id": "wps",
      "wps_revision": "1",
      "welder_ids": [
        "welder"
      ],
      "consumable_lot_ids": [
        "filler"
      ],
      "base_material_heat_ids": [
        "h1",
        "h2"
      ],
      "identity_reviewed": true,
      "evidence": [
        {
          "source_id": "w",
          "origin": "user_declared",
          "citation": "w",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "specimens": [
    {
      "specimen_id": "s1",
      "coupon_id": "coupon1",
      "weld_id": "w",
      "extraction_location_id": "x1",
      "extraction_orientation": "transverse",
      "source_group_id": "source1",
      "independence_group_id": "ind1",
      "extraction_reviewed": true,
      "evidence": [
        {
          "source_id": "s1",
          "origin": "user_declared",
          "citation": "s1",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "specimen_id": "s2",
      "coupon_id": "coupon2",
      "weld_id": "w",
      "extraction_location_id": "x2",
      "extraction_orientation": "transverse",
      "source_group_id": "source2",
      "independence_group_id": "ind2",
      "extraction_reviewed": true,
      "evidence": [
        {
          "source_id": "s2",
          "origin": "user_declared",
          "citation": "s2",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "measurements": [
    {
      "measurement_id": "m1",
      "specimen_id": "s1",
      "replicate_group_id": "g",
      "test_kind": "tensile",
      "metric_id": "strength",
      "metric_definition": "caller strength",
      "unit_token": "Pa",
      "status": "available",
      "value": 5000000.0,
      "standard_uncertainty": 100000.0,
      "method_id": "method",
      "provider_id": "lab",
      "provider_revision": "1",
      "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "m1",
          "origin": "user_declared",
          "citation": "m1",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "measurement_id": "m2",
      "specimen_id": "s2",
      "replicate_group_id": "g",
      "test_kind": "tensile",
      "metric_id": "strength",
      "metric_definition": "caller strength",
      "unit_token": "Pa",
      "status": "available",
      "value": 5200000.0,
      "standard_uncertainty": 100000.0,
      "method_id": "method",
      "provider_id": "lab",
      "provider_revision": "1",
      "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "missing_or_invalid_basis": null,
      "evidence": [
        {
          "source_id": "m2",
          "origin": "user_declared",
          "citation": "m2",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "profile": {
    "profile_id": "p",
    "profile_revision": "1",
    "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "permitted_wps_ids": [
      "wps"
    ],
    "permitted_consumable_lot_ids": [
      "filler"
    ],
    "permitted_base_material_heat_ids": [
      "h1",
      "h2"
    ],
    "criteria": [
      {
        "criterion_id": "strength-rule",
        "test_kind": "tensile",
        "metric_id": "strength",
        "unit_token": "Pa",
        "aggregation": "replicate_mean",
        "minimum_inclusive": 4000000.0,
        "maximum_inclusive": null,
        "uncertainty_policy": "interval_must_fit",
        "uncertainty_coverage_factor": 1.0,
        "minimum_replicates": 2,
        "minimum_independent_source_groups": 2,
        "missing_disposition": "insufficient_evidence",
        "description": "caller"
      }
    ],
    "profile_reviewed": true,
    "evidence": [
      {
        "source_id": "p",
        "origin": "user_declared",
        "citation": "p",
        "license_id": null,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    ]
  },
  "weld_joint_wps_welder_consumable_and_heat_identity_reviewed": true,
  "coupon_specimen_extraction_location_and_orientation_reviewed": true,
  "test_metric_units_uncertainty_status_and_provenance_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "caller_profile_authority_and_criteria_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/production_weld_test_campaign.py#L347)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
