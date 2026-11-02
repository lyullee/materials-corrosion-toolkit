# `degradation.hydrogen_fatigue_provider_evidence`

**목적:** Material condition, hydrogen species, quantity basis and units match exactly.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `hydrogen_species` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_quantity_kind` | 예 | `{"enum": ["absolute_partial_pressure", "fugacity"], "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_quantity_value` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `exposure_quantity_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `load_ratio` | 예 | `{"exclusiveMaximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `frequency_Hz` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `waveform_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_result` | 예 | `{"$ref": "#/$defs/HydrogenFatigueProviderResult"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/HydrogenFatigueQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `hydrogen_species_quantity_basis_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_load_ratio_frequency_and_waveform_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `crack_growth_definitions_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `solver_provider_revision_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_qualification_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenFatigueProviderEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `qualification_envelope_id` | `1` |
| `provider_result_record_id` | `1` |
| `curve_or_result_id` | `1` |
| `result_kind` | `1` |
| `outside_support_reasons` | `1` |
| `outside_delta_k_point_ids` | `1` |
| `provider_growth_points` | `mixed` |
| `calibration_source_group_ids` | `1` |
| `holdout_source_group_ids` | `1` |
| `holdout_independence_group_ids` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material condition, hydrogen species, quantity basis and units match exactly.
- Pressure and fugacity are not converted; load and waveform conditions are explicit.
- Provider growth evidence is not integrated into life, probability or acceptance.

## 구현 근거·독립 설명

- `reviewed_hydrogen_fatigue_provider_qualification_envelope`: Preserve material condition, hydrogen species and exact absolute-partial-pressure or fugacity basis, temperature, load ratio, frequency, waveform, crack-growth metric definitions and external provider curve or rate results with partitioned qualification evidence. Do not bundle proprietary curves, convert pressure to fugacity, interpolate or integrate growth, or infer life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.hydrogen_fatigue_provider_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.hydrogen_fatigue_provider_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-hydrogen-fatigue",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "material_id": "material-1",
  "material_condition_id": "condition-1",
  "hydrogen_species": "H2",
  "exposure_quantity_kind": "absolute_partial_pressure",
  "exposure_quantity_value": 2000000.0,
  "exposure_quantity_unit_token": "Pa_abs",
  "temperature_K": 293.15,
  "load_ratio": 0.1,
  "frequency_Hz": 1.0,
  "waveform_descriptor": "sine",
  "provider_result": {
    "result_record_id": "result-1",
    "curve_or_result_id": "curve-1",
    "result_kind": "tabulated_growth_curve",
    "material_condition_id": "condition-1",
    "hydrogen_species": "H2",
    "exposure_quantity_kind": "absolute_partial_pressure",
    "exposure_quantity_value": 2000000.0,
    "exposure_quantity_unit_token": "Pa_abs",
    "temperature_K": 293.15,
    "load_ratio": 0.1,
    "frequency_Hz": 1.0,
    "waveform_descriptor": "sine",
    "delta_k_definition": "caller range definition",
    "delta_k_unit_token": "custom-delta-k",
    "growth_rate_definition": "caller cycle growth definition",
    "growth_rate_unit_token": "custom-length-per-cycle",
    "points": [
      {
        "point_id": "point-1",
        "delta_k_value": 10.0,
        "growth_rate_value": 1e-08,
        "expanded_growth_rate_uncertainty": 1e-09,
        "uncertainty_coverage_factor": 2.0,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored curve point"
          }
        ]
      },
      {
        "point_id": "point-2",
        "delta_k_value": 20.0,
        "growth_rate_value": 4e-08,
        "expanded_growth_rate_uncertainty": 4e-09,
        "uncertainty_coverage_factor": 2.0,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored curve point"
          }
        ]
      }
    ],
    "solver_or_method_id": "method-1",
    "solver_or_method_revision": "method-revision-1",
    "provider_id": "provider-1",
    "provider_revision": "revision-1",
    "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "record_valid": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored hydrogen-fatigue result"
      }
    ]
  },
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "hydrogen_species": "H2",
      "exposure_quantity_kind": "absolute_partial_pressure",
      "exposure_quantity_unit_token": "Pa_abs",
      "minimum_exposure_quantity_value": 100000.0,
      "maximum_exposure_quantity_value": 5000000.0,
      "minimum_temperature_K": 250.0,
      "maximum_temperature_K": 350.0,
      "minimum_load_ratio": 0.0,
      "maximum_load_ratio": 0.8,
      "minimum_frequency_Hz": 0.1,
      "maximum_frequency_Hz": 10.0,
      "supported_waveform_descriptors": [
        "sine"
      ],
      "delta_k_definition": "caller range definition",
      "delta_k_unit_token": "custom-delta-k",
      "minimum_delta_k_value": 5.0,
      "maximum_delta_k_value": 30.0,
      "growth_rate_definition": "caller cycle growth definition",
      "growth_rate_unit_token": "custom-length-per-cycle",
      "supported_result_kinds": [
        "tabulated_growth_curve",
        "predicted_growth_rate"
      ],
      "solver_or_method_id": "method-1",
      "solver_or_method_revision": "method-revision-1",
      "provider_id": "provider-1",
      "provider_revision": "revision-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "qualification_evidence": [
        {
          "evidence_record_id": "cal-1",
          "partition": "calibration",
          "physical_specimen_id": "specimen-cal-1",
          "source_group_id": "source-cal",
          "independence_group_id": "ind-cal",
          "material_condition_id": "condition-1",
          "hydrogen_species": "H2",
          "exposure_quantity_kind": "absolute_partial_pressure",
          "exposure_quantity_unit_token": "Pa_abs",
          "delta_k_definition": "caller range definition",
          "delta_k_unit_token": "custom-delta-k",
          "growth_rate_definition": "caller cycle growth definition",
          "growth_rate_unit_token": "custom-length-per-cycle",
          "provider_id": "provider-1",
          "provider_revision": "revision-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
          "evidence_record_id": "hold-1",
          "partition": "holdout",
          "physical_specimen_id": "specimen-hold-1",
          "source_group_id": "source-hold",
          "independence_group_id": "ind-hold",
          "material_condition_id": "condition-1",
          "hydrogen_species": "H2",
          "exposure_quantity_kind": "absolute_partial_pressure",
          "exposure_quantity_unit_token": "Pa_abs",
          "delta_k_definition": "caller range definition",
          "delta_k_unit_token": "custom-delta-k",
          "growth_rate_definition": "caller cycle growth definition",
          "growth_rate_unit_token": "custom-length-per-cycle",
          "provider_id": "provider-1",
          "provider_revision": "revision-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
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
      "minimum_calibration_source_group_count": 1,
      "minimum_holdout_source_group_count": 1,
      "minimum_holdout_independence_group_count": 1,
      "qualification_basis": "authored validation plan",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored hydrogen-fatigue envelope"
        }
      ]
    }
  ],
  "material_and_condition_reviewed": true,
  "hydrogen_species_quantity_basis_and_units_reviewed": true,
  "temperature_load_ratio_frequency_and_waveform_reviewed": true,
  "crack_growth_definitions_units_and_uncertainty_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "solver_provider_revision_and_digests_reviewed": true,
  "calibration_holdout_qualification_reviewed": true,
  "qualification_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_fatigue_provider.py#L202)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
