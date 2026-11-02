# Papadopoulos P2형 유한표본 피로한계 스크리닝

## 목표와 공개 근거

`matintegrity.multiaxial_papadopoulos_p2_finite_screen`은 caller가 지정한 유한 임계면 집합에서 각 평면의 유한 전단 방향 quadrature로 generalized shear amplitude를 구하고, 최대 정수압 응력과 caller 보정 계수를 결합해 caller 한계와 비교한다. 이 계산은 Papadopoulos의 고주기 피로 기준에서 소개한 임계면 generalized shear amplitude + 최대 정수압 응력 형태를 유한 표본 입력으로 제한한 변형 구현이다.

근거 문헌은 I. V. Papadopoulos, “Long life fatigue under multiaxial loading,” *International Journal of Fatigue* 23(10), 839–849 (2001), [DOI: 10.1016/S0142-1123(01)00059-7](https://doi.org/10.1016/S0142-1123(01)00059-7)이다. 이 문서는 공식을 새로 발명하거나 문헌 문장을 옮겨 적지 않고 계산 규약과 구현 경계를 설명한다.

## 계산 규약

닫힌 stress history의 각 sample에서 caller가 지정한 plane normal \(n\)에 대한 traction은 \(t=\sigma n\)으로 구성한다. 평면 내 방향 \(m(\chi)=\cos\chi\,u+\sin\chi\,v\)에 대한 signed resolved shear stress는 \(\tau(\chi,t_i)=m(\chi)\cdot\sigma(t_i)n\)이다. 방향별 표본 진폭은 공급한 주기 표본의 최대-최소 범위 절반으로 둔다.

\[
\tau_a(\chi)=\frac{\max_i\tau(\chi,t_i)-\min_i\tau(\chi,t_i)}{2}
\]

연속 원형 적분 대신 caller 방향과 정규화 양수 가중치 \(w_j\), \(\sum_j w_j=1\)를 사용한다.

\[
T_{a,\mathrm{finite}}(\Delta)=\sqrt{2\sum_j w_j\tau_a(\chi_j)^2}
\]

균일 원형 quadrature에서 가중합은 원주 평균 제곱을 근사하며, 앞의 2는 해당 generalized shear amplitude 정의의 정규화에 해당한다. 계산은 caller plane 중 가장 큰 \(T_{a,\mathrm{finite}}\)를 택하고 다음 scalar를 구성한다.

\[
P_{\mathrm{finite}}=\max_{\Delta\in\mathcal{P}} T_{a,\mathrm{finite}}(\Delta)+a_{\mathrm{caller}}\max_i\sigma_H(t_i), \qquad
\sigma_H=(\sigma_{xx}+\sigma_{yy}+\sigma_{zz})/3
\]

마지막으로 `caller_limit_Pa - P_finite`를 반환한다. coefficient와 한계는 자료·재료조건이 연결된 caller 제공값이다. coefficient를 피로 limit ratio에서 자동 추정하지 않는다.

## 입력 조건

- stress component order는 `[xx, yy, zz, xy, yz, zx]`이며 응력 전단 성분은 대칭 응력 텐서의 물리 성분이다.
- `SampledStressInvariantHistory`는 원본 ID/SHA, 명시적 sample ID 순서, 정확한 양 끝 응력 closure, component basis, finite 값과 크기를 보존한다.
- 평면마다 unit normal과 두 unit tangent basis vectors를 입력한다. 세 벡터는 서로 직교해야 한다.
- 각 plane의 `chi_radians`와 정규화 weight를 명시한다. 방향은 유일한 [0, 2π) 값이며 weight의 합은 1이어야 한다.
- plane 표본·방향 quadrature·stress 기반/주기·calibration 재료 적용·caller 한계를 검토해야 계산한다. calibration의 material-condition ID는 history와 정확히 일치하고, Evidence의 source ID/SHA는 calibration 식별자와 일치해야 한다.
- `maximum_shear_evaluations`가 \(N_{stress}\sum_{plane}N_{direction}\)에 대한 계산 상한을 둔다. 상한을 넘으면 `out_of_scope`를 반환한다.

## 출력 해석 및 한계

결과에는 각 유한 plane의 generalized shear amplitude, governing plane ID, 최대 정수압 응력 sample, caller limit 대비 margin, 평가 방향 수와 범위 witness를 포함한다. 결과 `caller_limit_not_exceeded`는 유한 표본과 caller 계수/한계에 대한 수치 비교만 뜻한다.

이 API는 모든 연속 plane을 검색하거나 모든 연속 in-plane direction을 적분하지 않는다. sample 사이의 응력 극값, 숨은 cycle, cycle counting, 시간 외삽, 물성 계수 fitting, 피로수명, failure probability, 코드 acceptance 또는 material qualification을 제공하지 않는다. caller의 plane·direction 분포는 실제 재료 모집단에 대한 무작위 표본으로 해석하지 않는다. 수치 근사 오차는 별도 angular/grid refinement 및 재료/실험 비교로 확인해야 한다.

## 카탈로그 출처 문구 제안

`caller_finite_quadrature_papadopoulos_p2_limit_screen`: 공개 Papadopoulos P2형 generalized shear + 최대 정수압 피로한계 구성을 caller 제공 유한 임계면 및 유한 평면내 방향 quadrature로 근사한다. 보정계수·한계와 적용성은 Evidence-bound caller 입력이며 연속 방향/평면 최적화나 수명 자격을 뜻하지 않는다.
