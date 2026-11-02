# `fatigue.propose_critical_plane_interval_overlap_pairing`

**목적:** Deterministic continuous-capacity bipartite min-cost max-flow proposal over overlapping sample-index intervals; maximize paired cycle count, then allocated-count-weighted interval IoU.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `projected_rainflow_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `projected_rainflow_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `plane_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `shear_projection` | 예 | `{"pattern": "^(engineering_shear_strain_directional_component\|engineering_shear_strain_vector_magnitude)$", "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_interval_iou` | 아니오 | `{"default": 0.0, "maximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `method_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `same_ordered_sample_clock_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_cycle_pair_work` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_flow_augmentations` | 아니오 | `{"default": 100000, "maximum": 1000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneIntervalOverlapPairing.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `pairings[].allocated_cycle_count` | `cycle` |
| `pairings[].interval_intersection_over_union` | `1` |
| `normal_unallocated_cycle_count` | `cycle` |
| `shear_unallocated_cycle_count` | `cycle` |
| `normal_cycle_count` | `cycle` |
| `shear_cycle_count` | `cycle` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Deterministic continuous-capacity bipartite min-cost max-flow proposal over overlapping sample-index intervals; maximize paired cycle count, then allocated-count-weighted interval IoU.
- The proposed map is not a physical pairing law; caller review and explicit unallocated-cycle treatment are required before a calibrated damage calculation.

## 구현 근거·독립 설명

- `critical_plane_interval_overlap_pairing_proposal`: Read two independently rainflow-counted scalar channels from one digest-pinned projected result and propose allocations only where normal-stress and shear-strain cycle sample-index intervals overlap. A deterministic continuous-capacity bipartite min-cost max-flow first maximizes total paired cycle equivalent, then maximizes allocated-count-weighted interval IoU; stable source order resolves equal-cost paths. Return unallocated counts and exact lineage. The optimization is a temporal-overlap proxy, not a validated physical pairing law, and the proposal must be reviewed before calibrated damage evaluation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.propose_critical_plane_interval_overlap_pairing"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.propose_critical_plane_interval_overlap_pairing"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "projected_rainflow_result": {
    "status": "computed",
    "values": {
      "history_id": "synthetic-local-tensor-history",
      "material_condition_id": "synthetic-material-condition",
      "projection_cycle_results": [
        {
          "plane_id": "synthetic-plane-1",
          "projections": {
            "normal_stress": {
              "quantity_unit": "Pa",
              "projection_interpretation": "signed_normal_stress",
              "cycles": [
                {
                  "range": 120000000.0,
                  "mean": 15000000.0,
                  "count": 1.0,
                  "start_index": 0,
                  "end_index": 4,
                  "start_sample_id": "s0",
                  "end_sample_id": "s4"
                },
                {
                  "range": 80000000.0,
                  "mean": 5000000.0,
                  "count": 0.5,
                  "start_index": 5,
                  "end_index": 8,
                  "start_sample_id": "s5",
                  "end_sample_id": "s8"
                }
              ]
            },
            "engineering_shear_strain_directional_component": {
              "quantity_unit": "1",
              "projection_interpretation": "signed_engineering_shear_component_along_supplied_in_plane_direction",
              "cycles": [
                {
                  "range": 0.0012,
                  "mean": 0.0001,
                  "count": 1.0,
                  "start_index": 2,
                  "end_index": 5,
                  "start_sample_id": "s2",
                  "end_sample_id": "s5"
                },
                {
                  "range": 0.0008,
                  "mean": 0.0,
                  "count": 0.5,
                  "start_index": 6,
                  "end_index": 8,
                  "start_sample_id": "s6",
                  "end_sample_id": "s8"
                }
              ]
            }
          }
        }
      ],
      "sample_count": 9
    }
  },
  "projected_rainflow_result_sha256": "a945e77ccfe3667a77e2f232485d5202fe103146785fd02acd36abfb53b3d0d1",
  "plane_id": "synthetic-plane-1",
  "shear_projection": "engineering_shear_strain_directional_component",
  "minimum_interval_iou": 0.1,
  "method_revision": "project-method-1",
  "configuration_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "same_ordered_sample_clock_reviewed": true,
  "maximum_cycle_pair_work": 2000000
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/sequence_numeric.py#L105)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
