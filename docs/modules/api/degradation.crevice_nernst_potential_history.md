# `degradation.crevice_nernst_potential_history`

**목적:** Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_nernst_profile.v1", "default": "matintegrity.crevice_nernst_profile.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_inventory_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_quotient_stoichiometry` | 예 | `{"additionalProperties": {"type": "number"}, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `electron_number` | 예 | `{"maximum": 32, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | K |
| `standard_potential_V` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | V |
| `species_activity_history` | 예 | `{"additionalProperties": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `activity_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `activity_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `standard_potential_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `redox_reaction_direction_and_electron_number_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_standard_state_and_species_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `standard_potential_temperature_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `local_activity_history_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `potential_only_no_rate_or_acceptance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceNernstProfile.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `source_inventory_sha256` | `1` |
| `elapsed_time_s` | `s` |
| `temperature_K` | `K` |
| `standard_potential_V` | `V` |
| `potential_history[].time_s` | `s` |
| `potential_history[].temperature_K` | `K` |
| `potential_history[].standard_potential_V` | `V` |
| `potential_history[].potential_V` | `V` |
| `potential_history[].ln_reaction_quotient` | `1` |
| `electron_number` | `1` |
| `potential_history_sha256` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.
- Reaction direction, activity standard state, species mapping and temperature applicability are reviewed caller inputs; this half-cell potential is not a mixed-potential or corrosion-rate calculation.

## 구현 근거·독립 설명

- `crevice_nernst_activity_potential`: Evaluate a caller-specified redox half-cell potential at each crevice-history knot using E = E0 - RT/(nF) ln(Q), caller-supplied dimensionless species activities, signed reaction-quotient stoichiometry and a caller-supplied standard-potential history. Preserve source-inventory digest, activity-provider and standard-potential-provider configuration/record identities, and the complete potential history. Require explicit reaction direction, electron count, standard-state mapping, temperature and local applicability review, with both providers mapped to declared Evidence. This computes neither activity/speciation nor mixed potential, reaction kinetics, corrosion rate, susceptibility or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.crevice_nernst_potential_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.crevice_nernst_potential_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-crevice-redox-01",
  "asset_id": "synthetic-loop",
  "location_id": "synthetic-crevice",
  "physical_scope_id": "synthetic-scope-01",
  "clock_id": "synthetic-elapsed-time",
  "source_inventory_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "reaction_id": "Fe3+_plus_e_to_Fe2+",
  "standard_potential_reference_id": "SHE",
  "reaction_quotient_stoichiometry": {
    "Fe3+": -1.0,
    "Fe2+": 1.0
  },
  "electron_number": 1,
  "elapsed_time_s": [
    0.0,
    60.0,
    120.0
  ],
  "temperature_K": [
    298.15,
    300.0,
    302.0
  ],
  "standard_potential_V": [
    0.77,
    0.769,
    0.768
  ],
  "species_activity_history": {
    "Fe3+": [
      0.01,
      0.008,
      0.006
    ],
    "Fe2+": [
      0.02,
      0.025,
      0.03
    ]
  },
  "activity_provider_id": "synthetic-activity-provider",
  "activity_provider_revision": "1",
  "activity_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
  "activity_record_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
  "standard_potential_provider_id": "synthetic-standard-potential-provider",
  "standard_potential_provider_revision": "1",
  "standard_potential_configuration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
  "standard_potential_record_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
  "redox_reaction_direction_and_electron_number_reviewed": true,
  "activity_standard_state_and_species_mapping_reviewed": true,
  "standard_potential_temperature_history_reviewed": true,
  "local_activity_history_applicability_reviewed": true,
  "potential_only_no_rate_or_acceptance_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-activity-provider",
      "origin": "synthetic",
      "citation": "Synthetic activity-provider wiring illustration only; not experimental data.",
      "license_id": null,
      "sha256": null
    },
    {
      "source_id": "synthetic-standard-potential-provider",
      "origin": "synthetic",
      "citation": "Synthetic standard-potential wiring illustration only; not experimental data.",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crevice_nernst_profile.py#L154)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
