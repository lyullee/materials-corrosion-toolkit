# `integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history`

**목적:** Each point requires one computed and digest-verified Henry temperature-correction AssessmentResult and one aligned carbonate-equilibrium input.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | s |
| `knot_requests` | 예 | `{"items": {"$ref": "#/$defs/Co2HenryCarbonateAdapterRequest"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `history_clock_and_sample_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `all_points_must_compute_before_commit` | 아니오 | `{"default": true, "type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_point_evaluations` | 아니오 | `{"default": 20000, "maximum": 20000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/Co2HenryCarbonateHistoryAdapterRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `temperature_K_history[]` | `K` |
| `henry_coefficient_mol_L_Pa_history[]` | `mol/L/Pa` |
| `ph_activity_history[]` | `1` |
| `co2star_mol_L_history[]` | `mol/L` |
| `hco3_mol_L_history[]` | `mol/L` |
| `co3_mol_L_history[]` | `mol/L` |
| `point_count_computed` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each point requires one computed and digest-verified Henry temperature-correction AssessmentResult and one aligned carbonate-equilibrium input.
- Target temperature, mol/L/Pa convention, solvent digest, upstream provider/revision/configuration and reference/result digests are checked at every exact knot.
- The history uses exact caller order and complete-only aggregate semantics; it stops at the first failure and returns only the successful prefix plus the failure.
- No inter-knot temperature or solvent interpolation, Henry extrapolation, full aqueous composition, general reaction-network speciation, corrosion rate, scale or acceptance is inferred.

## 구현 근거·독립 설명

- `caller_ordered_co2_henry_carbonate_history`: Apply the digest-verified Henry-to-carbonate adapter once at each exact, strictly ordered caller time knot. Require a matching computed Henry-correction AssessmentResult, point input, target temperature, solvent identity and RunContext at each knot. Stop at the first failed point and retain only its successful prefix; do not interpolate or extrapolate temperature, solvent composition or Henry coefficients, and do not represent the carbonate subsystem as full aqueous speciation.
- `caller_reviewed_co2_henry_carbonate_handoff`: Adapt a digest-verified CO2* Henry temperature-correction result to the existing carbonate-only fixed-fugacity equilibrium calculation. Require exact agreement of upstream result/model/input and output digests, coefficient convention and unit, target temperature, solvent digest, provider revision/configuration and reference-record digest. The downstream solver covers a carbonate subsystem only; no other aqueous species, complete solution charge balance, multiphase network, reaction kinetics or corrosion rate is inferred.
- `caller_co2_henry_vant_hoff_thermochemistry`: Apply the integrated van't Hoff temperature correction to a caller-supplied CO2* Henry solubility coefficient using caller dissolution enthalpy and optional constant heat-capacity difference. Preserve solvent identity, reference/target temperature support, parameter record digest and Evidence. No Henry coefficient, thermochemical table, fugacity, speciation, corrosion rate or acceptance value is embedded or inferred.
- [IDAES: Equilibrium Constant Forms — van 't Hoff equation](https://idaes-pse.readthedocs.io/en/2.13.0/explanations/components/property_package/general_reactions/equil_constant.html) · `idaes_van_t_hoff_equilibrium_constant`
- [NIST CODATA 2022: molar gas constant](https://physics.nist.gov/cgi-bin/cuu/Value?r%7Csearch_for=R) · `nist_molar_gas_constant`
- [USGS PHREEQC 3 documentation: gas-phase Henry solubility and fixed-pressure/fixed-volume boundaries](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-17.htm) · `usgs_phreeqc_gas_liquid_equilibrium`
- [USGS advanced carbonate and bicarbonate speciation method](https://water.usgs.gov/water-resources/memos/memo.php?id=2098) · `usgs_advanced_carbonate_speciation`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/co2_henry_carbonate_history_adapter.py#L62)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
