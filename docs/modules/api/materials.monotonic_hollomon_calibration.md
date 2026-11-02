# `materials.monotonic_hollomon_calibration`

**목적:** Weighted log-space Hollomon fit to caller-reviewed monotonic pre-necking stress and elastic-subtracted plastic strain.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `quantity_convention` | 예 | `{"enum": ["engineering", "true"], "type": "string"}` | 계약·필드 설명 참조 |
| `points` | 예 | `{"items": {"$ref": "#/$defs/MonotonicStressStrainPoint"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_specimen_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_specimen_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `monotonic_loading_and_quantity_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_strain_units_sign_and_elastic_subtraction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pre_necking_windows_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_independence_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_weights_validity_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_support_and_no_extrapolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MonotonicHollomonCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `strength_coefficient` | `caller_stress_unit` |
| `strain_hardening_exponent` | `1` |
| `stress_unit_token` | `1` |
| `quantity_convention` | `1` |
| `calibration_plastic_strain_support` | `1` |
| `outside_support_holdout_point_ids` | `1` |
| `calibration_point_ids` | `1` |
| `holdout_point_ids` | `1` |
| `holdout_log_stress_bias` | `1` |
| `holdout_log_stress_rmse` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weighted log-space Hollomon fit to caller-reviewed monotonic pre-necking stress and elastic-subtracted plastic strain.
- Engineering or true quantity convention is preserved without implicit conversion.
- Calibration and holdout specimen, source and independence groups are disjoint.

## 구현 근거·독립 설명

- `weighted_pre_necking_monotonic_hollomon_calibration`: Fit log true or engineering stress against log plastic strain for caller-reviewed, weighted pre-necking monotonic calibration points after explicit elastic-strain subtraction. Preserve specimen, source and independence partitions; evaluate holdout error only inside calibration support without post-necking extrapolation, cyclic inference, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.monotonic_hollomon_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.monotonic_hollomon_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "f1",
  "asset_id": "a1",
  "location_id": "l1",
  "material_condition_id": "m1",
  "quantity_convention": "true",
  "points": [
    {
      "point_id": "c1",
      "physical_specimen_id": "s1",
      "source_group_id": "g1",
      "independence_group_id": "g1",
      "partition": "calibration",
      "material_condition_id": "m1",
      "quantity_convention": "true",
      "stress_value": 251.188643150958,
      "stress_unit_token": "MPa",
      "total_strain": 0.0022559432157547897,
      "strain_unit_token": "1",
      "elastic_modulus": 200000.0,
      "elastic_modulus_unit_token": "MPa",
      "stress_standard_uncertainty": 1.0,
      "weight": 1.0,
      "pre_necking_window_id": "window-1",
      "pre_necking_reviewed": true,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "point_id": "c2",
      "physical_specimen_id": "s2",
      "source_group_id": "g2",
      "independence_group_id": "g2",
      "partition": "calibration",
      "material_condition_id": "m1",
      "quantity_convention": "true",
      "stress_value": 331.44540173399866,
      "stress_unit_token": "MPa",
      "total_strain": 0.0056572270086699935,
      "strain_unit_token": "1",
      "elastic_modulus": 200000.0,
      "elastic_modulus_unit_token": "MPa",
      "stress_standard_uncertainty": 1.0,
      "weight": 1.0,
      "pre_necking_window_id": "window-1",
      "pre_necking_reviewed": true,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "point_id": "c3",
      "physical_specimen_id": "s3",
      "source_group_id": "g3",
      "independence_group_id": "g3",
      "partition": "calibration",
      "material_condition_id": "m1",
      "quantity_convention": "true",
      "stress_value": 398.10717055349727,
      "stress_unit_token": "MPa",
      "total_strain": 0.011990535852767487,
      "strain_unit_token": "1",
      "elastic_modulus": 200000.0,
      "elastic_modulus_unit_token": "MPa",
      "stress_standard_uncertainty": 1.0,
      "weight": 1.0,
      "pre_necking_window_id": "window-1",
      "pre_necking_reviewed": true,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "point_id": "h1",
      "physical_specimen_id": "s4",
      "source_group_id": "g4",
      "independence_group_id": "g4",
      "partition": "holdout",
      "material_condition_id": "m1",
      "quantity_convention": "true",
      "stress_value": 288.53998118144267,
      "stress_unit_token": "MPa",
      "total_strain": 0.0034426999059072134,
      "strain_unit_token": "1",
      "elastic_modulus": 200000.0,
      "elastic_modulus_unit_token": "MPa",
      "stress_standard_uncertainty": 1.0,
      "weight": 1.0,
      "pre_necking_window_id": "window-1",
      "pre_necking_reviewed": true,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "minimum_calibration_specimen_count": 3,
  "minimum_calibration_source_group_count": 3,
  "minimum_holdout_specimen_count": 1,
  "minimum_holdout_source_group_count": 1,
  "monotonic_loading_and_quantity_convention_reviewed": true,
  "stress_strain_units_sign_and_elastic_subtraction_reviewed": true,
  "pre_necking_windows_reviewed": true,
  "specimen_source_independence_and_partitions_reviewed": true,
  "uncertainty_weights_validity_and_digests_reviewed": true,
  "calibration_support_and_no_extrapolation_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/monotonic_plastic_curve.py#L89)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
