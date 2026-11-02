# `chemistry.competitive_solid_equilibrium`

**목적:** Caller-declared competing neutral pure solids in one fixed-volume liquid with fixed activity coefficients; candidate phase list, stoichiometry and source-backed equilibrium constants are explicit.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `equilibrium_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `aqueous_species` | 예 | `{"items": {"$ref": "#/$defs/CompetitiveAqueousSpecies"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_solid_phases` | 예 | `{"items": {"$ref": "#/$defs/CompetitiveSolidPhase"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `standard_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `candidate_phase_set_completeness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_activity_coefficients_and_standard_states_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equilibrium_constant_temperature_and_computational_use_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `optimizer_maximum_iterations` | 아니오 | `{"default": 2000, "maximum": 20000, "minimum": 50, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_absolute_log_saturation_residual` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_extent_balance_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `relative_extent_balance_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CompetitiveSolidEquilibrium.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `final_aqueous_concentration_mol_m3` | `mol/m3` |
| `solid_phase_results` | `phase-wise mol/m3 and log saturation ratio` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-declared competing neutral pure solids in one fixed-volume liquid with fixed activity coefficients; candidate phase list, stoichiometry and source-backed equilibrium constants are explicit. No automated aqueous speciation or kinetic precipitation is inferred.

## 구현 근거·독립 설명

- `competitive_pure_solid_fixed_gamma_equilibrium`: Minimize the dimensionless ideal-mixing Gibbs potential for a closed fixed-volume aqueous species set and declared neutral solid phases with fixed activity coefficients. Extent constraints enforce aqueous nonnegativity and nonnegative final solid inventories; equilibrium is checked with phase saturation inequalities, complementarity residuals, and species extent balances.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.competitive_solid_equilibrium"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.competitive_solid_equilibrium"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "equilibrium_id": "synthetic-calcite-gypsum-competition",
  "aqueous_species": [
    {
      "species_id": "Ca2+",
      "initial_concentration_mol_m3": 20.0,
      "activity_reference_concentration_mol_m3": 1000.0,
      "activity_coefficient": 1.0,
      "charge_number": 2,
      "elemental_composition": {
        "Ca": 1
      }
    },
    {
      "species_id": "CO3--",
      "initial_concentration_mol_m3": 10.0,
      "activity_reference_concentration_mol_m3": 1000.0,
      "activity_coefficient": 1.0,
      "charge_number": -2,
      "elemental_composition": {
        "C": 1,
        "O": 3
      }
    },
    {
      "species_id": "SO4--",
      "initial_concentration_mol_m3": 5.0,
      "activity_reference_concentration_mol_m3": 1000.0,
      "activity_coefficient": 1.0,
      "charge_number": -2,
      "elemental_composition": {
        "S": 1,
        "O": 4
      }
    },
    {
      "species_id": "Cl-",
      "initial_concentration_mol_m3": 10.0,
      "activity_reference_concentration_mol_m3": 1000.0,
      "activity_coefficient": 1.0,
      "charge_number": -1,
      "elemental_composition": {
        "Cl": 1
      }
    }
  ],
  "candidate_solid_phases": [
    {
      "solid_species_id": "CaCO3(s)",
      "precipitation_stoichiometry": {
        "Ca2+": 1.0,
        "CO3--": 1.0
      },
      "solid_elemental_composition": {
        "Ca": 1,
        "C": 1,
        "O": 3
      },
      "initial_solid_moles_per_solution_volume_mol_m3": 0.0,
      "dimensionless_solubility_product": 1e-08,
      "equilibrium_constant_source_sha256": "1111111111111111111111111111111111111111111111111111111111111111"
    },
    {
      "solid_species_id": "CaSO4(s)",
      "precipitation_stoichiometry": {
        "Ca2+": 1.0,
        "SO4--": 1.0
      },
      "solid_elemental_composition": {
        "Ca": 1,
        "S": 1,
        "O": 4
      },
      "initial_solid_moles_per_solution_volume_mol_m3": 0.0,
      "dimensionless_solubility_product": 1e-05,
      "equilibrium_constant_source_sha256": "2222222222222222222222222222222222222222222222222222222222222222"
    }
  ],
  "temperature_K": 298.15,
  "standard_state_id": "synthetic-1-mol-per-liter",
  "candidate_phase_set_completeness_reviewed": true,
  "fixed_activity_coefficients_and_standard_states_reviewed": true,
  "equilibrium_constant_temperature_and_computational_use_reviewed": true,
  "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": true,
  "maximum_absolute_log_saturation_residual": 0.0001
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_numeric.py#L46)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
