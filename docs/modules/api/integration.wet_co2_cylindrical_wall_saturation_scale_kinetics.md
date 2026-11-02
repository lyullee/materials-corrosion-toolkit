# `integration.wet_co2_cylindrical_wall_saturation_scale_kinetics`

**목적:** Exact wall-adjacent cylindrical transport concentrations are paired with caller activity coefficients and a caller-supplied log10 Ksp at the same time and temperature knots.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics.v1", "default": "matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transport_request` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalTransientTransport"}` | 계약·필드 설명 참조 |
| `transport_request_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `wall_adjacent_cell_index` | 아니오 | `{"default": 0, "maximum": 199, "minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `candidate_solid_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solid_elemental_composition` | 예 | `{"additionalProperties": {"exclusiveMinimum": 0, "type": "number"}, "type": "object"}` | 계약·필드 설명 참조 |
| `activity_product_terms` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalActivityProductTerm"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `dissolution_stoichiometry_provider_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `dissolution_stoichiometry_provider_revision` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `dissolution_stoichiometry_source_record_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `dissolution_stoichiometry_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `dissolution_stoichiometry_evidence` | 예 | `{"$ref": "#/$defs/Evidence"}` | 계약·필드 설명 참조 |
| `phase_activity_history` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalPhaseActivityKnot"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetics_request` | 예 | `{"$ref": "#/$defs/CallerSurfaceScaleKinetics"}` | 계약·필드 설명 참조 |
| `linear_saturation_path_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `interval_temperature_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `cylindrical_wall_state_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2CylindricalWallSaturationScaleKinetics.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `saturation_history[].time_s` | `s` |
| `saturation_history[].temperature_K` | `K` |
| `saturation_history[].wall_adjacent_cell_concentration_mol_m3_by_species.*` | `mol/m^3` |
| `saturation_history[].saturation_ratio` | `1` |
| `surface_scale_kinetics.values.scale_history[].scale_thickness_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Exact wall-adjacent cylindrical transport concentrations are paired with caller activity coefficients and a caller-supplied log10 Ksp at the same time and temperature knots.
- The activity product is calculated using molarity standard state and a caller-declared neutral solid dissolution formula.
- A caller-calibrated single-phase scale inventory model receives the exact knot saturation ratios; no coefficient is inferred.
- No automatic speciation, phase selection, scale-to-transport feedback or corrosion qualification is performed.

## 구현 근거·독립 설명

- `caller_cylindrical_wall_activity_product_to_scale_kinetics`: Caller-defined activity product and saturation mapping from exact cylindrical wall-adjacent states to a caller scale law.
- `caller_cylindrical_transient_species_history_for_wall_saturation`: Caller-paired transient cylindrical wall-adjacent concentration history at exact chemistry knots.
- `caller_surface_scale_kinetics`: Caller-calibrated single-phase scale kinetic law; no phase discovery or parameter fitting is performed by the bridge.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_cylindrical_wall_saturation_scale_kinetics"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'scipy': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_cylindrical_wall_saturation_scale_kinetics.py#L200)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
