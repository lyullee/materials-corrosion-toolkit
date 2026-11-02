# `fabrication.gasket_leakage_box_envelope`

**목적:** Returns deterministic extrema over caller-specified independent pressure, area and calibration-flux intervals using the piecewise-bilinear map without extrapolation.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_leakage_box_envelope.v1", "default": "matintegrity.gasket_leakage_box_envelope.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `calibration` | 예 | `{"$ref": "#/$defs/GasketLeakageCalibrationMap"}` | 계약·필드 설명 참조 |
| `nodes` | 예 | `{"items": {"$ref": "#/$defs/GasketLeakageBoxNode"}, "maxItems": 256, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_differential_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_differential_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `calibration_flux_lower_bound_mol_s_m2` | 예 | `{"items": {"items": {"minimum": 0, "type": "number"}, "type": "array"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `calibration_flux_upper_bound_mol_s_m2` | 예 | `{"items": {"items": {"minimum": 0, "type": "number"}, "type": "array"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `calibration_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `bound_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bound_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bound_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `maximum_candidate_evaluations` | 아니오 | `{"default": 2000000, "maximum": 10000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_and_bound_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `box_uncertainty_set_and_independence_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_area_units_and_physical_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `box_covers_intended_operating_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketLeakageBoxEnvelope.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `minimum_molar_leak_rate_mol_s` | `mol/s` |
| `maximum_molar_leak_rate_mol_s` | `mol/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Returns deterministic extrema over caller-specified independent pressure, area and calibration-flux intervals using the piecewise-bilinear map without extrapolation.
- Exactness applies only to the declared rectangular input set; no probability, covariance, correlated uncertainty or seal acceptance is inferred.

## 구현 근거·독립 설명

- `caller_gasket_leakage_independent_box_envelope`: Compute minimum and maximum total gasket leak rate over a caller-declared independent rectangular set of node contact pressures, positive areas, one common differential pressure and entrywise calibration-flux bounds. Require the nominal calibration table to lie inside the declared flux intervals, exact calibration-grid shapes, matching Evidence and usage rights, explicit box-independence and coverage reviews, and no extrapolation. Evaluate contact-pressure endpoints and table knots within each node interval, and common differential-pressure endpoints and table knots within the common interval; use nonnegative interpolation weights and positive area bounds to combine witnesses. The extrema are exact only for this finite-dimensional rectangular set and piecewise-bilinear reconstruction, not correlated/continuous mechanics, a probability/confidence interval, seal acceptance or qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_leakage_box_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.gasket_leakage_box_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-gasket-leakage-box",
  "asset_id": "synthetic-asset",
  "joint_id": "synthetic-flanged-joint",
  "physical_scope_id": "synthetic-seal-control-volume",
  "time_s": 0.0,
  "calibration": {
    "differential_pressure_Pa": [
      0.0,
      100000.0
    ],
    "rows": [
      {
        "contact_pressure_Pa": 0.0,
        "molar_leak_flux_by_delta_pressure_mol_s_m2": [
          0.0,
          1e-06
        ]
      },
      {
        "contact_pressure_Pa": 1000000.0,
        "molar_leak_flux_by_delta_pressure_mol_s_m2": [
          0.0,
          5e-07
        ]
      }
    ]
  },
  "nodes": [
    {
      "node_id": "synthetic-sealing-node-1",
      "minimum_contact_pressure_Pa": 100000.0,
      "maximum_contact_pressure_Pa": 900000.0,
      "minimum_area_m2": 0.001,
      "maximum_area_m2": 0.0012
    }
  ],
  "minimum_differential_pressure_Pa": 10000.0,
  "maximum_differential_pressure_Pa": 90000.0,
  "calibration_flux_lower_bound_mol_s_m2": [
    [
      0.0,
      9e-07
    ],
    [
      0.0,
      4.5e-07
    ]
  ],
  "calibration_flux_upper_bound_mol_s_m2": [
    [
      0.0,
      1.1e-06
    ],
    [
      0.0,
      5.5e-07
    ]
  ],
  "calibration_provider_id": "synthetic-gasket-calibration",
  "calibration_provider_revision": "synthetic-example-1",
  "calibration_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "bound_provider_id": "synthetic-gasket-box-bound",
  "bound_provider_revision": "synthetic-example-1",
  "bound_record_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "maximum_candidate_evaluations": 1000,
  "evidence": [
    {
      "source_id": "synthetic-gasket-calibration",
      "origin": "synthetic",
      "citation": "Project-authored synthetic calibration fixture; no seal behavior is claimed.",
      "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    },
    {
      "source_id": "synthetic-gasket-box-bound",
      "origin": "synthetic",
      "citation": "Project-authored synthetic rectangular interval fixture.",
      "sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
    }
  ],
  "usage_rights_evidence": [
    {
      "source_id": "synthetic-gasket-rights",
      "origin": "synthetic",
      "citation": "Synthetic project-authored fixture with no third-party dataset.",
      "license_id": "CC0-1.0"
    }
  ],
  "usage_license_id": "CC0-1.0",
  "calibration_and_bound_records_reviewed": true,
  "box_uncertainty_set_and_independence_scope_reviewed": true,
  "pressure_area_units_and_physical_mapping_reviewed": true,
  "box_covers_intended_operating_uncertainty_reviewed": true,
  "usage_rights_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/gasket_correlated_uncertainty.py#L592)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
