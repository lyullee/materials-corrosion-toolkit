# `corrosion.planar_slit_hydraulic_history`

**목적:** Digest-bound pressure samples are paired to every computed aperture-history knot; each knot is solved independently and the result is operator-split, not transiently or fully coupled.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `flow_history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `aperture_history_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `aperture_history_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_history_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_drop_Pa` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | Pa |
| `fluid_property_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `dynamic_viscosity_Pa_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa·s |
| `density_kg_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | kg/m³ |
| `minimum_width_to_aperture_ratio` | 아니오 | `{"default": 20.0, "exclusiveMinimum": 0, "maximum": 1000.0, "minimum": 20.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_reviewed_reynolds_number` | 아니오 | `{"default": 1000.0, "exclusiveMinimum": 0, "maximum": 1000.0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_and_boundary_pressures_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incompressible_newtonian_fluid_properties_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `laminar_fully_developed_slit_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_history_and_geometry_time_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PlanarSlitHydraulicHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `flow_snapshots` | `aligned steady snapshots, SI` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Digest-bound pressure samples are paired to every computed aperture-history knot; each knot is solved independently and the result is operator-split, not transiently or fully coupled.

## 구현 근거·독립 설명

- `planar_slit_sequential_hydraulic_history`: Require a computed digest-bound planar-slit aperture history and one positive pressure-drop sample for each geometry knot. At each knot, independently evaluate the registered steady wide-slit hydraulic reduction and retain its flow, pressure and face-velocity diagnostics with the source geometry time. Aggregate only when every knot is within the declared aspect-ratio and Reynolds support.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.planar_slit_hydraulic_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.planar_slit_hydraulic_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "flow_history_id": "synthetic-history",
  "aperture_history_result": {
    "geometry_id": "synthetic-crevice-geometry-history",
    "status": "computed",
    "input_sha256": "9aa91188885400504cd6ca375631847e35dea7cc8189fc22bfb60cec18da1070",
    "geometry_source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "wall_loss_source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "cell_count": 3,
    "cell_widths_m": [
      0.01,
      0.01,
      0.02
    ],
    "transverse_width_m": 0.01,
    "reference_cross_section_m2": 1e-06,
    "reactive_broad_face_count": 1,
    "face_area_interpolation_basis": "Linear interpolation of cross section between nonuniform cell centers; boundary faces use constant extrapolation from the nearest cell.",
    "wall_loss_selection_sha256": null,
    "geometry_states": [
      {
        "elapsed_time_s": 0.0,
        "cell_aperture_m": [
          0.0001,
          8e-05,
          6e-05
        ],
        "axial_cross_section_m2": [
          1.0000000000000002e-06,
          8.000000000000001e-07,
          6.000000000000001e-07
        ],
        "cell_cross_section_m2": [
          1.0000000000000002e-06,
          8.000000000000001e-07,
          6.000000000000001e-07
        ],
        "face_cross_section_m2": [
          1.0000000000000002e-06,
          9.000000000000001e-07,
          7.333333333333334e-07,
          6.000000000000001e-07
        ],
        "cell_volume_m3": [
          1.0000000000000002e-08,
          8e-09,
          1.2000000000000002e-08
        ],
        "reactive_broad_wall_area_m2": [
          0.0001,
          0.0001,
          0.0002
        ],
        "wall_area_per_volume_m2_m3": [
          9999.999999999998,
          12500.0,
          16666.666666666664
        ],
        "cumulative_signed_cell_average_recession_m": [
          0.0,
          0.0,
          0.0
        ],
        "restricted_transport_geometry": {
          "cell_count": 3,
          "length_m": 0.04,
          "cell_widths_m": [
            0.01,
            0.01,
            0.02
          ],
          "cell_cross_section_m2": [
            1.0000000000000002e-06,
            8.000000000000001e-07,
            6.000000000000001e-07
          ],
          "face_cross_section_m2": [
            1.0000000000000002e-06,
            9.000000000000001e-07,
            7.333333333333334e-07,
            6.000000000000001e-07
          ],
          "reference_cross_section_m2": 1e-06,
          "wall_area_per_volume_m2_m3": [
            9999.999999999998,
            12500.0,
            16666.666666666664
          ]
        }
      },
      {
        "elapsed_time_s": 10.0,
        "cell_aperture_m": [
          0.000102,
          8.1e-05,
          6e-05
        ],
        "axial_cross_section_m2": [
          1.02e-06,
          8.100000000000001e-07,
          6.000000000000001e-07
        ],
        "cell_cross_section_m2": [
          1.02e-06,
          8.100000000000001e-07,
          6.000000000000001e-07
        ],
        "face_cross_section_m2": [
          1.02e-06,
          9.15e-07,
          7.400000000000001e-07,
          6.000000000000001e-07
        ],
        "cell_volume_m3": [
          1.02e-08,
          8.100000000000001e-09,
          1.2000000000000002e-08
        ],
        "reactive_broad_wall_area_m2": [
          0.0001,
          0.0001,
          0.0002
        ],
        "wall_area_per_volume_m2_m3": [
          9803.921568627451,
          12345.679012345678,
          16666.666666666664
        ],
        "cumulative_signed_cell_average_recession_m": [
          2e-06,
          1e-06,
          0.0
        ],
        "restricted_transport_geometry": {
          "cell_count": 3,
          "length_m": 0.04,
          "cell_widths_m": [
            0.01,
            0.01,
            0.02
          ],
          "cell_cross_section_m2": [
            1.02e-06,
            8.100000000000001e-07,
            6.000000000000001e-07
          ],
          "face_cross_section_m2": [
            1.02e-06,
            9.15e-07,
            7.400000000000001e-07,
            6.000000000000001e-07
          ],
          "reference_cross_section_m2": 1e-06,
          "wall_area_per_volume_m2_m3": [
            9803.921568627451,
            12345.679012345678,
            16666.666666666664
          ]
        }
      }
    ],
    "basis": "Sequential fixed-length planar slit update. Signed recession is positive metal loss and negative deposition. For two reactive broad faces, equal recession on opposing faces is assumed only when reviewed. This remaps geometry for caller-controlled subsequent transport; it does not couple flow, chemistry, stress, deposits, roughness, or time integration within an interval."
  },
  "aperture_history_source_sha256": "c044f13ca59326b7154c53526e4faadba7d64a08cdd0ee752758f39da13eed95",
  "pressure_history_source_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "pressure_drop_Pa": [
    1000.0,
    1200.0
  ],
  "fluid_property_source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "dynamic_viscosity_Pa_s": 0.001,
  "density_kg_m3": 1000.0,
  "geometry_and_boundary_pressures_reviewed": true,
  "incompressible_newtonian_fluid_properties_reviewed": true,
  "laminar_fully_developed_slit_assumption_reviewed": true,
  "pressure_history_and_geometry_time_alignment_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_numeric.py#L112)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
