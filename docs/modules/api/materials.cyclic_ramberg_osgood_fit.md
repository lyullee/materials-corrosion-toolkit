# `materials.cyclic_ramberg_osgood_fit`

**목적:** Weighted log-space fit of stabilized cyclic stress amplitude against positive plastic strain amplitude.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `fit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/StabilizedCyclicObservation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_specimen_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_specimen_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `material_and_stabilized_cycle_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_strain_amplitudes_units_and_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `plastic_strain_definition_and_elastic_modulus_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_independence_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `weights_and_record_validity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_and_no_extrapolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CyclicRambergOsgoodFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `fit_id` | `1` |
| `cyclic_strength_coefficient` | `caller_stress_unit` |
| `cyclic_strain_hardening_exponent` | `1` |
| `stress_unit_token` | `1` |
| `calibration_plastic_strain_support` | `1` |
| `outside_support_holdout_observation_ids` | `1` |
| `calibration_observation_ids` | `1` |
| `holdout_observation_ids` | `1` |
| `holdout_log_stress_bias` | `log(stress)` |
| `holdout_log_stress_rmse` | `log(stress)` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weighted log-space fit of stabilized cyclic stress amplitude against positive plastic strain amplitude.
- Calibration and holdout specimens, source groups and independence groups are disjoint.
- The fitted coefficients are restricted to the calibration plastic-strain support.

## 구현 근거·독립 설명

- `weighted_stabilized_cyclic_ramberg_osgood_fit`: Fit log stabilized cyclic stress amplitude as an affine function of log positive plastic strain amplitude using caller weights and calibration records only. Preserve exact stress/elastic-modulus units, material condition and disjoint specimen/source/independence groups; report holdout log-stress diagnostics without extrapolating or inferring fatigue life, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.cyclic_ramberg_osgood_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.cyclic_ramberg_osgood_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "fit_id": "f1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "material_condition_id": "m1",
  "observations": [
    {
      "observation_id": "c1",
      "physical_specimen_id": "s1",
      "source_group_id": "g1",
      "independence_group_id": "g1",
      "partition": "calibration",
      "material_condition_id": "m1",
      "stress_amplitude": 251.188643150958,
      "stress_unit_token": "MPa",
      "total_strain_amplitude": 0.001,
      "strain_unit_token": "1",
      "plastic_strain_definition": "explicit_reported",
      "elastic_modulus": null,
      "elastic_modulus_unit_token": null,
      "reported_plastic_strain_amplitude": 0.001,
      "weight": 1.0,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored cyclic observation"
        }
      ]
    },
    {
      "observation_id": "c2",
      "physical_specimen_id": "s2",
      "source_group_id": "g2",
      "independence_group_id": "g2",
      "partition": "calibration",
      "material_condition_id": "m1",
      "stress_amplitude": 331.44540173399866,
      "stress_unit_token": "MPa",
      "total_strain_amplitude": 0.004,
      "strain_unit_token": "1",
      "plastic_strain_definition": "explicit_reported",
      "elastic_modulus": null,
      "elastic_modulus_unit_token": null,
      "reported_plastic_strain_amplitude": 0.004,
      "weight": 1.0,
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored cyclic observation"
        }
      ]
    },
    {
      "observation_id": "c3",
      "physical_specimen_id": "s3",
      "source_group_id": "g3",
      "independence_group_id": "g3",
      "partition": "calibration",
      "material_condition_id": "m1",
      "stress_amplitude": 398.10717055349727,
      "stress_unit_token": "MPa",
      "total_strain_amplitude": 0.01,
      "strain_unit_token": "1",
      "plastic_strain_definition": "explicit_reported",
      "elastic_modulus": null,
      "elastic_modulus_unit_token": null,
      "reported_plastic_strain_amplitude": 0.01,
      "weight": 1.0,
      "record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored cyclic observation"
        }
      ]
    },
    {
      "observation_id": "h1",
      "physical_specimen_id": "s4",
      "source_group_id": "g4",
      "independence_group_id": "g4",
      "partition": "holdout",
      "material_condition_id": "m1",
      "stress_amplitude": 288.53998118144267,
      "stress_unit_token": "MPa",
      "total_strain_amplitude": 0.002,
      "strain_unit_token": "1",
      "plastic_strain_definition": "explicit_reported",
      "elastic_modulus": null,
      "elastic_modulus_unit_token": null,
      "reported_plastic_strain_amplitude": 0.002,
      "weight": 1.0,
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored cyclic holdout"
        }
      ]
    }
  ],
  "minimum_calibration_specimen_count": 3,
  "minimum_calibration_source_group_count": 3,
  "minimum_holdout_specimen_count": 1,
  "minimum_holdout_source_group_count": 1,
  "material_and_stabilized_cycle_definition_reviewed": true,
  "stress_strain_amplitudes_units_and_sign_reviewed": true,
  "plastic_strain_definition_and_elastic_modulus_reviewed": true,
  "specimen_source_independence_and_partitions_reviewed": true,
  "weights_and_record_validity_reviewed": true,
  "support_and_no_extrapolation_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored cyclic fit"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/cyclic_ramberg_osgood_fit.py#L97)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
