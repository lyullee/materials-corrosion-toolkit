# `fabrication.heat_exchanger_geometry_evidence`

**목적:** Exchanger, shell, bundle, coordinate frame, units, ordering and payload digests are caller reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exchanger_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `shell_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `shell_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `shell_inside_diameter_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `shell_length_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `tube_layout` | 예 | `{"$ref": "#/$defs/TubeLayoutManifest"}` | 계약·필드 설명 참조 |
| `tubesheets` | 예 | `{"items": {"$ref": "#/$defs/TubesheetGeometryRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `baffles` | 예 | `{"items": {"$ref": "#/$defs/BaffleGeometryRecord"}, "type": "array"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_version` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_input_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `qualification_evidence` | 예 | `{"items": {"$ref": "#/$defs/GeometryProviderEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredHeatExchangerGeometryEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exchanger_shell_bundle_and_coordinate_frame_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `tube_layout_shape_order_units_and_digest_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `tubesheet_and_baffle_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_condition_and_geometry_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_revision_configuration_input_and_result_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_specimens_partitions_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HeatExchangerGeometryAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `exchanger_id` | `1` |
| `bundle_id` | `1` |
| `selected_envelope_id` | `1` |
| `declared_geometry_outcome` | `1` |
| `tube_count` | `count` |
| `tubesheet_count` | `count` |
| `baffle_count` | `count` |
| `outside_geometry_support_reasons` | `1` |
| `metric_comparisons` | `mixed` |
| `unsupported_qualification_evidence_ids` | `1` |
| `missing_metric_ids` | `1` |
| `outside_support_evidence_ids` | `1` |
| `qualification_source_group_count` | `count` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Exchanger, shell, bundle, coordinate frame, units, ordering and payload digests are caller reviewed.
- Tubesheet, baffle and tube geometry plus provider revision and support are caller-owned.
- Qualification evidence preserves physical specimens, source groups, partitions, methods and uncertainty.

## 구현 근거·독립 설명

- `reviewed_heat_exchanger_geometry_provider_envelope`: Preserve shell, bundle, tube-layout, tubesheet and baffle geometry with coordinate frame, component order, array shape, payload and provider digests, then compare provider values with partitioned metrology evidence inside caller support. Do not infer coordinates from counts or patterns or calculate flow, vibration, heat transfer, stress, capacity, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.heat_exchanger_geometry_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.heat_exchanger_geometry_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-geometry",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "exchanger_id": "exchanger-1",
  "shell_geometry_id": "shell-geometry-1",
  "shell_material_condition_id": "shell-condition-1",
  "shell_inside_diameter_m": 1.0,
  "shell_length_m": 5.0,
  "tube_layout": {
    "bundle_id": "bundle-1",
    "coordinate_frame_id": "bundle-frame",
    "coordinate_unit_token": "m",
    "coordinate_component_order": [
      "x",
      "y"
    ],
    "tube_ordering_definition": "authored row-major tube IDs",
    "tube_count": 100,
    "layout_pattern_descriptor": "triangular-pattern",
    "pitch_m": 0.03,
    "tube_outer_diameter_m": 0.02,
    "tube_wall_thickness_m": 0.001,
    "tube_length_m": 5.0,
    "coordinate_array_shape": [
      100,
      2
    ],
    "coordinate_payload_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored layout"
      }
    ]
  },
  "tubesheets": [
    {
      "tubesheet_id": "tubesheet-1",
      "axial_coordinate_m": 0.0,
      "outer_diameter_m": 1.1,
      "thickness_m": 0.1,
      "tube_hole_count": 100,
      "material_condition_id": "tubesheet-condition-1",
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored tubesheet"
        }
      ]
    }
  ],
  "baffles": [
    {
      "baffle_id": "baffle-1",
      "axial_coordinate_m": 1.0,
      "baffle_type_descriptor": "segmental",
      "outer_diameter_m": 0.98,
      "thickness_m": 0.01,
      "cut_or_open_fraction": 0.25,
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored baffle"
        }
      ]
    }
  ],
  "provider_id": "geometry-provider",
  "provider_version": "1",
  "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "provider_input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "provider_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "qualification_evidence": [
    {
      "evidence_record_id": "evidence-1",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "partition": "qualification",
      "metric_id": "tube-coordinate",
      "unit_token": "m",
      "observed_value": 0.1,
      "provider_value": 0.101,
      "expanded_uncertainty": 0.002,
      "method_id": "metrology-1",
      "provider_id": "geometry-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored geometry evidence"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "shell_geometry_id": "shell-geometry-1",
      "shell_material_condition_id": "shell-condition-1",
      "supported_layout_pattern_descriptors": [
        "triangular-pattern"
      ],
      "supported_baffle_type_descriptors": [
        "segmental"
      ],
      "minimum_shell_inside_diameter_m": 0.5,
      "maximum_shell_inside_diameter_m": 2.0,
      "minimum_shell_length_m": 1.0,
      "maximum_shell_length_m": 10.0,
      "minimum_tube_count": 10,
      "maximum_tube_count": 500,
      "minimum_baffle_count": 1,
      "maximum_baffle_count": 20,
      "metric_support": [
        {
          "metric_id": "tube-coordinate",
          "unit_token": "m",
          "maximum_absolute_difference": 0.005,
          "minimum_record_count": 1,
          "support_basis": "authored metrology support"
        }
      ],
      "minimum_source_group_count": 1,
      "provider_id": "geometry-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored geometry envelope"
        }
      ]
    }
  ],
  "exchanger_shell_bundle_and_coordinate_frame_reviewed": true,
  "tube_layout_shape_order_units_and_digest_reviewed": true,
  "tubesheet_and_baffle_geometry_reviewed": true,
  "material_condition_and_geometry_units_reviewed": true,
  "provider_revision_configuration_input_and_result_reviewed": true,
  "qualification_specimens_partitions_and_uncertainty_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored geometry assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/heat_exchanger_geometry.py#L198)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
