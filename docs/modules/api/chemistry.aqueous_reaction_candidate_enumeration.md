# `chemistry.aqueous_reaction_candidate_enumeration`

**목적:** Complete caller-supplied formulas and ionic charges define a bounded integer search; candidates satisfy atom and charge conservation within the declared species set and total order.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `enumeration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/AqueousReactionCandidateSpecies"}, "maxItems": 12, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_total_stoichiometric_order` | 아니오 | `{"default": 4, "maximum": 8, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_side_multisets` | 아니오 | `{"default": 250000, "maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_candidate_pair_checks` | 아니오 | `{"default": 250000, "maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_candidate_reactions` | 아니오 | `{"default": 50000, "maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `species_formula_and_charge_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `closed_candidate_species_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `candidate_use_and_manual_selection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousReactionCandidateEnumeration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `candidate_reaction_count` | `1` |
| `enumerated_side_multiset_count` | `1` |
| `candidate_reactions[].charge_stoichiometric_residual` | `charge-equivalent stoichiometry` |
| `candidate_reactions[].coefficient` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Complete caller-supplied formulas and ionic charges define a bounded integer search; candidates satisfy atom and charge conservation within the declared species set and total order.
- Enumeration is a stoichiometric screen only. It does not identify feasible chemistry, phase, reaction direction, equilibrium constants, rate laws, completeness, or corrosion behavior; candidates require independent selection and qualification.

## 구현 근거·독립 설명

- `caller_element_charge_balanced_aqueous_reaction_candidate_enumeration`: Enumerate primitive integer stoichiometric candidates from a caller-declared closed species list, complete elemental formulas and ionic charges within explicit total-order, side-multiset, candidate-pair and output budgets. Candidates conserve the supplied atom counts and charge; deterministic digest-derived candidate IDs, review gates and input digest are retained. This is a bounded balance screen, not chemical reaction discovery, phase selection, equilibrium-constant assignment, kinetics, network completeness or corrosion prediction.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_reaction_candidate_enumeration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_reaction_candidate_enumeration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "enumeration_id": "synthetic-water-ionization-candidates",
  "species": [
    {
      "species_id": "water",
      "charge_number": 0,
      "elemental_composition": {
        "H": 2,
        "O": 1
      }
    },
    {
      "species_id": "proton",
      "charge_number": 1,
      "elemental_composition": {
        "H": 1
      }
    },
    {
      "species_id": "hydroxide",
      "charge_number": -1,
      "elemental_composition": {
        "H": 1,
        "O": 1
      }
    },
    {
      "species_id": "hydronium",
      "charge_number": 1,
      "elemental_composition": {
        "H": 3,
        "O": 1
      }
    }
  ],
  "maximum_total_stoichiometric_order": 4,
  "maximum_side_multisets": 250000,
  "maximum_candidate_pair_checks": 250000,
  "maximum_candidate_reactions": 50000,
  "species_formula_and_charge_reviewed": true,
  "closed_candidate_species_inventory_reviewed": true,
  "candidate_use_and_manual_selection_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic_reaction_candidate_example",
      "origin": "synthetic",
      "citation": "Invented species used only to demonstrate API wiring"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_mass_action.py#L616)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
