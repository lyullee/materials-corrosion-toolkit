# `corrosion.coupled_wall_metal_loss`

**목적:** Signed integrated lateral-wall species flux is converted with reviewed metal stoichiometry, physical reference area, reactive wall area, molar mass and density; no local thinning map or acceptance is inferred.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `coupled_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `coupled_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `selection` | 예 | `{"$ref": "#/$defs/WallMetalLossSelection"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CoupledWallMetalLossRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `wall_metal_loss.elapsed_time_s` | `s` |
| `wall_metal_loss.reactive_wall_area_m2` | `m2` |
| `wall_metal_loss.reactive_wall_area_over_reference_area` | `1` |
| `wall_metal_loss.history.net_metal_amount_per_reference_area_mol_m2` | `mol/m2` |
| `wall_metal_loss.history.net_metal_amount_mol` | `mol` |
| `wall_metal_loss.history.net_mass_loss_kg` | `kg` |
| `wall_metal_loss.history.net_volume_change_m3` | `m3` |
| `wall_metal_loss.history.signed_area_average_recession_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Signed integrated lateral-wall species flux is converted with reviewed metal stoichiometry, physical reference area, reactive wall area, molar mass and density; no local thinning map or acceptance is inferred.

## 구현 근거·독립 설명

- `explicit_coupled_wall_metal_loss`: Map a coupled transport result's signed, integrated lateral-wall metal-species ledger to total molar/mass/volume change and area-average recession using a caller-reviewed physical reference area, reactive wall area, species stoichiometry, molar mass and density. Bind the full coupled result digest and retain source amount per reference area. Positive uptake denotes loss, negative uptake denotes redeposition. This is a whole-selected-area volume balance, not a local thinning field, corrosion-rate qualification, capacity or acceptance result.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.coupled_wall_metal_loss"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.coupled_wall_metal_loss"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "coupled_result": {
    "status": "computed",
    "transport_result": {
      "status": "computed",
      "species_ids": [
        "Fe_2plus",
        "H_plus"
      ],
      "elapsed_time_s": [
        0.0,
        3600.0
      ],
      "reference_cross_section_m2": 0.01,
      "wall_area_over_reference_area": 2.0,
      "cumulative_wall_inward_mol_m2": [
        [
          0.0,
          0.0
        ],
        [
          1e-05,
          0.0
        ]
      ]
    }
  },
  "coupled_result_sha256": "b5c65a1c2c5a07ab35d653c81839a975028e2635359e93980e6b641e67db7722",
  "selection": {
    "selection_id": "synthetic-wall-mapping",
    "metal_species_id": "Fe_2plus",
    "metal_molar_mass_kg_mol": 0.055845,
    "metal_density_kg_m3": 7800.0,
    "reference_cross_section_m2": 0.01,
    "boundary_species_is_one_metal_atom_per_mole_reviewed": true,
    "wall_flux_is_signed_dissolution_or_redeposition_reviewed": true,
    "reactive_wall_and_reference_areas_reviewed": true,
    "area_average_recession_interpretation_reviewed": true
  }
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/dissolution_numeric.py#L9)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
