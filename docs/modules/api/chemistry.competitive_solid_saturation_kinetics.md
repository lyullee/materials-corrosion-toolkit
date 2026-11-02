# `chemistry.competitive_solid_saturation_kinetics`

**목적:** Map caller-reviewed interval saturation ratios to per-phase precipitation or dissolution power-law rates, then apply the existing elemental/charge-conserving solid inventory limiter.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `kinetic_parameter_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `aqueous_species` | 예 | `{"items": {"$ref": "#/$defs/KineticAqueousSpecies"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_solid_phases` | 예 | `{"items": {"$ref": "#/$defs/KineticSolidPhase"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_rate_laws` | 예 | `{"items": {"$ref": "#/$defs/SolidSaturationRateLaw"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/CompetingSolidSaturationInterval"}, "maxItems": 5000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_balance_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `relative_balance_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `phase_stoichiometry_and_solution_volume_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `saturation_ratio_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_rate_law_units_temperature_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `dissolution_then_precipitation_split_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CompetingSolidSaturationKinetics.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `intervals[].start_time_s` | `s` |
| `intervals[].end_time_s` | `s` |
| `intervals[].saturation_ratio_by_phase` | `1` |
| `phase_rate_laws[].rate_constant_reference_temperature_K` | `K` |
| `phase_rate_laws[].minimum_valid_temperature_K` | `K` |
| `phase_rate_laws[].maximum_valid_temperature_K` | `K` |
| `phase_rate_laws[].precipitation_activation_energy_J_mol` | `J/mol` |
| `phase_rate_laws[].dissolution_activation_energy_J_mol` | `J/mol` |
| `derived_rate_history[].phase_rate_diagnostics[].rate_law_temperature_K` | `K` |
| `derived_rate_history[].phase_rate_diagnostics[].effective_precipitation_rate_constant_mol_m3_s` | `mol/m3/s` |
| `derived_rate_history[].phase_rate_diagnostics[].effective_dissolution_rate_constant_mol_m3_s` | `mol/m3/s` |
| `derived_rate_history[].phase_rate_diagnostics[].signed_extent_rate_mol_m3_s` | `mol/m3/s` |
| `kinetic_ledger.history[].solid_inventory_mol_m3` | `mol/m3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Map caller-reviewed interval saturation ratios to per-phase precipitation or dissolution power-law rates, then apply the existing elemental/charge-conserving solid inventory limiter.
- Saturation ratios, phase identity, rate coefficients, reaction orders, units, temperature range and applicability remain caller supplied; chemistry and equilibrium are not inferred.

## 구현 근거·독립 설명

- `caller_competing_solid_saturation_rate_law`: Use a caller-supplied dimensionless saturation ratio per declared neutral solid phase and interval to select a phase-specific precipitation power law above unity or dissolution power law below unity, then pass the signed extent rates into a conservative phase/aqueous inventory ledger. Coefficients, orders, standard state, temperature support, reaction network and qualification are user supplied. No saturation calculation, activity model, phase discovery, nucleation, or physical performance is inferred.
- `arrhenius_kinetics`: Rate ratio for a single supplied activation energy between two absolute temperatures.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.competitive_solid_saturation_kinetics"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["chemistry.competitive_solid_saturation_kinetics"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-competing-solid-saturation-kinetics",
  "physical_scope_id": "synthetic-closed-batch",
  "provider_id": "example://declared-saturation-history",
  "provider_revision": "synthetic-v1",
  "kinetic_configuration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "temperature_K": 298.15,
  "kinetic_parameter_source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "aqueous_species": [
    {
      "species_id": "X2+",
      "charge_number": 2,
      "elemental_composition": {
        "X": 1
      },
      "source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "initial_concentration_mol_m3": 2.0
    },
    {
      "species_id": "Y2-",
      "charge_number": -2,
      "elemental_composition": {
        "Y": 1
      },
      "source_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "initial_concentration_mol_m3": 2.0
    }
  ],
  "candidate_solid_phases": [
    {
      "solid_species_id": "XY(s)",
      "precipitation_stoichiometry": {
        "X2+": 1.0,
        "Y2-": 1.0
      },
      "solid_elemental_composition": {
        "X": 1,
        "Y": 1
      },
      "source_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "initial_solid_moles_per_solution_volume_mol_m3": 0.0
    },
    {
      "solid_species_id": "X2Y2(s)",
      "precipitation_stoichiometry": {
        "X2+": 2.0,
        "Y2-": 2.0
      },
      "solid_elemental_composition": {
        "X": 2,
        "Y": 2
      },
      "source_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "initial_solid_moles_per_solution_volume_mol_m3": 0.0
    }
  ],
  "phase_rate_laws": [
    {
      "solid_species_id": "XY(s)",
      "precipitation_rate_constant_mol_m3_s": 0.02,
      "precipitation_order": 1.0,
      "dissolution_rate_constant_mol_m3_s": 0.01,
      "dissolution_order": 1.0,
      "source_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "rate_constant_reference_temperature_K": 298.15,
      "precipitation_activation_energy_J_mol": 12000.0,
      "dissolution_activation_energy_J_mol": 18000.0,
      "arrhenius_parameter_applicability_reviewed": true,
      "minimum_valid_temperature_K": 273.15,
      "maximum_valid_temperature_K": 373.15
    },
    {
      "solid_species_id": "X2Y2(s)",
      "precipitation_rate_constant_mol_m3_s": 0.01,
      "precipitation_order": 1.5,
      "dissolution_rate_constant_mol_m3_s": 0.005,
      "dissolution_order": 1.0,
      "source_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "rate_constant_reference_temperature_K": 298.15,
      "precipitation_activation_energy_J_mol": 14000.0,
      "dissolution_activation_energy_J_mol": 20000.0,
      "arrhenius_parameter_applicability_reviewed": true,
      "minimum_valid_temperature_K": 273.15,
      "maximum_valid_temperature_K": 373.15
    }
  ],
  "intervals": [
    {
      "interval_id": "segment-1",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "saturation_ratio_by_phase": {
        "XY(s)": 1.5,
        "X2Y2(s)": 0.8
      },
      "temperature_K": 305.15
    },
    {
      "interval_id": "segment-2",
      "start_time_s": 10.0,
      "end_time_s": 20.0,
      "saturation_ratio_by_phase": {
        "XY(s)": 1.0,
        "X2Y2(s)": 1.2
      },
      "temperature_K": 330.15
    }
  ],
  "absolute_balance_tolerance_mol_m3": 1e-10,
  "relative_balance_tolerance": 1e-09,
  "phase_stoichiometry_and_solution_volume_reviewed": true,
  "saturation_ratio_and_standard_state_reviewed": true,
  "caller_rate_law_units_temperature_and_support_reviewed": true,
  "dissolution_then_precipitation_split_order_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/multiphase_kinetic_ledger.py#L311)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
