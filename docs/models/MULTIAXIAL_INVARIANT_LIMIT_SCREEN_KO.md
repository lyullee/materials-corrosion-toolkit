# 다축 불변량 한계 스크리닝

## 목적

`matintegrity.multiaxial_invariant_limit_screen`은 caller가 보정한 계수와 한계값을 사용해, 검토된 닫힌 응력주기의 두 유한표본 불변량을 선형 결합하고 한계와 비교한다. 이 API는 매개변수를 자동 추정하거나 표준의 재료상수를 내장하지 않는다. 결과는 caller limit에 대한 결정론적 비교다.

## 계산 정의

입력 주기 표본은 `SampledStressInvariantHistory` 계약을 따르며, 모듈은 그 결과에서 최대 표본 정수압 응력과 최대 pairwise 편차응력 `sqrt(J2)` 거리의 반값을 읽는다. caller가 제공하는 두 계수를 각각 \(a\), \(b\)라 할 때 계산은 다음 형태다.

\[
P = a\,R_{J2,\mathrm{sample}} + b\,\sigma_{H,\max,\mathrm{sample}}
\]

여기서 \(R_{J2,\mathrm{sample}}\)은 주어진 이산 편차응력 표본에서의 최대 pairwise 거리 / 2이고, \(\sigma_{H,\max,\mathrm{sample}}\)은 표본에서 계산한 최대 정수압 응력이다. 비교 여유는 `caller_limit_Pa - P`로 정의한다. 이 유한표본 규약을 피로기준의 연속 진폭이나 다른 진폭 산정법과 동일하다고 간주하지 않는다.

## 입력 및 계보

- nested 응력 이력 전체의 canonical SHA-256을 `stress_history_sha256`에 지정해야 한다.
- 보정 ID·원본 ID·SHA-256 및 그 SHA와 일치하는 `Evidence`를 요구한다.
- 보정의 material-condition ID는 응력 이력의 material-condition ID와 정확히 같아야 한다.
- 편차응력 계수는 양수, 정수압 계수는 0 이상, 한계 응력은 양수로 제한한다.
- 계수/한계, 재료 적용 범위, 이 유한표본 규약의 사용을 caller가 명시적으로 검토해야 계산한다. 검토가 빠지면 `needs_data`를 반환한다.
- 응력 이력이 미검토이거나 유한 표본 한계를 넘으면 nested descriptor의 `needs_data` 또는 `out_of_scope` 경계를 이어받는다.

## 반환값과 해석

`screening_parameter_Pa`, `margin_to_caller_limit_Pa`, caller limit의 초과 여부와 witness sample IDs를 반환한다. `caller_limit_not_exceeded`는 지정한 값과 유한표본 규칙 아래의 비교 결과일 뿐, 설계 허용, 표준 적합, 재료 자격, 피로수명, 고장확률 또는 안전을 의미하지 않는다.

입력된 응력 표본 사이의 보간이나 시간 경로를 생성하지 않고, cycle counting, 재료 계수 fitting, uncertainty propagation, 다중주기 누적손상도 수행하지 않는다. caller 한계가 한 번의 표본 주기 범위에만 적용되는지, 어떤 하중 모집단과 환경에 유효한지는 별도로 검토해야 한다.

## 카탈로그 출처 문구 제안

`caller_finite_sample_multiaxial_invariant_limit_screen`: caller가 제공한 유한 응력 표본의 최대 정수압 응력과 최대 pairwise 편차응력 `sqrt(J2)` 거리의 절반을 명시적 계수로 선형 결합하고, 같은 재료 조건에 대해 제공된 한계와 결정론적으로 비교한다. 계수·적용성은 caller 보정과 검토를 요구하며 표본 간 보간, 수명 또는 qualification을 도출하지 않는다.
