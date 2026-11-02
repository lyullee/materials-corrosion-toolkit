# `fabrication.gasket_correlated_scenario_envelope`

**목적:** Evaluate leakage only over complete caller-supplied joint scenarios that preserve dependence among node pressure, common differential pressure, area and calibration-grid variation.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_leakage_correlated_scenario_envelope.v1", "default": "matintegrity.gasket_leakage_correlated_scenario_envelope.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `calibration` | 예 | `{"$ref": "#/$defs/GasketLeakageCalibrationMap"}` | 계약·필드 설명 참조 |
| `calibration_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `scenario_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenario_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenario_set_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios` | 예 | `{"items": {"$ref": "#/$defs/GasketLeakageCorrelatedScenario"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_scenario_node_evaluations` | 아니오 | `{"default": 2000000, "maximum": 10000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_scenario_grid_cells` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_scenario_correlation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scenario_coverage_and_bounds_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_joint_match_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `area_partition_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketLeakageCorrelatedScenarioEnvelope.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `minimum_scenario_molar_leak_rate_mol_s` | `mol/s` |
| `maximum_scenario_molar_leak_rate_mol_s` | `mol/s` |
| `scenario_results[].molar_leak_rate_mol_s` | `mol/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Evaluate leakage only over complete caller-supplied joint scenarios that preserve dependence among node pressure, common differential pressure, area and calibration-grid variation.
- Bounds are exact only over the finite scenario set, use no probability weights, and do not establish a continuous uncertainty bound or seal acceptance.

## 구현 근거·독립 설명

- `caller_correlated_gasket_leakage_joint_scenario_envelope`: Evaluate each caller-declared complete joint scenario with its correlated node contact pressures, common differential pressure, node areas and scenario-specific calibration flux grid on the fixed calibrated axes. Bilinearly interpolate only inside calibration support and area-weight node fluxes. Return extrema and witnesses over the finite enumerated scenarios, with calibration/scenario/license evidence and bounded work budgets. Do not independently recombine variables, infer probability weights or distributions, claim continuous uncertainty bounds, extrapolate or determine seal acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_correlated_scenario_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.gasket_correlated_scenario_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-correlated",
  "asset_id": "synthetic-asset",
  "joint_id": "synthetic-joint",
  "physical_scope_id": "synthetic-scope",
  "time_s": 0,
  "node_ids": [
    "node-1"
  ],
  "calibration": {
    "differential_pressure_Pa": [
      0,
      1000000,
      2000000
    ],
    "rows": [
      {
        "contact_pressure_Pa": 0,
        "molar_leak_flux_by_delta_pressure_mol_s_m2": [
          0,
          1e-08,
          2e-08
        ]
      },
      {
        "contact_pressure_Pa": 1000000,
        "molar_leak_flux_by_delta_pressure_mol_s_m2": [
          0,
          5e-09,
          1e-08
        ]
      },
      {
        "contact_pressure_Pa": 2000000,
        "molar_leak_flux_by_delta_pressure_mol_s_m2": [
          0,
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
        1000000
      ],
      "common_differential_pressure_Pa": 1000000,
      "node_area_m2": [
        0.01
      ],
      "calibration_flux_by_contact_pressure_and_delta": [
        [
          0,
          1e-08,
          2e-08
        ],
        [
          0,
          5e-09,
          1e-08
        ],
        [
          0,
          2e-09,
          4e-09
        ]
      ]
    }
  ],
  "evidence": [
    {
      "source_id": "cal-provider",
      "origin": "synthetic",
      "citation": "Synthetic calibration record",
      "sha256": "2222222222222222222222222222222222222222222222222222222222222222"
    },
    {
      "source_id": "scenario-provider",
      "origin": "synthetic",
      "citation": "Synthetic scenario set",
      "sha256": "a83c700f66a397c26537d622ee0173dbda9d0b5f56f3be03d91f5e5ff3abc70d"
    }
  ],
  "usage_rights_evidence": [
    {
      "source_id": "synthetic-rights",
      "origin": "synthetic",
      "citation": "Synthetic project-authored fixture",
      "license_id": "CC0-1.0"
    }
  ],
  "usage_license_id": "CC0-1.0",
  "joint_scenario_correlation_reviewed": true,
  "scenario_coverage_and_bounds_reviewed": true,
  "calibration_and_joint_match_reviewed": true,
  "area_partition_and_units_reviewed": true,
  "usage_rights_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/gasket_correlated_uncertainty.py#L303)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
