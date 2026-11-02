# `data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows`

**목적:** The caller maps each worksheet, header value, inclusive row span, field meaning, unit token and field role.

**모델 버전:** `1.0.0` · **구현 분류:** `data_import` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `local_data_directory` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `authorization` | 예 | `{"$ref": "#/$defs/ExplosiveWeldFatigueReadAuthorization"}` | 계약·필드 설명 참조 |
| `worksheet_mappings` | 예 | `{"items": {"$ref": "#/$defs/ExplosiveWeldFatigueWorksheetMapping"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_output_rows` | 예 | `{"maximum": 10000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_output_cells` | 예 | `{"maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `mapping_reviewed` | 예 | `{"const": true, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExplosiveWeldFatigueMappedImportRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `source_file_bytes` | `byte` |
| `row_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller maps each worksheet, header value, inclusive row span, field meaning, unit token and field role.
- A mapping is rejected if its worksheet, dimensions or exact raw header values do not match the pinned workbook.
- Mapped rows preserve native cell types, raw formulas, cell addresses, caller mapping Evidence and source digests.
- No formula is evaluated, no unit is converted, and no material or specimen identity is inferred from labels.
- This data import does not fit a fatigue law, calculate design allowables or claim engineering qualification.
- The provider declares CC BY 4.0; possible third-party workbook content remains subject to separate rights review.

## 구현 근거·독립 설명

- [Fatigue test data of corrosion-resistant explosively welded heterostructured plates](https://data.mendeley.com/datasets/mc8bc9tm59/1) · `mendeley_explosive_weld_multilayer_fatigue_rows`
- `caller_explosive_weld_workbook_column_mapping`: Require a caller-reviewed worksheet, exact raw header values, selected row span, and explicit field IDs, meanings, unit tokens, roles and mapping Evidence before extracting selected source cells. Preserve raw values, formula text, cell types, coordinates and both source/mapping digests. Do not infer units or column meanings, evaluate formulas, fit fatigue relations, compute allowables or claim qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/mendeley_explosive_weld_fatigue_rows.py#L314)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
