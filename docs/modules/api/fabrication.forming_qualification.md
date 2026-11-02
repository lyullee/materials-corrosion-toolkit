# `fabrication.forming_qualification`

**목적:** Material, condition, product form, forming mode and method match the envelope exactly.

**모델 버전:** `1.0.2` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `product_form_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `governing_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `governing_direction_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `forming_mode` | 예 | `{"enum": ["cold", "hot"], "type": "string"}` | 계약·필드 설명 참조 |
| `forming_method_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `forming_metrics` | 예 | `{"items": {"$ref": "#/$defs/FormingMetricRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `thermal_history` | 예 | `{"items": {"$ref": "#/$defs/FormingThermalInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `inspection_and_property_evidence` | 예 | `{"items": {"$ref": "#/$defs/FormingEvidenceRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/FormingQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `component_material_product_and_thickness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `forming_mode_method_and_direction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deformation_metric_definitions_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_time_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `post_forming_heat_treatment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspection_property_and_partition_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FormingQualificationAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `component_id` | `1` |
| `qualification_envelope_id` | `1` |
| `outside_identity_reasons` | `1` |
| `outside_metric_record_ids` | `1` |
| `outside_thermal_interval_ids` | `1` |
| `cumulative_thermal_duration_outside_support_keys` | `1` |
| `outside_evidence_record_ids` | `1` |
| `metric_comparisons` | `mixed` |
| `physical_specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `independence_group_ids` | `1` |
| `declared_qualification_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, condition, product form, forming mode and method match the envelope exactly.
- Metric definitions and units are caller-defined and no strain reconstruction is inferred.
- Qualification evidence does not establish code acceptance or long-term property retention.

## 구현 근거·독립 설명

- `reviewed_forming_qualification_envelope`: Compare component, material condition, product form, thickness, direction, cold or hot forming method, exact deformation metrics and ordered forming or post-forming thermal history with partitioned inspection and property evidence. Do not bundle forming-code limits or infer unreported strain, property degradation, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.forming_qualification"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.forming_qualification"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-forming",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "component_id": "component-1",
  "material_id": "material-1",
  "material_condition_id": "condition-1",
  "product_form_id": "plate",
  "governing_thickness_m": 0.02,
  "governing_direction_id": "transverse",
  "forming_mode": "hot",
  "forming_method_id": "method-hot-1",
  "clock_id": "clock-1",
  "forming_metrics": [
    {
      "metric_record_id": "metric-1",
      "metric_definition_id": "caller-thickness-reduction",
      "direction_id": "transverse",
      "value": 0.1,
      "unit_token": "fraction",
      "expanded_uncertainty": 0.01,
      "uncertainty_coverage_factor": 2.0,
      "measurement_or_derivation_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored forming metric"
        }
      ]
    }
  ],
  "thermal_history": [
    {
      "interval_id": "forming-1",
      "stage": "forming",
      "procedure_id": "forming-procedure",
      "start_time_s": 0.0,
      "end_time_s": 50.0,
      "minimum_temperature_K": 750.0,
      "maximum_temperature_K": 850.0,
      "provider_id": "logger-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored forming interval"
        }
      ]
    },
    {
      "interval_id": "pht-1",
      "stage": "post_forming_heat_treatment",
      "procedure_id": "heat-treatment-1",
      "start_time_s": 60.0,
      "end_time_s": 160.0,
      "minimum_temperature_K": 650.0,
      "maximum_temperature_K": 750.0,
      "provider_id": "logger-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored post-forming interval"
        }
      ]
    }
  ],
  "inspection_and_property_evidence": [
    {
      "evidence_record_id": "evidence-1",
      "evidence_kind": "property_test",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "independence_group_id": "independent-1",
      "physical_region_id": "region-1",
      "method_id": "property-method",
      "result_definition": "caller retained-property metric",
      "reported_value": 95.0,
      "unit_token": "custom-property-unit",
      "expanded_uncertainty": 2.0,
      "uncertainty_coverage_factor": 2.0,
      "provider_id": "laboratory-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored forming evidence"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "product_form_id": "plate",
      "forming_mode": "hot",
      "forming_method_id": "method-hot-1",
      "minimum_thickness_m": 0.005,
      "maximum_thickness_m": 0.05,
      "supported_direction_ids": [
        "transverse"
      ],
      "metric_requirements": [
        {
          "metric_definition_id": "caller-thickness-reduction",
          "direction_id": "transverse",
          "unit_token": "fraction",
          "minimum_value": 0.0,
          "maximum_value": 0.2,
          "requirement_basis": "authored plan"
        }
      ],
      "thermal_supports": [
        {
          "stage": "forming",
          "procedure_id": "forming-procedure",
          "minimum_temperature_K": 700.0,
          "maximum_temperature_K": 900.0,
          "maximum_single_interval_s": 100.0,
          "maximum_cumulative_duration_s": 100.0
        },
        {
          "stage": "post_forming_heat_treatment",
          "procedure_id": "heat-treatment-1",
          "minimum_temperature_K": 600.0,
          "maximum_temperature_K": 800.0,
          "maximum_single_interval_s": 200.0,
          "maximum_cumulative_duration_s": 200.0
        }
      ],
      "evidence_requirements": [
        {
          "requirement_id": "property-1",
          "evidence_kind": "property_test",
          "method_id": "property-method",
          "result_definition": "caller retained-property metric",
          "unit_token": "custom-property-unit",
          "minimum_record_count": 1,
          "minimum_value": 90.0,
          "maximum_value": 110.0,
          "requirement_basis": "authored plan"
        }
      ],
      "minimum_physical_specimen_count": 1,
      "minimum_source_group_count": 1,
      "minimum_independence_group_count": 1,
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored forming envelope"
        }
      ]
    }
  ],
  "component_material_product_and_thickness_reviewed": true,
  "forming_mode_method_and_direction_reviewed": true,
  "deformation_metric_definitions_units_and_uncertainty_reviewed": true,
  "temperature_time_history_reviewed": true,
  "post_forming_heat_treatment_reviewed": true,
  "inspection_property_and_partition_evidence_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/forming_qualification.py#L451)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
