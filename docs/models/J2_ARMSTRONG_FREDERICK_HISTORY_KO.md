# J2 Armstrong–Frederick 비선형 이력

`fatigue.j2_armstrong_frederick_strain_history`는 caller의 작은 변형률 3D 이력을 J2 소성으로 적분하면서 하나의 Armstrong–Frederick 이동 경화 backstress를 계산한다. 기존 J2 Prager 선형 이동경화는 소성변형률에 비례해 backstress가 계속 증가하는 모델이다. 이 API는 회복항을 추가해 단일 backstress의 포화를 표현한다.

## 상태식과 수치 갱신

응력은 `[xx, yy, zz, xy, yz, zx]` 순서의 Pa, 변형률은 동일 순서의 **tensor shear strain**으로 입력한다. 각 시간 간격은 caller 순서 그대로 단일 backward-Euler radial return을 수행한다.

일관성 함수는 (f=q(\boldsymbol{s}-\boldsymbol{\alpha})-[\sigma_{y0}+H p]\)이며 (q=\sqrt{3(\boldsymbol{x}:\boldsymbol{x})/2})를 사용한다. 한 개 backstress의 적분은 다음 implicit update다.

\[
\boldsymbol{\alpha}_{n+1}=
\frac{\boldsymbol{\alpha}_n+C\,\Delta p\,\boldsymbol{n}}
{1+\gamma\,\Delta p},\qquad
\boldsymbol{s}_{n+1}=\boldsymbol{s}_{trial}-3G\Delta p\boldsymbol{n}.
\]

여기서 (C\ge0)는 caller 단일 이동경화 계수, (\gamma\ge0)는 equivalent plastic strain 단위당 회복계수, (H\ge0)는 선형 등방경화 계수다. 일관성 잔차의 1차원 root는 유한 bracket 확장과 이분법으로 푼다. 유한 root를 묶지 못하면 구간을 `out_of_scope`로 반환한다.

## 입력 요구사항

`base_path`는 기존 `J2PragerStrainHistory` 계약을 재사용하되 Prager 계수는 0이어야 한다. 이 계약에서 탄성상수, 항복응력, 선형 등방경화, 초기 응력·소성변형률·backstress, caller가 순서화한 총변형률 경로 및 입력 Evidence를 받는다. 비선형 경화 parameter는 별도 record ID와 SHA-256, source ID를 가진다. 초기 상태는 첫 시각의 declared yield surface 안에 있어야 한다.

## 제한

- 작은 변형률, rate-independent, 등온, 연관 J2 모델이다.
- 한 backstress만 지원하며 다중 성분 Chaboche 모델이나 자동 adaptive substepping을 구현하지 않는다.
- 단일 시간 knot 사이 strain 경로는 endpoint 간 총변형률 증분으로 처리한다. 검토하지 않은 순간 경로, 비비례 추가경화, ratcheting qualification과 온도 이력은 예측하지 않는다.
- 반환 signed stress–strain work는 knot 기반 trapezoidal 양이며 plastic dissipation으로 간주하지 않는다.
- 이 constitutive response는 fatigue damage, life, crack initiation, probability, code acceptance 또는 재료 qualification이 아니다. 보정은 재료조건에 맞는 독립 순환시험이 필요하다.

## 후속 검증

수치 검증에서는 (\gamma=0)일 때 Prager radial-return 식과의 일치, 비영 회복에서의 backstress 포화 경향, elastic-only 경로, 항복 잔차, 초기항복 surface 바깥 입력 및 강한 비선형 입력에서 root 실패 처리를 확인한다. 실험 검증은 적합에 사용하지 않은 동일 재료조건의 안정화 loop 및 ratcheting 자료로 따로 수행해야 한다.
