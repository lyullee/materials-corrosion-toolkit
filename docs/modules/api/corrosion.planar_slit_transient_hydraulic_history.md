# `corrosion.planar_slit_transient_hydraulic_history`

**목적:** Exact interval propagation for the caller-reviewed reduced balance I dQ/dt + R Q = pressure_drop with piecewise-constant pressure and aperture.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.planar_slit_transient_hydraulic_history.v1", "default": "matintegrity.planar_slit_transient_hydraulic_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_state_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 100001, "minItems": 2, "type": "array"}` | s |
| `cell_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | m |
| `aperture_by_interval_m` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `pressure_drop_by_interval_Pa` | 예 | `{"items": {"type": "number"}, "maxItems": 100000, "minItems": 1, "type": "array"}` | Pa |
| `initial_volumetric_flow_m3_s` | 예 | `{"type": "number"}` | m³/s |
| `density_kg_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | kg/m³ |
| `dynamic_viscosity_Pa_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa·s |
| `resistance_correction_multiplier` | 아니오 | `{"default": 1.0, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `inertance_correction_multiplier` | 아니오 | `{"default": 1.0, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `hydraulic_parameter_fit_result_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `hydraulic_parameter_fit_evidence` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/Evidence"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `hydraulic_parameter_fit_applicability_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `minimum_width_to_aperture_ratio` | 아니오 | `{"default": 20.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 20.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_reviewed_reynolds_number` | 아니오 | `{"default": 1000.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_property_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_property_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_property_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_clock_and_grid_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_reference_sign_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incompressible_newtonian_property_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wide_slit_aspect_ratio_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `laminar_fully_developed_resistance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `unsteady_lumped_inertance_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `signed_flow_reversal_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PlanarSlitTransientHydraulicHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `volumetric_flow_history_m3_s[]` | `m^3/s` |
| `interval_results[].integrated_signed_volume_m3` | `m^3` |
| `interval_results[].end_cell_velocity_m_s[]` | `m/s` |
| `interval_results[].series_resistance_Pa_s_m3` | `Pa*s/m^3` |
| `interval_results[].series_inertance_Pa_s2_m3` | `Pa*s^2/m^3` |
| `interval_results[].maximum_reynolds_number` | `1` |
| `flow_reversal_events[].time_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Exact interval propagation for the caller-reviewed reduced balance I dQ/dt + R Q = pressure_drop with piecewise-constant pressure and aperture.
- Uses a quasi-steady fully developed laminar slit resistance and lumped incompressible fluid inertance; it is not a Navier–Stokes, compressible, roughness, entrance, or moving-boundary solver.

## 구현 근거·독립 설명

- `caller_lumped_slit_inertance_resistance`: Evaluate the caller-reviewed reduced planar-slit momentum law with the declared resistance and inertance correction factors; factors default to unity and non-unity values require exact fit-result Evidence and an applicability review.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.planar_slit_transient_hydraulic_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.planar_slit_transient_hydraulic_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-transient-slit-flow",
  "asset_id": "synthetic-crevice-loop",
  "location_id": "slit-segment-set-a",
  "physical_scope_id": "synthetic-slit-test-scope",
  "time_basis": "elapsed_seconds_from_declared_origin",
  "time_s": [
    0.0,
    0.1,
    0.2
  ],
  "cell_ids": [
    "slit-cell-1",
    "slit-cell-2"
  ],
  "cell_widths_m": [
    0.1,
    0.1
  ],
  "aperture_by_interval_m": [
    [
      0.001,
      0.001
    ],
    [
      0.001,
      0.0008
    ]
  ],
  "transverse_width_m": 0.03,
  "pressure_drop_by_interval_Pa": [
    1000.0,
    -500.0
  ],
  "initial_volumetric_flow_m3_s": 0.0,
  "density_kg_m3": 1000.0,
  "dynamic_viscosity_Pa_s": 0.001,
  "geometry_provider_id": "synthetic-geometry-record",
  "geometry_provider_revision": "1",
  "geometry_record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "pressure_provider_id": "synthetic-pressure-record",
  "pressure_provider_revision": "1",
  "pressure_record_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "fluid_property_provider_id": "synthetic-fluid-property-record",
  "fluid_property_provider_revision": "1",
  "fluid_property_record_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "evidence": [
    {
      "source_id": "synthetic-geometry-record",
      "origin": "synthetic",
      "citation": "Synthetic geometry fixture; not measured data.",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "source_id": "synthetic-pressure-record",
      "origin": "synthetic",
      "citation": "Synthetic signed pressure fixture; not measured data.",
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    },
    {
      "source_id": "synthetic-fluid-property-record",
      "origin": "synthetic",
      "citation": "Synthetic Newtonian fluid-property fixture; not measured data.",
      "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    }
  ],
  "usage_rights_evidence": [
    {
      "source_id": "project-synthetic-fixture",
      "origin": "synthetic",
      "citation": "Project-authored synthetic example payload.",
      "license_id": "CC0-1.0"
    }
  ],
  "usage_license_id": "CC0-1.0",
  "geometry_clock_and_grid_reviewed": true,
  "pressure_reference_sign_and_clock_reviewed": true,
  "incompressible_newtonian_property_support_reviewed": true,
  "wide_slit_aspect_ratio_reviewed": true,
  "laminar_fully_developed_resistance_reviewed": true,
  "unsteady_lumped_inertance_applicability_reviewed": true,
  "signed_flow_reversal_reviewed": true,
  "usage_rights_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/planar_slit_transient_hydraulic.py#L108)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
