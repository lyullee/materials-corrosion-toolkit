# `degradation.under_deposit_local_environment_review`

**목적:** Local-environment observations and caller criteria are reviewed and identity-linked.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history` | 예 | `{"$ref": "#/$defs/LocalEnvironmentHistoryAssessment"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UnderDepositLocalEnvironmentInput.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `decision` | `1` |
| `findings` | `mixed` |
| `total_exposure_time_s` | `s` |
| `complete_evidence_time_s` | `s` |
| `complete_evidence_fraction` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |
| `calibrated_loss_integrated` | `1` |
| `corrosion_rate_inferred` | `1` |
| `failure_probability_inferred` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Local-environment observations and caller criteria are reviewed and identity-linked.
- This model delegates to the shared local-environment evaluator and produces no damage-rate calculation.

## 구현 근거·독립 설명

- `caller_under_deposit_environment_criteria_comparison`: Compare measured under-deposit local-environment facts with caller-owned bounds using method- and unit-matched expanded uncertainty intervals. Preserve sampling state, clock, material/environment, reference and evidence identity; missing or mismatched facts remain insufficient. Do not infer a corrosion mechanism, local-loss rate, lifetime or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.under_deposit_local_environment_review"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.under_deposit_local_environment_review"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history": {
    "schema_version": "matintegrity.local_environment_history.v1",
    "assessment_id": "synthetic-under-deposit-environment",
    "domain": "under_deposit",
    "asset_id": "synthetic-asset",
    "location_id": "synthetic-location",
    "physical_scope_id": "synthetic-deposit-covered-surface",
    "clock_id": "synthetic-deposit-clock",
    "couples": [],
    "states": [
      {
        "state_id": "state-1",
        "start_time_s": 0.0,
        "end_time_s": 3600.0,
        "material_condition_id": "material-1",
        "environment_id": "environment-1",
        "couple_id": null,
        "state_descriptors": {
          "deposit": "synthetic observed deposit"
        },
        "facts": [
          {
            "fact_id": "fact-ph-1",
            "fact_kind": "pH",
            "quantity_id": "deposit_pH",
            "status": "reported",
            "value": 6.5,
            "expanded_uncertainty": 0.2,
            "unit_token": "pH",
            "reference_electrode_id": null,
            "method_id": "synthetic-method",
            "fact_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "invalid_or_missing_basis": null,
            "evidence": [
              {
                "source_id": "authored-example",
                "origin": "synthetic",
                "citation": "authored environment record",
                "license_id": null,
                "sha256": null
              }
            ]
          }
        ],
        "state_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored environment interval",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "criteria": [
      {
        "criterion_id": "caller-ph-window",
        "applicable_domain": "under_deposit",
        "fact_kind": "pH",
        "quantity_id": "deposit_pH",
        "unit_token": "pH",
        "reference_electrode_id": null,
        "minimum_acceptable": 6.0,
        "maximum_acceptable": 7.0,
        "comparison": "uncertainty_interval_against_bounds",
        "criterion_basis": "synthetic caller-defined review window",
        "criterion_source_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored caller criterion",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "clock_state_and_identity_reviewed": true,
    "units_references_methods_and_uncertainties_reviewed": true,
    "caller_rules_and_missing_evidence_policy_reviewed": true,
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored campaign",
        "license_id": null,
        "sha256": null
      }
    ],
    "payload_digest": "96d75ff88ca16b363146215905104583d5e37601a98089312c13272668c61737"
  }
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/under_deposit.py#L196)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
