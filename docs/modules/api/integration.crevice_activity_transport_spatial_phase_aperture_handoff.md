# `integration.crevice_activity_transport_spatial_phase_aperture_handoff`

**목적:** The activity-corrected reactive transport calculation is completed on a fixed, uniform initial slit geometry and exact caller clock.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_activity_transport_phase_aperture.v1", "default": "matintegrity.crevice_activity_transport_phase_aperture.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `activity_transport_request` | 예 | `{"$ref": "#/$defs/CreviceActivityReactiveTransportRequest"}` | 계약·필드 설명 참조 |
| `activity_transport_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `activity_transport_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `solid_kinetic_campaign` | 예 | `{"$ref": "#/$defs/CompetingSolidKineticTransport"}` | 계약·필드 설명 참조 |
| `initial_aperture_m_by_cell` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `cell_length_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `deposition_side_count` | 예 | `{"enum": [1, 2], "type": "integer"}` | 계약·필드 설명 참조 |
| `coverage_fraction_by_cell` | 예 | `{"items": {"type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `solid_molar_volume_m3_mol_by_phase` | 예 | `{"additionalProperties": {"exclusiveMinimum": 0, "type": "number"}, "type": "object"}` | 계약·필드 설명 참조 |
| `molar_volume_record_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `molar_volume_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_inventory_balance_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `relative_inventory_balance_tolerance` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_charge_balance_tolerance_mol_eq_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_charge_balance_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_match_relative_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0.0, "maximum": 1e-05, "type": "number"}` | 계약·필드 설명 참조 |
| `fixed_uniform_initial_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_and_kinetic_species_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rate_campaign_is_interval_extent_rate_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_volume_coverage_and_side_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sequential_split_and_next_segment_only_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_morphology_or_local_pit_claim_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceActivityTransportPhaseApertureRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `initial_aperture_m_by_cell[]` | `m` |
| `cell_length_m[]` | `m` |
| `solid_molar_volume_m3_mol_by_phase.*` | `m^3/mol` |
| `phase_inventory_history[].solid_inventory_mol_per_initial_cell_volume_m3_by_phase_and_cell.*[]` | `mol/m^3(initial liquid volume)` |
| `phase_inventory_history[].solid_volume_m3_by_cell[]` | `m^3` |
| `aperture_history[].equivalent_mean_remaining_aperture_m_by_cell[]` | `m` |
| `aperture_history[].covered_patch_remaining_aperture_m_by_cell[]` | `m` |
| `aperture_history[].phase_corrected_aqueous_concentration_mol_m3_by_species_and_cell.*[]` | `mol/m^3` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The activity-corrected reactive transport calculation is completed on a fixed, uniform initial slit geometry and exact caller clock.
- The solid kinetic campaign supplies explicit cellwise extent rates for each exact interval; rates are held constant over that interval.
- Aqueous species are adjusted by balanced solid reaction extents after each transport segment and checked against finite cell inventories.
- Phase volume is converted to per-cell equivalent gap using caller molar volumes, face count and coverage; no morphology is solved.
- The aperture output is for a subsequent segment and does not feed back into the source transport result.

## 구현 근거·독립 설명

- `caller_activity_corrected_reactive_transport_history`: Caller-provided digest-pinned activity-corrected reactive transport history on an exact fixed slit geometry and clock.
- `caller_cellwise_competing_solid_kinetic_rate_campaign`: Caller-provided interval extent-rate campaign for a finite declared set of solid phases and exact spatial cells.
- `caller_solid_molar_volume_and_deposition_coverage`: Caller-provided evidence-backed phase molar volumes and reviewed deposition coverage and face partition.
- `sequential_finite_volume_phase_inventory_to_slit_aperture_handoff`: Sequential finite-volume solid inventory and aqueous-balance handoff into a next-segment equivalent slit aperture; no morphology or in-interval transport feedback is solved.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_activity_transport_spatial_phase_aperture_handoff"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_activity_transport_phase_aperture.py#L206)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.
