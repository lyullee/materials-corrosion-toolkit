# `fabrication.cryogenic_valve_evidence`

**목적:** Valve, body, seat, stem, seal, medium and pressure-basis identities match caller qualification evidence exactly.

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
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `valve_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `valve_type_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `body_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `seat_component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `seat_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stem_component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stem_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `seal_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_medium_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"enum": ["absolute", "gauge", "differential"], "type": "string"}` | 계약·필드 설명 참조 |
| `cycles` | 예 | `{"items": {"$ref": "#/$defs/CryogenicValveCycle"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/CryogenicValveObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/CryogenicValveQualificationEnvelope"}` | 계약·필드 설명 참조 |
| `valve_component_material_and_seal_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `medium_and_pressure_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_cycle_and_actuation_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thermal_stabilization_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_roles_metrics_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_detection_limits_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_specimen_and_source_group_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CryogenicValveEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `valve_id` | `1` |
| `qualification_envelope_id` | `1` |
| `cycle_comparisons` | `mixed` |
| `outside_support_cycle_ids` | `1` |
| `cumulative_actuation_count` | `count` |
| `cumulative_actuation_within_support` | `1` |
| `observation_summaries` | `mixed` |
| `observation_requirement_counts` | `1` |
| `qualification_evidence_summary` | `1` |
| `declared_evidence_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Valve, body, seat, stem, seal, medium and pressure-basis identities match caller qualification evidence exactly.
- Cycle pressure is compared only under an exact caller-declared unit token; no conversion or code threshold is inferred.
- Leakage, torque and function observations retain their role, censoring status, uncertainty and provider lineage.

## 구현 근거·독립 설명

- `reviewed_cryogenic_valve_qualification_envelope`: Compare exact valve, body, seat, stem, seal, medium and pressure-basis identities, ordered thermal-pressure-actuation cycles and leakage, torque or function observations with caller qualification evidence. Preserve below-detection and missing records; do not infer service performance, thermal stress, reliability, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.cryogenic_valve_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.cryogenic_valve_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-cryo-valve",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "clock_id": "clock-1",
  "valve_id": "valve-1",
  "valve_type_id": "valve-type-1",
  "body_material_id": "body-material-1",
  "seat_component_id": "seat-1",
  "seat_material_id": "seat-material-1",
  "stem_component_id": "stem-1",
  "stem_material_id": "stem-material-1",
  "seal_system_id": "seal-1",
  "test_medium_id": "medium-1",
  "pressure_basis": "absolute",
  "cycles": [
    {
      "cycle_id": "cycle-1",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "minimum_temperature_K": 80.0,
      "maximum_temperature_K": 300.0,
      "minimum_pressure_value": 1.0,
      "maximum_pressure_value": 2.0,
      "pressure_unit_token": "custom-pressure",
      "actuation_count": 5,
      "actuation_mode_descriptor": "full-open-close",
      "thermal_stabilization_basis": "authored plateau",
      "acquisition_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored valve cycle"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "leak-1",
      "cycle_id": "cycle-1",
      "physical_component_id": "seat-1",
      "source_group_id": "run-1",
      "observation_role": "test",
      "observation_kind": "leakage",
      "method_id": "method-1",
      "metric_id": "leak-rate",
      "metric_definition": "authored leak signal",
      "unit_token": "custom-leak-unit",
      "reporting_status": "below_detection",
      "detection_limit": 0.01,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored valve observation"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "envelope-1",
    "valve_type_id": "valve-type-1",
    "body_material_id": "body-material-1",
    "seat_component_id": "seat-1",
    "seat_material_id": "seat-material-1",
    "stem_component_id": "stem-1",
    "stem_material_id": "stem-material-1",
    "seal_system_id": "seal-1",
    "test_medium_id": "medium-1",
    "pressure_basis": "absolute",
    "minimum_temperature_K": 70.0,
    "maximum_temperature_K": 310.0,
    "minimum_pressure_value": 0.5,
    "maximum_pressure_value": 2.5,
    "pressure_unit_token": "custom-pressure",
    "supported_actuation_mode_descriptors": [
      "full-open-close"
    ],
    "maximum_single_cycle_duration_s": 200.0,
    "maximum_cumulative_actuation_count": 10,
    "observation_requirements": [
      {
        "requirement_id": "leak-test",
        "observation_kind": "leakage",
        "observation_role": "test",
        "method_id": "method-1",
        "metric_id": "leak-rate",
        "metric_definition": "authored leak signal",
        "unit_token": "custom-leak-unit",
        "minimum_record_count": 1,
        "requirement_basis": "authored evidence plan"
      }
    ],
    "physical_specimen_ids": [
      "specimen-1"
    ],
    "source_group_ids": [
      "source-1"
    ],
    "provider_id": "qualification-provider",
    "provider_revision": "1",
    "provider_state_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "qualification_result_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "qualification_basis": "authored qualification programme",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored valve envelope"
      }
    ]
  },
  "valve_component_material_and_seal_identity_reviewed": true,
  "medium_and_pressure_basis_reviewed": true,
  "clock_cycle_and_actuation_alignment_reviewed": true,
  "thermal_stabilization_reviewed": true,
  "observation_roles_metrics_and_units_reviewed": true,
  "uncertainty_detection_limits_and_missingness_reviewed": true,
  "physical_specimen_and_source_group_partitions_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored valve assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/cryogenic_valve.py#L202)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
