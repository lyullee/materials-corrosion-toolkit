# `structural.nozzle_local_stress_provider_evidence`

**목적:** Geometry, load component and stress metric units are exact caller/provider tokens.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `vessel_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `nozzle_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `opening_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_quantities` | 예 | `{"items": {"$ref": "#/$defs/NozzleGeometryQuantity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `load_components` | 예 | `{"items": {"$ref": "#/$defs/NozzleLoadComponent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `provider_results` | 예 | `{"items": {"$ref": "#/$defs/NozzleProviderStressResult"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/NozzleLocalStressEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `vessel_nozzle_opening_geometry_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coordinate_frame_and_load_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mesh_location_and_averaging_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_representation_metrics_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_revision_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/NozzleLocalStressProviderEvidence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `load_case_id` | `1` |
| `envelope_id` | `1` |
| `geometry_outside_support_ids` | `1` |
| `load_outside_support_ids` | `1` |
| `result_comparisons` | `mixed` |
| `outside_result_ids` | `1` |
| `uncovered_metric_ids` | `1` |
| `outside_support_reasons` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Geometry, load component and stress metric units are exact caller/provider tokens.
- Coordinate frame, mesh, result location and spatial averaging basis are not inferred.
- Calibration and holdout evidence retain disjoint physical source groups.

## 구현 근거·독립 설명

- `reviewed_nozzle_local_stress_provider_qualification_envelope`: Preserve vessel, nozzle and opening geometry, material, coordinate frame, load components, mesh, result location, averaging and stress representation, then bind external provider results to exact revision and digests with disjoint calibration and holdout evidence. Do not bundle proprietary stress indices or infer acceptance, fatigue, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.nozzle_local_stress_provider_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.nozzle_local_stress_provider_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-nozzle-stress",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "vessel_geometry_id": "vessel-geometry-1",
  "nozzle_geometry_id": "nozzle-geometry-1",
  "opening_geometry_id": "opening-geometry-1",
  "material_condition_id": "material-1",
  "coordinate_frame_id": "frame-1",
  "load_case_id": "load-case-1",
  "geometry_quantities": [
    {
      "quantity_id": "shell-thickness",
      "value": 0.02,
      "unit_token": "m",
      "basis": "authored geometry",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored geometry"
        }
      ]
    }
  ],
  "load_components": [
    {
      "component_id": "radial-force",
      "component_kind": "force",
      "value": 1000.0,
      "unit_token": "N",
      "sign_and_basis": "positive along authored radial axis",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored load"
        }
      ]
    }
  ],
  "provider_results": [
    {
      "result_id": "result-1",
      "load_case_id": "load-case-1",
      "mesh_id": "mesh-1",
      "result_location_id": "path-1",
      "spatial_averaging_basis": "through-thickness-linearization",
      "coordinate_frame_id": "frame-1",
      "representation_kind": "linearized_membrane",
      "metric_id": "membrane-hoop",
      "metric_definition": "authored hoop membrane stress",
      "reported_value": 100000000.0,
      "unit_token": "Pa",
      "expanded_uncertainty": 10000000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored nozzle result"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "vessel_geometry_id": "vessel-geometry-1",
      "nozzle_geometry_id": "nozzle-geometry-1",
      "opening_geometry_id": "opening-geometry-1",
      "material_condition_id": "material-1",
      "coordinate_frame_id": "frame-1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "supported_mesh_ids": [
        "mesh-1"
      ],
      "geometry_support": [
        {
          "quantity_id": "shell-thickness",
          "unit_token": "m",
          "minimum_supported_value": 0.005,
          "maximum_supported_value": 0.05
        }
      ],
      "load_support": [
        {
          "quantity_id": "radial-force",
          "unit_token": "N",
          "minimum_supported_value": -10000.0,
          "maximum_supported_value": 10000.0
        }
      ],
      "result_support": [
        {
          "representation_kind": "linearized_membrane",
          "metric_id": "membrane-hoop",
          "unit_token": "Pa",
          "minimum_supported_value": -300000000.0,
          "maximum_supported_value": 300000000.0,
          "maximum_supported_expanded_uncertainty": 20000000.0,
          "supported_result_location_ids": [
            "path-1"
          ],
          "supported_spatial_averaging_bases": [
            "through-thickness-linearization"
          ]
        }
      ],
      "qualification_evidence": [
        {
          "evidence_record_id": "evidence-cal",
          "physical_specimen_id": "specimen-cal",
          "source_group_id": "source-cal",
          "partition": "calibration",
          "supported_metric_ids": [
            "membrane-hoop"
          ],
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
          "evidence_record_id": "evidence-hold",
          "physical_specimen_id": "specimen-hold",
          "source_group_id": "source-hold",
          "partition": "holdout",
          "supported_metric_ids": [
            "membrane-hoop"
          ],
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored nozzle envelope"
        }
      ]
    }
  ],
  "vessel_nozzle_opening_geometry_and_units_reviewed": true,
  "material_condition_reviewed": true,
  "coordinate_frame_and_load_basis_reviewed": true,
  "mesh_location_and_averaging_reviewed": true,
  "stress_representation_metrics_units_and_uncertainty_reviewed": true,
  "provider_revision_configuration_and_digests_reviewed": true,
  "calibration_holdout_and_source_groups_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored nozzle assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/nozzle_local_stress.py#L232)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
