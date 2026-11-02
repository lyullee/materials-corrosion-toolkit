# `degradation.high_temperature_hydrogen_applicability`

**목적:** Hydrogen pressure is an absolute partial pressure in pascals; gauge or total pressure is not silently substituted.

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
| `heat_treatment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `composition` | 예 | `{"items": {"$ref": "#/$defs/MaterialCompositionEntry"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposures` | 예 | `{"items": {"$ref": "#/$defs/HighTemperatureHydrogenExposure"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `microstructure_evidence` | 예 | `{"items": {"$ref": "#/$defs/HydrogenMicrostructureEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/HighTemperatureHydrogenEnvelope"}` | 계약·필드 설명 참조 |
| `material_identity_composition_and_heat_treatment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `hydrogen_species_and_absolute_partial_pressure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_pressure_clock_and_time_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `microstructure_locations_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspection_method_and_provider_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_and_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HighTemperatureHydrogenApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `clock_id` | `1` |
| `envelope_id` | `1` |
| `composition_comparisons` | `mixed` |
| `composition_outside_support_ids` | `1` |
| `exposure_comparisons` | `mixed` |
| `outside_support_exposure_ids` | `1` |
| `cumulative_exposure_s` | `s` |
| `cumulative_exposure_within_declared_support` | `1` |
| `microstructure_comparisons` | `mixed` |
| `outside_support_microstructure_record_ids` | `1` |
| `physical_source_group_count` | `1` |
| `physical_source_group_count_within_declared_support` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Hydrogen pressure is an absolute partial pressure in pascals; gauge or total pressure is not silently substituted.
- Material condition, composition and heat treatment match caller-owned evidence identities and unit tokens.
- Microstructure descriptors and provider qualification bounds are reviewed caller inputs.

## 구현 근거·독립 설명

- `reviewed_high_temperature_hydrogen_qualification_envelope`: Compare exact material composition and heat-treatment identity, absolute hydrogen partial-pressure and temperature-time exposure intervals, and microstructure or inspection evidence with a caller-owned qualification envelope. Do not bundle industry curves, reaction kinetics, property loss, damage, cracks, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.high_temperature_hydrogen_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.high_temperature_hydrogen_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-hth",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "clock_id": "clock-1",
  "material_condition_id": "condition-1",
  "heat_treatment_id": "treatment-1",
  "composition": [
    {
      "constituent_id": "constituent-a",
      "reported_value": 0.01,
      "unit": "mass_fraction",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored composition"
        }
      ]
    }
  ],
  "exposures": [
    {
      "interval_id": "interval-1",
      "start_time_s": 0.0,
      "end_time_s": 3600.0,
      "hydrogen_species": "H2",
      "pressure_basis": "absolute_partial_pressure",
      "hydrogen_partial_pressure_Pa_abs": 2000000.0,
      "temperature_K": 700.0,
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored exposure"
        }
      ]
    }
  ],
  "microstructure_evidence": [
    {
      "record_id": "micro-1",
      "physical_source_group_id": "sample-1",
      "inspection_location": "authored mapped location",
      "inspection_method_id": "inspection-1",
      "provider_id": "provider-1",
      "provider_version": "1.0",
      "provider_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "microstructure_descriptor": "caller-descriptor-a",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_available": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored microstructure"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "envelope-1",
    "material_condition_id": "condition-1",
    "heat_treatment_id": "treatment-1",
    "supported_hydrogen_species": [
      "H2"
    ],
    "pressure_basis": "absolute_partial_pressure",
    "minimum_hydrogen_partial_pressure_Pa_abs": 100000.0,
    "maximum_hydrogen_partial_pressure_Pa_abs": 3000000.0,
    "minimum_temperature_K": 600.0,
    "maximum_temperature_K": 750.0,
    "maximum_cumulative_exposure_s": 7200.0,
    "composition_support": [
      {
        "constituent_id": "constituent-a",
        "unit": "mass_fraction",
        "minimum_supported_value": 0.005,
        "maximum_supported_value": 0.02
      }
    ],
    "supported_microstructure_descriptors": [
      "caller-descriptor-a"
    ],
    "supported_inspection_method_ids": [
      "inspection-1"
    ],
    "minimum_physical_source_group_count": 1,
    "provider_qualification": {
      "qualification_id": "qualification-1",
      "provider_id": "provider-1",
      "provider_version": "1.0",
      "provider_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "qualification_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "calibration_dataset_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "holdout_dataset_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "calibration_physical_source_group_count": 8,
      "holdout_physical_source_group_count": 3,
      "calibration_and_holdout_independent": true,
      "validation_metric_definition": "authored mismatch fraction",
      "validation_metric_value": 0.05,
      "validation_metric_unit": "1",
      "maximum_supported_validation_metric": 0.1,
      "qualification_basis": "authored validation plan",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored HTH qualification"
        }
      ]
    },
    "applicability_basis": "authored qualification programme",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored HTH envelope"
      }
    ]
  },
  "material_identity_composition_and_heat_treatment_reviewed": true,
  "hydrogen_species_and_absolute_partial_pressure_reviewed": true,
  "temperature_pressure_clock_and_time_reviewed": true,
  "microstructure_locations_and_source_groups_reviewed": true,
  "inspection_method_and_provider_lineage_reviewed": true,
  "record_and_result_digests_reviewed": true,
  "missingness_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored HTH assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/high_temperature_hydrogen.py#L175)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
