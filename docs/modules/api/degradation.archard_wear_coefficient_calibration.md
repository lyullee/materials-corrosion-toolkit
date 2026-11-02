# `degradation.archard_wear_coefficient_calibration`

**목적:** Calibration is restricted to one material/counterface/contact/lubrication regime with SI force, distance, hardness and wear volume.

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
| `counterface_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `contact_geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `lubrication_regime_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ArchardCalibrationObservation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_specimen_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_specimen_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `material_contact_lubrication_and_temperature_regime_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `si_units_load_distance_hardness_and_volume_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `hardness_identity_and_measurement_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_groups_and_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_weights_missingness_and_validity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_support_and_no_extrapolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ArchardWearCoefficientCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `dimensionless_wear_coefficient` | `1` |
| `calibration_support` | `SI` |
| `calibration_hardness_identity_ids` | `1` |
| `outside_support_holdout_observation_ids` | `1` |
| `excluded_missing_or_invalid_observation_ids` | `1` |
| `calibration_observation_ids` | `1` |
| `holdout_observation_ids` | `1` |
| `holdout_log_coefficient_bias` | `1` |
| `holdout_log_coefficient_rmse` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Calibration is restricted to one material/counterface/contact/lubrication regime with SI force, distance, hardness and wear volume.
- The dimensionless coefficient follows V*H/(F*s) for each valid caller observation.
- Calibration and holdout physical specimens and source groups are disjoint.

## 구현 근거·독립 설명

- `weighted_archard_wear_coefficient_calibration`: Derive one positive dimensionless Archard coefficient per valid calibration record from measured wear volume, hardness, normal force and sliding distance, then form a caller-weighted geometric mean for one reviewed material, counterface, contact and lubrication regime. Preserve disjoint specimen/source partitions, uncertainties and excluded records; evaluate holdout only inside calibration support without modeling fretting-corrosion interaction, service life, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.archard_wear_coefficient_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.archard_wear_coefficient_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "wear-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "material_condition_id": "material-1",
  "counterface_material_condition_id": "counterface-1",
  "contact_geometry_id": "contact-1",
  "lubrication_regime_id": "dry-1",
  "observations": [
    {
      "observation_id": "c1",
      "physical_specimen_id": "s1",
      "source_group_id": "g1",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 10,
      "sliding_distance_m": 100,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": 1e-10,
      "expanded_uncertainty_wear_volume_m3": 1e-15,
      "uncertainty_coverage_factor": 2,
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "c2",
      "physical_specimen_id": "s2",
      "source_group_id": "g2",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 20,
      "sliding_distance_m": 200,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": 4e-10,
      "expanded_uncertainty_wear_volume_m3": 1e-15,
      "uncertainty_coverage_factor": 2,
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "c3",
      "physical_specimen_id": "s3",
      "source_group_id": "g3",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 15,
      "sliding_distance_m": 150,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": 2.25e-10,
      "expanded_uncertainty_wear_volume_m3": 1e-15,
      "uncertainty_coverage_factor": 2,
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "h1",
      "physical_specimen_id": "s4",
      "source_group_id": "g4",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 12,
      "sliding_distance_m": 120,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": 1.4400000000000002e-10,
      "expanded_uncertainty_wear_volume_m3": 1e-15,
      "uncertainty_coverage_factor": 2,
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "h2",
      "physical_specimen_id": "s5",
      "source_group_id": "g5",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 18,
      "sliding_distance_m": 180,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": 3.24e-10,
      "expanded_uncertainty_wear_volume_m3": 1e-15,
      "uncertainty_coverage_factor": 2,
      "weight": 1,
      "record_status": "valid",
      "missing_or_invalid_basis": null,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
      "observation_id": "m1",
      "physical_specimen_id": "s6",
      "source_group_id": "g6",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "counterface_material_condition_id": "counterface-1",
      "contact_geometry_id": "contact-1",
      "lubrication_regime_id": "dry-1",
      "temperature_K": 300,
      "normal_force_N": 14,
      "sliding_distance_m": 140,
      "hardness_Pa": 1000000000,
      "hardness_identity_id": "hardness-1",
      "measured_wear_volume_m3": null,
      "expanded_uncertainty_wear_volume_m3": null,
      "uncertainty_coverage_factor": null,
      "weight": null,
      "record_status": "missing",
      "missing_or_invalid_basis": "missing result",
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
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
  "minimum_holdout_specimen_count": 2,
  "minimum_holdout_source_group_count": 2,
  "material_contact_lubrication_and_temperature_regime_reviewed": true,
  "si_units_load_distance_hardness_and_volume_reviewed": true,
  "hardness_identity_and_measurement_basis_reviewed": true,
  "specimen_source_groups_and_partitions_reviewed": true,
  "uncertainty_weights_missingness_and_validity_reviewed": true,
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

[계산 구현과 주석 확인](../../../src/matintegrity/models/archard_calibration.py#L107)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
