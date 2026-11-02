# 가스켓 Prony 시간–온도 이동 이력

`fabrication.gasket_prony_temperature_shift_history`는 기준 온도에서 주어진 generalized-Maxwell/Prony 완화시간을 caller가 검토한 Arrhenius 또는 WLF 이동식으로 reduced time에 매핑하고, 기존 등온 Prony 응답기를 그 시간축에서 실행한다.

각 caller 구간은 시작·끝 시각과 함께 하나의 일정 온도를 가진다. Arrhenius 이동식은 `ln(a_T)=E_a/R(1/T-1/T_ref)`를 사용하고, WLF는 `ln(a_T)=-ln(10) C_1 (T-T_ref)/(C_2+T-T_ref)`를 사용한다. Reduced-time 증가량은 `dt/a_T`이다. 이동계수와 온도는 모두 caller 자료에서 오며, 표준 상수 `R` 외에 계수·기준온도·적용범위의 기본값을 제공하지 않는다.

## 입력과 검토

- 기존 `GasketViscoelasticHistoryRequest`의 재료계수는 이동식 기준온도에서 정의되어야 한다.
- 실제 시간구간마다 온도를 하나씩 제공한다. 구간 안에서는 일정 온도로 취급한다.
- Arrhenius는 활성화에너지 하나만, WLF는 `C1`, `C2`만 받는다. 활성화에너지는 0 이상이어도 되며 WLF의 `C2 + (T-Tref)`는 양수여야 한다.
- Caller는 계수와 모델 형식, 기준온도, 지원구간, 이동 방향, 동일 재료조건 적용 가능성, Prony shift의 thermorheological simplicity를 검토하고 Evidence와 SHA-256으로 연결한다.

## 결과 해석

결과에는 실제 시간과 reduced time, 구간별 이동계수, 기존 generalized-Maxwell 변형률 응답, 재료·시편·source-group 식별자를 기록한다. 기존 constitutive solver가 미지원 상태를 내면 그 status와 계산 prefix를 보존한다.

계산은 Prony branch 완화시간만 이동시킨다. 평형탄성률과 branch modulus는 기준온도 값을 그대로 사용하며 열팽창, 온도에 따른 강성 변화, 비선형 비가역 변화, 계면 slip, contact separation, bolt equilibrium, FE 응답, 누설 및 씰 acceptance는 계산하지 않는다. Arrhenius/WLF 식을 선택했다는 사실은 해당 재료에 그 법칙이 맞다는 증거가 아니다. 데이터 보정과 별도 실험 검증이 필요하다.

이 구현은 공개 배포용으로 새로 작성한 계산 및 설명이다. 시험과 검증 결과는 아직 없다.
