# `chemistry.aqueous_saturation_screen`

**목적:** Caller-supplied dimensionless aqueous activities, activity standard state, candidate-solid activity products, and temperature-applicable solubility products.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.aqueous_saturation_screen.v1", "default": "matintegrity.aqueous_saturation_screen.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `activity_standard_state` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/SaturationScreenSpecies"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_solids` | 예 | `{"items": {"$ref": "#/$defs/CandidateSolid"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `activity_state_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `solubility_data_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solubility_data_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `complete_species_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `compatible_standard_states_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equilibrium_constants_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_interval_bounds_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | Caller confirms that nonzero activity interval bounds have reviewed source, interpretation, units and applicability. |
| `solubility_product_interval_bounds_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | Caller confirms that nonzero solubility-product interval bounds have reviewed source, interpretation and temperature applicability. |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AqueousSaturationScreen.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `candidate_results.log10_ion_activity_product` | `1` |
| `candidate_results.log10_saturation_ratio` | `1` |
| `candidate_results.log10_saturation_absolute_bound` | `1` |
| `candidate_results.log10_saturation_ratio_lower_bound` | `1` |
| `candidate_results.log10_saturation_ratio_upper_bound` | `1` |
| `candidate_results.saturation_ratio` | `1` |
| `candidate_count` | `1` |
| `phase_selection_performed` | `1` |
| `precipitated_amount_predicted` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied dimensionless aqueous activities, activity standard state, candidate-solid activity products, and temperature-applicable solubility products.
- Reports separate saturation indices only; it does not select phases, solve precipitation extent, infer kinetics, or predict corrosion.

## 구현 근거·독립 설명

- `caller_aqueous_candidate_saturation_screen`: For each explicitly declared candidate solid, calculate the logarithmic ion-activity product from caller-supplied dimensionless aqueous activities and positive exponents, then subtract the caller-supplied temperature-applicable log10 solubility product. Require a row-level solubility record ID and a matching Evidence source ID per candidate, and carry citation, license and checksum into each result. A Python composition adapter accepts computed fixed-gamma, Davies, B-dot, or tabulated-activity aqueous Calculation results or registered AssessmentResults, checks supported model identity for the latter, carries the complete upstream digest plus activity provider/record lineage, and rejects noncomputed or untraceable states. It also accepts a digest-pinned candidate-network speciation AssessmentResult by verifying wrapper input digest, embedded workflow result and input digests, assembled mass-action system digest, and nested speciation result digest before forwarding its activity state and retaining workflow/system/speciation lineage. It accepts a registered exact-knot B-dot history only with an explicit knot index, verifies full assessment/input/history/knot/request/result and parameter-record digests, and preserves selected time, temperature and parameter lineage in the saturation result. Callers may add absolute log10 activity bounds keyed by the exact upstream species ID set; partial or extra mappings return needs_data rather than silently dropping bounds. Propagate caller-supplied absolute log10 bounds for species activities and each solubility product by conservative interval arithmetic, reporting lower/upper saturation-index bounds and whether the interval lies wholly below, wholly above, or overlaps saturation. Nonzero activity and solubility bounds require separate caller review flags; otherwise the calculation returns needs_data without an interval classification. These deterministic intervals are not probabilities or confidence bounds. Return ordered candidate results with activity-state and solubility-data digests. The time-history adapter additionally requires an exact computed van't Hoff history digest, aligned Ksp records at every knot, matching candidate definitions and explicit per-record temperature support; it does not interpolate between knots. Do not choose stable phases, solve competing-solid mass balance, infer precipitation amount or kinetics, or predict corrosion.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_saturation_screen"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.aqueous_saturation_screen"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic",
  "solution_id": "synthetic",
  "temperature_K": 298.15,
  "activity_standard_state": "dimensionless 1 mol/L",
  "species": [
    {
      "species_id": "X+",
      "dimensionless_activity": 0.1
    },
    {
      "species_id": "Y-",
      "dimensionless_activity": 0.1
    }
  ],
  "candidate_solids": [
    {
      "solid_id": "XY(s)",
      "log10_solubility_product": -2,
      "solubility_record_id": "synthetic",
      "solubility_evidence_source_id": "synthetic",
      "terms": [
        {
          "species_id": "X+",
          "stoichiometric_exponent": 1
        },
        {
          "species_id": "Y-",
          "stoichiometric_exponent": 1
        }
      ]
    }
  ],
  "activity_state_provider_id": "synthetic",
  "activity_state_digest": "1111111111111111111111111111111111111111111111111111111111111111",
  "solubility_data_provider_id": "synthetic",
  "solubility_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
  "complete_species_inventory_reviewed": true,
  "compatible_standard_states_reviewed": true,
  "equilibrium_constants_temperature_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic",
      "origin": "synthetic",
      "citation": "Invented example values"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/aqueous_saturation_screening.py#L133)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
