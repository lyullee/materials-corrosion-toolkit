# 경쟁 고체상 caller-rate 수지 ledger

`chemistry.competitive_solid_kinetic_ledger`는 각 고체상의 구간별 서명 extent-rate를 입력받아 수용액 종과 고체상의 재고를 보수적으로 갱신한다. API는 속도식을 계산하거나 고체상 형성을 예측하지 않는다. kinetic/precipitation solver가 산출한 caller-owned rate를 다른 계산 단계와 연결하고 그 수지 이력을 남기기 위한 계약이다.

## 입력 계약과 계산 순서

- `KineticAqueousSpecies`에는 초기 `mol/m3`, 전하수, 원소별 원자수와 출처 digest를 둔다.
- `KineticSolidPhase`에는 고체 조성, 고체 1 mol 형성에 소비되는 수용액 종별 양론계수, 초기 고체 inventory 및 근거 digest를 둔다. 중성 고체 반응은 전하와 모든 선언 원소를 보존해야 한다.
- `CompetingSolidKineticInterval`은 0초부터 빈틈이나 중복 없이 이어지는 시간 구간과 각 상의 signed extent-rate를 제공한다. rate 단위는 `mol/m3/s`이며 양수는 침전, 음수는 용해다.
- 각 구간에서 요청된 용해를 먼저 적용하되 존재하는 해당 고체량을 초과할 수 없다. 다음으로 모든 침전 요청에 하나의 공통 계수를 적용해 수용액 반응물이 부족해지는 일을 막고, 상 사이 caller rate 비율을 보존한다.
- 계산된 수용액 농도와 고체량은 음수가 될 수 없다. 각 시간 knot에서 원소 및 수용액 전하 수지를 초기 상태와 비교해 허용오차를 벗어나면 성공 결과 대신 계산 가능한 prefix와 `out_of_scope`를 반환한다.

## 필수 검토와 기록

고체 반응 양론/solution volume 기준, caller rate-law의 단위·온도·지원 범위, 용해 후 침전 split 순서, 계산 사용 권한을 명시해야 한다. 결과에는 provider/configuration/parameter 출처, 각 종 및 상의 출처 digest, 정규 입력 digest, 시간별 요청·적용 extent, 재고량, 원소·전하 잔차와 rate limiter를 남긴다.

## 사용 범위와 한계

이 계산은 상평형·Gibbs 최소화·용해도곱·수용액 speciation, rate law fitting, nucleation, 표면 coverage/morphology, 공간 수송, 부식속도 또는 보호효과를 계산하지 않는다. 반응망의 완전성, 일정 solution volume 가정, 온도 적합성 및 공급자 결과의 품질은 호출자가 별도로 정해야 한다. 공통 precipitation limiter는 명시된 split 수치 규칙이지 검증된 결정화 경쟁 모델이 아니다. 합성 입력 모양은 `examples/competing_solid_kinetic_ledger.py`에 있다. 실행 검증은 별도 검증 단계에 남긴다.
