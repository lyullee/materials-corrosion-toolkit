# `integration.wet_co2_scale_diffusion_electrode_mixed_potential`

**목적:** At each caller time knot, a one-dimensional steady finite-volume reactant balance inside a fixed scale is solved simultaneously with one common mixed potential.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_scale_diffusion_electrode_mixed_potential.v1", "default": "matintegrity.wet_co2_scale_diffusion_electrode_mixed_potential.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `knots` | 예 | `{"items": {"$ref": "#/$defs/ScaleDiffusionElectrodeKnot"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `fixed_geometry_patch_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `finite_volume_and_first_order_sink_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_metal_potential_and_no_ohmic_drop_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `steady_state_at_each_knot_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2ScaleDiffusionElectrodeHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history[].time_s` | `s` |
| `history[].temperature_K` | `K` |
| `history[].scale_thickness_m` | `m` |
| `history[].mixed_potential_V` | `V` |
| `history[].cell_concentrations_mol_m3[]` | `mol/m^3` |
| `history[].wall_concentration_mol_m3` | `mol/m^3` |
| `history[].cathodic_current_density_A_m2_by_reaction.*` | `A/m^2` |
| `history[].anodic_current_density_A_m2_by_reaction.*` | `A/m^2` |
| `history[].wall_reactant_consumption_mol_m2_s` | `mol/m^2/s` |
| `history[].bulk_to_scale_diffusive_flux_mol_m2_s` | `mol/m^2/s` |
| `history[].distributed_first_order_reaction_consumption_mol_m2_s` | `mol/m^2/s` |
| `history[].reactant_mass_balance_residual_mol_m2_s` | `mol/m^2/s` |
| `history[].metal_loss_flux_mol_m2_s_by_reaction.*` | `mol/m^2/s` |
| `history[].total_uniform_wall_recession_rate_m_s` | `m/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- At each caller time knot, a one-dimensional steady finite-volume reactant balance inside a fixed scale is solved simultaneously with one common mixed potential.
- Scale consumption is a caller-defined first-order volumetric sink; cathodic Butler-Volmer branches consume the same declared species in proportion to wall concentration.
- The caller provides all electrochemical and transport parameters, temperature, root bracket, stoichiometry, and evidence; no parameter fitting or thermodynamic inference is performed.

## 구현 근거·독립 설명

- `caller_scale_reaction_diffusion_transport_parameters`: Caller-supplied scale thickness, temperature, diffusivity, sink rate, reactant boundary and kinetic parameters with explicit record provenance.
- `caller_scale_anodic_butler_volmer_branches`: Caller-defined anodic electrode branches and metal stoichiometry; no empirical branch parameters are bundled.
- `caller_scale_cathodic_butler_volmer_branches`: Caller-defined cathodic Butler-Volmer branches linked to caller-identified transported reactants.
- `caller_scale_reactant_and_metal_stoichiometry`: Caller-reviewed reactant and metal reaction-extent mapping for the declared electrochemical branches.
- `finite_volume_scale_first_order_sink_with_butler_volmer_mixed_potential`: Independent steady finite-volume first-order reactant sink coupled to a bounded common mixed-potential root solve.
- `butler_erdey_gruz_volmer_electrode_kinetics`: Independently implemented Butler-Volmer kinetic relation with caller-defined branch parameters; applicability is not externally qualified.
- `nist_codata_faraday_constant_2022`: CODATA Faraday constant used as an exact conversion constant; no source data table or prose is reproduced.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_scale_diffusion_electrode_mixed_potential"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'scipy': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_scale_diffusion_electrode.py#L390)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
