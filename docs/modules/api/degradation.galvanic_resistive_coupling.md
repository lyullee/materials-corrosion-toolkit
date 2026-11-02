# `degradation.galvanic_resistive_coupling`

**목적:** Exactly two reviewed signed net polarization curves share one environment and reference electrode; every root is bounded by both supplied curve supports.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `environment` | 예 | `{"$ref": "#/$defs/GalvanicEnvironment"}` | 계약·필드 설명 참조 |
| `electrodes` | 예 | `{"maxItems": 2, "minItems": 2, "prefixItems": [{"$ref": "#/$defs/GalvanicElectrodeEvidence"}, {"$ref": "#/$defs/GalvanicElectrodeEvidence"}], "type": "array"}` | 계약·필드 설명 참조 |
| `connection` | 예 | `{"$ref": "#/$defs/ResistiveGalvanicConnection"}` | 계약·필드 설명 참조 |
| `partial_dissolution_observations` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/PartialDissolutionObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `solver_id` | 예 | `{"const": "matintegrity.two_electrode_piecewise_resistive_balance.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `solver_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `quasi_steady_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `condition_compatibility_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_reference_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `anodic_positive_net_current_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_current_balance_tolerance_A` | 아니오 | `{"default": 1e-12, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_voltage_balance_tolerance_V` | 아니오 | `{"default": 1e-12, "minimum": 0, "type": "number"}` | V |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ResistiveGalvanicCoupling.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `electrode_interface_potential_V` | `V` |
| `signed_net_electrode_current_A` | `A` |
| `series_voltage_drop_V` | `V` |
| `declared_total_series_resistance_ohm` | `ohm` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Exactly two reviewed signed net polarization curves share one environment and reference electrode; every root is bounded by both supplied curve supports.
- Caller-owned electrolyte, contact and lead resistance components sum to the finite declared series resistance used in the voltage balance.
- No current-to-loss conversion, corrosion rate, acceptance, life, stability claim, or failure probability is produced.

## 구현 근거·독립 설명

- `authored_two_electrode_resistive_galvanic_balance`: For two caller-reviewed piecewise-linear signed polarization curves in one shared electrolyte, temperature and reference, solve every segment-pair equilibrium under one finite series resistance. Enforce current and voltage balance, retain multiple or continuous roots, reject roots outside either curve support, and keep net current distinct from partial dissolution. No corrosion rate, life, stability, acceptance or probability is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.galvanic_resistive_coupling"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.galvanic_resistive_coupling"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "resistive-couple-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "environment": {
    "environment_id": "environment-1",
    "electrolyte_id": "bath",
    "electrolyte_description": "authored electrolyte",
    "temperature_K": 298.15,
    "reference_electrode_id": "reference",
    "condition_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "electrodes": [
    {
      "electrode_id": "electrode-a",
      "metal_id": "metal-a",
      "material_condition_id": "condition-a",
      "exposed_area_m2": 1.0,
      "polarization_curve": {
        "curve_id": "curve-a",
        "surface_condition_id": "surface-curve-a",
        "protocol_id": "steady-branch",
        "electrolyte_id": "bath",
        "reference_electrode_id": "reference",
        "temperature_K": 298.15,
        "point_ids": [
          "curve-a-left",
          "curve-a-right"
        ],
        "potential_V": [
          -1.0,
          0.0
        ],
        "signed_net_current_density_A_m2": [
          -2.0,
          8.0
        ],
        "evidence": [
          {
            "source_id": "authored-resistive-fixture",
            "origin": "synthetic",
            "citation": "Independent finite-resistance circuit fixture"
          }
        ]
      },
      "curve_provider_id": "provider-a",
      "curve_provider_revision": "1",
      "curve_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "curve_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "curve_support_reviewed": true
    },
    {
      "electrode_id": "electrode-b",
      "metal_id": "metal-b",
      "material_condition_id": "condition-b",
      "exposed_area_m2": 1.0,
      "polarization_curve": {
        "curve_id": "curve-b",
        "surface_condition_id": "surface-curve-b",
        "protocol_id": "steady-branch",
        "electrolyte_id": "bath",
        "reference_electrode_id": "reference",
        "temperature_K": 298.15,
        "point_ids": [
          "curve-b-left",
          "curve-b-right"
        ],
        "potential_V": [
          -1.0,
          0.0
        ],
        "signed_net_current_density_A_m2": [
          -7.0,
          3.0
        ],
        "evidence": [
          {
            "source_id": "authored-resistive-fixture",
            "origin": "synthetic",
            "citation": "Independent finite-resistance circuit fixture"
          }
        ]
      },
      "curve_provider_id": "provider-b",
      "curve_provider_revision": "2",
      "curve_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "curve_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "curve_support_reviewed": true
    }
  ],
  "connection": {
    "connection_id": "connection-1",
    "components": [
      {
        "component_id": "electrolyte-path",
        "component_kind": "electrolyte",
        "resistance_ohm": 0.08,
        "basis": "caller four-terminal result",
        "evidence": [
          {
            "source_id": "authored-resistive-fixture",
            "origin": "synthetic",
            "citation": "Independent finite-resistance circuit fixture"
          }
        ]
      },
      {
        "component_id": "contact-path",
        "component_kind": "contact",
        "resistance_ohm": 0.02,
        "basis": "caller contact measurement",
        "evidence": [
          {
            "source_id": "authored-resistive-fixture",
            "origin": "synthetic",
            "citation": "Independent finite-resistance circuit fixture"
          }
        ]
      }
    ],
    "declared_total_series_resistance_ohm": 0.1,
    "component_sum_tolerance_ohm": 1e-12,
    "connection_reviewed": true
  },
  "solver_id": "matintegrity.two_electrode_piecewise_resistive_balance.v1",
  "solver_revision": "1",
  "quasi_steady_reviewed": true,
  "condition_compatibility_reviewed": true,
  "common_reference_reviewed": true,
  "anodic_positive_net_current_reviewed": true,
  "caller_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-resistive-fixture",
      "origin": "synthetic",
      "citation": "Independent finite-resistance circuit fixture"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/galvanic_resistive_coupling.py#L97)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
