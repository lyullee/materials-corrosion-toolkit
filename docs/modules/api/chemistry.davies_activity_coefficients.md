# `chemistry.davies_activity_coefficients`

**목적:** Ionic strength is calculated from the caller-reviewed complete molal species inventory; electroneutrality is checked against an explicit tolerance.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `ionic_strength_limit_mol_kg` | 예 | `{"exclusiveMinimum": 0, "maximum": 0.5, "type": "number"}` | mol/kg |
| `davies_A_at_temperature` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `A_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `A_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `A_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `A_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `charge_balance_absolute_tolerance_mol_kg` | 예 | `{"minimum": 0, "type": "number"}` | mol/kg |
| `species` | 예 | `{"items": {"$ref": "#/$defs/DaviesActivitySpecies"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `complete_ionic_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `charge_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ionic_strength_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `davies_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_solvent_A_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/DaviesActivityCoefficientInput.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `ionic_strength_mol_kg` | `mol/kg` |
| `charge_balance_residual_mol_kg` | `mol/kg` |
| `activity_standard_state` | `1` |
| `species.activity_coefficient` | `1` |
| `species.dimensionless_activity` | `1` |
| `species.log10_activity_coefficient` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Ionic strength is calculated from the caller-reviewed complete molal species inventory; electroneutrality is checked against an explicit tolerance.
- Davies A is a caller-supplied, evidenced value for the declared temperature and solvent; the declared applicability ceiling cannot exceed 0.5 mol/kg water.
- Neutral-species gamma is unity by convention; no salting-out, concentrated-brine correction, gas equilibrium, or corrosion-rate inference is included.

## 구현 근거·독립 설명

- [USGS PHREEQC 3 documentation: Davies activity-coefficient model](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm) · `usgs_phreeqc_davies_activity_coefficients`
- [USGS WSP 2254: Davies approximation for aqueous activity coefficients](https://pubs.usgs.gov/wsp/wsp2254/pdf/wsp2254a.pdf) · `usgs_davies_ionic_strength_approximation`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.davies_activity_coefficients"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.davies_activity_coefficients"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "davies-example",
  "solution_id": "synthetic-dilute-electrolyte",
  "temperature_K": 298.15,
  "ionic_strength_limit_mol_kg": 0.5,
  "davies_A_at_temperature": 0.5,
  "A_provider_id": "caller-aqueous-property-table",
  "A_provider_revision": "synthetic-1",
  "A_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "A_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "charge_balance_absolute_tolerance_mol_kg": 1e-12,
  "species": [
    {
      "species_id": "na",
      "species_label": "Na+",
      "charge_number": 1,
      "molality_mol_kg": 0.1
    },
    {
      "species_id": "cl",
      "species_label": "Cl-",
      "charge_number": -1,
      "molality_mol_kg": 0.1
    },
    {
      "species_id": "co2-star",
      "species_label": "CO2*",
      "charge_number": 0,
      "molality_mol_kg": 0.02
    }
  ],
  "complete_ionic_inventory_reviewed": true,
  "charge_balance_reviewed": true,
  "ionic_strength_convention_reviewed": true,
  "davies_scope_reviewed": true,
  "temperature_solvent_A_lineage_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic-davies-example",
      "origin": "synthetic",
      "citation": "Illustrative caller-supplied electrolyte fixture"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/davies_activity.py#L50)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
