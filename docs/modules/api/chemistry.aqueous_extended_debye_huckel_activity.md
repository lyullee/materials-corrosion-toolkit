# `chemistry.aqueous_extended_debye_huckel_activity`

**목적:** All Debye-Huckel A/B coefficients, ionic-strength support, and charged-species ion-size parameters are caller supplied and Evidence-bound.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `ionic_strength_limit_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `debye_huckel_A_at_temperature` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `debye_huckel_B_at_temperature` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `parameter_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/ExtendedDebyeHuckelSpecies"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `charge_balance_absolute_tolerance_mol_kg` | 예 | `{"minimum": 0, "type": "number"}` | mol/kg |
| `complete_ionic_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `charge_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ionic_strength_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `extended_debye_huckel_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `parameter_temperature_solvent_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExtendedDebyeHuckelActivityInput.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `ionic_strength_mol_kg` | `mol/kg` |
| `charge_balance_residual_mol_kg` | `mol/kg` |
| `activity_coefficient` | `1` |
| `dimensionless_activity` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- All Debye-Huckel A/B coefficients, ionic-strength support, and charged-species ion-size parameters are caller supplied and Evidence-bound.
- The result is a single-ion extended Debye-Huckel approximation within explicit reviewed temperature, solvent, ionic-strength and activity standard-state support.
- Neutral species use unit activity coefficient with no salting correction; this model does not infer CO2 solubility, phase equilibrium or corrosion kinetics.

## 구현 근거·독립 설명

- `caller_extended_debye_huckel_activity_parameters`: Compute ion activity coefficients from the extended Debye-Hückel equation using caller-supplied, evidence-pinned solvent constants, ion-size parameters, charges and temperature support. No database parameters are embedded; outside declared ionic-strength/temperature support the evaluator fails closed. This activity provider is not a complete aqueous speciation or corrosion model.
- [USGS PHREEQC Version 3 documentation: extended Debye-Hückel activity model](https://water.usgs.gov/water-resources/software/PHREEQC/Phreeqc_3_2013_manual.pdf) · `usgs_phreeqc_extended_debye_huckel_method`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.aqueous_extended_debye_huckel_activity"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/extended_debye_huckel_activity.py#L81)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
