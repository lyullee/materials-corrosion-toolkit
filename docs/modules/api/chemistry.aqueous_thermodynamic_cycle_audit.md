# `chemistry.aqueous_thermodynamic_cycle_audit`

**목적:** All species formulas, charges, activity standard state, temperature and equilibrium-constant records are caller supplied and explicitly reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_thermodynamic_cycle_audit.v1", "default": "matintegrity.aqueous_thermodynamic_cycle_audit.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `audit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `activity_standard_state` | 예 | `{"enum": ["molarity_1_mol_L", "molality_1_mol_kg_water", "dimensionless"], "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/AqueousCycleSpecies"}, "maxItems": 100, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `reactions` | 예 | `{"items": {"$ref": "#/$defs/AqueousCycleReaction"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `stoichiometric_balance_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "maximum": 0.0001, "type": "number"}` | 계약·필드 설명 참조 |
| `rank_relative_tolerance` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `cycle_closure_tolerance_log10` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `complete_species_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `elemental_formula_and_stoichiometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equilibrium_constant_conditions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `numerical_rank_and_cycle_tolerance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence_and_usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousThermodynamicCycleAudit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `reaction_balance[].charge_balance_residual` | `1` |
| `reaction_cycle_basis[].log10_equilibrium_cycle_residual` | `1` |
| `cycle_closure_residual_l2_log10` | `1` |
| `cycle_closure_tolerance_log10` | `1` |
| `rank_threshold` | `1` |
| `singular_values` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- All species formulas, charges, activity standard state, temperature and equilibrium-constant records are caller supplied and explicitly reviewed.
- The reaction-cycle basis is derived from the declared stoichiometric matrix; numerical rank and log10(K) closure tolerance are caller-reviewed.
- This API checks balance and algebraic cycle consistency only; it does not discover species/phases, solve speciation, infer missing constants or qualify corrosion.

## 구현 근거·독립 설명

- `aqueous_reaction_cycle_nullspace_consistency`: Construct the caller-declared species-by-reaction stoichiometric matrix after checking elemental and charge balance. An orthonormal right-null-space basis identifies linear reaction cycles; equilibrium constants are algebraically consistent on that declared cycle space when the L2 norm of the basis projection of log10(K) is within a caller-reviewed tolerance. Numerical rank tolerance and the supplied species, reactions and conditions remain caller responsibilities. No reaction or phase discovery, speciation solve, or parameter qualification is performed.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_thermodynamic_cycle_audit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_thermodynamic_cycle_audit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.aqueous_thermodynamic_cycle_audit.v1",
  "audit_id": "synthetic-water-ionization-cycle",
  "temperature_K": 298.15,
  "activity_standard_state": "molarity_1_mol_L",
  "parameter_provider_id": "synthetic-water-equilibrium-records",
  "parameter_provider_revision": "synthetic-1",
  "species": [
    {
      "species_id": "h2o",
      "charge_number": 0,
      "elemental_composition": {
        "H": 2,
        "O": 1
      }
    },
    {
      "species_id": "h_plus",
      "charge_number": 1,
      "elemental_composition": {
        "H": 1
      }
    },
    {
      "species_id": "oh_minus",
      "charge_number": -1,
      "elemental_composition": {
        "H": 1,
        "O": 1
      }
    }
  ],
  "reactions": [
    {
      "reaction_id": "water-ionization-forward",
      "log10_equilibrium_constant": -14.0,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 1.0
        },
        {
          "species_id": "oh_minus",
          "coefficient": 1.0
        },
        {
          "species_id": "h2o",
          "coefficient": -1.0
        }
      ],
      "evidence_source_id": "synthetic-cycle-fixture",
      "source_record_id": "water-forward",
      "evidence_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "reaction_id": "water-ionization-reverse",
      "log10_equilibrium_constant": 14.0,
      "terms": [
        {
          "species_id": "h2o",
          "coefficient": 1.0
        },
        {
          "species_id": "h_plus",
          "coefficient": -1.0
        },
        {
          "species_id": "oh_minus",
          "coefficient": -1.0
        }
      ],
      "evidence_source_id": "synthetic-cycle-fixture",
      "source_record_id": "water-reverse",
      "evidence_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "reaction_id": "water-ionization-scaled",
      "log10_equilibrium_constant": -28.0,
      "terms": [
        {
          "species_id": "h_plus",
          "coefficient": 2.0
        },
        {
          "species_id": "oh_minus",
          "coefficient": 2.0
        },
        {
          "species_id": "h2o",
          "coefficient": -2.0
        }
      ],
      "evidence_source_id": "synthetic-cycle-fixture",
      "source_record_id": "water-scaled",
      "evidence_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "evidence": [
    {
      "source_id": "synthetic-cycle-fixture",
      "origin": "synthetic",
      "citation": "Project-authored algebra-only cycle-audit wiring fixture",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "stoichiometric_balance_tolerance": 1e-10,
  "rank_relative_tolerance": 1e-12,
  "cycle_closure_tolerance_log10": 1e-08,
  "complete_species_inventory_reviewed": true,
  "elemental_formula_and_stoichiometry_reviewed": true,
  "equilibrium_constant_conditions_reviewed": true,
  "numerical_rank_and_cycle_tolerance_reviewed": true,
  "evidence_and_usage_rights_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_thermodynamic_cycle_audit.py#L99)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
