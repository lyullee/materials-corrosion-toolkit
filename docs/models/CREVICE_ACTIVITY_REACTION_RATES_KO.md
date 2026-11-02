# 간극 활동도 기반 가역 반응률 스냅샷

## 목적

`chemistry.crevice_activity_based_reaction_rates`는 caller가 제시한 단일 용액 상태와 가역 반응 parameter set에서 활동도 기반 전·역 반응률, 순 반응률, 종별 생성/소모항 및 반응 구동지수를 계산한다. transport 결과를 적분하거나 화학 평형을 직접 구하지 않는다.

## 수식과 적용 조건

종의 무차원 활동도는 caller가 선언한 농도 기준 (c^\circ)에 대해

\[
a_i=\gamma_i c_i/c^\circ
\]

로 계산한다. 반응의 caller stoichiometry를 이용해

\[
r_f=k_f\prod_{i\in R}a_i^{\nu_i},\qquad
r_r=k_r\prod_{i\in P}a_i^{\nu_i},\qquad
r_{net}=r_f-r_r
\]

를 평가하고, 종별 순 생성항은 signed stoichiometric coefficient와 (r_{net})의 합이다. 기록 간 thermodynamic consistency 조건으로 (k_f/k_r=K)를 지정 허용오차 안에서 검사한다. 계산된 \(\log_{10}(Q/K)\)는 반응 구동상태 지표이며 독립 평형해를 뜻하지 않는다.

입력 종 목록은 유일 ID, 전하와 원소 조성 및 양의 농도·활동도계수를 가진다. 모든 반응은 charge/element-balanced여야 한다. rate parameter record ID와 SHA-256, provider configuration ID/digest, 라이선스 또는 사용허가 Evidence를 대조한다. 표준상태와 계수 단위는 caller가 검토해야 한다.

## 공개 Python API

```python
from matintegrity.crevice_activity_reaction_rates import (
    CreviceActivityRateRequest,
    CreviceActivityRateSpecies,
    CreviceActivityRateTerm,
    CreviceActivityRateReaction,
    evaluate_crevice_activity_reaction_rates,
)
```

최상위 요청에는 한 개 `state_id`의 온도·scope, activity provider identity/configuration digest, 종 상태, 반응 records, rights/provider Evidence와 applicability review flags를 넣는다. 출력에는 요청 SHA, 종 활동도, 반응별 전/역/net rate와 Q/K, 그리고 종별 생성/소모항이 포함된다.

## 한계

- 전/역 속도 상수는 dimensionless activity 기반이며 두 값에 같은 volumetric extent-rate 단위가 적용된다. 농도 기반으로 보정한 기존 속도상수에 gamma를 단순 곱하는 변환은 수행하지 않는다.
- 파라미터의 단위·표준상태·온도 유효 범위·실험 적합성은 caller 책임이다. (k_f/k_r=K) 점검은 parameter provenance나 실험 적합성을 인증하지 않는다.
- 한 상태에서 계산하는 rate snapshot이다. 미분방정식 적분, 수송/확산, activity coefficient 계산, mass-action speciation, pH, 상 생성·용해, 핵생성, 표면 반응·벽 소모 또는 부식률은 포함하지 않는다.
- 원소/전하 보존은 입력 stoichiometry의 대수 검사다. 완전한 수용액 speciation이나 다상 열역학을 보장하지 않는다.
- 계산 overflow, 음수/비유한 activity 또는 상세평형 불일치가 있으면 유효한 계산 결과로 처리하지 않는다.

## 출처와 개발 기록

Source IDs: `caller_crevice_activity_rate_state_and_gamma`, `caller_crevice_activity_rate_reaction_records`, `reversible_mass_action_rates_on_dimensionless_activities`. 원자료나 화학 상수는 포함하지 않으며, 모든 수치와 권한 근거는 caller가 제공한다. 이 설명은 API의 계산식과 사용 경계를 위한 독립적인 방법 문서다.

이 모델의 테스트, 계산 예제 실행, 실험 검증, 패키지 생성과 HPC 검증은 아직 수행하지 않았다. 제안 후속 검증은 forward/reverse 평형에서 net rate 0, 활동도 스케일 변화, rate overflow, charge/element 불균형, detailed-balance 불일치 및 Evidence digest 변경이다.
