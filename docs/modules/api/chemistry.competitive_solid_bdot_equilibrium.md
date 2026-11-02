# `chemistry.competitive_solid_bdot_equilibrium`

**목적:** The caller supplies temperature-matched, Evidence-linked extended Debye-Huckel A/B, ion-size and B-dot parameters for every phase species.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.competitive_solid_bdot_iteration.v1", "default": "matintegrity.competitive_solid_bdot_iteration.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium` | 예 | `{"$ref": "#/$defs/CompetitiveSolidEquilibrium"}` | 계약·필드 설명 참조 |
| `water_mass_per_solution_volume_kg_L` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `debye_huckel_A_at_temperature` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `parameter_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `temperature_match_tolerance_K` | 아니오 | `{"default": 0.01, "maximum": 5.0, "minimum": 0.0, "type": "number"}` | K |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `species_parameters` | 예 | `{"items": {"$ref": "#/$defs/BdotSpeciesParameter"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_supported_ionic_strength_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `charge_balance_tolerance_mol_kg` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/kg |
| `maximum_outer_iterations` | 아니오 | `{"default": 100, "maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `log_gamma_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `damping_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `water_mass_conversion_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_parameter_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_species_parameter_set_and_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `competing_solid_bdot_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `charge_scope_and_solver_settings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CompetitiveSolidBdotIteration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `ionic_strength_mol_kg` | `mol/kg` |
| `charge_balance_residual_mol_kg` | `mol/kg` |
| `activity_coefficient_by_species.*` | `1` |
| `Bdot_target_log10_gamma_molality_by_species.*` | `1` |
| `Bdot_target_gamma_molality_by_species.*` | `1` |
| `Bdot_target_gamma_molarity_by_species.*` | `1` |
| `molality_by_species_mol_kg.*` | `mol/kg` |
| `maximum_log_gamma_fixed_point_residual` | `1` |
| `outer_iterations` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies temperature-matched, Evidence-linked extended Debye-Huckel A/B, ion-size and B-dot parameters for every phase species.
- The caller owns species, complete phase set, Ksp values, water-mass conversion and charge review; ionic strength is limited to its declared parameter support.
- No species/phase discovery, precipitation kinetics, neutral-species salting or corrosion-rate qualification is inferred.

## 구현 근거·독립 설명

- `competitive_pure_solid_fixed_gamma_equilibrium`: Minimize the dimensionless ideal-mixing Gibbs potential for a closed fixed-volume aqueous species set and declared neutral solid phases with fixed activity coefficients. Extent constraints enforce aqueous nonnegativity and nonnegative final solid inventories; equilibrium is checked with phase saturation inequalities, complementarity residuals, and species extent balances.
- [USGS PHREEQC 3 documentation: LLNL extended Debye-Huckel B-dot activity model](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-26.htm) · `usgs_phreeqc_llnl_bdot_activity`
- `molality_to_molarity_activity_standard_state_bridge`: Map a molality-standard-state coefficient to a molarity-standard-state coefficient by equating the same dimensionless activity: gamma_c*c/(1 mol/L) = gamma_m*m/(1 mol/kg-water), with m=c/w and caller-supplied w in kg-water/L-solution, giving gamma_c=gamma_m/w. Require review of the water-mass conversion and standard-state mapping, preserve both coefficients, and fail closed outside finite numeric range. This algebraic basis does not infer solution water content or validate an activity model.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.competitive_solid_bdot_equilibrium"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/competitive_solid_bdot_iteration.py#L47)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
