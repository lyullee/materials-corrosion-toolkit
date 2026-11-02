# `materials.allowable_property_provider`

**목적:** Property identity, edition, applicability and provider lineage are exact caller declarations.

**모델 버전:** `1.0.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `audit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_set_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_set_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tables` | 예 | `{"items": {"$ref": "#/$defs/AllowablePropertyTableRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `queries` | 예 | `{"items": {"$ref": "#/$defs/AllowablePropertyQueryRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_product_condition_orientation_and_edition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_revision_rights_and_provenance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applicability_units_and_temperature_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `query_identity_units_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AllowablePropertyProviderAudit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `audit_id` | `1` |
| `provider_set_id` | `1` |
| `provider_set_revision` | `1` |
| `table_audit_rows` | `mixed` |
| `query_result_rows` | `mixed` |
| `query_status_counts` | `count` |
| `audit_outcome` | `1` |
| `missing_reviews` | `1` |
| `extrapolation_performed` | `1` |
| `embedded_standard_table_used` | `1` |
| `allowable_stress_generated` | `1` |
| `automatic_acceptance_performed` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Property identity, edition, applicability and provider lineage are exact caller declarations.
- The supplied table is licensed or caller-owned and its declared temperature support has been reviewed.
- Results are property lookups only and establish no design acceptance or material qualification.

## 구현 근거·독립 설명

- `authored_allowable_property_provider_profile_audit`: Audit caller-owned or licensed material-property tables and exact material, product, condition, orientation, property, basis and edition identities, provider revision, applicability, units, temperature support, query and result digests. Reuse only reviewed in-support interpolation; do not extrapolate, embed proprietary tables, generate allowable stress or make acceptance decisions.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.allowable_property_provider"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.allowable_property_provider"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "audit_id": "audit-1",
  "provider_set_id": "provider-set-1",
  "provider_set_revision": "1",
  "tables": [
    {
      "table_id": "table-1",
      "provider_id": "caller-provider",
      "provider_revision": "rev-1",
      "provider_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "rights_basis": "caller_licensed",
      "entitlement_id": "caller-entitlement-1",
      "applicability_id": "scope-1",
      "applicability_statement": "Caller-reviewed plate property scope.",
      "table": {
        "identity": {
          "material_id": "material-A",
          "product_form": "plate",
          "material_condition": "normalized",
          "orientation": "longitudinal",
          "property_id": "caller_property",
          "basis_id": "caller-basis",
          "basis_edition": "2026-A"
        },
        "temperature_table": {
          "property_id": "caller_property",
          "x": [
            100.0,
            300.0
          ],
          "y": [
            200.0,
            100.0
          ],
          "x_unit": "K",
          "y_unit": "MPa",
          "source_id": "caller-table-source",
          "interpolation": "linear"
        },
        "evidence": {
          "source_id": "caller-table-source",
          "origin": "user_declared",
          "citation": "Caller-controlled property table record",
          "license_id": "caller-entitlement-1",
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        "permitted_use_note": "Use under the caller-controlled entitlement only."
      }
    }
  ],
  "queries": [
    {
      "query_id": "query-1",
      "applicability_id": "scope-1",
      "query": {
        "identity": {
          "material_id": "material-A",
          "product_form": "plate",
          "material_condition": "normalized",
          "orientation": "longitudinal",
          "property_id": "caller_property",
          "basis_id": "caller-basis",
          "basis_edition": "2026-A"
        },
        "temperature_K": 200.0,
        "requested_unit": "Pa"
      },
      "query_source_id": "caller-query-source",
      "query_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "caller-table-source",
          "origin": "user_declared",
          "citation": "Caller-controlled property table record",
          "license_id": "caller-entitlement-1",
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "material_product_condition_orientation_and_edition_reviewed": true,
  "provider_revision_rights_and_provenance_reviewed": true,
  "applicability_units_and_temperature_support_reviewed": true,
  "query_identity_units_and_digests_reviewed": true,
  "evidence": [
    {
      "source_id": "caller-table-source",
      "origin": "user_declared",
      "citation": "Caller-controlled property table record",
      "license_id": "caller-entitlement-1",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/allowable_property_provider.py#L67)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
