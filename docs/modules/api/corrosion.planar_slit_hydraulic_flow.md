# `corrosion.planar_slit_hydraulic_flow`

**목적:** Steady incompressible Newtonian laminar flow in caller-declared variable-gap planar-slit cells; optional aperture state is digest-bound, and unsupported Reynolds/aspect ratios fail closed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `flow_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `aperture_history_result` | 아니오 | `{"anyOf": [{"additionalProperties": true, "type": "object"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `cell_aperture_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `fluid_property_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_drop_Pa` | 예 | `{"type": "number"}` | Pa |
| `dynamic_viscosity_Pa_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa·s |
| `density_kg_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | kg/m³ |
| `minimum_width_to_aperture_ratio` | 아니오 | `{"default": 20.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 20.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_reviewed_reynolds_number` | 아니오 | `{"default": 1000.0, "exclusiveMinimum": 0, "maximum": 1000.0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_and_boundary_pressures_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incompressible_newtonian_fluid_properties_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `laminar_fully_developed_slit_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PlanarSlitHydraulicFlow.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `volume_flow_rate_m3_s` | `m3/s` |
| `transport_face_velocity_m_s` | `m/s` |
| `cell_boundary_pressure_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Steady incompressible Newtonian laminar flow in caller-declared variable-gap planar-slit cells; optional aperture state is digest-bound, and unsupported Reynolds/aspect ratios fail closed.

## 구현 근거·독립 설명

- `planar_slit_steady_laminar_hydraulic_reduction`: For each caller-defined axial cell, calculate the wide-slit resistance 12 mu L/(w h^3), sum cell resistances in series, and derive a steady flow from the explicit pressure difference. Convert the common flow to cell and interpolated face velocities, reconstruct cell pressure drops, and report hydraulic-diameter Reynolds diagnostics. A supplied aperture-history result must be digest-bound to the final cell apertures.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.planar_slit_hydraulic_flow"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.planar_slit_hydraulic_flow"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "flow_id": "synthetic-flow",
  "geometry_source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "cell_widths_m": [
    0.01,
    0.01,
    0.02
  ],
  "cell_aperture_m": [
    0.0001,
    8e-05,
    6e-05
  ],
  "transverse_width_m": 0.01,
  "fluid_property_source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "pressure_drop_Pa": 1000,
  "dynamic_viscosity_Pa_s": 0.001,
  "density_kg_m3": 1000,
  "geometry_and_boundary_pressures_reviewed": true,
  "incompressible_newtonian_fluid_properties_reviewed": true,
  "laminar_fully_developed_slit_assumption_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_numeric.py#L98)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
