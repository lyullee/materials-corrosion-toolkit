# `inspection.phased_array_campaign_quality`

**목적:** Procedure, acquisition, reference standard, coverage and encoded-data identities are caller supplied.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `imaging_family` | 예 | `{"enum": ["radiography", "phased_array"], "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `extent_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_standard` | 예 | `{"$ref": "#/$defs/ImagingReferenceStandard"}` | 계약·필드 설명 참조 |
| `acquisitions` | 예 | `{"items": {"$ref": "#/$defs/ImagingAcquisitionEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `acceptance_profile` | 예 | `{"$ref": "#/$defs/ImagingCampaignAcceptanceProfile"}` | 계약·필드 설명 참조 |
| `procedure_and_acquisition_identities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_standard_features_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_verification_checks_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coverage_and_extent_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `encoded_data_identity_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sensitivity_resolution_metrics_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_acceptance_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_validity_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ImagingCampaignQualityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `imaging_family` | `1` |
| `quality_outcome` | `1` |
| `acceptance_profile_id` | `1` |
| `metric_values` | `mixed` |
| `criterion_findings` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_acceptance_profile_only` | `1` |
| `automatic_flaw_acceptance` | `1` |
| `pod_claimed` | `1` |
| `physical_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Procedure, acquisition, reference standard, coverage and encoded-data identities are caller supplied.
- Sensitivity, resolution and reference response are quality metrics under caller limits only.
- Campaign audit does not establish flaw acceptance, POD or physical qualification.

## 구현 근거·독립 설명

- `authored_imaging_reference_campaign_quality_audit`: Aggregate caller-supplied radiography or phased-array procedure identity, reference-standard features, encoded-acquisition digests, coverage and staged verification metrics. Compare sensitivity, resolution and coverage descriptors only with caller-authored criteria. Do not inspect image pixels, accept flaws, estimate POD, reproduce a published limit or claim physical qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.phased_array_campaign_quality"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.phased_array_campaign_quality"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "phased_array-campaign-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "imaging_family": "phased_array",
  "procedure_id": "procedure-1",
  "procedure_revision": "rev-1",
  "extent_unit_token": "mm",
  "reference_standard": {
    "reference_standard_id": "standard-1",
    "material_and_product_form_id": "standard-material-1",
    "standard_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "features": [
      {
        "feature_id": "feature-1",
        "feature_type_descriptor": "caller reference feature",
        "physical_location_definition": "reviewed standard coordinate",
        "nominal_dimension": 1.0,
        "dimension_unit_token": "mm",
        "expanded_dimension_uncertainty": 0.05,
        "physical_feature_identity_reviewed": true,
        "feature_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored imaging audit",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored imaging audit",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "acquisitions": [
    {
      "acquisition_id": "acquisition-1",
      "procedure_id": "procedure-1",
      "procedure_revision": "rev-1",
      "acquisition_configuration_id": "config-1",
      "acquisition_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "acquisition_device_id": "device-1",
      "reference_standard_id": "standard-1",
      "target_extent": 100.0,
      "examined_extent": 90.0,
      "extent_unit_token": "mm",
      "encoded_data_id": "encoded-1",
      "encoded_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "encoded_data_format": "caller encoded format",
      "verifications": [
        {
          "verification_id": "verification-pre",
          "reference_feature_id": "feature-1",
          "check_stage": "pre_acquisition",
          "reported_response_present": true,
          "sensitivity_metric": 10.0,
          "sensitivity_unit_token": "response-ratio",
          "expanded_sensitivity_uncertainty": 0.2,
          "resolution_metric": 0.5,
          "resolution_unit_token": "mm",
          "expanded_resolution_uncertainty": 0.05,
          "verification_method_definition": "caller reference response measurement",
          "verification_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored imaging audit",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "verification_id": "verification-post",
          "reference_feature_id": "feature-1",
          "check_stage": "post_acquisition",
          "reported_response_present": true,
          "sensitivity_metric": 10.0,
          "sensitivity_unit_token": "response-ratio",
          "expanded_sensitivity_uncertainty": 0.2,
          "resolution_metric": 0.5,
          "resolution_unit_token": "mm",
          "expanded_resolution_uncertainty": 0.05,
          "verification_method_definition": "caller reference response measurement",
          "verification_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored imaging audit",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "acquisition_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored imaging audit",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "acceptance_profile": {
    "profile_id": "phased_array-profile-1",
    "profile_version": "1.0.0",
    "imaging_family": "phased_array",
    "required_check_stages": [
      "pre_acquisition",
      "post_acquisition"
    ],
    "sensitivity_metric_definition": "caller response ratio",
    "sensitivity_unit_token": "response-ratio",
    "resolution_metric_definition": "caller spatial resolution metric",
    "resolution_unit_token": "mm",
    "criteria": [
      {
        "criterion_id": "criterion-acquisition_count",
        "metric_id": "acquisition_count",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-coverage_fraction",
        "metric_id": "coverage_fraction",
        "direction": "minimum",
        "pass_limit": 0.9,
        "fail_limit": 0.7,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-reference_feature_check_coverage_fraction",
        "metric_id": "reference_feature_check_coverage_fraction",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-required_stage_coverage_fraction",
        "metric_id": "required_stage_coverage_fraction",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-response_present_fraction",
        "metric_id": "response_present_fraction",
        "direction": "minimum",
        "pass_limit": 1.0,
        "fail_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-minimum_sensitivity_metric",
        "metric_id": "minimum_sensitivity_metric",
        "direction": "minimum",
        "pass_limit": 8.0,
        "fail_limit": 5.0,
        "unit_token": "response-ratio",
        "criterion_basis": "caller-authored campaign quality limit"
      },
      {
        "criterion_id": "criterion-maximum_resolution_metric",
        "metric_id": "maximum_resolution_metric",
        "direction": "maximum",
        "pass_limit": 0.6,
        "fail_limit": 1.0,
        "unit_token": "mm",
        "criterion_basis": "caller-authored campaign quality limit"
      }
    ],
    "profile_provider_id": "caller-profile-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_acceptance_authority": "caller NDE review group",
    "built_in_code_or_standard_limits_used": false,
    "flaw_acceptance_claimed": false,
    "pod_claimed": false,
    "physical_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored imaging audit",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "procedure_and_acquisition_identities_reviewed": true,
  "reference_standard_features_and_uncertainty_reviewed": true,
  "calibration_and_verification_checks_reviewed": true,
  "coverage_and_extent_units_reviewed": true,
  "encoded_data_identity_and_digests_reviewed": true,
  "sensitivity_resolution_metrics_units_and_uncertainty_reviewed": true,
  "caller_acceptance_profile_reviewed": true,
  "record_validity_and_missingness_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored imaging audit",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/imaging_campaign_quality.py#L281)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
