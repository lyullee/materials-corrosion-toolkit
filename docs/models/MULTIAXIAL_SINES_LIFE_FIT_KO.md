# 유한표본 Sines parameter–수명 곡선 적합

`fatigue.multiaxial_sines_life_fit`은 caller가 제공한 같은 재료조건의 다축 피로시험들에서 유한표본 Sines형 parameter를 계산하고, 파손 cycle 수와 로그-로그 power relation을 적합한다. 시편·원자료 계보를 보존하며 적합 모형의 적용구간을 관측 parameter 범위에 한정한다.

## 입력과 적합

각 시험은 고유한 test ID, 물리 시편 ID, source group 및 source record ID, 실제 파손 cycle 수, 원 관측 Evidence와 `MultiaxialSinesMeanLimitScreen` 계약을 제공한다. 시편별 screen은 동일한 재료조건, 계수·한계, 보정 source 및 digest를 사용해야 한다. 원 관측은 측정 또는 오픈 데이터 근거여야 하고 Evidence의 해시가 필수다.

적합식은 caller가 검토한 다음 형태다.

\[
\ln(N_f)=c+m\ln(P/P_0), \qquad P_0=1\ \text{MPa}
\]

여기서 (P)는 중첩 Sines screen에서 나온 유한표본 parameter이며 (N_f)는 caller 파손 cycle 수다. 가중치를 두지 않은 최소제곱으로 (c,m)을 계산한다. 정상적인 감소 수명 곡선을 위해 적합 기울기 (m<0)을 요구한다.

## 적용 조건과 해석

- 최소 세 시험에서 서로 다른 양의 parameter가 필요하다. curve 보간이 아니라 이 caller 시험들의 로그-로그 관계를 적합하므로, (R^2)와 잔차는 calibration 표본 설명값으로 반환한다.
- 각 시험은 별도 물리 시편이어야 한다. 시편 독립성, 실패 끝점 일치, 시험조건·권리 검토를 명시적으로 확인하지 않으면 계산은 `needs_data`다.
- `source_group_id`를 보존하지만 같은 그룹의 행을 서로 독립이라고 추론하지 않는다. 사용자는 그룹 의존성을 검토해야 한다.
- runout·중도절단 자료는 양의 failure cycle 수로 대체하지 않는다. 이 계약은 uncensored failure만 받는다.
- 관측 parameter 바깥 외삽, 불확실도 구간, 독립 검증, cycle counting, 가변진폭 누적, sequence effect, failure probability, acceptance 및 qualification은 제공하지 않는다.
- nested Sines screen이 쓰는 편차 진폭은 유한 표본 half maximum pairwise distance이며 정수압은 제공 시각의 piecewise-linear 시간평균이다. 연속 경로 진폭으로 해석할 수 없다.

## 다음 검증 단계

소프트웨어 검증에서는 합성 멱함수 자료의 계수 회수, 세 distinct parameter 최소 조건, 서로 다른 시편 ID, source hash 불일치, 화면(screen) 미계산 전파와 음의 기울기 요건을 별도로 확인한다. 물리 검증은 보정에 쓰지 않은 재료·시편의 완전한 원 시험자료로 진행해야 한다. 적합에 사용한 자료의 (R^2)는 검증 증거가 아니다.
