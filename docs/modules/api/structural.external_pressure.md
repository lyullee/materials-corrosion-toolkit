# `structural.external_pressure`

**목적:** Existing provider assessments retain exact geometry, material, imperfection, boundary, load, mesh, model, pressure and digest identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_assessments` | 예 | `{"items": {"$ref": "#/$defs/ExternalPressureProviderEvidenceAssessment"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `convergence_evidence` | 예 | `{"items": {"$ref": "#/$defs/ExternalPressureConvergenceEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/ExternalPressureCampaignCallerProfile"}` | 계약·필드 설명 참조 |
| `component_geometry_material_imperfection_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `boundary_load_pressure_basis_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_solver_revision_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mesh_and_model_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applicability_and_envelope_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `convergence_definition_units_and_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_validation_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalPressureCampaignAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `evidence_outcome` | `1` |
| `caller_profile_id` | `1` |
| `metric_values` | `mixed` |
| `criterion_findings` | `mixed` |
| `receipt_summaries` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_profile_only` | `1` |
| `buckling_analysis_executed` | `1` |
| `allowable_pressure_or_safety_factor_produced` | `1` |
| `automatic_acceptance_or_field_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Existing provider assessments retain exact geometry, material, imperfection, boundary, load, mesh, model, pressure and digest identities.
- Campaign metrics audit applicability, convergence and holdout evidence without executing buckling analysis or component acceptance.

## 구현 근거·독립 설명

- `authored_external_pressure_provider_receipt_campaign_audit`: Audit externally supplied external-pressure assessments, exact geometry, material, imperfection, boundary and load identities, pressure basis, solver and provider digests, applicability support, convergence and calibration or holdout evidence. Do not solve buckling, embed code curves or factors, accept a component or claim field qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.external_pressure"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.external_pressure"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "campaign-assessment-1",
  "asset_id": "asset-1",
  "location_id": "shell-1",
  "campaign_id": "campaign-1",
  "component_id": "component-1",
  "provider_assessments": [
    {
      "assessment_id": "provider-assessment-1",
      "asset_id": "asset-1",
      "location_id": "shell-1",
      "component_id": "component-1",
      "shell_type_id": "cylindrical-shell",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "thickness_m": 0.02,
      "geometry_metrics": [
        {
          "metric_id": "diameter",
          "value": 1.0,
          "unit_token": "m",
          "measurement_basis": "caller measurement",
          "expanded_uncertainty": 0.001,
          "uncertainty_coverage_factor": 2.0,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored receipt",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "boundary_support_id": "support-1",
      "load_case_id": "load-1",
      "pressure_basis": "external-minus-internal",
      "imperfection": {
        "imperfection_field_id": "field-1",
        "physical_surface_id": "surface-1",
        "coordinate_frame_id": "frame-1",
        "field_definition": "caller radial deviation field",
        "field_data_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "metric_definition_id": "peak-radial-deviation",
        "metric_value": 0.002,
        "metric_unit_token": "m",
        "expanded_uncertainty": 0.0002,
        "uncertainty_coverage_factor": 2.0,
        "record_valid": true,
        "invalid_or_missing_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored receipt",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "provider_result": {
        "result_record_id": "provider-result-1",
        "analysis_id": "analysis-1",
        "result_kind": "nonlinear_limit_pressure",
        "pressure_basis": "external-minus-internal",
        "result_value": 1.1,
        "result_unit_token": "MPa",
        "mesh_id": "mesh-1",
        "mesh_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "geometry_model_id": "geometry-model-1",
        "material_model_id": "material-model-1",
        "imperfection_model_id": "imperfection-model-1",
        "boundary_model_id": "boundary-model-1",
        "load_model_id": "load-model-1",
        "solver_id": "solver-1",
        "solver_revision": "solver-rev-1",
        "provider_id": "provider-1",
        "provider_revision": "rev-1",
        "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "result_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "convergence_or_solution_state": "caller-reviewed converged state",
        "record_valid": true,
        "invalid_or_missing_basis": null,
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored receipt",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "candidate_envelopes": [
        {
          "envelope_id": "envelope-1",
          "shell_type_id": "cylindrical-shell",
          "material_condition_id": "condition-1",
          "boundary_support_id": "support-1",
          "load_case_id": "load-1",
          "pressure_basis": "external-minus-internal",
          "minimum_thickness_m": 0.005,
          "maximum_thickness_m": 0.05,
          "geometry_support": [
            {
              "metric_id": "diameter",
              "unit_token": "m",
              "minimum_value": 0.5,
              "maximum_value": 2.0
            }
          ],
          "imperfection_metric_definition_id": "peak-radial-deviation",
          "imperfection_metric_unit_token": "m",
          "minimum_imperfection_metric_value": 0.0,
          "maximum_imperfection_metric_value": 0.005,
          "supported_result_kinds": [
            "nonlinear_limit_pressure"
          ],
          "result_unit_token": "MPa",
          "solver_id": "solver-1",
          "solver_revision": "solver-rev-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "qualification_evidence": [
            {
              "evidence_record_id": "calibration-1",
              "partition": "calibration",
              "physical_benchmark_id": "benchmark-calibration-1",
              "source_group_id": "source-cal",
              "independence_group_id": "ind-cal",
              "result_kind": "nonlinear_limit_pressure",
              "pressure_basis": "external-minus-internal",
              "observed_value": 1.0,
              "predicted_value": 1.05,
              "unit_token": "MPa",
              "expanded_observation_uncertainty": 0.05,
              "uncertainty_coverage_factor": 2.0,
              "provider_id": "provider-1",
              "provider_revision": "rev-1",
              "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
              "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
              "record_valid": true,
              "supports_declared_envelope": true,
              "invalid_or_limiting_basis": null,
              "evidence": [
                {
                  "source_id": "authored",
                  "origin": "synthetic",
                  "citation": "authored receipt",
                  "license_id": null,
                  "sha256": null
                }
              ]
            },
            {
              "evidence_record_id": "holdout-1",
              "partition": "holdout",
              "physical_benchmark_id": "benchmark-holdout-1",
              "source_group_id": "source-hold",
              "independence_group_id": "ind-hold",
              "result_kind": "nonlinear_limit_pressure",
              "pressure_basis": "external-minus-internal",
              "observed_value": 1.0,
              "predicted_value": 1.05,
              "unit_token": "MPa",
              "expanded_observation_uncertainty": 0.05,
              "uncertainty_coverage_factor": 2.0,
              "provider_id": "provider-1",
              "provider_revision": "rev-1",
              "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
              "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
              "record_valid": true,
              "supports_declared_envelope": true,
              "invalid_or_limiting_basis": null,
              "evidence": [
                {
                  "source_id": "authored",
                  "origin": "synthetic",
                  "citation": "authored receipt",
                  "license_id": null,
                  "sha256": null
                }
              ]
            }
          ],
          "minimum_calibration_source_group_count": 1,
          "minimum_holdout_source_group_count": 1,
          "minimum_holdout_independence_group_count": 1,
          "qualification_basis": "caller validation plan",
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored receipt",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "component_material_geometry_and_thickness_reviewed": true,
      "boundary_support_load_case_and_pressure_basis_reviewed": true,
      "imperfection_field_metric_and_units_reviewed": true,
      "mesh_and_model_identity_reviewed": true,
      "solver_provider_revision_and_digests_reviewed": true,
      "result_kind_units_and_solution_state_reviewed": true,
      "calibration_holdout_partitions_reviewed": true,
      "qualification_envelope_authority_reviewed": true
    }
  ],
  "convergence_evidence": [
    {
      "convergence_record_id": "convergence-1",
      "provider_assessment_id": "provider-assessment-1",
      "analysis_id": "analysis-1",
      "result_kind": "nonlinear_limit_pressure",
      "mesh_family_id": "mesh-family-1",
      "model_family_id": "model-family-1",
      "pressure_basis": "external-minus-internal",
      "convergence_metric_definition": "caller adjacent-refinement relative change",
      "convergence_metric_value": 0.03,
      "convergence_metric_unit_token": "1",
      "comparison_result_ids": [
        "coarse-result",
        "fine-result"
      ],
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "comparison_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "comparison_result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored receipt",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_result_kinds": [
      "nonlinear_limit_pressure"
    ],
    "convergence_metric_definition": "caller adjacent-refinement relative change",
    "convergence_metric_unit_token": "1",
    "criteria": [
      {
        "criterion_id": "criterion-supported_receipt_count",
        "metric_id": "supported_receipt_count",
        "direction": "minimum",
        "accept_limit": 1.0,
        "reject_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller provider-receipt quality criterion"
      },
      {
        "criterion_id": "criterion-out_of_support_receipt_count",
        "metric_id": "out_of_support_receipt_count",
        "direction": "maximum",
        "accept_limit": 0.0,
        "reject_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller provider-receipt quality criterion"
      },
      {
        "criterion_id": "criterion-maximum_convergence_metric",
        "metric_id": "maximum_convergence_metric",
        "direction": "maximum",
        "accept_limit": 0.05,
        "reject_limit": 0.1,
        "unit_token": "1",
        "criterion_basis": "caller provider-receipt quality criterion"
      },
      {
        "criterion_id": "criterion-maximum_holdout_absolute_relative_error",
        "metric_id": "maximum_holdout_absolute_relative_error",
        "direction": "maximum",
        "accept_limit": 0.1,
        "reject_limit": 0.2,
        "unit_token": "1",
        "criterion_basis": "caller provider-receipt quality criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_review_authority": "caller structural review group",
    "buckling_analysis_executed": false,
    "code_curve_or_safety_factor_used": false,
    "automatic_acceptance_claimed": false,
    "field_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored receipt",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "component_geometry_material_imperfection_identity_reviewed": true,
  "boundary_load_pressure_basis_and_support_reviewed": true,
  "provider_solver_revision_configuration_and_digests_reviewed": true,
  "mesh_and_model_identity_reviewed": true,
  "applicability_and_envelope_support_reviewed": true,
  "convergence_definition_units_and_records_reviewed": true,
  "calibration_holdout_validation_evidence_reviewed": true,
  "caller_profile_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored receipt",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/external_pressure_campaign.py#L224)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
