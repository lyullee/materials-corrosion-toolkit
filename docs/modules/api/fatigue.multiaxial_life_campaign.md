# `fatigue.multiaxial_life_campaign`

**목적:** Closed caller local tensor cycle to supplied sampled planes and same-condition FS/SWT or caller shear-normal calibration; preserve ties and support limits.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `history` | 예 | `{"$ref": "#/$defs/CriticalPlaneHistory"}` | 계약·필드 설명 참조 |
| `calibration` | 예 | `{"discriminator": {"mapping": {"fatemi_socie": "#/$defs/FsLifeCalibration", "kandil_brown_miller_curve": "#/$defs/KandilBrownMillerLifeCalibration", "shear_normal_strain_curve": "#/$defs/ShearNormalStrainLifeCalibration", "swt": "#/$defs/SwtLifeCalibration"}, "propertyName": "criterion"}, "oneOf": [{"$ref": "#/$defs/FsLifeCalibration"}, {"$ref": "#/$defs/SwtLifeCalibration"}, {"$ref": "#/$defs/ShearNormalStrainLifeCalibration"}, {"$ref": "#/$defs/KandilBrownMillerLifeCalibration"}]}` | 계약·필드 설명 참조 |
| `calibration_material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_valid_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_valid_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `shear_range_method` | 예 | `{"enum": ["directional_component", "maximum_pairwise_chord", "minimum_enclosing_circle"], "type": "string"}` | 계약·필드 설명 참조 |
| `local_measure_calibration_and_nonproportional_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MultiaxialLifeCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| 가변 구조·진단·증거 결과 | 구현·예제의 `values` 확인 |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Closed caller local tensor cycle to supplied sampled planes and same-condition FS/SWT or caller shear-normal calibration; preserve ties and support limits.

## 구현 근거·독립 설명

- `multiaxial_cycle_life_composition`: Compose the declared closed local tensor cycle, finite supplied plane factors and caller material-matched FS or SWT strain-life coefficients. Keep directional, pairwise-chord and enclosing-circle shear ranges explicit and retain exactly tied sampled planes. Root finding is restricted to calibrated cycle support; no continuous optimum, rainflow, nonproportional qualification or acceptance is inferred.
- `caller_shear_normal_strain_curve_life`: For each caller-supplied finite plane, combine nonnegative shear-strain amplitude with caller-weighted normal-strain amplitude. Select the largest declared parameter, retain exact sampled ties, and interpolate log(cycles) against log(parameter) only between ordered, same-condition caller calibration points. Bind ordered curve and full calibration digests and point-level source records. This is a generic independently authored user-curve mapping, not a claim to reproduce a named criterion; do not extrapolate or infer calibration rights, continuous-plane extrema, path-sensitive law, qualification or acceptance.
- `kandil_brown_miller_curve_life`: For each supplied finite plane, obtain sampled shear-strain range from the maximum pairwise chord of the in-plane engineering-shear vector path. Restrict the KBM parameter to planes tied for the largest sampled shear range, then combine shear-strain amplitude with a caller-calibrated coefficient times the full normal-strain range on that plane. Map only by bounded log-log interpolation on an ordered, same-condition caller life curve and bind curve/calibration digests plus point-level Evidence. This is a sampled, caller-calibrated implementation of the KBM parameter form; it does not imply a continuous-plane optimum, universal coefficient, cycle counting, data rights, material qualification or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.multiaxial_life_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.multiaxial_life_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "campaign_id": "authored-multiaxial-life",
  "history": {
    "history_id": "synthetic-closed-uniaxial-cycle",
    "material_condition_id": "synthetic-condition",
    "location_id": "reviewed-integration-point",
    "tensor_source_id": "synthetic-closed-form",
    "sample_ids": [
      "s0",
      "s1",
      "s2",
      "s3",
      "s4"
    ],
    "stress_tensor_components_Pa": [
      [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
      ],
      [
        100000000.0,
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
        -100000000.0,
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
    "strain_tensor_components": [
      [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
      ],
      [
        0.0005,
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
        -0.0005,
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
    "candidate_planes": [
      {
        "plane_id": "normal-x",
        "normal": [
          1.0,
          0.0,
          0.0
        ],
        "in_plane_direction": [
          0.0,
          1.0,
          0.0
        ]
      },
      {
        "plane_id": "xy-45",
        "normal": [
          0.7071067811865476,
          0.7071067811865476,
          0.0
        ],
        "in_plane_direction": [
          -0.7071067811865476,
          0.7071067811865476,
          0.0
        ]
      }
    ],
    "representative_cycle_declared": true,
    "maximum_stress_closure_error_Pa": 0.0,
    "maximum_strain_closure_error": 0.0,
    "fatemi_socie_coefficient": 0.3,
    "normalization_stress_Pa": 400000000.0
  },
  "calibration": {
    "criterion": "fatemi_socie",
    "shear_modulus_Pa": 80000000000.0,
    "shear_fatigue_strength_coefficient_Pa": 500000000.0,
    "shear_fatigue_strength_exponent": -0.1,
    "shear_fatigue_ductility_coefficient": 0.3,
    "shear_fatigue_ductility_exponent": -0.5,
    "calibrated_fatemi_socie_coefficient": 0.3,
    "calibrated_normalization_stress_Pa": 400000000.0
  },
  "calibration_material_condition_id": "synthetic-condition",
  "calibration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "minimum_valid_cycles": 1.0,
  "maximum_valid_cycles": 1000000000000000.0,
  "shear_range_method": "directional_component",
  "local_measure_calibration_and_nonproportional_scope_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/sequence_numeric.py#L33)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
