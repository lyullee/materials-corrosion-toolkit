# `structural.external_pressure_provider_evidence`

**목적:** Shell, material condition, boundary, load case and pressure basis match exactly.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `shell_type_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `geometry_metrics` | 예 | `{"items": {"$ref": "#/$defs/ExternalPressureGeometryMetric"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `boundary_support_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `imperfection` | 예 | `{"$ref": "#/$defs/ExternalPressureImperfectionRecord"}` | 계약·필드 설명 참조 |
| `provider_result` | 예 | `{"$ref": "#/$defs/ExternalPressureProviderResult"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/ExternalPressureQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `component_material_geometry_and_thickness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `boundary_support_load_case_and_pressure_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `imperfection_field_metric_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mesh_and_model_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `solver_provider_revision_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_kind_units_and_solution_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalPressureProviderEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `component_id` | `1` |
| `qualification_envelope_id` | `1` |
| `provider_result_record_id` | `1` |
| `result_kind` | `1` |
| `provider_reported_result_value` | `provider unit` |
| `provider_reported_result_unit_token` | `1` |
| `pressure_basis` | `1` |
| `mesh_id` | `1` |
| `outside_support_reasons` | `1` |
| `geometry_comparisons` | `mixed` |
| `calibration_source_group_ids` | `1` |
| `holdout_source_group_ids` | `1` |
| `holdout_independence_group_ids` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Shell, material condition, boundary, load case and pressure basis match exactly.
- Geometry and imperfection metrics use exact caller definitions and units.
- Provider results remain evidence, not allowable pressure, acceptance or collapse probability.

## 구현 근거·독립 설명

- `reviewed_external_pressure_provider_qualification_envelope`: Preserve shell, material, geometry, boundary, load, pressure-basis and measured-imperfection identities and bind eigen or nonlinear external-pressure results to exact solver, mesh, model and provider digests with calibration and holdout evidence. Do not bundle code charts or infer allowable pressure, safety factor, collapse probability, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.external_pressure_provider_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.external_pressure_provider_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-external-pressure",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "component_id": "component-1",
  "shell_type_id": "cylindrical-shell",
  "material_id": "material-1",
  "material_condition_id": "condition-1",
  "thickness_m": 0.02,
  "geometry_metrics": [
    {
      "metric_id": "outside-diameter",
      "value": 1.0,
      "unit_token": "m",
      "measurement_basis": "authored measurement",
      "expanded_uncertainty": 0.001,
      "uncertainty_coverage_factor": 2.0,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored geometry"
        }
      ]
    },
    {
      "metric_id": "shell-length",
      "value": 5.0,
      "unit_token": "m",
      "measurement_basis": "authored measurement",
      "expanded_uncertainty": 0.002,
      "uncertainty_coverage_factor": 2.0,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored geometry"
        }
      ]
    }
  ],
  "boundary_support_id": "support-1",
  "load_case_id": "load-1",
  "pressure_basis": "external_minus_internal_pressure",
  "imperfection": {
    "imperfection_field_id": "field-1",
    "physical_surface_id": "surface-1",
    "coordinate_frame_id": "shell-frame",
    "field_definition": "authored radial deviation",
    "field_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "metric_definition_id": "caller-peak-radial-deviation",
    "metric_value": 0.002,
    "metric_unit_token": "m",
    "expanded_uncertainty": 0.0002,
    "uncertainty_coverage_factor": 2.0,
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored imperfection"
      }
    ]
  },
  "provider_result": {
    "result_record_id": "result-1",
    "analysis_id": "analysis-1",
    "result_kind": "nonlinear_limit_pressure",
    "pressure_basis": "external_minus_internal_pressure",
    "result_value": 1.1,
    "result_unit_token": "custom-pressure-unit",
    "mesh_id": "mesh-1",
    "mesh_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "geometry_model_id": "geometry-model-1",
    "material_model_id": "material-model-1",
    "imperfection_model_id": "imperfection-model-1",
    "boundary_model_id": "boundary-model-1",
    "load_model_id": "load-model-1",
    "solver_id": "solver-1",
    "solver_revision": "solver-revision-1",
    "provider_id": "solver-provider",
    "provider_revision": "revision-1",
    "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "convergence_or_solution_state": "authored converged state",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored provider result"
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
      "pressure_basis": "external_minus_internal_pressure",
      "minimum_thickness_m": 0.005,
      "maximum_thickness_m": 0.05,
      "geometry_support": [
        {
          "metric_id": "outside-diameter",
          "unit_token": "m",
          "minimum_value": 0.5,
          "maximum_value": 2.0
        },
        {
          "metric_id": "shell-length",
          "unit_token": "m",
          "minimum_value": 1.0,
          "maximum_value": 10.0
        }
      ],
      "imperfection_metric_definition_id": "caller-peak-radial-deviation",
      "imperfection_metric_unit_token": "m",
      "minimum_imperfection_metric_value": 0.0,
      "maximum_imperfection_metric_value": 0.005,
      "supported_result_kinds": [
        "eigen_buckling_pressure",
        "nonlinear_limit_pressure"
      ],
      "result_unit_token": "custom-pressure-unit",
      "solver_id": "solver-1",
      "solver_revision": "solver-revision-1",
      "provider_id": "solver-provider",
      "provider_revision": "revision-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "qualification_evidence": [
        {
          "evidence_record_id": "calibration-1",
          "partition": "calibration",
          "physical_benchmark_id": "benchmark-cal",
          "source_group_id": "source-cal",
          "independence_group_id": "ind-cal",
          "result_kind": "nonlinear_limit_pressure",
          "pressure_basis": "external_minus_internal_pressure",
          "observed_value": 1.0,
          "predicted_value": 1.05,
          "unit_token": "custom-pressure-unit",
          "expanded_observation_uncertainty": 0.05,
          "uncertainty_coverage_factor": 2.0,
          "provider_id": "solver-provider",
          "provider_revision": "revision-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored calibration"
            }
          ]
        },
        {
          "evidence_record_id": "holdout-1",
          "partition": "holdout",
          "physical_benchmark_id": "benchmark-hold",
          "source_group_id": "source-hold",
          "independence_group_id": "ind-hold",
          "result_kind": "nonlinear_limit_pressure",
          "pressure_basis": "external_minus_internal_pressure",
          "observed_value": 1.0,
          "predicted_value": 1.05,
          "unit_token": "custom-pressure-unit",
          "expanded_observation_uncertainty": 0.05,
          "uncertainty_coverage_factor": 2.0,
          "provider_id": "solver-provider",
          "provider_revision": "revision-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored holdout"
            }
          ]
        }
      ],
      "minimum_calibration_source_group_count": 1,
      "minimum_holdout_source_group_count": 1,
      "minimum_holdout_independence_group_count": 1,
      "qualification_basis": "authored validation plan",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored external pressure envelope"
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
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/external_pressure_provider.py#L217)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
