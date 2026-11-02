# `chemistry.layered_scale_diffusion_limit`

**목적:** Caller-supplied layered effective diffusivity, partition coefficients, thickness, concentration endpoints and covered-area fraction define a steady diffusion-limit bound.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.layered_scale_diffusion_limit.v1", "default": "matintegrity.layered_scale_diffusion_limit.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scale_phase_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scale_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transported_species_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_area_basis_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `condition_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `transport_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `scale_history_result_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `scale_history_time_s` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `scale_history_model_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `scale_history_phase_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `scale_history_layer_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `scale_history_covered_area_fraction` | 아니오 | `{"anyOf": [{"maximum": 1.0, "minimum": 0.0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `scale_history_mapping_reviewed` | 아니오 | `{"anyOf": [{"type": "boolean"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `bulk_concentration_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `interface_concentration_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `bare_film_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `bare_diffusivity_m2_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m²/s |
| `covered_area_fraction` | 예 | `{"maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `layers` | 예 | `{"items": {"$ref": "#/$defs/ScaleTransportLayer"}, "maxItems": 20, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `electron_equivalents_per_mole` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `concentration_basis_and_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `effective_diffusivity_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `area_coverage_and_uniform_parallel_path_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `electron_equivalent_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LayeredScaleDiffusionLimit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `driving_concentration_difference_mol_m3` | `mol/m3` |
| `bare_film_resistance_s_m` | `s/m` |
| `scale_layer_resistances_s_m[]` | `s/m` |
| `covered_path_resistance_s_m` | `s/m` |
| `bare_area_flux_limit_mol_m2_s` | `mol/m2/s` |
| `covered_area_flux_limit_mol_m2_s` | `mol/m2/s` |
| `area_average_flux_limit_mol_m2_s` | `mol/m2/s` |
| `area_average_diffusion_limited_current_density_A_m2` | `A/m2` |
| `flux_limit_reduction_fraction_vs_bare_film` | `1` |
| `covered_area_fraction` | `1` |
| `scale_history_covered_area_fraction` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied layered effective diffusivity, partition coefficients, thickness, concentration endpoints and covered-area fraction define a steady diffusion-limit bound.
- The result is not a Butler-Volmer or corrosion-rate solution and does not infer scale formation, morphology, adhesion or protection from scale thickness.

## 구현 근거·독립 설명

- `caller_layered_scale_diffusion_limit`: Calculate steady series diffusion resistance across caller-defined scale layers and a bare solution film, then mix covered and uncovered patch fluxes in parallel using a caller-reviewed area fraction. Convert transported-species flux to its electron-equivalent Faraday current bound. Preserve species, condition, layer order and provider digests. This does not determine layer morphology or coverage, solve charge balance or electrode kinetics, infer a corrosion current or claim an actual protection factor.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.layered_scale_diffusion_limit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.layered_scale_diffusion_limit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.layered_scale_diffusion_limit.v1",
  "assessment_id": "synthetic-layered-scale-limit",
  "physical_scope_id": "synthetic-one-interface",
  "substrate_condition_id": "synthetic-steel-condition",
  "solution_condition_id": "synthetic-aqueous-state",
  "scale_state_id": "synthetic-two-layer-state",
  "transported_species_id": "oxygen",
  "provider_id": "example://scale-transport-parameters",
  "provider_revision": "synthetic-1",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "condition_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "transport_configuration_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "bulk_concentration_mol_m3": 0.25,
  "interface_concentration_mol_m3": 0.0,
  "bare_film_thickness_m": 0.0001,
  "bare_diffusivity_m2_s": 2e-09,
  "covered_area_fraction": 0.85,
  "layers": [
    {
      "layer_id": "inner-porous",
      "thickness_m": 2e-06,
      "effective_diffusivity_m2_s": 2e-10,
      "solution_to_layer_partition_coefficient": 0.8
    },
    {
      "layer_id": "outer-dense",
      "thickness_m": 1e-06,
      "effective_diffusivity_m2_s": 1e-11,
      "solution_to_layer_partition_coefficient": 0.5
    }
  ],
  "electron_equivalents_per_mole": 4.0,
  "concentration_basis_and_partition_reviewed": true,
  "effective_diffusivity_support_reviewed": true,
  "area_coverage_and_uniform_parallel_path_reviewed": true,
  "electron_equivalent_mapping_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-layered-scale-transport-fixture",
      "origin": "synthetic",
      "citation": "Project-authored numerical fixture; not material test data"
    }
  ],
  "scale_phase_id": "synthetic-carbonate-phase"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/scale_film_transport.py#L107)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
