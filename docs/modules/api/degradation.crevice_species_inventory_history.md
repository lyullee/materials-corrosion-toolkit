# `degradation.crevice_species_inventory_history`

**목적:** Geometry, volumes, species definitions, initial inventories and interval source rates are reviewed caller inputs.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bulk_solution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `crevice_solution_volume_m3` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `species` | 예 | `{"items": {"$ref": "#/$defs/CreviceSpecies"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rate_intervals` | 예 | `{"items": {"$ref": "#/$defs/CreviceSpeciesRateInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rate_supports` | 예 | `{"items": {"$ref": "#/$defs/CreviceRateSupport"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_and_volume_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_bulk_solution_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `species_definitions_and_initial_inventory_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_and_gap_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_provider_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `clock_and_interval_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `charge_balance_tolerance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceSpeciesInventoryHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `clock_id` | `1` |
| `elapsed_time_s` | `s` |
| `species_amount_history_mol` | `mol` |
| `species_concentration_history_mol_m3` | `mol/m^3` |
| `interval_amount_change_mol` | `mol` |
| `net_charge_inventory_mol_charge` | `mol-charge` |
| `maximum_absolute_charge_imbalance_mol_charge` | `mol-charge` |
| `caller_charge_imbalance_tolerance_mol_charge` | `mol-charge` |
| `charge_balance_within_caller_tolerance` | `1` |
| `interval_diagnostics` | `mixed` |
| `interval_rate_diagnostics` | `mixed` |
| `interval_rate_diagnostics_sha256` | `1` |
| `negative_inventory_records` | `1` |
| `nonfinite_inventory_records` | `1` |
| `nonfinite_concentration_records` | `1` |
| `nonfinite_charge_inventory_time_indices` | `1` |
| `initial_inventory_sha256` | `1` |
| `solution_volume_history_sha256` | `1` |
| `rate_interval_ledger_sha256` | `1` |
| `rate_support_ledger_sha256` | `1` |
| `condition_history` | `mixed` |
| `condition_history_sha256` | `1` |
| `condition_knot_history` | `mixed` |
| `condition_knot_history_sha256` | `1` |
| `condition_boundary_comparison_tolerances` | `mixed` |
| `inventory_lineage_sha256` | `1` |
| `cumulative_net_species_source_mol` | `mol` |
| `species_inventory_balance_residual_mol` | `mol` |
| `cumulative_source_overflow_species` | `1` |
| `interval_state_boundary_ledger` | `mixed` |
| `interval_state_boundary_ledger_sha256` | `1` |
| `completed_interval_count` | `1` |
| `completed_time_knot_count` | `1` |
| `completed_through_time_s` | `s` |
| `completed_species_amount_history_mol` | `mol` |
| `completed_prefix_sha256` | `1` |
| `failed_interval_id` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Geometry, volumes, species definitions, initial inventories and interval source rates are reviewed caller inputs.
- Rate-provider support matches exact material, bulk solution, species, temperature and gap identities.
- Net species source rates include every provider-selected transport and reaction term. Rates are constant unless a start/end pair and explicit linear interpolation review are provided; then trapezoidal integration is exact for the declared linear history.

## 구현 근거·독립 설명

- `external_crevice_species_rate_inventory_accounting`: Integrate externally supplied net species source rates over a reviewed crevice clock and prescribed solution-volume history, then expose species inventories, concentrations, negative inventory and charge-balance diagnostics within exact provider support. Do not generate activities, pH, electrochemical kinetics, precipitation, susceptibility, damage, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.crevice_species_inventory_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.crevice_species_inventory_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "authored-crevice",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "crevice-cell-1",
  "clock_id": "clock-1",
  "material_condition_id": "material-1",
  "bulk_solution_id": "solution-1",
  "elapsed_time_s": [
    0.0,
    10.0,
    30.0
  ],
  "crevice_solution_volume_m3": [
    1e-06,
    1e-06,
    2e-06
  ],
  "species": [
    {
      "species_id": "cation",
      "charge_number": 1,
      "initial_amount_mol": 0.001,
      "species_definition": "authored monovalent cation",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored species"
        }
      ]
    },
    {
      "species_id": "anion",
      "charge_number": -1,
      "initial_amount_mol": 0.001,
      "species_definition": "authored monovalent anion",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored species"
        }
      ]
    }
  ],
  "rate_intervals": [
    {
      "interval_id": "i-1",
      "support_id": "support-1",
      "temperature_K": 300.0,
      "gap_m": 0.0001,
      "end_temperature_K": 305.0,
      "end_gap_m": 9e-05,
      "linear_condition_interpolation_reviewed": true,
      "net_species_source_mol_s": {
        "cation": 1e-06,
        "anion": 1e-06
      },
      "net_species_source_end_mol_s": {
        "cation": 2e-06,
        "anion": 2e-06
      },
      "linear_rate_interpolation_reviewed": true,
      "provider_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored crevice rate"
        }
      ]
    },
    {
      "interval_id": "i-2",
      "support_id": "support-1",
      "temperature_K": 310.0,
      "gap_m": 0.0001,
      "boundary_condition_jump_reviewed": true,
      "net_species_source_mol_s": {
        "cation": 2e-06,
        "anion": 2e-06
      },
      "provider_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored crevice rate"
        }
      ]
    }
  ],
  "rate_supports": [
    {
      "support_id": "support-1",
      "material_condition_id": "material-1",
      "bulk_solution_id": "solution-1",
      "minimum_temperature_K": 290.0,
      "maximum_temperature_K": 320.0,
      "minimum_gap_m": 5e-05,
      "maximum_gap_m": 0.0002,
      "rate_provider_id": "provider-1",
      "rate_provider_version": "1",
      "rate_provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "supported_species_ids": [
        "cation",
        "anion"
      ],
      "maximum_absolute_charge_imbalance_mol_charge": 1e-12,
      "calibration_basis": "authored provider support",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored crevice support"
        }
      ]
    }
  ],
  "geometry_and_volume_history_reviewed": true,
  "material_and_bulk_solution_identity_reviewed": true,
  "species_definitions_and_initial_inventory_reviewed": true,
  "temperature_and_gap_history_reviewed": true,
  "rate_provider_and_calibration_reviewed": true,
  "clock_and_interval_alignment_reviewed": true,
  "charge_balance_tolerance_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored crevice history"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crevice_chemistry.py#L171)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
