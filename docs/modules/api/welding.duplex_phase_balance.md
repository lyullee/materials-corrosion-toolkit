# `welding.duplex_phase_balance`

**목적:** Region, material, welding-process and thermal-history identities are reviewed caller records.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `weld_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `process_history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `heat_history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/DuplexPhaseObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DuplexPhaseEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `weld_and_region_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_process_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_history_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_and_fraction_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_state_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/DuplexPhaseBalanceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `selected_envelope_id` | `1` |
| `comparison_rows` | `mixed` |
| `missing_range_observation_ids` | `1` |
| `missing_observation_range_ids` | `1` |
| `outside_declared_envelope_observation_ids` | `1` |
| `all_uncertainty_intervals_within_declared_phase_envelope` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Region, material, welding-process and thermal-history identities are reviewed caller records.
- Measured volume fractions and expanded uncertainties use an explicit method and immutable provider-state identifiers.

## 구현 근거·독립 설명

- `reviewed_duplex_weld_phase_envelope_comparison`: Compare measured weld-metal, heat-affected-zone and base-material phase-fraction uncertainty intervals with exact caller-owned regional envelopes while preserving process, heat history, method and provider digests. Do not infer unmeasured phases, properties, corrosion, cracking, life or code acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.duplex_phase_balance"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.duplex_phase_balance"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-duplex-phase",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "weld_id": "weld-1",
  "material_condition_id": "duplex-condition-1",
  "welding_process_id": "process-1",
  "process_history_id": "process-history-1",
  "heat_history_id": "heat-history-1",
  "observations": [
    {
      "observation_id": "a-1",
      "sample_id": "sample-1",
      "region_id": "weld-metal",
      "region_kind": "weld_metal",
      "phase_id": "phase-a",
      "fraction_definition": "volume_fraction",
      "measured_fraction": 0.55,
      "expanded_uncertainty_fraction": 0.02,
      "uncertainty_coverage_factor": 2.0,
      "method_id": "image-analysis",
      "method_provider_id": "provider-1",
      "method_provider_version": "1",
      "method_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_state_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase observation"
        }
      ]
    },
    {
      "observation_id": "b-1",
      "sample_id": "sample-1",
      "region_id": "weld-metal",
      "region_kind": "weld_metal",
      "phase_id": "phase-b",
      "fraction_definition": "volume_fraction",
      "measured_fraction": 0.45,
      "expanded_uncertainty_fraction": 0.02,
      "uncertainty_coverage_factor": 2.0,
      "method_id": "image-analysis",
      "method_provider_id": "provider-1",
      "method_provider_version": "1",
      "method_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase observation"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_condition_id": "duplex-condition-1",
      "welding_process_id": "process-1",
      "process_history_id": "process-history-1",
      "heat_history_id": "heat-history-1",
      "regional_ranges": [
        {
          "range_id": "range-a",
          "region_id": "weld-metal",
          "region_kind": "weld_metal",
          "phase_id": "phase-a",
          "fraction_definition": "volume_fraction",
          "minimum_fraction": 0.4,
          "maximum_fraction": 0.6,
          "range_basis": "authored caller range",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored phase range"
            }
          ]
        },
        {
          "range_id": "range-b",
          "region_id": "weld-metal",
          "region_kind": "weld_metal",
          "phase_id": "phase-b",
          "fraction_definition": "volume_fraction",
          "minimum_fraction": 0.4,
          "maximum_fraction": 0.6,
          "range_basis": "authored caller range",
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored phase range"
            }
          ]
        }
      ],
      "envelope_provider_id": "provider-1",
      "envelope_provider_version": "1",
      "envelope_state_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "applicability_basis": "authored qualification",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored phase envelope"
        }
      ]
    }
  ],
  "weld_and_region_mapping_reviewed": true,
  "material_and_process_identity_reviewed": true,
  "heat_history_identity_reviewed": true,
  "phase_and_fraction_definitions_reviewed": true,
  "method_applicability_reviewed": true,
  "uncertainty_basis_reviewed": true,
  "provider_state_digests_reviewed": true,
  "envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored duplex phase assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding_duplex_phase_balance.py#L147)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
