# 경쟁 고체 평형과 SIT 활동도 반복

`chemistry.competitive_solid_sit_equilibrium`은 caller가 선언한 수용액 종·중성 고체상·반응·평형상수로 고정 활동도 경쟁 고체 평형을 풀고, 결과 액상의 molality 이온강도에서 SIT 활동도 계수를 다시 계산하는 제한된 외부 반복 API다.

## 입력과 호출

Python에서 `CompetitiveSolidSITIteration`을 만들고 `competitive_solid_sit_self_consistent_equilibrium(request)`를 직접 호출하거나 `ModelRegistry.run()`에 `chemistry.competitive_solid_sit_equilibrium` 식별자로 전달한다. 입력에는 다음 자료가 필요하다.

- 완전성을 검토한 공통 수용액 종과 후보 중성 고체상, 각 상의 원소·전하 보존 반응 및 용해도곱
- 용액 부피당 물 질량 `water_mass_per_solution_volume_kg_L`
- 온도별 Debye–Hückel A 및 방향성 `SITInteraction` 계수, 각 기록을 뒷받침하는 Evidence
- provider/revision, configuration digest, record digest, 이온강도·전하 잔차 한계 및 반복 제어값
- 상 목록, 열역학 자료, 표준상태 변환, 상호작용 계수 완전성 및 적용성에 관한 caller review

활동도 표준상태는 1 mol/L 농도 기준이어야 한다. 이 adapter는 `activity_reference_concentration_mol_m3=1000`인 종만 받는다. 액상 농도 `c`에서 `m = c/(1000w)`로 molality를 계산하며, molality 기준 SIT 계수 `gamma_m`은 `gamma_c = gamma_m/w`로 변환해 기존 평형 optimizer에 전달한다. `w`는 kg-water/L-solution이다. 이 조건과 변환 검토가 맞지 않으면 입력을 보완하도록 `needs_data`를 반환한다.

반복 절차는 (1) 현재 gamma로 고정-gamma 고체 평형을 풀고, (2) 최종 수용액 농도에서 종별 molality·이온강도·전하 잔차를 계산하고, (3) 명시된 SIT 상호작용으로 새 gamma를 산출하고, (4) log-gamma residual이 지정 허용치 안에 들 때까지 log 공간에서 damping하는 방식이다. 이온강도가 caller 한도를 넘거나 내부 평형이 실패하거나 반복 예산을 소진하면 수렴 결과로 승격하지 않는다.

## 범위와 사용 한계

이 API는 전체 종 네트워크·반응·고체상 목록·상수 또는 SIT 상호작용을 자동 생성하지 않는다. 누락된 방향성 상호작용은 완전한 parameter set을 검토했다는 caller 선언 아래 SIT evaluator의 기존 규칙에 따라 0으로 처리된다. 숫자 한도는 모델 자격화를 뜻하지 않는다. 자동 speciation, 고체상 발견, 핵생성, 시간의존 침전·용해, 스케일 구조·접착, 다상 수송 연성, 부식률, 설계 승인 또는 규격 적합성은 추론하지 않는다.

이 계산 경로는 구현 상태 기록이며 자체로 화학 시스템의 실험 검증을 의미하지 않는다. 운용 전에는 해당 용액 조성·온도·용매·상태 범위에서 신뢰할 수 있는 SIT 자료와 charge closure를 별도로 확보하고 비교해야 한다.
