# `fatigue.multiaxial_life_scenario_envelope`

**목적:** The envelope consumes only digest-pinned computed results from the registered multiaxial critical-plane life campaign.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenario_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenario_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios` | 예 | `{"items": {"$ref": "#/$defs/MultiaxialLifeScenario"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_license_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_scenario_dependence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scenario_coverage_and_bounds_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scenario_lineage_and_calibration_match_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MultiaxialLifeScenarioEnvelope.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `minimum_cycles_to_failure` | `cycle` |
| `maximum_cycles_to_failure` | `cycle` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The envelope consumes only digest-pinned computed results from the registered multiaxial critical-plane life campaign.
- All scenarios share a calibration/material/support/context basis and remain complete joint cases; results are finite-set extrema, not probabilities or continuous bounds.

## 구현 근거·독립 설명

- `caller_correlated_finite_multiaxial_life_scenario_envelope`: Evaluate only a finite caller-provided set of complete computed multiaxial critical-plane life campaign results. Require result/input-context digests, unique scenario IDs, matching registered campaign revision, calibration digest, material condition, valid cycle support and asset/location/time identity; preserve scenario source, calibration and plane-factor digests. Report extrema and witnesses over the supplied scenarios only. Do not assign probabilities, confidence levels, continuous bounds, parameter-wise recombinations or extrapolated life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.multiaxial_life_scenario_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.multiaxial_life_scenario_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-multiaxial-envelope",
  "asset_id": "synthetic-asset",
  "location_id": "synthetic-location",
  "time_basis": "elapsed_seconds",
  "scenario_provider_id": "synthetic-scenario-provider",
  "scenario_provider_revision": "1",
  "scenarios_sha256": "9da15ab050781e96a2c1390aca5593ac77aa37b2c64e55a3fd68d2d0ccfd27e1",
  "scenarios": [
    {
      "scenario_id": "scenario-1",
      "life_result": {
        "schema_version": "matintegrity.assessment.v1",
        "model_id": "fatigue.multiaxial_life_campaign",
        "model_version": "1.0.0",
        "status": "computed",
        "inputs": {
          "calibration_material_condition_id": "synthetic-material",
          "minimum_valid_cycles": 1.0,
          "maximum_valid_cycles": 1000000000000.0,
          "history": {
            "material_condition_id": "synthetic-material"
          }
        },
        "values": {
          "life_result": {
            "status": "computed",
            "cycles_to_failure": 12000.0,
            "plane_id": "synthetic-plane"
          },
          "calibration_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
          "factor_result_sha256": "6666666666666666666666666666666666666666666666666666666666666666"
        },
        "units": {
          "cycles_to_failure": "cycle"
        },
        "assumptions": [
          "Synthetic API fixture only."
        ],
        "notes": [],
        "context": {
          "asset_id": "synthetic-asset",
          "location_id": "synthetic-location",
          "time_basis": "elapsed_seconds",
          "evidence": [],
          "metadata": {}
        },
        "input_digest": "0f5b635119ce2cbdd7978d05f9d0021383f93e7a51d94fa121b0c0a0d91b7186",
        "source_ids": [
          "synthetic-fixture"
        ],
        "qualification": "user_model",
        "runtime": {
          "matintegrity": "0.1.0"
        },
        "probability_semantics": {}
      },
      "life_result_sha256": "a4e019f065ec4cadf6fb10ca4654be2f5c8c4d12c9efbbeef10508c8939f0f75"
    }
  ],
  "evidence": [
    {
      "source_id": "synthetic-scenario-provider",
      "origin": "synthetic",
      "citation": "Project-authored synthetic finite scenario fixture.",
      "sha256": "9da15ab050781e96a2c1390aca5593ac77aa37b2c64e55a3fd68d2d0ccfd27e1"
    }
  ],
  "usage_rights_evidence": [
    {
      "source_id": "synthetic-rights",
      "origin": "synthetic",
      "citation": "Project-authored synthetic fixture.",
      "license_id": "CC0-1.0"
    }
  ],
  "usage_license_id": "CC0-1.0",
  "joint_scenario_dependence_reviewed": true,
  "scenario_coverage_and_bounds_reviewed": true,
  "scenario_lineage_and_calibration_match_reviewed": true,
  "usage_rights_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/multiaxial_life_scenario_envelope.py#L121)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
