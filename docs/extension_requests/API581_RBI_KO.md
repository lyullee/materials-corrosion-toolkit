# api581-risk-analysis 연동 확장 요청

## 확인 범위

2026년 10월 28일 GitHub 공개 API에서 `lyullee/api581-risk-analysis`의 `main` commit
`7c8badb829f84b19c7b84d07fbc476601d9194eb`을 읽기 전용으로 확인했다. 저장소는 damage, thinning,
inspection effectiveness, probability of failure, consequence와 risk API를 별도 모듈로 두며 JSON schema와
Nurion 실행 경로를 갖는다. `LICENSE` 첫 줄은 Apache License다. 이 확인은 해당 구현이나 공학 결과의
자격화를 뜻하지 않는다.

## 요청할 중립 교환 계약

MatIntegrity에서 RBI 저장소로 보내는 record는 다음을 포함해야 한다.

- asset/component/location와 평가 horizon, 공통 clock 및 pressure basis
- damage mechanism ID와 사람이 검토 가능한 정의
- 현재 wall/flaw/material state, 단위, uncertainty, support와 source result digest
- inspection method, coverage, calibration/POD identity와 inspection date
- 계산 상태 `computed/needs_data/out_of_scope` 및 누락·범위초과 사유
- MatIntegrity model ID/version, configuration/input/result SHA-256와 evidence ID

RBI 저장소에서 되돌려 받을 record는 다음을 분리해야 한다.

- thinning/damage factor와 PoF를 동일 값으로 취급하지 않는 명시적 semantics
- PoF가 기간 최초고장확률인지, 연율·범주·상대점수인지 구분
- consequence category별 단위·통화 기준시점·discount convention
- inspection action별 residual probability를 반환할 경우 baseline과 같은 event/scope/horizon/conditioning
- 사용한 damage/provider revision, standard applicability 상태와 완전한 input/result digest

## 금지할 자동 변환

- MatIntegrity의 descriptive screen 또는 `partial` capability를 API 581 damage factor로 승격
- thickness mean만으로 결함 형상·COV·inspection effectiveness를 생성
- POD, spatial exceedance, damage factor 또는 generic frequency를 기간 최초고장확률로 재명명
- 서로 다른 pressure basis, component scope, horizon 또는 consequence currency year의 결과 결합
- 상대 저장소가 포함한 표·계수를 MatIntegrity의 독립 구현 근거로 복제

## 완료 조건

1. 상대 저장소가 위 필드를 가진 versioned JSON export/import를 제공한다.
2. 고정 commit과 양쪽 schema digest로 round-trip을 재현한다.
3. computed, needs-data, out-of-scope와 identity mismatch를 양쪽에서 모두 검사한다.
4. 동일 작성 fixture를 양쪽에서 계산했을 때 값뿐 아니라 probability semantics와 source tree를 비교한다.
5. 실제 규격 적용성·물리 검증·소프트웨어 계약 검증을 서로 다른 기록으로 남긴다.

현재 MatIntegrity는 `AssessmentResult`, `EventProbability`, `ActionEventProbabilityEvaluation`,
`InspectionRecord`와 `PipelineAssessmentRecord`를 재사용할 수 있지만, API 581 damage-factor 전용 record는
아직 만들지 않았다. 실제 상대 저장소 확장 뒤 최소 공통 필드만 별도 계약으로 추가한다.

## 2026-10-31 addendum — digest-bound remaining-thickness history evidence

### Target and reason

Target: `lyullee/api581-risk-analysis`, pinned reviewed commit `7c8badb829f84b19c7b84d07fbc476601d9194eb` in `data/catalogs/github_integrations.json`. The repository remains an external read-only target; this request does not claim that its source was changed or that consumer execution occurred.

MatIntegrity now exposes `corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness` in `src/matintegrity/ti12mo5zr_remaining_thickness.py`. It binds an AESEC metal-balance AssessmentResult, digest and run context to caller baseline-thickness evidence, then reports provider-time knots for positive, negative and signed-equivalent penetration and remaining thickness. Its explicit scope is uniform area-average loss; it is not a localized thickness map, future corrosion forecast, failure probability or acceptance result. A receiving RBI tool needs a typed evidence intake that preserves that distinction.

### Requested versioned exchange

