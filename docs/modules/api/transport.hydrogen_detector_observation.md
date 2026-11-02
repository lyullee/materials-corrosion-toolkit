# `transport.hydrogen_detector_observation`

**목적:** Instantaneous reviewed Faraday or sample-mass observation identity for a signed hydrogen-atom release history; detector dynamics and transport inversion are excluded.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.hydrogen_detector_observation.v1", "default": "matintegrity.hydrogen_detector_observation.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `observation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_origin_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_model_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `source_surface_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_flow_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `detector_calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `detector_kind` | 예 | `{"enum": ["electrochemical_current", "mass_normalized_tds"], "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 100000, "minItems": 2, "type": "array"}` | s |
| `outward_hydrogen_atoms_mol_s` | 예 | `{"items": {"type": "number"}, "type": "array"}` | 계약·필드 설명 참조 |
| `current_sign_for_outward_hydrogen` | 아니오 | `{"anyOf": [{"enum": [-1, 1], "type": "integer"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `electron_mol_per_hydrogen_atom_mol` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `current_efficiency` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "maximum": 1, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `background_current_A` | 아니오 | `{"anyOf": [{"type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `sample_mass_kg` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | kg |
| `hydrogen_atomic_molar_mass_kg_mol` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | kg/mol |
| `source_surface_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `detector_response_mapping_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HydrogenDetectorObservation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `outward_hydrogen_atoms_mol_s` | `mol/s` |
| `cumulative_outward_hydrogen_atoms_mol` | `mol` |
| `electrochemical_equivalent_current_A` | `A` |
| `predicted_current_A` | `A` |
| `background_current_A` | `A` |
| `predicted_hydrogen_mass_ppm_per_sample_mass_per_s` | `ppm/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Instantaneous reviewed Faraday or sample-mass observation identity for a signed hydrogen-atom release history; detector dynamics and transport inversion are excluded.

## 구현 근거·독립 설명

- [BIPM SI defining constants for elementary charge and the Avogadro constant](https://www.bipm.org/en/measurement-units/) · `si_defining_constants`
- `hydrogen_detector_observation_derivation`: For a reviewed signed outward hydrogen-atom molar flow, apply the declared electron-per-hydrogen-atom stoichiometry, current efficiency and exact-SI Faraday constant to form the ideal electrochemical current, or multiply by atomic molar mass and divide by reviewed sample mass to form a mass-normalized ppm rate. Preserve negative values and integrate only on the declared elapsed-time knots. This algebraic forward observation identity has no detector lag, gas-line volume, pumping, recombination, adsorption, noise, uncertainty or inverse boundary inference.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.hydrogen_detector_observation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["transport.hydrogen_detector_observation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "observation_id": "synthetic-permeation-observation",
  "material_condition_id": "synthetic-state",
  "specimen_id": "synthetic-membrane",
  "elapsed_time_origin_id": "synthetic-release-start",
  "source_model_id": "authored.synthetic_flow",
  "source_model_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_surface_id": "exit-face",
  "source_flow_basis": "Authored signed hydrogen-atom flow demonstration",
  "detector_calibration_id": "synthetic-faraday-mapping",
  "detector_kind": "electrochemical_current",
  "elapsed_time_s": [
    0.0,
    5.0,
    10.0
  ],
  "outward_hydrogen_atoms_mol_s": [
    0.0,
    2e-10,
    4e-10
  ],
  "current_sign_for_outward_hydrogen": 1,
  "electron_mol_per_hydrogen_atom_mol": 1.0,
  "current_efficiency": 0.9,
  "background_current_A": 1e-07,
  "source_surface_mapping_reviewed": true,
  "detector_response_mapping_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-synthetic",
      "origin": "synthetic",
      "citation": "Authored detector-observation demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hydrogen_observation.py#L75)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
