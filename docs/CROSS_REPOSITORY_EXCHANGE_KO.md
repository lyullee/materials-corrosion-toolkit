# 타 저장소 중립 교환 계약

기준일은 2026년 10월 28일이다. 이 계약들은 MatIntegrity와 독립 저장소 사이의 JSON 경계를
고정한다. 상대 저장소 코드를 import·복제하지 않으며, 계약 검증을 상대 모델 실행이나 물리 검증으로
표시하지 않는다.

## API 581 damage exchange

`matintegrity.api581_exchange`의 `Api581DamageExchangeRecord`는 asset/component/location/scope/horizon,
damage mechanism 정의, wall/flaw/material state, inspection lineage와 provider/model/configuration/input/
result digest를 보존한다. `computed`, `needs_data`, `out_of_scope`의 값 허용 범위가 다르다.

PoF는 사건 정의와 `conditional_first_failure_in_period` 의미가 있을 때만 기록한다. POD는
`detection_given_flaw_and_procedure`, 공간 확률은 `spatial_size_exceedance_at_one_exposure`로 따로
보존한다. Damage factor, POD 또는 공간 확률을 PoF로 변환하지 않는다.

## Consequence scenario exchange

`matintegrity.consequence_exchange`는 process state, composition, pressure absolute/gauge basis, temperature
basis, clock/horizon, event probability semantics, release geometry와 source/release/dispersion/effect model
identity를 갖는 handoff를 만든다. 결과는 receptor/location/time과 quantity/unit/uncertainty를 단계별로
보존하고 요청 단계 identity 및 scenario completeness를 교차검사한다.

Wall loss를 opening area로, consequence를 failure probability로 자동 변환하는 flag는 계약상 항상
거짓이다. Opening geometry나 release history는 별도 자격 있는 provider가 제공해야 한다.

## Compatibility receipt

`matintegrity.exchange_receipt`의 deterministic builder는 producer/consumer repository·schema·revision,
canonical payload SHA-256, configuration digest, 필수 schema/unit/identity/probability-semantics check와
accepted/rejected RFC 6901 path를 기록한다. JSON key 순서가 바뀌어도 같은 payload는 같은 receipt를
만든다.

Receipt는 전자서명, 네트워크 전송, 상대 저장소 실행 또는 공학 검증이 아니다. 실제 end-to-end 완료는
고정 consumer commit에서 동일 payload를 읽고 consumer result/receipt digest까지 되돌려 받은 별도
불변 기록이 있어야 한다.

## 고정 대상과 재개

`data/catalogs/github_integrations.json`은 현재 두 공개 대상의 reviewed commit, license evidence,
관찰한 public contract 경로와 요청서를 기록한다. `scripts/inspect_github_integration_catalog.py`는
네트워크 없이 commit 형식, 요청서 존재와 미실행·미자격화 상태를 검사한다. 원격 변경이 있으면 기존
record를 덮어쓰지 말고 새 reviewed commit과 검토일을 기록한 뒤 schema diff를 수행한다.

## Pinned schema adapter

API 581 대상의 고정 `docs/python-api.schema.json`에서 `frequency/pof-method-selection`은 `method`,
`qualification_basis`, `uncertainty_quantified`만 받는 closed input이다. 외부 numeric PoF를 넣을 필드가
없으므로 `api581_pinned_method_selection_request`는 숫자를 전송하지 않고, caller가 이 제한을 명시적으로
승인해야 한다. Damage factor·POD·spatial probability가 섞인 record는 거절한다.

Consequence 대상의 고정 `ccps.provider_request.v1`은 required top-level field와
`additionalProperties=false`를 사용한다. `export_pinned_provider_request`는 정확한 외형을 만들고, 상대
schema에 없는 pressure/composition/clock/horizon/event semantics와 release basis는 허용된
`settings.matintegrity_handoff_v1` 아래 원 record와 digest로 보존한다. Constant source rate·duration·mass는
별도 caller/provider 입력이며 wall loss에서 만들지 않는다.

`ExternalSchemaAuditRecord`는 raw schema 원문 대신 URL, commit, path, byte SHA-256, schema ID/version,
required/property 목록과 additional-properties 정책만 보존한다. 원문 다운로드나 상대 저장소 실행은
builder 밖의 명시적 작업이며 audit record는 schema 또는 물리모델 자격화가 아니다.

## 실제 schema validation과 제외 캐시

`validate_pinned_method_selection_request`와 `validate_pinned_provider_request`는 caller가 제공한 raw schema
bytes를 먼저 고정 SHA-256에 대조하고 실제 request JSON을 검증한다. 현재 환경에 `jsonschema`가 없으면
각 모듈이 선언한 제한된 독립 validator를 사용하고 그 engine ID를 report에 남긴다. Required,
additional-properties, enum, pattern, format와 request digest 불일치는 성공으로 완화하지 않는다.

`build_pinned_exchange_validation_receipt`는 external-schema audit identity, payload digest, schema/unit/
identity/probability-semantics finding을 기존 compatibility receipt로 묶는다. Schema 통과는 consumer 실행,
end-to-end 통합 또는 물리 자격화가 아니며 관련 flag는 항상 거짓이다.

`scripts/fetch_pinned_external_schemas.py`는 catalog의 URL에서 원문을 받아 expected SHA-256이 일치할 때만
`artifacts/external-schemas`에 atomic write한다. 이 디렉터리는 git·Ruff·release에서 제외된다. 현재
5개 파일 2,752,029바이트를 검증했으며 공개되는 것은 `validation/pinned_external_schema_fetch.json`의
경로·commit·hash·크기 기록뿐이다.

## 고정 consumer 실행

`scripts/validate_pinned_consumers.py`는 두 저장소를 `artifacts/external-repositories` 제외 영역에 고정 commit으로 checkout한 뒤 상대 저장소의 실제 Python 클래스를 import한다. API 581에서는 MatIntegrity의 closed method-selection request를 `api581.api.frequency.PofMethodSelectionInput`으로 다시 검증하고 `pof_method_selection` 계산을 실행했다. 이어 caller가 검토한 GFF·management factor·damage factor와 기간을 명시적으로 전달해 실제 `frequency/adjusted`와 `reliability/poisson-probability`를 실행했다. 합성 경로의 연간빈도는 `0.0001/year`, 1년 확률은 `9.99950001666625e-05`이며 독립 Poisson 식과 대조했다. 손상계수는 자동 추정하지 않으며 일정위험률 가정, 합성 입력, 비자격화 상태를 receipt에 보존한다.

Consequence 저장소에서는 `export_pinned_provider_request`의 JSON을 `ccps_consequence.integrations.ProviderRequest`로 다시 검증했다. 먼저 synthetic bound provider로 상대 저장소의 request/result digest·engine·model·code digest·receptor·quantity·evidence binding을 검사했다. 이어 `run_pinned_ccps_native_plume`가 loaded code digest를 고정하고 상대 저장소의 실제 `calculate("dispersion/plume")`를 호출한 뒤 `evaluate_provider` binding까지 수행했다. 풍속, sigma, crosswind, release/receptor height와 적용성은 모두 caller가 공급하며 자동 기상모델이나 fallback은 없다. 합성 검증 농도는 `0.002546479089470325 kg/m³`였고 현장 예측·물리 검증·qualification이 아니다. 재현 결과는 `validation/pinned_consumer_execution.json`에 있으며 checkout 원문과 Git history는 공개 배포에서 제외된다.
