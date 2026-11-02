# `data.zenodo_ceit_uniform_corrosion_field_typed_rows`

**목적:** Only the catalogued CEIT JSON filename, byte count, MD5 and acquisition SHA-256 are accepted before invoking the existing parser.

**모델 버전:** `1.0.0` · **구현 분류:** `data_import` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `local_json_path` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `series_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reported_tof_unit` | 아니오 | `{"anyOf": [{"enum": ["ns", "s"], "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `reported_temperature_unit` | 아니오 | `{"anyOf": [{"enum": ["degC", "K"], "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `sample_interval_s` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | s |
| `authorization` | 예 | `{"$ref": "#/$defs/CeitFieldReadAuthorization"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CeitFieldArchiveAuditRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `source_file_bytes` | `byte` |
| `observation_count` | `row` |
| `sample_interval_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only the catalogued CEIT JSON filename, byte count, MD5 and acquisition SHA-256 are accepted before invoking the existing parser.
- Caller supplies attribution and computational/local-only authorization; every typed row retains source Evidence and authorization digest.
- JSON array order and unresolved provider signal units are preserved; ToF, temperature and sample-clock conversions require explicit caller units.
- No thickness, wall loss, corrosion rate, uncertainty, acceptance, remaining life or probability is inferred.

## 구현 근거·독립 설명

- `zenodo_ceit_uniform_corrosion_field_typed_rows`: Read only the catalogued CEIT uniform-corrosion JSON after matching its filename, byte count, MD5 and local acquisition SHA-256 before reusing the existing parser. Preserve observation order, caller-selected units/clock choices, source/Evidence/authorization and row digest lineage. Keep raw signals local and do not infer thickness, corrosion rate, uncertainty, acceptance, life or probability from unresolved ToF and voltage fields.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "data.zenodo_ceit_uniform_corrosion_field_typed_rows"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/ceit_typed_rows.py#L200)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
