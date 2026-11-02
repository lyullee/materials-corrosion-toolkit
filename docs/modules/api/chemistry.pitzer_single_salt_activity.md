# `chemistry.pitzer_single_salt_activity`

**목적:** One pure aqueous electrolyte with a caller-reviewed electroneutral formula, molality-scale Pitzer-Debye-Huckel Aphi/b, beta0/beta1/beta2 and Cphi parameters inside caller-declared temperature and ionic-strength support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.pitzer_single_salt_activity.v1", "default": "matintegrity.pitzer_single_salt_activity.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `salt_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `anion_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cation_charge_number` | 예 | `{"exclusiveMinimum": 0, "maximum": 8, "type": "integer"}` | 계약·필드 설명 참조 |
| `anion_charge_number` | 예 | `{"exclusiveMaximum": 0, "minimum": -8, "type": "integer"}` | 계약·필드 설명 참조 |
| `cation_stoichiometric_number` | 예 | `{"maximum": 16, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `anion_stoichiometric_number` | 예 | `{"maximum": 16, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `salt_molality_mol_kg_water` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `parameter_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `temperature_match_tolerance_K` | 아니오 | `{"default": 0.01, "maximum": 5, "minimum": 0, "type": "number"}` | K |
| `maximum_supported_ionic_strength_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `debye_huckel_A_phi` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `debye_huckel_b_sqrt_kg_mol` | 아니오 | `{"default": 1.2, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `beta_phi_0_kg_mol` | 예 | `{"type": "number"}` | kg/mol |
| `beta_phi_1_kg_mol` | 예 | `{"type": "number"}` | kg/mol |
| `beta_phi_2_kg_mol` | 아니오 | `{"default": 0.0, "type": "number"}` | kg/mol |
| `alpha_1_sqrt_kg_mol` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `alpha_2_sqrt_kg_mol` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `c_phi_kg2_mol2` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `parameter_set_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_and_parameter_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `single_pure_electrolyte_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stoichiometry_and_charge_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `parameter_values_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `parameter_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PitzerSingleSaltActivity.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `ionic_strength_mol_kg` | `mol/kg-water` |
| `mean_ionic_activity_coefficient` | `1` |
| `ln_mean_ionic_activity_coefficient` | `1` |
| `mean_ionic_activity_mol_kg_water` | `mol/kg-water` |
| `osmotic_coefficient` | `1` |
| `water_activity` | `1` |
| `debye_huckel_f_gamma` | `1` |
| `debye_huckel_f_phi` | `1` |
| `beta_gamma_kg_mol` | `kg/mol` |
| `beta_phi_kg_mol` | `kg/mol` |
| `c_gamma_kg2_mol2` | `(kg/mol)^2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One pure aqueous electrolyte with a caller-reviewed electroneutral formula, molality-scale Pitzer-Debye-Huckel Aphi/b, beta0/beta1/beta2 and Cphi parameters inside caller-declared temperature and ionic-strength support.
- No mixed-salt theta/psi interactions, single-ion activity convention, parameter fitting, phase equilibrium, kinetic law or corrosion inference is included.

## 구현 근거·독립 설명

- `caller_single_salt_pitzer_mean_activity`: Calculate Pitzer-Debye-Huckel plus caller beta0/beta1/beta2 and Cphi virial contributions to the mean ionic activity coefficient and osmotic coefficient for one electroneutral pure electrolyte. The caller supplies molality-scale coefficients, temperature/ionic-strength support and rights evidence. It assigns no individual-ion gamma convention and omits mixed-salt theta/psi interactions, fitting, phase equilibrium, corrosion kinetics and qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.pitzer_single_salt_activity"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.pitzer_single_salt_activity"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic",
  "salt_id": "XY",
  "cation_id": "X+",
  "anion_id": "Y-",
  "cation_charge_number": 1,
  "anion_charge_number": -1,
  "cation_stoichiometric_number": 1,
  "anion_stoichiometric_number": 1,
  "salt_molality_mol_kg_water": 0.1,
  "temperature_K": 298.15,
  "parameter_temperature_K": 298.15,
  "temperature_match_tolerance_K": 0.01,
  "maximum_supported_ionic_strength_mol_kg": 1,
  "debye_huckel_A_phi": 0.3,
  "debye_huckel_b_sqrt_kg_mol": 1.2,
  "beta_phi_0_kg_mol": 0.1,
  "beta_phi_1_kg_mol": 0.2,
  "beta_phi_2_kg_mol": 0,
  "alpha_1_sqrt_kg_mol": 2,
  "alpha_2_sqrt_kg_mol": 12,
  "c_phi_kg2_mol2": 0.001,
  "parameter_set_id": "synthetic-unfitted",
  "parameter_record_id": "demo",
  "parameter_record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "temperature_and_parameter_applicability_reviewed": true,
  "single_pure_electrolyte_scope_reviewed": true,
  "stoichiometry_and_charge_reviewed": true,
  "parameter_values_and_units_reviewed": true,
  "parameter_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-unfitted",
      "origin": "synthetic",
      "citation": "Invented coefficients",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pitzer_single_salt.py#L70)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
