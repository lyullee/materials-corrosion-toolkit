# `integration.wet_co2_elemental_phase_handoff`

**목적:** Only an already-computed source result payload with matching digest and exact species/phase formula mappings is consumed.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_assessment_result` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/AssessmentResult"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_assessment_result_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `source_values` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `cell_solution_volume_m3` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `components` | 예 | `{"items": {"$ref": "#/$defs/ElementalComponent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/Evidence"}, "type": "array"}` | 계약·필드 설명 참조 |
| `formulas_and_cell_volume_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_species_and_phase_id_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCO2PhaseHistoryHandoff.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s[]` | `s` |
| `element_inventory[].aqueous_inventory_mol[]` | `mol` |
| `element_inventory[].solid_inventory_mol[]` | `mol` |
| `element_inventory[].combined_inventory_mol[]` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only an already-computed source result payload with matching digest and exact species/phase formula mappings is consumed.
- Caller-provided cell solution volumes and formulas are required; boundary flux closure, omitted pools, reaction extents and kinetics are not inferred.

## 구현 근거·독립 설명

- `caller_declared_wet_co2_elemental_phase_history_handoff`: Apply caller-declared elemental formula counts and cell solution volumes to already-computed aqueous and solid concentration histories; preserve source lineage and do not infer reaction extents, omitted pools, flux closure, kinetics or chemistry.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_elemental_phase_handoff"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.wet_co2_elemental_phase_handoff"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "campaign_id": "synthetic-phase",
  "source_provider_id": "synthetic-provider",
  "source_provider_revision": "1",
  "asset_id": "synthetic-asset",
  "location_id": "synthetic-cell",
  "time_basis": "elapsed_seconds",
  "source_result_digest": "8fa9074ef1666183ad95ad097d2137dc5aafef5d1e1153cd7552fb8305cd0c9c",
  "source_values": {
    "status": "computed",
    "species_ids": [
      "H2O"
    ],
    "solid_species_ids": [],
    "concentration_after_phase_mol_m3": [
      [
        [
          1000.0
        ]
      ]
    ],
    "solid_moles_per_solution_volume_mol_m3": [
      [
        []
      ]
    ],
    "elapsed_time_s": [
      0
    ]
  },
  "cell_solution_volume_m3": [
    1e-06
  ],
  "components": [
    {
      "component_id": "H2O",
      "phase": "aqueous_species",
      "atom_counts": {
        "H": 2,
        "O": 1
      }
    }
  ],
  "evidence": [
    {
      "source_id": "synthetic-provider",
      "origin": "synthetic",
      "citation": "Synthetic handoff fixture",
      "sha256": "8fa9074ef1666183ad95ad097d2137dc5aafef5d1e1153cd7552fb8305cd0c9c"
    }
  ],
  "formulas_and_cell_volume_basis_reviewed": true,
  "provider_species_and_phase_id_mapping_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/wet_co2_elemental_phase_handoff.py#L88)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
