# `fabrication.tube_bundle_integrity_evidence`

**목적:** Exchanger, bundle, tube, row and physical location are exact caller-reviewed identities.

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
| `bundle_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `row_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_location_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tube_outer_diameter_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `tube_wall_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `support_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `baffle_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `vibration_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `operating_intervals` | 예 | `{"items": {"$ref": "#/$defs/TubeBundleOperatingInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/TubeBundleObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `disposition_records` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/TubeBundleDispositionRecord"}, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/TubeBundleIntegrityEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exchanger_bundle_tube_row_and_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `tube_material_condition_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_baffle_and_vibration_descriptors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `operating_clock_and_states_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_metrics_units_uncertainty_and_detection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `disposition_records_reviewed_as_caller_decisions` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_specimens_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TubeBundleIntegrityEvidence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `exchanger_id` | `1` |
| `bundle_id` | `1` |
| `tube_id` | `1` |
| `row_id` | `1` |
| `clock_id` | `1` |
| `envelope_id` | `1` |
| `observation_comparisons` | `mixed` |
| `outside_observation_ids` | `1` |
| `qualification_source_group_count` | `1` |
| `uncovered_metric_ids` | `1` |
| `caller_disposition_summary` | `mixed` |
| `outside_support_reasons` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Exchanger, bundle, tube, row and physical location are exact caller-reviewed identities.
- Inspection and vibration values retain metric definitions, units, uncertainty and detection status.
- Repair, plug and retube records are caller decisions and are never inferred by the model.

## 구현 근거·독립 설명

- `reviewed_tube_bundle_integrity_evidence_envelope`: Preserve exchanger, bundle, tube, row and mapped location, material and geometry, support, baffle and vibration descriptors, operating clock, inspection or vibration observations and explicit caller disposition records, then compare only with caller-owned provider support and partitioned qualification evidence. Do not infer defect size, vibration response, repair or retubing decisions, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.tube_bundle_integrity_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.tube_bundle_integrity_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-tube-bundle",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "exchanger_id": "exchanger-1",
  "bundle_id": "bundle-1",
  "tube_id": "tube-1",
  "row_id": "row-1",
  "tube_location_definition": "authored mapped tube location",
  "tube_material_condition_id": "material-1",
  "tube_outer_diameter_m": 0.02,
  "tube_wall_thickness_m": 0.002,
  "support_descriptor": "support-1",
  "baffle_descriptor": "baffle-1",
  "vibration_descriptor": "vibration-state-1",
  "clock_id": "clock-1",
  "operating_intervals": [
    {
      "interval_id": "interval-1",
      "start_time_s": 0.0,
      "end_time_s": 3600.0,
      "operating_state_id": "state-1",
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored tube operating interval"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "obs-1",
      "observation_kind": "defect_or_condition_inspection",
      "physical_source_group_id": "inspection-run-1",
      "method_id": "inspection-1",
      "metric_id": "condition-metric",
      "metric_definition": "authored condition metric",
      "reported_value": 0.2,
      "unit_token": "custom-condition-unit",
      "expanded_uncertainty": 0.02,
      "detection_status": "detected",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored tube observation"
        }
      ]
    }
  ],
  "disposition_records": [
    {
      "disposition_id": "disposition-1",
      "disposition_kind": "monitor",
      "disposition_time_s": 3600.0,
      "caller_decision_record_id": "decision-1",
      "affected_tube_id": "tube-1",
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored caller disposition"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "tube_material_condition_id": "material-1",
      "minimum_outer_diameter_m": 0.01,
      "maximum_outer_diameter_m": 0.04,
      "minimum_wall_thickness_m": 0.0005,
      "maximum_wall_thickness_m": 0.005,
      "supported_support_descriptors": [
        "support-1"
      ],
      "supported_baffle_descriptors": [
        "baffle-1"
      ],
      "supported_vibration_descriptors": [
        "vibration-state-1"
      ],
      "supported_operating_state_ids": [
        "state-1"
      ],
      "metric_support": [
        {
          "observation_kind": "defect_or_condition_inspection",
          "metric_id": "condition-metric",
          "unit_token": "custom-condition-unit",
          "supported_method_ids": [
            "inspection-1"
          ],
          "minimum_supported_value": 0.0,
          "maximum_supported_value": 1.0,
          "maximum_supported_expanded_uncertainty": 0.1,
          "support_basis": "authored support"
        }
      ],
      "qualification_evidence": [
        {
          "evidence_record_id": "evidence-1",
          "physical_specimen_id": "specimen-1",
          "source_group_id": "source-1",
          "partition": "qualification",
          "supported_metric_ids": [
            "condition-metric"
          ],
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored tube qualification"
            }
          ]
        }
      ],
      "minimum_qualification_source_group_count": 1,
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored tube envelope"
        }
      ]
    }
  ],
  "exchanger_bundle_tube_row_and_location_reviewed": true,
  "tube_material_condition_and_geometry_reviewed": true,
  "support_baffle_and_vibration_descriptors_reviewed": true,
  "operating_clock_and_states_reviewed": true,
  "observation_metrics_units_uncertainty_and_detection_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "disposition_records_reviewed_as_caller_decisions": true,
  "qualification_specimens_and_source_groups_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored tube assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/tube_bundle_integrity.py#L213)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
