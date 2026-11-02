# `inspection.test_water_quality_summary`

**목적:** Samples retain explicit location, time, method and evidence identities on one reviewed test clock.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_start_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `test_end_time_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `required_location_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_sampling_gap_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `samples` | 예 | `{"items": {"$ref": "#/$defs/TestWaterSample"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `envelope` | 예 | `{"$ref": "#/$defs/TestWaterEnvelope"}` | 계약·필드 설명 참조 |
| `sampling_plan_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sample_identity_and_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_methods_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_envelope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_completeness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TestWaterQualityRecord.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `record_id` | `1` |
| `coverage` | `1` |
| `sample_comparisons` | `1` |
| `violating_sample_ids` | `1` |
| `observed_temperature_range_K` | `K` |
| `observed_pH_range` | `1` |
| `observed_conductivity_range_S_m` | `S/m` |
| `observed_chloride_range_kg_m3` | `kg/m^3` |
| `declared_envelope_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Samples retain explicit location, time, method and evidence identities on one reviewed test clock.
- Coverage and property limits are caller-owned inputs; no regulatory or material limit is embedded.
- Observed sample properties are not interpolated between sampling events.

## 구현 근거·독립 설명

- `declared_test_water_envelope`: Compare reviewed time- and location-identified water samples with caller-owned temperature, pH, conductivity and chloride envelopes while preserving sampling coverage and exact SI quantities. Do not supply regulatory limits, interpolate unobserved water chemistry, or infer corrosion or microbial activity.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.test_water_quality_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.test_water_quality_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "record_id": "authored-water-example",
  "test_id": "test-1",
  "asset_id": "synthetic",
  "material_condition_id": "material-1",
  "clock_id": "authored-test-clock",
  "test_start_time_s": 0.0,
  "test_end_time_s": 100.0,
  "required_location_ids": [
    "inlet",
    "outlet"
  ],
  "maximum_sampling_gap_s": 50.0,
  "samples": [
    {
      "sample_id": "i1",
      "location_id": "inlet",
      "sample_time_s": 25.0,
      "temperature_K": 295.0,
      "pH": 7.0,
      "conductivity_S_m": 0.02,
      "chloride_kg_m3": 0.01,
      "measurement_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored water sample"
        }
      ]
    },
    {
      "sample_id": "i2",
      "location_id": "inlet",
      "sample_time_s": 75.0,
      "temperature_K": 295.0,
      "pH": 7.0,
      "conductivity_S_m": 0.02,
      "chloride_kg_m3": 0.01,
      "measurement_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored water sample"
        }
      ]
    },
    {
      "sample_id": "o1",
      "location_id": "outlet",
      "sample_time_s": 25.0,
      "temperature_K": 295.0,
      "pH": 7.0,
      "conductivity_S_m": 0.02,
      "chloride_kg_m3": 0.01,
      "measurement_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored water sample"
        }
      ]
    },
    {
      "sample_id": "o2",
      "location_id": "outlet",
      "sample_time_s": 75.0,
      "temperature_K": 295.0,
      "pH": 7.0,
      "conductivity_S_m": 0.02,
      "chloride_kg_m3": 0.01,
      "measurement_method_id": "method-1",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored water sample"
        }
      ]
    }
  ],
  "envelope": {
    "envelope_id": "envelope-1",
    "material_condition_id": "material-1",
    "minimum_temperature_K": 280.0,
    "maximum_temperature_K": 310.0,
    "minimum_pH": 6.0,
    "maximum_pH": 8.0,
    "minimum_conductivity_S_m": 0.0,
    "maximum_conductivity_S_m": 0.05,
    "minimum_chloride_kg_m3": 0.0,
    "maximum_chloride_kg_m3": 0.02,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored water envelope"
      }
    ]
  },
  "sampling_plan_reviewed": true,
  "sample_identity_and_location_reviewed": true,
  "clock_and_units_reviewed": true,
  "measurement_methods_reviewed": true,
  "material_envelope_reviewed": true,
  "record_completeness_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/test_water_quality.py#L90)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
