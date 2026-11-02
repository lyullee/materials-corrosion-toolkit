# `integration.gasket_leakage_scenario_exposure`

**목적:** Only a digest-pinned computed finite correlated leakage scenario snapshot is accepted.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_leakage_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `source_leakage_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_start_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `exposure_duration_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `constant_leakage_state_over_window_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `time_basis_and_window_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketLeakageScenarioExposure.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `exposure_start_time_s` | `s` |
| `exposure_end_time_s` | `s` |
| `exposure_duration_s` | `s` |
| `scenario_exposure_amounts[].snapshot_molar_leak_rate_mol_s` | `mol/s` |
| `scenario_exposure_amounts[].constant_state_exposure_amount_mol` | `mol` |
| `minimum_scenario_exposure_amount_mol` | `mol` |
| `maximum_scenario_exposure_amount_mol` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only a digest-pinned computed finite correlated leakage scenario snapshot is accepted.
- Molar leak rate is multiplied by an explicit duration under a caller-reviewed constant-state assumption; no transient state or probability is inferred.

## 구현 근거·독립 설명

- `caller_constant_state_gasket_leakage_scenario_exposure`: Multiply every rate in a digest-pinned computed finite correlated gasket leakage scenario envelope by an explicitly caller-reviewed constant-state duration. Preserve source assessment/input/context/scenario digests, snapshot time and run-context asset/location/time basis; report finite-scenario molar exposure extrema and witnesses only. Do not infer pressure/contact/calibration evolution, scenario probability, continuous bounds or seal acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.gasket_leakage_scenario_exposure"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.gasket_leakage_scenario_exposure"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-exposure",
  "source_leakage_result": {
    "schema_version": "matintegrity.assessment.v1",
    "model_id": "fabrication.gasket_correlated_scenario_envelope",
    "model_version": "1.0.0",
    "status": "computed",
    "inputs": {
      "schema_version": "matintegrity.gasket_leakage_correlated_scenario_envelope.v1",
      "assessment_id": "synthetic-correlated-start",
      "asset_id": "synthetic-asset",
      "joint_id": "synthetic-joint",
      "physical_scope_id": "synthetic-scope",
      "time_s": 0.0,
      "node_ids": [
        "node-1"
      ],
      "calibration": {
        "differential_pressure_Pa": [
          0.0,
          1000000.0,
          2000000.0
        ],
        "rows": [
          {
            "contact_pressure_Pa": 0.0,
            "molar_leak_flux_by_delta_pressure_mol_s_m2": [
              0.0,
              1e-08,
              2e-08
            ]
          },
          {
            "contact_pressure_Pa": 1000000.0,
            "molar_leak_flux_by_delta_pressure_mol_s_m2": [
              0.0,
              5e-09,
              1e-08
            ]
          },
          {
            "contact_pressure_Pa": 2000000.0,
            "molar_leak_flux_by_delta_pressure_mol_s_m2": [
              0.0,
              2e-09,
              4e-09
            ]
          }
        ]
      },
      "calibration_provider_id": "cal-provider",
      "calibration_provider_revision": "1",
      "calibration_record_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "scenario_provider_id": "scenario-provider",
      "scenario_provider_revision": "1",
      "scenario_set_sha256": "a83c700f66a397c26537d622ee0173dbda9d0b5f56f3be03d91f5e5ff3abc70d",
      "scenarios": [
        {
          "scenario_id": "joint-case-1",
          "node_contact_pressure_Pa": [
            1000000.0
          ],
          "common_differential_pressure_Pa": 1000000.0,
          "node_area_m2": [
            0.01
          ],
          "calibration_flux_by_contact_pressure_and_delta": [
            [
              0.0,
              1e-08,
              2e-08
            ],
            [
              0.0,
              5e-09,
              1e-08
            ],
            [
              0.0,
              2e-09,
              4e-09
            ]
          ]
        }
      ],
      "maximum_scenario_node_evaluations": 2000000,
      "maximum_scenario_grid_cells": 2000000,
      "evidence": [
        {
          "source_id": "cal-provider",
          "origin": "synthetic",
          "citation": "Synthetic calibration record",
          "license_id": null,
          "sha256": "2222222222222222222222222222222222222222222222222222222222222222"
        },
        {
          "source_id": "scenario-provider",
          "origin": "synthetic",
          "citation": "Synthetic scenario set",
          "license_id": null,
          "sha256": "a83c700f66a397c26537d622ee0173dbda9d0b5f56f3be03d91f5e5ff3abc70d"
        }
      ],
      "usage_rights_evidence": [
        {
          "source_id": "synthetic-rights",
          "origin": "synthetic",
          "citation": "Synthetic project-authored fixture",
          "license_id": "CC0-1.0",
          "sha256": null
        }
      ],
      "usage_license_id": "CC0-1.0",
      "joint_scenario_correlation_reviewed": true,
      "scenario_coverage_and_bounds_reviewed": true,
      "calibration_and_joint_match_reviewed": true,
      "area_partition_and_units_reviewed": true,
      "usage_rights_reviewed": true,
      "computational_use_authorized": true
    },
    "values": {
      "assessment_id": "synthetic-correlated-start",
      "asset_id": "synthetic-asset",
      "joint_id": "synthetic-joint",
      "physical_scope_id": "synthetic-scope",
      "time_s": 0.0,
      "input_sha256": "1bc92f01b71c789fdf177cf9edb6eddd9e3c50ef6f15ba63e060545f539d315a",
      "calibration_record_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "calibration_map_sha256": "7bc8a7f0cbaaecfc7646e11daafa7d319c6ae0eb22f11571b2d43a0f544d73bb",
      "scenario_set_sha256": "a83c700f66a397c26537d622ee0173dbda9d0b5f56f3be03d91f5e5ff3abc70d",
      "scenario_provider_id": "scenario-provider",
      "scenario_provider_revision": "1",
      "usage_license_id": "CC0-1.0",
      "calibration_provider_id": "cal-provider",
      "calibration_provider_revision": "1",
      "node_ids": [
        "node-1"
      ],
      "usage_rights_evidence_sha256": "f0d3bd2221fbdbdaf62d90b0952134d99209a81febccf59533dcf53d4cdc541a",
      "maximum_scenario_node_evaluations": 2000000,
      "maximum_scenario_grid_cells": 2000000,
      "uncertainty_semantics": "finite_caller_supplied_joint_scenarios_without_probability_weights",
      "scenario_results": [
        {
          "scenario_id": "joint-case-1",
          "common_differential_pressure_Pa": 1000000.0,
          "molar_leak_rate_mol_s": 5e-11,
          "node_responses": [
            {
              "node_id": "node-1",
              "contact_pressure_Pa": 1000000.0,
              "contact_area_m2": 0.01,
              "calibrated_molar_leak_flux_mol_s_m2": 5e-09,
              "molar_leak_rate_contribution_mol_s": 5e-11,
              "interpolation_cell": {
                "contact_pressure_lower_index": 0,
                "differential_pressure_lower_index": 0
              }
            }
          ],
          "calibration_flux_sha256": "aefa7c125c91ae45d9786f0f175cc6559af3c3758361418d941d1309258f1572"
        }
      ],
      "scenario_results_sha256": "48777ab71aaff8cc1b881fd80b3f363b06f538266fee69846116f6fa6fbb5f1e",
      "minimum_scenario_molar_leak_rate_mol_s": 5e-11,
      "minimum_witness_scenario_id": "joint-case-1",
      "maximum_scenario_molar_leak_rate_mol_s": 5e-11,
      "maximum_witness_scenario_id": "joint-case-1",
      "scenario_count": 1,
      "calibration_uncertainty_included": true,
      "node_area_uncertainty_included": true,
      "pressure_correlation_preserved": true,
      "meaning": "exact extrema over the finite supplied joint scenario set only; not a probability, confidence interval, or continuous uncertainty-set bound"
    },
    "units": {
      "minimum_scenario_molar_leak_rate_mol_s": "mol/s",
      "maximum_scenario_molar_leak_rate_mol_s": "mol/s",
      "scenario_results[].molar_leak_rate_mol_s": "mol/s"
    },
    "assumptions": [
      "Evaluate leakage only over complete caller-supplied joint scenarios that preserve dependence among node pressure, common differential pressure, area and calibration-grid variation.",
      "Bounds are exact only over the finite scenario set, use no probability weights, and do not establish a continuous uncertainty bound or seal acceptance."
    ],
    "notes": [
      "Each scenario jointly supplies all node pressures, shared differential pressure, node areas and calibration-grid fluxes; these correlated values are never independently recombined.",
      "Piecewise-bilinear interpolation is evaluated only inside the fixed calibration axes. Reported extrema cover the enumerated scenarios only.",
      "No probability weights, Gaussian assumptions, covariance extrapolation, temporal integration or seal acceptance are inferred."
    ],
    "context": {
      "asset_id": "synthetic-asset",
      "location_id": "synthetic-location",
      "time_basis": "elapsed_seconds",
      "evidence": [],
      "metadata": {}
    },
    "input_digest": "6464a17890cb212c475563d004dad61c12e91b25d4e9a6df778cdd1d3fb181f8",
    "source_ids": [
      "caller_correlated_gasket_leakage_joint_scenario_envelope"
    ],
    "qualification": "user_model",
    "runtime": {
      "matintegrity": "0.1.0.dev0",
      "python": "3.12.14",
      "numpy": "2.3.5",
      "pydantic": "2.14.1",
      "pint": "0.26.2",
      "scipy": "1.18.1",
      "rainflow": "3.2.0"
    },
    "probability_semantics": {}
  },
  "source_leakage_result_sha256": "6553c12ffc878dfd12769cedd6752a3280d5f69c4b3a45419e41044abb521e63",
  "exposure_start_time_s": 0,
  "exposure_duration_s": 3600,
  "constant_leakage_state_over_window_reviewed": true,
  "time_basis_and_window_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_leakage_scenario_exposure.py#L58)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
