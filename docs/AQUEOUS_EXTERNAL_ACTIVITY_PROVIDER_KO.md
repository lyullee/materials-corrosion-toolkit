# 외부 조성 의존 활동도 provider 연결

`ExternalAqueousActivityIteration`와 `aqueous_external_activity_self_consistent_speciation()`은 caller가 보유한 Python 활동도 라이브러리를 기존 수용액 질량작용 solver에 연결한다. 프로젝트는 provider 코드를 import하거나 실행하지 않는다. 호출자는 composition 입력을 받아 종별 molality-standard-state 활동도 계수를 반환하는 callback을 직접 제공한다.

## Callback 계약

각 반복에서 callback은 다음 입력을 받는다.

- 절대온도, 정확한 ordered species ID와 전하수
- 각 종의 molality 및 그 complete inventory에서 계산한 ionic strength
- 용액 부피당 물 질량과 molality standard-state ID
- caller가 정한 single-ion activity convention ID

응답은 JSON 기본형(숫자/문자열/불리언/null, 배열, 객체)으로 표현해야 digest 재현이 가능하다. `status="computed"`, provider ID/revision, configuration·parameter-record SHA-256, 입력의 `request_sha256`, 정확히 일치하는 species ID 순서, molality 기준 gamma vector와 ionic strength를 포함해야 한다. 필수 응답 필드가 없거나 숫자 값이 유효하지 않으면 `needs_data` 또는 fail-closed 상태로 종료한다. 누락·순서변경·digest 불일치·ionic-strength mismatch는 평형 결과로 승격하지 않는다. Provider는 선택적으로 osmotic coefficient 및 water activity를 반환할 수 있다. 수치 출력이 아니라면 이 필드는 생략한다.

`aqueous_external_activity_self_consistent_speciation(request, activity_provider=callback)`은 응답의 gamma_m을 질량작용기의 1 mol/L 표준상태에 맞게 `gamma_c = gamma_m / w`로 변환한다. `w`는 caller가 제공하고 검토한 kg-water/L-solution이다. 기존 mass-action solver에서 해당 gamma를 사용해 평형을 풀고, 결과 molality로 provider를 다시 호출한다. 로그 gamma의 잔차가 caller tolerance 안에 들 때만 `computed`를 반환한다. 반복별 callback request/result digest와 내부 solver 잔차를 기록하고 예산 소진 또는 provider 실패 시 마지막 미수렴 상태를 평형 결과로 반환하지 않는다.

## 적용성·계보 review

요청은 parameter record가 provider Evidence와 정확히 맞아야 한다. 물 질량 및 표준상태 환산, 온도/parameter 지원범위, 완전 종 목록과 전하 균형, provider 단위·species 순서, single-ion convention, parameter coverage, callback 결정성, fixed-point 설정과 single-liquid/no-precipitation 가정을 각각 검토한다. Response digest는 내용 무결성 연결값이지 provider의 진위 인증은 아니다. Single-ion gamma convention은 모델별로 달라질 수 있으므로 그 ID와 적합성 review를 명시한다.

## Pitzer 등 외부 라이브러리

사용자는 Pitzer 구현 등 선택한 provider를 별도 환경에서 사용하고, 프로젝트 API 규격으로 callback을 감싸면 된다. Provider별 API·parameter library·revision·license·parameter coverage 검토는 caller 책임이다. 현재 upstream Pytzer 문서는 해당 패키지를 beta 및 GPLv3로 표시하므로 이 프로젝트는 설치 의존성이나 코드를 배포물에 넣지 않는다. Pytzer를 선택하는 사용자는 별도 설치·실행에 적용되는 라이선스와 parameter-data 권리를 직접 확인하고 provider/configuration/record digests를 고정해야 한다. [Pytzer upstream documentation](https://pytzer.readthedocs.io/en/develop/); source boundary 기록은 `data/catalogs/sources.json`의 `pytzer_optional_gpl_provider_metadata`를 따른다.

`examples/aqueous_external_activity_provider.py`는 identity-gamma synthetic callback으로 배선 형식만 보여준다. 이 예제는 electrolyte property, Pitzer output, chemistry calibration 또는 numerical verification이 아니다. Callback 모드의 실제 사용 전 독립 reference solution과 experimental validation을 별도 수행해야 한다.


## 정확한 절점 시간·온도 이력

`ExternalAqueousActivityHistory`와 `aqueous_external_activity_speciation_history()`는 기존 단일 상태 API를 사용해 각 caller 지정 시간 절점에서 독립적으로 self-consistent speciation을 계산한다. 요청은 시각이 0에서 시작하는 엄격 증가 시계와 절점별 온도/질량작용 파라미터 record를 요구한다. 종 ID·전하·formula, 반응 화학량론, constraint topology와 provider ID/revision/configuration/single-ion convention은 전체 절점에서 동일해야 한다. 평형상수, 활동도 parameter record, 물 질량 및 초기 활동도는 절점별로 달라질 수 있으며 각 request의 Evidence와 digest가 그대로 남는다.

이력 API는 절점 사이에서 시간, 온도, 평형상수, gamma 또는 조성을 보간하지 않는다. 사용자는 정확한 실험/운전 시각에 해당하는 모든 knot별 system을 제공하고 temperature/parameter mapping을 검토해야 한다. 어느 한 절점에서 review가 빠지거나 callback이 수렴하지 않으면 해당 절점에서 중단하고 이전 계산 결과는 diagnostic prefix로만 반환한다. 이는 시간 의존 kinetic/transport 해석이 아니며 전체 history status를 `computed`로 승격하지 않는다.


## Restricted transport 활동도 callback

`ExternalAqueousTransportActivity`와 `build_external_aqueous_transport_activity_callback()`는 `RestrictedTransportRequest`에 넘길 activity coefficient 함수다. 입력 농도는 기존 transport API 규약대로 종×(mouth + cells) 행렬의 mol/m³이며, callback은 각 공간 상태별로 `/1000/w`를 적용해 molality를 계산하고 전하 인벤토리에서 ionic strength를 구한다. 지원범위·단위·species 순서가 맞으면 외부 provider에 JSON 조성 request를 보내고, request digest, provider 계보, ordered species, ionic strength가 일치하는 molality-standard-state gamma를 반환한다. 이 callback을 연결할 때 transport request의 `species_ids` 순서는 callback 계약과 같아야 하며 `activity_provider_id`와 `activity_configuration_sha256`에는 callback의 대응 속성을 지정한다. solver 진입 시 species order와 provider ID/configuration digest를 확인한다. provider 예외나 유효하지 않은 gamma shape/value가 적분 중 발생하면 raw exception 대신 `out_of_scope`와 sanitized error type, 실패 구간 정보를 반환한다.

Callback은 provider 실행 횟수와 입력/응답 digest chain을 `runtime_trace`에 누적하며, `solve_restricted_transport()`의 반환 lineage에 이 runtime trace가 포함된다. 고정 설정 digest는 불변 configuration field만 대상으로 하고, runtime trace 안의 transcript digest가 실제 callback 순서를 연결한다. transport 단계마다 수치 solver가 호출하는 조성에서 활동도를 평가하므로 비용은 provider 속도와 적분 solver 호출 수에 좌우된다. 이 경로는 고정 온도·고정 용매질량 변환과 caller가 선언한 단일 액상 범위에 한정된다. 유동·확산 solver가 활동도 callback을 반복 호출하는 것만으로 국소 평형, speciation, 침전, 전하 균형, 상변화 또는 전기화학 반응을 풀지는 않는다.
