# Crossland 비례응력 블록 수명·Miner 캠페인

## 목적

`fatigue.crossland_proportional_miner_campaign`은 caller가 제공한 다축 응력 블록을 각각 유한 표본 Crossland 비례응력 스크린으로 계산하고, 같은 Crossland 파라미터 정의와 재료 조건의 정수명 곡선에서 반복수를 얻은 뒤 선형 Miner 합산을 수행한다. finite limit screen만으로는 수명을 추론할 수 없으므로, 생명 곡선 자료는 별도 실험 Evidence로 받아 연결한다.

## 입력

- 각 block의 명시된 정수 `cycle_count`와 `MultiaxialCrosslandProportionalLimitScreen`
- 같은 재료조건·Crossland 계수·limit·보정 원천 digest를 공유하는 블록들
- 단조 증가하는 Crossland parameter knots (Pa), 대응하는 단조 감소 cycles to failure, 곡선에 사용한 정확한 α 값
- 생명곡선 원자료 Evidence, SHA-256, 계산/재사용 근거 ID 및 조건 descriptor digest
- cycle 분해와 선형 Miner 규칙을 적용하겠다는 caller 검토
- caller가 지정하는 양의 Miner 손상 한도

하위 Crossland 스크린은 닫힌 sampled tensor cycle과 proportionality tolerance를 요구한다. 비례성 검토 실패나 다른 재료 조건, 서로 다른 Crossland 보정 자료/계수/한도를 가진 block은 contract 단계에서 거부한다. life curve의 α도 모든 block에 적용한 α와 정확히 일치해야 한다.

## 계산 절차

1. 각 block에서 기존 `fatigue.multiaxial_crossland_proportional_limit_screen`을 계산한다.
2. `sqrt(J2)_a + α σH,max` 값이 정수명 곡선 knot 사이에 있으면 로그-로그 선형 보간하고, 정확한 knot면 해당 값을 사용한다.
3. 곡선 범위를 벗어나면 외삽하지 않고 해당 block 실패로 기록한다.
4. block damage `D_i = n_i / N_i`를 계산하고, 모두 계산 가능할 때만 `D_total = ΣD_i`를 반환한다.
5. 완전한 입력 block 묶음이 같은 정의로 반복된다는 조건에서만 `caller threshold / D_total`을 반복 단위 수로 보고한다.

한 블록이라도 검토/경로/곡선 범위를 충족하지 못하면 완전 캠페인 총 손상은 withholding 하며 앞에서 계산한 결과를 포함한 ledger와 실패 block ID를 반환한다.

## 가정 및 경계

- cycle count와 block 분해는 caller가 제공합니다. 이 API는 cycle counting, 재반전 pairing, 실측 이력의 block 추출을 하지 않습니다.
- Crossland 계수/한도 및 life curve의 재료상태·열처리·온도·환경·시험 범위 일치는 caller가 검토해야 합니다.
- Crossland limit의 exceedance와 S-N life mapping은 별개의 결과입니다. 한도 비교값을 수명으로 변환하거나 정수명 데이터 없이 life를 추정하지 않습니다.
- 로그-로그 보간은 관측 curve support 내부에만 적용하며 외삽·재료 전이·파라미터 정의 전이를 하지 않습니다.
- 선형 Miner 합은 명시적 caller 가정입니다. block 순서, overload/underload, interaction, crack propagation, residual-life update는 반영되지 않습니다.
- 반복 단위 수는 입력된 한 세트의 block 묶음이 동일하게 반복되는 산술적 지표이며, 검사주기·파손확률·규격 합격·서비스 적격 판정이 아닙니다.

## 식별자 및 문헌 근거

- Model ID: `fatigue.crossland_proportional_miner_campaign`
- Curve source ID: `caller_crossland_parameter_constant_amplitude_life_curve`
- 하위 한도 screen source IDs: `caller_crossland_finite_proportional_limit_calibration`, `crossland_1956_hydrostatic_pressure_torsional_fatigue_criterion`
- Crossland 식 정리와 검증 사례: [Validation of Multiaxial Fatigue Strength Criteria on Specimens from Structural Steel in the High-Cycle Fatigue Region](https://www.mdpi.com/1996-1944/14/1/116), *Materials* 14(1), 116 (2021).
- 원 문헌 서지정보: B. Crossland, “Effect of large hydrostatic pressures on the torsional fatigue strength of an alloy steel,” *Proceedings of the International Conference on Fatigue of Metals*, IMechE, London, 1956, pp. 138–149.

이 소프트웨어는 문헌 원문, 시험 데이터, 그림이나 표를 배포하지 않는다. life curve, 시험자료 권리 및 계수는 caller가 공급하고 확인한다.

## Python API 연결

- Contract: `CrosslandProportionalMinerCampaign`
- Block contract: `CrosslandProportionalBlock`
- Evaluator: `evaluate_crossland_proportional_miner_campaign(request)`
- 하위 finite path 계산: `evaluate_multiaxial_crossland_proportional_limit_screen`

registry, capability/schema, source derivation, API 색인 및 scope audit 연결은 중앙 통합 단계에서 수행한다.
