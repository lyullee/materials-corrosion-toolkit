# `fatigue.pressurized_annulus_load_state`

**목적:** Long homogeneous isotropic linear-elastic annulus with static pressure, nominal axial force and Saint-Venant torsion; end, notch, fixture, residual-stress and inelastic effects are excluded.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `reference_section_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inner_radius_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `outer_radius_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `pressure_evaluation_radius_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `external_axial_force_mean_N` | 예 | `{"type": "number"}` | N |
| `external_axial_force_amplitude_N` | 예 | `{"minimum": 0, "type": "number"}` | N |
| `torque_mean_N_m` | 예 | `{"type": "number"}` | N·m |
| `torque_amplitude_N_m` | 예 | `{"minimum": 0, "type": "number"}` | N·m |
| `axial_torsion_phase_rad` | 예 | `{"maximum": 6.283185307179586, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `internal_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `external_pressure_Pa` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | Pa |
| `closed_ends` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PressurizedAnnulusLoadState.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `reference_area_m2` | `m^2` |
| `polar_second_moment_m4` | `m^4` |
| `external_axial_mean_Pa` | `Pa` |
| `external_axial_amplitude_Pa` | `Pa` |
| `external_axial_minimum_Pa` | `Pa` |
| `external_axial_maximum_Pa` | `Pa` |
| `torsional_shear_mean_Pa` | `Pa` |
| `torsional_shear_amplitude_Pa` | `Pa` |
| `torsional_shear_minimum_Pa` | `Pa` |
| `torsional_shear_maximum_Pa` | `Pa` |
| `pressure_hoop_mean_Pa` | `Pa` |
| `pressure_radial_mean_Pa` | `Pa` |
| `pressure_axial_mean_Pa` | `Pa` |
| `combined_axial_mean_Pa` | `Pa` |
| `axial_torsion_phase_rad` | `rad` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Long homogeneous isotropic linear-elastic annulus with static pressure, nominal axial force and Saint-Venant torsion; end, notch, fixture, residual-stress and inelastic effects are excluded.
- The caller declares the reference section, load case, pressure evaluation radius, end condition and axial-torsion phase; no fatigue-life or strength relationship is inferred.

## 구현 근거·독립 설명

- `annular_section_equilibrium`: Nominal axial stress is force divided by annular area and Saint-Venant torsional shear is torque times radius divided by the annular polar second moment; geometry and loads are supplied by the caller.
- [Cambridge engineering notes on thick cylinders](https://www-mdp.eng.cam.ac.uk/web/library/enginfo/textbooks_dvd_only/DAN/cylinders/thick/thick.html) · `cambridge_lame`
- [FABEST HCF Competition participant package version 2.1.2](https://doi.org/10.5281/zenodo.23532147) · `fabest_hcf_protocol_v2_1_2`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.pressurized_annulus_load_state"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.pressurized_annulus_load_state"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "reference_section_id": "synthetic-net-annulus",
  "load_case_id": "synthetic-axial-torsion-pressure",
  "inner_radius_m": 0.006,
  "outer_radius_m": 0.008,
  "pressure_evaluation_radius_m": 0.006,
  "external_axial_force_mean_N": 0.0,
  "external_axial_force_amplitude_N": 10000.0,
  "torque_mean_N_m": 0.0,
  "torque_amplitude_N_m": 100.0,
  "axial_torsion_phase_rad": 1.5707963267948966,
  "internal_pressure_Pa": 60000000.0,
  "external_pressure_Pa": 0.0,
  "closed_ends": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L184)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
