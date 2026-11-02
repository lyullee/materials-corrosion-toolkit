# `mechanics.through_wall_thermal_stress`

**목적:** Linear-elastic plane-section thermal stress under explicit resultants or explicit membrane strain and curvature.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.through_wall_thermal_stress.v1", "default": "matintegrity.through_wall_thermal_stress.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `profile_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `position_m` | 예 | `{"items": {"type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | m |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | K |
| `temperature_source_result_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_model_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_model_version` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_time_index` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "integer"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_time_s` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `temperature_source_time_basis_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_asset_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_source_location_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `temperature_to_section_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `secant_thermal_expansion_1_K` | 예 | `{"items": {"type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | K |
| `elastic_modulus_Pa` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | Pa |
| `poisson_ratio` | 예 | `{"items": {"exclusiveMaximum": 0.5, "exclusiveMinimum": -1.0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `elastic_limit_Pa` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | Pa |
| `property_profile_evidence` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ThermalStressPropertyEvidence"}, "type": "array"}` | 계약·필드 설명 참조 |
| `plane_condition` | 예 | `{"enum": ["uniaxial_plane_stress", "equi_biaxial_plane_stress"], "type": "string"}` | 계약·필드 설명 참조 |
| `control` | 예 | `{"enum": ["resultant_controlled", "kinematic_controlled"], "type": "string"}` | 계약·필드 설명 참조 |
| `membrane_force_N_m` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | N·m |
| `bending_moment_N` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | N |
| `midplane_total_strain` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `curvature_1_m` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | m |
| `plane_sections_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `linear_elastic_response_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `property_profiles_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applied_resultants_or_kinematics_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThroughWallThermalStress.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `section_midpoint_m` | `m` |
| `free_thermal_strain` | `1` |
| `midplane_total_strain` | `1` |
| `curvature_1_m` | `1/m` |
| `stress_Pa` | `Pa` |
| `membrane_force_N_m` | `N/m` |
| `bending_moment_N` | `N` |
| `membrane_force_residual_N_m` | `N/m` |
| `bending_moment_residual_N` | `N` |
| `elastic_limit_utilization_at_profile_points` | `1` |
| `maximum_evaluated_elastic_limit_utilization` | `1` |
| `maximum_evaluated_tensile_stress_Pa` | `Pa` |
| `minimum_evaluated_compressive_stress_Pa` | `Pa` |
| `section_quadrature_order` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Linear-elastic plane-section thermal stress under explicit resultants or explicit membrane strain and curvature.

## 구현 근거·독립 설명

- `thermoelastic_section_resultants`: Independently integrate a piecewise-linear through-wall temperature and caller-supplied elastic-property profile under a plane-section assumption. Either solve membrane strain and curvature from declared force and moment resultants or evaluate declared kinematics. Retain one-direction versus equi-biaxial plane-stress modulus, elastic-limit screening and force/moment residuals. Do not infer pressure, discontinuity, plasticity, creep, fracture or code stress classification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "mechanics.through_wall_thermal_stress"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["mechanics.through_wall_thermal_stress"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.through_wall_thermal_stress.v1",
  "profile_id": "authored-through-wall-profile",
  "position_m": [
    0.00125,
    0.00375,
    0.00625,
    0.00875
  ],
  "temperature_K": [
    390.0,
    360.0,
    330.0,
    310.0
  ],
  "reference_temperature_K": 300.0,
  "secant_thermal_expansion_1_K": [
    1e-05,
    1e-05,
    1e-05,
    1e-05
  ],
  "elastic_modulus_Pa": [
    200000000000.0,
    200000000000.0,
    200000000000.0,
    200000000000.0
  ],
  "poisson_ratio": [
    0.3,
    0.3,
    0.3,
    0.3
  ],
  "elastic_limit_Pa": [
    250000000.0,
    250000000.0,
    250000000.0,
    250000000.0
  ],
  "plane_condition": "uniaxial_plane_stress",
  "control": "resultant_controlled",
  "membrane_force_N_m": 0.0,
  "bending_moment_N": 0.0,
  "midplane_total_strain": null,
  "curvature_1_m": null,
  "plane_sections_reviewed": true,
  "linear_elastic_response_reviewed": true,
  "property_profiles_reviewed": true,
  "applied_resultants_or_kinematics_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_transient.py#L960)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
