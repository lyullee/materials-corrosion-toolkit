# `welding.hydrogen_bakeout_slab`

**목적:** One-dimensional finite planar diffusion screening with an initially uniform diffusible-hydrogen field, zero concentration on both reviewed exposed faces and caller-supplied effective diffusivity history.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `diffusivity_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `thickness_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 4096, "minItems": 2, "type": "array"}` | s |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 4096, "minItems": 2, "type": "array"}` | K |
| `effective_diffusivity_m2_s` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 4096, "minItems": 2, "type": "array"}` | m²/s |
| `slab_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `initial_diffusible_hydrogen_atoms_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `both_faces_exposed_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `uniform_initial_concentration_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `diffusion_limited_surface_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `diffusivity_history_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_history_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `series_absolute_tolerance` | 아니오 | `{"default": 1e-10, "maximum": 0.0001, "minimum": 1e-14, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_series_terms` | 아니오 | `{"default": 200000, "maximum": 1000000, "minimum": 10, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenBakeoutSlab.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `temperature_K` | `K` |
| `diffusion_time_m2` | `m^2` |
| `fourier_number` | `1` |
| `remaining_diffusible_fraction` | `1` |
| `released_diffusible_fraction` | `1` |
| `mean_diffusible_hydrogen_atoms_mol_m3` | `mol/m^3` |
| `cumulative_released_hydrogen_atoms_mol_m2` | `mol/m^2` |
| `series_tail_bound` | `1` |
| `series_terms_used` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One-dimensional finite planar diffusion screening with an initially uniform diffusible-hydrogen field, zero concentration on both reviewed exposed faces and caller-supplied effective diffusivity history.

## 구현 근거·독립 설명

- [NIST finite-slab diffusion-limited hydrogen outgassing model and characteristic time](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=924339) · `nist_hydrogen_outgassing`
- `hydrogen_bakeout_slab_derivation`: Transform the one-dimensional diffusion equation with spatially uniform time-dependent effective diffusivity by the cumulative diffusion time integral. For a finite slab with initially uniform diffusible concentration and zero concentration on both faces, evaluate the odd eigenfunction series for the volume-mean remaining fraction. Integrate caller-supplied piecewise-linear diffusivity exactly by the trapezoid rule at declared time knots and bound the omitted positive series tail. Preserve temperature as procedure evidence rather than generating hidden material properties. Do not infer diffusivity, traps, weld heterogeneity, surface kinetics, hydrogen cracking, procedure qualification or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.hydrogen_bakeout_slab"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.hydrogen_bakeout_slab"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "procedure_id": "authored-bakeout-example",
  "material_condition_id": "authored-steel-condition",
  "diffusivity_source_id": "authored-effective-diffusivity",
  "thickness_source_id": "authored-release-path",
  "elapsed_time_s": [
    0.0,
    1800.0,
    3600.0
  ],
  "temperature_K": [
    423.15,
    473.15,
    473.15
  ],
  "effective_diffusivity_m2_s": [
    2e-09,
    8e-09,
    8e-09
  ],
  "slab_thickness_m": 0.012,
  "initial_diffusible_hydrogen_atoms_mol_m3": 50.0,
  "both_faces_exposed_reviewed": true,
  "uniform_initial_concentration_reviewed": true,
  "diffusion_limited_surface_reviewed": true,
  "diffusivity_history_reviewed": true,
  "temperature_history_reviewed": true,
  "series_absolute_tolerance": 1e-10,
  "maximum_series_terms": 200000
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding.py#L67)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
