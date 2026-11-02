# `electrochemistry.nernst_driven_butler_volmer_history`

**목적:** Evaluate one caller-calibrated Butler-Volmer reaction at exact common time knots using an upstream digest-bound Nernst equilibrium-potential history.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.nernst_driven_butler_volmer_history.v1", "default": "matintegrity.nernst_driven_butler_volmer_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `nernst_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `nernst_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_potential_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `electrode_potential_reference_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `electrode_potential_difference_history_V` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | V |
| `exchange_current_density_A_m2` | 예 | `{"minimum": 0, "type": "number"}` | A/m² |
| `electron_number` | 예 | `{"maximum": 32, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `anodic_transfer_coefficient` | 예 | `{"exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `cathodic_transfer_coefficient` | 예 | `{"exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_overpotential_V` | 예 | `{"type": "number"}` | V |
| `maximum_overpotential_V` | 예 | `{"type": "number"}` | V |
| `stoichiometric_species_coefficients` | 예 | `{"additionalProperties": {"type": "number"}, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `kinetics_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetics_calibration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `redox_to_kinetics_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_electrode_and_potential_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_parameter_and_temperature_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_direction_and_species_flux_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/NernstDrivenButlerVolmerHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `temperature_K` | `K` |
| `equilibrium_potential_V` | `V` |
| `electrode_potential_difference_V` | `V` |
| `overpotential_V` | `V` |
| `signed_current_density_A_m2` | `A/m2` |
| `gross_anodic_current_density_A_m2` | `A/m2` |
| `gross_cathodic_current_density_A_m2` | `A/m2` |
| `signed_reaction_extent_mol_m2_s` | `mol/m2/s` |
| `species_flux_mol_m2_s.*` | `mol/m2/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Evaluate one caller-calibrated Butler-Volmer reaction at exact common time knots using an upstream digest-bound Nernst equilibrium-potential history.
- Caller must match the potential reference, redox/kinetic direction, reaction identity and temperature support. The API does not interpolate or integrate time and does not determine mixed potential or total corrosion rate.

## 구현 근거·독립 설명

- `nernst_driven_butler_volmer_history`: Bind a computed, input- and output-digest-checked caller Nernst half-cell potential history to one caller-calibrated Butler-Volmer reaction at an identical declared clock ID and exact time knots. Require matching reaction identity and explicitly identical potential reference identifiers, caller electrode-potential difference history, valid overpotential/temperature support, calibration lineage and direction/species-flux mapping review. Report signed partial current density, reaction extent and stoichiometric species flux only at supplied knots. Do not interpolate or integrate time, solve mixed potential, infer kinetics/activity, or convert partial current into total corrosion loss, protection or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "electrochemistry.nernst_driven_butler_volmer_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["electrochemistry.nernst_driven_butler_volmer_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-crevice-redox-flux-01",
  "nernst_result": {
    "schema_version": "matintegrity.assessment.v1",
    "model_id": "degradation.crevice_nernst_potential_history",
    "model_version": "1.0.0",
    "status": "computed",
    "inputs": {
      "schema_version": "matintegrity.crevice_nernst_profile.v1",
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
    },
    "values": {
      "assessment_id": "synthetic-crevice-redox-01",
      "asset_id": "synthetic-loop",
      "location_id": "synthetic-crevice",
      "physical_scope_id": "synthetic-scope-01",
      "clock_id": "synthetic-elapsed-time",
      "source_inventory_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "reaction_id": "Fe3+_plus_e_to_Fe2+",
      "reaction_quotient_stoichiometry": {
        "Fe3+": -1.0,
        "Fe2+": 1.0
      },
      "electron_number": 1,
      "activity_provider_id": "synthetic-activity-provider",
      "activity_provider_revision": "1",
      "activity_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "activity_record_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "standard_potential_provider_id": "synthetic-standard-potential-provider",
      "standard_potential_provider_revision": "1",
      "standard_potential_configuration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "standard_potential_record_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
      "input_digest": "41f37b337297201f17567285748ddc86bb17493b0a7bf106604f7cec5fbd858b",
      "potential_history": [
        {
          "time_s": 0.0,
          "temperature_K": 298.15,
          "standard_potential_V": 0.77,
          "ln_reaction_quotient": 0.693147180559945,
          "potential_V": 0.7521912612209061
        },
        {
          "time_s": 60.0,
          "temperature_K": 300.0,
          "standard_potential_V": 0.769,
          "ln_reaction_quotient": 1.1394342831883653,
          "potential_V": 0.739543345154357
        },
        {
          "time_s": 120.0,
          "temperature_K": 302.0,
          "standard_potential_V": 0.768,
          "ln_reaction_quotient": 1.6094379124341005,
          "potential_V": 0.7261154301743489
        }
      ],
      "potential_history_sha256": "e75c798c3b901cf0876083f6f19e1c421dcbf2025a4512fe67ce057c74a5e64f",
      "reaction_quotient_definition": "lnQ=sum(nu_i*ln(a_i)); products positive, reactants negative; electrons excluded",
      "standard_potential_interpretation": "caller_supplied_knotwise_history",
      "missing_reviews": []
    },
    "units": {
      "source_inventory_sha256": "1",
      "elapsed_time_s": "s",
      "temperature_K": "K",
      "standard_potential_V": "V",
      "potential_history[].time_s": "s",
      "potential_history[].temperature_K": "K",
      "potential_history[].standard_potential_V": "V",
      "potential_history[].potential_V": "V",
      "potential_history[].ln_reaction_quotient": "1",
      "electron_number": "1",
      "potential_history_sha256": "1"
    },
    "assumptions": [
      "Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.",
      "Reaction direction, activity standard state, species mapping and temperature applicability are reviewed caller inputs; this half-cell potential is not a mixed-potential or corrosion-rate calculation."
    ],
    "notes": [
      "This is a Nernst half-cell potential calculated from caller-supplied dimensionless activities and standard-potential history.",
      "It does not determine mixed potential, corrosion current, reaction kinetics, pH, activity coefficients, phase state, susceptibility, life or acceptance."
    ],
    "context": {
      "asset_id": "synthetic-loop",
      "location_id": "synthetic-crevice",
      "time_basis": "elapsed_seconds",
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
      ],
      "metadata": {}
    },
    "input_digest": "7d2e3570e304f11bf13c5f0c49707da63809f52eee375b7043ee2a4cba969f75",
    "source_ids": [
      "crevice_nernst_activity_potential"
    ],
    "qualification": "user_model",
    "runtime": {
      "matintegrity": "0.1.0.dev0",
      "python": "3.12.14",
      "numpy": "2.3.5",
      "pydantic": "2.14.1",
      "pint": "0.26.2",
      "scipy": "1.18.1",
      "rainflow": "3.2.0"
    },
    "probability_semantics": {}
  },
  "nernst_result_sha256": "58f940115892f5043263d60182c2df1b563ed0f725dd34075fc4242cdb364463",
  "reaction_id": "Fe3+_plus_e_to_Fe2+",
  "clock_id": "synthetic-elapsed-time",
  "equilibrium_potential_reference_id": "SHE",
  "electrode_potential_reference_id": "SHE",
  "electrode_potential_difference_history_V": [
    0.78,
    0.78,
    0.78
  ],
  "exchange_current_density_A_m2": 0.0001,
  "electron_number": 1,
  "anodic_transfer_coefficient": 0.5,
  "cathodic_transfer_coefficient": 0.5,
  "minimum_overpotential_V": -0.5,
  "maximum_overpotential_V": 0.5,
  "stoichiometric_species_coefficients": {
    "Fe3+": -1.0,
    "Fe2+": 1.0
  },
  "kinetics_provider_id": "synthetic-butler-volmer-provider",
  "kinetics_provider_revision": "1",
  "kinetics_calibration_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
  "redox_to_kinetics_mapping_reviewed": true,
  "reference_electrode_and_potential_basis_reviewed": true,
  "rate_parameter_and_temperature_applicability_reviewed": true,
  "reaction_direction_and_species_flux_basis_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-butler-volmer-provider",
      "origin": "synthetic",
      "citation": "Synthetic kinetic-provider wiring illustration only; not experimental data.",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/crevice_nernst_profile.py#L254)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