Add an optional `matintegrity_wall_state_history.v1` evidence record to the recipient's digital-twin or component-assessment input. It is additive and must not change behavior for callers that omit it. Proposed JSON shape:

```json
{
  "schema_version": "matintegrity_wall_state_history.v1",
  "evidence_id": "caller-assigned-id",
  "asset_id": "caller-asset-id",
  "component_id": "caller-component-id",
  "location_id": "caller-location-id",
  "material_condition_id": "caller-reviewed-condition",
  "metric_id": "uniform_equivalent_remaining_thickness",
  "spatial_scope": "uniform_area_average_only",
  "time_basis": {"clock_id": "caller-clock", "unit": "s", "origin": "provider_time_s"},
  "source": {
    "model_id": "corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness",
    "source_model_id": "corrosion.ti12mo5zr_aesec_signed_equivalent_penetration",
    "dataset_id": "zenodo-ti12mo5zr-aqueous-corrosion",
    "archive_sha256": "64 lowercase hex characters",
    "member_sha256": "64 lowercase hex characters",
    "assessment_input_sha256": "64 lowercase hex characters",
    "assessment_result_sha256": "64 lowercase hex characters",
    "history_sha256": "64 lowercase hex characters"
  },
  "baseline": {
    "thickness_m": 0.01,
    "measurement_evidence_id": "caller-evidence-id",
    "measurement_evidence_sha256": "64 lowercase hex characters"
  },
  "knots": [
    {
      "provider_time_s": 0.0,
      "remaining_thickness_m": 0.01,
      "cumulative_positive_penetration_m": 0.0,
      "cumulative_negative_penetration_m": 0.0,
      "cumulative_signed_net_penetration_m": 0.0,
      "source_row_number": 2,
      "source_row_sha256": "64 lowercase hex characters"
    }
  ],
  "status": "computed",
  "interpretation_limit": "uniform equivalent thickness; not localized wall state"
}
```

The example is a shape illustration only; it contains no project measurement and is not a valid qualification record. The receiver should preserve every source knot and digest, reject duplicate or non-increasing time, bind its own component/location/material condition and assessment horizon, and keep the three penetration ledgers separate. The baseline evidence is caller-owned; the dataset license does not grant rights to caller measurements.

### Receiver behavior and failure statuses

- `computed`: accept the record only as a digest-bound state-history evidence item. If an existing RBI method consumes it, echo the exact evidence ID and history digest in that method's input/result lineage.
- `needs_data`: preserve the unresolved record when asset/component/location, material condition, clock, baseline evidence or required caller scope review is missing. Do not substitute the latest value or another component.
- `out_of_scope`: reject promotion to localized thinning, crack dimensions, future corrosion rate, remaining life, API 581 damage factor or period probability unless a separate, explicitly applicable and validated method supplies that mapping.
- Upstream `needs_data` or `out_of_scope`: preserve that exact source status and reason and do not synthesize wall values.

The consumer must not recalculate the source penetration from the workbook or alter its sign convention. It must not infer corrosion mechanism, missing knots, operating time, inspection interval, thickness uncertainty, material density, required thickness or code acceptance.

### Acceptance criteria for a future implementation

1. Validate the payload against a versioned JSON schema and the pinned source IDs; reject altered history/assessment digests and mismatched dataset/member provenance.
2. Round-trip a complete synthetic fixture and a real, locally authorized fixture without sorting, interpolation, dropping rows or changing SI units; compare the returned history digest exactly.
3. Exercise missing baseline Evidence, material/location mismatch, duplicate/reversed knots, non-computed upstream status, and a request to use the uniform metric as a localized state; fail closed with the statuses above.
4. If the consumer calculates damage factor or PoF, require its own code-specific applicability, component geometry, inspection and time-horizon inputs. Compare those calculations separately; do not validate them by matching the transferred thickness values alone.
5. Record the recipient commit, schema hash, input/output hashes and consumer execution receipt. Until that receipt exists, integration status remains `not_run` and qualification remains `not_claimed`.

### Rights and maintenance

Only the MatIntegrity source record ID, dataset DOI/rights metadata and SHA-256 lineage should travel. Do not copy the provider workbook, worksheet cells, calibration tables or recipient-repository content into the other repository. Recheck the target commit/schema digest and the dataset rights record before implementation.
