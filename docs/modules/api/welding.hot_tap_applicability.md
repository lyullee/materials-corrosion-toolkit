# `welding.hot_tap_applicability`

**목적:** Host pipe, material condition and operating pressure basis are exact caller-reviewed identities.

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
| `host_pipe_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `host_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `operating_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `operating_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `wall_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `flow_heat_extraction_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `branch_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `consumable_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `hydrogen_control_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_results` | 예 | `{"items": {"$ref": "#/$defs/HotTapProviderResult"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/HotTapQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `host_pipe_material_and_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `operating_pressure_basis_and_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_thickness_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `flow_and_heat_extraction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `welding_process_consumable_and_hydrogen_control_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_results_units_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_specimens_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HotTapApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `envelope_id` | `1` |
| `metric_comparisons` | `mixed` |
| `outside_metric_ids` | `1` |
| `qualification_source_group_count` | `1` |
| `unsupported_evidence_metric_ids` | `1` |
| `outside_support_reasons` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Host pipe, material condition and operating pressure basis are exact caller-reviewed identities.
- Thermal/burn-through and hydrogen-cracking values are external provider results, not internal calculations.
- Qualification evidence preserves physical specimens, source groups, uncertainty and provider digests.

## 구현 근거·독립 설명

- `reviewed_hot_tap_provider_qualification_envelope`: Compare reviewed host-pipe condition, exact pressure basis, operating temperature, wall thickness, flow heat-extraction, branch and joint geometry, welding consumable and hydrogen-control identities with caller-owned thermal or burn-through and hydrogen-cracking provider outputs and partitioned qualification evidence. Do not bundle charts or infer acceptance, capacity, burn-through or crack probability, or life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.hot_tap_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.hot_tap_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-hot-tap",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "host_pipe_id": "pipe-1",
  "host_material_condition_id": "material-1",
  "pressure_basis": "absolute_internal_pressure",
  "operating_pressure_Pa": 2000000.0,
  "operating_temperature_K": 320.0,
  "wall_thickness_m": 0.01,
  "flow_heat_extraction_descriptor": "flowing-product-a",
  "branch_geometry_id": "branch-geometry-1",
  "joint_geometry_id": "joint-geometry-1",
  "welding_process_id": "process-1",
  "consumable_condition_id": "consumable-1",
  "hydrogen_control_descriptor": "control-1",
  "provider_results": [
    {
      "result_id": "result-thermal-margin",
      "result_kind": "thermal_or_burn_through_screen",
      "metric_id": "thermal-margin",
      "metric_definition": "authored thermal-margin",
      "reported_value": 200.0,
      "unit_token": "custom-temperature",
      "provider_id": "provider-1",
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
          "citation": "authored hot-tap result"
        }
      ]
    },
    {
      "result_id": "result-hydrogen-index",
      "result_kind": "hydrogen_cracking_screen",
      "metric_id": "hydrogen-index",
      "metric_definition": "authored hydrogen-index",
      "reported_value": 0.2,
      "unit_token": "custom-index",
      "provider_id": "provider-1",
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
          "citation": "authored hot-tap result"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "host_pipe_id": "pipe-1",
      "host_material_condition_id": "material-1",
      "pressure_basis": "absolute_internal_pressure",
      "minimum_operating_pressure_Pa": 100000.0,
      "maximum_operating_pressure_Pa": 5000000.0,
      "minimum_operating_temperature_K": 280.0,
      "maximum_operating_temperature_K": 400.0,
      "minimum_wall_thickness_m": 0.005,
      "maximum_wall_thickness_m": 0.03,
      "supported_flow_heat_extraction_descriptors": [
        "flowing-product-a"
      ],
      "supported_branch_geometry_ids": [
        "branch-geometry-1"
      ],
      "supported_joint_geometry_ids": [
        "joint-geometry-1"
      ],
      "supported_welding_process_ids": [
        "process-1"
      ],
      "supported_consumable_condition_ids": [
        "consumable-1"
      ],
      "supported_hydrogen_control_descriptors": [
        "control-1"
      ],
      "provider_metric_support": [
        {
          "result_kind": "thermal_or_burn_through_screen",
          "metric_id": "thermal-margin",
          "unit_token": "custom-temperature",
          "minimum_supported_value": 0.0,
          "maximum_supported_value": 500.0,
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "support_basis": "authored support"
        },
        {
          "result_kind": "hydrogen_cracking_screen",
          "metric_id": "hydrogen-index",
          "unit_token": "custom-index",
          "minimum_supported_value": 0.0,
          "maximum_supported_value": 1.0,
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
            "thermal-margin",
            "hydrogen-index"
          ],
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "expanded_uncertainty": 0.05,
          "uncertainty_unit_token": "custom-uncertainty",
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored hot-tap evidence"
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
          "citation": "authored hot-tap envelope"
        }
      ]
    }
  ],
  "host_pipe_material_and_condition_reviewed": true,
  "operating_pressure_basis_and_temperature_reviewed": true,
  "wall_thickness_and_geometry_reviewed": true,
  "flow_and_heat_extraction_reviewed": true,
  "welding_process_consumable_and_hydrogen_control_reviewed": true,
  "provider_results_units_and_support_reviewed": true,
  "qualification_specimens_and_source_groups_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored hot-tap assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hot_tap.py#L191)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
