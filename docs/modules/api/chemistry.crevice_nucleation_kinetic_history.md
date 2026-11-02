# `chemistry.crevice_nucleation_kinetic_history`

**목적:** Saturation is caller supplied and held constant over each exact interval.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_nucleation_kinetic_history.v1", "default": "matintegrity.crevice_nucleation_kinetic_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `kinetic_parameter_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `aqueous_species` | 예 | `{"items": {"$ref": "#/$defs/KineticAqueousSpecies"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_solid_phases` | 예 | `{"items": {"$ref": "#/$defs/KineticSolidPhase"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `nucleation_laws` | 예 | `{"items": {"$ref": "#/$defs/CreviceMolarNucleationLaw"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `growth_laws` | 예 | `{"items": {"$ref": "#/$defs/EvidenceBoundSaturationGrowthLaw"}, "maxItems": 16, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/NucleationSaturationInterval"}, "maxItems": 5000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 512, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_balance_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `relative_balance_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_total_nucleation_rate_mol_m3_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | mol/(m³·s) |
| `maximum_interval_phase_updates` | 아니오 | `{"default": 100000, "maximum": 500000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_ledger_evaluations` | 아니오 | `{"default": 100000, "maximum": 1000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_seed_threshold_splits_per_interval` | 아니오 | `{"default": 128, "maximum": 10000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `phase_stoichiometry_and_volume_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `saturation_source_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `nucleation_law_units_threshold_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `growth_law_temperature_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `dissolution_then_formation_split_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `closed_batch_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceNucleationKineticHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `intervals[].start_time_s` | `s` |
| `intervals[].end_time_s` | `s` |
| `intervals[].saturation_ratio_by_phase.*` | `1` |
| `nucleation_laws[].source_rate_constant_mol_m3_s` | `mol/m^3/s` |
| `nucleation_laws[].nucleated_inventory_threshold_mol_m3` | `mol/m^3` |
| `history[].aqueous_concentration_mol_m3.*` | `mol/m^3` |
| `history[].solid_inventory_mol_m3.*` | `mol/m^3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Saturation is caller supplied and held constant over each exact interval.
- Below the caller-declared phase seed inventory, a thresholded molar nucleation source is used; after the seed threshold is reached, the caller growth/dissolution law is used.
- Each interval's constant rates are applied through the existing dissolution-first, common aqueous-resource-limited ledger with element and charge checks.
- The nucleation source is expressed as moles of formed solid per solution volume per time, not nuclei count or a particle population balance.
- No automatic chemistry/phase discovery, moving geometry, spatial transport or qualification is included.

## 구현 근거·독립 설명

- `digest_bound_saturation_nucleation_and_growth_kinetic_history`: Apply Evidence-pinned caller saturation intervals and bounded phase-specific molar nucleation/growth/dissolution laws to a closed aqueous batch. Before a caller inventory threshold is met, evaluate the declared supersaturation-dependent nucleation source; thereafter use the caller seeded growth/dissolution law. Delegate each interval to the conservative aqueous/solid kinetic ledger and record phase inventory, element/charge balance and law digests. No automatic thermodynamic phase discovery, particle population balance or qualification is inferred.
- `caller_evidenced_crevice_molar_nucleation_source`: Define an Evidence/digest-bound caller-calibrated nucleation molar source with critical supersaturation, source coefficient, order, phase inventory seed threshold and rate ceiling. The record is a caller law, not a universal nucleation model or particle-number theory.
- `caller_rate_competitive_solid_mass_balance_ledger`: Apply explicitly supplied signed molar extent rates for a caller-declared set of neutral solid phases over contiguous time intervals. Limit dissolution by available phase inventory, then limit simultaneous precipitation with one common aqueous-reactant factor that preserves the supplied phase-rate ratios. Verify each declared reaction's charge and elemental stoichiometry and report time-resolved dissolved and solid inventories with balance residuals. This is conservative bookkeeping for user-supplied rate outputs; it does not estimate kinetic laws, phase selection, saturation, scale morphology or corrosion protection.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "chemistry.crevice_nucleation_kinetic_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_nucleation_kinetic_history.py#L175)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
