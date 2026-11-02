# `corrosion.crevice_solid_volume_rate`

**목적:** Positive phase molar rate denotes precipitation and negative rate denotes dissolution.

**모델 버전:** `0.1.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_solid_volume_rate.v1", "default": "matintegrity.crevice_solid_volume_rate.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"type": "number"}` | s |
| `cell_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_ids_by_cell` | 예 | `{"items": {"items": {"type": "string"}, "type": "array"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_molar_rate_mol_s_by_cell` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_molar_volume_m3_mol_by_cell` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_occupies_gap_by_cell` | 예 | `{"items": {"items": {"type": "boolean"}, "type": "array"}, "maxItems": 300, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `geometry_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetic_rate_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_rate_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceSolidVolumeRateRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `phase_molar_rate_mol_s_by_cell[][]` | `mol/s` |
| `phase_molar_volume_m3_mol_by_cell[][]` | `m^3/mol` |
| `solid_volume_rate_m3_s_by_cell[]` | `m^3/s` |
| `liquid_volume_rate_m3_s_by_cell[]` | `m^3/s` |
| `volume_rate_closure_residual_m3_s_by_cell[]` | `m^3/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Positive phase molar rate denotes precipitation and negative rate denotes dissolution.
- Only phases explicitly marked as gap occupying contribute to solid volume change; the liquid volume rate is the equal-and-opposite signed result.
- Phase rate and molar-volume geometry maps are separately digest bound by licensed Evidence; this conversion does not qualify the rates or the molar volumes.
- The output is a stage quantity and does not integrate a coupled chemistry, solid, hydraulic or moving-boundary system.

## 구현 근거·독립 설명

- `caller_evidenced_crevice_phase_molar_volume_gap_occupancy_map`: Consume a caller-evidenced ordered cell/phase map of solid molar volumes and explicit gap-occupancy flags. This map supplies geometric conversion factors only; phase identity, thermodynamic stability and property qualification remain caller responsibilities.
- `caller_evidenced_crevice_cell_phase_molar_rate_stage`: Consume signed caller-evidenced solid molar rates at one exact physical-scope clock stage, preserving ordered cell and phase identities. Positive values denote formation and negative values dissolution; the adapter does not calibrate or qualify a kinetic law.
- `composed_crevice_stage_geometry_and_phase_volume_rate`: Bind a caller-authorized composite license record to the exact digest of a hydraulic stage geometry and phase-derived liquid-volume rates. The record authorizes only the declared composition and makes no claim that source licenses transfer automatically.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.crevice_solid_volume_rate"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_solid_volume_rate.py#L96)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
