# Davies 활동도와 경쟁 중성 고체상 평형의 반복 결합

`chemistry.competitive_solid_davies_equilibrium`는 입력 종목록·원소/전하 보존 침전 반응·후보 순수 중성 고체상·source-backed Ksp를 고정 활동도 계수 Gibbs 평형 solver에 전달한 다음, 계산된 액상 농도에서 몰랄 이온강도를 구해 Davies 계수를 갱신한다. 이 갱신을 damping과 caller 지정 log-gamma 허용치로 반복한다.

입력 contract는 `CompetitiveSolidDaviesIteration`이며 내부의 `equilibrium`은 기존 `CompetitiveSolidEquilibrium` 계약이다. 용액 부피당 물 질량(kg/L), 온도/용매에 적용되는 Davies A, A의 provider·revision·configuration/record digest, 이온강도 ceiling(최대 0.5 mol/kg), 전하 잔차 허용치, damping, 반복 한도와 수렴 허용치를 caller가 제공한다. 기존 고체 평형 solver의 모든 review gate와 추가 활동도/물 질량/전하 범위 gate가 열려야 계산한다. 계산은 wrapper 입력 digest, 반복별 고정점 잔차, 상별 complementarity 결과와 최종 활동도 계수를 보존한다.

농도 단위는 mol/m³이므로 몰랄농도 계산에서 먼저 1000 L/m³로 환산한 뒤 caller가 준 kg-water/L-solution으로 나눈다. 몰랄 이온강도는 `0.5 * Σ(m_i z_i²)`로 계산한다. 종 inventory가 전하 허용치를 넘거나 Davies 지원 한도를 초과하면 결과를 승격하지 않는다. 종료된 inner optimizer만으로는 충분하지 않으며 gamma 고정점, 상별 평형/부등식, KKT 상보성, 원소 수지 잔차를 모두 만족하는 inner 결과만 반환한다.

이 API는 닫힌 단일 액상에서 caller가 나열한 중성 순수 고체 후보의 선택적 Gibbs 평형을 반복 결합하는 범위다. 용존 종·반응 네트워크를 자동 생성하거나, 후보 밖 상을 찾거나, 고농도 전해질 모델을 바꾸거나, 침전 핵생성/속도·scale morphology·부식률을 예측하지 않는다. Davies 근사와 Ksp 데이터의 온도/매질 적합성은 독립 검토와 검증이 필요하다. `examples/competitive_solid_davies_equilibrium.py`는 synthetic wiring만 보여 주며 물리 기준 예가 아니다.
