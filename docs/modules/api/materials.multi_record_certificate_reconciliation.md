# `materials.multi_record_certificate_reconciliation`

**목적:** One exact heat, lot and reviewed material-condition identity applies to every record.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `reconciliation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `heat_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `requirement_set_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `requirement_authority_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `requirements` | 예 | `{"items": {"$ref": "#/$defs/CertificateRequirementRow"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `records` | 예 | `{"items": {"$ref": "#/$defs/MaterialCertificateRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `heat_lot_and_material_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `alias_resolution_status_and_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_authority_and_bounds_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `chemistry_mass_fraction_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `property_si_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_samples_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `methods_uncertainties_and_coverage_factors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `duplicate_contradiction_and_missingness_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MaterialCertificateReconciliation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `reconciliation_id` | `1` |
| `physical_scope_id` | `1` |
| `heat_id` | `1` |
| `lot_id` | `1` |
| `material_condition_id` | `1` |
| `requirement_set_id` | `1` |
| `requirement_results` | `mixed` |
| `duplicate_measurement_rows` | `mixed` |
| `missing_requirement_ids` | `1` |
| `contradictory_requirement_ids` | `1` |
| `outside_requirement_ids` | `1` |
| `uncertainty_overlap_requirement_ids` | `1` |
| `declared_requirement_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One exact heat, lot and reviewed material-condition identity applies to every record.
- Chemistry mass fractions and property SI quantities remain separate exact unit domains.
- Reported expanded-uncertainty intervals are compared only with caller-supplied requirement bounds.

## 구현 근거·독립 설명

- `authored_multi_record_certificate_requirement_reconciliation`: Compare caller-supplied chemistry mass-fraction and SI property requirements with multiple provenance-bound material certificate or independent test records for one heat, lot and condition. Preserve aliases, duplicates, missing rows, uncertainty overlap and pairwise contradictions without averaging, embedding specification tables, choosing a material name, deciding code acceptance or creating failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.multi_record_certificate_reconciliation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.multi_record_certificate_reconciliation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "reconciliation_id": "reconciliation-1",
  "asset_id": "asset-1",
  "location_id": "material-location-1",
  "physical_scope_id": "heat-lot-scope-1",
  "heat_id": "heat-1",
  "lot_id": "lot-1",
  "material_condition_id": "material-1",
  "requirement_set_id": "caller-requirements-1",
  "requirement_authority_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "requirements": [
    {
      "requirement_id": "req-C",
      "quantity_kind": "chemistry_mass_fraction",
      "quantity_id": "C",
      "unit_basis": "mass_fraction",
      "unit_token": "mass_fraction",
      "minimum_allowed_value": 0.001,
      "maximum_allowed_value": 0.003,
      "comparison_policy": "reported_uncertainty_interval_against_requirement",
      "requirement_basis": "authored caller requirement",
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
      "requirement_id": "req-yield",
      "quantity_kind": "property_si",
      "quantity_id": "yield_strength",
      "unit_basis": "SI",
      "unit_token": "Pa",
      "minimum_allowed_value": 200000000,
      "maximum_allowed_value": 300000000,
      "comparison_policy": "reported_uncertainty_interval_against_requirement",
      "requirement_basis": "authored caller requirement",
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
      "requirement_id": "req-elongation",
      "quantity_kind": "property_si",
      "quantity_id": "elongation_fraction",
      "unit_basis": "SI",
      "unit_token": "1",
      "minimum_allowed_value": 0.2,
      "maximum_allowed_value": null,
      "comparison_policy": "reported_uncertainty_interval_against_requirement",
      "requirement_basis": "authored caller requirement",
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
  "records": [
    {
      "record_id": "certificate-1",
      "record_role": "certificate",
      "heat_id": "heat-1",
      "lot_id": "lot-1",
      "reported_material_identity_id": "reported-grade-1",
      "alias_resolution_status": "exact",
      "resolved_material_condition_id": "material-1",
      "alias_mapping_digest": null,
      "alias_resolution_basis": "authored exact identity",
      "physical_sample_id": "sample-certificate",
      "source_group_id": "source-certificate",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "measurements": [
        {
          "measurement_id": "cert-C-1",
          "quantity_kind": "chemistry_mass_fraction",
          "quantity_id": "C",
          "unit_basis": "mass_fraction",
          "unit_token": "mass_fraction",
          "reported_value": 0.002,
          "expanded_uncertainty": 0.0001,
          "uncertainty_coverage_factor": 2,
          "method_id": "method-1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
          "measurement_id": "cert-C-2",
          "quantity_kind": "chemistry_mass_fraction",
          "quantity_id": "C",
          "unit_basis": "mass_fraction",
          "unit_token": "mass_fraction",
          "reported_value": 0.0021,
          "expanded_uncertainty": 0.0001,
          "uncertainty_coverage_factor": 2,
          "method_id": "method-1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
          "measurement_id": "cert-yield",
          "quantity_kind": "property_si",
          "quantity_id": "yield_strength",
          "unit_basis": "SI",
          "unit_token": "Pa",
          "reported_value": 250000000,
          "expanded_uncertainty": 5000000,
          "uncertainty_coverage_factor": 2,
          "method_id": "method-1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
      "record_id": "test-1",
      "record_role": "independent_test",
      "heat_id": "heat-1",
      "lot_id": "lot-1",
      "reported_material_identity_id": "reported-grade-1",
      "alias_resolution_status": "exact",
      "resolved_material_condition_id": "material-1",
      "alias_mapping_digest": null,
      "alias_resolution_basis": "authored exact identity",
      "physical_sample_id": "sample-test",
      "source_group_id": "source-test",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "measurements": [
        {
          "measurement_id": "test-C",
          "quantity_kind": "chemistry_mass_fraction",
          "quantity_id": "C",
          "unit_basis": "mass_fraction",
          "unit_token": "mass_fraction",
          "reported_value": 0.00205,
          "expanded_uncertainty": 0.00015,
          "uncertainty_coverage_factor": 2,
          "method_id": "method-1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
          "measurement_id": "test-yield",
          "quantity_kind": "property_si",
          "quantity_id": "yield_strength",
          "unit_basis": "SI",
          "unit_token": "Pa",
          "reported_value": 252000000,
          "expanded_uncertainty": 5000000,
          "uncertainty_coverage_factor": 2,
          "method_id": "method-1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
  "heat_lot_and_material_condition_reviewed": true,
  "alias_resolution_status_and_mapping_reviewed": true,
  "requirement_authority_and_bounds_reviewed": true,
  "chemistry_mass_fraction_basis_reviewed": true,
  "property_si_units_reviewed": true,
  "physical_samples_and_source_groups_reviewed": true,
  "methods_uncertainties_and_coverage_factors_reviewed": true,
  "provider_lineage_and_result_digests_reviewed": true,
  "duplicate_contradiction_and_missingness_policy_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/certificate_reconciliation.py#L160)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
