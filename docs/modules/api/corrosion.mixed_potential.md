# `corrosion.mixed_potential`

**목적:** Reviewed compatible signed net polarization curves share one reference, electrolyte and temperature; negligible ohmic drop and quasi-steady response are required.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `electrodes` | 예 | `{"items": {"$ref": "#/$defs/PolarizedElectrode"}, "maxItems": 32, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `quasi_steady_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negligible_ohmic_drop_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `condition_compatibility_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `anodic_positive_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_balance_tolerance_A` | 아니오 | `{"default": 1e-12, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_balance_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMaximum": 0.01, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MixedPotential.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `mixed_potential_V` | `V` |
| `electrode_net_current_A` | `A` |
| `total_positive_net_current_A` | `A` |
| `common_potential_interval_V` | `V` |
| `zero_balance_intervals_V` | `V` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reviewed compatible signed net polarization curves share one reference, electrolyte and temperature; negligible ohmic drop and quasi-steady response are required.
- Area-scaled electrode currents sum to zero on the common measured support; all piecewise-linear roots and zero intervals are preserved.
- A unique algebraic equilibrium does not establish dynamic stability, total metal loss, structural acceptance or failure probability.

## 구현 근거·독립 설명

- [IUPAC mixed-potential definition and signed partial-current balance](https://goldbook.iupac.org/terms/view/M03944) · `iupac_mixed_potential`
- [Gamry explanation of measured net current, partial reactions and polarization limitations](https://www.gamry.com/application-notes/corrosion-coatings/basics-of-electrochemical-corrosion-measurements/) · `gamry_net_polarization`
- `signed_interpolant_balance`: Independently form the area-scaled sum of signed net electrode-current interpolants on their common potential support. The union of knots partitions the balance into linear segments; retain every isolated zero and contiguous zero interval. Normalize finite currents, check cancellation and final residuals, and select a scalar result only for one numerically resolved root with no zero intervals. Do not extrapolate, convert potential references automatically, equate net current to metal-dissolution current, or infer physical stability and failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.mixed_potential"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.mixed_potential"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "electrodes": [
    {
      "electrode_id": "authored-A",
      "exposed_area_m2": 0.0001,
      "curve": {
        "curve_id": "authored-A-curve",
        "surface_condition_id": "synthetic-A",
        "protocol_id": "synthetic-steady",
        "electrolyte_id": "synthetic-common-bath",
        "reference_electrode_id": "synthetic-reference",
        "temperature_K": 298.15,
        "point_ids": [
          "A-0",
          "A-1"
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
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "Authored linear balance fixture"
          }
        ]
      }
    },
    {
      "electrode_id": "authored-B",
      "exposed_area_m2": 0.0003,
      "curve": {
        "curve_id": "authored-B-curve",
        "surface_condition_id": "synthetic-B",
        "protocol_id": "synthetic-steady",
        "electrolyte_id": "synthetic-common-bath",
        "reference_electrode_id": "synthetic-reference",
        "temperature_K": 298.15,
        "point_ids": [
          "B-0",
          "B-1"
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
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "Authored linear balance fixture"
          }
        ]
      }
    }
  ],
  "quasi_steady_reviewed": true,
  "negligible_ohmic_drop_reviewed": true,
  "condition_compatibility_reviewed": true,
  "anodic_positive_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemistry.py#L321)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
