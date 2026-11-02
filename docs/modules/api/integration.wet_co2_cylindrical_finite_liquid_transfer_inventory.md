# `integration.wet_co2_cylindrical_finite_liquid_transfer_inventory`

**목적:** The transfer exposure result supplies a whole-segment conductance on the cylindrical wetted-area basis.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_cylindrical_finite_liquid_transfer_inventory.v1", "default": "matintegrity.wet_co2_cylindrical_finite_liquid_transfer_inventory.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `species_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `hydraulics_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `transfer_capacity_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `concentration_history` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalLiquidConcentrationKnot"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `external_exchange_history` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalExternalLiquidExchange"}, "maxItems": 4999, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_inventory_tolerance_mol` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_inventory_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2CylindricalFiniteLiquidTransferInventory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history[].bulk_concentration_mol_m3` | `mol/m^3` |
| `history[].wall_concentration_mol_m3` | `mol/m^3` |
| `history[].segment_transfer_conductance_m3_s` | `m^3/s` |
| `history[].signed_bulk_to_wall_transfer_rate_mol_s` | `mol/s` |
| `history[].left_held_interval_transfer_mol` | `mol` |
| `history[].bulk_inventory_mol` | `mol` |
| `history[].wall_inventory_mol` | `mol` |
| `history[].inventory_closure_residual_mol` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The transfer exposure result supplies a whole-segment conductance on the cylindrical wetted-area basis.
- One well-mixed bulk reservoir and one well-mixed wall-liquid reservoir are tracked for a single declared species.
- Exact-knot caller concentrations, liquid volumes, and external inventory changes close the finite two-reservoir balance.

## 구현 근거·독립 설명

- `caller_cylindrical_liquid_transfer_capacity_history`: Require the exact digest-pinned cylindrical wall-to-bulk transfer-capacity result and preserve its species, interval, geometry and hydraulics lineage.
- `caller_cylindrical_geometry_history`: Use the exact caller-provided cylindrical geometry knots as the time and wetted-area basis; no corrosion or deposition geometry is inferred.
- `caller_cylindrical_hydraulics_history`: Require the exact digest-pinned single-phase hydraulic knots used by the upstream transfer-capacity result.
- `caller_bulk_wall_liquid_concentration_records`: Caller supplies digest-pinned bulk and wall compartment concentrations and finite liquid volumes at every aligned knot, with licensed evidence.
- `caller_bulk_wall_external_inventory_exchange_records`: Caller supplies signed licensed external species inventory changes per interval for each liquid compartment; no gas/liquid reaction source is inferred.
- `finite_two_compartment_liquid_transfer_balance`: Convert an upstream per-segment transfer conductance and caller bulk-wall concentration difference into left-held signed molar exchange between finite liquid compartments, add explicit external inventory increments, and fail closed when either compartment inventory becomes negative or the closure residual exceeds tolerance. This is bookkeeping, not a mass-transfer or reaction model.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_cylindrical_finite_liquid_transfer_inventory"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_cylindrical_finite_liquid_transfer_inventory.py#L133)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
