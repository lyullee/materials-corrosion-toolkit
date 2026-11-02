# 경쟁 고체 평형과 extended Debye–Hückel B-dot 활동도

`chemistry.competitive_solid_bdot_equilibrium`은 caller가 정의한 수용액 종과 중성 순수 고체상 경쟁 평형을 고정-gamma Gibbs optimizer로 풀고, 결과 액상의 molal ionic strength에서 species별 extended Debye–Hückel B-dot 계수를 다시 계산하는 외부 fixed-point API다.

## 계산식과 입력

로그 활동도 계수는 caller가 제공한 A, B, 이온 크기 `a_i`, 전하 `z_i`, molality ionic strength `I` 및 species별 B-dot `b_i`로 계산한다.

`log10(gamma_i) = -A z_i^2 sqrt(I)/(1 + B a_i sqrt(I)) + b_i I`

입력은 `CompetitiveSolidBdotIteration`이며 `CompetitiveSolidEquilibrium`의 종/상 목록·보존 반응·온도·solubility product에 더해 다음을 받는다.

- 용액 부피당 물 질량 `w` (kg-water/L-solution), temperature-matched A/B 계수와 지원 ionic-strength 상한
- 평형 수용종 순서와 정확히 맞는 `BdotSpeciesParameter` 행: 이온 크기(Å), `b_i`(kg/mol), 출처·record ID·SHA-256
- provider/revision, configuration 및 aggregate parameter record digest, Evidence 원문 digest
- fixed-point 반복 제어, 전하 허용치 및 parameter·표준상태·phase-set 적용성 review

molality 기준 계수는 기존 평형의 molarity 표준상태로 `gamma_c = gamma_m/w` 변환한다. 이 adapter는 종별 activity reference가 1000 mol/m³인 1 mol/L 기준에만 적용한다. charged species는 양의 ion-size가 필요하고, 온도 차이·파라미터 순서 또는 Evidence digest가 맞지 않으면 계산을 거부하거나 `needs_data`로 반환한다.

고정-gamma 상 평형과 B-dot 계수 사이 log-gamma 잔차가 지정 tolerance 이내여야 수렴 결과를 반환한다. damping, charge closure, ionic-strength ceiling, optimizer 결과와 반복 이력을 기록한다. parameter support 이탈, 비수렴 또는 수치 비정상은 computed equilibrium으로 승격하지 않는다.

## 범위

모든 종, phase, 반응, Ksp, A/B, ion-size 및 `b_i` 데이터는 caller가 공급해야 한다. 중성종의 salting 계수도 직접 제공해야 하며 누락된 값을 추정하지 않는다. 보편적 농축 전해질 자격화, phase discovery, aqueous reaction-network generation, precipitation kinetics, scale morphology, corrosion-rate validation 또는 규격 판정은 제공하지 않는다. B-dot 파라미터의 수치 지원범위와 용매/온도 적용성은 반드시 별도 근거로 확인한다.
