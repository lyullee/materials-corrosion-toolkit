# `degradation.galvanic_coupling`

**목적:** Caller-reviewed, condition-compatible signed polarization curves are solved only on their common measured support.

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
| `electrodes` | 예 | `{"items": {"$ref": "#/$defs/GalvanicElectrodeEvidence"}, "maxItems": 32, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `connection` | 예 | `{"$ref": "#/$defs/ElectricalConnection"}` | 계약·필드 설명 참조 |
| `partial_dissolution_observations` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/PartialDissolutionObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `solver_id` | 예 | `{"const": "matintegrity.corrosion.mixed_potential.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `solver_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `quasi_steady_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `condition_compatibility_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `anodic_positive_net_current_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GalvanicCouplingAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `mixed_potential_V` | `V` |
| `signed_net_electrode_current_A` | `A` |
| `partial_dissolution_observations` | `A/m2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed, condition-compatible signed polarization curves are solved only on their common measured support.
- Connection resistance must remain within the caller-declared negligible-resistance bound; otherwise this model is out of scope.
- Net current and separately supplied partial dissolution evidence are not interchangeable, and no rate, life, acceptance, or probability is produced.

## 구현 근거·독립 설명

- `authored_bounded_galvanic_coupling_assessment`: Compose reviewed electrode polarization curves within their common support while preserving metal, surface, area, electrolyte, environment, reference electrode, electrical connection, resistance and solver identities. Keep signed net current separate from partial dissolution observations; do not infer corrosion rate, life, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.galvanic_coupling"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.galvanic_coupling"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "couple-1",
  "asset_id": "asset-1",
  "location_id": "joint-1",
  "environment": {
    "environment_id": "environment-1",
    "electrolyte_id": "bath",
    "electrolyte_description": "authored test electrolyte",
    "temperature_K": 298.15,
    "reference_electrode_id": "ref",
    "condition_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "electrodes": [
    {
      "electrode_id": "steel",
      "metal_id": "metal-steel",
      "material_condition_id": "condition-a",
      "exposed_area_m2": 0.0001,
      "polarization_curve": {
        "schema_version": "matintegrity.polarization_curve.v1",
        "curve_id": "curve-steel",
        "surface_condition_id": "surface-curve-steel",
        "protocol_id": "steady-scan",
        "electrolyte_id": "bath",
        "reference_electrode_id": "ref",
        "temperature_K": 298.15,
        "point_ids": [
          "curve-steel-0",
          "curve-steel-1"
        ],
        "potential_V": [
          -1.0,
          0.0
        ],
        "signed_net_current_density_A_m2": [
          -2.0,
          8.0
        ],
        "current_convention": "anodic_positive_net",
        "evidence": [
          {
            "source_id": "authored-fixture",
            "origin": "synthetic",
            "citation": "Independent galvanic coupling test fixture",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "curve_provider_id": "provider-a",
      "curve_provider_revision": "1",
      "curve_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "curve_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "curve_support_reviewed": true
    },
    {
      "electrode_id": "alloy",
      "metal_id": "metal-alloy",
      "material_condition_id": "condition-b",
      "exposed_area_m2": 0.0003,
      "polarization_curve": {
        "schema_version": "matintegrity.polarization_curve.v1",
        "curve_id": "curve-alloy",
        "surface_condition_id": "surface-curve-alloy",
        "protocol_id": "steady-scan",
        "electrolyte_id": "bath",
        "reference_electrode_id": "ref",
        "temperature_K": 298.15,
        "point_ids": [
          "curve-alloy-0",
          "curve-alloy-1"
        ],
        "potential_V": [
          -1.0,
          0.0
        ],
        "signed_net_current_density_A_m2": [
          -7.0,
          3.0
        ],
        "current_convention": "anodic_positive_net",
        "evidence": [
          {
            "source_id": "authored-fixture",
            "origin": "synthetic",
            "citation": "Independent galvanic coupling test fixture",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "curve_provider_id": "provider-b",
      "curve_provider_revision": "2",
      "curve_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "curve_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "curve_support_reviewed": true
    }
  ],
  "connection": {
    "connection_id": "connection-1",
    "state": "connected",
    "total_resistance_ohm": 0.01,
    "resistance_basis": "four-wire measurement",
    "resistance_reviewed": true,
    "maximum_negligible_resistance_ohm": 0.1
  },
  "partial_dissolution_observations": [
    {
      "observation_id": "dissolution-1",
      "electrode_id": "steel",
      "species_id": "Fe2+",
      "partial_dissolution_current_density_A_m2": 9.0,
      "method_id": "caller-speciation",
      "provider_id": "lab-1",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-fixture",
          "origin": "synthetic",
          "citation": "Independent galvanic coupling test fixture",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "solver_id": "matintegrity.corrosion.mixed_potential.v1",
  "solver_revision": "1",
  "quasi_steady_reviewed": true,
  "condition_compatibility_reviewed": true,
  "anodic_positive_net_current_reviewed": true,
  "caller_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-fixture",
      "origin": "synthetic",
      "citation": "Independent galvanic coupling test fixture",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/galvanic_coupling.py#L86)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
