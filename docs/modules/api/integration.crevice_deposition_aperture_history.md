# `integration.crevice_deposition_aperture_history`

**목적:** Each exact-knot solid-volume result is per the declared reference area and matches the physical scope, time and cell ordering.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_deposition_aperture_history.v1", "default": "matintegrity.crevice_deposition_aperture_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_aperture_m` | 예 | `{"items": {"type": "number"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | m |
| `cell_length_m` | 예 | `{"items": {"type": "number"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `reference_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `deposition_side_count` | 예 | `{"enum": [1, 2], "type": "integer"}` | 계약·필드 설명 참조 |
| `coverage_fraction_by_cell` | 예 | `{"items": {"type": "number"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `knots` | 예 | `{"items": {"$ref": "#/$defs/CreviceDepositionVolumeKnot"}, "maxItems": 5000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_geometry_and_cell_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_area_conversion_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `side_count_and_equal_side_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uniform_coverage_within_each_cell_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `solid_volume_result_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `nonnegative_remaining_gap_as_scope_limit_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceDepositionApertureHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `knots[].elapsed_time_s` | `s` |
| `initial_aperture_m` | `m` |
| `cell_length_m` | `m` |
| `transverse_width_m` | `m` |
| `reference_area_m2` | `m2` |
| `coverage_fraction_by_cell` | `1` |
| `knots[].equivalent_mean_aperture_loss_m_by_cell` | `m` |
| `knots[].equivalent_mean_remaining_aperture_m_by_cell` | `m` |
| `knots[].covered_patch_aperture_loss_m_by_cell` | `m` |
| `knots[].covered_patch_remaining_aperture_m_by_cell` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each exact-knot solid-volume result is per the declared reference area and matches the physical scope, time and cell ordering.
- Solid volume is distributed equally across the declared one or two deposition faces and uniformly over the caller-declared coverage within each cell.
- Equivalent mean gap loss is solid volume divided by the cell planform area; covered-patch local closure additionally depends on the reviewed coverage fraction and face count.
- Negative remaining aperture and positive deposition volume with zero coverage fail closed; no clipping or extrapolation occurs.
- The mapping is a geometric adapter only and does not resolve morphology, porosity, adhesion, kinetics or transport feedback.

## 구현 근거·독립 설명

- `caller_crevice_deposition_aperture_geometry_mapping`: Map caller-reviewed solid-volume snapshots to mean-equivalent and covered-patch gap measures using explicit cell geometry, reference area, deposition faces, and coverage. Preserve exact result digests and physical/time/cell alignment. Equal face partition and uniform within-cell coverage are declared assumptions; this geometry mapping does not resolve deposit morphology, porosity, adhesion, transport feedback, corrosion or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_deposition_aperture_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_deposition_aperture_history.py#L78)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
