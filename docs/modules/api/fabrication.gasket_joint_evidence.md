# `fabrication.gasket_joint_evidence`

**목적:** Flange, gasket, bolt lots, medium, pressure basis and operating state are caller reviewed.

**모델 버전:** `1.0.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `flange_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `flange_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `gasket_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `gasket_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bolt_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bolt_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `medium_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `operating_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `operating_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `bolt_preloads` | 예 | `{"items": {"$ref": "#/$defs/BoltPreloadRecord"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `seating_result` | 예 | `{"$ref": "#/$defs/GasketSeatingProviderResult"}` | 계약·필드 설명 참조 |
| `relaxation_observations` | 예 | `{"items": {"$ref": "#/$defs/JointRelaxationObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredGasketJointEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `flange_gasket_bolt_material_and_lot_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `medium_pressure_basis_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `preload_method_units_uncertainty_and_bolt_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `seating_provider_revision_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `relaxation_clock_metrics_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_specimens_partitions_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketJointAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `joint_id` | `1` |
| `selected_envelope_id` | `1` |
| `declared_evidence_outcome` | `1` |
| `bolt_count` | `count` |
| `preload_mean` | `caller_preload_unit` |
| `preload_population_standard_deviation` | `caller_preload_unit` |
| `preload_coefficient_of_variation` | `1` |
| `outside_support_preload_bolt_ids` | `1` |
| `seating_result_within_support` | `1` |
| `outside_support_relaxation_observation_ids` | `1` |
| `outside_support_reasons` | `1` |
| `qualification_source_group_count` | `count` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Flange, gasket, bolt lots, medium, pressure basis and operating state are caller reviewed.
- Bolt preload values are direct records in one exact unit and are not inferred from torque.
- Seating, relaxation and qualification metrics, uncertainty and support are caller-owned.

## 구현 근거·독립 설명

- `reviewed_gasket_joint_qualification_envelope`: Summarize direct bolt-preload records in one exact unit and compare flange, gasket and bolt material or lot identities, medium, pressure, temperature, seating-provider results and time-identified relaxation observations with caller-owned qualification evidence. Never convert torque to preload or infer gasket contact, leakage, relaxation, capacity, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_joint_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.gasket_joint_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-gasket",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "joint_id": "joint-1",
  "physical_scope_id": "scope-1",
  "flange_geometry_id": "flange-1",
  "flange_material_condition_id": "flange-material-1",
  "gasket_material_condition_id": "gasket-material-1",
  "gasket_lot_id": "gasket-lot-1",
  "bolt_material_condition_id": "bolt-material-1",
  "bolt_lot_id": "bolt-lot-1",
  "medium_id": "medium-1",
  "pressure_basis": "absolute",
  "operating_pressure_Pa": 1000000.0,
  "operating_temperature_K": 350.0,
  "bolt_preloads": [
    {
      "bolt_id": "bolt-1",
      "preload_value": 100.0,
      "preload_unit_token": "custom-force",
      "measurement_method_id": "direct-preload-method",
      "expanded_uncertainty": 2.0,
      "provider_id": "assembly-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored preload"
        }
      ]
    },
    {
      "bolt_id": "bolt-2",
      "preload_value": 102.0,
      "preload_unit_token": "custom-force",
      "measurement_method_id": "direct-preload-method",
      "expanded_uncertainty": 2.0,
      "provider_id": "assembly-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored preload"
        }
      ]
    }
  ],
  "seating_result": {
    "result_id": "seating-1",
    "metric_id": "seating-metric",
    "metric_definition": "authored seating metric",
    "reported_value": 50.0,
    "unit_token": "custom-seating-unit",
    "expanded_uncertainty": 2.0,
    "provider_id": "seating-provider",
    "provider_version": "1",
    "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored seating"
      }
    ]
  },
  "relaxation_observations": [
    {
      "observation_id": "relaxation-1",
      "elapsed_time_s": 3600.0,
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "partition": "application",
      "metric_id": "retained-preload",
      "metric_definition": "authored retained preload fraction",
      "reported_value": 0.9,
      "unit_token": "fraction",
      "expanded_uncertainty": 0.03,
      "method_id": "relaxation-method",
      "provider_id": "laboratory-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored relaxation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "flange_geometry_id": "flange-1",
      "flange_material_condition_id": "flange-material-1",
      "gasket_material_condition_id": "gasket-material-1",
      "bolt_material_condition_id": "bolt-material-1",
      "medium_id": "medium-1",
      "pressure_basis": "absolute",
      "minimum_pressure_Pa": 0.0,
      "maximum_pressure_Pa": 2000000.0,
      "minimum_temperature_K": 300.0,
      "maximum_temperature_K": 400.0,
      "preload_unit_token": "custom-force",
      "minimum_individual_preload_value": 90.0,
      "maximum_individual_preload_value": 110.0,
      "maximum_preload_coefficient_of_variation": 0.05,
      "seating_metric_support": {
        "metric_id": "seating-metric",
        "metric_definition": "authored seating metric",
        "unit_token": "custom-seating-unit",
        "minimum_supported_value": 40.0,
        "maximum_supported_value": 60.0,
        "maximum_supported_expanded_uncertainty": 5.0,
        "minimum_record_count": 1,
        "support_basis": "authored support"
      },
      "relaxation_metric_support": {
        "metric_id": "retained-preload",
        "metric_definition": "authored retained preload fraction",
        "unit_token": "fraction",
        "minimum_supported_value": 0.8,
        "maximum_supported_value": 1.0,
        "maximum_supported_expanded_uncertainty": 0.05,
        "minimum_record_count": 1,
        "support_basis": "authored support"
      },
      "qualification_evidence": [
        {
          "evidence_record_id": "qualification-1",
          "physical_specimen_id": "specimen-q1",
          "source_group_id": "source-q1",
          "partition": "qualification",
          "supported_metric_ids": [
            "seating-metric",
            "retained-preload"
          ],
          "provider_id": "qualification-provider",
          "provider_version": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored gasket qualification"
            }
          ]
        }
      ],
      "minimum_source_group_count": 1,
      "qualification_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored gasket envelope"
        }
      ]
    }
  ],
  "flange_gasket_bolt_material_and_lot_reviewed": true,
  "medium_pressure_basis_and_temperature_reviewed": true,
  "preload_method_units_uncertainty_and_bolt_identity_reviewed": true,
  "seating_provider_revision_configuration_and_digests_reviewed": true,
  "relaxation_clock_metrics_units_and_uncertainty_reviewed": true,
  "qualification_specimens_partitions_and_source_groups_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored gasket assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_joint.py#L207)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
