# `degradation.hydrogen_cracking_provider_evidence`

**목적:** Pressure or fugacity basis and unit are exact caller-reviewed tokens and are never interchanged.

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
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `heat_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `crack_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `crack_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `crack_orientation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_intervals` | 예 | `{"items": {"$ref": "#/$defs/HydrogenCrackingExposure"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `toughness_result` | 예 | `{"$ref": "#/$defs/HydrogenToughnessResult"}` | 계약·필드 설명 참조 |
| `crack_driving_result` | 예 | `{"$ref": "#/$defs/HydrogenCrackDrivingResult"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/HydrogenCrackingEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_condition_and_heat_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `hydrogen_state_pressure_or_fugacity_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_exposure_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `crack_geometry_location_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `toughness_endpoint_units_uncertainty_and_provider_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `driving_metric_load_case_units_and_provider_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_specimens_source_groups_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenCrackingProviderEvidence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `clock_id` | `1` |
| `envelope_id` | `1` |
| `cumulative_exposure_s` | `s` |
| `outside_exposure_ids` | `1` |
| `toughness_result_within_declared_support` | `1` |
| `driving_result_within_declared_support` | `1` |
| `outside_support_reasons` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Pressure or fugacity basis and unit are exact caller-reviewed tokens and are never interchanged.
- Toughness and crack-driving endpoints retain separate definitions, units and provider identities.
- Calibration and holdout evidence retain disjoint physical source groups.

## 구현 근거·독립 설명

- `reviewed_hydrogen_cracking_provider_qualification_envelope`: Preserve material and heat, ordered hydrogen exposure with exact pressure or fugacity basis, crack geometry and orientation, toughness endpoint, crack-driving metric, load case, units, uncertainty and provider digests with disjoint calibration and holdout evidence. Do not mix endpoints or infer fracture acceptance, crack initiation or growth, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.hydrogen_cracking_provider_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.hydrogen_cracking_provider_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-hydrogen-cracking",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "clock_id": "clock-1",
  "material_condition_id": "material-1",
  "heat_id": "heat-1",
  "crack_geometry_id": "crack-geometry-1",
  "crack_location_id": "location-geometry-1",
  "crack_orientation_id": "orientation-1",
  "exposure_intervals": [
    {
      "interval_id": "interval-1",
      "start_time_s": 0.0,
      "end_time_s": 3600.0,
      "hydrogen_state_id": "hydrogen-gas-1",
      "pressure_or_fugacity_basis": "absolute_fugacity",
      "pressure_or_fugacity_value": 2000000.0,
      "pressure_or_fugacity_unit_token": "Pa",
      "temperature_K": 300.0,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored hydrogen exposure"
        }
      ]
    }
  ],
  "toughness_result": {
    "result_id": "toughness-1",
    "physical_specimen_id": "specimen-application",
    "source_group_id": "source-application",
    "partition": "application",
    "endpoint_kind": "K",
    "endpoint_definition_id": "K-endpoint-1",
    "reported_value": 100000000.0,
    "unit_token": "Pa*sqrt(m)",
    "expanded_uncertainty": 5000000.0,
    "provider_id": "toughness-provider",
    "provider_revision": "1",
    "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored toughness"
      }
    ]
  },
  "crack_driving_result": {
    "result_id": "driving-1",
    "load_case_id": "load-case-1",
    "metric_kind": "K",
    "metric_definition_id": "K-driving-1",
    "reported_value": 50000000.0,
    "unit_token": "Pa*sqrt(m)",
    "expanded_uncertainty": 5000000.0,
    "provider_id": "driving-provider",
    "provider_revision": "1",
    "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored crack driving"
      }
    ]
  },
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "material-1",
      "heat_id": "heat-1",
      "hydrogen_state_id": "hydrogen-gas-1",
      "pressure_or_fugacity_basis": "absolute_fugacity",
      "pressure_or_fugacity_unit_token": "Pa",
      "minimum_pressure_or_fugacity_value": 100000.0,
      "maximum_pressure_or_fugacity_value": 5000000.0,
      "minimum_temperature_K": 280.0,
      "maximum_temperature_K": 350.0,
      "maximum_cumulative_exposure_s": 10000.0,
      "supported_crack_geometry_ids": [
        "crack-geometry-1"
      ],
      "supported_crack_location_ids": [
        "location-geometry-1"
      ],
      "supported_crack_orientation_ids": [
        "orientation-1"
      ],
      "toughness_endpoint_kind": "K",
      "toughness_endpoint_definition_id": "K-endpoint-1",
      "toughness_unit_token": "Pa*sqrt(m)",
      "minimum_supported_toughness_value": 10000000.0,
      "maximum_supported_toughness_value": 200000000.0,
      "maximum_toughness_expanded_uncertainty": 10000000.0,
      "toughness_provider_id": "toughness-provider",
      "toughness_provider_revision": "1",
      "toughness_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "driving_metric_kind": "K",
      "driving_metric_definition_id": "K-driving-1",
      "driving_unit_token": "Pa*sqrt(m)",
      "minimum_supported_driving_value": 0.0,
      "maximum_supported_driving_value": 150000000.0,
      "maximum_driving_expanded_uncertainty": 10000000.0,
      "driving_provider_id": "driving-provider",
      "driving_provider_revision": "1",
      "driving_provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "qualification_evidence": [
        {
          "evidence_record_id": "q-cal",
          "physical_specimen_id": "specimen-cal",
          "source_group_id": "source-cal",
          "partition": "calibration",
          "supported_toughness_endpoint_definition_ids": [
            "K-endpoint-1"
          ],
          "supported_driving_metric_definition_ids": [
            "K-driving-1"
          ],
          "provider_id": "qualification-provider",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
          "evidence_record_id": "q-hold",
          "physical_specimen_id": "specimen-hold",
          "source_group_id": "source-hold",
          "partition": "holdout",
          "supported_toughness_endpoint_definition_ids": [
            "K-endpoint-1"
          ],
          "supported_driving_metric_definition_ids": [
            "K-driving-1"
          ],
          "provider_id": "qualification-provider",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
          "citation": "authored hydrogen-cracking envelope"
        }
      ]
    }
  ],
  "material_condition_and_heat_reviewed": true,
  "hydrogen_state_pressure_or_fugacity_basis_reviewed": true,
  "temperature_exposure_clock_reviewed": true,
  "crack_geometry_location_and_orientation_reviewed": true,
  "toughness_endpoint_units_uncertainty_and_provider_reviewed": true,
  "driving_metric_load_case_units_and_provider_reviewed": true,
  "physical_specimens_source_groups_and_partitions_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored hydrogen-cracking assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_cracking.py#L238)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
