# `inspection.known_volume_pressure_rise`

**목적:** Rigid known volume, absolute pressure, one reviewed clock and independent blank/test source groups.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `apparatus_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `rigid_volume_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 아니오 | `{"const": "absolute", "default": "absolute", "type": "string"}` | 계약·필드 설명 참조 |
| `runs` | 예 | `{"items": {"$ref": "#/$defs/VacuumPressureRiseRun"}, "maxItems": 2, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_temperature_range_K` | 예 | `{"minimum": 0, "type": "number"}` | K |
| `molar_conversion_requested` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `molar_conversion_state_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_temperature_K` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | K |
| `reference_net_throughput_Pa_m3_s` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `reference_standard_uncertainty_Pa_m3_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `reference_source_group_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `reference_result_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `apparatus_volume_and_isolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `absolute_pressure_temperature_and_clock_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `blank_test_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fit_windows_weights_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_comparison_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/KnownVolumePressureRiseTest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `apparatus_id` | `1` |
| `blank_pressure_slope_Pa_s` | `Pa/s` |
| `test_pressure_slope_Pa_s` | `Pa/s` |
| `blank_slope_standard_uncertainty_Pa_s` | `Pa/s` |
| `test_slope_standard_uncertainty_Pa_s` | `Pa/s` |
| `net_gas_throughput_Pa_m3_s` | `Pa*m3/s` |
| `net_gas_throughput_standard_uncertainty_Pa_m3_s` | `Pa*m3/s` |
| `fit_point_counts` | `count` |
| `fit_window_temperature_ranges_K` | `K` |
| `net_molar_flow_mol_s` | `mol/s` |
| `net_molar_flow_standard_uncertainty_mol_s` | `mol/s` |
| `reference_comparison` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Rigid known volume, absolute pressure, one reviewed clock and independent blank/test source groups.
- Weighted linear fits use original monotonic trace points inside declared windows.
- Molar conversion is optional and requires an explicitly reviewed absolute temperature state.

## 구현 근거·독립 설명

- `weighted_blank_corrected_known_volume_pressure_rise`: Fit caller-reviewed blank and test absolute-pressure histories on their original clocks with uncertainty weights, subtract their slopes, and multiply by a known volume to obtain signed net gas throughput with propagated uncertainty. Preserve independent run/source identities and optional reviewed reference-temperature conversion without separating outgassing from through-leak, locating a leak, deciding acceptance or creating probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.known_volume_pressure_rise"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.known_volume_pressure_rise"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "vacuum-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "apparatus_id": "apparatus-1",
  "rigid_volume_m3": 0.5,
  "pressure_basis": "absolute",
  "runs": [
    {
      "run_id": "blank-1",
      "role": "blank",
      "source_group_id": "source-blank",
      "clock_id": "clock-1",
      "elapsed_time_s": [
        0,
        10,
        20,
        30
      ],
      "absolute_pressure_Pa": [
        100,
        110,
        120,
        130
      ],
      "pressure_standard_uncertainty_Pa": [
        1,
        1,
        1,
        1
      ],
      "temperature_K": [
        300,
        300,
        300,
        300
      ],
      "fit_window_start_s": 0,
      "fit_window_end_s": 30,
      "apparatus_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "run_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "run_id": "test-1",
      "role": "test",
      "source_group_id": "source-test",
      "clock_id": "clock-1",
      "elapsed_time_s": [
        0,
        10,
        20,
        30
      ],
      "absolute_pressure_Pa": [
        100,
        130,
        160,
        190
      ],
      "pressure_standard_uncertainty_Pa": [
        1,
        1,
        1,
        1
      ],
      "temperature_K": [
        300,
        300,
        300,
        300
      ],
      "fit_window_start_s": 0,
      "fit_window_end_s": 30,
      "apparatus_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "run_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "maximum_temperature_range_K": 1,
  "molar_conversion_requested": false,
  "molar_conversion_state_reviewed": false,
  "reference_temperature_K": null,
  "reference_net_throughput_Pa_m3_s": null,
  "reference_standard_uncertainty_Pa_m3_s": null,
  "reference_source_group_id": null,
  "reference_result_digest": null,
  "apparatus_volume_and_isolation_reviewed": true,
  "absolute_pressure_temperature_and_clock_reviewed": true,
  "blank_test_independence_reviewed": true,
  "fit_windows_weights_and_uncertainty_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "reference_comparison_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/vacuum_pressure_rise.py#L133)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
