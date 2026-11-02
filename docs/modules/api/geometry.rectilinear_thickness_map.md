# `geometry.rectilinear_thickness_map`

**목적:** Cell edges define a rectilinear map in metres and matrix entries are cell-centred thicknesses in metres.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `x_cell_edges_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `y_cell_edges_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `cell_thickness_m` | 예 | `{"items": {"items": {"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}]}, "type": "array"}, "minItems": 1, "type": "array"}` | m |
| `reference_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `reporting_threshold_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `threshold_comparison` | 예 | `{"enum": ["less_than", "less_than_or_equal"], "type": "string"}` | 계약·필드 설명 참조 |
| `connectivity` | 아니오 | `{"default": "four_neighbour", "enum": ["four_neighbour", "eight_neighbour"], "type": "string"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/RectilinearThicknessMap.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `minimum_observed_thickness_m` | `m` |
| `maximum_observed_thickness_m` | `m` |
| `area_weighted_mean_observed_thickness_m` | `m` |
| `total_map_area_m2` | `m^2` |
| `observed_area_m2` | `m^2` |
| `missing_area_m2` | `m^2` |
| `observed_area_fraction` | `1` |
| `net_observed_loss_volume_m3` | `m^3` |
| `threshold_cell_area_m2` | `m^2` |
| `connected_threshold_component_areas_m2` | `m^2` |
| `connected_threshold_component_count` | `count` |
| `connectivity` | `1` |
| `threshold_comparison` | `1` |
| `interpolation_performed` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Cell edges define a rectilinear map in metres and matrix entries are cell-centred thicknesses in metres.
- Only observed cells contribute to thickness and signed net-loss summaries; no spatial interpolation is performed.
- Caller-selected four-neighbour or eight-neighbour threshold connectivity describes map geometry and supplies no acceptance, capacity, life or probability conclusion.

## 구현 근거·독립 설명

- `authored_rectilinear_thickness_map_cell_area_balance`: Use explicit increasing x/y cell edges to compute actual rectilinear cell areas, observed-area-weighted thickness, missing coverage, signed observed reference-loss volume, and caller-selected four- or eight-neighbour threshold component areas. Missing cells are excluded from observations and never interpolated or assumed sound; geometry summaries are not structural acceptance or life predictions.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "geometry.rectilinear_thickness_map"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["geometry.rectilinear_thickness_map"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "x_cell_edges_m": [
    0.0,
    0.01,
    0.03
  ],
  "y_cell_edges_m": [
    0.0,
    0.01,
    0.04
  ],
  "cell_thickness_m": [
    [
      0.01,
      0.009
    ],
    [
      null,
      0.006
    ]
  ],
  "reference_thickness_m": 0.01,
  "reporting_threshold_m": 0.008,
  "threshold_comparison": "less_than",
  "connectivity": "four_neighbour"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/rectilinear_thickness_map.py#L51)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
