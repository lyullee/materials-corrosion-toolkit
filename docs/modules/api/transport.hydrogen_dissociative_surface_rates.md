# `transport.hydrogen_dissociative_surface_rates`

**목적:** Reviewed hydrogen fugacity, or explicitly reviewed ideal-gas partial-pressure approximation, and two effective Arrhenius surface-capacity laws over declared temperature and gas-driver support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `boundary_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_lattice_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `hydrogen_species_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `gas_state_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_origin_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 4096, "minItems": 2, "type": "array"}` | s |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | K |
| `hydrogen_gas_driver_Pa` | 예 | `{"items": {"minimum": 0, "type": "number"}, "type": "array"}` | Pa |
| `gas_driver_kind` | 예 | `{"enum": ["fugacity", "ideal_gas_partial_pressure_approximation"], "type": "string"}` | 계약·필드 설명 참조 |
| `reference_fugacity_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `supported_temperature_K` | 예 | `{"maxItems": 2, "minItems": 2, "prefixItems": [{"exclusiveMinimum": 0, "type": "number"}, {"exclusiveMinimum": 0, "type": "number"}], "type": "array"}` | K |
| `supported_hydrogen_gas_driver_Pa` | 예 | `{"maxItems": 2, "minItems": 2, "prefixItems": [{"minimum": 0, "type": "number"}, {"exclusiveMinimum": 0, "type": "number"}], "type": "array"}` | Pa |
| `absorption` | 예 | `{"$ref": "#/$defs/ThermallyActivatedSurfaceFlux"}` | 계약·필드 설명 참조 |
| `desorption` | 예 | `{"$ref": "#/$defs/ThermallyActivatedSurfaceFlux"}` | 계약·필드 설명 참조 |
| `temperature_history_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `gas_driver_history_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_parameterizations_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `lattice_surface_state_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `ideal_gas_approximation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenDissociativeSurfaceRates.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `temperature_K` | `K` |
| `hydrogen_gas_driver_Pa` | `Pa` |
| `absorption_capacity_flux_mol_m2_s` | `mol/(m^2*s)` |
| `desorption_capacity_flux_mol_m2_s` | `mol/(m^2*s)` |
| `log_absorption_capacity_flux_mol_m2_s` | `ln(numerical flux in mol/(m^2*s))` |
| `log_desorption_capacity_flux_mol_m2_s` | `ln(numerical flux in mol/(m^2*s))` |
| `zero_net_surface_occupancy` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reviewed hydrogen fugacity, or explicitly reviewed ideal-gas partial-pressure approximation, and two effective Arrhenius surface-capacity laws over declared temperature and gas-driver support.

## 구현 근거·독립 설명

- `hydrogen_reduced_surface_reaction_derivation`: At each reviewed temperature knot, evaluate separate Arrhenius limiting absorption and desorption atom-molar flux capacities in log space. Multiply the absorption capacity by the square root of caller-supplied hydrogen fugacity divided by a declared reference fugacity, or use hydrogen partial pressure only after an explicit ideal-gas approximation review. Define the reduced net inward surface flux as J_abs times one minus lattice-surface occupancy minus J_des times lattice-surface occupancy. Algebraically eliminate the surface occupancy against the adjacent half-cell Fickian resistance, preserving signed flux and total atom inventory. This effective one-state boundary is not a full adsorption microkinetic model, a bulk solubility relation or a parameter inference method.
- [IUPAC Gold Book definition of fugacity](https://doi.org/10.1351/goldbook.F02543) · `iupac_fugacity_definition`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.hydrogen_dissociative_surface_rates"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["transport.hydrogen_dissociative_surface_rates"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "boundary_id": "synthetic-gas-face",
  "material_condition_id": "synthetic-state",
  "reference_lattice_id": "synthetic-sites",
  "surface_condition_id": "synthetic-clean-face",
  "hydrogen_species_id": "H2",
  "gas_state_provider_id": "synthetic-reviewed-fugacity",
  "elapsed_time_origin_id": "synthetic-exposure-start",
  "elapsed_time_s": [
    0.0,
    5.0,
    10.0
  ],
  "temperature_K": [
    300.0,
    400.0,
    500.0
  ],
  "hydrogen_gas_driver_Pa": [
    100000.0,
    225000.0,
    400000.0
  ],
  "gas_driver_kind": "fugacity",
  "reference_fugacity_Pa": 100000.0,
  "supported_temperature_K": [
    280.0,
    520.0
  ],
  "supported_hydrogen_gas_driver_Pa": [
    0.0,
    500000.0
  ],
  "absorption": {
    "rate_id": "synthetic-absorption",
    "pre_exponential_capacity_flux_mol_m2_s": 0.001,
    "activation_energy_J_mol": 5000.0,
    "evidence": [
      {
        "source_id": "authored-synthetic",
        "origin": "synthetic",
        "citation": "Authored reduced surface-reaction demonstration",
        "license_id": "MIT"
      }
    ]
  },
  "desorption": {
    "rate_id": "synthetic-desorption",
    "pre_exponential_capacity_flux_mol_m2_s": 0.0002,
    "activation_energy_J_mol": 7000.0,
    "evidence": [
      {
        "source_id": "authored-synthetic",
        "origin": "synthetic",
        "citation": "Authored reduced surface-reaction demonstration",
        "license_id": "MIT"
      }
    ]
  },
  "temperature_history_reviewed": true,
  "gas_driver_history_reviewed": true,
  "surface_parameterizations_reviewed": true,
  "lattice_surface_state_mapping_reviewed": true,
  "ideal_gas_approximation_reviewed": false
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_surface.py#L76)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
