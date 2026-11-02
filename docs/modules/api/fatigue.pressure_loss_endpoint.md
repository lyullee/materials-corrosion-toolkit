# `fatigue.pressure_loss_endpoint`

**목적:** The caller supplies a reviewed pressure-drop threshold, event origin, physical-specimen continuity, load-case identity and valid-cycle accounting; the calculator does not infer them from a pressure trace.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `segments` | 예 | `{"items": {"$ref": "#/$defs/FatigueLoadingSegment"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_pressure_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `observed_pressure_drop_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `declared_drop_fraction_threshold` | 예 | `{"exclusiveMinimum": 0.0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `event_origin` | 예 | `{"enum": ["none", "specimen", "pressure_system", "instrumentation", "unresolved"], "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_event_kind` | 예 | `{"enum": ["none", "through_wall_crack", "rupture", "other"], "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_pressure_loss_confirmed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `same_physical_specimen_across_segments_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `loading_history_reconstructable` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `runout_limit_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `observation_window_closed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PressureLossFatigueEndpoint.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cumulative_valid_cycles` | `cycle` |
| `pressure_drop_fraction` | `1` |
| `declared_threshold_fraction` | `1` |
| `pressure_drop_margin_Pa` | `Pa` |
| `cycles_at_confirmed_endpoint` | `cycle` |
| `segment_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies a reviewed pressure-drop threshold, event origin, physical-specimen continuity, load-case identity and valid-cycle accounting; the calculator does not infer them from a pressure trace.
- Runout requires a closed observation window and the declared cycle limit without a confirmed specimen endpoint; interruption and unresolved history remain distinct.

## 구현 근거·독립 설명

- [FABEST HCF Competition participant package version 2.1.2](https://doi.org/10.5281/zenodo.23532147) · `fabest_hcf_protocol_v2_1_2`
- `cumulative_loading_segments`: public_method_reference

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.pressure_loss_endpoint"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.pressure_loss_endpoint"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "segments": [
    {
      "segment_id": "segment-1",
      "physical_specimen_id": "synthetic-specimen-1",
      "load_case_id": "synthetic-load-case-1",
      "valid_loading_cycles": 1200000.0,
      "cycle_count_basis": "segment_local_counter"
    },
    {
      "segment_id": "segment-2",
      "physical_specimen_id": "synthetic-specimen-1",
      "load_case_id": "synthetic-load-case-1",
      "valid_loading_cycles": 800000.0,
      "cycle_count_basis": "provider_cumulative_difference"
    }
  ],
  "initial_pressure_Pa": 60000000.0,
  "observed_pressure_drop_Pa": 0.0,
  "declared_drop_fraction_threshold": 0.1,
  "event_origin": "none",
  "specimen_event_kind": "none",
  "specimen_pressure_loss_confirmed": false,
  "same_physical_specimen_across_segments_declared": true,
  "loading_history_reconstructable": true,
  "runout_limit_cycles": 2000000.0,
  "observation_window_closed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L277)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
