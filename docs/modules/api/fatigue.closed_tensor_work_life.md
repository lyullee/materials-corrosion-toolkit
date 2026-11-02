# `fatigue.closed_tensor_work_life`

**목적:** Caller-provided closed 3D stress-strain tensor cycles and material-matched work-life calibration with bounded log-log interpolation and explicit Miner accumulation.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.closed_tensor_work_life.v1", "default": "matintegrity.closed_tensor_work_life.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `analysis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cycles` | 예 | `{"items": {"$ref": "#/$defs/ClosedTensorCycle"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `strain_shear_convention` | 예 | `{"enum": ["tensor", "engineering"], "type": "string"}` | 계약·필드 설명 참조 |
| `time_reconstruction` | 아니오 | `{"default": "piecewise_linear", "enum": ["piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"], "type": "string"}` | 계약·필드 설명 참조 |
| `stress_history_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_history_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `strain_history_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `strain_history_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `dissipated_energy_density_J_m3` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 3, "type": "array"}` | J/m³ |
| `cycles_to_failure` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_closure_stress_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_closure_strain_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `tensor_basis_and_order_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_strain_conjugacy_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `cycle_boundary_and_closure_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `time_reconstruction_and_derivative_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `periodic_spline_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `material_calibration_applicability_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `work_life_fit_and_miner_rule_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ClosedTensorWorkLife.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cycle_results[].signed_closed_loop_work_density_J_m3` | `J/m^3` |
| `cycle_results[].dissipated_energy_density_J_m3` | `J/m^3` |
| `cycle_results[].cycles_to_failure` | `cycle` |
| `cycle_results[].miner_damage` | `1` |
| `total_miner_damage` | `1` |
| `cycle_count` | `cycle` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-provided closed 3D stress-strain tensor cycles and material-matched work-life calibration with bounded log-log interpolation and explicit Miner accumulation.
- Path-work response is caller-calibrated and is not a universal nonproportional fatigue law or code acceptance result.

## 구현 근거·독립 설명

- `closed_tensor_work_life_calibration`: Integrate stress contraction with strain increments over each caller-supplied ordered, endpoint-closed 3D tensor cycle using trapezoidal segment work for piecewise-linear paths or exact polynomial-product integration for cubic-Hermite paths with caller-supplied times and endpoint derivatives. Use the selected tensor or engineering shear convention. Map positive absolute loop work to a material-condition-matched caller calibration using bounded piecewise log-log interpolation, then sum explicitly allocated counts with linear Miner damage only when all cycles are closed and supported. Require caller review of tensor basis, conjugacy, cycle extraction/reconstruction, calibration applicability and accumulation rule; do not infer rainflow cycles, derivatives, slopes, extrapolation, a universal nonproportional law or code acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.closed_tensor_work_life"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.closed_tensor_work_life"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.closed_tensor_work_life.v1",
  "analysis_id": "synthetic-closed-tensor-work-example",
  "material_condition_id": "synthetic-steel-condition-a",
  "location_id": "synthetic-gauge-section",
  "cycles": [
    {
      "cycle_id": "cycle-1",
      "allocated_cycle_count": 1.0,
      "sample_ids": [
        "s0",
        "s1",
        "s2",
        "s3",
        "s4",
        "s5",
        "s6",
        "s7",
        "s8"
      ],
      "stress_tensor_components_Pa": [
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          100000000,
          0,
          0,
          0,
          0,
          0
        ],
        [
          100000000,
          0,
          0,
          0,
          0,
          0
        ],
        [
          100000000,
          0,
          0,
          0,
          0,
          0
        ],
        [
          100000000,
          0,
          0,
          100000000,
          0,
          0
        ],
        [
          100000000,
          0,
          0,
          100000000,
          0,
          0
        ],
        [
          0,
          0,
          0,
          100000000,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "strain_tensor_components": [
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0.002,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0.002,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0.002,
          0,
          0,
          0.002,
          0,
          0
        ],
        [
          0.002,
          0,
          0,
          0.002,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0.002,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ]
      ],
      "sample_time_s": [
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0
      ],
      "stress_time_derivative_components_Pa_s": [
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ]
      ],
      "strain_time_derivative_components_s_inv": [
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ]
      ]
    }
  ],
  "strain_shear_convention": "engineering",
  "stress_history_source_id": "synthetic-stress-record",
  "stress_history_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
  "strain_history_source_id": "synthetic-strain-record",
  "strain_history_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
  "calibration_id": "synthetic-work-life-fit",
  "calibration_material_condition_id": "synthetic-steel-condition-a",
  "calibration_source_id": "synthetic-calibration-fixture",
  "calibration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
  "dissipated_energy_density_J_m3": [
    100000,
    200000,
    400000
  ],
  "cycles_to_failure": [
    1000000,
    100000,
    10000
  ],
  "maximum_closure_stress_error_Pa": 0,
  "maximum_closure_strain_error": 0,
  "tensor_basis_and_order_reviewed": true,
  "stress_strain_conjugacy_reviewed": true,
  "cycle_boundary_and_closure_reviewed": true,
  "material_calibration_applicability_reviewed": true,
  "work_life_fit_and_miner_rule_reviewed": true,
  "time_reconstruction": "piecewise_cubic_hermite",
  "time_reconstruction_and_derivative_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/multiaxial_work_life.py#L337)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
