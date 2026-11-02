# `fabrication.pull_off_adhesion_calibration`

**목적:** Force-area stress requires explicit newtons and square metres and is kept separate from provider stress.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_layer_stack_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_preparation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cure_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `adhesive_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `force_calibrations` | 예 | `{"items": {"$ref": "#/$defs/PullOffForceCalibration"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/PullOffObservation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_thresholds` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CallerPullOffThreshold"}, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_paired_calibration_record_count` | 예 | `{"minimum": 3, "type": "integer"}` | 계약·필드 설명 참조 |
| `dollies_locations_layers_and_substrate_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_preparation_cure_exposure_and_adhesive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `force_area_and_provider_stress_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `force_calibration_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `break_mode_descriptors_and_fractions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_revision_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_threshold_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PullOffAdhesionCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `physical_scope_id` | `1` |
| `coating_system_id` | `1` |
| `paired_calibration_record_count` | `1` |
| `provider_minus_force_area_bias_Pa` | `Pa` |
| `provider_minus_force_area_repeatability_Pa` | `Pa` |
| `observation_rows` | `mixed` |
| `holdout_provider_comparisons` | `mixed` |
| `caller_threshold_margins` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Force-area stress requires explicit newtons and square metres and is kept separate from provider stress.
- Calibration and holdout specimen, source and independence groups are disjoint.
- Break-mode descriptions and fractions are caller records and are not interpreted by the model.

## 구현 근거·독립 설명

- `authored_partitioned_pull_off_adhesion_evidence_calibration`: Preserve dolly, location, layer, substrate, preparation, cure, exposure, adhesive, break-mode components, calibration, provider and immutable evidence identities. Calculate force divided by area only for explicit SI inputs, retain provider stress separately, estimate paired calibration bias and compare independent holdout inside support without interpreting mixed break modes, embedding acceptance tables, predicting coating life or creating failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.pull_off_adhesion_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.pull_off_adhesion_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "pull-off-1",
  "asset_id": "asset-1",
  "location_id": "coating-scope-1",
  "physical_scope_id": "coating-physical-scope-1",
  "coating_system_id": "coating-system-1",
  "coating_layer_stack_id": "layers-1",
  "substrate_condition_id": "substrate-1",
  "surface_preparation_id": "prep-1",
  "cure_condition_id": "cure-1",
  "exposure_condition_id": "exposure-1",
  "adhesive_condition_id": "adhesive-1",
  "force_calibrations": [
    {
      "calibration_id": "force-cal-1",
      "force_instrument_id": "force-instrument-1",
      "instrument_configuration_id": "configuration-1",
      "force_unit_token": "N",
      "minimum_supported_force_N": 100.0,
      "maximum_supported_force_N": 1000.0,
      "expanded_uncertainty_N": 2.0,
      "provider_id": "calibration-provider",
      "provider_revision": "1",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "cal-1",
      "physical_specimen_id": "spec-cal-1",
      "source_group_id": "source-cal-a",
      "independence_group_id": "ind-spec-cal-1",
      "partition": "calibration",
      "dolly_id": "dolly-cal-1",
      "physical_location_id": "location-cal-1",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 400.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 4080000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-2",
      "physical_specimen_id": "spec-cal-2",
      "source_group_id": "source-cal-a",
      "independence_group_id": "ind-spec-cal-2",
      "partition": "calibration",
      "dolly_id": "dolly-cal-2",
      "physical_location_id": "location-cal-2",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 450.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 4630000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-3",
      "physical_specimen_id": "spec-cal-3",
      "source_group_id": "source-cal-b",
      "independence_group_id": "ind-spec-cal-3",
      "partition": "calibration",
      "dolly_id": "dolly-cal-3",
      "physical_location_id": "location-cal-3",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 500.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 5090000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-4",
      "physical_specimen_id": "spec-cal-4",
      "source_group_id": "source-cal-b",
      "independence_group_id": "ind-spec-cal-4",
      "partition": "calibration",
      "dolly_id": "dolly-cal-4",
      "physical_location_id": "location-cal-4",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 550.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 5610000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "hold-1",
      "physical_specimen_id": "spec-hold-1",
      "source_group_id": "source-hold",
      "independence_group_id": "ind-spec-hold-1",
      "partition": "holdout",
      "dolly_id": "dolly-hold-1",
      "physical_location_id": "location-hold-1",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 425.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 4370000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "hold-2",
      "physical_specimen_id": "spec-hold-2",
      "source_group_id": "source-hold",
      "independence_group_id": "ind-spec-hold-2",
      "partition": "holdout",
      "dolly_id": "dolly-hold-2",
      "physical_location_id": "location-hold-2",
      "location_definition": "authored coating location",
      "coating_layer_stack_id": "layers-1",
      "substrate_condition_id": "substrate-1",
      "surface_preparation_id": "prep-1",
      "cure_condition_id": "cure-1",
      "exposure_condition_id": "exposure-1",
      "adhesive_condition_id": "adhesive-1",
      "caller_break_mode_id": "mixed-caller-mode",
      "break_mode_components": [
        {
          "component_id": "component-a",
          "caller_descriptor": "caller layer A",
          "reported_area_fraction": 0.6
        },
        {
          "component_id": "component-b",
          "caller_descriptor": "caller layer B",
          "reported_area_fraction": 0.4
        }
      ],
      "measurement_basis": "both",
      "force_calibration_id": "force-cal-1",
      "pull_force_N": 525.0,
      "pull_force_unit_token": "N",
      "pull_force_expanded_uncertainty_N": 2.0,
      "dolly_area_m2": 0.0001,
      "dolly_area_unit_token": "m^2",
      "dolly_area_expanded_uncertainty_m2": 1e-06,
      "provider_stress_Pa": 5330000.0,
      "provider_stress_unit_token": "Pa",
      "provider_stress_expanded_uncertainty_Pa": 50000.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "nominal_weight": 1.0,
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_thresholds": [
    {
      "threshold_id": "threshold-1",
      "stress_basis": "force_area",
      "minimum_stress_Pa": 3000000.0,
      "authority_basis": "authored caller threshold",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "minimum_paired_calibration_record_count": 3,
  "dollies_locations_layers_and_substrate_reviewed": true,
  "surface_preparation_cure_exposure_and_adhesive_reviewed": true,
  "force_area_and_provider_stress_units_reviewed": true,
  "force_calibration_and_uncertainty_reviewed": true,
  "break_mode_descriptors_and_fractions_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "provider_revision_configuration_and_digests_reviewed": true,
  "caller_threshold_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pull_off_adhesion.py#L186)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
