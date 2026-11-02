# `chemistry.carbonate_alkalinity_speciation`

**목적:** Aqueous carbonate-only alkalinity balance with caller activity-based K1, K2, Kw and activity coefficients.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `sample_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `ph_activity` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `measured_total_alkalinity_mol_L` | 예 | `{"type": "number"}` | 계약·필드 설명 참조 |
| `expanded_total_alkalinity_uncertainty_mol_L` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `alkalinity_uncertainty_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `closure_absolute_tolerance_mol_L` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `constants_temperature_tolerance_K` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | K |
| `constants` | 예 | `{"$ref": "#/$defs/CarbonateActivityConstants"}` | 계약·필드 설명 참조 |
| `measurement_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `carbonate_only_alkalinity_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ph_activity_scale_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `equilibrium_constants_activity_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_coefficients_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_standard_state_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `aqueous_co2_star_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_provider_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `alkalinity_measurement_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `numerical_closure_tolerance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CarbonateAlkalinitySpeciation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `activity_standard_state` | `1` |
| `activity_standard_state_reviewed` | `1` |
| `ph_activity` | `1` |
| `measured_total_alkalinity_mol_L` | `mol/L` |
| `expanded_total_alkalinity_uncertainty_mol_L` | `mol/L` |
| `hydrogen_activity` | `1` |
| `hydrogen_concentration_mol_L` | `mol/L` |
| `hydroxide_concentration_mol_L` | `mol/L` |
| `carbonate_to_bicarbonate_ratio` | `1` |
| `bicarbonate_concentration_mol_L` | `mol/L` |
| `carbonate_concentration_mol_L` | `mol/L` |
| `bicarbonate_activity` | `1` |
| `aqueous_co2_star_concentration_mol_L` | `mol/L` |
| `bicarbonate_expanded_uncertainty_mol_L` | `mol/L` |
| `carbonate_expanded_uncertainty_mol_L` | `mol/L` |
| `aqueous_co2_star_expanded_uncertainty_mol_L` | `mol/L` |
| `reconstructed_total_alkalinity_mol_L` | `mol/L` |
| `alkalinity_closure_residual_mol_L` | `mol/L` |
| `gas_liquid_equilibrium_evaluated` | `1` |
| `gas_pressure_evaluated` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Aqueous carbonate-only alkalinity balance with caller activity-based K1, K2, Kw and activity coefficients.
- The activity standard state is fixed to 1 mol/L and requires explicit caller review; molality-standard coefficients are not directly accepted.
- No additional alkalinity species, gas-liquid equilibrium, gas pressure, corrosion rate, life, or acceptance is included.

## 구현 근거·독립 설명

- [USGS advanced carbonate and bicarbonate speciation method](https://water.usgs.gov/water-resources/memos/memo.php?id=2098) · `usgs_advanced_carbonate_speciation`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.carbonate_alkalinity_speciation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.carbonate_alkalinity_speciation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "sample-location-1",
  "sample_id": "sample-1",
  "temperature_K": 298.15,
  "ph_activity": 8.3,
  "measured_total_alkalinity_mol_L": 0.002,
  "expanded_total_alkalinity_uncertainty_mol_L": 2e-05,
  "alkalinity_uncertainty_basis": "synthetic expanded uncertainty",
  "closure_absolute_tolerance_mol_L": 1e-14,
  "constants_temperature_tolerance_K": 0.0,
  "constants": {
    "activity_standard_state": "molarity_1_mol_L",
    "temperature_K": 298.15,
    "K1_activity": 5.011872336272725e-07,
    "K2_activity": 5.011872336272715e-11,
    "Kw_activity": 1e-14,
    "gamma_h_plus": 0.9,
    "gamma_hco3_minus": 0.85,
    "gamma_co3_double_minus": 0.7,
    "gamma_oh_minus": 0.9,
    "constants_provider_id": "synthetic-provider",
    "constants_provider_revision": "revision-1",
    "constants_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "constants_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "evidence": [
      {
        "source_id": "synthetic-carbonate-case",
        "origin": "synthetic",
        "citation": "independently authored synthetic carbonate-only balance",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "measurement_provider_id": "synthetic-laboratory",
  "measurement_provider_revision": "revision-1",
  "measurement_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "measurement_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "carbonate_only_alkalinity_basis_reviewed": true,
  "ph_activity_scale_reviewed": true,
  "equilibrium_constants_activity_basis_reviewed": true,
  "activity_coefficients_reviewed": true,
  "activity_standard_state_reviewed": true,
  "aqueous_co2_star_definition_reviewed": true,
  "temperature_and_provider_lineage_reviewed": true,
  "alkalinity_measurement_units_and_uncertainty_reviewed": true,
  "numerical_closure_tolerance_reviewed": true,
  "evidence": [
    {
      "source_id": "synthetic-carbonate-case",
      "origin": "synthetic",
      "citation": "independently authored synthetic carbonate-only balance",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/carbonate_alkalinity.py#L95)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
