# `fabrication.gasket_calibrated_leakage_history`

**목적:** Caller-calibrated pressure-dependent leakage flux is evaluated at each contact node and integrated over its declared area for an aligned joint history.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_leakage_history.v1", "default": "matintegrity.gasket_leakage_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | s |
| `node_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `mean_contact_pressure_history_Pa` | 아니오 | `{"anyOf": [{"items": {"items": {"minimum": 0, "type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | Pa |
| `differential_pressure_history_Pa` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | Pa |
| `calibration` | 예 | `{"$ref": "#/$defs/GasketLeakageCalibrationMap"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `upstream_contact_result_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `contact_pressure_transfer_review_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `differential_pressure_basis_review_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_scope_review_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `complete_contact_area_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_joint_match_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `contact_field_and_leakage_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_direction_and_unit_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temporal_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `refined_contact_time_interpolation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_time_integration_subintervals` | 아니오 | `{"default": 100000, "maximum": 10000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketLeakageHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `contact_area_sum_m2` | `m2` |
| `calibration_contact_pressure_support_Pa` | `Pa` |
| `calibration_differential_pressure_support_Pa` | `Pa` |
| `time_history.differential_pressure_Pa` | `Pa` |
| `time_history.molar_leak_rate_mol_s` | `mol/s` |
| `time_history.node_responses.contact_pressure_Pa` | `Pa` |
| `time_history.node_responses.contact_area_m2` | `m2` |
| `time_history.node_responses.calibrated_molar_leak_flux_mol_s_m2` | `mol/s/m2` |
| `time_history.node_responses.molar_leak_rate_contribution_mol_s` | `mol/s` |
| `interval_molar_leak_amount_mol` | `mol` |
| `interval_integration[].start_time_s` | `s` |
| `interval_integration[].end_time_s` | `s` |
| `interval_integration[].calibration_cell_crossing_fractions[]` | `1` |
| `interval_integration[].quadratic_or_lower_subinterval_count` | `count` |
| `integration_subinterval_count` | `count` |
| `cumulative_molar_leak_amount_mol` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-calibrated pressure-dependent leakage flux is evaluated at each contact node and integrated over its declared area for an aligned joint history. Piecewise-linear pressure paths are split at calibration-axis knots and integrated exactly by Simpson quadrature on each resulting quadratic-or-lower segment.
- Calibration transfer, between-knot contact evolution, leak-tightness criteria and sealing acceptance remain caller-owned.

## 구현 근거·독립 설명

- `caller_qualified_gasket_leakage_flux_calibration`: Use a joint- and condition-matched caller calibration table of local molar leakage flux versus measured or solver-derived mean contact pressure and differential pressure. Interpolate only within its declared rectangular support and integrate over a reviewed complete partition of contact areas. For interval totals, assume linearly reconstructed pressure paths, split at every crossed calibration-axis knot, then apply Simpson integration on each resulting at-most-quadratic segment, which is exact for the declared bilinear surface and reconstruction. Enforce the declared total integration subinterval budget and a two-million-cell maximum calibration table. Preserve calibration, pressure, transfer and area-partition reviews. No universal gasket law, leakage mechanism, between-knot contact evolution, seal acceptance limit or design qualification is provided.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_calibrated_leakage_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.gasket_calibrated_leakage_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-gasket-leakage",
  "asset_id": "synthetic-asset",
  "joint_id": "synthetic-joint",
  "physical_scope_id": "synthetic-seal-boundary",
  "time_basis": "synthetic seconds from assembly",
  "time_s": [
    0.0,
    10.0
  ],
  "node_ids": [
    "node-a",
    "node-b"
  ],
  "contact_area_m2": [
    0.001,
    0.001
  ],
  "mean_contact_pressure_history_Pa": [
    [
      500000.0,
      1000000.0
    ],
    [
      400000.0,
      800000.0
    ]
  ],
  "differential_pressure_history_Pa": [
    500000.0,
    750000.0
  ],
  "calibration": {
    "differential_pressure_Pa": [
      0.0,
      1000000.0
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
          1e-09
        ]
      }
    ]
  },
  "provider_id": "synthetic-provider",
  "provider_revision": "1",
  "provider_configuration_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "calibration_record_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "contact_pressure_transfer_review_id": "synthetic-review-contact",
  "differential_pressure_basis_review_id": "synthetic-review-pressure",
  "calibration_scope_review_id": "synthetic-review-calibration",
  "complete_contact_area_partition_reviewed": true,
  "calibration_and_joint_match_reviewed": true,
  "contact_field_and_leakage_basis_reviewed": true,
  "pressure_direction_and_unit_reviewed": true,
  "temporal_alignment_reviewed": true,
  "evidence": [
    {
      "source_id": "caller_qualified_gasket_leakage_flux_calibration",
      "origin": "synthetic",
      "citation": "Project-authored synthetic calibration used only to illustrate the API contract."
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_leakage_calibration.py#L344)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
