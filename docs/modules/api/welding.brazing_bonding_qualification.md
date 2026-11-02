# `welding.brazing_bonding_qualification`

**목적:** Member ordering, material and surface-condition identities are preserved and compared exactly.

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
| `joints` | 예 | `{"items": {"$ref": "#/$defs/BrazingBondingJointRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/BrazingBondingQualificationEnvelope"}` | 계약·필드 설명 참조 |
| `member_material_and_surface_conditions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bonding_material_and_lot_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `process_atmosphere_and_flux_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clearance_overlap_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_pressure_cycle_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_specimen_and_source_group_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_metrics_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BrazingBondingQualification.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `qualification_envelope_id` | `1` |
| `joint_comparisons` | `1` |
| `outside_support_joint_ids` | `1` |
| `evidence_requirement_counts` | `1` |
| `qualification_evidence_summary` | `1` |
| `declared_qualification_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Member ordering, material and surface-condition identities are preserved and compared exactly.
- Clearance, overlap and cycle pressure are compared only under exact caller-declared unit tokens.
- Qualification observations and support are caller declarations, not an embedded acceptance code or bond-strength model.

## 구현 근거·독립 설명

- `reviewed_brazing_bonding_qualification_envelope`: Compare ordered member materials and surface conditions, bonding material and lot, process, flux, atmosphere, clearance, overlap and ordered heat-pressure cycle with physical-specimen and source-group observations. Preserve exact metric units, uncertainty and digests; do not infer unreported bond strength, failure probability, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.brazing_bonding_qualification"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.brazing_bonding_qualification"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-bonding",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "joints": [
    {
      "joint_id": "joint-1",
      "member_material_ids": [
        "member-a",
        "member-b"
      ],
      "member_surface_condition_ids": [
        "surface-a",
        "surface-b"
      ],
      "bonding_material_id": "filler-1",
      "bonding_material_lot_id": "lot-production-1",
      "process_id": "vacuum-braze",
      "flux_id": "no-flux",
      "joint_clearance_value": 0.1,
      "joint_clearance_unit_token": "custom-length",
      "overlap_value": 5.0,
      "overlap_unit_token": "custom-length",
      "cycle_segments": [
        {
          "segment_id": "segment-1",
          "start_time_s": 0.0,
          "end_time_s": 300.0,
          "minimum_temperature_K": 300.0,
          "maximum_temperature_K": 1000.0,
          "minimum_pressure_value": 0.0,
          "maximum_pressure_value": 0.5,
          "pressure_unit_token": "custom-pressure",
          "atmosphere_descriptor": "vacuum-a",
          "record_valid": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored bonding cycle"
            }
          ]
        }
      ],
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored bonding joint"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "envelope-1",
    "member_material_ids": [
      "member-a",
      "member-b"
    ],
    "member_surface_condition_ids": [
      "surface-a",
      "surface-b"
    ],
    "supported_bonding_material_ids": [
      "filler-1"
    ],
    "supported_process_ids": [
      "vacuum-braze"
    ],
    "supported_flux_ids": [
      "no-flux"
    ],
    "supported_atmosphere_descriptors": [
      "vacuum-a"
    ],
    "minimum_joint_clearance_value": 0.05,
    "maximum_joint_clearance_value": 0.2,
    "joint_clearance_unit_token": "custom-length",
    "minimum_overlap_value": 4.0,
    "maximum_overlap_value": 6.0,
    "overlap_unit_token": "custom-length",
    "minimum_temperature_K": 300.0,
    "maximum_temperature_K": 1100.0,
    "minimum_pressure_value": 0.0,
    "maximum_pressure_value": 1.0,
    "pressure_unit_token": "custom-pressure",
    "maximum_cycle_duration_s": 1000.0,
    "evidence_requirements": [
      {
        "requirement_id": "mechanical-1",
        "observation_kind": "mechanical",
        "metric_id": "caller-strength",
        "metric_definition": "authored mechanical endpoint",
        "unit_token": "custom-strength",
        "minimum_record_count": 1,
        "requirement_basis": "authored evidence plan"
      }
    ],
    "qualification_records": [
      {
        "evidence_record_id": "record-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "independence_group_id": "independent-1",
        "member_material_ids": [
          "member-a",
          "member-b"
        ],
        "member_surface_condition_ids": [
          "surface-a",
          "surface-b"
        ],
        "bonding_material_id": "filler-1",
        "bonding_material_lot_id": "filler-lot-q",
        "process_id": "vacuum-braze",
        "flux_id": "no-flux",
        "joint_clearance_value": 0.1,
        "joint_clearance_unit_token": "custom-length",
        "overlap_value": 5.0,
        "overlap_unit_token": "custom-length",
        "observations": [
          {
            "observation_id": "observation-1",
            "observation_kind": "mechanical",
            "metric_id": "caller-strength",
            "metric_definition": "authored mechanical endpoint",
            "method_id": "method-1",
            "reported_value": 100.0,
            "unit_token": "custom-strength",
            "expanded_uncertainty": 5.0,
            "coverage_factor": 2.0,
            "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "record_available": true,
            "evidence": [
              {
                "source_id": "authored-example",
                "origin": "synthetic",
                "citation": "authored bonding observation"
              }
            ]
          }
        ],
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "record_valid": true,
        "supports_declared_envelope": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored bonding evidence"
          }
        ]
      }
    ],
    "qualification_basis": "authored qualification programme",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored bonding envelope"
      }
    ]
  },
  "member_material_and_surface_conditions_reviewed": true,
  "bonding_material_and_lot_reviewed": true,
  "process_atmosphere_and_flux_reviewed": true,
  "clearance_overlap_and_geometry_reviewed": true,
  "heat_pressure_cycle_and_clock_reviewed": true,
  "physical_specimen_and_source_group_partitions_reviewed": true,
  "observation_metrics_units_and_uncertainty_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored bonding assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/brazing_bonding.py#L229)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
