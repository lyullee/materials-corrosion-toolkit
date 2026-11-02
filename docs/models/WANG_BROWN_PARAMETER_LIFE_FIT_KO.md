# Wang–Brown 유한 파라미터 기반 수명 회귀

## 목적

`fatigue.wang_brown_reviewed_excursion_parameter`가 계산한 유한 표본 파라미터를, 동일 재료 조건에서 수행한 사용자의 정수명 시험 자료와 연결한다. 시험점으로 로그-로그 거듭제곱 관계를 추정하고, 입력 파라미터가 관측 범위 안에 있을 때만 파손 반복수를 계산한다.

이 구성요소는 Wang–Brown 파라미터 자체의 재계산이나 주기 분해를 하지 않는다. 정수명 자료에 대한 회귀와 한 점의 범위 내 예측을 수행하는 별도 계산 모델이다.

## 입력 및 추적성

- 계산된 Wang–Brown 유한 파라미터 `AssessmentResult`와 canonical SHA-256 digest
- 정확히 일치하는 `material_condition_id` 및 정의 ID `wang_brown_finite_reviewed_shear_reversal_plus_normal_excursion.v1`
- 서로 다른 파라미터 수준이 3개 이상인 양의 `calibration_parameter_values`
- 각 수준에 대응하는 양의 `observed_cycles_to_failure`
- 자료 식별자, 원자료 digest, `Evidence`, 재사용/계산 허가 근거 ID
- 시험 범위·재료 상태 일치성, 권리, 회귀/예측 범위의 명시적 검토 플래그

사용 전 upstream 결과의 재료 조건과 파라미터 정의를 확인한다. 자료가 원 시험 보고서나 자체 시험에서 왔다면 원자료 자체의 provenance와 재배포 권리를 별도로 관리해야 한다. 모듈은 자료 라이선스를 대신 판단하지 않는다.

## 계산

양의 시험점 `(P_i, N_i)`에 대해 `ln(N_i) = a + b ln(P_i)`를 일반 최소제곱법으로 적합한다. 추정 기울기가 음수일 때만 계산을 이어간다. 예측 대상 `P*`는 시험 파라미터 최솟값과 최댓값 사이에 있어야 한다. 그때 `N* = exp(a + b ln(P*))`를 반환한다. 로그 수명 잔차의 결정계수와 RMS도 설명용 진단값으로 기록한다.

## 적용 한계

- 회귀는 호출자가 제공한 정수명 자료의 경험적 표현이다. 특정 재료에 대한 보편식이나 문헌에서 자동 도출된 계수로 취급하지 않는다.
- 파라미터 계산이 사용한 `S`, 변형률 이력, 반전 구간, 시험 온도/환경/열처리와 회귀자료의 범위가 부합하는지는 검토자가 확인해야 한다.
- 시험점 밖 외삽, 재료·환경 간 전이, 임의 파라미터 정의 전이, 변동진폭 손상 누적, 순서 효과, 신뢰도/확률, 설계 코드 합격 및 사용수명 적격 판정은 수행하지 않는다.
- 회귀 진단값은 입력 자료의 산포 설명일 뿐 독립 검증이나 적합성 판정이 아니다.

## 식별자 및 근거

- 모델 ID: `fatigue.wang_brown_parameter_life_fit`
- 계산 자료 source ID: `caller_wang_brown_parameter_constant_amplitude_life_data`
- 파라미터 근거 source ID: `wang_brown_1993_path_independent_multiaxial_strain_parameter`
- 방법의 공개 서지정보: C. H. Wang, M. W. Brown, “A path-independent parameter for fatigue under proportional and non-proportional loading,” *Fatigue & Fracture of Engineering Materials & Structures*, 16 (1993), 1285–1297. [DOI: 10.1111/j.1460-2695.1993.tb00739.x](https://doi.org/10.1111/j.1460-2695.1993.tb00739.x)

문헌 링크는 방법의 맥락을 가리킨다. 이 코드는 문헌의 문장이나 시험 데이터를 포함하지 않으며, 재료별 계수는 호출자에게서만 받는다.

## 연결 절차

1. `fatigue.wang_brown_reviewed_excursion_parameter`를 실행하고 계산된 `AssessmentResult`를 보존한다.
2. 해당 파라미터 정의와 같은 재료 조건/시험 조건으로 얻은 독립 constant-amplitude 수명점을 준비한다.
3. 입력 contract에 upstream 결과 digest, 시험 데이터 digest/Evidence, condition descriptor digest 및 검토 플래그를 채운다.
4. 등록 후 Python API `evaluate_wang_brown_parameter_life_fit(request)`를 호출한다.
5. `computed`는 지원 범위 내 경험적 수명값, `needs_data`는 검토 미완료, `out_of_scope`는 조건/범위 불일치나 계산 불가를 뜻한다.

registry, catalog, schema 및 중앙 API 색인 연결은 별도 통합 작업에서 수행한다.
